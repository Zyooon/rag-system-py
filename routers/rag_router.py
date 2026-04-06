"""
RAG 시스템 관리 API 라우터
문서 관리 엔드포인트 직접 구현
BackgroundTasks로 비동기 처리 지원
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import sys
import os
import asyncio

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dto.rag_response import RagResponse
from services.rag_management_service import RagManagementService
from constants import (
    MAP_KEY_TOTAL_DELETED, MAP_KEY_RAG_KEYS_DELETED,
    MAP_KEY_EMBEDDING_KEYS_DELETED, MAP_KEY_MESSAGE,
    MSG_REDIS_VECTORSTORE_DELETE_COMPLETE, MSG_REDIS_VECTORSTORE_DELETE_FAILED,
    MSG_REDIS_VECTORSTORE_BUILD_FAILED, MSG_DOCUMENTS_RELOADED, MSG_DOCUMENT_RELOAD_FAILED,
    MSG_DOCUMENT_PROCESSING_STARTED
)


router = APIRouter(prefix="/api/rag", tags=["RAG 관리"])

# 서비스 인스턴스 직접 생성
rag_management_service = RagManagementService()


@router.get("/documents")
async def get_documents_list():
    """저장된 문서 목록 조회 엔드포인트"""
    try:
        document_list = await rag_management_service.get_documents_list()
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
    try:
        result = await rag_management_service.clear_store()
        message = MSG_REDIS_VECTORSTORE_DELETE_COMPLETE.format(
            result.get(MAP_KEY_TOTAL_DELETED, 0),
            result.get(MAP_KEY_RAG_KEYS_DELETED, 0),
            result.get(MAP_KEY_EMBEDDING_KEYS_DELETED, 0)
        )
        return RagResponse.success_response(message, result)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=MSG_REDIS_VECTORSTORE_DELETE_FAILED + str(e)
        )


@router.post("/documents")
async def build_documents(background_tasks: BackgroundTasks):
    """문서 저장 엔드포인트 (백그라운드 처리)"""
    try:
        # 백그라운드 작업 추가
        background_tasks.add_task(
            rag_management_service.save_documents_to_redis
        )
        
        # 즉시 응답 반환
        return RagResponse.success_response(
            MSG_DOCUMENT_PROCESSING_STARTED,
            {
                "status": "processing",
                "message": "문서 처리가 백그라운드에서 시작되었습니다."
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=MSG_REDIS_VECTORSTORE_BUILD_FAILED + str(e)
        )


@router.post("/documents/sync")
async def build_documents_sync():
    """문서 저장 엔드포인트 (동기 처리 - 테스트용)"""
    try:
        result = await rag_management_service.save_documents_to_redis()
        message = result.get(MAP_KEY_MESSAGE, "문서 저장 완료")
        return RagResponse.success_response(message, result)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=MSG_REDIS_VECTORSTORE_BUILD_FAILED + str(e)
        )


@router.put("/documents/reload")
async def reload_documents(background_tasks: BackgroundTasks):
    """문서 재로드 엔드포인트 (백그라운드 처리)"""
    try:
        # 백그라운드 작업 추가
        background_tasks.add_task(
            _reload_documents_background
        )
        
        # 즉시 응답 반환
        return RagResponse.success_response(
            MSG_DOCUMENT_PROCESSING_STARTED,
            {
                "status": "processing",
                "message": "문서 재로드가 백그라운드에서 시작되었습니다."
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=MSG_DOCUMENT_RELOAD_FAILED + str(e)
        )


@router.put("/documents/reload/sync")
async def reload_documents_sync():
    """문서 재로드 엔드포인트 (동기 처리 - 테스트용)"""
    try:
        clear_result = await rag_management_service.clear_store()
        await rag_management_service.initialize_documents()
        
        message = MSG_DOCUMENTS_RELOADED.format(
            clear_result.get(MAP_KEY_TOTAL_DELETED, 0)
        )
        
        return RagResponse.success_response(message, clear_result)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=MSG_DOCUMENT_RELOAD_FAILED + str(e)
        )


async def _reload_documents_background():
    """백그라운드에서 문서 재로드 처리"""
    try:
        clear_result = await rag_management_service.clear_store()
        await rag_management_service.initialize_documents()
        print(f"✅ 백그라운드 문서 재로드 완료: {clear_result.get(MAP_KEY_TOTAL_DELETED, 0)}개 파일 삭제 후 재로드")
    except Exception as e:
        print(f"❌ 백그라운드 문서 재로드 실패: {e}")


@router.get("/status")
async def get_processing_status():
    """처리 상태 확인 엔드포인트"""
    try:
        # 현재 처리 상태 확인 (간단한 구현)
        is_initialized = await rag_management_service.is_initialized_check()
        
        return RagResponse.success_response(
            "상태 확인 완료",
            {
                "initialized": is_initialized,
                "status": "ready" if is_initialized else "processing",
                "message": "시스템 준비 완료" if is_initialized else "백그라운드 처리 중"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"상태 확인 실패: {str(e)}"
        )
