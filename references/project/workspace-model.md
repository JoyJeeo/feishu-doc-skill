# Project workspace document model

Read this reference when creating or organizing a project home, project document set, or weekly report.

## Workspace structure

Use one Wiki-hosted Docx project home as both the project index and the parent for project documents. Do not create a separate empty directory when the project home can provide the same navigation and hierarchy.

Project documents are the user-declared subset of PRD, technical design, meeting notes, weekly reports, retrospectives, and other named deliverables. Do not create every template by default. Keep structured action, risk, decision, and metric registers out of this model; use [register-model.md](register-model.md) for those Bitable resources.

## Evidence rules

Build and validate the project evidence map from [audit-model.md](audit-model.md) before drafting status content. Every factual status, milestone, metric, risk, decision, or completion statement must cite an exact source URL. A missing or partially readable source produces a specific pending-confirmation marker, not an inferred fact.

For every generated document:

- keep exact source URLs in a `Sources` section;
- separate source facts, derived findings, plans, and pending confirmations;
- use the closest existing template from [../docx/templates.md](../docx/templates.md);
- omit an optional document or section when it is irrelevant, but never hide a missing required fact.

## Project home

The project home uses the `project_home` template and includes:

1. current state with an `as_of` date and supporting source;
2. goal and scope;
3. milestones and status;
4. roles and contacts;
5. key documents with exact links;
6. action and risk summary, or explicit pending markers until the Bitable registers exist;
7. decisions;
8. sources and pending confirmations.

When the home is new, its first creation preview may contain planned-document names but not invented links. Create and verify child documents first, then prepare a separate section-edit preview that adds their returned links.

## Weekly report

A weekly report has one explicit inclusive period (`start` and `end`, both `YYYY-MM-DD`) and one `as_of` date. It includes:

1. a conclusion for that period;
2. progress against declared goals, with sources;
3. metrics and evidence, or specific pending markers;
4. next-week plans, clearly distinguished from committed work;
5. risks, blockers, and help needed;
6. sources and pending confirmations.

Do not carry a status, count, owner, due date, metric, or risk from an earlier report unless the current source read confirms it.

## Independent preview plan

Create every resource or later home-page link update with its own ordinary Docx preview. Record their dependency order in this local plan:

```yaml
project_name: visible project name
steps:
  - step_id: STEP-001
    resource_key: HOME
    role: project_home | prd | technical_design | meeting_notes | weekly_report | retrospective | other
    resource_type: docx
    operation: create | append | insert | replace
    preview_id: fs-...
    depends_on: []
    source_urls: []
    linked_resource_keys: []
    period:                         # required only for weekly_report
      start: YYYY-MM-DD
      end: YYYY-MM-DD
```

Run `scripts/feishu_guard.py validate-project-preview-plan` before displaying the plan. The validator requires unique preview IDs, backward-only dependencies, and a direct dependency on every newly created resource whose link is added. It validates orchestration only; each preview must still pass `make-preview` and the normal pre-write `validate-preview` gate.

Confirmation remains per preview. A confirmed prerequisite does not confirm its dependents. If a prerequisite fails or cannot be verified, mark dependent steps unattempted and do not create replacement links or report the workspace as complete.
