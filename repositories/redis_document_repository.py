"""
Redis 문서 저장소
Java 프로젝트의 RedisDocumentRepository와 유사한 기능 제공
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from config import settings


class RedisDocumentRepository:
    """Redis 문서 저장소"""
    
    def __init__(self):
        self.redis_url = settings.redis_url
        self.rag_key_prefix = settings.redis_rag_key_prefix
        self.embedding_key_prefix = settings.redis_embedding_key_prefix
        
        # TODO: 실제 Redis 클라이언트 연결 필요
        # self.redis_client = redis.from_url(self.redis_url)
        print(f"Redis 저장소 초기화: {self.redis_url}")
    
    async def save_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        문서들을 Redis에 저장
        
        Args:
            documents: 저장할 문서 리스트
            
        Returns:
            저장 결과 통계
        """
        try:
            saved_count = 0
            duplicate_count = 0
            
            # TODO: 실제 Redis 저장 로직 구현
            for doc in documents:
                doc_id = self._generate_document_id(doc)
                metadata = doc.get("metadata", {})
                
                # 메타데이터를 JSON으로 변환하여 저장
                metadata_json = json.dumps(metadata, ensure_ascii=False)
                
                # 임시 구현 - 실제로는 Redis에 저장
                print(f"문서 저장 시도: {doc_id}")
                saved_count += 1
            
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
        try:
            # TODO: 실제 Redis 키 조회 로직 구현
            # keys = self.redis_client.keys(f"{self.rag_key_prefix}:*")
            
            # 임시 구현
            keys = [
                f"{self.rag_key_prefix}:doc1",
                f"{self.rag_key_prefix}:doc2",
                f"{self.rag_key_prefix}:doc3"
            ]
            
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
        try:
            # TODO: 실제 Redis 문서 조회 로직 구현
            # data = self.redis_client.get(key)
            
            # 임시 구현
            if "doc1" in key:
                return {
                    "text": "샘플 문서 내용 1...",
                    "metadata": {
                        "filename": "sample.txt",
                        "chunk_index": 0
                    }
                }
            elif "doc2" in key:
                return {
                    "text": "샘플 문서 내용 2...",
                    "metadata": {
                        "filename": "README.md",
                        "chunk_index": 1
                    }
                }
            
            return None
        
        except Exception as e:
            print(f"문서 조회 실패: {key} - {e}")
            return None
    
    async def delete_keys_by_patterns(self, key_patterns: List[str]) -> Dict[str, int]:
        """
        키 패턴으로 데이터 삭제
        
        Args:
            key_patterns: 삭제할 키 패턴 리스트
            
        Returns:
            삭제된 키 수 통계
        """
        try:
            delete_results = {}
            
            for pattern in key_patterns:
                # TODO: 실제 Redis 키 삭제 로직 구현
                # deleted_count = len(self.redis_client.keys(pattern))
                # self.redis_client.delete(*keys)
                
                # 임시 구현
                if "rag:documents" in pattern:
                    deleted_count = 3  # doc1, doc2, doc3
                elif "rag:embeddings" in pattern:
                    deleted_count = 0
                else:
                    deleted_count = 0
                
                delete_results[pattern] = deleted_count
                print(f"키 패턴 삭제: {pattern} -> {deleted_count}개")
            
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
