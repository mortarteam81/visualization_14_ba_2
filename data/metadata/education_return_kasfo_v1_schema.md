# 교육비 환원율 KASFO 원자료 Candidate v1

## Source

- Source system: 사학재정알리미
- Provider: 한국사학진흥재단
- Primary menu: 대학재정데이터
- Supplementary official-value menu: 통계현황 > 테마·이슈통계 > 교육비 환원율
- Raw preservation: `data/raw/kasfo/education_return/original`
- Candidate: `data/conversion_outputs/kasfo/education_return/kasfo_education_return_2016_2025_candidate.csv`
- Official theme issue candidate: `data/conversion_outputs/kasfo/education_return/kasfo_education_return_theme_issue_2020_2025_candidate.csv`
- Official theme issue crosscheck: `data/validation/mismatch_reports/kasfo_education_return_theme_issue_crosscheck.csv`

## Scope

- Candidate only. This file is not promoted to the operating dashboard CSV.
- Source files cover 2015-2024 accounting years and produce 2016-2025 display years.
- Supplementary KASFO theme issue Excel files cover survey years 2020-2025 and match the current operating CSV directly.
- Default validation compares the current dashboard scope: 서울 소재 사립 일반대학.

## Key Columns

| Column | Description |
| --- | --- |
| `accounting_year` | KASFO accounting year |
| `기준년도` | Dashboard display year, accounting year + 1 |
| `학교명` | Canonicalized school name where configured |
| `등록금회계_교육비합계` | Current dashboard verification numerator from school account components |
| `산학협력단회계_교육비합계` | Current dashboard verification numerator from industry-academic cooperation account components |
| `등록금수입` | Tuition revenue denominator |
| `교육비환원율` | `(등록금회계_교육비합계 + 산학협력단회계_교육비합계) / 등록금수입 * 100` |
| `equipment_purchase_recent_5yr_avg` | Recent 5-year average of school-account equipment purchase plus industry equipment acquisition |
| `building_cost_recent_5yr_avg_2_5pct` | Recent 5-year average of school-account building purchase cost multiplied by 2.5% |
| `national_scholarship_type1_dadak_deduction` | Not filled from KASFO; requires Korea Student Aid Foundation source |
| `private_accreditation_formula_partial_rate_pct` | Partial private-university accreditation formula using available KASFO components only |
| `formula_completeness_status` | Source gap flag for missing scholarship deduction |
| `source_file_name` | Raw source files used for the row |

## Known Limitation

The 2026 accreditation formula subtracts 국가장학금 I유형 and 다자녀 국가장학금. The uploaded formula indicates that this component comes from 한국장학재단 or 평가원-requested materials, not KASFO 대학재정데이터. Therefore the KASFO candidate verifies the current dashboard formula and preserves partial accreditation-formula components, but it does not claim the full accreditation formula is complete.

The supplementary KASFO theme issue files are treated as official published
metric values, not as component-level formula proof. They are used to confirm
that the current operating CSV matches KASFO's published education-return-rate
table while the component-level raw financial candidate remains available for
deeper audit.
