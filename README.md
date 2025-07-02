# Upbit MCP 서버

이 프로젝트는 [Upbit](https://upbit.com) 암호화폐 거래소 OpenAPI를 위한 MCP(Model Context Protocol) 서버 구현입니다. Upbit 거래소의 다양한 서비스(시세, 호가창, 체결 내역, 차트 데이터 조회, 계정 정보 확인, 주문 생성 및 취소, 입출금 관리, 기술적 분석 등)와 상호작용할 수 있는 도구들을 제공합니다.

**본 프로젝트는 [solangii/upbit-mcp-server](https://github.com/solangii/upbit-mcp-server)를 기반으로 합니다.**
원본 프로젝트는 MCP stdio 통신 방식으로 설계되어 n8n과 같은 워크플로우 자동화 도구와의 직접적인 연동에 어려움이 있었습니다. 이 버전은 n8n과의 원활한 연동을 위해 SSE(Server-Sent Events)를 지원하도록 핵심 로직이 수정되었으며, Docker 및 Docker Compose를 활용한 배포 방식을 기본으로 제공합니다. 또한, FastMCP 1.0.0 버전에 맞게 내부 로직 및 에러 처리 방식이 개선되었고, 기술적 분석 도구의 정확성과 안정성이 향상되었습니다.

## 주요 기능

- 실시간 시장 데이터 조회 (현재가, 호가창, 최근 체결 내역, 캔들 데이터 등)
- 계정 정보 확인 (전체 잔고, 미체결 주문, 개별 주문 상세, 입출금 내역 등)
- 주문 실행 및 취소 (지정가/시장가 주문, 주문 취소)
- 기술적 분석 지표 및 신호 제공 (EMA 기반 MACD 계산, API 엔드포인트 수정 등 정확도 향상)
- **백테스팅 시스템** (SMA, RSI, 볼린저 밴드, MACD 전략 지원, 자연어 요청 처리 가능)
- **차트 이미지 생성 기능** (캔들스틱, 라인, OHLC 차트 지원, 날짜 범위 지정 가능, 웹 접근 가능한 이미지 URL 제공)
- LLM 에이전트의 답변 및 행동을 가이드하기 위한 프롬프트 및 리소스 제공
- `FastMCP 1.0.0` 기반의 SSE(Server-Sent Events) 통신 지원으로 n8n 등 외부 시스템과의 유연한 연동
- 주요 기능에 대한 상세 로깅 추가로 디버깅 편의성 증대
- FastMCP 1.0.0 표준에 맞춘 에러 처리 (툴 실행 오류 시, 에러 메시지를 포함한 JSON 객체 반환)

### 제공 툴 (Tools)

본 MCP 서버는 다음과 같은 툴들을 제공하여 LLM 에이전트가 업비트 API와 상호작용할 수 있도록 합니다.

| 툴 이름                      | 기능 설명                                                                 | 주요 파라미터 (예시)      |
| ---------------------------- | ------------------------------------------------------------------------- | ------------------------ |
| `get_ticker`                 | 특정 암호화폐 마켓의 현재 시세 정보(가격, 변동률 등)를 조회합니다.        | `symbol="KRW-BTC"`       |
| `get_orderbook`              | 특정 마켓의 실시간 매수/매도 호가 정보를 조회합니다.                        | `symbol="KRW-BTC"`       |
| `get_trades`                 | 특정 마켓의 가장 최근 단일 체결 내역을 조회합니다. (API 기본값)             | `symbol="KRW-BTC"`       |
| `get_accounts`               | 사용자의 전체 계좌 잔고 및 보유 자산 정보를 조회합니다.                     | -                        |
| `create_order`               | 지정가 또는 시장가로 매수/매도 주문을 생성합니다.                           | `market`, `side`, `ord_type`, `volume`, `price` |
| `get_orders`                 | 사용자의 미체결 주문 목록을 조회합니다.                                     | `market` (선택)          |
| `get_order`                  | 특정 주문의 상세 내역을 조회합니다.                                         | `uuid`                   |
| `cancel_order`               | 특정 주문을 취소합니다.                                                     | `uuid`                   |
| `get_market_summary`         | KRW 전체 마켓의 현재 상황을 동적으로 요약하여 제공합니다.                   | `major_n`, `top_n`, `sort_by` |
| `get_deposits_withdrawals`   | 사용자의 입출금 내역을 조회합니다.                                          | `currency` (선택)        |
| `get_markets`                | 업비트에서 거래 가능한 전체 마켓 코드 목록을 조회합니다.                     | -                        |
| `get_candles`                | 지정된 마켓의 캔들(시고저종) 데이터를 조회합니다.                           | `market`, `interval`, `count` |
| `create_withdraw`            | 디지털 자산 또는 원화 출금을 요청합니다.                                    | `currency`, `amount`, `address` |
| `technical_analysis`         | 지정된 마켓과 인터벌에 대한 다양한 기술적 지표 및 분석 신호를 제공합니다. (API 엔드포인트 수정 및 MACD 계산 로직 개선)     | `market`, `interval`     |
| `backtesting`                | 지정된 전략으로 과거 데이터를 이용한 백테스팅을 수행하고 성과 지표를 제공합니다. (SMA, RSI, 볼린저 밴드, MACD 전략 지원) | `market`, `strategy_type`, `start_date`, `end_date`, `strategy_params` |
| `generate_chart_image`       | 지정된 마켓의 차트 이미지를 생성하고 웹 접근 가능한 URL을 제공합니다. (캔들스틱, 라인, OHLC 차트, 날짜 범위 지정 가능) | `market`, `interval`, `chart_type`, `start_date`, `end_date` |

### 제공 프롬프트 (Prompts)

LLM 에이전트가 특정 상황에 더 적절하게 응답하거나 작업을 수행하도록 안내하는 프롬프트 템플릿을 제공합니다.

| 프롬프트 이름          | 기능 설명                                                              |
| ---------------------- | ---------------------------------------------------------------------- |
| `explain_ticker`       | `get_ticker`로 얻은 시세 데이터를 사용자에게 설명하기 위한 텍스트를 생성합니다. |
| `analyze_portfolio`    | `get_accounts`로 얻은 계좌 정보를 바탕으로 포트폴리오 분석을 요청하는 텍스트를 생성합니다. |
| `order_help`           | `create_order` 툴 사용법 및 주문 관련 도움말을 제공합니다.                 |
| `trading_strategy`     | 트레이딩 전략 수립 과정을 안내하고 관련 툴 사용을 유도하는 텍스트를 생성합니다. |
| `backtesting_guide`    | 자연어 백테스팅 요청을 툴 파라미터로 변환하는 가이드를 제공합니다. |

### 제공 리소스 (Resources)

MCP 클라이언트나 LLM 에이전트가 참조할 수 있는 정적 또는 동적 데이터를 제공합니다.

| 리소스 URI        | 제공 데이터                               | 관련 툴/기능           |
| ----------------- | ----------------------------------------- | ---------------------- |
| `market://list`   | 업비트에서 거래 가능한 전체 마켓 코드 목록 | `get_market_list.py` |


## 기술적 분석 도구 상세

`tools/technical_analysis.py` 에서 제공하는 `technical_analysis` 함수는 다음의 기술적 지표 및 분석 정보를 제공합니다. 캔들 데이터 조회 시 Upbit API의 정확한 엔드포인트(일/주/월봉의 경우 `/candles/days`, `/candles/weeks`, `/candles/months` 사용)를 사용하도록 수정되었으며, MACD 계산 시 단순 이동 평균(SMA) 대신 지수 이동 평균(EMA)을 사용하여 정확도를 높였습니다.

| 기능 분류 | 세부 지표/항목 | 기본 설정/참고 | 제공 신호 |
|---|---|---|---|
| **캔들 데이터** | 지정된 마켓 및 인터벌의 캔들 조회 | Upbit API 사용 (기본 200개, 정확한 엔드포인트 사용) | - |
| **이동 평균선 (SMA)** | 20, 50, 200일(충분한 데이터 시) 단순 이동 평균 |  | "bullish", "bearish", "neutral" |
| **상대강도지수 (RSI)** | 14일 RSI |  | "overbought", "oversold", "neutral" |
| **볼린저 밴드** | 20일 기준 중간, 상단, 하단 밴드 |  | "overbought", "oversold", "neutral" |
| **MACD** | MACD 선 (12, 26일 EMA), 신호선 (9일 EMA), 히스토그램 | EMA 기반 계산 | "bullish", "bearish", "neutral" |
| **거래량 분석** | 현재 거래량, 20일 평균 거래량, 비율 |  | "high", "low", "neutral" |
| **종합 신호** | 투자 판단 보조 신호 | 여러 지표 신호 종합 (MA, RSI, BB, MACD 기반) | "strong_buy", "buy", "strong_sell", "sell", "neutral" |

**참고:** `technical_analysis` 함수는 `market` (예: "KRW-BTC") 및 `interval` (예: "day", "minute60")을 인자로 받습니다. 제공되는 신호는 투자 결정에 대한 참고 자료이며, 실제 투자는 사용자의 신중한 판단 하에 이루어져야 합니다. 데이터 부족 시 지표 값은 "N/A"로 표시될 수 있습니다.

## 백테스팅 도구 상세

`tools/backtesting.py`에서 제공하는 `backtesting` 함수는 다양한 거래 전략을 과거 데이터에 적용하여 성과를 시뮬레이션하고 분석합니다. 2025년 1월 기준으로 완전히 구현되어 모든 주요 기능이 정상 작동합니다.

### 지원하는 백테스팅 전략

| 전략 타입 | 전략명 | 설명 | 주요 파라미터 |
|---|---|---|---|
| `sma_crossover` | SMA 교차 전략 | 단기/장기 이동평균선의 골든크로스/데드크로스 기반 매매 | `fast_period`, `slow_period` |
| `rsi_oversold` | RSI 과매도/과매수 전략 | RSI 지표의 과매도/과매수 구간 진입 시 매매 | `rsi_period`, `oversold_threshold`, `overbought_threshold` |
| `bollinger_bands` | 볼린저 밴드 전략 | 볼린저 밴드 내 상대적 위치 기반 매매 | `period`, `std_dev`, `buy_threshold`, `sell_threshold` |
| `macd_signal` | MACD 신호선 전략 | MACD선과 신호선의 교차 기반 매매 | `fast_period`, `slow_period`, `signal_period` |

### 지원하는 시간 간격

- **분봉**: 1분(`minute1`), 3분(`minute3`), 5분(`minute5`), 10분(`minute10`), 15분(`minute15`), 30분(`minute30`)
- **시간봉**: 1시간(`minute60`), 4시간(`minute240`)
- **일봉**: `day`
- **주봉**: `week`
- **월봉**: `month`

### 제공하는 성과 지표

백테스팅 결과로 다음과 같은 상세한 성과 지표를 제공합니다:

| 지표 분류 | 세부 지표 | 설명 |
|---|---|---|
| **포트폴리오 요약** | `initial_capital` | 초기 자본금 |
|  | `final_cash_balance` | 최종 현금 잔고 |
|  | `final_asset_quantity` | 최종 자산 보유량 |
|  | `final_asset_price` | 최종 자산 가격 |
|  | `final_asset_value` | 최종 자산 평가가치 |
|  | `final_total_value` | 최종 총 포트폴리오 가치 |
|  | `absolute_profit` | 절대 수익 금액 |
|  | `position_status` | 포지션 상태 (CASH/HOLDING_ASSET/MIXED) |
| **수익률 지표** | `total_return` | 백테스트 기간 총 수익률 |
|  | `annualized_return` | 연환산 수익률 |
|  | `realized_return` | 실현 수익률 |
|  | `unrealized_return` | 미실현 수익률 |
| **손익 분석** | `realized_profit` | 실현 손익 (완료된 거래의 손익) |
|  | `unrealized_profit` | 미실현 손익 (보유 포지션의 손익) |
| **위험 지표** | `volatility` | 연율화 변동성 |
|  | `sharpe_ratio` | 샤프 지수 (위험 대비 수익률) |
|  | `max_drawdown` | 최대 낙폭 |
| **거래 성과** | `win_rate` | 승률 (수익 거래 비율) |
|  | `profit_factor` | 프로핏 팩터 (총 이익/총 손실) |
|  | `total_trades` | 총 거래 횟수 |
| **상세 분석** | `monthly_returns` | 월별 수익률 상세 |
|  | `drawdown_periods` | 주요 드로우다운 구간 분석 |
|  | `trade_history` | 모든 거래 내역 상세 (개별 거래 손익 포함) |

### 자연어 백테스팅 사용 예시

`backtesting_guide` 프롬프트를 통해 자연어로 백테스팅을 요청할 수 있습니다:

#### 📝 사용자 요청 예시
```
"비트코인 20일선과 50일선 골든크로스 전략으로 2024년 전체 기간 일봉 백테스팅해줘"
"이더리움 RSI 14일 과매도 25, 과매수 75 전략, 2024년 하반기 4시간봉으로 분석해줘"
"리플 볼린저밴드 20일 2시그마 전략으로 2024년 상반기 백테스팅 결과 보여줘"
"도지코인 MACD 12-26-9 신호선 교차 전략으로 2024년 6월~12월 백테스팅 분석해줘"
```

#### 🤖 LLM 에이전트 응답 예시 (프롬프트 활용)

**사용자**: "비트코인 20일선과 50일선 골든크로스 전략으로 2024년 전체 기간 일봉 백테스팅해줘"

**LLM**: 비트코인 SMA 교차 전략 백테스팅을 진행하겠습니다. 다음 파라미터로 분석하겠습니다:
- 마켓: KRW-BTC
- 전략: SMA 교차 (20일선과 50일선)
- 기간: 2024년 1월 1일 ~ 2024년 12월 31일
- 시간간격: 일봉(day)

```json
{
  "market": "KRW-BTC",
  "strategy_type": "sma_crossover",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "interval": "day",
  "strategy_params": {
    "fast_period": 20,
    "slow_period": 50
  }
}
```

**사용자**: "리플 볼린저밴드 전략으로 최근 3개월 4시간봉 백테스팅해줘"

**LLM**: 리플(XRP) 볼린저 밴드 전략 백테스팅을 실행하겠습니다:
- 마켓: KRW-XRP
- 전략: 볼린저 밴드 (기본 20일, 2시그마)
- 기간: 최근 3개월
- 시간간격: 4시간봉

```json
{
  "market": "KRW-XRP",
  "strategy_type": "bollinger_bands",
  "start_date": "2024-10-01",
  "end_date": "2024-12-31",
  "interval": "minute240",
  "strategy_params": {
    "period": 20,
    "std_dev": 2.0,
    "buy_threshold": 0.2,
    "sell_threshold": 0.8
  }
}
```

#### 💡 프롬프트 변환 가이드

`backtesting_guide` 프롬프트는 다음과 같은 자연어 표현을 툴 파라미터로 변환합니다:

| 자연어 표현 | 툴 파라미터 변환 |
|---|---|
| "20일선과 50일선 골든크로스" | `strategy_type: "sma_crossover"`, `fast_period: 20`, `slow_period: 50` |
| "RSI 과매도 25, 과매수 75" | `strategy_type: "rsi_oversold"`, `oversold_threshold: 25`, `overbought_threshold: 75` |
| "볼린저밴드 20일 2시그마" | `strategy_type: "bollinger_bands"`, `period: 20`, `std_dev: 2.0` |
| "MACD 12-26-9" | `strategy_type: "macd_signal"`, `fast_period: 12`, `slow_period: 26`, `signal_period: 9` |
| "2024년 상반기" | `start_date: "2024-01-01"`, `end_date: "2024-06-30"` |
| "최근 3개월" | 현재 날짜 기준 3개월 전부터 |
| "4시간봉" | `interval: "minute240"` |
| "일봉" | `interval: "day"` |

### 백테스팅 시스템 특징

- **정확한 API 연동**: Upbit API의 모든 시간 간격에 대해 올바른 엔드포인트 사용
- **페이징 처리**: 200개 제한을 넘는 긴 기간 데이터도 자동으로 수집
- **안정적인 계산**: 무한 루프 및 API 오류 문제 해결 완료
- **상세한 분석**: 단순 수익률뿐만 아니라 리스크 조정 지표까지 제공
- **유연한 파라미터**: 각 전략별로 세부 파라미터 조정 가능
- **🆕 완전한 포트폴리오 추적**: 최종 잔고, 포지션 상태, 실현/미실현 손익 명확 표시
- **🆕 개별 거래 분석**: 각 거래의 손익률과 포트폴리오 영향 상세 제공

### 개선된 백테스팅 결과 예시

```json
{
  "portfolio_summary": {
    "initial_capital": 1000000,
    "final_cash_balance": 0,
    "final_asset_quantity": 0.00899,
    "final_asset_price": 139300000,
    "final_asset_value": 1252507,
    "final_total_value": 1252507,
    "absolute_profit": 252507,
    "position_status": "HOLDING_ASSET",
    "realized_profit": -218101,
    "unrealized_profit": 470608,
    "realized_return": -0.218,
    "unrealized_return": 0.471
  },
  "performance_metrics": {
    "total_return": 0.2525,
    "annualized_return": 0.2971,
    "volatility": 0.2554,
    "sharpe_ratio": 1.16,
    "max_drawdown": -0.2928,
    "win_rate": 0.0,
    "profit_factor": 0,
    "total_trades": 5
  },
  "trade_history": [
    {
      "date": "2024-05-30",
      "action": "BUY",
      "price": 94593000,
      "quantity": 0.01053,
      "commission": 500,
      "portfolio_value": 995500,
      "trade_profit": 0,
      "trade_return": 0
    },
    {
      "date": "2024-06-26", 
      "action": "SELL",
      "price": 86027000,
      "quantity": 0.01053,
      "commission": 453,
      "portfolio_value": 905185,
      "trade_profit": -90315,
      "trade_return": -0.096
    }
  ]
}
```

이제 **"초기 자본 1,000,000원으로 시작해서 최종적으로 1,252,507원이 되었다"**는 것을 명확히 알 수 있습니다!

**⚠️ 면책 조항**: 백테스팅 결과는 과거 데이터를 기반으로 한 시뮬레이션이며, 미래 수익을 보장하지 않습니다. 실제 투자 결정은 신중한 판단 하에 이루어져야 합니다.

## 차트 이미지 생성 도구 상세

`tools/generate_chart_image.py`에서 제공하는 `generate_chart_image` 함수는 지정된 마켓의 시각적 차트를 생성하고 웹에서 접근 가능한 이미지 URL을 제공합니다. 2025년 1월 기준으로 완전히 구현되어 모든 주요 기능이 정상 작동합니다.

### 지원하는 차트 기능

| 기능 분류 | 세부 옵션 | 설명 | 기본값 |
|---|---|---|---|
| **차트 타입** | `candlestick` | 캔들스틱 차트 (시가, 고가, 저가, 종가 표시) | ✅ 기본값 |
|  | `line` | 라인 차트 (종가만 표시) |  |
|  | `ohlc` | OHLC 바 차트 (시고저종 표시) |  |
| **시간 간격** | `minute1` ~ `minute240` | 1분봉부터 4시간봉까지 | `day` |
|  | `day`, `week`, `month` | 일봉, 주봉, 월봉 |  |
| **데이터 개수** | `count` | 표시할 캔들 개수 (10~200개) | 100개 |
| **날짜 범위** | `start_date` | 시작 날짜 (YYYY-MM-DD 형식) | 없음 (최신 데이터) |
|  | `end_date` | 종료 날짜 (YYYY-MM-DD 형식) | 없음 (최신 데이터) |
| **추가 지표** | `include_volume` | 거래량 차트 포함 여부 | ✅ 포함 |
|  | `include_ma` | 이동평균선(MA20, MA50) 포함 여부 | ✅ 포함 |

### 차트 생성 플로우

1. **데이터 수집**: Upbit API에서 지정된 마켓과 시간 간격의 캔들 데이터 조회
2. **날짜 필터링**: `start_date`와 `end_date`가 지정된 경우 해당 범위의 데이터만 추출
3. **차트 생성**: Matplotlib을 사용하여 시각적 차트 이미지 생성
   - 캔들스틱/라인/OHLC 차트
   - 거래량 서브차트 (선택 시)
   - 이동평균선 오버레이 (선택 시)
4. **파일 저장**: `/app/uploads/charts/` 디렉토리에 PNG 파일로 저장
5. **URL 반환**: `https://charts.resteful3.shop/파일명.png` 형태의 웹 접근 가능한 URL 제공

### 차트 이미지 접근

생성된 차트는 별도 서브도메인을 통해 웹에서 바로 접근할 수 있습니다:

- **도메인**: `charts.resteful3.shop`
- **SSL 인증서**: Let's Encrypt 자동 갱신
- **CORS 설정**: 모든 도메인에서 접근 가능
- **캐시 설정**: 1시간 캐시로 성능 최적화

### 사용 예시

#### 📝 기본 차트 생성
```json
{
  "market": "KRW-BTC",
  "interval": "day",
  "chart_type": "candlestick",
  "count": 100
}
```

#### 📅 날짜 범위 지정 차트
```json
{
  "market": "KRW-BTC", 
  "interval": "day",
  "chart_type": "candlestick",
  "start_date": "2024-06-01",
  "end_date": "2024-12-31",
  "count": 200
}
```

#### 💬 자연어 요청 예시
- "비트코인 일봉 캔들스틱 차트를 생성해주세요"
- "2024년 6월부터 12월까지 이더리움 차트를 보여주세요"
- "리플 4시간봉 라인 차트를 거래량과 함께 만들어주세요"
- "도지코인 15분봉 차트를 이동평균선 없이 생성해주세요"

### 기술적 세부사항

- **이미지 형식**: PNG (고해상도 150 DPI)
- **차트 크기**: 12x8 또는 12x10 (거래량 포함 시)
- **한글 폰트**: 시스템 기본 폰트 사용
- **색상 구성**: 
  - 상승 캔들: 빨간색
  - 하락 캔들: 파란색
  - MA20: 주황색
  - MA50: 빨간색
- **파일명 형식**: `{마켓}_{간격}_{타입}_{타임스탬프}.png`

### Docker 환경 설정

차트 생성을 위한 Docker 환경이 구성되어 있습니다:

```dockerfile
# 의존성 패키지
matplotlib>=3.7.0
pillow>=10.0.0

# 볼륨 마운트
/app/uploads/charts -> Nginx 정적 파일 서빙
```

### 차트 기능의 장점

1. **즉시 시각화**: 복잡한 데이터를 한눈에 파악 가능한 차트로 변환
2. **웹 접근성**: 생성된 이미지를 바로 웹에서 확인 가능
3. **유연한 설정**: 다양한 차트 타입과 시간 간격 지원
4. **날짜 범위**: 특정 기간의 과거 데이터 차트 생성 가능
5. **기술적 분석**: 이동평균선과 거래량으로 추가 인사이트 제공

<details>
  <summary><strong>수행 가능한 기능 목록 (세부)</strong></summary>
  <br/>

  <h4>시장 데이터 조회</h4>
  <ul>
    <li>특정 암호화폐의 현재 시세(가격, 변동률 등) 조회 (<code>get_ticker</code>)</li>
    <li>특정 마켓의 실시간 매수/매도 호가 정보 조회 (<code>get_orderbook</code>)</li>
    <li>특정 마켓의 가장 최근 단일 체결 내역 조회 (<code>get_trades</code>)</li>
    <li>(<code>get_market_summary</code>는 현재 <code>get_ticker</code>와 유사 기능 제공 가능성)</li>
    <li>지정된 마켓의 캔들(시고저종) 데이터 조회 (<code>get_candles</code>)</li>
    <li>지정된 마켓과 인터벌에 대한 다양한 기술적 지표 및 분석 신호 확인 (<code>technical_analysis</code>)</li>
    <li>시각적 차트 이미지 생성 및 웹 URL 제공 (<code>generate_chart_image</code>)</li>
    <li>업비트 거래 가능 전체 마켓 코드 목록 확인 (<code>get_markets</code>, <code>market://list</code> 리소스)</li>
  </ul>

  <h4>계정 정보 조회</h4>
  <ul>
    <li>전체 계좌 잔고 및 보유 자산 정보 확인 (<code>get_accounts</code>)</li>
    <li>미체결 주문 목록 조회 (<code>get_orders</code>)</li>
    <li>특정 주문의 상세 내역 조회 (<code>get_order</code>)</li>
    <li>입출금 내역 조회 (<code>get_deposits_withdrawals</code>)</li>
  </ul>

  <h4>거래 기능</h4>
  <ul>
    <li>지정가 또는 시장가 매수/매도 주문 생성 (<code>create_order</code>)</li>
    <li>특정 주문 취소 (<code>cancel_order</code>)</li>
    <li>디지털 자산 또는 원화 출금 요청 (<code>create_withdraw</code>)</li>
  </ul>

  <h4>LLM 에이전트 보조</h4>
  <ul>
    <li>시세 정보 사용자 설명 생성 (<code>explain_ticker</code> 프롬프트)</li>
    <li>포트폴리오 분석 요청 생성 (<code>analyze_portfolio</code> 프롬프트)</li>
    <li>주문 방법 안내 (<code>order_help</code> 프롬프트)</li>
    <li>트레이딩 전략 수립 가이드 (<code>trading_strategy</code> 프롬프트)</li>
  </ul>

  <h4>백테스팅 및 전략 분석</h4>
  <ul>
    <li>다양한 거래 전략의 과거 성과 시뮬레이션 (<code>backtesting</code>)</li>
    <li>SMA 교차, RSI 과매도/과매수, 볼린저 밴드, MACD 신호선 전략 지원</li>
    <li>상세한 성과 지표 및 위험 분석 (수익률, 샤프 지수, 최대 낙폭 등)</li>
    <li>자연어 백테스팅 요청 처리 (<code>backtesting_guide</code> 프롬프트)</li>
  </ul>

  <h4>차트 이미지 생성</h4>
  <ul>
    <li>캔들스틱, 라인, OHLC 차트 생성 (<code>generate_chart_image</code>)</li>
    <li>날짜 범위 지정 가능 (과거 특정 기간 차트 생성)</li>
    <li>거래량 및 이동평균선 포함/제외 선택</li>
    <li>웹 접근 가능한 이미지 URL 자동 생성</li>
    <li>다양한 시간 간격 지원 (1분봉~월봉)</li>
  </ul>
</details>

<details>
  <summary><strong>채팅 예시 (원본 프로젝트 기준)</strong></summary>
  <br/>
  <p>
    아래는 원본 프로젝트([solangii/upbit-mcp-server](https://github.com/solangii/upbit-mcp-server))의 채팅 예시 이미지입니다.
    이 프로젝트는 해당 기능을 기반으로 n8n 연동 및 기능 개선이 이루어졌습니다.
  </p>
  <img src="./assets/img1.png" alt="example1" width="600"/>
  <img src="./assets/img2.png" alt="example2" width="600"/>
</details>

## 프로젝트 구조

프로젝트의 주요 디렉토리 및 파일은 다음과 같습니다:

-   `main.py`: FastMCP 서버의 메인 실행 파일입니다. 모든 툴, 프롬프트, 리소스를 초기화하고 서버를 실행합니다.
-   `config.py`: Upbit API 키, 기본 API URL 등의 설정을 관리합니다. (실제 키는 `.env` 파일에 저장)
-   `docker-compose.yml`: Docker를 사용하여 서버를 빌드하고 실행하기 위한 설정 파일입니다. n8n과의 네트워크 연동 설정 등이 포함됩니다.
-   `requirements.txt` / `pyproject.toml` / `uv.lock`: Python 프로젝트의 의존성 패키지들을 관리합니다. (`uv` 사용 권장)
-   `.env`: Upbit API 키와 같이 민감한 환경 변수를 저장하는 파일입니다. (버전 관리에서 제외됨)
-   `tools/`: 업비트 API 기능을 수행하는 개별 MCP 툴 파이썬 파일들이 위치합니다. (예: `get_ticker.py`, `create_order.py`)
-   `prompts/`: LLM 에이전트의 행동을 가이드하거나 특정 작업 템플릿을 제공하는 프롬프트 파이썬 파일들이 위치합니다. (예: `order_help.py`)
-   `resources/`: MCP 서버가 제공하는 리소스(예: 거래 가능 마켓 목록)를 정의하는 파이썬 파일들이 위치합니다. (예: `get_market_list.py`)
-   `README.md`: 본 프로젝트 설명 파일입니다.

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

2.  **의존성 패키지 설치 (uv 권장):**
    `uv`를 사용하여 Python 프로젝트에 필요한 패키지들을 설치하는 것을 강력히 권장합니다. `uv`는 기존 `pip` 및 `venv`보다 빠르고 효율적인 패키지 관리를 제공합니다.
    
    **주요 의존성 패키지:**
    - `fastmcp>=0.1.8` (하지만 requirements.txt에서는 1.0.0 사용)
    - `httpx>=0.27.0` (HTTP 클라이언트)
    - `pyjwt` (JWT 토큰 생성)
    - `python-dotenv` (환경변수 관리)
    - `numpy` (기술적 분석)
    - `pyupbit` (업비트 API 지원)
    - `uvicorn` (ASGI 서버)
    - `matplotlib>=3.7.0` (차트 생성)
    - `pillow>=10.0.0` (이미지 처리)

    만약 `uv`가 설치되어 있지 않다면, 다음 방법으로 먼저 설치해주세요:
    ```bash
    # uv 설치 (Linux, macOS, Windows WSL)
    curl -Ls https://astral.sh/uv/install.sh | sh
    
    # Windows (Powershell):
    # irm https://astral.sh/uv/install.ps1 | iex
    
    # 설치 후, 터미널 환경에 맞게 PATH 설정을 업데이트해야 할 수 있습니다.
    # (예: 쉘 설정 파일(~/.bashrc, ~/.zshrc 등)에 export PATH="$HOME/.astral/bin:$PATH" 추가 후 source ~/.bashrc 또는 터미널 재시작)
    # Windows의 경우, 설치 스크립트가 PATH를 자동으로 업데이트하려고 시도할 수 있습니다.
    ```

    `uv` 설치 후, 프로젝트 루트 디렉토리에서 다음 명령을 실행하여 `uv.lock` 파일에 명시된 정확한 버전의 의존성을 설치합니다:
    ```bash
    uv sync
    ```
    이 명령은 가상 환경을 자동으로 감지하거나 생성하며(` .venv` 폴더), 필요한 패키지를 설치합니다.
    
    (*대안: 기존 `pip` 사용 시 - 권장하지 않음*)
    ```bash
    # python3 -m venv .venv  # 가상환경 생성 (필요시)
    # source .venv/bin/activate # 가상환경 활성화 (Linux/macOS)
    # .venv\\Scripts\\activate # 가상환경 활성화 (Windows)
    # pip install -r requirements.txt
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
    *   **`networks`**: 서버를 특정 Docker 네트워크(예: `nginx-n8n-net`)에 연결합니다. n8n과 이 서버가 모두 동일한 Docker 네트워크 상에서 컨테이너로 실행될 때 서로 통신하기 위해 **매우 중요합니다.** 사용 중인 n8n 컨테이너가 연결된 Docker 네트워크 이름과 동일하게 설정하거나, 필요한 경우 `docker-compose.yml` 파일 내의 `networks` 섹션을 직접 수정하십시오. (예: `nginx-n8n-net` -> 사용자의 n8n 네트워크 이름)
    *   **`env_file`**: `.env` 파일로부터 환경 변수를 로드합니다.
    *   **`volumes`**: 현재 디렉토리를 컨테이너 내부에 마운트하여, 이미지 재빌드 없이 코드 변경사항을 반영할 수 있게 합니다 (개발 시 유용).

2.  **서버 시작:**
    ```bash
    docker-compose up -d --build
    ```
    `--build` 옵션은 Docker 이미지를 강제로 다시 빌드합니다. 코드 변경사항이 있을 때 유용합니다.
    서버를 중지하려면 다음 명령을 사용합니다:
    ```bash
    docker-compose down
    ```

3.  **로그 확인:**
    서버 로그는 다음 명령으로 확인할 수 있습니다:
    ```bash
    docker-compose logs -f upbit-mcp-server
    ```

### n8n 연동

위 설명대로 Upbit MCP 서버가 Docker Compose를 통해 실행되고 n8n 인스턴스와 동일한 Docker 네트워크에 연결되었다면, 다음과 같이 n8n 워크플로우를 설정합니다:

1.  n8n 워크플로우에서 HTTP Request 노드 또는 MCP 관련 커뮤니티 노드(사용 가능하다면)를 사용합니다.
2.  **SSE 엔드포인트 URL**을 `http://upbit_mcp_server:8001/sse`로 설정합니다.
    *   `upbit_mcp_server`: `docker-compose.yml`에 정의된 서비스 이름입니다. Docker 내부 DNS가 이 이름을 공유 네트워크 내의 올바른 컨테이너 IP로 해석합니다.
    *   `8001`: 컨테이너 내부에서 서버가 리스닝하는 포트입니다. (호스트 포트와 동일하게 매핑된 경우)
    *   `/sse`: `FastMCP` 라이브러리에서 SSE 스트림을 위해 사용하는 일반적인 경로입니다. 만약 루트 경로(`/`)로 요청 시 `404 Not Found` 오류가 발생하면, `/sse` 경로를 사용해보세요.
    *   만약 n8n이 Docker 외부(예: 로컬 머신)에서 실행되고 MCP 서버만 Docker로 실행 중이라면, URL은 `http://localhost:8001/sse` (또는 Docker 호스트의 IP와 노출된 포트)가 됩니다.

**⚠️ 주의사항**: 현재 FastMCP import 오류로 인해 서버가 정상 실행되지 않을 수 있습니다. 이 문제는 우선적으로 해결되어야 합니다.

### 개발 서버 실행 (Docker 미사용, 직접 테스트용)

개발 또는 직접 테스트 목적으로 Docker 없이 서버를 실행할 수 있습니다:
```bash
# uv를 사용하여 가상환경 활성화 및 실행 (권장)
uv run python main.py
```
또는 FastMCP의 개발 모드를 사용할 수 있습니다 (FastMCP < 1.0.0 에서 주로 사용되던 방식, 현재 버전에서는 `uv run` 또는 직접 실행 권장):
```bash
# fastmcp dev main.py # 이 방식은 FastMCP 버전에 따라 다를 수 있습니다.
```
주의: 이 방법으로 직접 실행 시, n8n 인스턴스가 서버가 실행 중인 호스트와 포트로 접근할 수 있어야 합니다. n8n 연동 시에는 일반적으로 Docker를 사용하는 것이 더 편리하고 안정적입니다.

## LLM 에이전트 연동 가이드

이 MCP 서버는 LLM(Large Language Model) 기반 에이전트와 효과적으로 연동되도록 설계되었습니다. 에이전트가 본 서버의 기능을 최대한 활용하기 위한 몇 가지 가이드라인은 다음과 같습니다.

### 1. 툴(Tool) 사용 이해

-   **목적 숙지**: 위에 설명된 각 툴의 목적, 필요한 파라미터, 반환 값을 LLM이 정확히 이해해야 합니다. 이는 시스템 프롬프트나 별도의 툴 사용 가이드 문서를 통해 LLM에게 제공될 수 있습니다.
-   **파라미터 추출**: 사용자의 자연어 질문에서 각 툴에 필요한 파라미터를 정확히 추출하는 능력이 중요합니다. 예를 들어, "비트코인 현재가 알려줘"에서 `get_ticker` 툴의 `symbol` 파라미터 값으로 "KRW-BTC"를 추론해야 합니다.
-   **적절한 툴 선택**: 사용자의 요청 의도에 가장 적합한 툴을 선택해야 합니다. 예를 들어, "비트코인 가격"은 `get_ticker`를, "비트코인 최근 체결 기록"은 `get_trades`를 사용하도록 구분해야 합니다.
-   **오류 처리**: 툴 실행 중 오류가 발생하면 (예: API 통신 실패, 잘못된 파라미터 등), 툴은 오류 정보를 담은 JSON 객체(예: `{\"error\": \"에러 메시지\"}`)를 반환합니다. LLM은 이 오류 메시지를 사용자에게 친절하게 전달하고, 필요한 경우 추가 정보를 요청하거나 대안적인 행동을 제안해야 합니다. (기존 `UserError` 발생 방식에서 변경됨)

### 2. 프롬프트(Prompt) 활용

-   제공되는 프롬프트들(`explain_ticker`, `analyze_portfolio`, `order_help`, `trading_strategy`)은 LLM이 특정 작업을 수행하거나 사용자에게 정보를 제공하는 방식을 표준화하고 질을 높이는 데 도움을 줍니다.
-   예를 들어, `get_ticker`로 시세 정보를 얻은 후, `explain_ticker` 프롬프트를 활용하여 사용자에게 더 이해하기 쉬운 형태로 정보를 가공하여 전달할 수 있습니다.

### 3. 리소스(Resource) 활용

-   `market://list`와 같은 리소스를 통해 거래 가능한 마켓 목록 등의 동적인 정보를 얻어 툴 사용 시 정확한 파라미터를 구성하는 데 활용할 수 있습니다.

## 개발 참고 사항

-   **로깅**: 주요 함수의 시작, API 호출 시도, 응답 결과, 오류 발생 등의 상황에 `print(f\"DEBUG_TA: ...\", flush=True)` 또는 `print(f\"ERROR_TA: ...\", flush=True)` 형태의 로그가 추가되어 터미널에서 실시간으로 확인할 수 있습니다. Docker 사용 시 `docker-compose logs -f upbit-mcp-server` 명령으로 로그를 모니터링하세요.
-   **비동기 처리**: API 호출과 관련된 툴 함수들(`get_ticker`, `technical_analysis` 등)은 `async def`로 정의되어 있으며, 내부적으로 `httpx.AsyncClient`를 사용하여 비동기 HTTP 요청을 처리합니다.
-   **EMA 계산**: `technical_analysis`에서 MACD 등의 지표 계산 시, 초기에는 단순 평균(SMA)으로 EMA를 근사했지만, 현재는 보다 표준적인 EMA 계산 방식을 적용하여 정확도를 높였습니다.

## 현재 이슈 및 해결 필요 사항

### ✅ 최근 완료된 주요 기능

1. **차트 이미지 생성 시스템 구축 완료** 
   - `tools/generate_chart_image.py` 구현
   - Matplotlib 기반 캔들스틱/라인/OHLC 차트 생성
   - 날짜 범위 지정 기능 (과거 특정 기간 차트 생성 가능)
   - Nginx + SSL 기반 웹 서빙 (`charts.resteful3.shop`)
   - Docker 환경 완전 구성

2. **백테스팅 시스템 안정화 완료** 
   - 모든 주요 전략 (SMA, RSI, 볼린저 밴드, MACD) 정상 작동
   - 정확한 포트폴리오 추적 및 손익 계산
   - 자연어 요청 처리 프롬프트 완성

3. **백테스팅 차트 시각화 기능 완성** 
   - `tools/generate_backtest_chart.py` 구현
   - 3단 구성 차트 (가격+매매신호, 포트폴리오 가치 변화, 거래량+거래 시점)
   - 백테스팅 실행 시 자동 차트 생성 옵션 (`generate_chart: bool = True`)
   - 모든 매매 신호와 포트폴리오 변화가 정확히 시각화됨

4. **백테스팅 시스템 주요 버그 수정**
   - **매도 수량 기록 문제 해결**: 모든 전략에서 매도 시 수량이 0으로 기록되던 문제 수정
   - **포트폴리오 요약 누락 문제 해결**: RSI, 볼린저 밴드 전략에서 `portfolio_summary` 계산 누락 수정
   - **enhance_trade_history 오류 해결**: `'cash_balance'` 키 오류를 유발하는 함수 호출 제거
   - **MACD 전략 완전 수정**: 매도 로직, 포트폴리오 요약, 에러 처리 모두 정상화
   - 모든 백테스팅 전략 (SMA, RSI, 볼린저 밴드, MACD, 브레이크아웃)이 완전히 정상 작동 확인

### 🚨 긴급 수정 필요
1. **FastMCP Import 오류**: `main.py`에서 `from mcp.server.fastmcp import FastMCP, Context` 라인이 모듈을 찾을 수 없는 오류 발생
2. **의존성 버전 불일치**: 
   - `requirements.txt`: `fastmcp==1.0.0`
   - `pyproject.toml`: `fastmcp>=0.1.8`

### 📋 향후 개선 방향 (TODO)

#### 기능 확장
-   더 많은 기술적 지표 추가 (예: Stochastic Oscillator, Ichimoku Cloud 등)
-   실시간 웹소켓 데이터 스트리밍 지원 (별도 툴 또는 기능으로)
-   사용자별 설정 저장 기능 (예: 선호하는 기술적 지표, 알림 설정 등)
-   툴 파라미터 유효성 검증 강화
-   더 다양한 프롬프트 및 리소스 추가
-   테스트 코드 커버리지 확대

#### 차트 기능 개선
-   더 많은 차트 타입 추가 (헤이킨 아시, 렌코 차트 등)
-   추가 기술적 지표 오버레이 (RSI, MACD, 볼린저 밴드 등)
-   인터랙티브 차트 지원 (Plotly 등)
-   차트 스타일 커스터마이징 옵션
-   다중 마켓 비교 차트

## 라이선스

MIT

---

## ⚠️ 면책 조항 (DISCLAIMER)

**본 프로젝트는 교육 및 연구 목적으로 제공됩니다.**

### 🚨 중요한 경고

1. **투자 손실에 대한 책임 부인**
   - 본 소프트웨어를 사용하여 발생하는 모든 투자 손실에 대해 개발자, 기여자, 배포자는 **어떠한 책임도 지지 않습니다**.
   - 암호화폐 투자는 높은 위험을 수반하며, 투자 원금의 전액 손실 가능성이 있습니다.

2. **백테스팅 결과의 한계**
   - 백테스팅 결과는 과거 데이터를 기반으로 한 시뮬레이션이며, **미래 수익을 보장하지 않습니다**.
   - 실제 거래 환경에서는 슬리피지, 유동성 부족, 거래소 장애 등 백테스팅에서 고려되지 않은 요소들이 성과에 영향을 줄 수 있습니다.

3. **소프트웨어 품질 보증 부인**
   - 본 소프트웨어는 "있는 그대로(AS-IS)" 제공되며, **명시적 또는 묵시적 보증 없이** 제공됩니다.
   - 소프트웨어의 오류, 버그, 보안 취약점으로 인한 손실에 대해 책임지지 않습니다.

4. **사용자 책임**
   - 본 프로젝트를 사용하기 전에 충분한 테스트와 검증을 수행하시기 바랍니다.
   - 실제 자금을 투자하기 전에 모의 거래나 소액 테스트를 통해 시스템을 충분히 이해하시기 바랍니다.
   - 투자 결정은 전적으로 사용자의 책임이며, 전문가의 조언을 구하시기 바랍니다.

### 📋 권장 사항

- 본 프로젝트는 **교육 목적**으로만 사용하시기 바랍니다.
- 실제 투자에 사용하기 전에 **충분한 검증과 테스트**를 수행하시기 바랍니다.
- 감당할 수 있는 범위 내에서만 투자하시기 바랍니다.
- 투자 전에 **전문가의 조언**을 구하시기 바랍니다.

**본 프로젝트를 사용함으로써 위의 면책 조항에 동의하는 것으로 간주됩니다.**
