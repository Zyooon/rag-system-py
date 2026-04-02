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
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """Redis에 저장된 모든 문서를 조회하는 디버깅 엔드포인트"""
        try:
            return await self.redis_search_repository.get_all_documents()
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


@router.get("/health")
async def check_embedding_health():
    """임베딩 서비스 상태 확인 엔드포인트"""
    try:
        from services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        health_status = await embedding_service.health_check()
        
        return {
            "status": "success",
            "embedding_health": health_status
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"임베딩 서비스 상태 확인 실패: {str(e)}"
        }


@router.get("/documents", response_model=List[Dict[str, Any]])
async def get_all_documents():
    """Redis에 저장된 모든 문서를 조회하는 엔드포인트"""
    documents = await search_controller.get_all_documents()
    return documents


@router.get("/documents/keys")
async def get_document_keys():
    """Redis에 저장된 모든 문서 키를 조회하는 엔드포인트"""
    try:
        keys = await search_controller.redis_search_repository.get_all_document_keys()
        return {"keys": keys, "count": len(keys)}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"키 조회 실패: {str(e)}"
        )


@router.get("/documents/count")
async def get_document_count():
    """저장된 문서 개수를 조회하는 엔드포인트"""
    try:
        count = await search_controller.redis_search_repository.get_document_count()
        return {"count": count}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"문서 개수 조회 실패: {str(e)}"
        )


@router.get("/documents/summary")
async def get_document_summary():
    """문서 저장소 요약 정보를 조회하는 엔드포인트"""
    try:
        summary = await search_controller.redis_search_repository.get_document_summary()
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"요약 정보 조회 실패: {str(e)}"
        )


@router.get("/debug/redis-info")
async def debug_redis_info():
    """Redis 디버깅 정보 조회 엔드포인트"""
    try:
        # Redis 연결 상태 확인
        health = await search_controller.redis_search_repository.health_check()
        
        # 모든 키 조회 (다양한 패턴으로)
        all_keys_info = {}
        
        # rag:documents:* 패턴
        docs_keys = await search_controller.redis_search_repository.get_all_document_keys()
        all_keys_info["rag_documents_keys"] = {
            "pattern": "rag:documents:*",
            "count": len(docs_keys),
            "keys": docs_keys[:5]  # 처음 5개만 표시
        }
        
        # rag:* 패턴으로 모든 키 조회
        await search_controller.redis_search_repository._ensure_initialized()
        if search_controller.redis_search_repository.redis_client:
            try:
                rag_all_keys = await search_controller.redis_search_repository.redis_client.keys("rag:*")
                all_keys_info["rag_all_keys"] = {
                    "pattern": "rag:*",
                    "count": len(rag_all_keys),
                    "keys": rag_all_keys[:10]  # 처음 10개만 표시
                }
            except Exception as e:
                all_keys_info["rag_all_keys"] = {"error": str(e)}
        
        # 실제 문서 내용 샘플 조회
        sample_docs = []
        if docs_keys:
            for key in docs_keys[:3]:  # 처음 3개 문서만
                doc = await search_controller.redis_search_repository.get_document(key)
                if doc:
                    sample_docs.append({
                        "key": key,
                        "text_preview": doc.get("text", "")[:100] + "..." if len(doc.get("text", "")) > 100 else doc.get("text", ""),
                        "metadata": doc.get("metadata", {})
                    })
        
        all_keys_info["sample_documents"] = sample_docs
        
        return {
            "health": health,
            "keys_info": all_keys_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"디버깅 정보 조회 실패: {str(e)}"
        )


@router.get("/health/repository")
async def check_repository_health():
    """검색 리포지토리 상태 확인 엔드포인트"""
    try:
        health = await search_controller.redis_search_repository.health_check()
        return health
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"리포지토리 상태 확인 실패: {str(e)}"
        )
