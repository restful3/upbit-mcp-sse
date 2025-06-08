import httpx
from config import API_BASE
import json

async def get_ticker(symbol: str) -> dict:
    """
    Upbit API를 사용하여 특정 암호화폐 마켓의 최신 시세 정보를 비동기적으로 조회합니다.

    이 함수는 Upbit의 Ticker API 엔드포인트(/v1/ticker)에 GET 요청을 보내, 지정된 단일 마켓(예: KRW-BTC)의 현재 상태를 가져옵니다. 
    성공적으로 데이터를 수신하면 해당 마켓의 시세 정보가 담긴 딕셔너리를 반환하고, 실패 시에는 오류 정보가 담긴 딕셔너리를 반환합니다.

    Args:
        symbol (str): 조회할 마켓의 코드입니다. Upbit에서 사용하는 공식 마켓 코드를 사용해야 합니다. 
                      (예: "KRW-BTC", "BTC-ETH")

    Returns:
        dict: 
            - 성공 시: API 응답에서 받은 첫 번째 시세 정보 딕셔너리. 주요 키는 다음과 같습니다:
                - `market` (str): 마켓 코드 (e.g., "KRW-BTC")
                - `trade_date_kst` (str): 최근 거래 일자(KST)
                - `trade_time_kst` (str): 최근 거래 시각(KST)
                - `trade_price` (float): 현재가
                - `high_price` (float): 고가(오늘)
                - `low_price` (float): 저가(오늘)
                - `acc_trade_price_24h` (float): 24시간 누적 거래대금
                - `acc_trade_volume_24h` (float): 24시간 누적 거래량
                - `signed_change_rate` (float): 전일 대비 등락률
                - ... 등 Upbit Ticker API에서 제공하는 모든 필드.
            - 실패 시: 오류의 원인을 설명하는 메시지를 포함한 딕셔너리.
                - `{"error": "오류 메시지"}` 형식입니다.
                - API 요청 실패, 비정상적인 응답, 데이터 파싱 오류 등 다양한 경우에 반환될 수 있습니다.

    Raises:
        이 함수는 내부적으로 발생하는 예외(httpx.RequestError, json.JSONDecodeError 등)를 처리하고, 
        `{"error": ...}` 형태의 딕셔너리로 반환하므로 직접적인 예외를 발생시키지 않습니다.
    
    Example:
        >>> import asyncio
        >>> 
        >>> async def main():
        >>>     btc_ticker = await get_ticker("KRW-BTC")
        >>>     if "error" not in btc_ticker:
        ...         print(f"비트코인 현재가: {btc_ticker['trade_price']} KRW")
        ...     else:
        ...         print(f"오류 발생: {btc_ticker['error']}")
        >>>
        >>> asyncio.run(main())
    """
    url = f"{API_BASE}/ticker"
    async with httpx.AsyncClient() as client:
        try:
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
        except json.JSONDecodeError as e:
            error_message = f"Failed to decode JSON response: {str(e)}. Response text: {res.text if 'res' in locals() else 'Response object not available'}"
            return {"error": f"Upbit API returned invalid JSON for {symbol}: {error_message}"}
        except IndexError as e:
            error_message = f"Data list is empty, cannot access index 0. Response: {json.dumps(data) if 'data' in locals() else 'Data not available'}"
            return {"error": f"Upbit API returned unexpected data structure for {symbol}: {error_message}"}
        except Exception as e:
            error_message = f"An unexpected error occurred in get_ticker: {str(e)}"
            return {"error": f"An unexpected error occurred while fetching ticker for {symbol}: {error_message}"}