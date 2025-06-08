import httpx
from fastmcp import Context
from typing import Optional
from config import generate_upbit_token, UPBIT_ACCESS_KEY, API_BASE

async def cancel_order(
    uuid: str,
    ctx: Optional[Context] = None
) -> dict:
    """
    주어진 UUID에 해당하는 주문을 취소합니다. (인증 필요)

    이 함수는 Upbit의 주문 취소 API 엔드포인트(/v1/order)에 DELETE 요청을 보내, 
    미체결 상태의 특정 주문을 취소합니다. API 키 설정이 필수적입니다.

    Args:
        uuid (str): 취소하고자 하는 주문의 고유 UUID. `get_orders`나 `create_order`를 통해 얻을 수 있습니다.
        ctx (Context, optional): FastMCP 컨텍스트 객체. 함수 실행 중 정보나 오류를 로깅하는 데 사용됩니다.

    Returns:
        dict:
            - 성공 시: 취소된 주문의 상세 정보를 담은 딕셔너리. 주요 키는 다음과 같습니다:
                - `uuid` (str): 취소된 주문의 UUID
                - `side` (str): 주문 종류 ('bid': 매수, 'ask': 매도)
                - `ord_type` (str): 주문 방식 ('limit': 지정가, 'market': 시장가 등)
                - `price` (str): 주문 가격
                - `state` (str): 주문 상태 (e.g., 'cancel' - 취소됨)
                - `market` (str): 마켓 코드 (e.g., "KRW-BTC")
                - ... 등 Upbit 주문 조회 API에서 제공하는 모든 필드.
            - 실패 시: 오류의 원인을 설명하는 메시지를 포함한 딕셔너리.
                - `{"error": "오류 메시지"}` 형식입니다.
                - API 키 미설정, API 요청 실패, 존재하지 않는 UUID 등의 경우에 반환됩니다.

    Example:
        >>> # 'some-order-uuid-1234'를 실제 주문 UUID로 대체해야 합니다.
        >>> canceled_order = await cancel_order("some-order-uuid-1234")
        >>> if "error" not in canceled_order:
        ...     print(f"주문이 성공적으로 취소되었습니다. 상태: {canceled_order['state']}")
        ... else:
        ...     print(f"오류 발생: {canceled_order['error']}")
    """
    if not UPBIT_ACCESS_KEY:
        if ctx:
            ctx.error("API 키가 설정되지 않았습니다. .env 파일에 UPBIT_ACCESS_KEY와 UPBIT_SECRET_KEY를 설정해주세요.")
        return {"error": "API 키가 설정되지 않았습니다."}
    
    url = f"{API_BASE}/order"
    query_params = {'uuid': uuid}
    headers = {
        "Authorization": f"Bearer {generate_upbit_token(query_params)}"
    }
    
    if ctx:
        ctx.info(f"주문 취소 중: {uuid}")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.delete(url, params=query_params, headers=headers)
            if res.status_code != 200:
                if ctx:
                    ctx.error(f"업비트 API 오류: {res.status_code} - {res.text}")
                return {"error": f"업비트 API 오류: {res.status_code} - {res.text}"}
            return res.json()
        except Exception as e:
            if ctx:
                ctx.error(f"API 호출 중 오류 발생: {str(e)}")
            return {"error": f"API 호출 중 오류 발생: {str(e)}"}