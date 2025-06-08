import httpx
from config import API_BASE
import json

async def get_trades(symbol: str, count: int = 1) -> list[dict]:
    """
    지정된 마켓의 최근 체결 내역을 조회합니다.

    Upbit의 최근 체결 내역 API(/v1/trades/ticks)를 호출하여, 
    가장 최근에 체결된 거래 기록을 `count` 개수만큼 가져옵니다.

    Args:
        symbol (str): 조회할 마켓의 코드 (예: "KRW-BTC").
        count (int): 조회할 체결 내역의 개수. 기본값은 1, 최대 500까지 가능.

    Returns:
        list[dict]:
            - 성공 시: 체결 내역 정보를 담은 딕셔너리의 리스트. 각 딕셔너리는 다음 키를 포함합니다:
                - `market` (str): 마켓 코드
                - `trade_date_utc` (str): 체결 일자 (UTC)
                - `trade_time_utc` (str): 체결 시각 (UTC)
                - `trade_price` (float): 체결 가격
                - `trade_volume` (float): 체결량
                - `ask_bid` (str): 매수/매도 구분 ('ASK': 매도, 'BID': 매수)
            - 실패 시: 오류 정보를 담은 딕셔너리를 포함한 리스트.
                - `[{"error": "오류 메시지"}]` 형식입니다.

    Example:
        >>> btc_trades = await get_trades("KRW-BTC", count=5)
        >>> if btc_trades and "error" not in btc_trades[0]:
        ...     for trade in btc_trades:
        ...         print(f"[{trade['trade_time_utc']}] {trade['trade_price']} KRW, 체결량: {trade['trade_volume']}")
        ... else:
        ...     print(f"오류: {btc_trades}")
    """
    url = f"{API_BASE}/trades/ticks"
    params = {"market": symbol, "count": str(count)}
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url, params=params)
            res.raise_for_status()
            return res.json()
    except httpx.HTTPStatusError as e:
        error_message = f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        return [{"error": f"Upbit API request failed for {symbol}: {error_message}"}]
    except httpx.RequestError as e:
        error_message = f"Request error occurred: {str(e)}"
        return [{"error": f"Upbit API request failed for {symbol}: {error_message}"}]
    except json.JSONDecodeError as e:
        error_message = f"Failed to parse JSON response: {str(e)}"
        return [{"error": f"Upbit API returned invalid JSON for {symbol}: {error_message}"}]
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        return [{"error": f"An unexpected error occurred while fetching trades for {symbol}: {error_message}"}]