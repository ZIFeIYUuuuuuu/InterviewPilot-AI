# AGENTS.md

## Mandatory Read Order

Before reading any other project file, planning a task, or making code/document changes in this repository, the AI must read [agent.md](./agent.md) first.

After reading `agent.md`, the AI must read these repository memory files before continuing with substantial work:

1. [project-context.md](./project-context.md)
2. [progress.md](./progress.md)
3. [memory.md](./memory.md)

After the files above, read [docs/PRD.md](./docs/PRD.md) whenever the task touches product scope, workflow, agent behavior, UX, architecture, or prioritization.

The enforced startup order is:

1. `agent.md`
2. `project-context.md`
3. `progress.md`
4. `memory.md`
5. `docs/PRD.md` when relevant
6. Only then read task-specific code and files

## Instruction Priority

Use this order for project-local guidance:

1. Direct user request
2. `AGENTS.md`
3. `agent.md`
4. `docs/PRD.md`
5. Existing code and comments

## Notes

- `agent.md` is the primary working contract for this repository.
- If a task starts and `agent.md` has not been read in the current session, read it before continuing.
- The three memory files are default-maintained project files and must be kept up to date.
- `project-context.md`, `progress.md`, and `memory.md` must be read and written as UTF-8.
- When writing these memory files, use UTF-8 without BOM.
- If any of these files are found in a different encoding or contain garbled text, convert them to UTF-8 and verify content before further edits.
- Do not introduce behavior that conflicts with the product direction defined in the PRD.
