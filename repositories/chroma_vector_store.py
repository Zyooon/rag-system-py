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
        """임베딩 서비스 설정 (순환 임포트 방지 및 동기 래퍼 생성)"""
        self.embedding_service = embedding_service
        
        # 동기 임베딩 래퍼 생성
        if embedding_service:
            import asyncio
            
            class SyncEmbedding:
                def __init__(self, async_service):
                    self.async_service = async_service
                
                def embed_documents(self, texts):
                    """동기 문서 임베딩 래퍼"""
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # 이벤트 루프가 실행 중이면 스레드 풀 사용
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(self._run_embed_documents, texts)
                                return future.result()
                        else:
                            # 루프가 없으면 직접 실행
                            return self._run_embed_documents(texts)
                    except Exception as e:
                        print(f"동기 임베딩 실패: {e}")
                        # 실패 시 더미 벡터 반환
                        return [[0.0] * 768 for _ in texts]
                
                def _run_embed_documents(self, texts):
                    """embed_documents를 동기적으로 실행"""
                    return asyncio.run(self.async_service.embed_documents(texts))
                
                def embed_query(self, text):
                    """동기 쿼리 임베딩 래퍼"""
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(asyncio.run, self.async_service.embed_query(text))
                                return future.result()
                        else:
                            return asyncio.run(self.async_service.embed_query(text))
                    except Exception as e:
                        print(f"동기 쿼리 임베딩 실패: {e}")
                        return [0.0] * 768
            
            embedding_function = SyncEmbedding(embedding_service)
        else:
            embedding_function = None
        
        # ChromaDB 재초기화
        self._initialize_chroma_with_function(embedding_function)
    
    def _initialize_chroma_with_function(self, embedding_function):
        """임베딩 함수와 함께 ChromaDB 초기화"""
        try:
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
    
    def _initialize_chroma(self):
        """ChromaDB 초기화"""
        try:
            # 임베딩 서비스가 없으면 더미 함수 사용
            if self.embedding_service is None:
                # 더미 임베딩 함수
                def dummy_embedding(*args, **kwargs):
                    # 첫 번째 인자가 텍스트 리스트
                    if args:
                        texts = args[0]
                        if isinstance(texts, str):
                            return [0.0] * 768
                        elif isinstance(texts, list):
                            return [[0.0] * 768 for _ in texts]
                    # 기본값: 빈 리스트에 대한 더미 임베딩
                    return [[0.0] * 768]
                
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
    
    async def similarity_search(self, query: str, k: int = 5, threshold: float = 0.3, 
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        유사도 기반 검색 (메타데이터 필터링 지원)
        
        Args:
            query: 검색 쿼리
            k: 반환할 최대 결과 수
            threshold: 유사도 임계값
            filters: 메타데이터 필터링 조건
            
        Returns:
            유사한 문서 리스트
        """
        try:
            print(f"[SEARCH] 유사도 검색 시작: '{query}' (k={k}, threshold={threshold})")
            if filters:
                print(f"[TARGET] 필터링 조건: {filters}")
            
            # ChromaDB 필터링 구성
            chroma_filters = self._build_chroma_filters(filters) if filters else None
            
            # 필터링 적용 검색
            results = await asyncio.to_thread(
                self.vector_store.similarity_search_with_score,
                query,
                k=k * 2,  # 더 많은 결과를 가져와서 필터링
                filter=chroma_filters
            )
            
            print(f"[STATS] ChromaDB에서 {len(results)}개 결과 반환")
            
            # 임계값 필터링 및 점수 포맷팅
            filtered_results = []
            for doc, score in results:
                formatted_score = self._format_similarity_score(score)
                
                print(f"📄 문서 점수: {formatted_score:.4f} (임계값: {threshold})")
                
                if formatted_score >= threshold:
                    filtered_results.append({
                        "text": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": formatted_score,
                        "id": str(uuid.uuid4())
                    })
            
            print(f"[OK] 최종 {len(filtered_results)}개 문서 통과 (임계값 {threshold} 이상)")
            return filtered_results
            
        except Exception as e:
            print(f"[FAIL] 유사도 검색 실패: {e}")
            return []
    
    def _build_chroma_filters(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        ChromaDB 필터링 조건 구성
        
        Args:
            filters: 필터링 조건
            
        Returns:
            ChromaDB 필터 객체
        """
        if not filters:
            return None
        
        chroma_filters = {}
        
        # 파일명 필터링
        if "filename" in filters:
            filename = filters["filename"]
            if isinstance(filename, str):
                chroma_filters["filename"] = {"$eq": filename}
            elif isinstance(filename, list):
                chroma_filters["filename"] = {"$in": filename}
        
        # 파일 타입 필터링
        if "file_type" in filters:
            file_type = filters["file_type"]
            if isinstance(file_type, str):
                chroma_filters["file_type"] = {"$eq": file_type}
            elif isinstance(file_type, list):
                chroma_filters["file_type"] = {"$in": file_type}
        
        # 기간 필터링 (saved_at 기준)
        if "date_range" in filters:
            date_range = filters["date_range"]
            if isinstance(date_range, dict):
                start_date = date_range.get("start")
                end_date = date_range.get("end")
                
                if start_date or end_date:
                    date_filter = {}
                    if start_date:
                        date_filter["$gte"] = start_date
                    if end_date:
                        date_filter["$lte"] = end_date
                    chroma_filters["saved_at"] = date_filter
        
        # 청크 타입 필터링
        if "chunk_type" in filters:
            chunk_type = filters["chunk_type"]
            if isinstance(chunk_type, str):
                chroma_filters["chunk_type"] = {"$eq": chunk_type}
            elif isinstance(chunk_type, list):
                chroma_filters["chunk_type"] = {"$in": chunk_type}
        
        # 유사도 점수 필터링 (저장 시점)
        if "min_score" in filters:
            min_score = filters["min_score"]
            chroma_filters["vector_score"] = {"$gte": float(min_score)}
        
        return chroma_filters if chroma_filters else None
    
    def _format_similarity_score(self, score: float) -> float:
        """
        유사도 점수 포맷팅 (소수점 2자리)
        
        Args:
            score: 원본 점수
            
        Returns:
            포맷팅된 점수
        """
        try:
            # 소수점 2자리로 반올림
            return round(float(score), 2)
        except (ValueError, TypeError):
            return 0.0
    
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
