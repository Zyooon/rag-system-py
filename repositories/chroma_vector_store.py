"""
Chroma 벡터 저장소 구현
Java 프로젝트의 VectorStore와 유사한 기능 제공
"""

import asyncio
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from config import settings
from .vector_store_repository import VectorStoreRepository


class ChromaVectorStore(VectorStoreRepository):
    """Chroma 벡터 저장소 구현"""
    
    def __init__(self):
        self.collection_name = settings.chroma_collection_name
        self.persist_directory = settings.chroma_path
        self.embedding_service = None
        
        # ChromaDB 초기화
        self._initialize_chroma()
    
    def _set_embedding_service(self, embedding_service):
        """임베딩 서비스 설정 (순환 임포트 방지)"""
        self.embedding_service = embedding_service
        # ChromaDB 재초기화
        self._initialize_chroma()
    
    def _initialize_chroma(self):
        """ChromaDB 초기화"""
        try:
            # 임베딩 서비스가 없으면 더미 함수 사용
            if self.embedding_service is None:
                # 더미 임베딩 함수
                def dummy_embedding(texts):
                    if isinstance(texts, str):
                        return [0.0] * 768
                    return [[0.0] * 768 for _ in texts]
                
                embedding_function = type('DummyEmbedding', (), {
                    'embed_documents': dummy_embedding,
                    'embed_query': dummy_embedding
                })()
            else:
                embedding_function = self.embedding_service
            
            # 컬렉션이 존재하면 로드, 아니면 새로 생성
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                persist_directory=str(self.persist_directory),
                embedding_function=embedding_function
            )
            
            print(f"ChromaDB 초기화 완료: {self.collection_name}")
            print(f"저장 경로: {self.persist_directory}")
            
        except Exception as e:
            print(f"ChromaDB 초기화 실패: {e}")
            raise
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        문서들을 벡터 저장소에 추가
        
        Args:
            documents: 추가할 문서 리스트
            
        Returns:
            성공 여부
        """
        try:
            # LangChain Document 객체로 변환
            langchain_docs = []
            
            for doc in documents:
                text = doc.get("text", "")
                metadata = doc.get("metadata", {})
                
                if text.strip():
                    langchain_doc = Document(
                        page_content=text,
                        metadata=metadata
                    )
                    langchain_docs.append(langchain_doc)
            
            if langchain_docs:
                # 벡터 저장소에 문서 추가
                await asyncio.to_thread(self.vector_store.add_documents, langchain_docs)
                
                # 영구 저장
                await asyncio.to_thread(self.vector_store.persist)
                
                print(f"ChromaDB에 {len(langchain_docs)}개 문서 추가됨")
                return True
            else:
                print("추가할 문서가 없습니다")
                return False
                
        except Exception as e:
            print(f"문서 추가 실패: {e}")
            return False
    
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
        try:
            # TODO: 실제 임베딩 모델로 쿼리 벡터화
            # query_embedding = await self.embeddings.embed_query(query)
            
            # 임시 구현 - 텍스트 기반 검색
            results = await asyncio.to_thread(
                self.vector_store.similarity_search_with_score,
                query,
                k=k
            )
            
            # 임계값 필터링
            filtered_results = []
            for doc, score in results:
                if score >= threshold:
                    filtered_results.append({
                        "text": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": float(score),
                        "id": str(uuid.uuid4())
                    })
            
            print(f"유사도 검색: {query} -> {len(filtered_results)}개 결과")
            return filtered_results
            
        except Exception as e:
            print(f"유사도 검색 실패: {e}")
            return []
    
    async def clear(self) -> bool:
        """
        벡터 저장소 초기화
        
        Returns:
            성공 여부
        """
        try:
            # 모든 문서 삭제
            await asyncio.to_thread(self.vector_store.delete_collection)
            
            # 새로운 컬렉션 생성
            await asyncio.to_thread(self._initialize_chroma)
            
            print("벡터 저장소 초기화 완료")
            return True
            
        except Exception as e:
            print(f"벡터 저장소 초기화 실패: {e}")
            return False
    
    async def get_document_count(self) -> int:
        """
        저장된 문서 수 반환
        
        Returns:
            문서 수
        """
        try:
            count = await asyncio.to_thread(lambda: len(self.vector_store.get()))
            return count
        except Exception as e:
            print(f"문서 수 조회 실패: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """
        벡터 저장소 상태 확인
        
        Returns:
            상태 정보
        """
        try:
            count = await self.get_document_count()
            
            return {
                "status": "healthy",
                "collection_name": self.collection_name,
                "persist_directory": str(self.persist_directory),
                "document_count": count,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
