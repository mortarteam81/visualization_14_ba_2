export const libraryStaffPer1000Columns = [
  "reference_year",
  "row_no",
  "university_name",
  "school_type",
  "founding_type",
  "region_name",
  "size_group",
  "regular_staff_certified",
  "regular_staff_not_certified",
  "non_regular_staff_certified",
  "non_regular_staff_not_certified",
  "total_staff_certified",
  "total_staff_not_certified",
  "enrolled_students",
  "library_staff_per_1000_students_original",
  "student_count_basis",
  "schema_group",
  "library_staff_per_1000_students_recalculated",
  "library_staff_per_1000_students_recalculated_2025_weighted"
] as const;

export type LibraryStaffPer1000Column = (typeof libraryStaffPer1000Columns)[number];

export const libraryStaffPer1000ColumnLabels: Record<LibraryStaffPer1000Column, string> = {
  "reference_year": "기준연도",
  "row_no": "원본 순번",
  "university_name": "학교명",
  "school_type": "학교유형",
  "founding_type": "설립유형",
  "region_name": "지역",
  "size_group": "대학규모",
  "regular_staff_certified": "정규직(사서자격증소지자)",
  "regular_staff_not_certified": "정규직(사서자격증미소지자)",
  "non_regular_staff_certified": "비정규직(사서자격증소지자)",
  "non_regular_staff_not_certified": "비정규직(사서자격증미소지자)",
  "total_staff_certified": "사서자격증소지자 합계",
  "total_staff_not_certified": "사서자격증미소지자 합계",
  "enrolled_students": "재학생수",
  "library_staff_per_1000_students_original": "재학생 1,000명당 직원수(원자료)",
  "library_staff_per_1000_students_recalculated": "재학생 1,000명당 직원수(재계산)",
  "library_staff_per_1000_students_recalculated_2025_weighted": "재학생 1,000명당 직원수(2025 가중치 재계산)",
  "student_count_basis": "재학생수 기준",
  "schema_group": "구조 구간",
  "source_file_name": "원본 파일명"
};

export const numericColumns: LibraryStaffPer1000Column[] = [
  "reference_year","row_no","regular_staff_certified","regular_staff_not_certified","non_regular_staff_certified",
  "non_regular_staff_not_certified","total_staff_certified","total_staff_not_certified","enrolled_students",
  "library_staff_per_1000_students_original","library_staff_per_1000_students_recalculated",
  "library_staff_per_1000_students_recalculated_2025_weighted"
];

export const dimensionColumns: LibraryStaffPer1000Column[] = [
  "university_name","school_type","founding_type","region_name","size_group","student_count_basis","schema_group","source_file_name"
];

export const defaultVisibleColumns: LibraryStaffPer1000Column[] = [
  "reference_year","university_name","school_type","founding_type","region_name",
  "total_staff_certified","total_staff_not_certified","enrolled_students",
  "library_staff_per_1000_students_recalculated"
];
