import httpx
from fastmcp import Context
from typing import Literal, Optional, Union
from config import generate_upbit_token, UPBIT_ACCESS_KEY, API_BASE

async def create_order(
    market: str, 
    side: Literal["bid", "ask"], 
    ord_type: Literal["limit", "price", "market"],
    volume: Optional[Union[str, float, int]] = None,
    price: Optional[Union[str, float, int]] = None,
    ctx: Optional[Context] = None
) -> dict:
    """
    지정가, 시장가 매수/매도 주문을 생성합니다. (인증 필요)

    Upbit의 주문 생성 API 엔드포인트(/v1/orders)에 POST 요청을 보내 새로운 주문을 생성합니다.
    주문 유형(ord_type)에 따라 필수 파라미터가 달라지므로 주의해야 합니다. API 키 설정이 필수적입니다.

    Args:
        market (str): 마켓 코드 (예: "KRW-BTC")
        side (Literal["bid", "ask"]): 주문 종류. "bid"는 매수, "ask"는 매도입니다.
        ord_type (Literal["limit", "price", "market"]): 주문 방식.
            - "limit": 지정가 주문. `volume`(주문량)과 `price`(주문가)가 모두 필요합니다.
            - "price": 시장가 매수 주문. `price`(주문 총액)가 필요합니다.
            - "market": 시장가 매도 주문. `volume`(주문량)이 필요합니다.
        volume (Optional[Union[str, float, int]]): 주문량. (지정가, 시장가 매도 시 필수)
        price (Optional[Union[str, float, int]]): 주문 가격 또는 주문 총액. (지정가, 시장가 매수 시 필수)
        ctx (Context, optional): FastMCP 컨텍스트 객체. 함수 실행 중 정보나 오류를 로깅하는 데 사용됩니다.

    Returns:
        dict:
            - 성공 시: 생성된 주문의 상세 정보를 담은 딕셔너리. 주요 키는 다음과 같습니다:
                - `uuid` (str): 생성된 주문의 고유 UUID
                - `side` (str): 주문 종류 ('bid' 또는 'ask')
                - `ord_type` (str): 주문 방식
                - `price` (str): 주문 가격
                - `volume` (str): 주문량
                - `state` (str): 주문 상태 (e.g., 'wait' - 체결 대기)
                - `market` (str): 마켓 코드
                - ... 등 Upbit 주문 조회 API에서 제공하는 모든 필드.
            - 실패 시: 오류의 원인을 설명하는 메시지를 포함한 딕셔너리.
                - `{"error": "오류 메시지"}` 형식입니다.

    Example:
        >>> # KRW-BTC 지정가 매수 주문 (0.01개, 50,000,000원)
        >>> order_result = await create_order(market="KRW-BTC", side="bid", ord_type="limit", volume="0.01", price="50000000")
        >>>
        >>> # KRW-BTC 시장가 매수 주문 (50,000원 어치)
        >>> order_result_market_buy = await create_order(market="KRW-BTC", side="bid", ord_type="price", price="50000")
        >>>
        >>> # KRW-BTC 시장가 매도 주문 (0.01개)
        >>> order_result_market_sell = await create_order(market="KRW-BTC", side="ask", ord_type="market", volume="0.01")
    """
    if not UPBIT_ACCESS_KEY:
        if ctx:
            ctx.error("API 키가 설정되지 않았습니다. .env 파일에 UPBIT_ACCESS_KEY와 UPBIT_SECRET_KEY를 설정해주세요.")
        return {"error": "API 키가 설정되지 않았습니다."}
    
    # 주문 유효성 검사 (타입 변환 전 원본 값으로 검사할 수도 있지만, 일단 문자열 변환 후 검사하는 로직은 유지)
    # volume과 price가 None이 아니고, 문자열로 변환 가능한 숫자 형태라고 가정.
    str_volume = str(volume) if volume is not None else None
    str_price = str(price) if price is not None else None 

    if ord_type == "limit" and (str_volume is None or str_price is None):
        if ctx:
            ctx.error("지정가 주문에는 volume과 price가 모두 필요합니다.")
        return {"error": "지정가 주문에는 volume과 price가 모두 필요합니다."}
    
    if ord_type == "price" and str_price is None:
        if ctx:
            ctx.error("시장가 매수 주문에는 price가 필요합니다.")
        return {"error": "시장가 매수 주문에는 price가 필요합니다."}
    
    if ord_type == "market" and str_volume is None:
        if ctx:
            ctx.error("시장가 매도 주문에는 volume이 필요합니다.")
        return {"error": "시장가 매도 주문에는 volume이 필요합니다."}
    
    url = f"{API_BASE}/orders"
    query_params = {
        'market': market,
        'side': side,
        'ord_type': ord_type
    }
    
    if str_volume is not None: # 문자열로 변환된 값 사용
        query_params['volume'] = str_volume
    
    if str_price is not None: # 문자열로 변환된 값 사용
        query_params['price'] = str_price
    
    headers = {
        "Authorization": f"Bearer {generate_upbit_token(query_params)}"
    }
    
    if ctx:
        ctx.info(f"주문 생성 중: {market} {side} {ord_type}, params: {query_params}") # query_params 로깅 추가
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, params=query_params, headers=headers)
            if res.status_code != 201: # 생성 성공 코드는 201
                if ctx:
                    ctx.error(f"업비트 API 오류: {res.status_code} - {res.text}")
                return {"error": f"업비트 API 오류: {res.status_code} - {res.text}"} # API 응답 텍스트 포함
            return res.json()
        except Exception as e:
            if ctx:
                ctx.error(f"API 호출 중 오류 발생: {str(e)}")
            return {"error": f"API 호출 중 오류 발생: {str(e)}"}