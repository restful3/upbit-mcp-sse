import httpx
from typing import Optional
from fastmcp import Context
from config import generate_upbit_token, UPBIT_ACCESS_KEY, API_BASE

async def get_accounts(ctx: Optional[Context] = None) -> list[dict]:
    """
    보유한 모든 자산의 잔고 및 상세 정보를 조회합니다. (인증 필요)

    Upbit의 전체 계좌 조회 API 엔드포인트(/v1/accounts)에 GET 요청을 보내, 
    보유 중인 모든 디지털 자산과 원화(KRW)의 잔고, 평균 매입가 등의 정보를 가져옵니다.
    API 키 설정이 필수적입니다.

    Args:
        ctx (Context, optional): FastMCP 컨텍스트 객체. 함수 실행 중 정보나 오류를 로깅하는 데 사용됩니다.

    Returns:
        list[dict]:
            - 성공 시: 각 자산의 정보를 담은 딕셔너리의 리스트. 주요 키는 다음과 같습니다:
                - `currency` (str): 통화 코드 (e.g., "BTC", "KRW")
                - `balance` (str): 주문가능 금액/수량
                - `locked` (str): 주문 중 묶여있는 금액/수량
                - `avg_buy_price` (str): 평균 매입가
                - `unit_currency` (str): 평단가 기준 통화 (e.g., "KRW")
                - ... 등 Upbit 계좌 조회 API에서 제공하는 모든 필드.
            - 실패 시: 오류 정보를 담은 딕셔너리를 포함한 리스트.
                - `[{"error": "오류 메시지"}]` 형식입니다.

    Example:
        >>> my_accounts = await get_accounts()
        >>> if my_accounts and "error" not in my_accounts[0]:
        ...     for account in my_accounts:
        ...         print(f"통화: {account['currency']}, 보유수량: {account['balance']}")
        ... else:
        ...     print(f"오류: {my_accounts[0]['error']}")
    """
    if not UPBIT_ACCESS_KEY:
        if ctx:
            ctx.error("API 키가 설정되지 않았습니다. .env 파일에 UPBIT_ACCESS_KEY와 UPBIT_SECRET_KEY를 설정해주세요.")
        return [{"error": "API 키가 설정되지 않았습니다."}]
    
    url = f"{API_BASE}/accounts"
    headers = {
        "Authorization": f"Bearer {generate_upbit_token()}"
    }
    
    if ctx:
        ctx.info("계정 잔고 조회 중...")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                if ctx:
                    ctx.error(f"업비트 API 오류: {res.status_code} - {res.text}")
                return [{"error": f"업비트 API 오류: {res.status_code}"}]
            return res.json()
        except Exception as e:
            if ctx:
                ctx.error(f"API 호출 중 오류 발생: {str(e)}")
            return [{"error": f"API 호출 중 오류 발생: {str(e)}"}]