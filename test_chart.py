#!/usr/bin/env python3
"""
차트 생성 기능 테스트 스크립트
"""
import asyncio
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_chart_generation():
    """차트 생성 기능을 테스트합니다."""
    try:
        from tools.generate_chart_image import generate_chart_image
        
        print("🚀 차트 생성 테스트 시작...")
        
        # 비트코인 일봉 캔들스틱 차트 생성
        result = await generate_chart_image(
            market="KRW-BTC",
            interval="day",
            chart_type="candlestick",
            count=50,
            include_volume=True,
            include_ma=True
        )
        
        print("📊 테스트 결과:")
        print(f"  - 성공 여부: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"  - 파일 경로: {result.get('file_path', 'N/A')}")
            print(f"  - 이미지 URL: {result.get('image_url', 'N/A')}")
            print(f"  - 파일명: {result.get('filename', 'N/A')}")
            print(f"  - 메시지: {result.get('message', 'N/A')}")
        else:
            print(f"  - 오류: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chart_generation()) 