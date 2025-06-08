import httpx
from config import API_BASE
import json

async def get_orderbook(symbol: str) -> dict:
    """
    지정된 마켓의 호가 정보(매수/매도 잔량)를 조회합니다.

    Upbit의 호가 정보 조회 API(/v1/orderbook)를 호출하여 특정 마켓의 실시간 매수/매도 호가 정보를 가져옵니다.

    Args:
        symbol (str): 조회할 마켓의 코드 (예: "KRW-BTC").

    Returns:
        dict:
            - 성공 시: 해당 마켓의 호가 정보를 담은 딕셔너리. 주요 키는 다음과 같습니다:
                - `market` (str): 마켓 코드
                - `timestamp` (int): 호가 정보 생성 시각 타임스탬프
                - `orderbook_units` (list[dict]): 매도/매수 호가 정보 리스트.
                    - `ask_price` (float): 매도 호가
                    - `bid_price` (float): 매수 호가
                    - `ask_size` (float): 매도 잔량
                    - `bid_size` (float): 매수 잔량
            - 실패 시: `{"error": "오류 메시지"}` 형식의 딕셔너리.

    Example:
        >>> btc_orderbook = await get_orderbook("KRW-BTC")
        >>> if "error" not in btc_orderbook:
        ...     # 1호가(가장 낮은 매도 호가) 정보 출력
        ...     first_ask = btc_orderbook['orderbook_units'][0]
        ...     print(f"BTC 1호 매도 호가: {first_ask['ask_price']}, 잔량: {first_ask['ask_size']}")
        ... else:
        ...     print(f"오류: {btc_orderbook['error']}")
    """
    url = f"{API_BASE}/orderbook"
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url, params={"markets": symbol})
            res.raise_for_status()
            data = res.json()
            if not data:
                return {"error": f"Upbit API returned empty data for symbol: {symbol}"}
            return data[0]
    except httpx.HTTPStatusError as e:
        error_message = f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        return {"error": f"Upbit API request failed for {symbol}: {error_message}"}
    except httpx.RequestError as e:
        error_message = f"Request error occurred: {str(e)}"
        return {"error": f"Upbit API request failed for {symbol}: {error_message}"}
    except (json.JSONDecodeError, IndexError) as e:
        error_message = f"Failed to parse response or data is empty: {str(e)}"
        return {"error": f"Upbit API returned invalid data for {symbol}: {error_message}"}
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        return {"error": f"An unexpected error occurred while fetching orderbook for {symbol}: {error_message}"}