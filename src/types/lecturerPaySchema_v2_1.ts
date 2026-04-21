export interface LecturerPayRow {
  reference_year: number | null;
  university_name: string | null;
  school_type: string | null;
  founding_type: string | null;
  region_name: string | null;
  school_status: string | null;
  lecturer_category: string | null;
  payment_category: string | null;
  hourly_pay_rate_krw: number | null;
  paid_lecturer_count: number | null;
  total_lecture_hours: number | null;
  paid_lecturer_ratio_pct: number | null;
}

export const parseNumberOrNull = (value: unknown): number | null => {
  if (value === null || value === undefined || value === "") return null;
  const normalized = String(value).replace(/,/g, "").trim();
  const num = Number(normalized);
  return Number.isFinite(num) ? num : null;
};

export const parseStringOrNull = (value: unknown): string | null => {
  if (value === null || value === undefined) return null;
  const str = String(value).trim();
  return str === "" ? null : str;
};

export const normalizeLecturerPayRow = (
  raw: Record<string, unknown>
): LecturerPayRow => {
  return {
    reference_year: parseNumberOrNull(raw.reference_year),
    university_name: parseStringOrNull(raw.university_name),
    school_type: parseStringOrNull(raw.school_type),
    founding_type: parseStringOrNull(raw.founding_type),
    region_name: parseStringOrNull(raw.region_name),
    school_status: parseStringOrNull(raw.school_status),
    lecturer_category: parseStringOrNull(raw.lecturer_category),
    payment_category: parseStringOrNull(raw.payment_category),
    hourly_pay_rate_krw: parseNumberOrNull(raw.hourly_pay_rate_krw),
    paid_lecturer_count: parseNumberOrNull(raw.paid_lecturer_count),
    total_lecture_hours: parseNumberOrNull(raw.total_lecture_hours),
    paid_lecturer_ratio_pct: parseNumberOrNull(raw.paid_lecturer_ratio_pct),
  };
};
