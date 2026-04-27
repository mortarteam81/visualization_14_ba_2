# 2026-04-26 로그인/권한/Neon 연동 작업 정리

## 현재 상태

- Streamlit 기반 대학 경영 인사이트 대시보드에 Google OIDC 로그인과 DB 기반 접근 제어를 적용했다.
- 최신 구현 커밋 `4318a4f`는 `origin/main`에 푸쉬 완료했다.
- 로컬에서 Google 로그인, Neon DB 연결, 운영자 계정 접근, 사용자 관리 화면, 로그아웃 버튼 동작을 확인했다.
- 전체 테스트는 `214 passed, 1 warning` 상태다.
- 실제 OAuth client secret, cookie secret, Neon connection string, 사용자 이메일 원문은 Git에 포함하지 않았다.

## 구현 내용

### 인증/권한

- `utils/auth.py`를 추가해 `require_authenticated_user()` 인증 가드를 구현했다.
- 모든 Streamlit entrypoint가 `st.set_page_config()` 직후 인증 가드를 호출한다.
- Google OIDC `st.login` / `st.user` 기반으로 로그인 이메일을 식별한다.
- Neon DB의 `app_users` allowlist에서 활성 사용자만 통과시킨다.
- 권한은 `admin` / `viewer` 2단계다.
- 로그인 후 사이드바에 현재 계정, 권한, 로그아웃 버튼을 표시한다.

### Neon DB

- `utils/app_db.py`를 추가해 앱 DB bootstrap과 사용자 저장소를 구현했다.
- 앱 시작 시 `CREATE TABLE IF NOT EXISTS`로 아래 테이블을 준비한다.
  - `app_users`
  - `comparison_profiles`
- `[app_auth].initial_admin_emails`에 설정한 이메일은 항상 active admin으로 upsert한다.
- `utils/profile_db.py`를 추가해 비교대학 설정을 Neon DB에 저장하도록 구현했다.

### 비교대학 설정

- `pages/00_비교대학_설정.py`를 설정 허브로 확장했다.
- 모든 로그인 사용자는 “내 비교군”을 저장할 수 있다.
- `admin`만 “운영자 기본 비교군”과 “사용자 관리” 탭을 볼 수 있다.
- 사용자 관리 탭에서 접근 허용 이메일 등록, 표시 이름 변경, 권한 변경, 활성/비활성 변경이 가능하다.
- 초기 운영자와 현재 로그인한 본인의 권한/활성 상태는 보호된다.
- 지표 페이지의 기본 비교군 적용 순서는 `user profile -> system default -> 코드 기본값`이다.
- 기존 로컬 파일 저장 방식은 fallback으로 유지했다.

### 의존성/호환성

- `requirements.txt`에 인증/DB 의존성을 추가했다.
  - `streamlit>=1.50.0`
  - `Authlib>=1.3.2,<1.4`
  - `sqlalchemy>=2.0.0`
  - `psycopg2-binary>=2.9.9`
- `Authlib 1.6.x`에서는 Streamlit 1.50 OIDC flow와 맞지 않아 `NoneType` state 오류가 발생했다.
- 호환을 위해 `Authlib>=1.3.2,<1.4`로 고정했다.

### Secrets

- 실제 `.streamlit/secrets.toml`은 Git에 포함하지 않는다.
- `.streamlit/secrets.example.toml`만 placeholder 예시로 커밋했다.
- 로컬 secrets와 Streamlit Cloud secrets는 별도 저장소다.
- Streamlit Cloud에 배포할 때는 Cloud 앱 Settings의 Secrets에 동일한 구조를 직접 입력해야 한다.

필요한 secrets 구조:

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "replace-with-a-long-random-secret"
client_id = "replace-with-google-oauth-client-id"
client_secret = "replace-with-google-oauth-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[connections.neon]
url = "replace-with-neon-postgres-connection-string"

[app_auth]
initial_admin_emails = ["admin@example.com"]
```

## 오늘 확인한 것

- Google Cloud OAuth client를 로컬 테스트용으로 구성했다.
- Neon Free 프로젝트를 만들고 production connection string을 로컬 secrets에 설정했다.
- Neon 실제 접속, `SELECT 1`, `app_users`/`comparison_profiles` 테이블 생성 확인을 완료했다.
- 초기 운영자 1명이 `app_users`에 active admin으로 등록되는 것을 확인했다.
- Streamlit 로컬 앱에서 DB 오류 없이 대시보드 진입을 확인했다.
- 사용자 관리 탭과 로그아웃 버튼이 보이는 것을 확인했다.
- 실제 secret, OAuth 값, Neon URL, 사용자 원문 정보는 문서/커밋에 남기지 않았다.

## GitHub 반영

- 푸쉬 대상: `origin/main`
- 최신 커밋: `4318a4f Add Streamlit auth and Neon profile storage`
- 이전 기준 커밋: `dda2084`
- 현재 로컬 `main`은 `origin/main`과 동기화된 상태에서 이 문서를 추가했다.

## 로컬 네트워크 접속 메모

Streamlit Cloud에 배포하지 않고, 로컬 Mac에서 서버를 띄운 뒤 같은 네트워크 기기에서 접속하는 것도 가능하다.

주의할 점:

- 접속 기기와 서버 Mac이 같은 네트워크에 있어야 한다.
- Mac 방화벽이 Streamlit 포트 접근을 막지 않아야 한다.
- 서버 Mac이 잠자기 상태가 되면 접속할 수 없다.
- Google OIDC를 네트워크 주소로 테스트하려면 아래 두 곳이 같은 redirect URI를 사용해야 한다.
  - 로컬 `.streamlit/secrets.toml`의 `[auth].redirect_uri`
  - Google Cloud OAuth client의 Authorized redirect URI
- 네트워크 접속용 redirect URI 형식은 `http://<LAN-IP>:8501/oauth2callback`이다.
- 이 값도 로컬 설정값이며 Git에 커밋하지 않는다.

## Streamlit Cloud 배포 시 해야 할 일

1. Streamlit Cloud에서 GitHub repo `mortarteam81/visualization_14_ba_2`의 `main` 브랜치로 앱을 만든다.
2. Cloud Secrets에 `[auth]`, `[connections.neon]`, `[app_auth]`를 입력한다.
3. `[auth].redirect_uri`는 Cloud 앱 주소 기준으로 설정한다.
   - 예: `https://<app-name>.streamlit.app/oauth2callback`
4. Google Cloud OAuth client에도 같은 Cloud redirect URI를 추가한다.
5. Streamlit Cloud Sharing을 “Only specific people can view this app”으로 설정한다.
6. Cloud에서도 같은 Neon DB URL을 쓰면 기존 운영자/사용자/비교군 데이터가 이어진다.
7. 배포 후 확인한다.
   - 운영자 로그인
   - 사용자 관리 탭 접근
   - viewer 계정 등록 및 로그인 차단/허용 흐름
   - 운영자 기본 비교군 저장
   - 개인 비교군 저장

## 내일 이어서 할 작업 후보

### 우선순위 높음

- Streamlit Cloud 배포 진행
- Cloud Secrets 설정
- Cloud 앱 URL 기준 Google OAuth redirect URI 추가
- Cloud private sharing 설정
- 운영자/사용자 로그인 smoke test

### 다음 구현 후보

- `student_recruitment` 지표 구현
- 사용자 관리 UX 개선
  - 사용자 검색/필터
  - 최근 로그인 기준 정렬
  - 비활성 사용자 표시 개선
- 비교군 저장 UX 개선
  - 저장 성공 후 현재 적용 프로필 표시
  - system default와 user profile의 적용 출처 표시
- 배포 문서 정리
  - Streamlit Cloud 설정 절차
  - 로컬 네트워크 테스트 절차
  - Google OAuth redirect URI 체크리스트

### 확인하면 좋은 리스크

- Streamlit Cloud에서 Python 버전과 `Authlib>=1.3.2,<1.4` 설치 호환성 확인
- Cloud Secrets TOML 문법 오류 여부 확인
- Google OAuth consent screen의 테스트/프로덕션 상태 확인
- Cloud app private sharing과 앱 내부 allowlist가 기대대로 이중 방어로 동작하는지 확인
- Neon Free의 scale-to-zero 이후 첫 접속 지연이 사용자 경험에 미치는 영향 확인

## 종료 메모

- 오늘 작업의 핵심은 “GitHub에는 코드만, secrets는 로컬/Cloud Secrets에, 운영 데이터는 Neon DB에”로 책임을 분리한 것이다.
- 내일은 배포 환경에서 같은 구조가 재현되는지 확인하면 된다.
