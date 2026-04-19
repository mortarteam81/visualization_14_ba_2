# Agent Prompts

Reusable execution prompts for parallel Codex-style agentic coding on this project.

Files:
- `master_prompt.md`
- `subagent_1_pages_2_5.md`
- `subagent_2_pages_3_4.md`
- `subagent_3_pages_6_7.md`
- `subagent_4_shared_utils.md`

Recommended flow:
1. Start the master prompt.
2. Spawn 4 subagents with the matching prompt files.
3. Let the master integrate results and run final verification.
