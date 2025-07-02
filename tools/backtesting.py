from fastmcp import Context
import httpx
import numpy as np
from typing import Literal, Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
from tools.get_candles import get_candles
from config import API_BASE

async def backtesting(
    market: str,
    strategy_type: Literal["sma_crossover", "rsi_oversold", "bollinger_bands", "macd_signal", "breakout", "custom"],
    start_date: str,
    end_date: str,
    initial_capital: float = 1000000,
    interval: Literal["minute1", "minute3", "minute5", "minute10", "minute15", "minute30", "minute60", "minute240", "day", "week", "month"] = "day",
    strategy_params: Optional[dict] = None,
    commission_rate: float = 0.0005,
    generate_chart: bool = True,
    ctx: Optional[Context] = None
) -> dict:
    """
    지정된 마켓에서 다양한 거래 전략을 백테스팅합니다.

    이 함수는 과거 캔들 데이터를 기반으로 지정된 거래 전략을 시뮬레이션하여
    성과 지표와 거래 내역을 제공합니다. 사용자의 자연어 요청을 파싱하여
    해당 전략에 맞는 백테스팅을 수행합니다.

    Args:
        market (str): 백테스트할 마켓 코드 (예: "KRW-BTC")
        strategy_type (Literal): 사용할 거래 전략 타입
            - "sma_crossover": SMA 골든크로스/데드크로스 전략
            - "rsi_oversold": RSI 과매도/과매수 전략 
            - "bollinger_bands": 볼린저 밴드 전략
            - "macd_signal": MACD 신호선 교차 전략
            - "breakout": 브레이크아웃 추세 추종 전략
            - "custom": 사용자 정의 전략 (향후 지원 예정)
        start_date (str): 백테스트 시작일 (YYYY-MM-DD 형식)
        end_date (str): 백테스트 종료일 (YYYY-MM-DD 형식)
        initial_capital (float): 초기 자본금 (기본: 1,000,000원)
        interval (Literal): 캔들 간격 (기본: "day")
        strategy_params (Optional[dict]): 전략별 파라미터
            - sma_crossover: {"fast_period": 20, "slow_period": 50}
            - rsi_oversold: {"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70}
            - bollinger_bands: {"period": 20, "std_dev": 2, "buy_threshold": 0.1, "sell_threshold": 0.9}
            - macd_signal: {"fast_period": 12, "slow_period": 26, "signal_period": 9}
            - breakout: {"lookback": 55, "exit_lookback": 20, "atr_period": 14, "atr_filter": False}
        commission_rate (float): 거래 수수료율 (기본: 0.0005 = 0.05%)
        generate_chart (bool): 백테스팅 차트 생성 여부 (기본: True)
        ctx (Context, optional): FastMCP 컨텍스트 객체

    Returns:
        dict: 백테스팅 결과
            - strategy_info: 전략 정보 및 설정
            - performance_metrics: 성과 지표 (수익률, 샤프비율, 최대낙폭 등)
            - trade_history: 거래 내역 리스트
            - monthly_returns: 월별 수익률
            - drawdown_periods: 주요 드로우다운 구간

    Example:
        >>> # 비트코인 SMA 20/50 교차 전략 백테스팅 (2023년)
        >>> result = await backtesting(
        ...     market="KRW-BTC",
        ...     strategy_type="sma_crossover", 
        ...     start_date="2023-01-01",
        ...     end_date="2023-12-31",
        ...     strategy_params={"fast_period": 20, "slow_period": 50}
        ... )
        >>> print(f"총 수익률: {result['performance_metrics']['total_return']:.2%}")
    """
    
    if ctx:
        ctx.info(f"백테스팅 시작: {market} {strategy_type} ({start_date} ~ {end_date})")
    
    # 입력 파라미터 유효성 검사
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        if start_dt >= end_dt:
            return {"error": "시작일이 종료일보다 늦거나 같습니다."}
    except ValueError:
        return {"error": "날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요."}
    
    if initial_capital <= 0:
        return {"error": "초기 자본은 0보다 커야 합니다."}
    
    if commission_rate < 0 or commission_rate > 0.1:
        return {"error": "수수료율은 0과 0.1 사이의 값이어야 합니다."}
    
    # 지원되지 않는 전략 체크
    if strategy_type == "custom":
        return {"error": f"{strategy_type} 전략은 아직 지원되지 않습니다."}
    
    # 전략 파라미터 설정 및 유효성 검사
    if strategy_params is None:
        strategy_params = {}
    
    # 전략별 파라미터 초기화
    fast_period = slow_period = rsi_period = period = signal_period = 0
    oversold_threshold = overbought_threshold = std_dev = buy_threshold = sell_threshold = 0.0
    lookback = exit_lookback = atr_period = 0
    atr_filter = False
    
    # 전략별 파라미터 유효성 검사
    if strategy_type == "sma_crossover":
        fast_period = strategy_params.get("fast_period", 20)
        slow_period = strategy_params.get("slow_period", 50)
        
        if fast_period >= slow_period:
            return {"error": "단기 이동평균 기간이 장기 이동평균 기간보다 작아야 합니다."}
        
        if fast_period < 1 or slow_period < 1:
            return {"error": "이동평균 기간은 1 이상이어야 합니다."}
            
    elif strategy_type == "rsi_oversold":
        rsi_period = strategy_params.get("rsi_period", 14)
        oversold_threshold = strategy_params.get("oversold_threshold", 30)
        overbought_threshold = strategy_params.get("overbought_threshold", 70)
        
        if rsi_period < 2:
            return {"error": "RSI 기간은 2 이상이어야 합니다."}
        
        if oversold_threshold >= overbought_threshold:
            return {"error": "과매도 임계값이 과매수 임계값보다 작아야 합니다."}
            
        if oversold_threshold < 0 or overbought_threshold > 100:
            return {"error": "RSI 임계값은 0-100 범위 내에 있어야 합니다."}
            
    elif strategy_type == "bollinger_bands":
        period = strategy_params.get("period", 20)
        std_dev = strategy_params.get("std_dev", 2)
        buy_threshold = strategy_params.get("buy_threshold", 0.1)
        sell_threshold = strategy_params.get("sell_threshold", 0.9)
        
        if period < 2:
            return {"error": "볼린저 밴드 기간은 2 이상이어야 합니다."}
            
        if std_dev <= 0:
            return {"error": "표준편차 배수는 0보다 커야 합니다."}
            
        if buy_threshold >= sell_threshold:
            return {"error": "매수 임계값이 매도 임계값보다 작아야 합니다."}
            
        if buy_threshold < 0 or sell_threshold > 1:
            return {"error": "임계값은 0-1 범위 내에 있어야 합니다."}
            
    elif strategy_type == "macd_signal":
        fast_period = strategy_params.get("fast_period", 12)
        slow_period = strategy_params.get("slow_period", 26)
        signal_period = strategy_params.get("signal_period", 9)
        
        if fast_period >= slow_period:
            return {"error": "MACD 단기 기간이 장기 기간보다 작아야 합니다."}
            
        if fast_period < 1 or slow_period < 1 or signal_period < 1:
            return {"error": "MACD 기간들은 1 이상이어야 합니다."}
            
    elif strategy_type == "breakout":
        lookback = strategy_params.get("lookback", 55)
        exit_lookback = strategy_params.get("exit_lookback", 20)
        atr_period = strategy_params.get("atr_period", 14)
        atr_filter = strategy_params.get("atr_filter", False)
        
        if lookback < 1 or exit_lookback < 1:
            return {"error": "브레이크아웃 기간은 1 이상이어야 합니다."}
            
        if atr_period < 1:
            return {"error": "ATR 기간은 1 이상이어야 합니다."}
            
        if lookback <= exit_lookback:
            return {"error": "진입 채널 기간이 청산 채널 기간보다 길어야 합니다."}
    
    try:
        # 캔들 데이터 수집
        candles_data = await collect_candle_data(market, interval, start_date, end_date, ctx)
        if "error" in candles_data:
            return candles_data
        
        candles = candles_data["candles"]
        
        # 전략별 최소 데이터 요구량 확인
        min_required_candles = 50  # 기본값
        if strategy_type == "sma_crossover":
            min_required_candles = max(fast_period, slow_period)
        elif strategy_type == "rsi_oversold":
            min_required_candles = rsi_period + 1
        elif strategy_type == "bollinger_bands":
            min_required_candles = period
        elif strategy_type == "macd_signal":
            min_required_candles = max(fast_period, slow_period) + signal_period
        elif strategy_type == "breakout":
            min_required_candles = max(lookback, exit_lookback, atr_period) + 5
            
        if len(candles) < min_required_candles:
            return {"error": f"데이터가 부족합니다. 최소 {min_required_candles}개의 캔들이 필요하지만 {len(candles)}개만 있습니다."}
        
        # 백테스팅 실행
        if strategy_type == "sma_crossover":
            result = await backtest_sma_crossover(
                candles, initial_capital, fast_period, slow_period, commission_rate, ctx
            )
        elif strategy_type == "rsi_oversold":
            result = await backtest_rsi_oversold(
                candles, initial_capital, rsi_period, oversold_threshold, overbought_threshold, commission_rate, ctx
            )
        elif strategy_type == "bollinger_bands":
            result = await backtest_bollinger_bands(
                candles, initial_capital, period, std_dev, buy_threshold, sell_threshold, commission_rate, ctx
            )
        elif strategy_type == "macd_signal":
            result = await backtest_macd_signal(
                candles, initial_capital, fast_period, slow_period, signal_period, commission_rate, ctx
            )
        elif strategy_type == "breakout":
            result = await backtest_breakout(
                candles, initial_capital, lookback, exit_lookback, atr_period, atr_filter, commission_rate, ctx
            )
        
        # 전략 정보 추가
        result["strategy_info"] = {
            "strategy": strategy_type,
            "market": market,
            "interval": interval,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "capital_source": "user_specified" if initial_capital != 1000000 else "default",
            "commission_rate": commission_rate,
            "strategy_params": strategy_params,
            "total_candles": len(candles)
        }
        
        # 사용자 안내 메시지 추가
        if initial_capital == 1000000:
            result["user_guidance"] = {
                "capital_notice": "💡 초기 자본금이 지정되지 않아 기본값 1,000,000원을 사용했습니다.",
                "recalculation_guide": "다른 자본금으로 계산하려면 'initial_capital' 파라미터를 지정하세요.",
                "quick_calculation": f"간단 계산법: (원하는 자본금 ÷ 1,000,000) × {result['portfolio_summary']['absolute_profit']:.0f}원",
                "examples": [
                    f"500만원 기준: {result['portfolio_summary']['absolute_profit'] * 5:.0f}원 수익",
                    f"1000만원 기준: {result['portfolio_summary']['absolute_profit'] * 10:.0f}원 수익"
                ]
            }
        else:
            result["user_guidance"] = {
                "capital_notice": f"✅ 사용자 지정 초기 자본금 {initial_capital:,.0f}원을 사용했습니다.",
                "performance_note": "위 결과는 지정하신 자본금 기준입니다."
            }
        
        # 자본금 독립적 지표 강조
        result["capital_independent_metrics"] = {
            "note": "아래 지표들은 초기 자본금과 무관하게 동일합니다",
            "total_return_pct": result['performance_metrics']['total_return'] * 100,
            "annualized_return_pct": result['performance_metrics']['annualized_return'] * 100,
            "sharpe_ratio": result['performance_metrics']['sharpe_ratio'],
            "max_drawdown_pct": result['performance_metrics']['max_drawdown'] * 100,
            "win_rate_pct": result['performance_metrics']['win_rate'] * 100
        }
        
        # 차트 생성 (옵션)
        if generate_chart:
            try:
                if ctx:
                    ctx.info("백테스팅 차트 생성 중...")
                
                from tools.generate_backtest_chart import generate_backtest_chart
                
                chart_result = await generate_backtest_chart(
                    backtest_result=result,
                    candles_data=candles,
                    market=market,
                    strategy_type=strategy_type,
                    interval=interval,
                    ctx=ctx
                )
                
                if chart_result.get("success", False):
                    result["chart_info"] = {
                        "chart_generated": True,
                        "image_url": chart_result["image_url"],
                        "filename": chart_result["filename"],
                        "message": chart_result["message"]
                    }
                    if ctx:
                        ctx.info(f"백테스팅 차트 생성 완료: {chart_result['image_url']}")
                else:
                    result["chart_info"] = {
                        "chart_generated": False,
                        "error": chart_result.get("error", "알 수 없는 차트 생성 오류"),
                        "message": "차트 생성에 실패했지만 백테스팅 결과는 정상적으로 제공됩니다."
                    }
                    if ctx:
                        ctx.warning(f"차트 생성 실패: {chart_result.get('error', '알 수 없는 오류')}")
                        
            except Exception as e:
                result["chart_info"] = {
                    "chart_generated": False,
                    "error": f"차트 생성 중 예외 발생: {str(e)}",
                    "message": "차트 생성에 실패했지만 백테스팅 결과는 정상적으로 제공됩니다."
                }
                if ctx:
                    ctx.error(f"차트 생성 중 예외: {str(e)}")
        else:
            result["chart_info"] = {
                "chart_generated": False,
                "message": "차트 생성이 비활성화되었습니다."
            }

        if ctx:
            ctx.info(f"백테스팅 완료: {market} 총수익률 {result['performance_metrics']['total_return']:.2%}")
        
        return result
        
    except Exception as e:
        error_msg = f"백테스팅 중 오류 발생: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return {"error": error_msg}


async def collect_candle_data(market: str, interval: Literal["minute1", "minute3", "minute5", "minute10", "minute15", "minute30", "minute60", "minute240", "day", "week", "month"], start_date: str, end_date: str, ctx: Optional[Context] = None) -> dict:
    """
    지정된 기간의 모든 캔들 데이터를 수집합니다.
    Upbit API의 200개 제한을 고려하여 페이징 처리를 수행합니다.
    """
    try:
        all_candles = []
        current_to = end_date + "T23:59:59"
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        
        max_retries = 3
        call_count = 0
        
        while True:
            call_count += 1
            
            # 너무 많은 호출 방지 (무한루프 방지)
            if call_count > 50:
                return {"error": f"너무 많은 API 호출이 필요합니다. 기간을 줄여주세요. (호출 횟수: {call_count})"}
            
            # 재시도 로직
            candles = None
            for retry in range(max_retries):
                try:
                    candles = await get_candles(market, interval, 200, current_to, ctx)
                    
                    # API 제한 에러 체크
                    if (isinstance(candles, list) and len(candles) > 0 and 
                        isinstance(candles[0], dict) and "error" in candles[0] and 
                        "too_many_requests" in str(candles[0].get("error", "")).lower()):
                        
                        if ctx:
                            ctx.warning(f"API 제한 도달, {2 ** retry}초 대기 후 재시도...")
                        await asyncio.sleep(2 ** retry)  # 지수 백오프
                        continue
                    
                    break  # 성공하면 재시도 루프 탈출
                    
                except Exception as e:
                    if retry == max_retries - 1:
                        return {"error": f"API 호출 실패: {str(e)}"}
                    await asyncio.sleep(1)
            
            if candles is None:
                return {"error": "API 호출 재시도 실패"}
            
            # 응답 검증
            if not isinstance(candles, list):
                return {"error": f"잘못된 API 응답 형식: {type(candles)}"}
            
            if len(candles) == 0:
                if ctx:
                    ctx.info("더 이상 캔들 데이터가 없습니다.")
                break
            
            # 에러 응답 체크
            if isinstance(candles[0], dict) and "error" in candles[0]:
                error_msg = candles[0].get("error", "알 수 없는 오류")
                return {"error": f"API 오류: {error_msg}"}
            
            # 시작일 이전 데이터 필터링
            filtered_candles = []
            found_before_start = False
            
            for candle in candles:
                try:
                    candle_date = datetime.strptime(candle["candle_date_time_kst"][:10], "%Y-%m-%d")
                    if candle_date >= start_dt:
                        filtered_candles.append(candle)
                    else:
                        # 시작일 이전 데이터에 도달했으므로 중단
                        found_before_start = True
                        break
                except (KeyError, ValueError) as e:
                    if ctx:
                        ctx.warning(f"캔들 데이터 파싱 오류: {e}")
                    continue
            
            # 필터링된 캔들 추가
            all_candles.extend(filtered_candles)
            
            # 시작일 이전 데이터를 발견했으면 전체 루프 종료
            if found_before_start:
                if ctx:
                    ctx.info(f"시작일 이전 데이터 도달, 수집 완료")
                break
            
            # 더 이상 데이터가 없으면 종료
            if len(candles) < 200:
                if ctx:
                    ctx.info("모든 데이터 수집 완료")
                break
            
            # 가장 오래된 캔들의 시간을 다음 to로 설정
            try:
                oldest_candle = candles[-1]
                new_to = oldest_candle["candle_date_time_kst"]
                
                # 무한루프 방지: to가 변경되지 않으면 중단
                if new_to == current_to:
                    if ctx:
                        ctx.warning("동일한 시점 반복, 수집 중단")
                    break
                    
                current_to = new_to
            except (KeyError, IndexError) as e:
                return {"error": f"캔들 데이터 구조 오류: {e}"}
            
            # API 호출 제한을 위한 지연
            await asyncio.sleep(0.2)
        
        # 데이터 검증
        if len(all_candles) == 0:
            return {"error": "지정된 기간에 해당하는 캔들 데이터가 없습니다."}
        
        # 시간순으로 정렬 (오래된 것부터)
        all_candles.sort(key=lambda x: x["candle_date_time_kst"])
        
        if ctx:
            ctx.info(f"총 {len(all_candles)}개의 캔들 데이터 수집 완료 (API 호출: {call_count}회)")
        
        return {"candles": all_candles}
        
    except Exception as e:
        return {"error": f"캔들 데이터 수집 중 오류: {str(e)}"}


async def backtest_sma_crossover(
    candles: List[dict], 
    initial_capital: float, 
    fast_period: int, 
    slow_period: int, 
    commission_rate: float,
    ctx: Optional[Context] = None
) -> dict:
    """
    SMA 교차 전략 백테스팅을 수행합니다.
    """
    try:
        # 가격 데이터 추출
        closes = np.array([float(candle["trade_price"]) for candle in candles])
        dates = [candle["candle_date_time_kst"] for candle in candles]
        
        # 이동평균 계산
        fast_sma = calculate_sma(closes, fast_period)
        slow_sma = calculate_sma(closes, slow_period)
        
        # 포트폴리오 초기화
        cash = initial_capital
        asset = 0.0
        portfolio_values = []
        trade_history = []
        
        # 백테스팅 시뮬레이션
        for i in range(slow_period, len(candles)):
            current_price = closes[i]
            current_date = dates[i]
            
            # 현재 포트폴리오 가치 계산
            portfolio_value = cash + (asset * current_price)
            portfolio_values.append({
                "date": current_date,
                "value": portfolio_value,
                "price": current_price
            })
            
            # 골든크로스/데드크로스 신호 감지
            if i > slow_period:  # 이전 값과 비교하기 위해
                prev_fast = fast_sma[i-1]
                prev_slow = slow_sma[i-1]
                curr_fast = fast_sma[i]
                curr_slow = slow_sma[i]
                
                # 골든크로스 (매수 신호)
                if prev_fast <= prev_slow and curr_fast > curr_slow and asset == 0:
                    # 전액 매수
                    buy_amount = cash * (1 - commission_rate)
                    asset = buy_amount / current_price
                    cash = 0
                    
                    trade_history.append({
                        "date": current_date,
                        "action": "BUY",
                        "price": current_price,
                        "quantity": asset,
                        "commission": cash * commission_rate if cash > 0 else buy_amount * commission_rate / current_price,
                        "cash_balance": cash,
                        "asset_balance": asset
                    })
                    
                    if ctx:
                        ctx.info(f"매수: {current_date} {current_price:,.0f}원 {asset:.8f}개")
                
                # 데드크로스 (매도 신호)
                elif prev_fast >= prev_slow and curr_fast < curr_slow and asset > 0:
                    # 전량 매도
                    sell_amount = asset * current_price * (1 - commission_rate)
                    cash = sell_amount
                    
                    trade_history.append({
                        "date": current_date,
                        "action": "SELL",
                        "price": current_price,
                        "quantity": asset,
                        "commission": asset * current_price * commission_rate,
                        "cash_balance": cash,
                        "asset_balance": 0
                    })
                    
                    if ctx:
                        ctx.info(f"매도: {current_date} {current_price:,.0f}원 {asset:.8f}개")
                    
                    asset = 0
        
        # 최종 포트폴리오 가치
        final_price = closes[-1]
        final_value = cash + (asset * final_price)
        
        # 성과 지표 계산
        performance_metrics = calculate_performance_metrics(
            portfolio_values, trade_history, initial_capital, final_value
        )
        
        # 월별 수익률 계산
        monthly_returns = calculate_monthly_returns(portfolio_values)
        
        # 드로우다운 분석
        drawdown_periods = calculate_drawdown_periods(portfolio_values)
        
        # 포트폴리오 요약 정보 계산
        portfolio_summary = calculate_portfolio_summary(
            initial_capital, cash, asset, final_price, trade_history
        )
        
        # 거래 내역에 상세 정보 추가
        enhanced_trade_history = enhance_trade_history(trade_history, candles)
        
        return {
            "performance_metrics": performance_metrics,
            "trade_history": enhanced_trade_history,
            "monthly_returns": monthly_returns,
            "drawdown_periods": drawdown_periods,
            "portfolio_summary": portfolio_summary
        }
        
    except Exception as e:
        return {"error": f"SMA 교차 전략 백테스팅 중 오류: {str(e)}"}


def calculate_sma(prices: np.ndarray, period: int) -> np.ndarray:
    """단순 이동평균을 계산합니다."""
    sma = np.full_like(prices, np.nan)
    for i in range(period - 1, len(prices)):
        sma[i] = np.mean(prices[i - period + 1:i + 1])
    return sma


def calculate_performance_metrics(portfolio_values: List[dict], trade_history: List[dict], initial_capital: float, final_value: float) -> dict:
    """성과 지표를 계산합니다."""
    try:
        # 기본 수익률 지표
        total_return = (final_value / initial_capital) - 1
        
        # 기간 계산 (일 단위)
        if len(portfolio_values) > 1:
            start_date = datetime.strptime(portfolio_values[0]["date"][:10], "%Y-%m-%d")
            end_date = datetime.strptime(portfolio_values[-1]["date"][:10], "%Y-%m-%d")
            days = (end_date - start_date).days
            years = days / 365.25
        else:
            years = 1
        
        annualized_return = ((1 + total_return) ** (1/years)) - 1 if years > 0 else total_return
        
        # 변동성 계산
        if len(portfolio_values) > 1:
            daily_returns = []
            for i in range(1, len(portfolio_values)):
                prev_value = portfolio_values[i-1]["value"]
                curr_value = portfolio_values[i]["value"]
                daily_return = (curr_value / prev_value) - 1
                daily_returns.append(daily_return)
            
            volatility = np.std(daily_returns) * np.sqrt(252) if daily_returns else 0
        else:
            volatility = 0
        
        # 샤프 지수
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # 최대 낙폭
        max_drawdown = calculate_max_drawdown(portfolio_values)
        
        # 거래 성과 지표
        trade_metrics = calculate_trade_metrics(trade_history)
        
        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            **trade_metrics
        }
        
    except Exception as e:
        return {"error": f"성과 지표 계산 중 오류: {str(e)}"}


def calculate_max_drawdown(portfolio_values: List[dict]) -> float:
    """최대 낙폭을 계산합니다."""
    if len(portfolio_values) < 2:
        return 0.0
    
    max_drawdown = 0.0
    peak = portfolio_values[0]["value"]
    
    for pv in portfolio_values:
        value = pv["value"]
        if value > peak:
            peak = value
        
        drawdown = (peak - value) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    return -max_drawdown  # 음수로 표시


def calculate_trade_metrics(trade_history: List[dict]) -> dict:
    """거래 성과 지표를 계산합니다."""
    if len(trade_history) < 2:
        return {
            "win_rate": 0,
            "profit_factor": 0,
            "total_trades": len(trade_history)
        }
    
    # 매수-매도 쌍으로 거래 분석
    completed_trades = []
    buy_trades = [t for t in trade_history if t["action"] == "BUY"]
    sell_trades = [t for t in trade_history if t["action"] == "SELL"]
    
    for i in range(min(len(buy_trades), len(sell_trades))):
        buy_trade = buy_trades[i]
        sell_trade = sell_trades[i]
        
        buy_cost = buy_trade["quantity"] * buy_trade["price"]
        sell_revenue = sell_trade["quantity"] * sell_trade["price"]
        profit = sell_revenue - buy_cost
        
        completed_trades.append(profit)
    
    if not completed_trades:
        return {
            "win_rate": 0,
            "profit_factor": 0,
            "total_trades": len(trade_history)
        }
    
    # 승률 계산
    winning_trades = [p for p in completed_trades if p > 0]
    win_rate = len(winning_trades) / len(completed_trades)
    
    # 프로핏 팩터 계산
    total_profit = sum(p for p in completed_trades if p > 0)
    total_loss = abs(sum(p for p in completed_trades if p < 0))
    profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
    
    return {
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "total_trades": len(trade_history)
    }


def calculate_monthly_returns(portfolio_values: List[dict]) -> dict:
    """월별 수익률을 계산합니다."""
    if len(portfolio_values) < 2:
        return {}
    
    monthly_data = {}
    
    for pv in portfolio_values:
        date_str = pv["date"][:7]  # YYYY-MM
        if date_str not in monthly_data:
            monthly_data[date_str] = {"start": pv["value"], "end": pv["value"]}
        else:
            monthly_data[date_str]["end"] = pv["value"]
    
    monthly_returns = {}
    for month, data in monthly_data.items():
        if data["start"] > 0:
            monthly_returns[month] = (data["end"] / data["start"]) - 1
    
    return monthly_returns


def calculate_drawdown_periods(portfolio_values: List[dict]) -> List[dict]:
    """주요 드로우다운 구간을 분석합니다."""
    if len(portfolio_values) < 2:
        return []
    
    drawdown_periods = []
    peak_value = portfolio_values[0]["value"]
    peak_date = portfolio_values[0]["date"]
    in_drawdown = False
    trough_value = peak_value
    trough_date = peak_date
    
    for pv in portfolio_values[1:]:
        value = pv["value"]
        date = pv["date"]
        
        if value > peak_value:
            # 새로운 최고점
            if in_drawdown:
                # 드로우다운 종료
                drawdown = (peak_value - trough_value) / peak_value
                drawdown_periods.append({
                    "peak_date": peak_date,
                    "trough_date": trough_date,
                    "recovery_date": date,
                    "drawdown": -drawdown
                })
                in_drawdown = False
            
            peak_value = value
            peak_date = date
            trough_value = value
            trough_date = date
        else:
            # 하락 중
            if not in_drawdown:
                in_drawdown = True
            
            if value < trough_value:
                trough_value = value
                trough_date = date
    
    # 정렬 (큰 드로우다운 순)
    drawdown_periods.sort(key=lambda x: x["drawdown"])
    
    return drawdown_periods[:5]  # 상위 5개만 반환


def calculate_portfolio_summary(
    initial_capital: float, 
    final_cash: float, 
    final_asset: float, 
    final_price: float,
    trade_history: List[dict]
) -> dict:
    """포트폴리오 요약 정보를 계산합니다."""
    try:
        final_asset_value = final_asset * final_price
        final_total_value = final_cash + final_asset_value
        absolute_profit = final_total_value - initial_capital
        
        # 포지션 상태 판단
        if final_asset > 0 and final_cash > 0:
            position_status = "MIXED"
        elif final_asset > 0:
            position_status = "HOLDING_ASSET"
        else:
            position_status = "CASH"
        
        # 실현/미실현 손익 계산
        realized_profit = 0
        if len(trade_history) >= 2:
            for i in range(1, len(trade_history), 2):  # 매수-매도 쌍
                if i < len(trade_history) and trade_history[i]["action"] == "SELL":
                    buy_trade = trade_history[i-1]
                    sell_trade = trade_history[i]
                    trade_profit = (sell_trade["price"] - buy_trade["price"]) * buy_trade["quantity"]
                    trade_profit -= (buy_trade["commission"] + sell_trade["commission"])
                    realized_profit += trade_profit
        
        unrealized_profit = absolute_profit - realized_profit
        
        return {
            "initial_capital": initial_capital,
            "final_cash_balance": final_cash,
            "final_asset_quantity": final_asset,
            "final_asset_price": final_price,
            "final_asset_value": final_asset_value,
            "final_total_value": final_total_value,
            "absolute_profit": absolute_profit,
            "position_status": position_status,
            "realized_profit": realized_profit,
            "unrealized_profit": unrealized_profit,
            "realized_return": realized_profit / initial_capital if initial_capital > 0 else 0,
            "unrealized_return": unrealized_profit / initial_capital if initial_capital > 0 else 0
        }
    except Exception as e:
        return {"error": f"포트폴리오 요약 계산 중 오류: {str(e)}"}


def enhance_trade_history(trade_history: List[dict], candles: List[dict]) -> List[dict]:
    """거래 내역에 상세 정보를 추가합니다."""
    enhanced_history = []
    
    for i, trade in enumerate(trade_history):
        enhanced_trade = trade.copy()
        
        # 거래 후 포트폴리오 가치 계산
        current_price = trade["price"]
        cash_after = trade["cash_balance"]
        asset_after = trade["asset_balance"]
        portfolio_value = cash_after + (asset_after * current_price)
        enhanced_trade["portfolio_value"] = portfolio_value
        
        # 매도 거래의 경우 해당 거래 손익 계산
        if trade["action"] == "SELL" and i > 0:
            prev_buy = trade_history[i-1]
            if prev_buy["action"] == "BUY":
                buy_price = prev_buy["price"]
                sell_price = trade["price"]
                quantity = prev_buy["quantity"]
                trade_profit = (sell_price - buy_price) * quantity
                trade_profit -= (prev_buy["commission"] + trade["commission"])
                enhanced_trade["trade_profit"] = trade_profit
                enhanced_trade["trade_return"] = trade_profit / (buy_price * quantity) if buy_price * quantity > 0 else 0
        else:
            enhanced_trade["trade_profit"] = 0
            enhanced_trade["trade_return"] = 0
        
        enhanced_history.append(enhanced_trade)
    
    return enhanced_history


async def backtest_rsi_oversold(
    candles: List[dict], 
    initial_capital: float, 
    rsi_period: int, 
    oversold_threshold: float,
    overbought_threshold: float,
    commission_rate: float,
    ctx: Optional[Context] = None
) -> dict:
    """RSI 과매도/과매수 전략 백테스팅"""
    try:
        if ctx:
            ctx.info(f"RSI 전략 시작: 기간={rsi_period}, 과매도={oversold_threshold}, 과매수={overbought_threshold}")
        
        # 가격 데이터 추출
        prices = np.array([float(candle["trade_price"]) for candle in candles])
        
        # RSI 계산
        rsi_values = calculate_rsi(prices, rsi_period)
        
        # 포트폴리오 초기화
        cash = initial_capital
        asset = 0.0
        trade_history = []
        portfolio_values = []
        
        # 이전 RSI 상태 추적
        prev_rsi_oversold = False
        prev_rsi_overbought = False
        
        for i in range(len(candles)):
            candle = candles[i]
            price = float(candle["trade_price"])
            date = candle["candle_date_time_kst"]
            
            # 현재 포트폴리오 가치
            portfolio_value = cash + (asset * price)
            portfolio_values.append({"date": date, "value": portfolio_value})
            
            # RSI 신호 확인 (충분한 데이터가 있을 때만)
            if i >= rsi_period and not np.isnan(rsi_values[i]):
                current_rsi = rsi_values[i]
                
                # 과매도 진입 시 매수 (포지션이 없을 때)
                if current_rsi <= oversold_threshold and not prev_rsi_oversold and asset == 0:
                    # 전액 매수
                    buy_amount = cash * (1 - commission_rate)
                    asset = buy_amount / price
                    cash = 0
                    
                    trade_history.append({
                        "date": date,
                        "action": "BUY",
                        "price": price,
                        "quantity": asset,
                        "commission": cash * commission_rate,
                        "rsi": current_rsi
                    })
                    
                    if ctx:
                        ctx.info(f"RSI 과매도 매수: {date}, 가격={price:,.0f}, RSI={current_rsi:.1f}")
                
                # 과매수 진입 시 매도 (포지션이 있을 때)
                elif current_rsi >= overbought_threshold and not prev_rsi_overbought and asset > 0:
                    # 전량 매도
                    sell_amount = asset * price * (1 - commission_rate)
                    cash = sell_amount
                    asset = 0
                    
                    trade_history.append({
                        "date": date,
                        "action": "SELL",
                        "price": price,
                        "quantity": asset,
                        "commission": asset * price * commission_rate,
                        "rsi": current_rsi
                    })
                    
                    if ctx:
                        ctx.info(f"RSI 과매수 매도: {date}, 가격={price:,.0f}, RSI={current_rsi:.1f}")
                
                # 이전 상태 업데이트
                prev_rsi_oversold = current_rsi <= oversold_threshold
                prev_rsi_overbought = current_rsi >= overbought_threshold
        
        # 최종 정산
        final_value = cash + (asset * prices[-1])
        
        # 성과 지표 계산
        performance_metrics = calculate_performance_metrics(
            portfolio_values, trade_history, initial_capital, final_value
        )
        
        # 월별 수익률 및 드로우다운 계산
        monthly_returns = calculate_monthly_returns(portfolio_values)
        drawdown_periods = calculate_drawdown_periods(portfolio_values)
        
        # 포트폴리오 요약 정보 계산
        portfolio_summary = calculate_portfolio_summary(
            initial_capital, cash, asset, prices[-1], trade_history
        )
        
        # 거래 내역에 상세 정보 추가
        enhanced_trade_history = enhance_trade_history(trade_history, candles)
        
        return {
            "performance_metrics": performance_metrics,
            "trade_history": enhanced_trade_history,
            "monthly_returns": monthly_returns,
            "drawdown_periods": drawdown_periods,
            "portfolio_summary": portfolio_summary
        }
        
    except Exception as e:
        return {"error": f"RSI 전략 백테스팅 중 오류: {str(e)}"}


def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """RSI를 계산합니다."""
    if len(prices) < period + 1:
        return np.full_like(prices, np.nan)
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    rsi = np.full_like(prices, np.nan)
    
    if len(gains) < period or len(losses) < period:
        return rsi
    
    # 초기 평균 계산
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    # 첫 번째 RSI 값
    if avg_loss == 0:
        rsi[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi[period] = 100.0 - (100.0 / (1.0 + rs))
    
    # 나머지 RSI 값들 계산
    for i in range(period + 1, len(prices)):
        avg_gain = (avg_gain * (period - 1) + gains[i-1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i-1]) / period
        
        if avg_loss == 0:
            rsi[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))
    
    return rsi


async def backtest_bollinger_bands(
    candles: List[dict], 
    initial_capital: float, 
    period: int, 
    std_dev: float,
    buy_threshold: float,
    sell_threshold: float,
    commission_rate: float,
    ctx: Optional[Context] = None
) -> dict:
    """볼린저 밴드 전략 백테스팅"""
    try:
        if ctx:
            ctx.info(f"볼린저 밴드 전략 시작: 기간={period}, 표준편차={std_dev}, 매수임계값={buy_threshold}, 매도임계값={sell_threshold}")
        
        # 가격 데이터 추출
        prices = np.array([float(candle["trade_price"]) for candle in candles])
        
        # 볼린저 밴드 계산
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices, period, std_dev)
        
        # 포트폴리오 초기화
        cash = initial_capital
        asset = 0.0
        trade_history = []
        portfolio_values = []
        
        for i in range(len(candles)):
            candle = candles[i]
            price = float(candle["trade_price"])
            date = candle["candle_date_time_kst"]
            
            # 현재 포트폴리오 가치
            portfolio_value = cash + (asset * price)
            portfolio_values.append({"date": date, "value": portfolio_value})
            
            # 볼린저 밴드 신호 확인 (충분한 데이터가 있을 때만)
            if i >= period and not np.isnan(bb_upper[i]):
                upper = bb_upper[i]
                lower = bb_lower[i]
                band_width = upper - lower
                
                # 밴드 내 상대적 위치 계산
                if band_width > 0:
                    position = (price - lower) / band_width
                    
                    # 매수 신호: 하단 임계값 이하 (포지션이 없을 때)
                    if position <= buy_threshold and asset == 0:
                        # 전액 매수
                        buy_amount = cash * (1 - commission_rate)
                        asset = buy_amount / price
                        cash = 0
                        
                        trade_history.append({
                            "date": date,
                            "action": "BUY",
                            "price": price,
                            "quantity": asset,
                            "commission": cash * commission_rate,
                            "bb_position": position,
                            "bb_upper": upper,
                            "bb_lower": lower
                        })
                        
                        if ctx:
                            ctx.info(f"볼린저 밴드 매수: {date}, 가격={price:,.0f}, 위치={position:.3f}")
                    
                    # 매도 신호: 상단 임계값 이상 (포지션이 있을 때)
                    elif position >= sell_threshold and asset > 0:
                        # 전량 매도
                        sell_amount = asset * price * (1 - commission_rate)
                        cash = sell_amount
                        asset = 0
                        
                        trade_history.append({
                            "date": date,
                            "action": "SELL",
                            "price": price,
                            "quantity": asset,
                            "commission": asset * price * commission_rate,
                            "bb_position": position,
                            "bb_upper": upper,
                            "bb_lower": lower
                        })
                        
                        if ctx:
                            ctx.info(f"볼린저 밴드 매도: {date}, 가격={price:,.0f}, 위치={position:.3f}")
        
        # 최종 정산
        final_value = cash + (asset * prices[-1])
        
        # 성과 지표 계산
        performance_metrics = calculate_performance_metrics(
            portfolio_values, trade_history, initial_capital, final_value
        )
        
        # 월별 수익률 및 드로우다운 계산
        monthly_returns = calculate_monthly_returns(portfolio_values)
        drawdown_periods = calculate_drawdown_periods(portfolio_values)
        
        return {
            "performance_metrics": performance_metrics,
            "trade_history": trade_history,
            "monthly_returns": monthly_returns,
            "drawdown_periods": drawdown_periods
        }
        
    except Exception as e:
        return {"error": f"볼린저 밴드 전략 백테스팅 중 오류: {str(e)}"}


def calculate_bollinger_bands(prices: np.ndarray, period: int = 20, num_std: float = 2) -> tuple:
    """볼린저 밴드를 계산합니다."""
    upper = np.full_like(prices, np.nan)
    middle = np.full_like(prices, np.nan)
    lower = np.full_like(prices, np.nan)
    
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        sma = np.mean(window)
        std = np.std(window)
        
        middle[i] = sma
        upper[i] = sma + (std * num_std)
        lower[i] = sma - (std * num_std)
    
    return upper, middle, lower


async def backtest_macd_signal(
    candles: List[dict], 
    initial_capital: float, 
    fast_period: int, 
    slow_period: int,
    signal_period: int,
    commission_rate: float,
    ctx: Optional[Context] = None
) -> dict:
    """MACD 신호선 교차 전략 백테스팅"""
    try:
        if ctx:
            ctx.info(f"MACD 전략 시작: 단기={fast_period}, 장기={slow_period}, 신호={signal_period}")
        
        # 가격 데이터 추출
        prices = np.array([float(candle["trade_price"]) for candle in candles])
        
        # MACD 계산
        macd_line, signal_line, histogram = calculate_macd(prices, fast_period, slow_period, signal_period)
        
        # 포트폴리오 초기화
        cash = initial_capital
        asset = 0.0
        trade_history = []
        portfolio_values = []
        
        # 이전 MACD 상태 추적
        prev_macd_above_signal = False
        
        for i in range(len(candles)):
            candle = candles[i]
            price = float(candle["trade_price"])
            date = candle["candle_date_time_kst"]
            
            # 현재 포트폴리오 가치
            portfolio_value = cash + (asset * price)
            portfolio_values.append({"date": date, "value": portfolio_value})
            
            # MACD 신호 확인 (충분한 데이터가 있을 때만)
            if i >= slow_period + signal_period and not np.isnan(macd_line[i]) and not np.isnan(signal_line[i]):
                current_macd = macd_line[i]
                current_signal = signal_line[i]
                current_macd_above = current_macd > current_signal
                
                # 골든크로스: MACD가 신호선을 상향 돌파 (포지션이 없을 때)
                if current_macd_above and not prev_macd_above_signal and asset == 0:
                    # 전액 매수
                    buy_amount = cash * (1 - commission_rate)
                    asset = buy_amount / price
                    cash = 0
                    
                    trade_history.append({
                        "date": date,
                        "action": "BUY",
                        "price": price,
                        "quantity": asset,
                        "commission": cash * commission_rate,
                        "macd": current_macd,
                        "signal": current_signal,
                        "histogram": histogram[i] if not np.isnan(histogram[i]) else 0
                    })
                    
                    if ctx:
                        ctx.info(f"MACD 골든크로스 매수: {date}, 가격={price:,.0f}")
                
                # 데드크로스: MACD가 신호선을 하향 돌파 (포지션이 있을 때)
                elif not current_macd_above and prev_macd_above_signal and asset > 0:
                    # 전량 매도
                    sell_amount = asset * price * (1 - commission_rate)
                    cash = sell_amount
                    asset = 0
                    
                    trade_history.append({
                        "date": date,
                        "action": "SELL",
                        "price": price,
                        "quantity": asset,
                        "commission": asset * price * commission_rate,
                        "macd": current_macd,
                        "signal": current_signal,
                        "histogram": histogram[i] if not np.isnan(histogram[i]) else 0
                    })
                    
                    if ctx:
                        ctx.info(f"MACD 데드크로스 매도: {date}, 가격={price:,.0f}")
                
                # 이전 상태 업데이트
                prev_macd_above_signal = current_macd_above
        
        # 최종 정산
        final_value = cash + (asset * prices[-1])
        
        # 성과 지표 계산
        performance_metrics = calculate_performance_metrics(
            portfolio_values, trade_history, initial_capital, final_value
        )
        
        # 월별 수익률 및 드로우다운 계산
        monthly_returns = calculate_monthly_returns(portfolio_values)
        drawdown_periods = calculate_drawdown_periods(portfolio_values)
        
        return {
            "performance_metrics": performance_metrics,
            "trade_history": trade_history,
            "monthly_returns": monthly_returns,
            "drawdown_periods": drawdown_periods
        }
        
    except Exception as e:
        return {"error": f"MACD 전략 백테스팅 중 오류: {str(e)}"}


def calculate_macd(prices: np.ndarray, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> tuple:
    """MACD를 계산합니다."""
    if len(prices) < slow_period:
        return np.full_like(prices, np.nan), np.full_like(prices, np.nan), np.full_like(prices, np.nan)
    
    # EMA 계산 함수
    def calculate_ema(data, period):
        ema = np.full_like(data, np.nan)
        ema[period-1] = np.mean(data[:period])
        multiplier = 2 / (period + 1)
        
        for i in range(period, len(data)):
            ema[i] = data[i] * multiplier + ema[i-1] * (1 - multiplier)
        
        return ema
    
    # Fast EMA와 Slow EMA 계산
    ema_fast = calculate_ema(prices, fast_period)
    ema_slow = calculate_ema(prices, slow_period)
    
    # MACD 라인 계산
    macd_line = ema_fast - ema_slow
    
    # 신호선 계산 (MACD의 EMA)
    valid_macd = macd_line[~np.isnan(macd_line)]
    if len(valid_macd) >= signal_period:
        signal_line = np.full_like(macd_line, np.nan)
        start_idx = slow_period - 1
        signal_ema = calculate_ema(macd_line[start_idx:], signal_period)
        signal_line[start_idx:] = signal_ema
    else:
        signal_line = np.full_like(macd_line, np.nan)
    
    # 히스토그램 계산
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


async def backtest_breakout(
    candles: List[dict], 
    initial_capital: float, 
    lookback: int,
    exit_lookback: int,
    atr_period: int,
    atr_filter: bool,
    commission_rate: float,
    ctx: Optional[Context] = None
) -> dict:
    """
    브레이크아웃 추세 추종 전략 백테스팅을 수행합니다.
    
    이 전략은 가격이 일정 기간의 최고가를 돌파할 때 매수하고,
    일정 기간의 최저가를 하향 돌파할 때 매도하는 추세 추종 전략입니다.
    전통적인 Turtle Trading 시스템을 기반으로 합니다.
    
    Args:
        candles: 캔들 데이터 리스트
        initial_capital: 초기 자본금
        lookback: 진입용 채널 기간 (긴 기간)
        exit_lookback: 청산용 채널 기간 (짧은 기간)
        atr_period: ATR 계산 기간
        atr_filter: ATR 필터 사용 여부
        commission_rate: 거래 수수료율
        ctx: 컨텍스트 객체
    
    Returns:
        dict: 백테스팅 결과
    """
    try:
        if ctx:
            ctx.info(f"브레이크아웃 전략 시작: 진입채널={lookback}, 청산채널={exit_lookback}, ATR={atr_period}")
        
        # 가격 데이터 추출
        highs = np.array([float(candle["high_price"]) for candle in candles])
        lows = np.array([float(candle["low_price"]) for candle in candles])
        closes = np.array([float(candle["trade_price"]) for candle in candles])
        dates = [candle["candle_date_time_kst"] for candle in candles]
        
        # 롤링 최고가/최저가 계산
        entry_highs = calculate_rolling_high(highs, lookback)
        exit_lows = calculate_rolling_low(lows, exit_lookback)
        
        # ATR 계산 (필터 사용 시)
        atr_values = None
        if atr_filter:
            atr_values = calculate_atr(highs, lows, closes, atr_period)
        
        # 포트폴리오 초기화
        cash = initial_capital
        asset = 0.0
        portfolio_values = []
        trade_history = []
        
        # 이전 상태 추적
        prev_in_position = False
        
        for i in range(len(candles)):
            current_price = closes[i]
            current_date = dates[i]
            
            # 현재 포트폴리오 가치 계산
            portfolio_value = cash + (asset * current_price)
            portfolio_values.append({
                "date": current_date,
                "value": portfolio_value,
                "price": current_price
            })
            
            # 브레이크아웃 신호 확인 (충분한 데이터가 있을 때만)
            if i >= lookback:
                entry_level = entry_highs[i-1]  # 이전 봉의 최고가를 기준으로
                exit_level = exit_lows[i-1] if i >= exit_lookback else None
                
                # 매수 신호: 종가가 진입 채널 최고가 돌파 (포지션이 없을 때)
                if not np.isnan(entry_level) and current_price > entry_level and asset == 0:
                    # ATR 필터 확인 (사용 시)
                    can_enter = True
                    if atr_filter and atr_values is not None and i >= atr_period:
                        current_atr = atr_values[i]
                        if not np.isnan(current_atr):
                            # 돌파 강도가 ATR의 0.5배 이상일 때만 진입
                            breakout_strength = current_price - entry_level
                            can_enter = breakout_strength >= (current_atr * 0.5)
                    
                    if can_enter:
                        # 전액 매수
                        buy_amount = cash * (1 - commission_rate)
                        asset = buy_amount / current_price
                        cash = 0
                        
                        trade_history.append({
                            "date": current_date,
                            "action": "BUY",
                            "price": current_price,
                            "quantity": asset,
                            "commission": initial_capital * commission_rate if cash == 0 else cash * commission_rate,
                            "cash_balance": cash,
                            "asset_balance": asset,
                            "entry_level": entry_level,
                            "breakout_strength": current_price - entry_level
                        })
                        
                        if ctx:
                            ctx.info(f"브레이크아웃 매수: {current_date} {current_price:,.0f}원 (진입레벨: {entry_level:,.0f})")
                
                # 매도 신호: 종가가 청산 채널 최저가 하향 돌파 (포지션이 있을 때)
                elif (exit_level is not None and not np.isnan(exit_level) and 
                      current_price < exit_level and asset > 0):
                    # 전량 매도
                    sell_amount = asset * current_price * (1 - commission_rate)
                    cash = sell_amount
                    
                    trade_history.append({
                        "date": current_date,
                        "action": "SELL",
                        "price": current_price,
                        "quantity": asset,
                        "commission": asset * current_price * commission_rate,
                        "cash_balance": cash,
                        "asset_balance": 0,
                        "exit_level": exit_level,
                        "breakdown_strength": exit_level - current_price
                    })
                    
                    if ctx:
                        ctx.info(f"브레이크아웃 매도: {current_date} {current_price:,.0f}원 (청산레벨: {exit_level:,.0f})")
                    
                    asset = 0
        
        # 최종 포트폴리오 가치
        final_price = closes[-1]
        final_value = cash + (asset * final_price)
        
        # 성과 지표 계산
        performance_metrics = calculate_performance_metrics(
            portfolio_values, trade_history, initial_capital, final_value
        )
        
        # 월별 수익률 계산
        monthly_returns = calculate_monthly_returns(portfolio_values)
        
        # 드로우다운 분석
        drawdown_periods = calculate_drawdown_periods(portfolio_values)
        
        # 포트폴리오 요약 정보 계산
        portfolio_summary = calculate_portfolio_summary(
            initial_capital, cash, asset, final_price, trade_history
        )
        
        # 거래 내역에 상세 정보 추가
        enhanced_trade_history = enhance_trade_history(trade_history, candles)
        
        return {
            "performance_metrics": performance_metrics,
            "trade_history": enhanced_trade_history,
            "monthly_returns": monthly_returns,
            "drawdown_periods": drawdown_periods,
            "portfolio_summary": portfolio_summary
        }
        
    except Exception as e:
        return {"error": f"브레이크아웃 전략 백테스팅 중 오류: {str(e)}"}


def calculate_rolling_high(prices: np.ndarray, period: int) -> np.ndarray:
    """
    롤링 최고가를 계산합니다.
    
    Args:
        prices: 가격 배열
        period: 롤링 기간
        
    Returns:
        np.ndarray: 롤링 최고가 배열
    """
    rolling_high = np.full(len(prices), np.nan, dtype=float)
    
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        rolling_high[i] = np.max(window)
    
    return rolling_high


def calculate_rolling_low(prices: np.ndarray, period: int) -> np.ndarray:
    """
    롤링 최저가를 계산합니다.
    
    Args:
        prices: 가격 배열
        period: 롤링 기간
        
    Returns:
        np.ndarray: 롤링 최저가 배열
    """
    rolling_low = np.full(len(prices), np.nan, dtype=float)
    
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        rolling_low[i] = np.min(window)
    
    return rolling_low


def calculate_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    """
    ATR(Average True Range)을 계산합니다.
    
    Args:
        highs: 고가 배열
        lows: 저가 배열
        closes: 종가 배열
        period: ATR 계산 기간
        
    Returns:
        np.ndarray: ATR 값 배열
    """
    if len(highs) < 2:
        return np.full(len(highs), np.nan, dtype=float)
    
    # True Range 계산
    tr = np.full(len(highs), np.nan, dtype=float)
    
    for i in range(1, len(highs)):
        high_low = highs[i] - lows[i]
        high_close_prev = abs(highs[i] - closes[i-1])
        low_close_prev = abs(lows[i] - closes[i-1])
        tr[i] = max(high_low, high_close_prev, low_close_prev)
    
    # ATR 계산 (단순 이동평균 사용)
    atr = np.full(len(highs), np.nan, dtype=float)
    
    for i in range(period, len(tr)):
        if not np.isnan(tr[i-period+1:i+1]).any():
            atr[i] = np.mean(tr[i-period+1:i+1])
    
    return atr