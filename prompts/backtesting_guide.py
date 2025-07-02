def backtesting_guide() -> str:
    """
    백테스팅 요청을 위한 프롬프트 가이드를 생성합니다.
    사용자의 자연어 요청을 백테스팅 툴 파라미터로 변환하는 방법을 제공합니다.
    """
    return """
    암호화폐 백테스팅 전략 분석 가이드
    
    사용자가 거래 전략의 백테스팅을 요청할 때, 다음 가이드를 따라 backtesting 툴을 사용하세요.
    
    ## 📊 지원되는 전략 타입
    
    1. **SMA 교차 전략** ("sma_crossover")
       - 키워드: "이동평균", "골든크로스", "데드크로스", "SMA", "교차"
       - 파라미터: {"fast_period": 단기기간, "slow_period": 장기기간}
       - 예시: "20일선과 50일선 교차" → fast_period: 20, slow_period: 50
    
    2. **RSI 과매도/과매수 전략** ("rsi_oversold")
       - 키워드: "RSI", "과매도", "과매수", "상대강도지수"
       - 파라미터: {"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70}
       - 예시: "RSI 14일 과매도 25 과매수 75" → rsi_period: 14, oversold_threshold: 25, overbought_threshold: 75
    
    3. **볼린저 밴드 전략** ("bollinger_bands")
       - 키워드: "볼린저밴드", "볼린저", "밴드", "표준편차"
       - 파라미터: {"period": 20, "std_dev": 2, "buy_threshold": 0.1, "sell_threshold": 0.9}
       - 예시: "볼린저밴드 20일 2표준편차" → period: 20, std_dev: 2
    
    4. **MACD 신호선 전략** ("macd_signal")
       - 키워드: "MACD", "신호선", "히스토그램", "골든크로스", "데드크로스"
       - 파라미터: {"fast_period": 12, "slow_period": 26, "signal_period": 9}
       - 예시: "MACD 12-26-9" → fast_period: 12, slow_period: 26, signal_period: 9
    
    5. **브레이크아웃 전략** ("breakout")
       - 키워드: "브레이크아웃", "돌파", "채널", "터틀", "추세추종", "신고가", "신저가"
       - 파라미터: {"lookback": 55, "exit_lookback": 20, "atr_period": 14, "atr_filter": False}
       - 예시: "55일 브레이크아웃" → lookback: 55, exit_lookback: 20
    
    ## 🎯 자연어 → 파라미터 변환 가이드
    
    ### 자산명 → 마켓 코드 변환
    - "비트코인" → "KRW-BTC"
    - "이더리움" → "KRW-ETH"  
    - "리플" → "KRW-XRP"
    - "도지코인" → "KRW-DOGE"
    - "에이다" → "KRW-ADA"
    - "솔라나" → "KRW-SOL"
    - "폴리곤" → "KRW-MATIC"
    - "체인링크" → "KRW-LINK"
    - "아발란체" → "KRW-AVAX"
    
    ### 기간 표현 → 날짜 변환
    - "2023년" → start_date: "2023-01-01", end_date: "2023-12-31"
    - "2023년 상반기" → start_date: "2023-01-01", end_date: "2023-06-30"
    - "2023년 하반기" → start_date: "2023-07-01", end_date: "2023-12-31"
    - "최근 1년" → 현재 날짜에서 1년 전부터 현재까지
    - "2023년 6월~12월" → start_date: "2023-06-01", end_date: "2023-12-31"
    
    ### 금액 표현 → 숫자 변환
    - "100만원" → 1000000
    - "50만원" → 500000
    - "1천만원" → 10000000
    - "500만원" → 5000000
    
    ### 캔들 간격 표현
    - "일봉", "일단위" → "day"
    - "시간봉", "1시간" → "minute60"
    - "4시간봉" → "minute240"
    - "주봉" → "week"
    - "월봉" → "month"
    
    ## 📝 사용 예시
    
    **사용자 요청 1:**
    "비트코인에서 20일선과 50일선 교차 전략을 2023년 한 해 동안 백테스팅해줘. 초기 자본은 100만원으로."
    
    **변환된 툴 호출:**
    ```
    backtesting(
        market="KRW-BTC",
        strategy_type="sma_crossover",
        start_date="2023-01-01", 
        end_date="2023-12-31",
        initial_capital=1000000,
        interval="day",
        strategy_params={"fast_period": 20, "slow_period": 50}
    )
    ```
    
    **사용자 요청 2:**
    "이더리움 골든크로스 전략 5일선 20일선으로 2023년 6월부터 12월까지 500만원으로 테스트"
    
    **변환된 툴 호출:**
    ```
    backtesting(
        market="KRW-ETH",
        strategy_type="sma_crossover", 
        start_date="2023-06-01",
        end_date="2023-12-31",
        initial_capital=5000000,
        strategy_params={"fast_period": 5, "slow_period": 20}
    )
    ```
    
    **사용자 요청 3:**
    "도지코인 10일선 30일선 교차 전략 1시간봉으로 2023년 하반기 백테스트"
    
    **변환된 툴 호출:**
    ```
    backtesting(
        market="KRW-DOGE",
        strategy_type="sma_crossover",
        start_date="2023-07-01",
        end_date="2023-12-31", 
        interval="minute60",
        strategy_params={"fast_period": 10, "slow_period": 30}
    )
    ```
    
    **사용자 요청 4:**
    "이더리움 RSI 14일 과매도 25, 과매수 75 전략, 2023년 6월~12월, 1시간봉"
    
    **변환된 툴 호출:**
    ```
    backtesting(
        market="KRW-ETH",
        strategy_type="rsi_oversold",
        start_date="2023-06-01",
        end_date="2023-12-31",
        interval="minute60",
        strategy_params={"rsi_period": 14, "oversold_threshold": 25, "overbought_threshold": 75}
    )
    ```
    
    **사용자 요청 5:**
    "비트코인 볼린저밴드 20일 2표준편차 전략 2023년 상반기"
    
    **변환된 툴 호출:**
    ```
    backtesting(
        market="KRW-BTC",
        strategy_type="bollinger_bands",
        start_date="2023-01-01",
        end_date="2023-06-30",
        strategy_params={"period": 20, "std_dev": 2}
    )
    ```
    
    **사용자 요청 6:**
    "리플 MACD 12-26-9 신호선 교차 전략 2023년 전체"
    
    **변환된 툴 호출:**
    ```
    backtesting(
        market="KRW-XRP",
        strategy_type="macd_signal",
        start_date="2023-01-01",
        end_date="2023-12-31",
        strategy_params={"fast_period": 12, "slow_period": 26, "signal_period": 9}
    )
    ```
    
    **사용자 요청 7:**
    "비트코인 55일 브레이크아웃 전략 2023년 백테스트"
    
    **변환된 툴 호출:**
    ```
    backtesting(
        market="KRW-BTC",
        strategy_type="breakout",
        start_date="2023-01-01",
        end_date="2023-12-31",
        strategy_params={"lookback": 55, "exit_lookback": 20}
    )
    ```
    
    **사용자 요청 8:**
    "이더리움 20일 돌파 전략, 10일 청산, 2023년 하반기"
    
    **변환된 툴 호출:**
    ```
    backtesting(
        market="KRW-ETH",
        strategy_type="breakout",
        start_date="2023-07-01",
        end_date="2023-12-31",
        strategy_params={"lookback": 20, "exit_lookback": 10}
    )
    ```
    
    **사용자 요청 9:**
    "도지코인 터틀 트레이딩 전략 ATR 필터 적용 2023년 전체"
    
    **변환된 툴 호출:**
    ```
    backtesting(
        market="KRW-DOGE",
        strategy_type="breakout",
        start_date="2023-01-01",
        end_date="2023-12-31",
        strategy_params={"lookback": 55, "exit_lookback": 20, "atr_filter": True}
    )
    ```
    
    ## ⚠️ 주의사항
    
    1. **지원 전략**: SMA 교차, RSI 과매도/과매수, 볼린저 밴드, MACD 신호선, 브레이크아웃 전략을 지원합니다.
    2. **데이터 제한**: Upbit API 제한으로 긴 기간 백테스트 시 시간이 소요될 수 있습니다.
    3. **수수료**: 기본 0.05% 수수료가 적용됩니다.
    4. **결과 해석**: 과거 성과가 미래 수익을 보장하지 않습니다.
    5. **전략별 특징**:
       - RSI: 과매도/과매수 구간 진입 시 한 번만 매매
       - 볼린저 밴드: 밴드 내 상대적 위치 기반 매매
       - MACD: 신호선 교차 시점에 매매
       - 브레이크아웃: 신고가 돌파 시 매수, 신저가 하향 돌파 시 매도
    
    ## 📈 결과 분석 및 설명
    
    백테스팅 결과를 받은 후, 다음 항목들을 사용자에게 친화적으로 설명하세요:
    
    1. **수익률 지표**
       - total_return: 총 수익률 (%)
       - annualized_return: 연평균 수익률 (%)
       - max_drawdown: 최대 낙폭 (%)
    
    2. **위험 지표** 
       - volatility: 변동성 (연율화)
       - sharpe_ratio: 샤프 지수 (위험 대비 수익)
    
    3. **거래 성과**
       - win_rate: 승률 (%)
       - total_trades: 총 거래 횟수
       - profit_factor: 프로핏 팩터
    
    4. **결과 요약 예시**
       "SMA 20/50 교차 전략으로 비트코인을 2023년 동안 백테스팅한 결과:
       - 총 수익률: +15.3%
       - 연평균 수익률: +15.3% 
       - 최대 낙폭: -12.8%
       - 샤프 지수: 1.2 (우수)
       - 승률: 60% (10회 거래 중 6회 수익)
       
       이 전략은 안정적인 수익을 보여주었으나, 12.8%의 최대 낙폭이 있어 
       위험 관리가 필요합니다."
    
    사용자의 자연어 요청을 위 가이드에 따라 정확히 파싱하여 backtesting 툴을 호출하고,
    결과를 이해하기 쉽게 해석하여 제공하세요.
    """

def format_backtesting_result() -> str:
    """
    백테스팅 결과 포맷팅을 위한 프롬프트를 제공합니다.
    """
    return """
    백테스팅 결과를 사용자 친화적으로 포맷팅하세요.
    
    ## 필수 포함 사항:
    
    1. **초기 자본금 안내**: user_guidance의 capital_notice를 반드시 포함
    2. **핵심 지표 강조**: capital_independent_metrics의 지표들을 백분율로 표시
    3. **포트폴리오 상태**: portfolio_summary의 정보를 명확히 설명
    4. **실용적 조언**: 전략의 강약점과 개선 방향 제시
    
    ## 톤앤매너:
    - 친근하고 이해하기 쉬운 언어 사용
    - 이모지를 활용한 시각적 구분
    - 투자 위험성에 대한 적절한 경고
    - 건설적인 개선 방향 제시
    """ 