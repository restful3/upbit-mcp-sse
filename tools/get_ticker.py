import httpx
from config import API_BASE
import json

async def get_ticker(symbol: str) -> dict:
    print(f"DEBUG: get_ticker called with symbol: {symbol}", flush=True)
    """Get the latest ticker data from Upbit"""
    url = f"{API_BASE}/ticker"
    print(f"DEBUG: get_ticker requesting URL: {url} with params: {{'markets': symbol}}", flush=True)
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, params={"markets": symbol})
            res.raise_for_status()
            data = res.json()
            print(f"DEBUG: get_ticker received data: {json.dumps(data)}", flush=True)
            if not data:
                print(f"ERROR: get_ticker received empty data for symbol: {symbol}", flush=True)
                return {"error": f"Upbit API returned empty data for symbol: {symbol}"}
            return data[0]
        except httpx.HTTPStatusError as e:
            error_message = f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
            print(f"ERROR: get_ticker {error_message}", flush=True)
            return {"error": f"Upbit API request failed for {symbol}: {error_message}"}
        except httpx.RequestError as e:
            error_message = f"Request error occurred: {str(e)}"
            print(f"ERROR: get_ticker {error_message}", flush=True)
            return {"error": f"Upbit API request failed for {symbol}: {error_message}"}
        except json.JSONDecodeError as e:
            error_message = f"Failed to decode JSON response: {str(e)}. Response text: {res.text if 'res' in locals() else 'Response object not available'}"
            print(f"ERROR: get_ticker {error_message}", flush=True)
            return {"error": f"Upbit API returned invalid JSON for {symbol}: {error_message}"}
        except IndexError as e:
            error_message = f"Data list is empty, cannot access index 0. Response: {json.dumps(data) if 'data' in locals() else 'Data not available'}"
            print(f"ERROR: get_ticker {error_message}", flush=True)
            return {"error": f"Upbit API returned unexpected data structure for {symbol}: {error_message}"}
        except Exception as e:
            error_message = f"An unexpected error occurred in get_ticker: {str(e)}"
            print(f"ERROR: get_ticker {error_message}", flush=True)
            return {"error": f"An unexpected error occurred while fetching ticker for {symbol}: {error_message}"}