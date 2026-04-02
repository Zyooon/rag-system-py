"""
벡터 저장소 추상화
Java 프로젝트의 VectorStore와 유사한 기능 제공
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class VectorStoreRepository(ABC):
    """벡터 저장소 추상 클래스"""
    
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        문서들을 벡터 저장소에 추가
        
        Args:
            documents: 추가할 문서 리스트
            
        Returns:
            성공 여부
        """
        pass
    
    @abstractmethod
    async def similarity_search(self, query: str, k: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        유사도 기반 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 최대 결과 수
            threshold: 유사도 임계값
            
        Returns:
            유사한 문서 리스트
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        벡터 저장소 초기화
        
        Returns:
            성공 여부
        """
        pass
    
    @abstractmethod
    async def get_document_count(self) -> int:
        """
        저장된 문서 수 반환
        
        Returns:
            문서 수
        """
        pass
