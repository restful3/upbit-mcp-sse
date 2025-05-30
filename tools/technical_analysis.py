from fastmcp import Context
import httpx
import numpy as np
from typing import List, Literal, Dict, Any, Optional, Set
from config import API_BASE

# 사용 가능한 지표 및 신호 키 정의
# AVAILABLE_INDICATOR_KEYS: Set[str] = {
#     "sma", "rsi", "bollinger_bands", "macd", "stochastic", "volume", "pivots", "current_price"
# }
# AVAILABLE_SIGNAL_KEYS: Set[str] = {
#     "ma_signal", "rsi_signal", "bb_signal", "macd_signal", "stoch_signal", "overall_signal"
# }
# ALL_KEYS: Set[str] = AVAILABLE_INDICATOR_KEYS.union(AVAILABLE_SIGNAL_KEYS)

# overall_signal이 의존하는 개별 신호 키들
# OVERALL_SIGNAL_DEPENDENCIES: Set[str] = {
#     "ma_signal", "rsi_signal", "bb_signal", "macd_signal", "stoch_signal"
# }

def technical_analysis(
    market: str,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    print(f"DEBUG: technical_analysis called. market={market}, ctx_type={type(ctx)}", flush=True)
    """
    (단순 테스트용) 특정 마켓에 대한 매우 간단한 기술적 분석을 수행합니다.
    """
    if ctx:
        # 이 로그가 찍히는지 확인하는 것이 매우 중요합니다.
        ctx.info(f"SYNC_DEBUG_SIMPLE_TOOL: technical_analysis_simple called with market: {market}")
    
    # 매우 간단한 결과 반환
    result = {
        "status": "ok",
        "tool_name": "technical_analysis_simple_test",
        "market_received": market,
        "message": "This is a simple synchronous tool test response."
    }
    
    if ctx:
        ctx.info(f"SYNC_DEBUG_SIMPLE_TOOL: Returning simple result: {result}")
        
    return result

# 기존 main_test 함수는 현재 테스트와 직접 관련 없으므로 그대로 두거나 주석 처리
def main_test():
    class MockContext:
        def info(self, msg): print(f"INFO: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")

    ctx = MockContext()
    # print("SYNC_DEBUG: main_test (동기)는 서버를 통해 테스트해야 합니다.")
    # 직접 호출 테스트 (단순화된 함수)
    # test_result = technical_analysis(market="KRW-BTC", ctx=ctx)
    # import json
    # print(json.dumps(test_result, indent=2, ensure_ascii=False))
    print("SYNC_DEBUG_SIMPLE_TOOL: main_test is for direct script execution, not server testing.")


if __name__ == '__main__':
    main_test()