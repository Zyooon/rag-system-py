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
            # 임베딩 모델 초기화
            self.embeddings = OllamaEmbeddings(
                model=self.embedding_model,
                base_url=self.base_url
            )
            
            print(f"임베딩 모델 초기화 완료: {self.embedding_model}")
            
        except Exception as e:
            print(f"[FAIL] Ollama 임베딩 모델 초기화 실패: {e}")
            print("해결 방안:")
            print(f"1. Ollama 서버가 실행 중인지 확인: {self.base_url}")
            print(f"2. 모델 설치: ollama pull {self.embedding_model}")
            print("3. 네트워크 연결 확인")
            self.embeddings = None
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        List of documents to vector conversion
        
        Args:
            texts: List of texts to convert to vectors
            
        Returns:
            Vector list
        """
        if not self.embeddings:
            # Raise exception instead of dummy vectors
            raise Exception(
                f"Cannot use embedding model '{self.embedding_model}'.\n"
                f"Ollama server: {self.base_url}\n"
                f"Solution: Run 'ollama pull {self.embedding_model}'"
            )
        
        if not texts:
            return []
        
        try:
            # Process all texts directly
            vectors = await asyncio.to_thread(
                self.embeddings.embed_documents,
                texts
            )
            return vectors
                
        except Exception as e:
            print(f"Document embedding failed: {e}")
            raise Exception(f"Error occurred during embedding processing: {e}")
        
    async def embed_query(self, text: str) -> List[float]:
        """
        Convert single text to vector
        
        Args:
            text: Text to convert to vector
            
        Returns:
            Vector
        """
        if not self.embeddings:
            # Raise exception instead of dummy vectors
            raise Exception(
                f"Cannot use embedding model '{self.embedding_model}'.\n"
                f"Ollama server: {self.base_url}\n"
                f"Solution: Run 'ollama pull {self.embedding_model}'"
            )
        
        try:
            # Async call
            vector = await asyncio.to_thread(
                self.embeddings.embed_query,
                text
            )
            return vector
        except Exception as e:
            print(f"Query embedding failed: {e}")
            raise Exception(f"Error occurred during query embedding processing: {e}")
