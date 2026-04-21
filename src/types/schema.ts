export interface EducationCostReturnRateRow {
  survey_year: number | null;
  university_name: string | null;
  school_level: string | null;
  school_type: string | null;
  region: string | null;
  row_no: number | null;

  tuition_salary: number | null;
  tuition_admin: number | null;
  tuition_research_student: number | null;
  tuition_books: number | null;
  tuition_equipment: number | null;
  tuition_scholarship: number | null;
  tuition_admissions: number | null;
  tuition_account_total: number | null;

  industry_project_cost: number | null;
  industry_support_project_cost: number | null;
  industry_indirect_project_cost: number | null;
  industry_general_admin: number | null;
  industry_equipment: number | null;
  industry_account_total: number | null;

  tuition_revenue: number | null;
  education_cost_return_rate_original_pct: number | null;
  education_cost_return_rate_recalculated_pct: number | null;

  source_file_name: string | null;
}

export const parseNumberOrNull = (value: unknown): number | null => {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const normalized = String(value).replace(/,/g, "").trim();
  const num = Number(normalized);

  return Number.isFinite(num) ? num : null;
};

export const parseStringOrNull = (value: unknown): string | null => {
  if (value === null || value === undefined) {
    return null;
  }

  const str = String(value).trim();
  return str === "" ? null : str;
};

export const normalizeEducationCostReturnRateRow = (
  raw: Record<string, unknown>
): EducationCostReturnRateRow => {
  return {
    survey_year: parseNumberOrNull(raw.survey_year),
    university_name: parseStringOrNull(raw.university_name),
    school_level: parseStringOrNull(raw.school_level),
    school_type: parseStringOrNull(raw.school_type),
    region: parseStringOrNull(raw.region),
    row_no: parseNumberOrNull(raw.row_no),

    tuition_salary: parseNumberOrNull(raw.tuition_salary),
    tuition_admin: parseNumberOrNull(raw.tuition_admin),
    tuition_research_student: parseNumberOrNull(raw.tuition_research_student),
    tuition_books: parseNumberOrNull(raw.tuition_books),
    tuition_equipment: parseNumberOrNull(raw.tuition_equipment),
    tuition_scholarship: parseNumberOrNull(raw.tuition_scholarship),
    tuition_admissions: parseNumberOrNull(raw.tuition_admissions),
    tuition_account_total: parseNumberOrNull(raw.tuition_account_total),

    industry_project_cost: parseNumberOrNull(raw.industry_project_cost),
    industry_support_project_cost: parseNumberOrNull(raw.industry_support_project_cost),
    industry_indirect_project_cost: parseNumberOrNull(raw.industry_indirect_project_cost),
    industry_general_admin: parseNumberOrNull(raw.industry_general_admin),
    industry_equipment: parseNumberOrNull(raw.industry_equipment),
    industry_account_total: parseNumberOrNull(raw.industry_account_total),

    tuition_revenue: parseNumberOrNull(raw.tuition_revenue),
    education_cost_return_rate_original_pct: parseNumberOrNull(raw.education_cost_return_rate_original_pct),
    education_cost_return_rate_recalculated_pct: parseNumberOrNull(raw.education_cost_return_rate_recalculated_pct),

    source_file_name: parseStringOrNull(raw.source_file_name),
  };
};

export const calculateEducationCostReturnRate = (
  row: Pick<EducationCostReturnRateRow, "tuition_account_total" | "industry_account_total" | "tuition_revenue">
): number | null => {
  const tuitionTotal = row.tuition_account_total ?? 0;
  const industryTotal = row.industry_account_total ?? 0;
  const revenue = row.tuition_revenue ?? 0;

  if (revenue <= 0) return null;

  return Number((((tuitionTotal + industryTotal) / revenue) * 100).toFixed(1));
};

export const hasRateMismatch = (
  row: Pick<EducationCostReturnRateRow, "education_cost_return_rate_original_pct" | "education_cost_return_rate_recalculated_pct">,
  tolerance = 0.1
): boolean => {
  if (
    row.education_cost_return_rate_original_pct === null ||
    row.education_cost_return_rate_recalculated_pct === null
  ) return false;

  return (
    Math.abs(
      row.education_cost_return_rate_original_pct -
      row.education_cost_return_rate_recalculated_pct
    ) > tolerance
  );
};
