"""
RAG API 테스트 스크립트
"""

import asyncio
import sys
import httpx
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))


class RAGAPITester:
    """RAG API 테스터"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def test_health_check(self):
        """상태 확인 엔드포인트 테스트"""
        print("=== 상태 확인 테스트 ===")
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            print(f"상태: {response.status_code}")
            print(f"응답: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"상태 확인 실패: {e}")
            return False
    
    async def test_rag_status(self):
        """RAG 시스템 상태 조회 테스트"""
        print("\n=== RAG 시스템 상태 조회 테스트 ===")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/rag/")
            print(f"상태: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"성공: {data.get('success', False)}")
                print(f"메시지: {data.get('message', '')}")
                if data.get('data'):
                    print(f"초기화 상태: {data['data'].get('is_initialized', 'Unknown')}")
                    print(f"로드된 파일: {data['data'].get('loaded_files', [])}")
                    print(f"문서 수: {data['data'].get('document_count', 0)}")
            else:
                print(f"오류: {response.text}")
            
            return response.status_code == 200
        except Exception as e:
            print(f"RAG 상태 조회 실패: {e}")
            return False
    
    async def test_build_documents(self):
        """문서 구축 엔드포인트 테스트"""
        print("\n=== 문서 구축 테스트 ===")
        
        try:
            response = await self.client.post(f"{self.base_url}/api/rag/documents")
            print(f"상태: {response.status_code}")
            print(f"응답: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"문서 구축 실패: {e}")
            return False
    
    async def test_search(self, query: str = "RAG 시스템이란 무엇인가?"):
        """검색 엔드포인트 테스트"""
        print(f"\n=== 검색 테스트 (질문: {query}) ===")
        
        try:
            request_data = {
                "query": query,
                "max_results": 5,
                "threshold": 0.7
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/search",
                json=request_data
            )
            print(f"상태: {response.status_code}")
            print(f"응답: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"검색 실패: {e}")
            return False
    
    async def test_debug_documents(self):
        """디버그 문서 조회 엔드포인트 테스트"""
        print("\n=== 디버그 문서 조회 테스트 ===")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/search/debug/documents")
            print(f"상태: {response.status_code}")
            print(f"응답: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"디버그 문서 조회 실패: {e}")
            return False
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("RAG API 테스트 시작...\n")
        
        tests = [
            ("상태 확인", self.test_health_check),
            ("RAG 시스템 상태 조회", self.test_rag_status),
            ("문서 구축", self.test_build_documents),
            ("검색", self.test_search),
            ("디버그 문서 조회", self.test_debug_documents)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"테스트 '{test_name}' 실행 중 오류: {e}")
                results.append((test_name, False))
        
        # 테스트 결과 요약
        print("\n" + "="*50)
        print("테스트 결과 요약:")
        print("="*50)
        
        passed = 0
        for test_name, result in results:
            status = "[OK] 통과" if result else "[FAIL] 실패"
            print(f"{test_name:.<30} {status}")
            if result:
                passed += 1
        
        print(f"\n총계: {passed}/{len(results)} 테스트 통과")
        
        await self.client.aclose()
        return passed == len(results)


async def main():
    """메인 테스트 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG API 테스트")
    parser.add_argument("--url", default="http://localhost:8000",
                       help="API 서버 URL (기본값: http://localhost:8000)")
    parser.add_argument("--query", default="RAG 시스템이란 무엇인가?",
                       help="검색 테스트용 질문")
    
    args = parser.parse_args()
    
    tester = RAGAPITester(args.url)
    
    # 개별 테스트 실행 옵션
    if args.query:
        await tester.test_search(args.query)
    else:
        success = await tester.run_all_tests()
        if success:
            print("\n[SUCCESS] 모든 테스트 통과!")
        else:
            print("\n⚠️ 일부 테스트 실패")


if __name__ == "__main__":
    asyncio.run(main())
