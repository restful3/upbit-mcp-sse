from fastmcp import Context
import httpx
from typing import Optional
from config import generate_upbit_token, UPBIT_ACCESS_KEY, API_BASE

async def get_order(
    uuid: Optional[str] = None,
    identifier: Optional[str] = None,
    ctx: Optional[Context] = None
) -> dict:
    """
    개별 주문의 상세 내역을 조회합니다. (인증 필요)

    Upbit의 개별 주문 조회 API 엔드포인트(/v1/order)에 GET 요청을 보내, 
    `uuid` 또는 `identifier`를 사용하여 특정 주문의 체결 또는 미체결 내역을 상세하게 가져옵니다.
    API 키 설정이 필수적입니다.

    Args:
        uuid (Optional[str]): 조회할 주문의 고유 UUID.
        identifier (Optional[str]): 주문 생성 시 사용자가 지정한 조회용 ID.
                                 `uuid`와 `identifier` 중 적어도 하나는 반드시 제공되어야 합니다.
        ctx (Context, optional): FastMCP 컨텍스트 객체. 함수 실행 중 정보나 오류를 로깅하는 데 사용됩니다.

    Returns:
        dict:
            - 성공 시: 조회된 주문의 상세 정보를 담은 딕셔너리. 주요 키는 다음과 같습니다:
                - `uuid` (str): 주문의 고유 UUID
                - `side` (str): 주문 종류 ('bid': 매수, 'ask': 매도)
                - `ord_type` (str): 주문 방식 ('limit', 'market' 등)
                - `price` (str): 주문 가격
                - `state` (str): 주문 상태 ('wait', 'done', 'cancel')
                - `market` (str): 마켓 코드
                - `created_at` (str): 주문 시각
                - `trades_count` (int): 해당 주문에 연관된 체결 수
                - `trades` (list[dict]): 체결 내역 상세 정보 리스트
                - ... 등 Upbit 주문 조회 API에서 제공하는 모든 필드.
            - 실패 시: 오류의 원인을 설명하는 메시지를 포함한 딕셔너리.
                - `{"error": "오류 메시지"}` 형식입니다.

    Example:
        >>> # 'some-order-uuid-1234'를 실제 주문 UUID로 대체해야 합니다.
        >>> order_details = await get_order(uuid="some-order-uuid-1234")
        >>> if "error" not in order_details:
        ...     print(f"주문 상태: {order_details['state']}, 체결 수: {order_details['trades_count']}")
        ... else:
        ...     print(f"오류: {order_details['error']}")
    """
    if not UPBIT_ACCESS_KEY:
        if ctx:
            ctx.error("API 키가 설정되지 않았습니다. .env 파일에 UPBIT_ACCESS_KEY와 UPBIT_SECRET_KEY를 설정해주세요.")
        return {"error": "API 키가 설정되지 않았습니다."}
    
    if not uuid and not identifier:
        if ctx:
            ctx.error("uuid 또는 identifier 중 하나는 필수입니다.")
        return {"error": "uuid 또는 identifier 중 하나는 필수입니다."}
    
    url = f"{API_BASE}/order"
    query_params = {}
    
    if uuid:
        query_params['uuid'] = uuid
    
    if identifier:
        query_params['identifier'] = identifier
    
    headers = {
        "Authorization": f"Bearer {generate_upbit_token(query_params)}"
    }
    
    if ctx:
        ctx.info(f"주문 정보 조회 중: {uuid or identifier}")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, params=query_params, headers=headers)
            if res.status_code != 200:
                if ctx:
                    ctx.error(f"업비트 API 오류: {res.status_code} - {res.text}")
                return {"error": f"업비트 API 오류: {res.status_code} - {res.text}"}
            return res.json()
        except Exception as e:
            if ctx:
                ctx.error(f"API 호출 중 오류 발생: {str(e)}")
            return {"error": f"API 호출 중 오류 발생: {str(e)}"}