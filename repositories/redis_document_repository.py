"""
Redis 문서 저장소
Java 프로젝트의 RedisDocumentRepository와 유사한 기능 제공
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

try:
    import redis.asyncio as redis
except ImportError:
    print("Redis 패키지가 설치되지 않았습니다. 'pip install redis'를 실행하세요")
    redis = None

from config import settings


class RedisDocumentRepository:
    """Redis 문서 저장소"""
    
    def __init__(self):
        self.redis_url = settings.redis_url
        self.rag_key_prefix = settings.redis_rag_key_prefix
        self.embedding_key_prefix = settings.redis_embedding_key_prefix
        self.redis_client: Optional[Any] = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Redis 클라이언트 초기화 보장"""
        if not self._initialized:
            await self._initialize_redis()
            self._initialized = True
    
    async def _initialize_redis(self):
        """Redis 클라이언트 초기화"""
        if redis is None:
            print("Redis 패키지가 설치되지 않았습니다")
            self.redis_client = None
            return
            
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # 연결 테스트
            await self.redis_client.ping()
            print(f"Redis 연결 성공: {self.redis_url}")
            
        except Exception as e:
            print(f"Redis 연결 실패: {e}")
            self.redis_client = None
    
    async def save_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        문서들을 Redis에 저장
        
        Args:
            documents: 저장할 문서 리스트
            
        Returns:
            저장 결과 통계
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            print("Redis 클라이언트가 초기화되지 않았습니다")
            return {
                "saved_count": 0,
                "duplicate_count": 0,
                "total_processed": len(documents),
                "error": "Redis 연결 실패"
            }
        
        try:
            saved_count = 0
            duplicate_count = 0
            
            # 파이프라인을 사용하여 성능 향상
            pipe = self.redis_client.pipeline()
            
            for doc in documents:
                doc_id = self._generate_document_id(doc)
                metadata = doc.get("metadata", {})
                
                # 메타데이터를 JSON으로 변환하여 저장
                metadata_json = json.dumps(metadata, ensure_ascii=False)
                
                # 이미 존재하는지 확인
                exists = await self.redis_client.exists(doc_id)
                
                if not exists:
                    # 문서 내용과 메타데이터 저장
                    await pipe.hset(doc_id, mapping={
                        "text": doc.get("text", ""),
                        "metadata": metadata_json
                    })
                    saved_count += 1
                else:
                    duplicate_count += 1
            
            # 파이프라인 실행
            await pipe.execute()
            
            print(f"Redis에 {saved_count}개 문서 저장됨, {duplicate_count}개 중복")
            
            return {
                "saved_count": saved_count,
                "duplicate_count": duplicate_count,
                "total_processed": len(documents)
            }
        
        except Exception as e:
            print(f"문서 저장 실패: {e}")
            return {
                "saved_count": 0,
                "duplicate_count": 0,
                "total_processed": len(documents),
                "error": str(e)
            }
    
    async def get_all_document_keys(self) -> List[str]:
        """
        모든 문서 키 목록 반환
        
        Returns:
            문서 키 리스트
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            print("Redis 클라이언트가 초기화되지 않았습니다")
            return []
        
        try:
            pattern = f"{self.rag_key_prefix}:*"
            keys = await self.redis_client.keys(pattern)
            return keys
        
        except Exception as e:
            print(f"문서 키 조회 실패: {e}")
            return []
    
    async def get_document(self, key: str) -> Optional[Dict[str, Any]]:
        """
        특정 문서 조회
        
        Args:
            key: 문서 키
            
        Returns:
            문서 데이터 또는 None
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            return None
        
        try:
            doc_data = await self.redis_client.hgetall(key)
            
            if not doc_data:
                return None
            
            # 텍스트와 메타데이터 추출
            text = doc_data.get("text", "")
            metadata_str = doc_data.get("metadata", "{}")
            
            # 메타데이터 파싱
            try:
                metadata = json.loads(metadata_str)
            except json.JSONDecodeError:
                metadata = {"filename": "unknown"}
            
            return {
                "text": text,
                "metadata": metadata
            }
        
        except Exception as e:
            print(f"문서 조회 실패: {key} - {e}")
            return None
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        모든 문서 조회
        
        Returns:
            모든 문서 리스트
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            return []
        
        try:
            # 모든 문서 키 가져오기
            keys = await self.get_all_document_keys()
            
            if not keys:
                return []
            
            # 모든 문서 데이터 가져오기
            documents = []
            for key in keys:
                doc = await self.get_document(key)
                if doc:
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"모든 문서 조회 실패: {e}")
            return []
    
    async def delete_keys_by_patterns(self, key_patterns: List[str]) -> Dict[str, int]:
        """
        키 패턴으로 데이터 삭제
        
        Args:
            key_patterns: 삭제할 키 패턴 리스트
            
        Returns:
            삭제된 키 수 통계
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            print("Redis 클라이언트가 초기화되지 않았습니다")
            return {}
        
        try:
            delete_results = {}
            
            for pattern in key_patterns:
                # 패턴에 해당하는 키 찾기
                keys = await self.redis_client.keys(pattern)
                
                if keys:
                    # 키 삭제
                    deleted_count = await self.redis_client.delete(*keys)
                    delete_results[pattern] = deleted_count
                    print(f"키 패턴 삭제: {pattern} -> {deleted_count}개")
                else:
                    delete_results[pattern] = 0
            
            return delete_results
        
        except Exception as e:
            print(f"키 패턴 삭제 실패: {e}")
            return {}
    
    def _generate_document_id(self, doc: Dict[str, Any]) -> str:
        """
        문서 ID 생성
        
        Args:
            doc: 문서 데이터
            
        Returns:
            고유 문서 ID
        """
        metadata = doc.get("metadata", {})
        filename = metadata.get("filename", "unknown")
        chunk_index = metadata.get("chunk_index", 0)
        
        return f"{self.rag_key_prefix}:{filename}:{chunk_index}"
    
    def get_key_patterns(self) -> List[str]:
        """
        삭제에 사용할 키 패턴 반환
        
        Returns:
            키 패턴 리스트
        """
        return [
            f"{self.rag_key_prefix}:*",
            f"{self.embedding_key_prefix}:*"
        ]
    
    def get_full_key_pattern(self) -> str:
        """
        전체 키 패턴 반환
        
        Returns:
            전체 키 패턴
        """
        return f"{self.rag_key_prefix}:*"
    
    def get_embedding_key_pattern(self) -> str:
        """
        임베딩 키 패턴 반환
        
        Returns:
            임베딩 키 패턴
        """
        return f"{self.embedding_key_prefix}:*"
