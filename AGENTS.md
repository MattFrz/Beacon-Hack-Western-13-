# Beacon: notes for coding agents

`graphify-out/GRAPH_REPORT.md` maps how the code, the spec and the docs connect. Read it first when a question spans more than one folder.

## Before opening a PR into `main`: refresh the graph

The `graphify graph updated` CI check fails any PR into `main` that changes code or docs without also changing `graphify-out/graph.json`.

1. Merge the latest `main` into your branch, so the graph covers what will land. If `graphify-out/` conflicts, take main's copy (`git checkout origin/main -- graphify-out/`) and refresh in step 2.
2. Refresh the graph from the repo root:
   - In Claude Code: `/graphify . --update`. It re-reads only changed files: code for free, docs with subagents.
   - Code-only change, any agent or a terminal: `graphify update .` (no LLM needed).
   - Changed docs (`.md`, `.txt`, `.html`) need the skill run, so use Claude Code or another agent with the graphify skill.
   - First time: `uv tool install graphifyy`, then `graphify install --platform <claude|codex|cursor|...>`.
3. Commit `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.json` and `graphify-out/graph.html`. The rest of `graphify-out/` is a local cache and stays git-ignored.

Done when those three files are in your PR and the `graphify graph updated` check passes.
