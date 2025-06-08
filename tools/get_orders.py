from fastmcp import Context
import httpx
from typing import Optional, Literal
from config import generate_upbit_token, UPBIT_ACCESS_KEY, API_BASE

async def get_orders(
    market: Optional[str] = None,
    state: Literal["wait", "done", "cancel"] = "wait",
    page: int = 1,
    limit: int = 100,
    ctx: Optional[Context] = None
) -> list[dict]:
    """
    주문 목록을 필터링하여 조회합니다. (인증 필요)

    Upbit의 주문 목록 조회 API 엔드포인트(/v1/orders)에 GET 요청을 보내, 
    특정 마켓 또는 특정 상태의 주문 목록을 가져옵니다. API 키 설정이 필수적입니다.

    Args:
        market (Optional[str]): 조회할 마켓의 코드 (예: "KRW-BTC"). 지정하지 않으면 모든 마켓의 주문을 조회합니다.
        state (Literal["wait", "done", "cancel"]): 조회할 주문의 상태.
            - "wait": 미체결 주문 (기본값)
            - "done": 완료된 주문 (체결 완료)
            - "cancel": 취소된 주문
        page (int): 결과의 페이지 번호. 기본값은 1입니다.
        limit (int): 한 페이지에 표시할 주문의 수. 기본값은 100입니다.
        ctx (Context, optional): FastMCP 컨텍스트 객체. 함수 실행 중 정보나 오류를 로깅하는 데 사용됩니다.

    Returns:
        list[dict]:
            - 성공 시: 조회된 주문의 정보를 담은 딕셔너리의 리스트.
                      리스트의 각 항목은 `get_order`가 반환하는 주문 상세 정보와 유사한 구조를 가집니다.
            - 실패 시: 오류 정보를 담은 딕셔너리를 포함한 리스트.
                - `[{"error": "오류 메시지"}]` 형식입니다.

    Example:
        >>> # 현재 모든 마켓의 미체결 주문 조회
        >>> pending_orders = await get_orders(state="wait")
        >>> if pending_orders and "error" not in pending_orders[0]:
        ...     print(f"총 {len(pending_orders)}개의 미체결 주문이 있습니다.")
        ... else:
        ...     print(f"오류 또는 미체결 주문 없음: {pending_orders}")
        >>>
        >>> # KRW-BTC 마켓의 체결 완료된 주문 조회
        >>> btc_done_orders = await get_orders(market="KRW-BTC", state="done")
    """
    if not UPBIT_ACCESS_KEY:
        if ctx:
            ctx.error("API 키가 설정되지 않았습니다. .env 파일에 UPBIT_ACCESS_KEY와 UPBIT_SECRET_KEY를 설정해주세요.")
        return [{"error": "API 키가 설정되지 않았습니다."}]
    
    url = f"{API_BASE}/orders"
    query_params = {
        'state': state,
        'page': str(page),
        'limit': str(limit)
    }
    
    if market:
        query_params['market'] = market
    
    headers = {
        "Authorization": f"Bearer {generate_upbit_token(query_params)}"
    }
    
    if ctx:
        ctx.info(f"주문 내역 조회 중: 상태={state}")
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