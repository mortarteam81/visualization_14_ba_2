"""Source acquisition metadata for first-wave pending metrics.

The records here document what has been verified from public source pages.  They
separate raw-first acquisition from API-refresh acquisition so implementation can
avoid premature API coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal


SourceKind = Literal["file", "api", "web-indicator"]
AuthMode = Literal["none", "service-key", "web-session-unknown"]


@dataclass(frozen=True)
class SourceAcquisitionSpec:
    metric_id: str
    purpose: Literal["raw-first", "api-refresh"]
    source_name: str
    url: str
    kind: SourceKind
    format: str
    auth: AuthMode
    verified_fields: tuple[str, ...]
    caveats: tuple[str, ...] = ()


FIRST_WAVE_SOURCE_ACQUISITION: Final[tuple[SourceAcquisitionSpec, ...]] = (
    SourceAcquisitionSpec(
        metric_id="student_recruitment",
        purpose="raw-first",
        source_name="교육부_대학알리미_대학주요정보_학생_교원_연구_재정_교육여건",
        url="https://www.data.go.kr/data/15118998/fileData.do",
        kind="file",
        format="XLSX",
        auth="none",
        verified_fields=(
            "공시년도",
            "학교명",
            "본분교명",
            "학교종류",
            "학교유형",
            "설립유형",
            "지역명",
            "입학정원(학부)",
            "재학생(학부)",
            "신입생경쟁률(학부)",
            "신입생 충원율(학부)",
        ),
        caveats=(
            "재학생 충원율은 이 XLSX 설명에서 직접 확인되지 않아 학생 현황 API/원자료 보강 필요.",
            "제공 URL은 academyinfo.go.kr 다운로드 화면으로 연결된다.",
            "실제 공개 화면 데이터 엔드포인트는 https://www.academyinfo.go.kr/main/main2130/selectSchlList.do 로 확인됨.",
        ),
    ),
    SourceAcquisitionSpec(
        metric_id="student_recruitment",
        purpose="api-refresh",
        source_name="한국대학교육협의회 대학정보공시 학생 현황",
        url="https://www.data.go.kr/data/15037346/openapi.do",
        kind="api",
        format="XML REST",
        auth="service-key",
        verified_fields=(
            "신입생 충원율",
            "재학생 충원율",
            "재학생수",
            "재적학생수",
            "졸업자 수",
            "취업자 수",
            "schlId",
            "svyYr",
        ),
        caveats=(
            "ServiceKey 필수.",
            "개발/운영 활용승인은 자동승인으로 표시됨.",
        ),
    ),
    SourceAcquisitionSpec(
        metric_id="staff_per_student",
        purpose="raw-first",
        source_name="교육부_대학알리미_대학주요정보_학생_교원_연구_재정_교육여건",
        url="https://www.data.go.kr/data/15118998/fileData.do",
        kind="file",
        format="XLSX",
        auth="none",
        verified_fields=(
            "공시년도",
            "학교명",
            "본분교명",
            "설립유형",
            "지역명",
            "재학생(학부)",
        ),
        caveats=(
            "실제 확인한 대학주요정보 화면 엔드포인트에는 직원총계 컬럼이 없었다.",
            "직원 1인당 학생수 구현에는 직원 현황 원자료를 별도 확보해야 한다.",
            "확인된 공개 화면 데이터 엔드포인트는 https://www.academyinfo.go.kr/main/main2130/selectSchlList.do 이다.",
        ),
    ),
    SourceAcquisitionSpec(
        metric_id="scholarship_ratio",
        purpose="raw-first",
        source_name="한국장학재단_대학별 장학금 수혜 현황",
        url="https://www.data.go.kr/data/15038576/fileData.do",
        kind="file",
        format="CSV",
        auth="none",
        verified_fields=(
            "교내장학금",
            "교외장학금",
            "재원구분",
            "성격유형",
            "조사연도",
            "기준연도",
        ),
        caveats=(
            "파일데이터는 로그인 없이 다운로드 가능하다고 표시됨.",
            "등록금 수입 분모는 별도 재정 원자료 또는 대학재정알리미 지표와 결합 필요.",
        ),
    ),
    SourceAcquisitionSpec(
        metric_id="scholarship_ratio",
        purpose="api-refresh",
        source_name="한국장학재단_대학별 장학금 수혜 현황 자동변환 API",
        url="https://www.data.go.kr/data/15038576/fileData.do",
        kind="api",
        format="XML/JSON",
        auth="service-key",
        verified_fields=(
            "교내장학금",
            "교외장학금",
            "재원구분",
            "성격유형",
        ),
        caveats=(
            "API는 공공데이터포털 회원가입 및 활용신청 필요.",
            "파일 원문과 API 자동변환 스키마 차이를 비교해야 한다.",
        ),
    ),
    SourceAcquisitionSpec(
        metric_id="corp_transfer_ratio",
        purpose="raw-first",
        source_name="한국사학진흥재단 대학재정알리미 대학재정 주요 지표",
        url="https://uniarlimi.kasfo.or.kr/statistics/indicator",
        kind="web-indicator",
        format="web table / possible excel download",
        auth="web-session-unknown",
        verified_fields=(
            "법인전입금 비율",
            "법인책무성",
            "법인의 대학에 대한 재정기여도",
        ),
        caveats=(
            "직접 지표는 확인됨.",
            "엑셀 다운로드 요청 방식과 자동화 가능 여부는 브라우저 기반 추가 확인 필요.",
            "API-refresh 경로는 아직 확인되지 않음.",
        ),
    ),
)


__all__ = [
    "FIRST_WAVE_SOURCE_ACQUISITION",
    "SourceAcquisitionSpec",
]
