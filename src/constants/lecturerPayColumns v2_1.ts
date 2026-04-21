export const lecturerPayColumns = [
  "reference_year",
  "university_name",
  "school_type",
  "founding_type",
  "region_name",
  "school_status",
  "lecturer_category",
  "payment_category",
  "hourly_pay_rate_krw",
  "paid_lecturer_count",
  "total_lecture_hours",
  "paid_lecturer_ratio_pct",
] as const;

export type LecturerPayColumn =
  (typeof lecturerPayColumns)[number];

export const lecturerPayColumnLabels: Record<LecturerPayColumn, string> = {
  reference_year: "기준연도",
  university_name: "학교",
  school_type: "학교종류/학종",
  founding_type: "설립구분",
  region_name: "지역",
  school_status: "상태",
  lecturer_category: "강사구분",
  payment_category: "구분",
  hourly_pay_rate_krw: "시간당 지급기준 단가(원)",
  paid_lecturer_count: "지급인원수",
  total_lecture_hours: "총 강의시간 수",
  paid_lecturer_ratio_pct: "지급인원비율(%)",
};

export const numericColumns: LecturerPayColumn[] = [
  "reference_year",
  "hourly_pay_rate_krw",
  "paid_lecturer_count",
  "total_lecture_hours",
  "paid_lecturer_ratio_pct",
];

export const dimensionColumns: LecturerPayColumn[] = [
  "university_name",
  "school_type",
  "founding_type",
  "region_name",
  "school_status",
  "lecturer_category",
  "payment_category",
];

export const defaultVisibleColumns: LecturerPayColumn[] = [
  "reference_year",
  "university_name",
  "school_type",
  "founding_type",
  "lecturer_category",
  "hourly_pay_rate_krw",
  "paid_lecturer_count",
  "paid_lecturer_ratio_pct",
];