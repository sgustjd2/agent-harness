---
name: m1-script-probe-fixture
description: >-
  Isolated test fixture for experiment B (ATS-020), which investigates whether a
  bundled script can be located without assuming the working directory. Never
  installed; lives outside the installable plugin root.
---

# m1-script-probe-fixture

**Test fixture. Deliberately outside `plugins/agent-harness/`.**

Experiment B asks a question the canonical Skill layer is forbidden to assume the
answer to: how does a Skill locate a bundled script without assuming the working
directory, without a host path variable, and without `PLUGIN_ROOT` -- which is
verified for plugin hooks only and undocumented for Skill-started commands.

This fixture is not shipped, because a probe in the installable root would be a
product surface. Experiment B needs Skill execution, which may require an
interactive or paid model, so it is excluded from CI and run manually.

A negative result is a valid outcome. An unrecorded result is not.
