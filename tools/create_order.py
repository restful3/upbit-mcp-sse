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
    print(f"DEBUG: create_order called. market={market}, side={side}, ord_type={ord_type}, volume={volume} (type: {type(volume)}), price={price} (type: {type(price)}), ctx_type={type(ctx)}", flush=True)
    """
    업비트에 주문을 생성합니다.
    
    Args:
        market (str): 마켓 코드 (예: KRW-BTC)
        side (str): 주문 종류 - bid(매수) 또는 ask(매도)
        ord_type (str): 주문 타입 - limit(지정가), price(시장가 매수), market(시장가 매도)
        volume (str, float, int, optional): 주문량 (지정가, 시장가 매도 필수)
        price (str, float, int, optional): 주문 가격 (지정가 필수, 시장가 매수 필수)
        
    Returns:
        dict: 주문 결과
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