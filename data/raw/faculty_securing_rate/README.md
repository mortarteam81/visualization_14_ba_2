# 교원확보율 원자료

## 위치

- 원자료: `data/raw/faculty_securing_rate/original`
- 변환 스크립트: `scripts/build_faculty_securing_rate.py`

## 원자료 관리 규칙

- `2015년교원확보율.xlsx`부터 `2025년교원확보율.xlsx`까지 실제 원자료 11개만 처리한다.
- `~$`로 시작하는 Excel 임시 잠금 파일은 처리하지 않는다.
- 원자료 파일명은 연도 추출에 사용하므로 4자리 연도를 유지한다.

## 재생성 명령

```bash
python scripts/build_faculty_securing_rate.py
```

## 산출물

- 상세 CSV: `data/processed/faculty_securing_rate/faculty_securing_rate_2015_2025_v1_utf8.csv`
- 업로드용 총계 CSV: `data/processed/faculty_securing_rate/faculty_securing_rate_total_2015_2025_v1_utf8.csv`
- Long metric CSV: `data/processed/faculty_securing_rate/faculty_securing_metric_values_2015_2025_v1_utf8.csv`
- 스키마: `data/metadata/faculty_securing_rate_v1_schema.md`
- 출처: `data/metadata/faculty_securing_rate_v1.source.json`
- 처리 보고서: `data/metadata/faculty_securing_rate_v1.processing_report.json`
