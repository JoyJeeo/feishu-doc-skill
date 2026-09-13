# Document templates

Use these as minimum block-level structures, not fixed prose. The document title is metadata and should not be repeated as the first heading.

## PRD

1. `quote` — product conclusion and current decision state.
2. `heading1` — Background and problem.
3. `heading1` — Goals and non-goals.
4. `heading1` — Users and scenarios.
5. `heading1` — Requirements, using a table or ordered list with IDs and acceptance criteria.
6. `heading1` — Interaction and edge cases.
7. `heading1` — Metrics and acceptance.
8. `heading1` — Dependencies and risks.
9. `heading1` — Pending confirmations.

## Meeting notes

1. `quote` — meeting conclusion.
2. `heading1` — Metadata: date, attendees, topic, and source.
3. `heading1` — Agenda and key discussion.
4. `heading1` — Decisions, each with rationale when known.
5. `heading1` — Action items, using a table with item, owner, due date, and status.
6. `heading1` — Risks and blockers.
7. `heading1` — Pending confirmations.

## Project home

1. `quote` — current project state and `as_of` date, with a source or pending marker.
2. `heading1` — Goal and scope.
3. `heading1` — Status and milestones, with source links.
4. `heading1` — Roles and contacts.
5. `heading1` — Key documents and exact links; planned documents without resolved links remain pending.
6. `heading1` — Action items and risks, with source links or pending markers.
7. `heading1` — Decisions, with source links.
8. `heading1` — Sources.
9. `heading1` — Pending confirmations.

## Weekly report

1. `quote` — conclusion for the explicit inclusive reporting period.
2. `heading1` — Reporting period and `as_of` date.
3. `heading1` — Progress against goals, with source links.
4. `heading1` — Metrics and evidence, or specific pending markers.
5. `heading1` — Next-week plan, separated from committed work.
6. `heading1` — Risks and blockers, with source links.
7. `heading1` — Help needed.
8. `heading1` — Sources.
9. `heading1` — Pending confirmations.

## Technical design

1. `quote` — chosen design and expected result.
2. `heading1` — Context and constraints.
3. `heading1` — Goals and non-goals.
4. `heading1` — Current state.
5. `heading1` — Design, including flow, data, interfaces, and key tradeoffs as needed.
6. `heading1` — Compatibility, migration, and rollback.
7. `heading1` — Verification and acceptance.
8. `heading1` — Risks.
9. `heading1` — Pending confirmations.

## Retrospective

1. `quote` — outcome and primary lesson.
2. `heading1` — Goal and result.
3. `heading1` — Timeline and evidence.
4. `heading1` — What worked.
5. `heading1` — What did not work and root causes.
6. `heading1` — Actions, using a table with owner and due date.
7. `heading1` — Follow-up checks.
8. `heading1` — Pending confirmations.

## Field rules

- Omit irrelevant optional sections; keep required sections with explicit `[待确认：...]` markers when facts are missing.
- Treat source facts, derived conclusions, and recommendations as different statements.
- Do not place a decision under actions, or a proposal under completed work.
- Use tables only for genuinely repeated fields. Use lists for ordinary parallel items.
