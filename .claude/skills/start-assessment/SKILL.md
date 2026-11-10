---
name: start-assessment
description: Validate assessment prerequisites and create a safe multi-agent assessment plan. Does not start active testing automatically.
---

# Start assessment workflow

1. Read `CLAUDE.md` and `MULTI_AGENT_DESIGN.md`.
2. Run `aipentester init` if the project is not initialized (creates the
   manifest, the `state/` directories, and the starter `STATE.md`).
3. Check every required manifest field. Stop if placeholders remain.
4. Run `aipentester validate-scope`. Stop on failure.
5. Ask the user to confirm written authorization, exact origins/paths, test
   window, accounts, excluded workflows, rate limits, and approved
   synthetic objects.
6. Confirm the AIPentester MCP tools are available by inspecting the live
   MCP tool list (`claude mcp list`, then `/mcp` in the session). Do not
   guess tool names. The server exposes 17 tools (8 `browser_*`,
   3 `pentest_*`, 4 `recon_*`, `pentest_skill_execute`, `pentest`). There
   are NO `burp_*` MCP tools. Map each discovered tool to allow /
   approval-required / prohibited / unknown. Unknown traffic-generating
   tools remain denied. If the MCP server is unavailable, explain the
   enforcement gap and do not pretend it works.
7. Check `aipentester status` for existing state; if a previous session
   left a `STATE.md`, resume from it instead of starting over.
8. Plan reconnaissance and browser crawling. Assign the first tasks to
   `recon-agent` (Haiku) with task claims. Do not send active
   vulnerability probes yet.
9. Present the plan, risk notes, and approval gates for user confirmation.
   State that high-impact Burp operations (Intruder/Scanner runs) are NOT
   available over MCP and need a human in the Burp UI.
10. Only after explicit approval, start the approved discovery tasks.
