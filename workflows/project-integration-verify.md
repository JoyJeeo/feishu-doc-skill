# Project integration verification workflow

Use within `verify` mode for a cross-resource project workspace.

1. Fix the exact resource set, expected links, dependency order, and supported read scope.
2. Reread every resource completely with `useUAT: true`; resolve Wiki nodes before reading their underlying object.
3. Verify each resource independently before following links or declaring dependents successful.
4. Extract exact observed links from the source content and compare them with the verified target URLs.
5. Record failed and unattempted resources with reasons. Do not execute a dependent write after an unverified prerequisite.
6. Run `scripts/feishu_guard.py validate-project-integration` and report its derived overall status without promotion.

This workflow is read-only. Any corrective change requires a new resource-specific preview and confirmation before returning here for another verification pass.
