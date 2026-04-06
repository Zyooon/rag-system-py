"""
RAG 시스템 완전 테스트 스크립트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from services import RagManagementService, SearchService
from dto import RagRequest


class RAGSystemTester:
    """RAG 시스템 통합 테스터"""
    
    def __init__(self):
        self.rag_service = RagManagementService()
        self.search_service = SearchService()
    
    async def test_complete_pipeline(self):
        """전체 RAG 파이프라인 테스트"""
        print("=== RAG 시스템 완전 테스트 ===\n")
        
        # 1. 문서 저장 테스트
        print("1. 문서 저장 테스트")
        save_result = await self.test_document_saving()
        
        # 2. 시스템 상태 확인
        print("\n2. 시스템 상태 확인")
        status = await self.test_system_status()
        
        # 3. 검색 테스트
        print("\n3. 검색 테스트")
        search_results = await self.test_search()
        
        # 4. 문서 삭제 테스트
        print("\n4. 문서 삭제 테스트")
        clear_result = await self.test_document_clearing()
        
        # 5. 최종 상태 확인
        print("\n5. 최종 상태 확인")
        final_status = await self.test_system_status()
        
        # 테스트 결과 요약
        self.print_test_summary(save_result, status, search_results, clear_result, final_status)
    
    async def test_document_saving(self):
        """문서 저장 테스트"""
        try:
            result = await self.rag_service.save_documents_to_redis()
            print(f"문서 저장 결과: {result}")
            return result
        except Exception as e:
            print(f"문서 저장 실패: {e}")
            return {}
    
    async def test_system_status(self):
        """시스템 상태 확인 테스트"""
        try:
            status = await self.rag_service.get_status_with_files()
            print(f"시스템 상태:")
            print(f"  초기화 여부: {status.get('is_initialized', False)}")
            print(f"  로드된 파일: {status.get('loaded_files', [])}")
            print(f"  문서 수: {status.get('document_count', 0)}")
            print(f"  전체 수: {status.get('total_count', 0)}")
            return status
        except Exception as e:
            print(f"상태 확인 실패: {e}")
            return {}
    
    async def test_search(self):
        """검색 테스트"""
        test_queries = [
            "RAG 시스템이란 무엇인가?",
            "문서 처리는 어떻게 되나요?",
            "벡터 저장소의 역할은 무엇인가?"
        ]
        
        search_results = []
        
        for query in test_queries:
            try:
                print(f"\n질문: {query}")
                result = await self.search_service.search_and_answer_with_sources(query)
                
                answer = result.get('answer', '답변 없음')
                sources = result.get('sources')
                
                print(f"답변: {answer}")
                if sources and sources.filename != "unknown":
                    print(f"출처: {sources.filename}")
                    print(f"유사도: {sources.similarity_score}")
                
                search_results.append({
                    'query': query,
                    'answer': answer,
                    'sources': sources
                })
                
            except Exception as e:
                print(f"검색 실패: {e}")
                search_results.append({
                    'query': query,
                    'answer': f'오류: {e}',
                    'sources': None
                })
        
        return search_results
    
    async def test_document_clearing(self):
        """문서 삭제 테스트"""
        try:
            result = await self.rag_service.clear_store()
            print(f"문서 삭제 결과: {result}")
            return result
        except Exception as e:
            print(f"문서 삭제 실패: {e}")
            return {}
    
    def print_test_summary(self, save_result, status, search_results, clear_result, final_status):
        """테스트 결과 요약"""
        print("\n" + "="*60)
        print("테스트 결과 요약")
        print("="*60)
        
        # 문서 저장 결과
        saved_count = save_result.get('saved_count', 0)
        print(f"문서 저장: {'[OK] 성공' if saved_count > 0 else '[FAIL] 실패'} ({saved_count}개)")
        
        # 시스템 상태
        is_initialized = status.get('is_initialized', False)
        print(f"시스템 초기화: {'[OK] 완료' if is_initialized else '[FAIL] 미완료'}")
        
        # 검색 결과
        successful_searches = sum(1 for r in search_results if '오류' not in r.get('answer', ''))
        print(f"검색 기능: {'[OK] 정상' if successful_searches > 0 else '[FAIL] 실패'} ({successful_searches}/{len(search_results)} 성공)")
        
        # 문서 삭제 결과
        total_deleted = clear_result.get('total_deleted', 0)
        print(f"문서 삭제: {'[OK] 성공' if total_deleted >= 0 else '[FAIL] 실패'} ({total_deleted}개 삭제)")
        
        # 최종 상태
        final_initialized = final_status.get('is_initialized', False)
        print(f"최종 상태: {'[OK] 정상' if not final_initialized else '⚠️ 초기화됨'}")
        
        print("="*60)


async def main():
    """메인 테스트 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG 시스템 완전 테스트")
    parser.add_argument("--step", choices=["save", "status", "search", "clear"], 
                       help="특정 단계만 테스트")
    
    args = parser.parse_args()
    
    tester = RAGSystemTester()
    
    if args.step == "save":
        await tester.test_document_saving()
    elif args.step == "status":
        await tester.test_system_status()
    elif args.step == "search":
        await tester.test_search()
    elif args.step == "clear":
        await tester.test_document_clearing()
    else:
        await tester.test_complete_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
