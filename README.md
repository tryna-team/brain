# 🧠 tryna brain

> 일정을 이해하고 맥락을 연결해 필요한 준비·실행 항목을 추천하는 FastAPI 기반 분석 서버

tryna brain은 tryna 서비스의 일정 파싱 및 추천 전용 서버입니다. Spring 서버와 역할을 분리하여 자연어 일정 파싱, Neo4j 기반 의미 매핑과 후보 조회, Upstage 기반 임베딩 및 추천 문구 정제를 담당합니다.

---

## 📌 소개

tryna는 사용자가 입력한 짧은 일정의 맥락을 이해하고, 일정 전후에 필요한 할 일을 제안하는 일정 서비스입니다.

tryna brain은 다음 두 기능을 제공합니다.

- 자연어 일정에서 날짜, 시간, 장소 등 일정 후보 정보 추출
- 일정 유형·맥락·장소를 분석하여 준비 및 실행 항목 추천

예를 들어 사용자가 다음과 같이 입력하면:

```text
금요일 3시 팀플 회의
```

파싱 API는 다음과 같이 일정 후보 정보를 반환합니다.

```json
{
  "tempEventId": "tmp_f7258568-0374-4710-8473-329576255448",
  "eventTitle": "금요일 3시 팀플 회의",
  "draftRevision": 1,
  "startDate": "2026-08-14",
  "dateSource": "RELATIVE_EXPRESSION",
  "startTime": "15:00:00",
  "placeCandidate": null,
  "toEmbedding": ["팀플", "회의"],
  "isAllDayCandidate": false,
  "needsConfirmation": false,
  "warnings": []
}
```

이후 추천 API는 Neo4j 관계·벡터 후보와 Upstage LLM을 활용하여 `회의 시간 확인`, `얘기할 내용 정리`와 같은 준비·실행 항목을 최대 3개까지 제안합니다.

---

## 🧩 Server Responsibility

tryna 백엔드는 역할에 따라 Spring 서버와 FastAPI brain 서버로 분리합니다.

### Spring Server

Spring 서버는 서비스 운영에 필요한 핵심 백엔드 기능을 담당합니다.

- 회원/비회원 인증 및 사용자 계정 관리
- 일정 CRUD 및 캘린더 조회
- 추천 요청 중 최신 `draftRevision` 등록
- 추천 결과 저장
- 알림 및 외부 캘린더 연동
- DB 트랜잭션 및 권한 검증

### FastAPI Brain Server

FastAPI brain 서버는 일정 문장을 이해하고 추천 후보를 생성·정제하는 분석 엔진 역할을 담당합니다.

- Rule Based Parser와 Kiwi 기반 자연어 일정 파싱
- Upstage 임베딩 기반 일정 유형·맥락·장소 의미 매핑
- Neo4j 관계 및 벡터 기반 추천 후보 조회
- Upstage LLM 기반 추천 항목 선택 및 `displayText` 정제
- 시간 맥락 검증과 `TIMED_ACTION`·`UNTIMED_PREP` 분류
- Redis 기반 최신 `draftRevision` 검증
- Spring 서버에 파싱 및 추천 결과 반환

---

## 🛠 기술 스택

<div align="center">

|       Type       | Tool |
| :--------------: | :---: |
|     Language     | ![Python](https://img.shields.io/badge/Python_3.13-3776AB?style=for-the-badge&logo=python&logoColor=white) |
|    Framework     | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white) |
|   ASGI Server    | ![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=for-the-badge) |
|     Database     | ![Neo4j](https://img.shields.io/badge/Neo4j-4581C3?style=for-the-badge&logo=neo4j&logoColor=white) |
|      Cache       | ![Redis](https://img.shields.io/badge/Redis%2FValkey-FF4438?style=for-the-badge&logo=redis&logoColor=white) |
|       LLM        | ![Upstage](https://img.shields.io/badge/Upstage_Solar-000000?style=for-the-badge) |
|       NLP        | ![Kiwi](https://img.shields.io/badge/Kiwi_NLP-4CAF50?style=for-the-badge) |
| Configuration | ![pydantic-settings](https://img.shields.io/badge/pydantic--settings-E92063?style=for-the-badge) ![python-dotenv](https://img.shields.io/badge/python--dotenv-ECD53F?style=for-the-badge) |
| Package Manager | ![pip](https://img.shields.io/badge/pip-3775A9?style=for-the-badge&logo=pypi&logoColor=white) |
| Version Control | ![Git](https://img.shields.io/badge/git-F05032?style=for-the-badge&logo=git&logoColor=white) ![GitHub](https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white) |
| Collaboration | ![Notion](https://img.shields.io/badge/Notion-000000?style=for-the-badge&logo=notion&logoColor=white) |

</div>

---

## 🏗 Architecture

```text
Client
   │
   ▼
Spring Server
   │
   │ 내부 API 인증 및 일정 파싱/추천 요청
   ▼
FastAPI Brain Server
   │
   ├── Rule Based Parser + Kiwi
   │     날짜, 시간, 장소 등 일정 후보 추출
   │
   ├── Upstage Embedding + Neo4j
   │     의미 매핑 및 관계·벡터 추천 후보 조회
   │
   ├── Upstage LLM
   │     추천 항목 선택 및 displayText 정제
   │
   └── Redis/Valkey
         최신 draftRevision 검증
   │
   ▼
Spring Server
   │
   │ 추천 결과 저장/응답
   ▼
Client
```

---

## 🔄 Recommendation Pipeline

| Step | Component | Responsibility |
| --- | --- | --- |
| D101 | Schedule Context + Upstage Embedding | 일정 정보를 임베딩 입력으로 구성하고 쿼리 벡터 생성 |
| D102 | Neo4j | EventType, Context, PlaceType 의미 매핑 및 관계·벡터 추천 후보 결합 |
| D103 | Upstage LLM | 후보 중 최대 3개를 선택하고 자연스러운 `displayText`로 정제 |
| D104 | Temporal Validator | 날짜 맥락 검증 및 `TIMED_ACTION`·`UNTIMED_PREP` 확정 |
| D105 | Suggestion Composer | 순위와 부모 임시 일정 ID를 검증하고 최종 응답 구성 |

Spring 서버는 `tempEventId`별 최신 `draftRevision`을 Redis에 등록합니다. FastAPI는 D101~D105 단계 사이에서 `recommendation:latest-revision:{tempEventId}`를 조회하고, 오래된 요청이면 `409 STALE_DRAFT_REVISION_409`로 후속 처리를 중단합니다. Redis를 사용할 수 없을 때에는 추천 파이프라인을 계속 실행하는 fail-open 정책을 적용합니다.

> Upstage에는 분석과 추천 정제에 필요한 일정 정보 및 Neo4j 후보만 전달합니다. 개인정보나 불필요한 민감 정보는 전달하지 않는 것을 원칙으로 합니다.

---

## 📂 Project Structure

```text
brain/
├─ app/
│  ├─ main.py
│  ├─ api/
│  │  └─ v1/
│  │     ├─ router.py
│  │     └─ routes/
│  │        ├─ event_previews.py
│  │        ├─ health.py
│  │        └─ recommendations.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ deps.py
│  │  ├─ error_code.py
│  │  ├─ handlers.py
│  │  ├─ internal_auth.py
│  │  ├─ responses.py
│  │  └─ valkey_client.py
│  ├─ graph/
│  │  ├─ neo4j_client.py
│  │  ├─ models/
│  │  └─ repositories/
│  ├─ schemas/
│  │  ├─ recommendation/
│  │  ├─ event_preview.py
│  │  └─ health.py
│  └─ services/
│     ├─ event_preview_service.py
│     ├─ parser_service.py
│     └─ recommendation/
│        ├─ schedule_context_service.py
│        ├─ candidate_search_service.py
│        ├─ refinement_service.py
│        ├─ temporal_validation_service.py
│        ├─ suggestion_compose_service.py
│        └─ revision_guard_service.py
├─ tests/
├─ nginx/
├─ Dockerfile
├─ requirements.txt
├─ .env.example
└─ README.md
```

---

## 📦 Package Responsibility

| Package | Responsibility |
| --- | --- |
| `app.main` | FastAPI 앱 진입점과 Neo4j·Redis 생명주기 관리 |
| `app.core` | 환경변수, 의존성, 내부 인증, 공통 응답·예외 및 Redis 연결 관리 |
| `app.api` | 헬스체크, 일정 미리보기, 추천 API 엔드포인트 정의 |
| `app.graph` | Neo4j 연결과 일정 의미 매핑·추천 후보 조회 |
| `app.schemas` | 파싱·추천 파이프라인의 요청/응답 모델 정의 |
| `app.services` | 자연어 파싱 및 D101~D105 추천 비즈니스 로직 수행 |

---

## 🚀 시작하기

Python 3.13 환경을 권장합니다.

### 1. 가상환경 생성

```bash
python3.13 -m venv .venv
```

### 2. 의존성 설치

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Windows PowerShell에서는 `.venv/bin/python` 대신 `.\.venv\Scripts\python.exe`를 사용합니다.

### 3. 환경변수 파일 생성

```bash
cp .env.example .env
```

로컬 Neo4j, Redis/Valkey 및 Upstage API 정보를 `.env`에 설정합니다. `VALKEY_HOST`를 비워두면 Redis 기반 기능은 비활성화되며 서버는 계속 실행됩니다.

### 4. 서버 실행

```bash
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

테스트는 다음 명령어로 실행합니다.

```bash
PYTHONPATH=. .venv/bin/python -m pytest
```

---

## 📖 API Documentation

FastAPI brain 서버는 FastAPI 기본 Swagger UI를 사용합니다.

```text
http://127.0.0.1:8000/docs
```

비즈니스 API는 `X-Internal-Api-Key` 헤더로 Spring 서버와의 내부 통신을 인증합니다. 헬스체크는 인증 대상에서 제외됩니다.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Neo4j 및 Redis 연결 상태 확인 |
| `POST` | `/api/v1/event-previews` | 자연어 일정 파싱 및 미리보기 생성 |
| `POST` | `/api/v1/recommendations` | D101~D105 추천 파이프라인 실행 |

추천 API의 `stop_after_step` 쿼리는 개발 환경에서 중간 결과를 확인할 때만 사용할 수 있으며 운영 환경에서는 `403`을 반환합니다.

---

## ✅ Health Check

```http
GET /api/v1/health
```

Response:

```json
{
  "status": "UP",
  "timestamp": "2026-08-13T09:00:00Z",
  "components": {
    "neo4j": {
      "status": "UP",
      "detail": null
    },
    "redis": {
      "status": "UP",
      "detail": null
    }
  }
}
```

Redis/Valkey가 설정되지 않은 로컬 환경에서는 `components.redis.status`가 `DISABLED`로 표시됩니다. 현재 전체 상태와 HTTP 상태 코드는 Neo4j 연결 상태를 기준으로 결정합니다.

---

## 📦 Common Response

비즈니스 예외와 요청값 검증 오류는 공통 응답 객체를 사용합니다.

Error:

```json
{
  "success": false,
  "code": "COMMON_400",
  "message": "잘못된 요청입니다.",
  "data": null
}
```

일정 미리보기, 추천 성공 응답 및 헬스체크 응답은 각 API의 응답 스키마를 직접 반환합니다. 따라서 모든 성공 응답이 `success`, `code`, `message`, `data` 형식으로 감싸지지는 않습니다.

---

## ⚠️ Error Handling

공통 예외 처리는 `app/core`에서 관리합니다.

현재 주요 에러 코드는 다음과 같습니다.

| Code | HTTP Status | Description |
| --- | --- | --- |
| `COMMON_400` | 400 | 잘못된 요청 |
| `INTERNAL_AUTH_401` | 401 | 서버 간 인증 실패 |
| `COMMON_403` | 403 | 현재 환경에서 사용할 수 없는 기능 |
| `COMMON_404` | 404 | 리소스 없음 |
| `STALE_DRAFT_REVISION_409` | 409 | 최신 입력이 존재하는 이전 추천 요청 중단 |
| `COMMON_422` | 422 | 요청값 검증 실패 |
| `COMMON_500` | 500 | 서버 내부 오류 |
| `INTERNAL_AUTH_500` | 500 | 내부 API 인증 설정 누락 |
| `EMBEDDING_400` | 400 | 임베딩 입력값 누락 |
| `EMBEDDING_503` | 503 | 임베딩 모델 연동 불가 |
| `NEO4J_503` | 503 | Neo4j 연결 불가 |
| `LLM_503` | 503 | LLM 연동 불가 |

---

## ⚙️ Environment Configuration

brain 서버는 `.env` 기반으로 환경변수를 관리합니다.

```env
APP_NAME=tryna brain
APP_ENV=local
API_V1_PREFIX=/api/v1
ROOT_PATH=
INTERNAL_API_KEY=local-internal-api-key

VALKEY_HOST=localhost
VALKEY_PORT=6379
VALKEY_PASSWORD=

NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

UPSTAGE_API_KEY=
UPSTAGE_API_KEY_MULTI=
UPSTAGE_QUERY_EMBEDDING_MODEL=solar-embedding-1-large-query
UPSTAGE_PASSAGE_EMBEDDING_MODEL=solar-embedding-1-large-passage
UPSTAGE_EMBEDDING_TIMEOUT_SECONDS=10
UPSTAGE_CHAT_MODEL=solar-pro3
UPSTAGE_CHAT_TIMEOUT_SECONDS=20

D102_EMBEDDING_DIMENSION=4096
D102_EVENT_TYPE_MIN_SCORE=0.61
D102_CONTEXT_MIN_SCORE=0.63
D102_PLACE_TYPE_MIN_SCORE=0.63
D102_RECOMMENDATION_MIN_SCORE=0.62
```

운영 환경(`APP_ENV=prod`)에서는 Redis/Valkey 연결에 TLS와 시스템 CA 인증서 검증을 적용합니다. `.env`는 Git에 커밋하지 않고 `.env.example`만 공유합니다.

---

## 🔐 Security

민감 정보는 저장소에 커밋하지 않습니다.

다음 값은 로컬 `.env` 또는 배포 환경의 secret으로 관리합니다.

- `INTERNAL_API_KEY`
- `NEO4J_PASSWORD`
- `VALKEY_PASSWORD`
- `UPSTAGE_API_KEY`
- `UPSTAGE_API_KEY_MULTI`

`.gitignore`에 다음 파일과 디렉터리를 제외하도록 설정합니다.

```gitignore
.env
.env.local
.env.*.local
.venv
__pycache__/
```

---

## ✅ Current Setup Checklist

- [x] 자연어 일정 미리보기 API 구현
- [x] D101~D105 추천 파이프라인 구현
- [x] Neo4j 연결 및 관계·벡터 추천 후보 조회
- [x] Upstage 임베딩 및 추천 문구 정제
- [x] Redis/Valkey 연결 및 최신 revision 검증
- [x] 내부 API 키 인증
- [x] 공통 예외 처리와 Health Check API
- [x] Docker 및 GitHub Actions CI/CD 구성
- [x] pytest 테스트 구성

---

## 🗺 개발 로드맵

- [x] Python 및 FastAPI 실행 환경 구축
- [x] 자연어 일정 1차 파싱과 Kiwi 연동
- [x] Neo4j 연결 및 지식베이스 구축
- [x] Neo4j 의미 매핑과 추천 후보 조회 구현
- [x] 관계·벡터 추천 후보 결합
- [x] Upstage 임베딩 및 LLM 연동
- [x] 추천 항목 시간 맥락 검증과 최종 응답 구성
- [x] Redis 기반 오래된 추천 요청 후속 처리 차단
- [x] Spring 서버 내부 API 연동
