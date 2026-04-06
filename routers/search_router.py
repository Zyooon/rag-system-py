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

from dto.rag_response import RagResponse, RagRequest, SourceInfo, FilteredSearchRequest, SearchStats
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
async def search_with_filters(request: FilteredSearchRequest):
    """필터링 조건으로 검색하는 엔드포인트 (Pydantic 검증 강화)"""
    try:
        import time
        start_time = time.time()
        
        # Pydantic 모델에서 필터링 조건 추출
        filters = request.filters.model_dump(exclude_none=True) if request.filters else None
        
        result = await search_service.search_and_answer_with_sources(request.query, filters)
        
        # 검색 통계 생성
        search_time = time.time() - start_time
        stats = SearchStats(
            total_results=len(result.get("documents", [])),
            filtered_results=len(result.get("documents", [])),
            search_time=search_time,
            avg_similarity=0.0  # TODO: 계산 로직 추가
        )
        
        sources = None
        if result.get("sources"):
            if isinstance(result["sources"], dict):
                sources = SourceInfo(**result["sources"])
            else:
                sources = result["sources"]
        
        return RagResponse.success_response(
            message=f"필터링 검색 완료: {filters}",
            data={**result, "stats": stats.model_dump()},
            sources=sources
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"필터링 검색 실패: {str(e)}"
        )


@router.get("/filters")
async def get_available_filters():
    """사용 가능한 필터링 옵션 반환 (Pydantic 모델 기반)"""
    try:
        from dto.rag_response import FilterRequest
        
        # Pydantic 모델에서 필드 정보 추출
        filter_schema = FilterRequest.model_json_schema()
        
        return RagResponse.success_response(
            "필터링 옵션",
            {
                "available_filters": filter_schema.get("properties", {}),
                "schema": filter_schema
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"필터링 옵션 조회 실패: {str(e)}"
        )


@router.post("/validate", response_model=RagResponse)
async def validate_search_request(request: RagRequest):
    """검색 요청 유효성 검증 엔드포인트"""
    try:
        # Pydantic 모델이 자동으로 검증 수행
        validation_result = {
            "valid": True,
            "query": request.query,
            "max_results": request.max_results,
            "threshold": request.threshold,
            "message": "검색 요청이 유효합니다"
        }
        
        return RagResponse.success_response(
            "검색 요청 검증 완료",
            data=validation_result
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"검색 요청 검증 실패: {str(e)}"
        )