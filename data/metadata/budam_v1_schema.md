# 법정부담금 부담율 v1 Schema

## Source

- Source: 대학알리미 공시데이터 추이
- Item: `14-바-2. 법정부담금 부담 현황_대학_법정부담금 부담률`
- Raw file: `data/raw/academyinfo/budam/original/14-바-2. 법정부담금 부담 현황_대학_법정부담금 부담률.xlsx`
- Candidate output: `data/conversion_outputs/academyinfo/budam/budam_2011_2024_candidate.csv`

## Candidate Columns

| Column | Meaning |
| --- | --- |
| `기준년도` | 법정부담금 부담 현황 기준년도 |
| `학교명` | 학교명, 기본 분석 scope alias 기준으로 정규화 |
| `부담율` | 법정부담금 기준액 대비 법정부담금 부담액 비율 |

## Formula

- `부담율 = 법정부담금부담액 / 법정부담금기준액 * 100`
- 대학알리미 원자료와 동일하게 소수점 1자리 half-up 반올림을 사용한다.
- 기준액과 부담액이 모두 0인 경우 부담율은 0으로 처리한다.

## Promotion Policy

이 schema는 후보 데이터 검증용이다. 운영 CSV인 `data/법정부담금_부담율.csv`는 자동 교체하지 않는다.
