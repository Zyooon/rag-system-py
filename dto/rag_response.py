"""
RAG 응답 DTO
Java 프로젝트의 RagResponse와 유사한 기능 제공
"""

from typing import Any, Optional, Dict
from pydantic import BaseModel


class SourceInfo(BaseModel):
    """출처 정보 모델"""
    filename: str
    chunk_index: int
    content_preview: str
    similarity_score: Optional[float] = None


class RagResponse(BaseModel):
    """RAG 시스템 표준 응답 모델"""
    success: bool
    message: str
    data: Optional[Any] = None
    sources: Optional[SourceInfo] = None
    timestamp: Optional[str] = None
    
    @classmethod
    def success_response(cls, message: str, data: Any = None, sources: SourceInfo = None) -> "RagResponse":
        """성공 응답 생성"""
        from datetime import datetime
        return cls(
            success=True,
            message=message,
            data=data,
            sources=sources,
            timestamp=datetime.now().isoformat()
        )
    
    @classmethod
    def error_response(cls, message: str) -> "RagResponse":
        """오류 응답 생성"""
        from datetime import datetime
        return cls(
            success=False,
            message=message,
            timestamp=datetime.now().isoformat()
        )


class RagRequest(BaseModel):
    """RAG 요청 모델"""
    query: str
    max_results: Optional[int] = 5
    threshold: Optional[float] = 0.7
