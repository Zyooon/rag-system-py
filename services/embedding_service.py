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
            # Ollama 서버 연결 테스트
            import httpx
            
            # 서버 상태 확인
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            if response.status_code != 200:
                raise Exception(f"Ollama 서버 응답 오류: {response.status_code}")
            
            # 모델 목록에서 해당 모델 확인
            models_data = response.json()
            available_models = [model.get('name', '') for model in models_data.get('models', [])]
            
            if self.embedding_model not in available_models:
                print(f"경고: Ollama에 '{self.embedding_model}' 모델이 없습니다.")
                print(f"사용 가능한 모델: {', '.join(available_models)}")
                print(f"'ollama pull {self.embedding_model}' 명령어로 모델을 설치하세요.")
                self.embeddings = None
                return
            
            # 임베딩 모델 초기화
            self.embeddings = OllamaEmbeddings(
                base_url=self.base_url,
                model=self.embedding_model
            )
            
            # 실제 임베딩 테스트
            test_vector = self.embeddings.embed_query("test")
            if not test_vector or all(v == 0 for v in test_vector):
                raise Exception("임베딩 결과가 유효하지 않음")
            
            print(f"Ollama 임베딩 모델 초기화 완료: {self.embedding_model} ({self.base_url})")
            print(f"벡터 차원: {len(test_vector)}")
            
        except Exception as e:
            print(f"Ollama 임베딩 모델 초기화 실패: {e}")
            print("해결 방안:")
            print(f"1. Ollama 서버가 실행 중인지 확인: {self.base_url}")
            print(f"2. 모델 설치: ollama pull {self.embedding_model}")
            print("3. 네트워크 연결 확인")
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
            # 더미 벡터 대신 예외 발생
            raise Exception(
                f"임베딩 모델 '{self.embedding_model}'을 사용할 수 없습니다.\n"
                f"Ollama 서버: {self.base_url}\n"
                f"해결 방안: 'ollama pull {self.embedding_model}' 실행"
            )
        
        try:
            # 비동기 호출을 위해 asyncio.to_thread 사용
            vectors = await asyncio.to_thread(
                self.embeddings.embed_documents,
                texts
            )
            return vectors
        except Exception as e:
            print(f"문서 임베딩 실패: {e}")
            raise Exception(f"임베딩 처리 중 오류 발생: {e}")
    
    async def embed_query(self, text: str) -> List[float]:
        """
        단일 텍스트를 벡터로 변환
        
        Args:
            text: 벡터로 변환할 텍스트
            
        Returns:
            벡터
        """
        if not self.embeddings:
            # 더미 벡터 대신 예외 발생
            raise Exception(
                f"임베딩 모델 '{self.embedding_model}'을 사용할 수 없습니다.\n"
                f"Ollama 서버: {self.base_url}\n"
                f"해결 방안: 'ollama pull {self.embedding_model}' 실행"
            )
        
        try:
            # 비동기 호출
            vector = await asyncio.to_thread(
                self.embeddings.embed_query,
                text
            )
            return vector
        except Exception as e:
            print(f"쿼리 임베딩 실패: {e}")
            raise Exception(f"쿼리 임베딩 처리 중 오류 발생: {e}")
    
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
