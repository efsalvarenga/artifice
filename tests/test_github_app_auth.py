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
from unittest.mock import patch
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
        cache_dir = self.cache_root / "artifice" / "gh-app-tokens"
        cache_dir.mkdir(parents=True, exist_ok=True)
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
                with self.assertRaises(self.auth.AuthError):
                    self.auth.load_config(config_path=str(p), env=self.env)

        bad_inst = dict(self.base_cfg)
        bad_inst["installations"] = {"org": "../999"}
        p = self.config_dir / "github-apps" / "badinst.json"
        p.write_text(json.dumps(bad_inst), encoding="utf-8")
        with self.assertRaises(self.auth.AuthError):
            self.auth.load_config(config_path=str(p), env=self.env)

    def test_config_precedence_cli_over_env_over_default(self):
        other = dict(self.base_cfg)
        other["app_slug"] = "env-profile-bot"
        (self.config_dir / "github-apps" / "work.json").write_text(json.dumps(other), encoding="utf-8")

        explicit = dict(self.base_cfg)
        explicit["app_slug"] = "explicit-file-bot"
        explicit_path = self.root / "explicit.json"
        explicit_path.write_text(json.dumps(explicit), encoding="utf-8")

        env = dict(self.env, ARTIFICE_GH_APP_PROFILE="work")
        cfg = self.auth.load_config(env=env)
        self.assertEqual(cfg.app_slug, "env-profile-bot")

        cfg = self.auth.load_config(profile="default", env=env)
        self.assertEqual(cfg.app_slug, "artifice-agent")

        cfg = self.auth.load_config(config_path=str(explicit_path), profile="work", env=env)
        self.assertEqual(cfg.app_slug, "explicit-file-bot")

    def test_private_key_guards_mode_symlink_repo_worktree_encrypted(self):
        # Mode wider than 0600 fails
        os.chmod(self.pem, 0o644)
        with self.assertRaises(self.auth.AuthError):
            self.auth.validate_and_open_private_key(self.pem)
        os.chmod(self.pem, 0o600)

        # Symlink fails
        link = self.config_dir / "link.pem"
        link.symlink_to(self.pem)
        with self.assertRaises(self.auth.AuthError):
            self.auth.validate_and_open_private_key(link)

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

    def test_redirect_blocked_and_token_not_leaked_in_errors(self):
        handler = self.auth._NoRedirectHandler()
        with self.assertRaises(HTTPError) as ctx:
            handler.redirect_request(None, None, 302, "Found", {}, "https://evil.example/steal")
        self.assertEqual(ctx.exception.code, 302)

        cfg = self.auth.load_config(env=self.env)
        secret_jwt = "eyJhbGciOiJSUzI1NiJ9.eyJpc3MiOiIxMjM0NTYifQ.supersecretsig"
        with patch.object(self.auth, "mint_jwt", return_value=secret_jwt):
            with patch.object(
                self.auth,
                "_api_request",
                side_effect=self.auth.AuthError("GitHub API error 401"),
            ):
                with self.assertRaises(self.auth.AuthError) as err:
                    self.auth.get_installation_token(cfg, env=self.env, no_cache=True)
        self.assertNotIn(secret_jwt, str(err.exception))

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

            cache_file = self.cache_root / "artifice" / "gh-app-tokens" / "123456-11111111.json"
            self.assertTrue(cache_file.exists())
            self.assertEqual(stat.S_IMODE(cache_file.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(cache_file.parent.stat().st_mode), 0o700)

            # Near-expiry (<300s) triggers refresh
            self._seed_cache("123456", "11111111", "ghs_expiring", seconds=120)
            t3 = self.auth.get_installation_token(cfg, env=self.env)
            self.assertEqual(t3, "ghs_tok_2")

            # Overly permissive cache file is ignored and replaced
            os.chmod(cache_file, 0o644)
            t4 = self.auth.get_installation_token(cfg, env=self.env)
            self.assertEqual(t4, "ghs_tok_3")
            self.assertEqual(stat.S_IMODE(cache_file.stat().st_mode), 0o600)

            # Corrupt cache file is ignored and replaced
            cache_file.write_text("{corrupt", encoding="utf-8")
            os.chmod(cache_file, 0o600)
            t5 = self.auth.get_installation_token(cfg, env=self.env)
            self.assertEqual(t5, "ghs_tok_4")

            # no_cache bypasses cache
            t6 = self.auth.get_installation_token(cfg, env=self.env, no_cache=True)
            self.assertEqual(t6, "ghs_tok_5")

    def test_git_credential_get_store_erase_and_host_scoping(self):
        c_terra = self._seed_cache("123456", "22222222", "ghs_terra_token")
        self._seed_cache("123456", "11111111", "ghs_default_token")

        # Matching https + case-insensitive github.com + leading slash path resolves owner
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "git-credential", "get"],
            input="protocol=https\nhost=GitHub.COM\npath=/terra-campaigns/oude-mechanismen.git\n\n",
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout, "username=x-access-token\npassword=ghs_terra_token\n")

        # Non-GitHub host returns nothing and exits 0
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

        # store is no-op
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "git-credential", "store"],
            input="protocol=https\nhost=github.com\n\n",
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertEqual(res.stdout, "")

        # erase unlinks matching cache file
        self.assertTrue(c_terra.exists())
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "git-credential", "erase"],
            input="protocol=https\nhost=github.com\npath=terra-campaigns/oude-mechanismen.git\n\n",
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertFalse(c_terra.exists())

    def test_git_env_and_exec_offline_git_and_git_config_preservation(self):
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
        self.assertIn("export GIT_COMMITTER_NAME='artifice-agent[bot]'", env_res.stdout)

        # exec with non-gh command works completely offline (cold cache, no network)
        probe = (
            "import json, os; "
            "keys = [k for k in os.environ if k.startswith(('GIT_', 'GH_'))]; "
            "print(json.dumps({k: os.environ[k] for k in sorted(keys)}))"
        )
        extra = dict(
            self.env,
            GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0="core.autocrlf",
            GIT_CONFIG_VALUE_0="false",
        )
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "exec", "--", sys.executable, "-c", probe],
            env=extra, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        captured = json.loads(res.stdout)
        self.assertNotIn("GH_TOKEN", captured)
        self.assertEqual(captured["GIT_AUTHOR_NAME"], "artifice-agent[bot]")
        self.assertEqual(
            captured["GIT_AUTHOR_EMAIL"],
            "987654321+artifice-agent[bot]@users.noreply.github.com",
        )
        self.assertEqual(captured["GIT_CONFIG_COUNT"], "4")
        self.assertEqual(captured["GIT_CONFIG_KEY_0"], "core.autocrlf")
        self.assertEqual(captured["GIT_CONFIG_VALUE_0"], "false")
        self.assertEqual(captured["GIT_CONFIG_KEY_1"], "credential.https://github.com.useHttpPath")
        self.assertEqual(captured["GIT_CONFIG_VALUE_1"], "true")
        self.assertEqual(captured["GIT_CONFIG_KEY_2"], "credential.https://github.com.helper")
        self.assertEqual(captured["GIT_CONFIG_VALUE_2"], "")
        self.assertEqual(captured["GIT_CONFIG_KEY_3"], "credential.https://github.com.helper")
        self.assertTrue(captured["GIT_CONFIG_VALUE_3"].startswith("!"))
        self.assertIn("git-credential", captured["GIT_CONFIG_VALUE_3"])
        self.assertIn("--profile", captured["GIT_CONFIG_VALUE_3"])

        # Malformed GIT_CONFIG_COUNT fails cleanly
        bad_env = dict(self.env, GIT_CONFIG_COUNT="not-a-number")
        bad_res = subprocess.run(
            [sys.executable, str(SCRIPT), "exec", "--", sys.executable, "-c", "pass"],
            env=bad_env, text=True, capture_output=True,
        )
        self.assertNotEqual(bad_res.returncode, 0)

    def test_exec_gh_host_guard_and_symlinked_gh_bot(self):
        self._seed_cache("123456", "11111111", "ghs_default_tok")
        self._seed_cache("123456", "33333333", "ghs_arete_tok")

        # Non-github.com GH_HOST fails closed
        bad_host = dict(self.env, GH_HOST="ghe.internal.example")
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "exec", "--with-gh-token", "--", sys.executable, "-c", "pass"],
            env=bad_host, text=True, capture_output=True,
        )
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("GH_HOST", res.stderr)

        # Symlinked gh-bot in a dir with spaces resolves repo owner from -R and injects GH_TOKEN
        bin_dir = self.root / "bin with space"
        bin_dir.mkdir()
        fake_gh = bin_dir / "gh"
        fake_gh.write_text(
            "#!/usr/bin/env bash\n"
            "printf 'TOKEN=%s AUTHOR=%s ARGS=%s\\n' \"$GH_TOKEN\" \"$GIT_AUTHOR_NAME\" \"$*\"\n",
            encoding="utf-8",
        )
        os.chmod(fake_gh, 0o755)
        gh_bot_link = bin_dir / "gh-bot"
        gh_bot_link.symlink_to(GH_BOT)

        run_env = dict(self.env, PATH=f"{bin_dir}:{self.env['PATH']}")
        res = subprocess.run(
            [str(gh_bot_link), "pr", "view", "-R", "AretePX/arete-engine", "44"],
            env=run_env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("TOKEN=ghs_arete_tok", res.stdout)
        self.assertIn("AUTHOR=artifice-agent[bot]", res.stdout)
        self.assertIn("ARGS=pr view -R AretePX/arete-engine 44", res.stdout)

    def test_check_offline_warnings_and_live_never_prints_token(self):
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "check"],
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("artifice-agent[bot]", res.stdout)

        # Warn if bot_user_id == app_id
        same_id = dict(self.base_cfg)
        same_id["bot_user_id"] = same_id["app_id"]
        same_path = self.root / "same.json"
        same_path.write_text(json.dumps(same_id), encoding="utf-8")
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "check", "--config", str(same_path)],
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("WARNING", res.stdout + res.stderr)

        # Live check verifies token + bot user ID without printing token
        cfg = self.auth.load_config(env=self.env)
        buf = io.StringIO()
        with patch.object(self.auth, "get_installation_token", return_value="ghs_secret_live_token"):
            with patch.object(self.auth, "fetch_bot_user_id", return_value="987654321"):
                rc = self.auth.run_check(cfg, owner=None, live=True, env=self.env, stream=buf)
        self.assertEqual(rc, 0)
        self.assertNotIn("ghs_secret_live_token", buf.getvalue())
        self.assertIn("OK", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
