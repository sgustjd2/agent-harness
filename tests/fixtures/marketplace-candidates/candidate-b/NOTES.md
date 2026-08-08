# Candidate B -- one physical Claude-path catalog

Valid ONLY if both hosts and both installation surfaces parse this file correctly AND
all required metadata survives. The ChatGPT desktop app reads the legacy
`.claude-plugin/marketplace.json` path, but that fact alone does not establish:

- that Codex CLI accepts the same schema at that path
- that Claude Code accepts OpenAI-specific `policy` fields
- that one physical file is sufficient
- that desktop-app compatibility implies Codex CLI compatibility

ATS-022 check 5 is decisive here: if `policy` is silently dropped, Candidate B fails.
