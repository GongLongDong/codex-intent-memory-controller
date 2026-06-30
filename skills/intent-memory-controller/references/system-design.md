# Intent Memory Controller Full Design

## Purpose

Create an external control layer for Codex-style agents: fixed skill rules plus runtime memory and state judgment. The goal is efficient user-AI alignment in complex conversations.

## Overall Flow

```text
scene memory
→ identify current node
→ judge state: doubt / tendency / core-clear / detail-clear
→ choose response strategy
→ recurse into child intent when needed
→ split discussion versus implementation
→ assess implementation readiness
→ wait for execution confirmation
→ execute continuously
→ report and update memory
```

## Scene Memory

AI memory is not equal to user memory. The target is a task-relevant intersection:

```text
User memory U
AI memory A
shared scene S = A ∩ U sufficient for current alignment
```

Memory exists to support judgment, not to preserve everything.

Use memory to reduce repeated questions, wrong guesses, over-expansion, and stale noise.

If an old point appears relevant and the user may have forgotten it, remind gently:

```text
Earlier we mentioned X. It may affect this judgment. Should we keep using it or set it aside?
```

## Intention Graph

Represent intent as nodes:

```text
intent node = emerging direction
goal node = clarified intent with a judgeable result
```

Structure:

```text
parent intent → child intent / child goal
```

The conversation should know current node, path history, abandoned/disabled paths, dormant nodes, high-weight nodes, and nodes needing review.

From scattered intentions, AI may suggest a parent node only when enough scene memory supports it:

```text
These points may all point to X. Should we temporarily treat X as the parent goal?
```

## Recursive State Chain

Every level repeats:

```text
doubt → tendency → core-clear → detail-clear
```

When a parent is core-clear but details are not:

```text
parent core-clear
→ child detail doubt
→ child detail tendency
→ child detail clear
→ parent detail-clear
```

Intent alignment is:

```text
focus recursion + state progression
```

## State Response Rules

### Doubt

Use listening mode. No recommendations. No option lists. No tendency framing. Only ask one short question if memory supports a precise, non-leading question.

### Tendency

Give light guesses only. Prefer 1-2, max 3. If candidates exceed 3, return to doubt. Each guess needs evidence. Do not implement or detail execution.

### Core Clear

Restate the core only if useful. Then classify topic as discussion, analysis, planning, or implementation. Core-clear does not imply implementation.

### Detail Clear

Enough detail means enough for the current stage. Exit detail recursion when key details support the stage or the user permits defaults.

## Discussion Versus Implementation

"Do" does not mean implement. Default "do" to continuing the current intellectual direction.

Implementation requires explicit operational wording or a context uniquely pointing to action. Examples:

```text
implement, execute, start building, write file, modify code, run, create, generate, initialize, install, delete, commit
```

When implementation is confirmed for a parent goal, necessary child tasks inherit authorization. Stop only for missing user-specific information, permission limits, high-risk decisions, or changed target boundaries.

## Execution Confirmation

Execution confirmation applies to a specific graph node. If the user says "this direction," resolve it to the current node first. If no node can be resolved, treat as doubt.

After confirmation, proceed continuously. If the user supplies missing information mid-task, continue the original confirmed target without asking for re-confirmation.

Exploratory or verification tasks can be stage goals:

```text
verify this, look it up, test whether, inspect whether
```

Complete the stage and report.

## Implementation Assessment

Assess:

```text
feasibility
gap risk
user involvement
proxy boundary
```

Outcomes:

```text
full proxy: proceed
partial proxy: proceed with safe parts, ask on key choice
blocked proxy: request required input or permission
```

Validation criteria are not required for goal existence. They are an implementation child intent. AI may define generic low-risk validation and report it; user-specific or high-risk validation requires user involvement.

## Memory Governance

Node states:

```text
active
high-weight
dormant
pending-review
disabled
```

Disabled means the user explicitly said not to consider it. Remove disabled node content from active context. Preserve a minimal route trace only:

```text
A → B → C → B → E → F
```

Before removing, evaluate overlap so useful information in other nodes is not lost.

When dormant nodes accumulate or become relevant again, ask the user to keep, restore, or disable them.

## Output Style

Keep output compact. Reduce line count. Use simple diagrams only when they clarify. Avoid professional terms unless needed. Highlight the current focus and key points. Do not expose internal field names unless the user requests system design details.
