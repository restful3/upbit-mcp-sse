from fastmcp import Context
import httpx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import os
from typing import Literal, Optional, Dict, Any
from config import API_BASE
import asyncio

# 한글 폰트 설정 (시스템에 따라 조정 필요)
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

async def generate_chart_image(
    market: str,
    interval: Literal["minute1", "minute3", "minute5", "minute10", "minute15", "minute30", "minute60", "minute240", "day", "week", "month"] = "day",
    chart_type: Literal["line", "candlestick", "ohlc"] = "candlestick",
    count: int = 100,
    include_volume: bool = True,
    include_ma: bool = True,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    지정된 마켓의 캔들 데이터를 기반으로 차트 이미지를 생성합니다.

    Args:
        market (str): 차트를 생성할 마켓 코드 (예: "KRW-BTC")
        interval (Literal): 캔들 간격
        chart_type (Literal): 차트 유형 ("line", "candlestick", "ohlc")
        count (int): 표시할 캔들 개수 (기본: 100, 최대: 200)
        include_volume (bool): 거래량 포함 여부 (기본: True)
        include_ma (bool): 이동평균선 포함 여부 (기본: True)
        start_date (str, optional): 시작 날짜 (YYYY-MM-DD 형식, 예: "2024-06-01")
        end_date (str, optional): 종료 날짜 (YYYY-MM-DD 형식, 예: "2024-12-31")
        ctx (Context, optional): FastMCP 컨텍스트 객체

    Returns:
        Dict[str, Any]: 차트 생성 결과
            - success 시: {"success": True, "file_path": "경로", "image_url": "URL", "message": "메시지"}
            - error 시: {"success": False, "error": "오류 메시지"}
    """
    
    if ctx:
        ctx.info(f"차트 생성 시작: {market} {interval} {chart_type}")
    
    # 입력 파라미터 검증
    if count > 200:
        count = 200
    elif count < 10:
        count = 10
    
    try:
        # 캔들 데이터 조회
        candles_data = await fetch_candle_data(market, interval, count, start_date, end_date, ctx)
        if not candles_data:
            return {"success": False, "error": "캔들 데이터를 가져올 수 없습니다."}
        
        # 차트 생성
        chart_path = await create_chart(
            candles_data, market, interval, chart_type, 
            include_volume, include_ma, ctx
        )
        
        if not chart_path:
            return {"success": False, "error": "차트 생성에 실패했습니다."}
        
        # URL 생성 (기존 Nginx 서버 사용)
        filename = os.path.basename(chart_path)
        image_url = f"https://charts.resteful3.shop/{filename}"  # 차트 전용 서브도메인 URL
        
        return {
            "success": True,
            "file_path": chart_path,
            "image_url": image_url,
            "filename": filename,
            "message": f"{market} {interval} 차트가 성공적으로 생성되었습니다."
        }
        
    except Exception as e:
        error_msg = f"차트 생성 중 오류 발생: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return {"success": False, "error": error_msg}


async def fetch_candle_data(market: str, interval: str, count: int, start_date: Optional[str] = None, end_date: Optional[str] = None, ctx: Optional[Context] = None) -> list:
    """Upbit API에서 캔들 데이터를 조회합니다."""
    
    # interval에 따라 API 엔드포인트 조정
    if interval in ["day", "week", "month"]:
        url_interval = f"{interval}s"
    elif interval.startswith("minute"):
        url_interval = interval
    else:
        url_interval = interval

    url = f"{API_BASE}/candles/{url_interval}"
    params = {
        'market': market,
        'count': str(count)
    }
    
    # 날짜 범위가 지정된 경우 to 파라미터 추가
    if end_date:
        try:
            # end_date를 ISO 형식으로 변환 (YYYY-MM-DDTHH:mm:ss)
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            # 하루의 마지막 시간으로 설정
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            params['to'] = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            if ctx:
                ctx.error(f"잘못된 종료 날짜 형식: {end_date}. YYYY-MM-DD 형식을 사용해주세요.")
            return []
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url, params=params)
            
            if res.status_code != 200:
                if ctx:
                    ctx.error(f"API 오류: {res.status_code} - {res.text}")
                return []
            
            candles = res.json()
            if not candles:
                if ctx:
                    ctx.error("API 응답이 비어있습니다.")
                return []
            
            # 시간 순서대로 정렬 (오래된 것부터)
            candles.sort(key=lambda x: x['candle_date_time_kst'])
            
            # 시작 날짜 필터링 (start_date가 지정된 경우)
            if start_date:
                try:
                    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                    filtered_candles = []
                    for candle in candles:
                        candle_date = datetime.fromisoformat(candle['candle_date_time_kst'].replace('T', ' '))
                        if candle_date.date() >= start_datetime.date():
                            filtered_candles.append(candle)
                    candles = filtered_candles
                except ValueError:
                    if ctx:
                        ctx.error(f"잘못된 시작 날짜 형식: {start_date}. YYYY-MM-DD 형식을 사용해주세요.")
                    return []
            
            return candles
            
    except Exception as e:
        if ctx:
            ctx.error(f"캔들 데이터 조회 중 오류: {str(e)}")
        return []


async def create_chart(
    candles: list, 
    market: str, 
    interval: str, 
    chart_type: str,
    include_volume: bool,
    include_ma: bool,
    ctx: Optional[Context] = None
) -> str:
    """차트 이미지를 생성하고 파일로 저장합니다."""
    
    try:
        # 데이터 준비
        dates = [datetime.fromisoformat(candle['candle_date_time_kst'].replace('T', ' ')) for candle in candles]
        opens = [float(candle['opening_price']) for candle in candles]
        highs = [float(candle['high_price']) for candle in candles]
        lows = [float(candle['low_price']) for candle in candles]
        closes = [float(candle['trade_price']) for candle in candles]
        volumes = [float(candle['candle_acc_trade_volume']) for candle in candles]
        
        # 차트 설정
        if include_volume:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), 
                                         gridspec_kw={'height_ratios': [3, 1]}, 
                                         sharex=True)
        else:
            fig, ax1 = plt.subplots(1, 1, figsize=(12, 8))
            ax2 = None
        
        # 메인 차트 그리기
        if chart_type == "candlestick":
            draw_candlestick(ax1, dates, opens, highs, lows, closes)
        elif chart_type == "ohlc":
            draw_ohlc(ax1, dates, opens, highs, lows, closes)
        else:  # line
            ax1.plot(dates, closes, linewidth=1.5, color='blue')
        
        # 이동평균선 추가
        if include_ma and len(closes) >= 20:
            ma_20 = calculate_moving_average(closes, 20)
            ma_50 = calculate_moving_average(closes, 50) if len(closes) >= 50 else None
            
            ax1.plot(dates[19:], ma_20, label='MA20', color='orange', linewidth=1)
            if ma_50:
                ax1.plot(dates[49:], ma_50, label='MA50', color='red', linewidth=1)
            ax1.legend()
        
        # 차트 스타일링 (날짜 범위 표시)
        title = f"{market} {interval.upper()} Chart"
        if dates:
            start_date_str = dates[0].strftime('%Y-%m-%d')
            end_date_str = dates[-1].strftime('%Y-%m-%d')
            title += f" ({start_date_str} ~ {end_date_str})"
        
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price', fontsize=12)
        ax1.grid(True, alpha=0.3)
        
        # 거래량 차트
        if include_volume and ax2 is not None:
            colors = ['red' if closes[i] >= opens[i] else 'blue' for i in range(len(closes))]
            ax2.bar(dates, volumes, color=colors, alpha=0.7, width=0.8)
            ax2.set_ylabel('Volume', fontsize=12)
            ax2.grid(True, alpha=0.3)
        
        # X축 날짜 포맷
        if interval.startswith('minute'):
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        else:
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 저장 디렉토리 생성 (기존 Nginx uploads 디렉토리 사용)
        charts_dir = "/app/uploads/charts"  # 기존 Nginx와 공유되는 디렉토리
        os.makedirs(charts_dir, exist_ok=True)
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{market.replace('-', '_')}_{interval}_{chart_type}_{timestamp}.png"
        file_path = os.path.join(charts_dir, filename)
        
        # 이미지 저장
        plt.savefig(file_path, dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        if ctx:
            ctx.info(f"차트 저장 완료: {file_path}")
        
        return file_path
        
    except Exception as e:
        if ctx:
            ctx.error(f"차트 생성 중 오류: {str(e)}")
        return ""


def draw_candlestick(ax, dates, opens, highs, lows, closes):
    """캔들스틱 차트를 그립니다."""
    for i in range(len(dates)):
        color = 'red' if closes[i] >= opens[i] else 'blue'
        
        # 몸통 (body)
        body_height = abs(closes[i] - opens[i])
        body_bottom = min(opens[i], closes[i])
        
        rect = Rectangle((dates[i], body_bottom), timedelta(hours=12), body_height,
                        facecolor=color, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax.add_patch(rect)
        
        # 그림자 (shadow)
        ax.plot([dates[i], dates[i]], [lows[i], highs[i]], 
               color='black', linewidth=0.8)


def draw_ohlc(ax, dates, opens, highs, lows, closes):
    """OHLC 바 차트를 그립니다."""
    for i in range(len(dates)):
        color = 'red' if closes[i] >= opens[i] else 'blue'
        
        # 세로선
        ax.plot([dates[i], dates[i]], [lows[i], highs[i]], 
               color=color, linewidth=1.5)
        
        # 시가 표시 (왼쪽)
        ax.plot([dates[i] - timedelta(hours=6), dates[i]], [opens[i], opens[i]], 
               color=color, linewidth=1.5)
        
        # 종가 표시 (오른쪽)
        ax.plot([dates[i], dates[i] + timedelta(hours=6)], [closes[i], closes[i]], 
               color=color, linewidth=1.5)


def calculate_moving_average(prices: list, period: int) -> list:
    """이동평균을 계산합니다."""
    ma = []
    for i in range(period - 1, len(prices)):
        avg = sum(prices[i - period + 1:i + 1]) / period
        ma.append(avg)
    return ma


# 테스트 함수
async def test_chart_generation():
    """차트 생성 기능을 테스트합니다."""
    # 2024년 6월-12월 비트코인 차트 테스트
    result = await generate_chart_image(
        market="KRW-BTC",
        interval="day",
        chart_type="candlestick",
        count=200,
        start_date="2024-06-01",
        end_date="2024-12-31"
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(test_chart_generation()) 