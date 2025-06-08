from fastmcp import Context
import httpx
from typing import Optional
from config import API_BASE, MAJOR_COINS, create_error_response

async def get_market_summary(ctx: Optional[Context] = None) -> dict:
    """
    Upbit KRW 전체 마켓의 현재 상황을 요약하여 제공합니다.

    Upbit API를 통해 모든 KRW 마켓의 시세(Ticker) 정보를 조회한 후, 이를 바탕으로 
    시장 상황을 한눈에 파악할 수 있는 요약 정보를 생성합니다. 이 함수는 여러 API 호출을 포함할 수 있습니다.

    반환되는 정보에는 사전에 정의된 주요 코인들의 시세, 24시간 거래대금 상위 5개 코인, 
    상승률 상위 5개 코인, 하락률 상위 5개 코인이 포함됩니다.

    Args:
        ctx (Context, optional): FastMCP 컨텍스트 객체. 함수 실행 중 정보나 오류를 로깅하는 데 사용됩니다.

    Returns:
        dict:
            - 성공 시: 시장 요약 정보를 담은 딕셔너리. 주요 키는 다음과 같습니다:
                - `timestamp` (int): 데이터 조회 시점의 타임스탬프
                - `major_coins` (list[dict]): `config.py`에 정의된 주요 코인들의 시세 정보 리스트
                - `top_volume` (list[dict]): 24시간 거래대금 상위 5개 코인의 시세 정보 리스트
                - `top_gainers` (list[dict]): 24시간 등락률 상위 5개 코인의 시세 정보 리스트
                - `top_losers` (list[dict]): 24시간 등락률 하위 5개 코인의 시세 정보 리스트
                - `krw_market_count` (int): 전체 KRW 마켓의 개수
            - 실패 시: `{"error": "오류 메시지"}` 형식의 딕셔너리.

    Example:
        >>> summary = await get_market_summary()
        >>> if "error" not in summary:
        ...     print(f"총 {summary['krw_market_count']}개의 KRW 마켓이 운영 중입니다.")
        ...     print(f"거래대금 1위: {summary['top_volume'][0]['market']}")
        ... else:
        ...     print(f"오류: {summary['error']}")
    """
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
            
            # 티커 정보 가져오기 (50개씩 나누어 요청)
            all_tickers = []
            chunk_size = 50
            
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
            
            # 주요 코인 정보
            major_coin_info = [ticker for ticker in all_tickers if ticker["market"] in MAJOR_COINS]
            
            # 상위 거래량 코인 (주요 코인 제외)
            volume_sorted = sorted([t for t in all_tickers if t["market"] not in MAJOR_COINS], 
                                  key=lambda x: x["acc_trade_price_24h"], 
                                  reverse=True)
            top_volume_coins = volume_sorted[:5]
            
            # 상위 상승률 코인
            price_change_sorted = sorted(all_tickers, key=lambda x: x["signed_change_rate"], reverse=True)
            top_gainers = price_change_sorted[:5]
            
            # 상위 하락률 코인
            top_losers = price_change_sorted[-5:]
            
            return {
                "timestamp": all_tickers[0]["timestamp"] if all_tickers else None,
                "major_coins": major_coin_info,
                "top_volume": top_volume_coins,
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