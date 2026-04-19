You are the master agent for this Streamlit dashboard repo.

Goal:
- Apply the chart readability and selected-school UX from `pages/1_법정부담금_부담율.py` to:
  - `pages/2_전임교원_확보율.py`
  - `pages/3_연구비_수혜실적.py`
  - `pages/4_논문실적.py`
  - `pages/5_졸업생_진로_성과.py`
  - `pages/6_세입_중_등록금_비율.py`
  - `pages/7_세입_중_기부금_비율.py`

Target UX:
- Default school stays `성신여자대학교`
- Selected school line is thicker and easier to see
- Selected school name appears at the right side of the chart
- Label color matches the line color
- Non-selected lines are visually weaker
- Dark theme contrast stays strong
- Use shared utilities where possible

Execution plan:
1. Review shared logic in:
   - `utils/chart_utils.py`
   - `utils/ui/renderers.py`
2. Delegate with strict file ownership:
   - Subagent 1: `pages/2_전임교원_확보율.py`, `pages/5_졸업생_진로_성과.py`
   - Subagent 2: `pages/3_연구비_수혜실적.py`, `pages/4_논문실적.py`
   - Subagent 3: `pages/6_세입_중_등록금_비율.py`, `pages/7_세입_중_기부금_비율.py`
   - Subagent 4: `utils/chart_utils.py`, `utils/ui/renderers.py`
3. Integrate results without reverting user changes.
4. Verify:
   - default selection
   - selected-school highlight
   - right-side label
   - label color matches line color
   - no syntax errors
5. Report:
   - summary
   - changed files
   - verification
   - remaining risks

Rules:
- Reuse shared code first.
- Do not let page agents modify shared utils.
- Do not let shared-utils agent modify page files.
- Preserve existing page-specific custom logic where needed.
