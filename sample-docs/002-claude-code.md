# Claude Code

Anthropic's agentic coding environment where Claude reads files, runs commands, and autonomously implements changes, shifting the user role from writing code to describing outcomes and verifying results.

## Key Concepts

- Agentic loop — Claude explores, plans, and implements rather than waiting on every instruction; the user describes what they want and Claude figures out how to build it.
- Context window as primary constraint — the conversation, file reads, and command outputs share a single budget; performance degrades as it fills, so most best practices exist to manage this resource.
- Verification as highest leverage — giving Claude a way to check its own work (tests, screenshots, linters, Bash commands) produces dramatically better results and removes the user as the sole feedback loop.
- Explore-plan-code-commit workflow — use Plan Mode to read files and draft an implementation plan before switching to Normal Mode to execute, then commit; skip planning only when the diff is describable in one sentence.
- Specific prompting — scope the task to a file or scenario, point to sources, reference existing patterns, and describe symptoms with likely locations; vague prompts are for open-ended exploration only.
- Rich context inputs — reference files with `@`, paste images, supply URLs, pipe data via `cat file | claude`, or let Claude fetch context itself with Bash/MCP/Read.
- CLAUDE.md — a per-session file loaded automatically, holding bash commands, style rules, workflow conventions, and environment quirks; must stay concise because bloated files cause Claude to ignore rules.
- CLAUDE.md locations — `~/.claude/CLAUDE.md` (global), `./CLAUDE.md` (team, checked into git), `./CLAUDE.local.md` (personal, gitignored), parent/child directories pulled in by proximity; imports via `@path/to/import` syntax.
- Permission modes — default prompt-per-action, auto mode (classifier blocks risky actions), `/permissions` allowlists for known-safe commands, and `/sandbox` for OS-level filesystem/network isolation.
- CLI tools over APIs — tools like `gh`, `aws`, `gcloud`, `sentry-cli` are the most context-efficient way to reach external services; Claude can learn new CLIs via `--help`.
- MCP servers — connect external tools (Notion, Figma, databases) through `claude mcp add` for feature implementation, data queries, and workflow automation.
- Hooks — scripts run deterministically at workflow points via `.claude/settings.json`; unlike advisory CLAUDE.md rules, hooks guarantee the action happens every time.
- Skills — `SKILL.md` files in `.claude/skills/` provide domain knowledge and reusable workflows loaded on demand, avoiding CLAUDE.md bloat; `disable-model-invocation: true` restricts a skill to manual invocation.
- Subagents — `.claude/agents/*.md` define specialized assistants with isolated context and scoped tool access, useful for investigation and verification without cluttering the main conversation.
- Plugins — installable bundles of skills, hooks, subagents, and MCP servers browsed via `/plugin`; code intelligence plugins give precise symbol navigation for typed languages.
- Interview-driven specs — for larger features, ask Claude to interview you using `AskUserQuestion` and write a `SPEC.md`, then start a fresh session to implement it with clean context.
- Course-correction primitives — `Esc` stops mid-action preserving context, `Esc+Esc` or `/rewind` restores prior conversation/code checkpoints, "undo that" reverts changes, `/clear` resets context between unrelated tasks.
- Two-correction rule — after two failed corrections on the same issue, `/clear` and restart with a better prompt; a clean session with a better prompt beats a long session with accumulated failed approaches.
- Context management commands — `/clear` between tasks, `/compact <instructions>` for targeted compaction, `/rewind` for partial summarization, `/btw` for side questions that never enter history.
- Checkpoints — Claude auto-checkpoints before changes and persists them across sessions; enables "try something risky, rewind if it fails" workflows, but only tracks Claude-made changes (not a git replacement).
- Session resumption — `claude --continue` resumes the most recent conversation, `--resume` picks from a list, `/rename` labels sessions so they function like branches with persistent contexts.
- Non-interactive mode — `claude -p "prompt"` runs sessionless for CI, pre-commit hooks, and scripts; `--output-format json` or `stream-json` enables programmatic parsing.
- Parallel sessions — desktop app with isolated worktrees, Claude Code on the web in cloud VMs, or agent teams coordinating multiple sessions; also enables Writer/Reviewer patterns where a fresh context reviews code without bias.
- Fan-out pattern — loop `claude -p` across a task list for migrations or analyses, using `--allowedTools` to scope permissions for unattended batch runs; test on a few files before scaling.
- Auto mode for autonomy — `claude --permission-mode auto -p "..."` runs uninterrupted with a classifier blocking scope escalation; non-interactive runs abort if the classifier repeatedly blocks.

## Common Failure Patterns

- Kitchen sink session — mixing unrelated tasks pollutes context; fix with `/clear` between tasks.
- Correcting over and over — repeated corrections accumulate failed approaches; fix by `/clear`-ing after two failed corrections and writing a better prompt.
- Over-specified CLAUDE.md — long files cause Claude to ignore rules buried in noise; fix by ruthlessly pruning and converting guarantees to hooks.
- Trust-then-verify gap — plausible-looking code that skips edge cases; fix by always providing verification (tests, scripts, screenshots).
- Infinite exploration — unscoped "investigate X" requests read hundreds of files; fix by scoping narrowly or delegating to subagents.

## Sources

- Best Practices for Claude Code — `digested-original/claude-code/claude-code-best-practice.md` (Anthropic, code.claude.com docs)
- Harness Design for Long-Running Application Development — `digested-original/harness-engineering/harness-engineering-from-anthropic.md` (Prithvi Rajasekaran, Anthropic, anthropic.com/engineering/harness-design-long-running-apps)

## Related Topics

- [[codebase-exploration]]
- [[harness-engineering]]
- [[prompt-engineering]]
