# Document content generation

Read this reference when drafting a new `docx` document or preparing its creation preview.

## Inputs

Determine the document purpose, audience, document type, source material, required length, terminology, date convention, and required fields. Target location is mandatory for a creation preview; ask for it when neither the request nor personal configuration provides one.

Missing business facts do not block a local draft. Mark them as `[待确认：具体问题]`. Never invent owners, dates, metrics, decisions, sources, user quotes, or implementation status.

## Drafting

1. Choose the closest template from [templates.md](templates.md); use a custom outline only when none fits.
2. Extract a local fact ledger from the supplied material. Keep facts, derived conclusions, recommendations, and unresolved questions distinct.
3. Draft the summary first with the conclusion and intended outcome.
4. Arrange the remaining material into sections with one purpose each. Remove repetition and keep terminology, dates, statuses, and field labels consistent.
5. To compress, remove repetition and secondary explanation before removing decisions or evidence. To expand, add supported reasoning, examples, consequences, or implementation detail without adding new facts.
6. Convert the draft into an ordered block plan. Use the simplest supported block kind that preserves meaning.
7. Run a final fact and completeness pass. List every unresolved item in `pending_confirmations`.

## Output

The local result must contain:

```yaml
title: final document title
template: template name or custom
audience: intended readers
summary: conclusion-first summary
blocks:
  - kind: heading1 | heading2 | text | bullet | ordered | quote | code | table
    content: complete visible content, or structured rows/items
pending_confirmations:
  - unresolved question
```

Do not hide omitted sections or unresolved facts behind generic placeholders. A required empty field must carry a specific pending-confirmation question; an optional irrelevant section should be omitted.
