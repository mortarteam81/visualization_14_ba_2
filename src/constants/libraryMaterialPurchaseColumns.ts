export const libraryMaterialPurchaseColumns = [
  "reference_year",
  "row_no",
  "university_name",
  "school_type",
  "founding_type",
  "region_name",
  "size_group",
  "university_total_settlement",
  "books_purchase_expense",
  "serials_purchase_expense",
  "non_book_purchase_expense",
  "electronic_resources_total",
  "electronic_journals_expense",
  "web_db_expense",
  "subscribed_ebook_expense",
  "other_electronic_resources_expense",
  "total_material_purchase_expense",
  "enrolled_students_current_year",
  "material_purchase_expense_per_student",
  "source_file_name"
] as const;

export type LibraryMaterialPurchaseColumn =
  (typeof libraryMaterialPurchaseColumns)[number];

export const libraryMaterialPurchaseColumnLabels: Record<LibraryMaterialPurchaseColumn, string> = {
  "reference_year": "기준연도",
  "row_no": "원본 순번",
  "university_name": "학교명",
  "school_type": "학교유형",
  "founding_type": "설립유형",
  "region_name": "지역",
  "size_group": "규모그룹",
  "university_total_settlement": "대학총결산",
  "books_purchase_expense": "도서자료 구입비",
  "serials_purchase_expense": "연속간행물 구입비",
  "non_book_purchase_expense": "비도서자료 구입비",
  "electronic_resources_total": "전자자료 구입비",
  "electronic_journals_expense": "전자저널",
  "web_db_expense": "웹DB",
  "subscribed_ebook_expense": "[구독] e-book",
  "other_electronic_resources_expense": "기타 전자자료",
  "total_material_purchase_expense": "자료구입비계",
  "enrolled_students_current_year": "재학생수(당해년도)",
  "material_purchase_expense_per_student": "재학생 1인당 자료구입비(결산)",
  "source_file_name": "원본 파일명"
};

export const numericColumns: LibraryMaterialPurchaseColumn[] = [
  "reference_year",
  "row_no",
  "university_total_settlement",
  "books_purchase_expense",
  "serials_purchase_expense",
  "non_book_purchase_expense",
  "electronic_resources_total",
  "electronic_journals_expense",
  "web_db_expense",
  "subscribed_ebook_expense",
  "other_electronic_resources_expense",
  "total_material_purchase_expense",
  "enrolled_students_current_year",
  "material_purchase_expense_per_student"
];

export const dimensionColumns: LibraryMaterialPurchaseColumn[] = [
  "university_name",
  "school_type",
  "founding_type",
  "region_name",
  "size_group",
  "source_file_name"
];

export const defaultVisibleColumns: LibraryMaterialPurchaseColumn[] = [
  "reference_year",
  "university_name",
  "school_type",
  "founding_type",
  "region_name",
  "total_material_purchase_expense",
  "enrolled_students_current_year",
  "material_purchase_expense_per_student"
];
