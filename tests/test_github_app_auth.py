"""Unit and black-box tests for scripts/github_app_auth.py and scripts/gh-bot."""

import base64
import datetime
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "github_app_auth.py"
GH_BOT = ROOT / "scripts" / "gh-bot"

sys.path.insert(0, str(ROOT / "scripts"))


def _generate_rsa_keypair(directory: Path) -> tuple[Path, Path]:
    priv = directory / "test-app.pem"
    pub = directory / "test-app.pub.pem"
    subprocess.run(
        ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(priv)],
        check=True, capture_output=True,
    )
    os.chmod(priv, 0o600)
    subprocess.run(
        ["openssl", "pkey", "-in", str(priv), "-pubout", "-out", str(pub)],
        check=True, capture_output=True,
    )
    return priv, pub


class _FakeHTTPResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self, n: int = -1) -> bytes:
        return self._body if n < 0 else self._body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class GitHubAppAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._key_tmp = tempfile.TemporaryDirectory()
        cls.key_dir = Path(cls._key_tmp.name).resolve()
        cls.priv_key, cls.pub_key = _generate_rsa_keypair(cls.key_dir)

    @classmethod
    def tearDownClass(cls):
        cls._key_tmp.cleanup()

    def setUp(self):
        import github_app_auth as auth  # noqa: PLC0415

        self.auth = auth
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.home = self.root / "home with space"
        self.config_dir = self.home / ".config" / "artifice"
        self.cache_root = self.home / ".cache"
        (self.config_dir / "github-apps").mkdir(parents=True)
        self.cache_root.mkdir(parents=True)

        self.pem = self.config_dir / "github-app.pem"
        self.pem.write_bytes(self.priv_key.read_bytes())
        os.chmod(self.pem, 0o600)

        self.base_cfg = {
            "app_id": "123456",
            "app_slug": "artifice-agent",
            "bot_user_id": "987654321",
            "installation_id": "11111111",
            "installations": {
                "efsalvarenga": "11111111",
                "terra-campaigns": "22222222",
                "AretePX": "33333333",
            },
            "private_key_path": str(self.pem),
        }
        self.default_profile = self.config_dir / "github-apps" / "default.json"
        self.default_profile.write_text(json.dumps(self.base_cfg), encoding="utf-8")

        self.env = {
            "PATH": os.environ["PATH"],
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "XDG_CACHE_HOME": str(self.cache_root),
            "PYTHONDONTWRITEBYTECODE": "1",
        }

    def _future_expiry(self, seconds: int = 3600) -> str:
        dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _seed_cache(self, app_id: str, installation_id: str, token: str, seconds: int = 3600) -> Path:
        artifice_dir = self.cache_root / "artifice"
        cache_dir = artifice_dir / "gh-app-tokens"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(artifice_dir, 0o700)
        os.chmod(cache_dir, 0o700)
        path = cache_dir / f"{app_id}-{installation_id}.json"
        path.write_text(
            json.dumps({"token": token, "expires_at": self._future_expiry(seconds)}),
            encoding="utf-8",
        )
        os.chmod(path, 0o600)
        return path

    def test_profile_and_schema_validation(self):
        for bad_profile in ("", "../escape", "bad/name", "has space", ".hidden"):
            with self.subTest(profile=bad_profile):
                with self.assertRaises(self.auth.AuthError):
                    self.auth.validate_profile_name(bad_profile)

        for field, bad_value in (
            ("app_id", "abc"),
            ("app_id", 123456),
            ("app_id", "123/../456"),
            ("bot_user_id", "bot123"),
            ("installation_id", "999/evil"),
            ("app_slug", "bad_slug!"),
            ("app_slug", "bad\nslug"),
        ):
            with self.subTest(field=field, bad_value=bad_value):
                cfg = dict(self.base_cfg)
                cfg[field] = bad_value
                p = self.config_dir / "github-apps" / "bad.json"
                p.write_text(json.dumps(cfg), encoding="utf-8")
                with self.assertRaises(self.auth.AuthError) as ctx:
                    self.auth.load_config(config_path=str(p), env=self.env)
                if field == "app_id" and bad_value == 123456:
                    self.assertIn("quoted numeric string", str(ctx.exception))

        # Invalid installation value and duplicate case-insensitive keys rejected
        for inst_map in ({"org": "../999"}, {"AretePX": "33333333", "aretepx": "44444444"}):
            bad_inst = dict(self.base_cfg)
            bad_inst["installations"] = inst_map
            p = self.config_dir / "github-apps" / "badinst.json"
            p.write_text(json.dumps(bad_inst), encoding="utf-8")
            with self.assertRaises(self.auth.AuthError):
                self.auth.load_config(config_path=str(p), env=self.env)

    def test_config_precedence_cli_over_env_over_default(self):
        work_cfg = dict(self.base_cfg, app_slug="work-profile-bot")
        (self.config_dir / "github-apps" / "work.json").write_text(json.dumps(work_cfg), encoding="utf-8")

        env_file_cfg = dict(self.base_cfg, app_slug="env-file-bot")
        env_file = self.root / "env-config.json"
        env_file.write_text(json.dumps(env_file_cfg), encoding="utf-8")

        cli_file_cfg = dict(self.base_cfg, app_slug="cli-file-bot")
        cli_file = self.root / "cli-config.json"
        cli_file.write_text(json.dumps(cli_file_cfg), encoding="utf-8")

        # Env ARTIFICE_GH_APP_CONFIG wins over env ARTIFICE_GH_APP_PROFILE
        env = dict(self.env, ARTIFICE_GH_APP_CONFIG=str(env_file), ARTIFICE_GH_APP_PROFILE="../invalid")
        cfg = self.auth.load_config(env=env)
        self.assertEqual(cfg.app_slug, "env-file-bot")

        # CLI --profile wins over env ARTIFICE_GH_APP_CONFIG
        cfg = self.auth.load_config(profile="work", env=env)
        self.assertEqual(cfg.app_slug, "work-profile-bot")

        # CLI --config wins over CLI --profile and env vars (even with invalid env profile)
        cfg = self.auth.load_config(config_path=str(cli_file), profile="work", env=env)
        self.assertEqual(cfg.app_slug, "cli-file-bot")
        self.assertTrue(cfg.config_path.is_absolute())

        # Empty explicit --config fails closed
        with self.assertRaises(self.auth.AuthError):
            self.auth.load_config(config_path="", env=self.env)

        # ARTIFICE_GH_APP_CONFIG_DIR override works
        alt_dir = self.root / "alt-cfg"
        (alt_dir / "github-apps").mkdir(parents=True)
        alt_cfg = dict(self.base_cfg, app_slug="alt-dir-bot")
        (alt_dir / "github-apps" / "default.json").write_text(json.dumps(alt_cfg), encoding="utf-8")
        cfg = self.auth.load_config(env=dict(self.env, ARTIFICE_GH_APP_CONFIG_DIR=str(alt_dir)))
        self.assertEqual(cfg.app_slug, "alt-dir-bot")

    def test_private_key_guards_mode_symlink_repo_worktree_encrypted_fifo(self):
        # Mode wider than 0600 fails and quotes path
        os.chmod(self.pem, 0o644)
        with self.assertRaises(self.auth.AuthError) as ctx:
            self.auth.validate_and_open_private_key(self.pem)
        self.assertIn("chmod 600 '", str(ctx.exception))
        os.chmod(self.pem, 0o600)

        # Symlink fails
        link = self.config_dir / "link.pem"
        link.symlink_to(self.pem)
        with self.assertRaises(self.auth.AuthError):
            self.auth.validate_and_open_private_key(link)

        # FIFO does not hang and is rejected as non-regular
        fifo = self.config_dir / "key.fifo"
        os.mkfifo(fifo, 0o600)
        with self.assertRaises(self.auth.AuthError):
            self.auth.validate_and_open_private_key(fifo)

        # Inside a normal git repo (.git directory) fails
        repo = self.root / "normal-repo"
        (repo / ".git").mkdir(parents=True)
        in_repo = repo / "sub" / "key.pem"
        in_repo.parent.mkdir(parents=True)
        in_repo.write_bytes(self.priv_key.read_bytes())
        os.chmod(in_repo, 0o600)
        with self.assertRaises(self.auth.AuthError):
            self.auth.validate_and_open_private_key(in_repo)

        # Inside a git worktree (.git regular file) fails
        wt = self.root / "wt-repo"
        wt.mkdir()
        (wt / ".git").write_text("gitdir: /tmp/fake\n", encoding="utf-8")
        in_wt = wt / "key.pem"
        in_wt.write_bytes(self.priv_key.read_bytes())
        os.chmod(in_wt, 0o600)
        with self.assertRaises(self.auth.AuthError):
            self.auth.validate_and_open_private_key(in_wt)

        # Passphrase-protected key fails cleanly without hanging
        enc = self.config_dir / "encrypted.pem"
        enc.write_text("-----BEGIN ENCRYPTED PRIVATE KEY-----\nAAAA\n-----END ENCRYPTED PRIVATE KEY-----\n", encoding="utf-8")
        os.chmod(enc, 0o600)
        with self.assertRaises(self.auth.AuthError):
            self.auth.validate_and_open_private_key(enc)

    def test_jwt_rs256_claims_and_openssl_signature_verification(self):
        now = 1_700_000_000
        jwt = self.auth.mint_jwt("123456", self.pem, now=now)
        parts = jwt.split(".")
        self.assertEqual(len(parts), 3)

        def b64d(seg: str) -> bytes:
            pad = "=" * ((4 - len(seg) % 4) % 4)
            return base64.urlsafe_b64decode(seg + pad)

        header = json.loads(b64d(parts[0]).decode("utf-8"))
        payload = json.loads(b64d(parts[1]).decode("utf-8"))
        self.assertEqual(header, {"alg": "RS256", "typ": "JWT"})
        self.assertEqual(payload, {"iat": now - 60, "exp": now + 480, "iss": "123456"})
        self.assertLess(payload["exp"] - payload["iat"], 600)

        sig_file = self.root / "sig.bin"
        sig_file.write_bytes(b64d(parts[2]))
        verify = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", str(self.pub_key), "-signature", str(sig_file)],
            input=f"{parts[0]}.{parts[1]}".encode("ascii"),
            capture_output=True,
        )
        self.assertEqual(verify.returncode, 0, verify.stderr.decode("utf-8", "replace"))

    def test_api_exchange_redirect_blocking_headers_and_bot_user_id_lookup(self):
        # Redirect handler blocks redirects explicitly
        handler = self.auth._NoRedirectHandler()
        with self.assertRaises(HTTPError) as ctx:
            handler.redirect_request(None, None, 302, "Found", {}, "https://evil.example/steal")
        self.assertEqual(ctx.exception.code, 302)

        # Real exchange_installation_token exercises _api_request headers, URL, and response parsing
        captured_reqs = []
        expiry = self._future_expiry(3600)

        def fake_open(req, timeout=None):
            captured_reqs.append((req, timeout))
            return _FakeHTTPResponse(json.dumps({"token": "ghs_minted_ok", "expires_at": expiry}).encode("utf-8"))

        fake_opener = MagicMock()
        fake_opener.open.side_effect = fake_open
        with patch.object(self.auth.urllib.request, "build_opener", return_value=fake_opener):
            token, exp = self.auth.exchange_installation_token("123456", "22222222", self.pem)
        self.assertEqual(token, "ghs_minted_ok")
        self.assertEqual(exp, expiry)
        req, timeout = captured_reqs[0]
        self.assertEqual(req.full_url, "https://api.github.com/app/installations/22222222/access_tokens")
        self.assertEqual(req.get_method(), "POST")
        self.assertTrue(req.get_header("Authorization").startswith("Bearer "))
        self.assertEqual(req.get_header("Accept"), "application/vnd.github+json")
        self.assertEqual(req.get_header("X-github-api-version"), "2022-11-28")
        self.assertEqual(timeout, 15)

        # HTTP 401 never leaks JWT and gives actionable hint
        jwt_used = req.get_header("Authorization").split(" ", 1)[1]
        http_401 = HTTPError(req.full_url, 401, "Unauthorized", {}, io.BytesIO(b'{"message":"Bad credentials"}'))
        fake_opener.open.side_effect = http_401
        with patch.object(self.auth.urllib.request, "build_opener", return_value=fake_opener):
            with patch.object(self.auth, "mint_jwt", return_value=jwt_used):
                with self.assertRaises(self.auth.AuthError) as err:
                    self.auth.exchange_installation_token("123456", "22222222", self.pem)
        self.assertNotIn(jwt_used, str(err.exception))
        self.assertIn("401", str(err.exception))

        # fetch_bot_user_id accepts int and rejects bool
        fake_opener.open.side_effect = lambda r, timeout=None: _FakeHTTPResponse(b'{"id": 987654321}')
        with patch.object(self.auth.urllib.request, "build_opener", return_value=fake_opener):
            self.assertEqual(self.auth.fetch_bot_user_id("artifice-agent", "ghs_tok"), "987654321")

        fake_opener.open.side_effect = lambda r, timeout=None: _FakeHTTPResponse(b'{"id": true}')
        with patch.object(self.auth.urllib.request, "build_opener", return_value=fake_opener):
            with self.assertRaises(self.auth.AuthError):
                self.auth.fetch_bot_user_id("artifice-agent", "ghs_tok")

        # Non-UTF-8 response raises clean AuthError
        fake_opener.open.side_effect = lambda r, timeout=None: _FakeHTTPResponse(b"\xff\xfe")
        with patch.object(self.auth.urllib.request, "build_opener", return_value=fake_opener):
            with self.assertRaises(self.auth.AuthError):
                self.auth.fetch_bot_user_id("artifice-agent", "ghs_tok")

    def test_token_cache_reuse_expiry_permissions_and_symlink_safety(self):
        cfg = self.auth.load_config(env=self.env)
        calls = []

        def fake_exchange(app_id, installation_id, private_key_path):
            calls.append((app_id, installation_id))
            return f"ghs_tok_{len(calls)}", self._future_expiry(3600)

        with patch.object(self.auth, "exchange_installation_token", side_effect=fake_exchange):
            t1 = self.auth.get_installation_token(cfg, env=self.env)
            t2 = self.auth.get_installation_token(cfg, env=self.env)
            self.assertEqual(t1, "ghs_tok_1")
            self.assertEqual(t2, "ghs_tok_1")
            self.assertEqual(len(calls), 1)

            cache_dir = self.cache_root / "artifice" / "gh-app-tokens"
            cache_file = cache_dir / "123456-11111111.json"
            self.assertTrue(cache_file.exists())
            self.assertEqual(stat.S_IMODE(cache_file.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(cache_dir.stat().st_mode), 0o700)

            # Near-expiry (<300s) triggers refresh
            self._seed_cache("123456", "11111111", "ghs_expiring", seconds=120)
            self.assertEqual(self.auth.get_installation_token(cfg, env=self.env), "ghs_tok_2")

            # Overly permissive cache file is ignored and replaced
            os.chmod(cache_file, 0o644)
            self.assertEqual(self.auth.get_installation_token(cfg, env=self.env), "ghs_tok_3")
            self.assertEqual(stat.S_IMODE(cache_file.stat().st_mode), 0o600)

            # Corrupt cache file is ignored and replaced
            cache_file.write_text("{corrupt", encoding="utf-8")
            os.chmod(cache_file, 0o600)
            self.assertEqual(self.auth.get_installation_token(cfg, env=self.env), "ghs_tok_4")

            # Symlinked cache file is ignored on read and safely replaced via os.replace
            decoy = self.root / "decoy.json"
            decoy.write_text(json.dumps({"token": "ghs_poison", "expires_at": self._future_expiry(3600)}), encoding="utf-8")
            os.chmod(decoy, 0o600)
            cache_file.unlink()
            cache_file.symlink_to(decoy)
            self.assertEqual(self.auth.get_installation_token(cfg, env=self.env), "ghs_tok_5")
            self.assertFalse(cache_file.is_symlink())

            # no_cache bypasses cache
            self.assertEqual(self.auth.get_installation_token(cfg, env=self.env, no_cache=True), "ghs_tok_6")

            # Symlinked cache directory is rejected on read, write, and erase
            real_dir = self.root / "symlink-target"
            real_dir.mkdir(mode=0o700)
            sym_cache_root = self.root / "sym-cache"
            (sym_cache_root / "artifice").mkdir(parents=True)
            os.chmod(sym_cache_root / "artifice", 0o700)
            (sym_cache_root / "artifice" / "gh-app-tokens").symlink_to(real_dir)
            sym_env = dict(self.env, XDG_CACHE_HOME=str(sym_cache_root))
            with self.assertRaises(self.auth.AuthError):
                self.auth.get_installation_token(cfg, env=sym_env)
            with self.assertRaises(self.auth.AuthError):
                self.auth.erase_cached_token(cfg, env=sym_env)

    def test_cross_owner_isolation_and_git_credential_protocol(self):
        c_terra = self._seed_cache("123456", "22222222", "ghs_terra_token")
        c_default = self._seed_cache("123456", "11111111", "ghs_default_token")

        # Matching https + case-insensitive github.com + leading slash resolves owner
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "git-credential", "get"],
            input="protocol=https\nhost=GitHub.COM\npath=/terra-campaigns/oude-mechanismen.git\n\n",
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout, "username=x-access-token\npassword=ghs_terra_token\n")

        # Unconfigured third-party owner returns empty (does NOT leak default token or evict default cache)
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "git-credential", "get"],
            input="protocol=https\nhost=github.com\npath=third-party/repo.git\n\n",
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout, "")

        res = subprocess.run(
            [sys.executable, str(SCRIPT), "git-credential", "erase"],
            input="protocol=https\nhost=github.com\npath=third-party/repo.git\n\n",
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue(c_default.exists())

        # Explicit unknown --owner on token CLI fails closed
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "token", "--owner", "unknown-org"],
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("not configured", res.stderr)

        # CLI token subcommand succeeds for configured owner from cache
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "token", "--owner", "terra-campaigns"],
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout, "ghs_terra_token\n")

        # Non-GitHub host or http returns empty
        for payload in (
            "protocol=https\nhost=gitlab.com\npath=foo/bar.git\n\n",
            "protocol=http\nhost=github.com\npath=efsalvarenga/artifice.git\n\n",
        ):
            res = subprocess.run(
                [sys.executable, str(SCRIPT), "git-credential", "get"],
                input=payload, env=self.env, text=True, capture_output=True,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertEqual(res.stdout, "")

        # store is no-op; erase unlinks matching configured owner cache
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "git-credential", "store"],
            input="protocol=https\nhost=github.com\n\n",
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0)
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "git-credential", "erase"],
            input="protocol=https\nhost=github.com\npath=terra-campaigns/oude-mechanismen.git\n\n",
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertFalse(c_terra.exists())

    def test_git_env_and_exec_offline_git_and_flags(self):
        env_res = subprocess.run(
            [sys.executable, str(SCRIPT), "git-env"],
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(env_res.returncode, 0, env_res.stderr)
        self.assertIn("export GIT_AUTHOR_NAME='artifice-agent[bot]'", env_res.stdout)
        self.assertIn(
            "export GIT_AUTHOR_EMAIL='987654321+artifice-agent[bot]@users.noreply.github.com'",
            env_res.stdout,
        )

        # exec with non-gh command works offline, preserves GIT_CONFIG_COUNT, passes absolute --config & --owner
        probe = (
            "import json, os; "
            "keys = [k for k in os.environ if k.startswith(('GIT_', 'GH_', 'GITHUB_', 'ARTIFICE_'))]; "
            "print(json.dumps({k: os.environ[k] for k in sorted(keys)}))"
        )
        extra = dict(
            self.env,
            GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0="core.autocrlf",
            GIT_CONFIG_VALUE_0="false",
            GH_TOKEN="ambient_human_tok",
            GITHUB_TOKEN="ambient_github_tok",
        )
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "exec", "--owner", "AretePX", "--no-gh-token", "--", sys.executable, "-c", probe],
            env=extra, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        captured = json.loads(res.stdout)
        self.assertNotIn("GH_TOKEN", captured)
        self.assertNotIn("GITHUB_TOKEN", captured)
        self.assertEqual(captured["ARTIFICE_GH_APP_OWNER"], "AretePX")
        self.assertEqual(captured["GIT_AUTHOR_NAME"], "artifice-agent[bot]")
        self.assertEqual(captured["GIT_CONFIG_COUNT"], "4")
        self.assertEqual(captured["GIT_CONFIG_KEY_0"], "core.autocrlf")
        self.assertEqual(captured["GIT_CONFIG_KEY_1"], "credential.https://github.com.useHttpPath")
        self.assertEqual(captured["GIT_CONFIG_VALUE_1"], "true")
        self.assertEqual(captured["GIT_CONFIG_VALUE_2"], "")
        self.assertTrue(captured["GIT_CONFIG_VALUE_3"].startswith("!"))
        self.assertIn("--config", captured["GIT_CONFIG_VALUE_3"])
        self.assertIn(str(self.default_profile), captured["GIT_CONFIG_VALUE_3"])

        # --no-git-credential skips GIT_CONFIG_* injection
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "exec", "--no-git-credential", "--", sys.executable, "-c", probe],
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("GIT_CONFIG_COUNT", json.loads(res.stdout))

        # Missing binary returns clean exit 127 without Python traceback
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "exec", "--", "nonexistent-binary-xyz-999"],
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 127)
        self.assertNotIn("Traceback", res.stderr)

        # Malformed GIT_CONFIG_COUNT fails cleanly
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "exec", "--", sys.executable, "-c", "pass"],
            env=dict(self.env, GIT_CONFIG_COUNT="not-a-number"), text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 1)

    def test_exec_host_guards_ambient_token_strip_and_symlinked_gh_bot(self):
        self._seed_cache("123456", "11111111", "ghs_default_tok")
        self._seed_cache("123456", "33333333", "ghs_arete_tok")

        bin_dir = self.root / "bin with space"
        bin_dir.mkdir()
        fake_gh = bin_dir / "gh"
        fake_gh.write_text(
            "#!/usr/bin/env bash\n"
            "printf 'TOKEN=%s GH_TOK2=%s AUTHOR=%s ARGS=%s\\n' \"$GH_TOKEN\" \"${GITHUB_TOKEN:-unset}\" \"$GIT_AUTHOR_NAME\" \"$*\"\n",
            encoding="utf-8",
        )
        os.chmod(fake_gh, 0o755)
        gh_bot_link = bin_dir / "gh-bot"
        gh_bot_link.symlink_to(GH_BOT)

        run_env = dict(self.env, PATH=f"{bin_dir}:{self.env['PATH']}", GITHUB_TOKEN="human_pat")

        # Non-github.com hosts blocked across GH_HOST, -R, --hostname, and GH_REPO
        for extra_env, args in (
            ({"GH_HOST": "ghe.internal.example"}, ["pr", "list"]),
            ({}, ["pr", "view", "-R", "ghe.internal.example/org/repo", "1"]),
            ({}, ["api", "--hostname", "ghe.internal.example", "user"]),
            ({"GH_REPO": "ghe.internal.example/org/repo"}, ["pr", "list"]),
        ):
            with self.subTest(extra_env=extra_env, args=args):
                res = subprocess.run(
                    [str(gh_bot_link), *args],
                    env=dict(run_env, **extra_env), text=True, capture_output=True,
                )
                self.assertEqual(res.returncode, 1, res.stdout + res.stderr)

        # Symlinked gh-bot resolves owner from -R, injects bot GH_TOKEN, and strips ambient GITHUB_TOKEN
        res = subprocess.run(
            [str(gh_bot_link), "pr", "view", "-R", "AretePX/arete-engine", "44"],
            env=run_env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("TOKEN=ghs_arete_tok", res.stdout)
        self.assertIn("GH_TOK2=unset", res.stdout)
        self.assertIn("AUTHOR=artifice-agent[bot]", res.stdout)
        self.assertIn("ARGS=pr view -R AretePX/arete-engine 44", res.stdout)

    def test_check_offline_warnings_live_match_and_mismatch(self):
        # SSH remote warning in a repo with SSH origin
        ssh_repo = self.root / "ssh-repo"
        ssh_repo.mkdir()
        subprocess.run(["git", "-C", str(ssh_repo), "init", "-q"], check=True, env=self.env)
        subprocess.run(
            ["git", "-C", str(ssh_repo), "remote", "add", "origin", "git@github.com:terra-campaigns/oude-mechanismen.git"],
            check=True, env=self.env,
        )
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "check"],
            cwd=ssh_repo, env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("artifice-agent[bot]", res.stdout)
        self.assertIn("Installation ID: 22222222", res.stdout)
        self.assertIn("WARNING: origin remote uses SSH", res.stdout)

        # Warn if bot_user_id == app_id with quoted app_slug, and show Config: for explicit --config
        same_id = dict(self.base_cfg, bot_user_id=self.base_cfg["app_id"])
        same_path = self.root / "same.json"
        same_path.write_text(json.dumps(same_id), encoding="utf-8")
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "check", "--config", str(same_path)],
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn(f"Config: {same_path}", res.stdout)
        self.assertIn('"users/artifice-agent[bot]"', res.stdout)

        # Live check verifies token + bot user ID without printing token, and fails on ID mismatch
        cfg = self.auth.load_config(env=self.env)
        buf = io.StringIO()
        with patch.object(self.auth, "get_installation_token", return_value="ghs_secret_live_token"):
            with patch.object(self.auth, "fetch_bot_user_id", return_value="987654321"):
                rc = self.auth.run_check(cfg, owner=None, live=True, env=self.env, stream=buf)
        self.assertEqual(rc, 0)
        self.assertNotIn("ghs_secret_live_token", buf.getvalue())
        self.assertIn("OK", buf.getvalue())

        with patch.object(self.auth, "get_installation_token", return_value="ghs_secret_live_token"):
            with patch.object(self.auth, "fetch_bot_user_id", return_value="555555555"):
                with self.assertRaises(self.auth.AuthError):
                    self.auth.run_check(cfg, owner=None, live=True, env=self.env, stream=io.StringIO())


if __name__ == "__main__":
    unittest.main()
