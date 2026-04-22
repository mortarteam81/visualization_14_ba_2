export interface LibraryStaffPer1000Row {
  reference_year: number | null;
  row_no: number | null;
  university_name: string | null;
  school_type: string | null;
  founding_type: string | null;
  region_name: string | null;
  size_group: string | null;
  regular_staff_certified: number | null;
  regular_staff_not_certified: number | null;
  non_regular_staff_certified: number | null;
  non_regular_staff_not_certified: number | null;
  total_staff_certified: number | null;
  total_staff_not_certified: number | null;
  enrolled_students: number | null;
  library_staff_per_1000_students_original: number | null;
  library_staff_per_1000_students_recalculated: number | null;
  student_count_basis: string | null;
  schema_group: string | null;
  source_file_name: string | null;
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

export const normalizeLibraryStaffPer1000Row = (
  raw: Record<string, unknown>
): LibraryStaffPer1000Row => {
  return {
    reference_year: parseNumberOrNull(raw.reference_year),
    row_no: parseNumberOrNull(raw.row_no),
    university_name: parseStringOrNull(raw.university_name),
    school_type: parseStringOrNull(raw.school_type),
    founding_type: parseStringOrNull(raw.founding_type),
    region_name: parseStringOrNull(raw.region_name),
    size_group: parseStringOrNull(raw.size_group),
    regular_staff_certified: parseNumberOrNull(raw.regular_staff_certified),
    regular_staff_not_certified: parseNumberOrNull(raw.regular_staff_not_certified),
    non_regular_staff_certified: parseNumberOrNull(raw.non_regular_staff_certified),
    non_regular_staff_not_certified: parseNumberOrNull(raw.non_regular_staff_not_certified),
    total_staff_certified: parseNumberOrNull(raw.total_staff_certified),
    total_staff_not_certified: parseNumberOrNull(raw.total_staff_not_certified),
    enrolled_students: parseNumberOrNull(raw.enrolled_students),
    library_staff_per_1000_students_original: parseNumberOrNull(raw.library_staff_per_1000_students_original),
    library_staff_per_1000_students_recalculated: parseNumberOrNull(raw.library_staff_per_1000_students_recalculated),
    student_count_basis: parseStringOrNull(raw.student_count_basis),
    schema_group: parseStringOrNull(raw.schema_group),
    source_file_name: parseStringOrNull(raw.source_file_name),
  };
};

export const calculateLibraryStaffPer1000Students = (
  row: Pick<
    LibraryStaffPer1000Row,
    | "reference_year"
    | "regular_staff_certified"
    | "regular_staff_not_certified"
    | "non_regular_staff_certified"
    | "non_regular_staff_not_certified"
    | "enrolled_students"
  >
): number | null => {
  const year = row.reference_year ?? 0;
  const regularCertified = row.regular_staff_certified ?? 0;
  const regularNotCertified = row.regular_staff_not_certified ?? 0;
  const nonRegularCertified = row.non_regular_staff_certified ?? 0;
  const nonRegularNotCertified = row.non_regular_staff_not_certified ?? 0;
  const students = row.enrolled_students ?? 0;

  if (students <= 0) return null;

  const nonRegularCertifiedWeight = year <= 2024 ? 0.8 : 1.0;

  const weightedStaff =
    regularCertified * 1.0 +
    nonRegularCertified * nonRegularCertifiedWeight +
    regularNotCertified * 0.8 +
    nonRegularNotCertified * 0.5;

  return Number(((weightedStaff / students) * 1000).toFixed(6));
};
