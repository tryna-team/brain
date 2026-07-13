# 🧠 Tryna Brain

> 일정을 이해하고, 맥락을 연결하며, 필요한 준비를 추천하는 FastAPI 기반 Context Intelligence Engine.

Tryna Brain은 TRYNA 서비스의 분석/추천 전용 서버입니다. 기존 README의 방향처럼 자연어 일정 분석, Neo4j 지식 그래프 조회, LLM 기반 추천 정제를 담당하되, Spring Server와 역할을 분리하여 독립적인 FastAPI 서버로 운영하는 것을 목표로 합니다.

---

## 📌 소개

TRYNA는 사용자가 입력한 짧은 일정 속 맥락을 이해하고, 일정 전후에 실제로 필요한 할 일을 제안하는 일정 관리 서비스입니다.

Tryna Brain은 이 중에서 **일정 문장 이해, 맥락 구조화, 관계 기반 추천 후보 조회, LLM 기반 후보 정제**를 담당하는 분석/추천 엔진입니다.

예를 들어 사용자가 다음과 같이 입력하면:

```text
금요일 3시 팀플 회의
```

Brain 서버는 후속 구현에서 다음과 같은 정보를 분석하고 추천 후보를 생성합니다.

```json
{
  "sourceText": "금요일 3시 팀플 회의",
  "titleCandidate": "팀플 회의",
  "dateCandidate": "이번 주 금요일",
  "timeCandidate": "15:00",
  "placeCandidate": null,
  "eventTypeCandidate": "meeting"
}
```

이후 Neo4j와 Upstage LLM을 활용해 회의 안건 정리, 공유 자료 확인, 장소 확인 같은 준비/실행 항목 후보를 제안하는 방향으로 확장합니다.

---

## 🧩 Server Responsibility

TRYNA 백엔드는 역할에 따라 Spring Server와 FastAPI Brain Server로 분리합니다.

### Spring Server

Spring Server는 서비스 운영에 필요한 핵심 백엔드 기능을 담당합니다.

- 회원/비회원 인증
- 사용자 계정 관리
- 일정 CRUD
- 캘린더 조회
- 추천 결과 저장
- 알림 및 외부 캘린더 연동
- DB 트랜잭션 및 권한 검증

### FastAPI Brain Server

FastAPI Brain Server는 일정 문장을 이해하고 추천 후보를 생성·정제하는 분석/추천 엔진 역할을 담당합니다.

- 자연어 일정 1차 파싱
- Kiwi 기반 한국어 형태소 분석 보조
- Rule Based Parser 기반 일정 후보 구조화
- Neo4j 기반 추천 후보 조회
- Upstage LLM 기반 추천 후보 정제
- 시간형/비시간형 분류 및 추천 개수 제한
- Spring Server에 분석/추천 결과 반환

---

## 🛠 기술 스택

<div align="center">

|       Type       | Tool |
| :--------------: | :---: |
|     Language     | ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) |
|    Framework     | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white) |
|   ASGI Server    | ![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=for-the-badge) |
|     Database     | ![Neo4j](https://img.shields.io/badge/Neo4j-4581C3?style=for-the-badge&logo=neo4j&logoColor=white) |
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
   │ 일정 분석/추천 요청
   ▼
FastAPI Brain Server
   │
   ├── Rule Based Parser + Kiwi
   │     일정 정보 1차 파싱
   │
   ├── Neo4j
   │     관계 기반 추천 후보 조회
   │
   └── Upstage LLM
         추천 후보 정제
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
| 1 | Rule Based Parser | 날짜, 시간, 장소, 일정 유형 후보 추출 |
| 2 | Kiwi | 한국어 형태소 분석 보조 |
| 3 | Neo4j | 일정과 행동의 관계 기반 추천 후보 조회 |
| 4 | Upstage LLM | 중복 후보 통합 및 불필요한 후보 제거 |
| 5 | Recommender | 시간형/비시간형 분류, 추천 개수 제한, 최종 응답 구성 |

> Upstage LLM에는 추천 정제에 필요한 최소한의 일정 정보와 Neo4j 후보 목록만 전달합니다. 개인정보나 민감한 상세 메모는 전달하지 않는 것을 원칙으로 합니다.

---

## 📂 Project Structure

```text
brain/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  │
│  ├─ api/
│  │  └─ v1/
│  │     ├─ router.py
│  │     └─ routes/
│  │        └─ health.py
│  │
│  ├─ global_response/
│  │  └─ response.py
│  │
│  ├─ global_exception/
│  │  ├─ error_code.py
│  │  ├─ exceptions.py
│  │  └─ handlers.py
│  │
│  ├─ graph/
│  │  └─ neo4j_client.py
│  │
│  ├─ parser/
│  ├─ recommender/
│  ├─ llm/
│  ├─ schemas/
│  │  └─ health.py
│  └─ services/
│
├─ scripts/
│  ├─ sample_data.py
│  └─ test_connection.py
│
├─ requirements.txt
├─ .env.example
└─ README.md
```

---

## 📦 Package Responsibility

| Package | Responsibility |
| --- | --- |
| `app.main` | FastAPI 앱 진입점, 라우터 및 예외 핸들러 등록 |
| `app.config` | 환경변수 및 설정 관리 |
| `app.api` | FastAPI 라우터 및 엔드포인트 정의 |
| `app.global_response` | 공통 응답 객체 관리 |
| `app.global_exception` | 공통 에러 코드, 비즈니스 예외, 예외 핸들러 관리 |
| `app.graph` | Neo4j 연결 및 그래프 조회 로직 |
| `app.parser` | 자연어 일정 1차 파싱 로직 |
| `app.recommender` | 추천 후보 조합, 시간형/비시간형 분류, 최종 추천 생성 |
| `app.llm` | Upstage LLM 연동 로직 |
| `app.schemas` | 요청/응답 DTO 정의 |
| `app.services` | API 흐름 및 비즈니스 로직 조합 |

---

## 🚀 시작하기

### 1. 가상환경 생성

```powershell
python -m venv .venv
```

### 2. 의존성 설치

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. 환경변수 파일 생성

```powershell
Copy-Item .env.example .env
```

### 4. 서버 실행

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 📖 API Documentation

FastAPI Brain Server는 FastAPI 기본 Swagger UI를 사용합니다.

```text
http://127.0.0.1:8000/docs
```

---

## ✅ Health Check

```http
GET /api/v1/health
```

Response:

```json
{
  "success": true,
  "code": "COMMON_200",
  "message": "Tryna Brain server is running.",
  "data": {
    "status": "ok"
  }
}
```

---

## 📦 Common Response

모든 API 응답은 공통 응답 객체를 사용합니다.

Success:

```json
{
  "success": true,
  "code": "COMMON_200",
  "message": "요청이 성공했습니다.",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "code": "COMMON_400",
  "message": "잘못된 요청입니다.",
  "data": null
}
```

응답 데이터가 없는 경우 `data`는 `null`로 반환합니다.

---

## ⚠️ Error Handling

공통 예외 처리는 `app/global_exception`에서 관리합니다.

현재 기본 에러 코드는 다음과 같습니다.

| Code | Description |
| --- | --- |
| `COMMON_400` | 잘못된 요청 |
| `COMMON_404` | 리소스 없음 |
| `COMMON_422` | 요청값 검증 실패 |
| `COMMON_500` | 서버 내부 오류 |
| `NEO4J_503` | Neo4j 연결 사용 불가 |

추후 parser, graph, llm, recommender 기능이 추가되면 도메인별 에러 코드를 확장합니다.

---

## ⚙️ Environment Configuration

Brain Server는 `.env` 기반으로 환경변수를 관리합니다.

```env
APP_NAME=Tryna Brain
APP_ENV=local
API_V1_PREFIX=/api/v1

NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

UPSTAGE_API_KEY=
```

`.env`는 Git에 커밋하지 않고, `.env.example`만 공유합니다.

---

## 🔐 Security

민감 정보는 저장소에 커밋하지 않습니다.

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

- [x] 필요한 의존성 추가
- [x] 민감 정보 제외를 위한 `.gitignore` 설정
- [x] FastAPI Swagger UI 확인 가능
- [x] 공통 응답 객체 세팅
- [x] 공통 에러 핸들러 세팅
- [x] Health Check API 세팅
- [x] 로컬 서버 실행 확인

---

## 🗺 개발 로드맵

- [x] Python 환경 구축
- [x] FastAPI 서버 초기 세팅
- [x] Health Check API 구축
- [x] 공통 응답 객체 구축
- [x] 공통 에러 핸들러 구축
- [x] Neo4j client 기본 구조 정리
- [ ] 자연어 일정 1차 파싱 API 구현
- [ ] Kiwi 형태소 분석 연동
- [ ] Neo4j 실제 연결 환경 구성
- [ ] Neo4j 지식베이스 구축
- [ ] Neo4j 추천 후보 조회 구현
- [ ] Upstage LLM 연동
- [ ] 추천 항목 생성 로직 구현
- [ ] Spring Server 연동