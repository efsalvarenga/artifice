# Design Specification: [Feature Name]

**Document ID:** `docs/designs/XXX_[feature_name].md`  
**Status:** Draft | Under Review | Approved | Superseded  
**Author:** Elephant Agent & Developer  
**Target Milestone:** [Target Milestone or Release]  

---

## 1. Overview & Objectives

[Concise summary of the feature, the problem it solves, and how it fits into the broader system architecture.]

### Goals

* [Primary goal 1]
* [Primary goal 2]

### Non-Goals

* [Explicitly out-of-scope item 1]
* [Explicitly out-of-scope item 2]

---

## 2. Domain Framing & User/System Experience

[Domain context, operational framing, user or caller interaction model, and expected interface/API presentation.]

---

## 3. State Schema & Data Models

[Complete, unambiguous data models. Provide field names, types, constraints, and valid ranges.]

```text
[Data schema, type definition, or interface contract]
```

---

## 4. Invariants & Rules

* **Invariant 1:** [Condition that must ALWAYS hold true across state transitions]
* **Invariant 2:** [Validation constraint or boundary condition]

---

## 5. Execution & State Mutation Logic

### Inputs & Triggers

* [Actions, input events, command arguments, or schedule triggers]

### State Mutation Logic

1. [Step-by-step deterministic state calculation]
2. [Boundary checks, side-effect isolation, and resource updates]

### Outputs & Events

* [Returned results, emitted events, or persisted state updates]

---

## 6. Edge Cases & Failure Modes

* **Edge Case 1:** [Description and deterministic resolution]
* **Edge Case 2:** [Boundary condition handling]

---

## 7. Verification & Automated Test Strategy

### Unit Tests

* [Test scenario 1: Boundary condition assertion]
* [Test scenario 2: State transition assertion]

### Integration & Perception Tests

* [End-to-end or perception verification assertion]

---

## 8. Goldfish Review Gates

- [ ] Zero-context Goldfish review completed
- [ ] Logic contradictions and edge-case holes addressed
- [ ] Human developer approval signed off
