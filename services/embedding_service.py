"""
임베딩 서비스
Ollama 임베딩 모델 연결 및 벡터 생성
"""

import asyncio
from typing import List, Optional, Dict, Any
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings

from config import settings


class EmbeddingService(Embeddings):
    """임베딩 서비스 클래스"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.embedding_model = settings.ollama_embedding_model
        self.embeddings: Optional[OllamaEmbeddings] = None
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Ollama 임베딩 모델 초기화"""
        try:
            self.embeddings = OllamaEmbeddings(
                base_url=self.base_url,
                model=self.embedding_model
            )
            print(f"Ollama 임베딩 모델 초기화 완료: {self.embedding_model} ({self.base_url})")
        except Exception as e:
            print(f"Ollama 임베딩 모델 초기화 실패: {e}")
            self.embeddings = None
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        문서 리스트를 벡터로 변환
        
        Args:
            texts: 벡터로 변환할 텍스트 리스트
            
        Returns:
            벡터 리스트
        """
        if not self.embeddings:
            # 임시로 더미 벡터 반환 (실제로는 오류 처리 필요)
            print("경고: 임베딩 모델이 초기화되지 않아 더미 벡터를 반환합니다")
            return [[0.0] * 768 for _ in texts]  # 768차원 더미 벡터
        
        try:
            # 비동기 호출을 위해 asyncio.to_thread 사용
            vectors = await asyncio.to_thread(
                self.embeddings.embed_documents,
                texts
            )
            return vectors
        except Exception as e:
            print(f"문서 임베딩 실패: {e}")
            # 오류 시 더미 벡터 반환
            return [[0.0] * 768 for _ in texts]
    
    async def embed_query(self, text: str) -> List[float]:
        """
        단일 텍스트를 벡터로 변환
        
        Args:
            text: 벡터로 변환할 텍스트
            
        Returns:
            벡터
        """
        if not self.embeddings:
            print("경고: 임베딩 모델이 초기화되지 않아 더미 벡터를 반환합니다")
            return [0.0] * 768  # 768차원 더미 벡터
        
        try:
            # 비동기 호출
            vector = await asyncio.to_thread(
                self.embeddings.embed_query,
                text
            )
            return vector
        except Exception as e:
            print(f"쿼리 임베딩 실패: {e}")
            # 오류 시 더미 벡터 반환
            return [0.0] * 768
    
    async def health_check(self) -> Dict[str, Any]:
        """
        임베딩 서비스 상태 확인
        
        Returns:
            상태 정보
        """
        try:
            if not self.embeddings:
                return {
                    "status": "unhealthy",
                    "error": "임베딩 모델이 초기화되지 않음",
                    "model": self.embedding_model,
                    "base_url": self.base_url
                }
            
            # 간단한 테스트 텍스트로 임베딩 확인
            test_vector = await self.embed_query("테스트")
            
            return {
                "status": "healthy",
                "model": self.embedding_model,
                "base_url": self.base_url,
                "vector_dimension": len(test_vector),
                "test_vector_preview": test_vector[:5]  # 처음 5차원만 표시
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.embedding_model,
                "base_url": self.base_url
            }
    
    def is_available(self) -> bool:
        """
        임베딩 서비스 사용 가능 여부 확인
        
        Returns:
            사용 가능 여부
        """
        return self.embeddings is not None
    
    def get_model_info(self) -> Dict[str, str]:
        """
        모델 정보 반환
        
        Returns:
            모델 정보
        """
        return {
            "model_name": self.embedding_model,
            "base_url": self.base_url,
            "provider": "Ollama",
            "status": "available" if self.is_available() else "unavailable"
        }
    
    async def get_embedding_dimension(self) -> int:
        """
        임베딩 차원 수 반환
        
        Returns:
            임베딩 차원 수
        """
        try:
            test_vector = await self.embed_query("test")
            return len(test_vector)
        except Exception:
            return 768  # 기본값
