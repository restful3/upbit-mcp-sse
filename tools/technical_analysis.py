from fastmcp import Context
import httpx
import numpy as np
from typing import List, Literal, Dict, Any, Optional, Set
from config import API_BASE

# 사용 가능한 지표 및 신호 키 정의
# AVAILABLE_INDICATOR_KEYS: Set[str] = {
#     "sma", "rsi", "bollinger_bands", "macd", "stochastic", "volume", "pivots", "current_price"
# }
# AVAILABLE_SIGNAL_KEYS: Set[str] = {
#     "ma_signal", "rsi_signal", "bb_signal", "macd_signal", "stoch_signal", "overall_signal"
# }
# ALL_KEYS: Set[str] = AVAILABLE_INDICATOR_KEYS.union(AVAILABLE_SIGNAL_KEYS)

# overall_signal이 의존하는 개별 신호 키들
# OVERALL_SIGNAL_DEPENDENCIES: Set[str] = {
#     "ma_signal", "rsi_signal", "bb_signal", "macd_signal", "stoch_signal"
# }

async def technical_analysis(
    market: str,
    interval: Literal["minute1", "minute3", "minute5", "minute10", "minute15", "minute30", "minute60", "minute240", "day", "week", "month"] = "day",
    count: int = 200,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    지정된 마켓의 캔들 데이터를 기반으로 다양한 기술적 지표와 매매 신호를 계산합니다.

    Upbit API를 통해 캔들 데이터를 조회한 후, `numpy`를 사용하여 이동평균(SMA), 상대강도지수(RSI), 
    볼린저 밴드, MACD, 거래량 등 주요 기술적 지표를 계산합니다. 
    이러한 지표들을 종합하여 간단한 매매 신호("strong_buy", "buy", "sell", "strong_sell", "neutral")를 제공합니다.

    Args:
        market (str): 분석할 마켓 코드 (예: "KRW-BTC").
        interval (Literal[...]): 캔들의 시간 간격. 
            "minute1"~"minute240", "day", "week", "month" 중 선택. 기본값은 "day"입니다.
        count (int): 분석에 사용할 최신 캔들의 개수. 기본값 및 최대값은 200입니다.
        ctx (Context, optional): FastMCP 컨텍스트 객체. 함수 실행 중 정보나 오류를 로깅하는 데 사용됩니다.

    Returns:
        Dict[str, Any]:
            - 성공 시: 기술적 분석 결과를 담은 딕셔너리. 주요 키는 다음과 같습니다:
                - `market` (str): 분석한 마켓 코드
                - `interval` (str): 사용된 캔들 인터벌
                - `indicators` (Dict): 계산된 기술적 지표 값
                    - `current_price` (float): 현재가
                    - `sma` (Dict): 단순 이동 평균 (e.g., `sma_20`, `sma_50`)
                    - `rsi` (float): 상대강도지수
                    - `bollinger_bands` (Dict): 볼린저 밴드 (`upper`, `middle`, `lower`)
                    - `macd` (Dict): MACD (`line`, `signal`, `histogram`)
                    - `volume_analysis` (Dict): 거래량 분석 (`current`, `sma_20`, `ratio`)
                - `signals` (Dict): 각 지표에 대한 신호
                    - `ma_signal` ('bullish'|'bearish'|'neutral')
                    - `rsi_signal` ('overbought'|'oversold'|'neutral')
                    - `bb_signal` ('overbought'|'oversold'|'neutral')
                    - `macd_signal` ('bullish'|'bearish'|'neutral')
                - `overall_signal` (str): 모든 신호를 종합한 최종 매매 신호.
            - 실패 시: `{"error": "오류 메시지"}` 형식의 딕셔너리.

    Example:
        >>> btc_analysis = await technical_analysis(market="KRW-BTC", interval="day")
        >>> if "error" not in btc_analysis:
        ...     print(f"BTC 일봉 분석 종합 신호: {btc_analysis['overall_signal']}")
        ...     print(f"현재 RSI: {btc_analysis['indicators']['rsi']:.2f}")
        ... else:
        ...     print(f"오류: {btc_analysis['error']}")
    """
    if ctx:
        ctx.info(f"기술적 분석 시작: {market} {interval}")
    
    # 캔들스틱 데이터 가져오기
    # interval에 따라 API 엔드포인트 포맷 조정
    if interval in ["day", "week", "month"]:
        url_interval = f"{interval}s"
    elif interval.startswith("minute"):
        # 분봉의 경우 interval에 unit이 포함되어 있으므로 그대로 사용
        # 예: minute1, minute3, ... minute240
        url_interval = interval 
    else:
        # 혹시 모를 다른 interval 값에 대한 기본 처리 (현재 정의된 Literal 타입에는 해당되지 않음)
        url_interval = interval

    url = f"{API_BASE}/candles/{url_interval}"
    params = {
        'market': market,
        'count': str(count)
    }
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url, params=params)
            
            if res.status_code != 200:
                error_msg = f"업비트 API 오류: {res.status_code} - {res.text}"
                if ctx:
                    ctx.error(error_msg)
                return {"error": error_msg}
            
            candles = res.json()
            if not candles:
                error_msg = "데이터를 가져오는데 실패했습니다. API 응답이 비어있습니다."
                if ctx:
                    ctx.error(error_msg)
                return {"error": error_msg}
    except httpx.RequestError as e:
        error_msg = f"API 호출 중 httpx.RequestError 발생: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"API 호출 중 알 수 없는 오류 발생: {str(e)}, Type: {type(e).__name__}"
        if ctx:
            ctx.error(error_msg)
        return {"error": error_msg}
    
    # 가격 데이터 추출
    try:
        closes = np.array([float(candle["trade_price"]) for candle in candles])
        highs = np.array([float(candle["high_price"]) for candle in candles])
        lows = np.array([float(candle["low_price"]) for candle in candles])
        volumes = np.array([float(candle["candle_acc_trade_volume"]) for candle in candles])
    except (KeyError, ValueError) as e:
        error_msg = f"데이터 처리 중 오류 발생 (KeyError or ValueError): {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"데이터 처리 중 알 수 없는 오류 발생: {str(e)}, Type: {type(e).__name__}"
        if ctx:
            ctx.error(error_msg)
        return {"error": error_msg}

    # 기술적 지표 계산
    try:
        # 1. 이동평균선 (SMA)
        sma_20 = np.mean(closes[-20:])
        sma_50 = np.mean(closes[-50:])
        sma_200 = np.mean(closes[-200:]) if len(closes) >= 200 else None
        
        # 2. RSI (14일)
        def calculate_rsi(prices, period=14):
            # Ensure prices has enough data
            if len(prices) < period + 1: # Need at least period + 1 for np.diff and initial mean
                 return np.nan # Return NaN or some default if not enough data

            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # Ensure there are enough gains/losses for the initial average
            if len(gains) < period or len(losses) < period:
                return np.nan

            avg_gain = np.mean(gains[:period])
            avg_loss = np.mean(losses[:period])
            
            for i in range(period, len(deltas)):
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                return 100.0
            rs = avg_gain / avg_loss
            rsi_val = 100.0 - (100.0 / (1.0 + rs))
            return rsi_val
        
        rsi = calculate_rsi(closes)
        
        # 3. 볼린저 밴드 (20일, 2 표준편차)
        def calculate_bollinger_bands(prices, period=20, num_std=2):
            if len(prices) < period:
                return np.nan, np.nan, np.nan
            sma = np.mean(prices[-period:])
            std = np.std(prices[-period:])
            upper_band = sma + (std * num_std)
            lower_band = sma - (std * num_std)
            return upper_band, sma, lower_band
        
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(closes)
        
        # 4. MACD (12, 26, 9)
        def calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9):
            if len(prices) < slow_period:
                return np.nan, np.nan, np.nan

            # Calculate Fast EMA
            ema_fast = np.full_like(prices, np.nan)
            ema_fast[fast_period-1] = np.mean(prices[:fast_period])
            for i in range(fast_period, len(prices)):
                ema_fast[i] = prices[i] * (2 / (fast_period + 1)) + ema_fast[i-1] * (1 - (2 / (fast_period + 1)))

            # Calculate Slow EMA
            ema_slow = np.full_like(prices, np.nan)
            ema_slow[slow_period-1] = np.mean(prices[:slow_period])
            for i in range(slow_period, len(prices)):
                ema_slow[i] = prices[i] * (2 / (slow_period + 1)) + ema_slow[i-1] * (1 - (2 / (slow_period + 1)))
            
            macd_line = ema_fast - ema_slow

            # Calculate Signal Line (EMA of MACD line)
            signal_line_val = np.full_like(macd_line, np.nan)
            # Ensure there are enough non-NaN MACD values to start signal calculation
            valid_macd_start_index = -1
            for i in range(len(macd_line)):
                if not np.isnan(macd_line[i]):
                    valid_macd_start_index = i
                    break
            
            if valid_macd_start_index != -1 and len(macd_line) - valid_macd_start_index >= signal_period:
                signal_line_val[valid_macd_start_index + signal_period - 1] = np.mean(macd_line[valid_macd_start_index : valid_macd_start_index + signal_period])
                for i in range(valid_macd_start_index + signal_period, len(macd_line)):
                    signal_line_val[i] = macd_line[i] * (2 / (signal_period + 1)) + signal_line_val[i-1] * (1 - (2 / (signal_period + 1)))
            
            histogram_val = macd_line - signal_line_val
            
            # Return the last values
            return (macd_line[-1] if len(macd_line) > 0 and not np.isnan(macd_line[-1]) else np.nan,
                    signal_line_val[-1] if len(signal_line_val) > 0 and not np.isnan(signal_line_val[-1]) else np.nan,
                    histogram_val[-1] if len(histogram_val) > 0 and not np.isnan(histogram_val[-1]) else np.nan)

        macd, signal_line, histogram = calculate_macd(closes)
        
        # 5. 거래량 분석
        current_volume = volumes[-1] if len(volumes) > 0 else np.nan
        if len(volumes) >= 20:
            volume_sma = np.mean(volumes[-20:])
            volume_ratio = current_volume / volume_sma if volume_sma > 0 and not np.isnan(current_volume) else np.nan
        else:
            volume_sma = np.nan
            volume_ratio = np.nan
        
        # 신호 생성
        current_price = closes[-1] if len(closes) > 0 else np.nan
        
        # 이동평균선 신호
        ma_signal = "neutral"
        if not np.isnan(current_price) and not np.isnan(sma_20) and not np.isnan(sma_50) and sma_200 is not None and not np.isnan(sma_200):
            if current_price > sma_20 and sma_20 > sma_50:
                ma_signal = "bullish"
            elif current_price < sma_20 and sma_20 < sma_50:
                ma_signal = "bearish"
        
        # RSI 신호
        rsi_signal = "neutral"
        if not np.isnan(rsi):
            if rsi > 70:
                rsi_signal = "overbought"
            elif rsi < 30:
                rsi_signal = "oversold"
        
        # 볼린저 밴드 신호
        bb_signal = "neutral"
        if not np.isnan(current_price) and not np.isnan(bb_upper) and not np.isnan(bb_lower):
            if current_price > bb_upper:
                bb_signal = "overbought"
            elif current_price < bb_lower:
                bb_signal = "oversold"
        
        # MACD 신호
        macd_signal = "neutral"
        if not np.isnan(macd) and not np.isnan(signal_line) and not np.isnan(histogram):
            if macd > signal_line and histogram > 0:
                macd_signal = "bullish"
            elif macd < signal_line and histogram < 0:
                macd_signal = "bearish"
        
        # 거래량 신호
        volume_signal = "neutral"
        if not np.isnan(volume_ratio):
            if volume_ratio > 1.5:
                volume_signal = "high"
            elif volume_ratio < 0.5:
                volume_signal = "low"
        
        # 종합 신호
        defined_signals = [sig for sig in [ma_signal, rsi_signal, bb_signal, macd_signal] if sig != "neutral"]
        bullish_signals = sum(1 for signal_val in defined_signals if signal_val in ["bullish", "oversold"])
        bearish_signals = sum(1 for signal_val in defined_signals if signal_val in ["bearish", "overbought"])
        
        overall_signal = "neutral"
        if len(defined_signals) > 0:
            if bullish_signals >= max(1, len(defined_signals) * 0.6):
                overall_signal = "strong_buy"
            elif bullish_signals > bearish_signals and bullish_signals >= max(1, len(defined_signals) * 0.4):
                overall_signal = "buy"
            elif bearish_signals >= max(1, len(defined_signals) * 0.6):
                overall_signal = "strong_sell"
            elif bearish_signals > bullish_signals and bearish_signals >= max(1, len(defined_signals) * 0.4):
                overall_signal = "sell"

        result = {
            "status": "ok",
            "market": market,
            "interval": interval,
            "current_price": current_price if not np.isnan(current_price) else "N/A",
            "indicators": {
                "sma": {
                    "sma_20": sma_20 if not np.isnan(sma_20) else "N/A",
                    "sma_50": sma_50 if not np.isnan(sma_50) else "N/A",
                    "sma_200": sma_200 if sma_200 is not None and not np.isnan(sma_200) else "N/A"
                },
                "rsi": rsi if not np.isnan(rsi) else "N/A",
                "bollinger_bands": {
                    "upper": bb_upper if not np.isnan(bb_upper) else "N/A",
                    "middle": bb_middle if not np.isnan(bb_middle) else "N/A",
                    "lower": bb_lower if not np.isnan(bb_lower) else "N/A"
                },
                "macd": {
                    "macd": macd if not np.isnan(macd) else "N/A",
                    "signal": signal_line if not np.isnan(signal_line) else "N/A",
                    "histogram": histogram if not np.isnan(histogram) else "N/A"
                },
                "volume": {
                    "current": current_volume if not np.isnan(current_volume) else "N/A",
                    "sma": volume_sma if not np.isnan(volume_sma) else "N/A",
                    "ratio": volume_ratio if not np.isnan(volume_ratio) else "N/A"
                }
            },
            "signals": {
                "ma_signal": ma_signal,
                "rsi_signal": rsi_signal,
                "bb_signal": bb_signal,
                "macd_signal": macd_signal,
                "volume_signal": volume_signal,
                "overall_signal": overall_signal
            }
        }
        
        if ctx:
            ctx.info(f"기술적 분석 완료: {market} {interval}")
        return result
        
    except Exception as e:
        error_msg = f"기술적 지표 계산 또는 신호 생성 중 알 수 없는 오류 발생: {str(e)}, Type: {type(e).__name__}"
        if ctx:
            ctx.error(error_msg)
        return {"error": error_msg}

def main_test():
    class MockContext:
        def info(self, msg): print(f"INFO: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")

    ctx = MockContext()
    print("SYNC_DEBUG: main_test는 서버를 통해 테스트해야 합니다.")

if __name__ == '__main__':
    main_test()