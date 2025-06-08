# main.py
print("DEBUG: main.py execution started", flush=True) # 로그 추가
from mcp.server.fastmcp import FastMCP, Context # FastMCP 1.0.0 권장 import 경로
# from config import UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY, API_BASE # 일단 주석 처리
# import httpx # dummy_tool에 필요 없으면 주석 처리 가능 -> 이미 활성화 됨
import asyncio
# import uvicorn # uvicorn 직접 실행 안 함

print("DEBUG: Imports in main.py finished", flush=True) # 로그 추가

from tools.technical_analysis import technical_analysis # technical_analysis 주석 해제
# --- 모든 외부 툴, 프롬프트, 리소스 import 제거 ---
from tools.get_ticker import get_ticker
from tools.get_orderbook import get_orderbook
from tools.get_trades import get_trades
from tools.get_accounts import get_accounts
from tools.create_order import create_order
from tools.get_orders import get_orders
from tools.get_order import get_order
from tools.cancel_order import cancel_order
from tools.get_market_summary import get_market_summary
from tools.get_deposits_withdrawals import get_deposits_withdrawals
from tools.get_markets import get_markets
from tools.get_candles import get_candles
from tools.create_withdraw import create_withdraw

print("DEBUG: Tool imports in main.py finished", flush=True) # 로그 추가

from prompts.explain_ticker import explain_ticker
from prompts.analyze_portfolio import analyze_portfolio
from prompts.order_help import order_help
from prompts.trading_strategy import trading_strategy

from resources.get_market_list import get_market_list

print("✅ API 키 관련 로직은 일단 생략합니다.", flush=True)


mcp = FastMCP(
    "Upbit MCP Server with Technical Analysis", 
    description="FastMCP 1.0.0 with SSE, upbit tool, and technical analysis.",
    port=8001  # 생성자에 포트 추가
)

try:
    # FastMCP 1.0.0의 내부 툴 저장 방식은 다를 수 있음
    print(f"MCP tools (before): {getattr(mcp, 'tools', 'not found or different structure')}", flush=True) 
    print(f"MCP _tools (before): {getattr(mcp, '_tools', 'not found or different structure')}", flush=True)
except AttributeError:
    pass

tool_decorator_instance = mcp.tool()

mcp.tool()(technical_analysis) # technical_analysis 툴 등록 주석 해제
mcp.tool()(get_ticker)
mcp.tool()(get_orderbook)
mcp.tool()(get_trades)
mcp.tool()(get_accounts)
mcp.tool()(create_order)
mcp.tool()(get_orders)
mcp.tool()(get_order)
mcp.tool()(cancel_order)
mcp.tool()(get_market_summary)
mcp.tool()(get_deposits_withdrawals)
mcp.tool()(get_markets)
mcp.tool()(get_candles)
mcp.tool()(create_withdraw)
print(f"--- Additional tools registered ---", flush=True)

# --- 다른 모든 mcp.resource, mcp.prompt 등록 제거 ---

mcp.resource("market://list")(get_market_list)

mcp.prompt()(explain_ticker)
mcp.prompt()(analyze_portfolio)
mcp.prompt()(order_help)
mcp.prompt()(trading_strategy)

if __name__ == "__main__":
    print("DEBUG: Entering __main__ block", flush=True)
    print("FastMCP 1.0.0 + SSE 테스트 서버 시작 (Target Port: 8001)", flush=True)
    
    # target_host = "0.0.0.0" # 더 이상 사용하지 않음
    # target_port = 8001 # 생성자에서 이미 설정됨

    try:
        # mcp.port로 직접 접근하는 대신, 생성자에 전달된 포트 값(8001)을 명시적으로 언급합니다.
        print(f"DEBUG: About to call mcp.run(transport='sse') using constructor port (expected: 8001)", flush=True)
        mcp.run(transport="sse") # host, port 인자 제거
    except Exception as e:
        print(f"An unexpected error occurred during mcp.run(): {e}", flush=True)