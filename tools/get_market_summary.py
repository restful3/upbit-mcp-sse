from fastmcp import Context
import httpx
from typing import Optional
from config import API_BASE, create_error_response

async def get_market_summary(ctx: Optional[Context] = None, major_n: int = 5, top_n: int = 5, sort_by: str = "trade_price") -> dict:
    """
    Upbit KRW 전체 마켓의 현재 상황을 동적으로 요약하여 제공합니다.

    Upbit API를 통해 모든 KRW 마켓의 시세(Ticker) 정보를 조회한 후,
    `sort_by` 파라미터에 따라 '거래대금' 또는 '거래량'을 기준으로 코인을 정렬하고 요약합니다.
    상승률 및 하락률 상위 코인 정보도 함께 제공하여 시장 상황을 한눈에 파악할 수 있도록 합니다.

    Args:
        ctx (Context, optional): FastMCP 컨텍스트 객체. 함수 실행 중 정보나 오류를 로깅하는 데 사용됩니다.
        major_n (int, optional): `sort_by` 기준으로 '주요 코인'으로 선정할 개수입니다. 기본값은 5입니다.
        top_n (int, optional): '주요 코인' 외에 추가로 보여줄 순위 개수입니다. 기본값은 5입니다.
        sort_by (str, optional): 정렬 기준입니다. 'trade_price'(거래대금, 기본값) 또는 'trade_volume'(거래량)을 선택할 수 있습니다.

    Returns:
        dict:
            - 성공 시: 시장 요약 정보를 담은 딕셔너리. 주요 키는 다음과 같습니다:
                - `timestamp` (int): 데이터 조회 시점의 타임스탬프
                - `major_coins` (list[dict]): `sort_by` 기준 상위 `major_n`개 코인의 시세 정보 리스트
                - `next_top_coins` (list[dict]): '주요 코인'을 제외한 `sort_by` 기준 상위 `top_n`개 코인의 시세 정보 리스트
                - `top_gainers` (list[dict]): 24시간 등락률 상위 `top_n`개 코인의 시세 정보 리스트
                - `top_losers` (list[dict]): 24시간 등락률 하위 `top_n`개 코인의 시세 정보 리스트
                - `krw_market_count` (int): 전체 KRW 마켓의 개수
            - 실패 시: `{"error": "오류 메시지"}` 형식의 딕셔너리.

    Example:
        >>> # 거래량 상위 10개 코인만 조회하고 싶을 때
        >>> summary = await get_market_summary(major_n=10, top_n=0, sort_by="trade_volume")
        >>> if "error" not in summary:
        ...     print(f"거래량 1~10위: {[c['market'] for c in summary['major_coins']]}")
        ... else:
        ...     print(f"오류: {summary['error']}")
    """
    if sort_by not in ["trade_price", "trade_volume"]:
        return create_error_response("Invalid sort_by parameter. Must be 'trade_price' or 'trade_volume'.", 400)
        
    async with httpx.AsyncClient() as client:
        # 마켓 정보 가져오기
        try:
            markets_res = await client.get(f"{API_BASE}/market/all")
            if markets_res.status_code != 200:
                if ctx:
                    ctx.error(f"마켓 정보 조회 실패: {markets_res.status_code} - {markets_res.text}")
                return create_error_response("마켓 정보 조회에 실패했습니다.", markets_res.status_code)
            
            all_markets = markets_res.json()
            krw_markets = [market for market in all_markets if market["market"].startswith("KRW-")]
            
            # 티커 정보 가져오기 (100개씩 나누어 요청)
            all_tickers = []
            chunk_size = 100 # 청크 사이즈 상향 조정
            
            for i in range(0, len(krw_markets), chunk_size):
                chunk = krw_markets[i:i+chunk_size]
                markets_param = ",".join([market["market"] for market in chunk])
                
                ticker_res = await client.get(f"{API_BASE}/ticker", params={"markets": markets_param})
                if ticker_res.status_code != 200:
                    if ctx:
                        ctx.warning(f"일부 티커 정보 조회 실패: {ticker_res.status_code} - {ticker_res.text}")
                    continue
                    
                all_tickers.extend(ticker_res.json())
            
            if not all_tickers:
                return create_error_response("티커 정보를 조회하는데 실패했습니다.", 500)
            
            # 정렬 기준 설정
            sort_key = "acc_trade_price_24h" if sort_by == "trade_price" else "acc_trade_volume_24h"

            # 선택된 기준으로 모든 티커 정렬
            sorted_tickers = sorted(all_tickers, key=lambda x: x.get(sort_key, 0), reverse=True)
            
            # 주요 코인 및 다음 순위 코인 동적 선정
            major_coin_info = sorted_tickers[:major_n]
            next_top_coins = sorted_tickers[major_n:major_n + top_n]
            
            # 상위 상승률 코인
            price_change_sorted = sorted(all_tickers, key=lambda x: x.get("signed_change_rate", 0), reverse=True)
            top_gainers = price_change_sorted[:top_n]
            
            # 상위 하락률 코인
            top_losers = price_change_sorted[-top_n:]
            
            return {
                "timestamp": all_tickers[0].get("timestamp"),
                "major_coins": major_coin_info,
                "next_top_coins": next_top_coins,
                "top_gainers": top_gainers,
                "top_losers": list(reversed(top_losers)),
                "krw_market_count": len(krw_markets)
            }
        except httpx.RequestError as e:
            if ctx:
                ctx.error(f"API 호출 중 오류 발생: {str(e)}")
            return create_error_response(f"API 호출 중 오류가 발생했습니다: {e}", 500)
        except Exception as e:
            if ctx:
                ctx.error(f"시장 요약 정보 생성 중 알 수 없는 오류 발생: {str(e)}")
            return create_error_response(f"시장 요약 정보 생성 중 알 수 없는 오류가 발생했습니다: {e}", 500)