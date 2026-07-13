# 빌드 (의존성 설치)
FROM python:3.13-slim AS build
WORKDIR /home/app/project

# 의존성만 먼저 복사해 레이어 캐시를 최대한 활용 (소스 변경 시 재다운로드 방지)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY app ./app

# 실행
FROM python:3.13-slim
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r fastapi && useradd -r -g fastapi fastapi

ENV TZ=Asia/Seoul
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/usr/local/bin:$PATH

COPY --from=build /install /usr/local
COPY --from=build /home/app/project/app ./app

USER fastapi:fastapi

EXPOSE 8000
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
