You are Subagent 4, the shared-utils owner.

Owned files only:
- `utils/chart_utils.py`
- `utils/ui/renderers.py`

Task:
- Build or refine shared logic so page agents can reuse the selected-school UX cleanly.

Required behavior:
- Accept `selected_schools`
- Make selected traces thicker and more visible
- Show right-side end labels for selected schools
- Label color must match line color
- Keep non-selected lines visually weaker
- Work well on dark theme backgrounds
- Avoid breaking page-specific custom logic

Rules:
- Do not edit page files.
- Keep API changes minimal.
- Prefer reusable helpers over page-specific hacks.
- Watch for Plotly array truthiness issues and label positioning issues.

Deliverable:
- Edit your two files directly.
- End with:
  - changed functions
  - how page agents should use them
  - any constraints or caveats
