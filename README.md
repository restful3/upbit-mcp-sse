# Upbit MCP 서버

이 프로젝트는 [Upbit](https://upbit.com) 암호화폐 거래소 OpenAPI를 위한 MCP(Model Context Protocol) 서버 구현입니다. Upbit 거래소의 다양한 서비스(시세, 호가창, 체결 내역, 차트 데이터 조회, 계정 정보 확인, 주문 생성 및 취소, 입출금 관리, 기술적 분석 등)와 상호작용할 수 있는 도구들을 제공합니다.

**본 프로젝트는 [solangii/upbit-mcp-server](https://github.com/solangii/upbit-mcp-server)를 기반으로 합니다.**
원본 프로젝트는 MCP stdio 통신 방식으로 설계되어 n8n과 같은 워크플로우 자동화 도구와의 직접적인 연동에 어려움이 있었습니다. 이 버전은 n8n과의 원활한 연동을 위해 SSE(Server-Sent Events)를 지원하도록 핵심 로직이 수정되었으며, Docker 및 Docker Compose를 활용한 배포 방식을 기본으로 제공합니다.

## 주요 기능

- 실시간 시장 데이터 조회 (현재가, 호가창, 체결 내역, 캔들 데이터 등)
- 계정 정보 확인 (잔고, 주문 내역 등)
- 주문 실행 및 취소
- 입출금 기능 연동
- 기술적 분석 도구 통합

## 기술적 분석 도구 상세

`tools/technical_analysis.py` 에서 제공하는 `technical_analysis` 함수는 다음의 기술적 지표 및 분석 정보를 제공합니다.

| 기능 분류 | 세부 지표/항목 | 기본 설정/참고 | 제공 신호 |
|---|---|---|---|
| **캔들 데이터** | 지정된 마켓 및 인터벌의 캔들 조회 | Upbit API 사용 (기본 100개) | - |
| **이동 평균선 (SMA)** | 5, 10, 20, 50일 단순 이동 평균 |  | "상승 추세 (황금 교차)", "하락 추세 (죽음의 교차)", "중립" |
| **상대강도지수 (RSI)** | 14일 RSI |  | "과매수", "과매도", "중립" |
| **볼린저 밴드** | 20일 기준 중간, 상단, 하단 밴드 |  | "과매수 (상단 돌파)", "과매도 (하단 돌파)", "중립 (밴드 내)" |
| **MACD** | MACD 선 (12, 26일), 신호선 (9일), 히스토그램 | EMA 대신 SMA 사용 (간략화) | "매수 신호", "매도 신호", "중립" |
| **스토캐스틱** | %K (14일), %D (3일) | %D는 %K의 3일 SMA (간략화) | "과매수", "과매도", "상승 중", "하락 중", "중립" |
| **거래량 분석** | 평균 거래량 대비 현재 거래량 비율 |  | - |
| **지지/저항** | 피봇 포인트, R1, R2, S1, S2 | 단순화된 계산 방식 | - |
| **종합 분석** | 각 지표 값 반환 |  | - |
| **종합 신호** | 투자 판단 보조 신호 | 여러 지표 신호 종합 | "매수 고려", "매도 고려", "중립 관망" |

**참고:** `technical_analysis` 함수는 `market` (예: "KRW-BTC") 및 `interval` (예: "day", "minute60")을 인자로 받습니다. 제공되는 신호는 투자 결정에 대한 참고 자료이며, 실제 투자는 사용자의 신중한 판단 하에 이루어져야 합니다.

<details>
  <summary><strong>수행 가능한 기능 목록 (세부)</strong></summary>
  <br/>

  <h4>시장 데이터 조회</h4>
  <ul>
    <li>현재 암호화폐 시세 조회 (<code>get_ticker</code>)</li>
    <li>호가창 정보 조회 (<code>get_orderbook</code>)</li>
    <li>최근 체결 내역 조회 (<code>get_trades</code>)</li>
    <li>주요 암호화폐 시장 요약 정보 확인 (<code>get_market_summary</code>)</li>
  </ul>

  <h4>계정 정보 조회</h4>
  <ul>
    <li>보유 중인 자산 목록 및 잔고 확인 (<code>get_accounts</code>)</li>
    <li>주문 내역 조회 (<code>get_orders</code>)</li>
    <li>특정 주문 상세 정보 조회 (<code>get_order</code>)</li>
    <li>입출금 내역 조회 (<code>get_deposits_withdrawals</code>)</li>
  </ul>

  <h4>거래 기능</h4>
  <ul>
    <li>지정가/시장가 매수 주문 생성 (<code>create_order</code>)</li>
    <li>지정가/시장가 매도 주문 생성 (<code>create_order</code>)</li>
    <li>주문 취소 (<code>cancel_order</code>)</li>
  </ul>
</details>

<details>
  <summary><strong>채팅 예시 (원본 프로젝트 기준)</strong></summary>
  <br/>
  <p>
    아래는 원본 프로젝트([solangii/upbit-mcp-server](https://github.com/solangii/upbit-mcp-server))의 채팅 예시 이미지입니다.
  </p>
  <img src="./assets/img1.png" alt="example1" width="600"/>
  <img src="./assets/img2.png" alt="example2" width="600"/>
</details>

## 사전 준비 사항

시작하기 전에 Upbit API 키를 발급받아야 합니다:

1. [Upbit](https://upbit.com)에 계정이 없다면 먼저 회원가입을 진행합니다.
2. [Upbit 개발자 센터](https://upbit.com/service_center/open_api_guide)로 이동합니다.
3. 새로운 API 키를 생성합니다.
4. API 키에 필요한 권한(조회, 주문, 출금 등)을 적절히 설정합니다.
5. 발급받은 API 키(`UPBIT_ACCESS_KEY`, `UPBIT_SECRET_KEY`)를 프로젝트 루트 디렉토리에 `.env` 파일로 저장합니다 (설치 섹션 참조).

## 설치 방법

1.  **저장소 복제:**
    ```bash
    git clone <현재_프로젝트_저장소_URL> # 이 부분은 실제 저장소 URL로 변경해주세요.
    cd upbit-mcp-server
    ```

2.  **의존성 패키지 설치:**
    `uv`를 사용하여 프로젝트에 필요한 패키지들을 설치합니다.
    ```bash
    uv sync
    ```
    
    만약 `uv`가 설치되어 있지 않다면, 다음 방법으로 설치할 수 있습니다. `uv`를 사용하면 더 빠르고 안정적인 의존성 관리가 가능합니다.
    ```bash
    # uv 설치
    curl -Ls https://astral.sh/uv/install.sh | sh
    
    # uv를 PATH에 추가 (사용하는 쉘 환경에 맞게 수정)
    # 예: bash 또는 zsh의 경우, 홈 디렉토리의 .bashrc 또는 .zshrc 파일에 아래 내용 추가
    export PATH="$HOME/.local/bin:$PATH"
    # 변경사항 적용 (또는 터미널 재시작)
    # source ~/.bashrc  # 또는 source ~/.zshrc
    ```

3.  **환경 변수 설정:**
    프로젝트 루트 디렉토리에 `.env` 파일을 생성하고, 발급받은 Upbit API 키를 다음과 같이 입력합니다:
    ```env
    UPBIT_ACCESS_KEY=여기에_발급받은_ACCESS_KEY를_입력하세요
    UPBIT_SECRET_KEY=여기에_발급받은_SECRET_KEY를_입력하세요
    ```

## 사용 방법

이 서버는 n8n과의 원활한 연동을 위해 Docker Compose를 사용하여 실행하는 것을 권장합니다.

### Docker Compose를 이용한 실행 (n8n 연동 권장)

1.  **`docker-compose.yml` 설정 확인:**
    프로젝트에 포함된 `docker-compose.yml` 파일은 Upbit MCP 서버를 빌드하고 실행하도록 구성되어 있습니다. 주요 설정은 다음과 같습니다:
    *   **`ports`**: 서버의 포트(예: `8001:8001`)를 호스트 머신에 노출시킵니다. 이는 n8n이 (호스트나 다른 Docker 네트워크에서 실행 중일 경우) 서버에 접속할 수 있게 합니다.
    *   **`networks`**: 서버를 특정 Docker 네트워크(예: `nginx-n8n-net`)에 연결합니다. n8n과 이 서버가 모두 동일한 Docker 네트워크 상에서 컨테이너로 실행될 때 서로 통신하기 위해 **매우 중요합니다.** 사용 중인 n8n 컨테이너가 연결된 네트워크 이름과 동일하게 설정해야 합니다.
    *   **`env_file`**: `.env` 파일로부터 환경 변수를 로드합니다.
    *   **`volumes`**: 현재 디렉토리를 컨테이너 내부에 마운트하여, 이미지 재빌드 없이 코드 변경사항을 반영할 수 있게 합니다 (개발 시 유용).

2.  **서버 시작:**
    ```bash
    docker-compose up -d --build
    ```

3.  **로그 확인:**
    ```bash
    docker-compose logs -f upbit-mcp-server
    ```

### n8n 연동 설정

위 설명대로 Upbit MCP 서버가 Docker Compose를 통해 실행되고 n8n 인스턴스와 동일한 Docker 네트워크에 연결되었다면, 다음과 같이 n8n 워크플로우를 설정합니다:

1.  n8n 워크플로우에서 HTTP Request 노드 또는 MCP 관련 커뮤니티 노드(사용 가능하다면)를 사용합니다.
2.  **SSE 엔드포인트 URL**을 `http://upbit_mcp_server:8001/sse`로 설정합니다.
    *   `upbit_mcp_server`: `docker-compose.yml`에 정의된 서비스 이름입니다. Docker 내부 DNS가 이 이름을 공유 네트워크 내의 올바른 컨테이너 IP로 해석합니다.
    *   `8001`: 컨테이너 내부에서 서버가 리스닝하는 포트입니다.
    *   `/sse`: `FastMCP` 라이브러리에서 SSE 스트림을 위해 사용하는 일반적인 경로입니다. 만약 루트 경로(`/`)로 요청 시 `404 Not Found` 오류가 발생하면, `/sse` 경로를 사용해보세요.

### 개발 서버 실행 (Docker 미사용, 직접 테스트용)

개발 또는 직접 테스트 목적으로 Docker 없이 서버를 실행할 수 있습니다:
```bash
uv run python main.py
```
또는 FastMCP의 개발 모드를 사용할 수 있습니다:
```bash
fastmcp dev main.py
```
주의: 이 방법으로 직접 실행 시, n8n 인스턴스가 서버가 실행 중인 호스트와 포트로 접근할 수 있어야 합니다. n8n 연동 시에는 일반적으로 Docker를 사용하는 것이 더 편리하고 안정적입니다.

## 주의 사항

-   이 서버는 실제 거래를 처리할 수 있으므로 주의해서 사용해야 합니다.
-   API 키를 안전하게 보관하고, 절대로 공개 저장소에 커밋하지 마십시오.

## 라이선스

MIT
