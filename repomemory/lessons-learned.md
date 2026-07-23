# Lessons Learned

## 2026-07-23: Process discipline must live in AGENTS.md, not IDE-local skills

**Problem:** FEAT-001–005 were all implemented without subagent isolation or code review gates. Verification evidence declined from 146 lines (FEAT-002) to 19 lines of placeholder text (FEAT-004/005).

**Root cause:** The Ubuntu cron agent that executed FEAT-002–005 only had access to `AGENTS.md` (which ships with the repo). The skills mandating subagents (`dispatching-parallel-agents`, `subagent-driven-development`) and code reviews (`requesting-code-review`) lived at `C:\Users\Alandelone\.gemini\config\skills\` — a Windows-local path invisible to non-local agents.

**Fix:** Embedded Execution Discipline (subagent isolation, code review gates, execution handoff) and Verification Evidence Standard directly into `AGENTS.md`. Any agent on any environment that reads the repo constitution now inherits the full process.

**Rule:** If a process rule matters for quality, it MUST be in `AGENTS.md` or `rules/`, not only in IDE-local skill files.

