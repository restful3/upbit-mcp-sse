from fastmcp import Context
import httpx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import os
from typing import Literal, Optional, Dict, Any, List
from config import API_BASE
import asyncio

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

async def generate_backtest_chart(
    backtest_result: dict,
    candles_data: List[dict],
    market: str,
    strategy_type: str,
    interval: str = "day",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    백테스팅 결과를 시각화하는 종합 차트를 생성합니다.

    Args:
        backtest_result (dict): 백테스팅 결과 데이터
        candles_data (List[dict]): 캔들 데이터
        market (str): 마켓 코드 (예: "KRW-BTC")
        strategy_type (str): 전략 타입
        interval (str): 시간 간격
        ctx (Context, optional): FastMCP 컨텍스트 객체

    Returns:
        Dict[str, Any]: 차트 생성 결과
            - success 시: {"success": True, "file_path": "경로", "image_url": "URL", "message": "메시지"}
            - error 시: {"success": False, "error": "오류 메시지"}
    """
    
    if ctx:
        ctx.info(f"백테스팅 차트 생성 시작: {market} {strategy_type}")
    
    try:
        # 데이터 검증
        if "error" in backtest_result:
            return {"success": False, "error": f"백테스팅 결과에 오류가 있습니다: {backtest_result['error']}"}
        
        if not candles_data:
            return {"success": False, "error": "캔들 데이터가 없습니다."}
        
        # 필수 데이터 추출
        trade_history = backtest_result.get("trade_history", [])
        portfolio_summary = backtest_result.get("portfolio_summary", {})
        performance_metrics = backtest_result.get("performance_metrics", {})
        
        # 차트 생성
        chart_path = await create_backtest_chart(
            candles_data, trade_history, portfolio_summary, performance_metrics,
            market, strategy_type, interval, ctx
        )
        
        if not chart_path:
            return {"success": False, "error": "차트 생성에 실패했습니다."}
        
        # URL 생성
        filename = os.path.basename(chart_path)
        if chart_path.startswith("./charts"):
            # 로컬 환경에서는 파일 경로 제공
            image_url = f"file://{os.path.abspath(chart_path)}"
        else:
            # Docker 환경에서는 웹 URL 제공
            image_url = f"https://charts.resteful3.shop/{filename}"
        
        return {
            "success": True,
            "file_path": chart_path,
            "image_url": image_url,
            "filename": filename,
            "message": f"{market} {strategy_type} 백테스팅 차트가 성공적으로 생성되었습니다."
        }
        
    except Exception as e:
        error_msg = f"백테스팅 차트 생성 중 오류 발생: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return {"success": False, "error": error_msg}


async def create_backtest_chart(
    candles: List[dict], 
    trade_history: List[dict],
    portfolio_summary: dict,
    performance_metrics: dict,
    market: str, 
    strategy_type: str,
    interval: str,
    ctx: Optional[Context] = None
) -> str:
    """백테스팅 결과를 시각화하는 차트를 생성합니다."""
    
    try:
        # 데이터 준비
        dates = [datetime.fromisoformat(candle['candle_date_time_kst'].replace('T', ' ')) for candle in candles]
        closes = [float(candle['trade_price']) for candle in candles]
        highs = [float(candle['high_price']) for candle in candles]
        lows = [float(candle['low_price']) for candle in candles]
        volumes = [float(candle['candle_acc_trade_volume']) for candle in candles]
        
        # 3개 서브플롯으로 구성
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), 
                                          gridspec_kw={'height_ratios': [2, 1.5, 1]}, 
                                          sharex=True)
        
        # 1. 가격 차트 + 매매 신호 (상단)
        draw_price_and_signals(ax1, dates, closes, highs, lows, trade_history, strategy_type)
        
        # 2. 포트폴리오 가치 변화 (중간)
        draw_portfolio_value(ax2, dates, closes, trade_history, portfolio_summary)
        
        # 3. 포지션 변화 및 거래량 (하단)
        draw_position_and_volume(ax3, dates, volumes, trade_history)
        
        # 전체 차트 설정
        setup_chart_layout(fig, ax1, ax2, ax3, market, strategy_type, performance_metrics)
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_{market}_{strategy_type}_{interval}_{timestamp}.png"
        
        # 저장 디렉토리 확인 및 생성
        charts_dir = "/app/uploads/charts"
        try:
            os.makedirs(charts_dir, exist_ok=True)
        except PermissionError:
            # Docker 환경이 아닌 경우 로컬 디렉토리 사용
            charts_dir = "./charts"
            os.makedirs(charts_dir, exist_ok=True)
            if ctx:
                ctx.info(f"로컬 환경에서 차트 디렉토리 사용: {charts_dir}")
        
        file_path = os.path.join(charts_dir, filename)
        plt.savefig(file_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        if ctx:
            ctx.info(f"백테스팅 차트 저장 완료: {file_path}")
        
        return file_path
        
    except Exception as e:
        if ctx:
            ctx.error(f"차트 생성 중 오류: {str(e)}")
        return ""


def draw_price_and_signals(ax, dates, closes, highs, lows, trade_history, strategy_type):
    """가격 차트와 매매 신호를 그립니다."""
    
    # 가격 라인 차트
    ax.plot(dates, closes, linewidth=1.5, color='black', label='Price', alpha=0.8)
    
    # 이동평균선 추가 (SMA 전략인 경우)
    if strategy_type == "sma_crossover" and len(closes) >= 50:
        ma20 = calculate_moving_average(closes, 20)
        ma50 = calculate_moving_average(closes, 50)
        
        if len(ma20) == len(dates):
            ax.plot(dates, ma20, linewidth=1, color='orange', label='MA20', alpha=0.7)
        if len(ma50) == len(dates):
            ax.plot(dates, ma50, linewidth=1, color='red', label='MA50', alpha=0.7)
    
    # 매매 신호 표시
    buy_signal_shown = False
    sell_signal_shown = False
    
    for trade in trade_history:
        trade_date_str = trade.get('date', '')
        if not trade_date_str:
            continue
            
        try:
            # 다양한 날짜 형식 시도
            trade_date = None
            for date_format in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    trade_date = datetime.strptime(trade_date_str, date_format)
                    break
                except ValueError:
                    continue
            
            if trade_date is None:
                print(f"DEBUG: 날짜 파싱 실패: {trade_date_str}")
                continue
                
            trade_price = float(trade.get('price', 0))
            action = trade.get('action', '')
            
            print(f"DEBUG: 거래 신호 - 날짜: {trade_date}, 가격: {trade_price}, 액션: {action}")
            print(f"DEBUG: 차트 날짜 범위: {min(dates)} ~ {max(dates)}")
            
            # 날짜 범위를 더 유연하게 확인 (같은 날짜 또는 가장 가까운 날짜 찾기)
            closest_date = min(dates, key=lambda x: abs((x - trade_date).total_seconds()))
            time_diff = abs((closest_date - trade_date).total_seconds())
            
            # 24시간 이내의 차이는 허용
            if time_diff <= 24 * 3600:  # 24시간
                if action == 'BUY':
                    ax.scatter(closest_date, trade_price, color='green', s=150, 
                             marker='^', label='Buy Signal' if not buy_signal_shown else "", 
                             zorder=5, alpha=0.9, edgecolors='darkgreen', linewidth=1)
                    buy_signal_shown = True
                    print(f"DEBUG: 매수 신호 표시됨 - {closest_date}, {trade_price}")
                elif action == 'SELL':
                    ax.scatter(closest_date, trade_price, color='red', s=150, 
                             marker='v', label='Sell Signal' if not sell_signal_shown else "", 
                             zorder=5, alpha=0.9, edgecolors='darkred', linewidth=1)
                    sell_signal_shown = True
                    print(f"DEBUG: 매도 신호 표시됨 - {closest_date}, {trade_price}")
            else:
                print(f"DEBUG: 날짜 차이가 너무 큼: {time_diff}초")
                
        except (ValueError, TypeError) as e:
            print(f"DEBUG: 거래 처리 오류: {e}")
            continue
    
    ax.set_ylabel('Price (KRW)', fontsize=10)
    ax.set_title('Price Chart with Trading Signals', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)


def draw_portfolio_value(ax, dates, closes, trade_history, portfolio_summary):
    """포트폴리오 가치 변화를 그립니다."""
    
    # 포트폴리오 가치 계산
    initial_capital = portfolio_summary.get('initial_capital', 1000000)
    portfolio_values = calculate_portfolio_timeline(dates, closes, trade_history, initial_capital)
    
    # Buy & Hold 전략 계산
    if closes:
        initial_price = closes[0]
        buy_hold_values = [initial_capital * (price / initial_price) for price in closes]
    else:
        buy_hold_values = [initial_capital] * len(dates)
    
    # 포트폴리오 가치 라인
    ax.plot(dates, portfolio_values, linewidth=2, color='blue', label='Strategy Portfolio')
    ax.plot(dates, buy_hold_values, linewidth=2, color='gray', label='Buy & Hold', alpha=0.7, linestyle='--')
    
    # 최종 수익률 계산 (portfolio_summary에서 가져오거나 직접 계산)
    final_value = portfolio_summary.get('final_total_value', initial_capital)
    if final_value and initial_capital:
        total_return = (final_value - initial_capital) / initial_capital
    else:
        # 직접 계산
        if portfolio_values:
            total_return = (portfolio_values[-1] - initial_capital) / initial_capital
        else:
            total_return = 0
    
    ax.axhline(y=initial_capital, color='black', linestyle=':', alpha=0.5, label='Initial Capital')
    
    ax.set_ylabel('Portfolio Value (KRW)', fontsize=10)
    ax.set_title(f'Portfolio Value Change (Final Return: {total_return:.2%})', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)


def draw_position_and_volume(ax, dates, volumes, trade_history):
    """포지션 변화와 거래량을 그립니다."""
    
    # 거래량 바 차트
    ax.bar(dates, volumes, alpha=0.3, color='lightblue', label='Volume')
    
    # 거래 발생 시점 표시
    for trade in trade_history:
        trade_date_str = trade.get('date', '')
        if not trade_date_str:
            continue
            
        try:
            trade_date = datetime.strptime(trade_date_str, "%Y-%m-%d")
            action = trade.get('action', '')
            
            if trade_date >= min(dates) and trade_date <= max(dates):
                # 거래량 차트에서 해당 날짜의 거래량 찾기
                closest_date_idx = min(range(len(dates)), key=lambda i: abs(dates[i] - trade_date))
                volume_height = volumes[closest_date_idx] if closest_date_idx < len(volumes) else max(volumes) * 0.1
                
                color = 'green' if action == 'BUY' else 'red'
                ax.axvline(x=trade_date, color=color, alpha=0.7, linewidth=2)
                
        except (ValueError, TypeError):
            continue
    
    ax.set_ylabel('Volume', fontsize=10)
    ax.set_xlabel('Date', fontsize=10)
    ax.set_title('Trading Volume and Position Changes', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)


def setup_chart_layout(fig, ax1, ax2, ax3, market, strategy_type, performance_metrics):
    """차트 전체 레이아웃을 설정합니다."""
    
    # 전체 제목
    total_return = performance_metrics.get('total_return', 0)
    sharpe_ratio = performance_metrics.get('sharpe_ratio', 0)
    max_drawdown = performance_metrics.get('max_drawdown', 0)
    
    main_title = f"{market} - {strategy_type.upper()} Strategy Backtest Results"
    subtitle = f"Return: {total_return:.2%} | Sharpe: {sharpe_ratio:.2f} | Max DD: {max_drawdown:.2%}"
    
    fig.suptitle(main_title, fontsize=14, fontweight='bold', y=0.98)
    fig.text(0.5, 0.94, subtitle, ha='center', fontsize=11, style='italic')
    
    # X축 날짜 포맷팅
    for ax in [ax1, ax2, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    
    # 레이아웃 조정
    plt.tight_layout()
    plt.subplots_adjust(top=0.90, hspace=0.3)


def calculate_moving_average(prices: List[float], period: int) -> List[float]:
    """이동평균을 계산합니다."""
    if len(prices) < period:
        return prices
    
    ma_values = []
    for i in range(len(prices)):
        if i < period - 1:
            ma_values.append(prices[i])  # 초기값은 현재가로 설정
        else:
            ma = sum(prices[i-period+1:i+1]) / period
            ma_values.append(ma)
    
    return ma_values


def calculate_portfolio_timeline(dates: List[datetime], closes: List[float], trade_history: List[dict], initial_capital: float) -> List[float]:
    """시간에 따른 포트폴리오 가치를 계산합니다."""
    
    portfolio_values = []
    current_cash = initial_capital
    current_asset = 0.0
    
    print(f"DEBUG: 포트폴리오 계산 시작 - 초기자본: {initial_capital}, 거래수: {len(trade_history)}")
    
    # 거래 내역을 날짜별로 정리 (더 유연한 날짜 파싱)
    trades_by_date = {}
    for trade in trade_history:
        trade_date_str = trade.get('date', '')
        if trade_date_str:
            try:
                # 다양한 날짜 형식 시도
                trade_date = None
                for date_format in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        trade_date = datetime.strptime(trade_date_str, date_format).date()
                        break
                    except ValueError:
                        continue
                
                if trade_date:
                    if trade_date not in trades_by_date:
                        trades_by_date[trade_date] = []
                    trades_by_date[trade_date].append(trade)
                    print(f"DEBUG: 거래 등록 - {trade_date}: {trade.get('action')} {trade.get('quantity')} @ {trade.get('price')}")
            except Exception as e:
                print(f"DEBUG: 거래 날짜 파싱 오류: {e}")
                continue
    
    # 각 날짜별로 포트폴리오 가치 계산
    for i, (date, price) in enumerate(zip(dates, closes)):
        date_only = date.date()
        
        # 해당 날짜의 거래 실행 (정확한 날짜 매칭만)
        executed_trade = False
        if date_only in trades_by_date:
            for trade in trades_by_date[date_only]:
                action = trade.get('action', '')
                quantity = float(trade.get('quantity', 0))
                trade_price = float(trade.get('price', 0))
                commission = float(trade.get('commission', 0))
                
                if action == 'BUY':
                    cost = quantity * trade_price + commission
                    current_cash -= cost
                    current_asset += quantity
                    executed_trade = True
                    print(f"DEBUG: 매수 실행 - 날짜: {date_only}, 수량: {quantity}, 가격: {trade_price}, 현금: {current_cash}, 자산: {current_asset}")
                elif action == 'SELL':
                    proceeds = quantity * trade_price - commission
                    current_cash += proceeds
                    current_asset -= quantity
                    executed_trade = True
                    print(f"DEBUG: 매도 실행 - 날짜: {date_only}, 수량: {quantity}, 가격: {trade_price}, 현금: {current_cash}, 자산: {current_asset}")
            
            # 처리된 거래는 제거하여 중복 실행 방지
            del trades_by_date[date_only]
        
        # 현재 포트폴리오 가치 계산
        total_value = current_cash + (current_asset * price)
        portfolio_values.append(total_value)
        
        if executed_trade or i % 50 == 0:  # 거래 발생시나 50일마다 로그
            print(f"DEBUG: 포트폴리오 가치 - 날짜: {date_only}, 현금: {current_cash:.0f}, 자산가치: {current_asset * price:.0f}, 총가치: {total_value:.0f}")
    
    print(f"DEBUG: 포트폴리오 계산 완료 - 최종가치: {portfolio_values[-1] if portfolio_values else 0}")
    return portfolio_values


async def test_backtest_chart():
    """테스트용 함수"""
    print("백테스팅 차트 생성 테스트는 실제 백테스팅 결과와 함께 실행해야 합니다.")


if __name__ == "__main__":
    asyncio.run(test_backtest_chart()) 