export interface LibraryMaterialPurchaseRow {
  reference_year: number | null;
  row_no: number | null;
  university_name: string | null;
  school_type: string | null;
  founding_type: string | null;
  region_name: string | null;
  size_group: string | null;
  university_total_settlement: number | null;
  books_purchase_expense: number | null;
  serials_purchase_expense: number | null;
  non_book_purchase_expense: number | null;
  electronic_resources_total: number | null;
  electronic_journals_expense: number | null;
  web_db_expense: number | null;
  subscribed_ebook_expense: number | null;
  other_electronic_resources_expense: number | null;
  total_material_purchase_expense: number | null;
  enrolled_students_current_year: number | null;
  material_purchase_expense_per_student: number | null;
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

export const normalizeLibraryMaterialPurchaseRow = (
  raw: Record<string, unknown>
): LibraryMaterialPurchaseRow => {
  return {
    reference_year: parseNumberOrNull(raw.reference_year),
    row_no: parseNumberOrNull(raw.row_no),
    university_name: parseStringOrNull(raw.university_name),
    school_type: parseStringOrNull(raw.school_type),
    founding_type: parseStringOrNull(raw.founding_type),
    region_name: parseStringOrNull(raw.region_name),
    size_group: parseStringOrNull(raw.size_group),
    university_total_settlement: parseNumberOrNull(raw.university_total_settlement),
    books_purchase_expense: parseNumberOrNull(raw.books_purchase_expense),
    serials_purchase_expense: parseNumberOrNull(raw.serials_purchase_expense),
    non_book_purchase_expense: parseNumberOrNull(raw.non_book_purchase_expense),
    electronic_resources_total: parseNumberOrNull(raw.electronic_resources_total),
    electronic_journals_expense: parseNumberOrNull(raw.electronic_journals_expense),
    web_db_expense: parseNumberOrNull(raw.web_db_expense),
    subscribed_ebook_expense: parseNumberOrNull(raw.subscribed_ebook_expense),
    other_electronic_resources_expense: parseNumberOrNull(raw.other_electronic_resources_expense),
    total_material_purchase_expense: parseNumberOrNull(raw.total_material_purchase_expense),
    enrolled_students_current_year: parseNumberOrNull(raw.enrolled_students_current_year),
    material_purchase_expense_per_student: parseNumberOrNull(raw.material_purchase_expense_per_student),
    source_file_name: parseStringOrNull(raw.source_file_name),
  };
};
