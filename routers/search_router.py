"""
검색 API 라우터
검색 엔드포인트 직접 구현
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dto.rag_response import RagResponse, RagRequest, SourceInfo
from services.search_service import SearchService
from repositories import RedisSearchRepository
from constants import MAP_KEY_ANSWER, MAP_KEY_SOURCES


router = APIRouter(prefix="/api/search", tags=["검색"])

# 서비스 인스턴스 직접 생성
search_service = SearchService()
redis_search_repository = RedisSearchRepository()


@router.post("", response_model=RagResponse)
async def ask_question(request: RagRequest):
    """사용자 질문에 대해 RAG를 통해 답변을 생성하는 엔드포인트"""
    try:
        result = await search_service.query(request)
        
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
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"검색 실패: {str(e)}"
        )