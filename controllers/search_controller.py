"""
검색 전용 컨트롤러
Java 프로젝트의 SearchController와 유사한 기능 제공
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from dto import RagResponse, RagRequest, SourceInfo
from services import SearchService
from constants import MAP_KEY_ANSWER, MAP_KEY_SOURCES


router = APIRouter(prefix="/api/search", tags=["검색"])


class SearchController:
    """검색 전용 컨트롤러"""
    
    def __init__(self):
        self.search_service = SearchService()
    
    async def query(self, request: RagRequest) -> Dict[str, Any]:
        """사용자 질문에 대해 RAG를 통해 답변 생성"""
        try:
            result = await self.search_service.search_and_answer_with_sources(request.query)
            
            answer = result.get(MAP_KEY_ANSWER, "답변을 찾을 수 없습니다.")
            sources = result.get(MAP_KEY_SOURCES)
            
            return {
                "answer": answer,
                "sources": sources.dict() if sources else None,
                "query": request.query
            }
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"검색 실패: {str(e)}"
            )
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """Redis에 저장된 모든 문서를 조회하는 디버깅 엔드포인트"""
        try:
            return await self.search_service.get_all_documents()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"문서 조회 실패: {str(e)}"
            )
    
    # 컨트롤러 인스턴스
search_controller = SearchController()


@router.post("", response_model=RagResponse)
async def ask_question(request: RagRequest):
    """사용자 질문에 대해 RAG를 통해 답변을 생성하는 엔드포인트"""
    result = await search_controller.query(request)
    
    sources = None
    if result.get("sources"):
        sources = SourceInfo(**result["sources"])
    
    return RagResponse.success_response(
        message=result["answer"],
        data=result,
        sources=sources
    )


@router.get("/debug/documents", response_model=List[Dict[str, Any]])
async def get_all_documents_debug():
    """Redis에 저장된 모든 문서를 조회하는 디버깅 엔드포인트"""
    documents = await search_controller.get_all_documents()
    return documents
