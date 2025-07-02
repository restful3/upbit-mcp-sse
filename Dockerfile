FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 프로젝트 파일 복사
COPY . .

# 의존성 설치
RUN uv sync

# 차트 디렉토리 생성
RUN mkdir -p /app/charts /app/charts-shared

# 포트 노출
EXPOSE 8001

# 서버 실행
CMD ["uv", "run", "python", "main.py"] 