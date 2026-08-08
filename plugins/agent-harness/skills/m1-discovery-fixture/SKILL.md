---
name: m1-discovery-fixture
description: >-
  M1 compatibility fixture. Confirms that both hosts discover the shared skills
  directory from a single plugin root. It performs no work and must never be used
  for anything but loader and validator verification.
---

# m1-discovery-fixture

**This is a compatibility fixture, not a product Skill.** It is the only Skill in
the installable plugin root during M1.

## Purpose

Experiment ATS-018 asks whether Claude Code and Codex both discover the same
`skills/` directory when two manifests share one plugin root. Answering that needs
a Skill the hosts can actually see. This is that Skill and nothing more.

## Behaviour

None. If invoked, state that this is an M1 compatibility fixture with no behaviour,
and take no action.

## Why it carries agents/openai.yaml

The policy file sets `allow_implicit_invocation: false`, so the fixture cannot be
selected implicitly by a model. A fixture that could be auto-invoked would be a
surface with no purpose. It also demonstrates that the policy file travels inside
the Skill directory through packaging and cache copy.
