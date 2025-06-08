from fastmcp import Context
import httpx
from typing import Literal, Optional
from config import generate_upbit_token, UPBIT_ACCESS_KEY, API_BASE

async def get_deposits_withdrawals(
    currency: Optional[str] = None,
    txid: Optional[str] = None,
    transaction_type: Literal["deposit", "withdraw"] = "deposit",
    page: int = 1,
    limit: int = 100,
    ctx: Optional[Context] = None
) -> list[dict]:
    """
    특정 통화의 입금 또는 출금 내역을 조회합니다. (인증 필요)

    Upbit의 입금 목록 조회(/v1/deposits) 또는 출금 목록 조회(/v1/withdraws) API에 GET 요청을 보내, 
    과거 입출금 기록을 가져옵니다. API 키 설정이 필수적입니다.

    Args:
        currency (Optional[str]): 조회할 통화의 코드 (예: "KRW", "BTC"). 지정하지 않으면 전체 통화에 대해 조회합니다.
        txid (Optional[str]): 조회할 입출금 내역의 고유 트랜잭션 ID.
        transaction_type (Literal["deposit", "withdraw"]): 조회할 거래 유형. "deposit"은 입금, "withdraw"는 출금입니다.
        page (int): 결과의 페이지 번호. 기본값은 1입니다.
        limit (int): 한 페이지에 표시할 결과의 수. 기본값은 100입니다.
        ctx (Context, optional): FastMCP 컨텍스트 객체. 함수 실행 중 정보나 오류를 로깅하는 데 사용됩니다.

    Returns:
        list[dict]:
            - 성공 시: 입금 또는 출금 내역의 정보를 담은 딕셔너리의 리스트. 주요 키는 다음과 같습니다:
                - `type` (str): 거래 유형 ('deposit' 또는 'withdraw')
                - `uuid` (str): 입출금의 고유 UUID
                - `currency` (str): 통화 코드
                - `amount` (str): 수량/금액
                - `state` (str): 진행 상태 (e.g., 'DONE', 'ACCEPTED')
                - `created_at` (str): 요청 시각
                - `txid` (str): 트랜잭션 ID
                - ... 등 Upbit 입출금 조회 API에서 제공하는 모든 필드.
            - 실패 시: 오류 정보를 담은 딕셔너리를 포함한 리스트.
                - `[{"error": "오류 메시지"}]` 형식입니다.

    Example:
        >>> # 가장 최근 비트코인(BTC) 입금 내역 조회
        >>> btc_deposits = await get_deposits_withdrawals(currency="BTC", transaction_type="deposit")
        >>> if btc_deposits and "error" not in btc_deposits[0]:
        ...     print(f"최근 BTC 입금: {btc_deposits[0]['amount']} BTC, 상태: {btc_deposits[0]['state']}")
        ... else:
        ...     print(f"오류 또는 내역 없음: {btc_deposits}")
    """
    if not UPBIT_ACCESS_KEY:
        if ctx:
            ctx.error("API 키가 설정되지 않았습니다. .env 파일에 UPBIT_ACCESS_KEY와 UPBIT_SECRET_KEY를 설정해주세요.")
        return [{"error": "API 키가 설정되지 않았습니다."}]
    
    url = f"{API_BASE}/{transaction_type}s"
    query_params = {
        'page': str(page),
        'limit': str(limit)
    }
    
    if currency:
        query_params['currency'] = currency
    
    if txid:
        query_params['txid'] = txid
    
    headers = {
        "Authorization": f"Bearer {generate_upbit_token(query_params)}"
    }
    
    if ctx:
        ctx.info(f"{transaction_type} 내역 조회 중")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, params=query_params, headers=headers)
            if res.status_code != 200:
                if ctx:
                    ctx.error(f"업비트 API 오류: {res.status_code} - {res.text}")
                return [{"error": f"업비트 API 오류: {res.status_code} - {res.text}"}]
            return res.json()
        except Exception as e:
            if ctx:
                ctx.error(f"API 호출 중 오류 발생: {str(e)}")
            return [{"error": f"API 호출 중 오류 발생: {str(e)}"}]