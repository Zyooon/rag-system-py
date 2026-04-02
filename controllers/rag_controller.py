"""
RAG 시스템 관리 컨트롤러
Java 프로젝트의 RagController와 유사한 기능 제공
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dto.rag_response import RagResponse
from services.rag_management_service import RagManagementService
from constants import (
    MAP_KEY_TOTAL_DELETED, MAP_KEY_RAG_KEYS_DELETED,
    MAP_KEY_EMBEDDING_KEYS_DELETED, MAP_KEY_MESSAGE,
    MSG_REDIS_VECTORSTORE_DELETE_COMPLETE, MSG_REDIS_VECTORSTORE_DELETE_FAILED,
    MSG_REDIS_VECTORSTORE_BUILD_FAILED, MSG_DOCUMENTS_RELOADED, MSG_DOCUMENT_RELOAD_FAILED
)


router = APIRouter(prefix="/api/rag", tags=["RAG 관리"])


class RagController:
    """RAG 시스템 관리 컨트롤러"""
    
    def __init__(self):
        self.rag_management_service = RagManagementService()
    
    async def clear_redis_vector_store(self) -> Dict[str, Any]:
        """Redis 벡터 저장소 초기화"""
        try:
            result = await self.rag_management_service.clear_store()
            
            message = MSG_REDIS_VECTORSTORE_DELETE_COMPLETE.format(
                result.get(MAP_KEY_TOTAL_DELETED, 0),
                result.get(MAP_KEY_RAG_KEYS_DELETED, 0),
                result.get(MAP_KEY_EMBEDDING_KEYS_DELETED, 0)
            )
            
            return result
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=MSG_REDIS_VECTORSTORE_DELETE_FAILED + str(e)
            )
    
    async def build_redis_vector_store(self) -> Dict[str, Any]:
        """Redis 벡터 저장소 구축"""
        try:
            result = await self.rag_management_service.save_documents_to_redis()
            message = result.get(MAP_KEY_MESSAGE, "문서 저장 완료")
            
            return result
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=MSG_REDIS_VECTORSTORE_BUILD_FAILED + str(e)
            )
    
    async def reload_documents(self) -> Dict[str, Any]:
        """문서 다시 로드"""
        try:
            # 벡터 저장소 초기화 후 다시 로드
            clear_result = await self.rag_management_service.clear_store()
            await self.rag_management_service.initialize_documents()
            
            message = MSG_DOCUMENTS_RELOADED.format(
                clear_result.get(MAP_KEY_TOTAL_DELETED, 0)
            )
            
            return clear_result
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=MSG_DOCUMENT_RELOAD_FAILED + str(e)
            )
    
    async def get_documents_list(self) -> List[Dict[str, Any]]:
        """저장된 문서 목록 조회"""
        try:
            return await self.rag_management_service.get_documents_list()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"문서 목록 조회 실패: {str(e)}"
            )


# 컨트롤러 인스턴스
rag_controller = RagController()


@router.get("/documents")
async def get_documents_list():
    """저장된 문서 목록 조회 엔드포인트"""
    try:
        document_list = await rag_controller.get_documents_list()
        return RagResponse.success_response(f"{len(document_list)}개 파일의 문서를 찾았습니다", {
            "total_count": len(document_list),
            "documents": document_list
        })
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"문서 목록 조회 실패: {str(e)}"
        )


@router.delete("/documents")
async def clear_documents():
    """문서 삭제 엔드포인트"""
    result = await rag_controller.clear_redis_vector_store()
    message = MSG_REDIS_VECTORSTORE_DELETE_COMPLETE.format(
        result.get(MAP_KEY_TOTAL_DELETED, 0),
        result.get(MAP_KEY_RAG_KEYS_DELETED, 0),
        result.get(MAP_KEY_EMBEDDING_KEYS_DELETED, 0)
    )
    return RagResponse.success_response(message, result)


@router.post("/documents")
async def build_documents():
    """문서 저장 엔드포인트"""
    result = await rag_controller.build_redis_vector_store()
    message = result.get(MAP_KEY_MESSAGE, "문서 저장 완료")
    return RagResponse.success_response(message, result)


@router.put("/documents/reload")
async def reload_documents():
    """문서 재로드 엔드포인트"""
    result = await rag_controller.reload_documents()
    message = MSG_DOCUMENTS_RELOADED.format(
        result.get(MAP_KEY_TOTAL_DELETED, 0)
    )
    return RagResponse.success_response(message, result)
