# 🧠 Tryna Brain

> 일정을 이해하고, 맥락을 연결하며, 필요한 준비를 추천하는 Context Intelligence Engine.

---

## 기술 스택

<div align="center">

|       Type       |                                                                                          Tool                                                                                           |
| :--------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
|     Language     |                     ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)                     |
|    Framework     |                    ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)                    |
|     Database     |                      ![Neo4j](https://img.shields.io/badge/Neo4j-4581C3?style=for-the-badge&logo=neo4j&logoColor=white)                      |
|       LLM        |                     ![Upstage](https://img.shields.io/badge/Upstage_Solar-000000?style=for-the-badge)                      |
|       NLP        |                     ![Kiwi](https://img.shields.io/badge/Kiwi_NLP-4CAF50?style=for-the-badge)                      |
| Configuration | ![python-dotenv](https://img.shields.io/badge/python--dotenv-ECD53F?style=for-the-badge) |
| Package Manager |                        ![pip](https://img.shields.io/badge/pip-3775A9?style=for-the-badge&logo=pypi&logoColor=white)                        |
| Version Control |             ![Git](https://img.shields.io/badge/git-F05032?style=for-the-badge&logo=git&logoColor=white) ![GitHub](https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white)             |
| Collaboration |               ![Notion](https://img.shields.io/badge/Notion-000000?style=for-the-badge&logo=notion&logoColor=white)                |

</div>

---

## 소개

Tryna Brain은 Tryna의 AI 추천 엔진입니다.

사용자의 일정을 분석하고, Neo4j 기반 지식 그래프와 LLM을 활용하여
맥락에 맞는 준비물과 할 일을 추천합니다.

---

## 주요 역할

- 자연어 일정 분석
- Neo4j 지식 그래프 조회
- 추천 후보 생성
- LLM 기반 추천 정제
- Spring Server API 연동

---

## 프로젝트 구조

```text
brain/

app/
├── api/
├── graph/
├── parser/
├── recommender/
├── llm/
├── config.py
└── main.py

scripts/
├── sample_data.py
└── test_connection.py
```

---

## 시작하기

```bash
python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
```

환경 변수 설정

```bash
cp .env.example .env
```

---

## 개발 로드맵

- [x] Python 환경 구축
- [x] Neo4j 연결
- [ ] Neo4j 지식베이스 구축
- [ ] Recommendation Repository
- [ ] FastAPI 구축
- [ ] Kiwi Parser 연동
- [ ] Upstage LLM 연동
- [ ] 사용자 맥락 기반 추천