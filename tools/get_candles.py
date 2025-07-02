from fastmcp import Context
import httpx
from typing import Literal, Optional
from config import API_BASE

async def get_candles(
    market: str,
    interval: Literal["minute1", "minute3", "minute5", "minute10", "minute15", "minute30", "minute60", "minute240", "day", "week", "month"],
    count: int = 200,
    to: Optional[str] = None,
    ctx: Optional[Context] = None
) -> list[dict]:
    """
    지정된 마켓의 캔들(시고저종) 데이터를 조회합니다.

    Upbit의 캔들 조회 API를 호출하여 특정 마켓의 시계열 데이터를 가져옵니다.
    분, 일, 주, 월 단위의 캔들 조회가 가능합니다.

    Args:
        market (str): 조회할 마켓의 코드 (예: "KRW-BTC").
        interval (Literal[...]): 캔들의 시간 간격. 
            "minute1"~"minute240", "day", "week", "month" 중 선택해야 합니다.
        count (int): 조회할 캔들의 개수. 최대 200개까지 가능하며, 기본값은 200입니다.
        to (Optional[str]): 조회할 마지막 캔들의 시각. 'yyyy-MM-dd HH:mm:ss' 또는 'yyyy-MM-dd'T'HH:mm:ssZ' 형식.
                           지정하지 않으면 가장 최신 캔들을 기준으로 조회합니다.
        ctx (Context, optional): FastMCP 컨텍스트 객체. 함수 실행 중 정보나 오류를 로깅하는 데 사용됩니다.

    Returns:
        list[dict]:
            - 성공 시: 캔들 데이터 딕셔너리의 리스트. 각 딕셔너리는 다음 키를 포함합니다:
                - `market` (str): 마켓 코드
                - `candle_date_time_kst` (str): 캔들 시작 시각 (KST)
                - `opening_price` (float): 시가
                - `high_price` (float): 고가
                - `low_price` (float): 저가
                - `trade_price` (float): 종가
                - `candle_acc_trade_volume` (float): 해당 캔들의 누적 거래량
                - ... 등 Upbit 캔들 API에서 제공하는 모든 필드.
            - 실패 시: 오류 정보를 담은 딕셔너리를 포함한 리스트.
                - `[{"error": "오류 메시지"}]` 형식입니다.

    Example:
        >>> # 비트코인 일봉 10개 조회
        >>> btc_daily_candles = await get_candles(market="KRW-BTC", interval="day", count=10)
        >>> if btc_daily_candles and "error" not in btc_daily_candles[0]:
        ...     print(f"가장 최근 BTC 일봉 종가: {btc_daily_candles[0]['trade_price']}")
        ... else:
        ...     print(f"오류: {btc_daily_candles}")
    """
    if count > 200:
        count = 200
        if ctx:
            ctx.warning("최대 200개의 캔들만 조회할 수 있습니다. count를 200으로 제한합니다.")
    
    # interval에 따라 API 엔드포인트 선택
    if interval.startswith("minute"):
        # minute60 -> 60 추출
        unit = interval.replace("minute", "")
        url = f"{API_BASE}/candles/minutes/{unit}"
    elif interval == "day":
        url = f"{API_BASE}/candles/days"
    elif interval == "week":
        url = f"{API_BASE}/candles/weeks"
    elif interval == "month":
        url = f"{API_BASE}/candles/months"
    else:
        if ctx:
            ctx.error(f"지원하지 않는 interval: {interval}")
        return [{"error": f"지원하지 않는 interval: {interval}"}]
    
    params = {
        'market': market,
        'count': str(count)
    }
    
    if to:
        params['to'] = to
    
    if ctx:
        ctx.info(f"{market} {interval} 캔들 데이터 조회 중...")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, params=params)
            if res.status_code != 200:
                if ctx:
                    ctx.error(f"업비트 API 오류: {res.status_code} - {res.text}")
                return [{"error": f"업비트 API 오류: {res.status_code} - {res.text}"}]
            return res.json()
        except Exception as e:
            if ctx:
                ctx.error(f"API 호출 중 오류 발생: {str(e)}")
            return [{"error": f"API 호출 중 오류 발생: {str(e)}"}]