# Project workspace preview workflow

Use within `preview` mode for a project home, project document set, or weekly report.

1. Read the project audit and workspace models, then the common preview and Docx creation rules.
2. Fix the exact project root, requested document set, reporting period, source roots, and existing-versus-new resources. Do not infer a standard document set.
3. Read all declared sources with `useUAT: true`, build the evidence map, and run `validate-project-audit`.
4. Draft each requested Docx separately. Keep exact source links, pending confirmations, and the complete visible block plan in that resource's preview.
5. Use the Wiki-hosted project home as the project directory. If it does not exist, prepare only its creation preview first; dependent child previews require the returned and verified parent link.
6. After the home exists, prepare one `docx` creation preview per requested child document through [docx-create-preview.md](docx-create-preview.md). Display and confirm each preview independently.
7. Add links for newly created documents to the project home only after their exact links resolve. Use a separate section-edit preview and declare every linked document step as a dependency.
8. For a weekly report, lock the inclusive reporting period and cite the current source for each factual statement. Keep missing metrics or register data as pending confirmation.
9. Build the ordered project preview plan and run `scripts/feishu_guard.py validate-project-preview-plan`. Stop dependents after any prerequisite failure or unverified result.
10. Show the locally viewable effect confirmation for the next executable resource and stop. A project-level authorization or another resource's confirmation never authorizes this write.

This workflow performs no remote writes. Apply and verify only the one confirmed preview, then recalculate which dependent preview can be generated from the new state.
