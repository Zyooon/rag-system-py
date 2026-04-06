"""
검색 API 라우터
검색 엔드포인트 직접 구현
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
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
async def ask_question(request: RagRequest, filters: Optional[Dict[str, Any]] = None):
    """사용자 질문에 대해 RAG를 통해 답변을 생성하는 엔드포인트 (필터링 지원)"""
    try:
        result = await search_service.search_and_answer_with_sources(request.query, filters)
        
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


@router.post("/filtered", response_model=RagResponse)
async def search_with_filters(request: RagRequest, filters: Dict[str, Any]):
    """필터링 조건으로 검색하는 엔드포인트"""
    try:
        result = await search_service.search_and_answer_with_sources(request.query, filters)
        
        sources = None
        if result.get("sources"):
            if isinstance(result["sources"], dict):
                sources = SourceInfo(**result["sources"])
            else:
                sources = result["sources"]
        
        return RagResponse.success_response(
            message=f"필터링 검색 완료: {filters}",
            data=result,
            sources=sources
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"필터링 검색 실패: {str(e)}"
        )


@router.get("/filters")
async def get_available_filters():
    """사용 가능한 필터링 옵션 반환"""
    return RagResponse.success_response(
        "필터링 옵션",
        {
            "available_filters": {
                "filename": {
                    "type": "string or list",
                    "description": "파일명으로 필터링",
                    "example": "document.txt or ['doc1.txt', 'doc2.txt']"
                },
                "file_type": {
                    "type": "string or list", 
                    "description": "파일 타입으로 필터링",
                    "example": "pdf or ['txt', 'md']"
                },
                "chunk_type": {
                    "type": "string or list",
                    "description": "청크 타입으로 필터링",
                    "example": "semantic or ['semantic', 'fallback']"
                },
                "date_range": {
                    "type": "object",
                    "description": "기간으로 필터링",
                    "example": {"start": "2024-01-01", "end": "2024-12-31"}
                },
                "min_score": {
                    "type": "number",
                    "description": "최소 유사도 점수",
                    "example": 0.5
                }
            }
        }
    )