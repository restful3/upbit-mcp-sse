import httpx
from config import API_BASE
import json

async def get_markets(verbose: bool = False) -> list[dict]:
    """
    업비트에서 거래 가능한 전체 마켓의 상세 정보를 조회합니다.

    Upbit의 /v1/market/all API를 호출하여 거래 가능한 모든 마켓의 정보를 가져옵니다.
    verbose 파라미터를 통해 유의 종목만 필터링하여 조회할 수 있습니다.

    Args:
        verbose (bool): True로 설정 시, 유의 종목 필드(market_warning)를 포함한 상세 정보를 반환합니다. 
                        기본값은 False입니다.

    Returns:
        list[dict]:
            - 성공 시: 마켓 정보를 담은 딕셔너리의 리스트. 각 딕셔너리는 다음 키를 포함합니다:
                - `market` (str): 마켓 코드 (예: "KRW-BTC")
                - `korean_name` (str): 마켓의 한글 이름 (예: "비트코인")
                - `english_name` (str): 마켓의 영문 이름 (예: "Bitcoin")
                - `market_warning` (str, optional): 유의 종목 여부 (NONE, CAUTION). verbose=True일 때만 포함됩니다.
            - 실패 시: 오류 정보를 담은 딕셔너리를 포함한 리스트.
                - `[{"error": "오류 메시지"}]` 형식입니다.

    Example:
        >>> markets = await get_markets()
        >>> if markets and "error" not in markets[0]:
        ...     krw_markets = [m for m in markets if m['market'].startswith('KRW')]
        ...     print(f"원화 마켓 수: {len(krw_markets)}")
        ... else:
        ...     print(f"오류: {markets}")
    """
    url = f"{API_BASE}/market/all"
    params = {"isDetails": str(verbose).lower()}
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url, params=params)
            res.raise_for_status()
            return res.json()
    except httpx.HTTPStatusError as e:
        error_message = f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        return [{"error": f"Upbit API request failed: {error_message}"}]
    except httpx.RequestError as e:
        error_message = f"Request error occurred: {str(e)}"
        return [{"error": f"Upbit API request failed: {error_message}"}]
    except json.JSONDecodeError as e:
        error_message = f"Failed to parse JSON response: {str(e)}"
        return [{"error": f"Upbit API returned invalid JSON: {error_message}"}]
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        return [{"error": f"An unexpected error occurred while fetching markets: {error_message}"}] 