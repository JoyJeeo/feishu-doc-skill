# Repository Instructions

These instructions apply to the entire repository.

## Required startup context

Before planning, editing, reviewing, or running project work, read these files completely in order:

1. `.ai/README.md`
2. `.ai/STATUS.md`
3. `.ai/DECISIONS.md`
4. `.ai/PRODUCT.md`
5. `.ai/ROADMAP.md`

Then inspect `git status`, the current branch, and the relevant implementation and tests. Do not rely on conversation history as the only source of project state.

If the documents conflict, follow this order:

```text
current explicit user instruction
> active decisions in .ai/DECISIONS.md
> .ai/PRODUCT.md
> .ai/ROADMAP.md
> .ai/STATUS.md
> existing implementation behavior
```

Do not silently resolve a material conflict. Report it and stop only the affected work when user direction is required.

## Status record

`.ai/STATUS.md` is the repository's current-state record and the handoff entry point for future AI tasks. It is a snapshot as of its recorded update time, not an automatically generated live dashboard.

At the start of every task:

- compare `.ai/STATUS.md` with `git status`, `.ai/ROADMAP.md`, the relevant files, and available verification evidence;
- correct stale or unsupported statements before relying on them for implementation;
- treat Git and newly produced test results as stronger evidence than an older status snapshot.

Before finishing any task that materially changes repository files, milestone state, verification results, blockers, or required authorization, update `.ai/STATUS.md` in the same change. Keep it concise and replace stale facts instead of building a chronological log.

The status snapshot must record:

- update date;
- current milestone and substage;
- completed and outstanding deliverables;
- latest verification commands and results;
- blockers or unverified areas;
- the next concrete action and any authorization or input it requires.

Do not mark work complete without evidence. Do not store credentials, authorization headers, document tokens, user or tenant identifiers, sensitive document content, or other secrets in `.ai/STATUS.md`.

## Development work control

Development has two equal entry types:

- **Product requirement:** a milestone, FR item, or other requirement recorded in `.ai/PRODUCT.md` or `.ai/ROADMAP.md`. It may enter development directly and does not need a wrapper local Issue.
- **Local Issue:** a repository-tracked defect, improvement, maintenance task, or technical task. Store new local Issue records under `.ai/issues/` when they are needed.

These entry types share the same execution rules:

1. Treat one product requirement or one local Issue as the active parent work item. Do not implement more than one parent work item at a time.
2. Read-only analysis and backlog recording may cover several future items, but implementation edits must remain inside the single active parent item's declared scope.
3. Before coding, decide whether the parent can be implemented and verified safely in one authorized task.
4. If it can, implement and verify it as one unsplit work item. Do not create ceremonial Specs.
5. If it cannot, split it into ordered, independently verifiable Specs before implementing it. Store Spec records under `.ai/specs/` when they are needed.

For every split parent:

- assign stable IDs to the parent and each Spec;
- make every Spec identify its parent type and parent ID;
- make the parent record list all Spec IDs in execution order;
- for a local Issue, keep the mapping in its Issue file;
- for a product requirement, keep the mapping in the relevant roadmap section or in `.ai/STATUS.md` while it is active;
- record each Spec's scope, non-goals, dependencies, deliverables, verification, acceptance criteria, and status;
- use `未开始`, `进行中`, `受阻`, and `已完成` consistently with `.ai/ROADMAP.md`.

Authorization is a hard gate between Specs:

- the initial authorization for a split parent permits only the first authorized Spec;
- after completing a Spec, run its verification, update its parent mapping and `.ai/STATUS.md`, report the result, and stop;
- ask the user to confirm the completed Spec and explicitly authorize the next Spec;
- do not edit files for the next Spec before that authorization;
- a broad milestone or Issue authorization does not authorize all remaining Specs;
- if confirmation is withheld, keep the parent active and the next Spec `未开始`.

An unsplit parent may be completed in one authorized implementation when its acceptance criteria and verification pass. A split parent may be marked complete only after every Spec is completed and the final parent-level acceptance criteria pass.

## Project boundaries

- This is a personal Skill for Feishu China cloud documents.
- All remote Feishu access is through the connected Feishu MCP only.
- Default to user identity and never fall back to application identity automatically.
- Every remote write requires a preview and explicit confirmation of that preview.
- Do not use Chrome, browser automation, CUA, OpenAPI, direct HTTP, or another connector as a Feishu fallback.
- When the MCP lacks a capability, report it as unsupported without trying another channel.
- Deletion, ownership transfer, and public-permission changes remain disabled unless the product decisions are explicitly revised by the user.

## Verification

For local safety-framework changes, run:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

Record the actual result in `.ai/STATUS.md`. Local tests do not prove real Feishu MCP compatibility; report remote integration as unverified until an authorized test completes.
