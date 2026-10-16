# Repo readiness

Getting a repository to the state its purpose calls for (published, deployable, maintainable): find what is missing
or stale by running a catalog of checks fitted to the repo, then close each gap with a known recipe.

## Language

### Finding gaps

**Check**:
One named question about a repo with a yes/no answer ("does the image run as a numeric uid?"), plus when it applies,
why it matters and which Procedure closes it.
_Avoid_: rule, item, lint, test

**Repo fact**:
Something true about the repo that decides which Checks apply: a language, a stack marker (a Dockerfile, a Helm
chart), visibility, the presence of a GUI. Drawn from a fixed vocabulary.
_Avoid_: axiom, tag, trait

**Check kind**:
How a Check gets its answer: by matching files, running a command, querying GitHub, or the agent's judgement.
_Avoid_: rule type, check type

**Judgement check**:
A Check answered by the agent reading the repo, not by a script ("does the README say why not just X?").
_Avoid_: manual check, soft check

**Outcome**:
The result of one Check on one repo: pass, fail, skipped (a condition did not hold), exempt (excused, with a
reason) or broken (could not run). A broken error-level Check blocks like a failed one.
_Avoid_: status, verdict, score, error (that word is a Severity)

**Severity**:
How much a failed Check matters. **error**: blocks the Scenario's outward-facing steps (visibility change, release,
publishing an install command). **warning**: the Scenario is not done until it is fixed or exempted. **info**: advice
only.
_Avoid_: level, priority, blocker (use error)

**Exemption**:
A per-repo decision that a Check does not apply here, always recorded with its reason.
_Avoid_: ignore, waiver, disable

### Organizing the catalog

**Scenario**:
A goal the user names ("publish it", "is it ready to deploy", "clean up the code") that picks which Checks run and
in what order.
_Avoid_: mode, profile, phase

**Stack pack**:
The Checks and Procedures for one stack (Python, Docker, Helm…), applied whenever the repo's facts show that stack.
The user never asks for one by name.
_Avoid_: language plugin, module

### Closing gaps

**Procedure**:
A recipe that closes one or more failed Checks: steps, a "done when" test and known pitfalls.
_Avoid_: fix, playbook entry, remediation
