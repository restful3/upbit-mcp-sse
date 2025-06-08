import httpx
from fastmcp import Context
from typing import Optional
from config import generate_upbit_token, UPBIT_ACCESS_KEY, API_BASE

async def create_withdraw(
    currency: str,
    amount: str,
    address: Optional[str] = None,
    secondary_address: Optional[str] = None,
    transaction_type: Optional[str] = None,
    ctx: Optional[Context] = None
) -> dict:
    """
    디지털 자산 또는 원화 출금을 요청합니다. (인증 및 출금 권한 필요)

    Upbit의 디지털 자산 출금(/v1/withdraws/coin) 또는 원화 출금(/v1/withdraws/krw) API에 POST 요청을 보내 출금을 신청합니다.
    이 기능을 사용하려면 API 키에 '출금' 권한이 반드시 포함되어 있어야 합니다.

    Args:
        currency (str): 출금할 통화의 코드 (예: "BTC", "ETH", "KRW").
        amount (str): 출금할 수량 또는 금액.
        address (Optional[str]): 디지털 자산 출금 시 필요한 출금 주소. `currency`가 "KRW"가 아닐 경우 필수입니다.
        secondary_address (Optional[str]): 2차 주소가 필요한 경우 입력 (예: XRP의 Destination Tag, STEEM의 Memo).
        transaction_type (Optional[str]): 출금 유형. 'default', 'internal' 등 허용된 값을 사용해야 합니다.
        ctx (Context, optional): FastMCP 컨텍스트 객체. 함수 실행 중 정보나 오류를 로깅하는 데 사용됩니다.

    Returns:
        dict:
            - 성공 시: 출금 요청의 상세 정보를 담은 딕셔너리. 주요 키는 다음과 같습니다:
                - `type` (str): 출금 유형 (e.g., 'withdraw')
                - `uuid` (str): 출금 요청의 고유 UUID
                - `currency` (str): 통화 코드
                - `amount` (str): 출금 수량/금액
                - `state` (str): 출금 상태 (e.g., 'submitting' - 처리 중)
                - ... 등 Upbit 출금 API에서 제공하는 모든 필드.
            - 실패 시: 오류의 원인을 설명하는 메시지를 포함한 딕셔너리.
                - `{"error": "오류 메시지"}` 형식입니다.

    Example:
        >>> # 비트코인 0.01 BTC 출금 요청
        >>> btc_withdraw = await create_withdraw("BTC", "0.01", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        >>> if "error" not in btc_withdraw:
        ...     print(f"출금 요청 성공. UUID: {btc_withdraw['uuid']}")
        ... else:
        ...     print(f"오류: {btc_withdraw['error']}")
        >>>
        >>> # 원화 10,000 KRW 출금 요청 (사전에 등록된 계좌로)
        >>> krw_withdraw = await create_withdraw("KRW", "10000")
    """
    if not UPBIT_ACCESS_KEY:
        if ctx:
            ctx.error("API 키가 설정되지 않았습니다. .env 파일에 UPBIT_ACCESS_KEY와 UPBIT_SECRET_KEY를 설정해주세요.")
        return {"error": "API 키가 설정되지 않았습니다."}
    
    if currency.upper() != "KRW" and not address:
        if ctx:
            ctx.error("암호화폐 출금 시 address는 필수입니다.")
        return {"error": "암호화폐 출금 시 address는 필수입니다."}
    
    # API_BASE를 사용하여 URL 구성
    url_path = "withdraws/coin" if currency.upper() != "KRW" else "withdraws/krw"
    url = f"{API_BASE}/{url_path}"
    
    query_params = {
        'currency': currency,
        'amount': amount
    }
    
    if address:
        query_params['address'] = address
    
    if secondary_address:
        query_params['secondary_address'] = secondary_address
    
    if transaction_type:
        query_params['transaction_type'] = transaction_type
    
    headers = {
        "Authorization": f"Bearer {generate_upbit_token(query_params)}"
    }
    
    if ctx:
        ctx.info(f"{currency} 출금 요청 중: {amount}")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, params=query_params, headers=headers)
            if res.status_code != 200:
                if ctx:
                    ctx.error(f"업비트 API 오류: {res.status_code} - {res.text}")
                return {"error": f"업비트 API 오류: {res.status_code} - {res.text}"}
            return res.json()
        except Exception as e:
            if ctx:
                ctx.error(f"API 호출 중 오류 발생: {str(e)}")
            return {"error": f"API 호출 중 오류 발생: {str(e)}"}