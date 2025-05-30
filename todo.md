# 차트 이미지 생성 및 LLM 연동 기능 개발 TODO

## 1. 차트 생성 툴 개발 (MCP 서버 내)

- **파일 생성**: `tools/generate_chart_image.py` 파일 생성
- **함수 정의**:
    - 비동기 함수 `generate_chart_image` 정의
    - 파라미터: `market: str`, `interval: str`, `chart_type: str = "line"`, `ctx: Context = None`
    - 반환 값: `dict` (예: `{"image_url": "생성된_URL", "file_path": "저장된_파일_경로", "message": "차트 생성 완료"}`)
- **핵심 로직**:
    - Upbit API를 통해 캔들 데이터 조회 (100~200개 캔들)
        - `tools/get_candels.py` 또는 `technical_analysis.py`의 캔들 조회 로직 활용 고려
    - 차트 생성 라이브러리 선택 및 설치:
        - `Matplotlib`을 기본으로 사용 (의존성에 추가 필요 - `pyproject.toml` 또는 `requirements.txt`)
    - 차트 이미지 생성:
        - 캔들 데이터를 기반으로 시계열 차트 (예: 종가 라인 차트, 봉 차트 등) 생성
        - 차트에 마켓, 인터벌 등 기본 정보 표시
    - 이미지 파일 저장:
        - 저장 경로: 컨테이너 내 `/app/charts/` 디렉터리 (Docker 볼륨으로 호스트와 공유될 경로)
        - 파일명 규칙 정의: 예) `[마켓코드]_[인터벌]_[차트타입]_[타임스탬프].png` (예: `KRW-BTC_day_line_20231027112233.png`)
- **URL 생성 로직**:
    - 저장된 이미지 파일에 접근 가능한 내부 URL 생성
    - 예: `http://[웹서버_서비스명_또는_IP]:[포트]/charts/[파일명]`
    - 초기에는 웹 서버 구축 전이므로, 파일 경로만 우선 반환하고 URL 부분은 주석 처리 또는 플레이스홀더로 남겨둘 수 있음.

## 2. Docker 환경 설정 (`docker-compose.yml` 수정)

- **MCP 서버 컨테이너 설정**:
    - 볼륨 마운트 추가: `./charts:/app/charts` (호스트의 `charts` 디렉터리를 컨테이너의 `/app/charts`로 연결)
- **웹 서버 컨테이너 추가 (예: Nginx)**:
    - 이미지: `nginx:latest` (또는 다른 경량 웹 서버 이미지)
    - 볼륨 마운트: `./charts:/usr/share/nginx/html/charts:ro` (MCP 서버가 저장한 이미지들을 Nginx가 읽을 수 있도록 공유, 읽기 전용)
    - 포트 설정: 호스트와 컨테이너 포트 매핑 (예: `8081:80`)
    - Nginx 설정 파일 (`nginx.conf` - 필요시)
        - `/charts` 경로로 요청이 오면 `/usr/share/nginx/html/charts` 디렉터리의 파일을 제공하도록 설정
        - 간단한 경우, 기본 설정으로도 동작 가능성 있음.

## 3. MCP 서버 `main.py` 수정

- 새로운 `generate_chart_image` 툴을 FastMCP 라우터에 등록
- `__init__.py` 에 `generate_chart_image` 함수 import

## 4. n8n 워크플로우 연동

- MCP 서버의 `generate_chart_image` 툴 호출하는 노드 추가
- 반환된 `image_url`을 받아 LLM 노드의 입력으로 사용 (이미지 URL 입력 방식 지원하는 LLM 사용)
- (선택 사항) n8n 내에서 `<img>` 태그를 사용하여 이미지 표시 테스트

## 5. 의존성 관리

- `pyproject.toml` (또는 `requirements.txt`) 에 `matplotlib` 추가
- `uv sync` 실행하여 의존성 업데이트

## 6. 테스트 및 디버깅

- 단위 테스트: `generate_chart_image` 함수가 올바르게 이미지 파일 생성 및 정보 반환하는지 확인
- 통합 테스트: n8n에서 전체 워크플로우 실행하여 차트 생성, URL 전달, LLM 연동까지 확인
- Docker 환경에서 볼륨 마운트 및 웹 서버를 통한 이미지 접근성 확인

## 기타 고려 사항

- **에러 핸들링**: API 요청 실패, 차트 생성 실패, 파일 저장 실패 등 예외 상황 처리
- **보안**: 생성된 URL이 외부로 직접 노출될 경우, 접근 제어 방안 고려 (초기에는 내부 네트워크 접근으로 한정)
- **차트 커스터마이징**: 다양한 차트 종류(봉차트, 이동평균선 포함 등), 색상, 크기 등을 파라미터로 조절할 수 있도록 확장 가능성 고려 