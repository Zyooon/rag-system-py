"""
검색 전용 컨트롤러
Java 프로젝트의 SearchController와 유사한 기능 제공
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dto.rag_response import RagResponse, RagRequest, SourceInfo
from services.search_service import SearchService
from repositories import RedisSearchRepository
from constants import MAP_KEY_ANSWER, MAP_KEY_SOURCES


router = APIRouter(prefix="/api/search", tags=["검색"])


class SearchController:
    """검색 전용 컨트롤러"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.redis_search_repository = RedisSearchRepository()
    
    async def query(self, request: RagRequest) -> Dict[str, Any]:
        """사용자 질문에 대해 RAG를 통해 답변 생성"""
        try:
            result = await self.search_service.search_and_answer_with_sources(request.query)
            
            answer = result.get(MAP_KEY_ANSWER, "답변을 찾을 수 없습니다.")
            sources = result.get(MAP_KEY_SOURCES)
            
            return {
                "answer": answer,
                "sources": sources.dict() if sources and hasattr(sources, 'dict') else sources,
                "query": request.query
            }
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"검색 실패: {str(e)}"
            )
    
    # 컨트롤러 인스턴스
search_controller = SearchController()


@router.post("", response_model=RagResponse)
async def ask_question(request: RagRequest):
    """사용자 질문에 대해 RAG를 통해 답변을 생성하는 엔드포인트"""
    result = await search_controller.query(request)
    
    sources = None
    if result.get("sources"):
        # SourceInfo 객체로 변환
        if isinstance(result["sources"], dict):
            sources = SourceInfo(**result["sources"])
        else:
            sources = result["sources"]
    
    return RagResponse.success_response(
        message=result["answer"],
        data=result,
        sources=sources
    )