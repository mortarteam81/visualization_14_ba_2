# library_staff_per_1000_students v6 processing guide

## 계산 규칙
단일 계산 컬럼 `library_staff_per_1000_students_recalculated`만 유지한다.

### 2008~2024
weighted_staff =
(regular_staff_certified * 1.0)
+ (non_regular_staff_certified * 0.8)
+ (regular_staff_not_certified * 0.8)
+ (non_regular_staff_not_certified * 0.5)

library_staff_per_1000_students_recalculated =
weighted_staff / enrolled_students * 1000

### 2025
weighted_staff =
(regular_staff_certified * 1.0)
+ (non_regular_staff_certified * 1.0)
+ (regular_staff_not_certified * 0.8)
+ (non_regular_staff_not_certified * 0.5)

library_staff_per_1000_students_recalculated =
weighted_staff / enrolled_students * 1000
