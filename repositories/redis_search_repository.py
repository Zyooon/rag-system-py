"""
Redis 검색용 문서 데이터 접근 리포지토리
Java 프로젝트의 RedisSearchRepository와 유사한 기능 제공

이 클래스는 SearchService를 위해 Redis에 저장된 문서 데이터를 조회하는 역할을 담당합니다:
- 문서 조회 - 모든 문서 조회
- 키 관리 - 문서 키 목록 조회
- 데이터 접근 - 개별 문서 조회
- 예외 처리 - Redis 연결 및 데이터 처리 예외

주요 책임:
- RedisTemplate을 통한 데이터 조회 작업
- SearchService를 위한 읽기 전용 접근
- 문서 내용 기반 검색 지원

키 전략:
- 접두사: rag:document:
- 메타데이터: JSON 형태로 저장
"""

import json
import asyncio
import logging
from typing import List, Dict, Any, Optional

try:
    import redis.asyncio as redis
except ImportError:
    print("Redis 패키지가 설치되지 않았습니다. 'pip install redis'를 실행하세요")
    redis = None

from config import settings
from constants import (
    REDIS_DOCUMENT_KEY_PREFIX, LOG_DOCUMENT_STATUS_CHECK_FAILED,
    LOG_REDIS_STATUS_CHECK_ERROR, LOG_UNEXPECTED_ERROR
)

# 로거 설정
logger = logging.getLogger(__name__)


class RedisSearchRepository:
    """Redis 검색용 문서 데이터 접근 리포지토리"""
    
    def __init__(self):
        self.redis_url = settings.redis_url
        self.document_key_prefix = settings.redis_rag_key_prefix  # 설정 값 사용
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
            logger.error("Redis 패키지가 설치되지 않았습니다")
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
            logger.info("Redis 검색 리포지토리 초기화 성공")
            
        except Exception as e:
            logger.error(f"Redis 검색 리포지토리 초기화 실패: {e}")
            self.redis_client = None
    
    async def get_all_document_keys(self) -> List[str]:
        """
        Redis에 저장된 모든 문서 키 목록 조회
        
        Returns:
            문서 키 목록
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 초기화되지 않았습니다")
            return []
        
        try:
            # 접두사로 모든 키 조회
            pattern = f"{self.document_key_prefix}:*"  # rag:documents:*
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                logger.info(f"Redis에서 {len(keys)}개의 문서 키를 조회했습니다")
                return keys
            else:
                logger.info("Redis에 저장된 문서 키가 없습니다")
                return []
                
        except Exception as e:
            logger.error(f"Redis 키 조회 실패: {e}")
            return []
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Redis에 저장된 모든 문서 조회
        
        Returns:
            문서 목록
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 초기화되지 않았습니다")
            return []
        
        try:
            keys = await self.get_all_document_keys()
            documents = []
            
            for key in keys:
                doc = await self.get_document(key)
                if doc:
                    documents.append(doc)
            
            logger.info(f"Redis에서 {len(documents)}개의 문서를 조회했습니다")
            return documents
            
        except Exception as e:
            logger.error(f"Redis 문서 목록 조회 실패: {e}")
            return []
    
    async def get_document(self, key: str) -> Dict[str, Any]:
        """
        특정 키로 문서 조회
        
        Args:
            key: 문서 키
            
        Returns:
            문서 데이터
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 초기화되지 않았습니다")
            return {}
        
        try:
            # Hash 형태로 저장된 문서 데이터 조회
            data = await self.redis_client.hgetall(key)
            
            if data:
                # JSON 문자열 필드 파싱
                parsed_data = {}
                for field_name, field_value in data.items():
                    if field_value:
                        try:
                            # 메타데이터나 JSON 필드는 파싱 시도
                            if field_name in ['metadata', 'text', 'content']:
                                parsed_data[field_name] = json.loads(field_value) if field_value.startswith('{') else field_value
                            else:
                                parsed_data[field_name] = field_value
                        except (json.JSONDecodeError, TypeError):
                            # JSON 파싱 실패시 원본 문자열 사용
                            parsed_data[field_name] = field_value
                
                logger.debug(f"문서 조회 성공 ({key}): {len(parsed_data)}개 필드")
                return parsed_data
            else:
                logger.debug(f"문서를 찾을 수 없음: {key}")
                return {}
                
        except Exception as e:
            logger.error(f"Redis 문서 조회 실패 ({key}): {e}")
            return {}
    
    async def search_documents_by_content(self, search_term: str) -> List[Dict[str, Any]]:
        """
        내용으로 문서 검색
        
        Args:
            search_term: 검색어
            
        Returns:
            검색된 문서 목록
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 초기화되지 않았습니다")
            return []
        
        try:
            all_documents = await self.get_all_documents()
            matching_documents = []
            
            search_term_lower = search_term.lower()
            
            for doc in all_documents:
                text_content = doc.get('text', '') or doc.get('content', '')
                metadata = doc.get('metadata', {})
                
                # 텍스트 내용에서 검색
                if search_term_lower in text_content.lower():
                    matching_documents.append(doc)
                    continue
                
                # 메타데이터에서 검색
                for meta_value in metadata.values():
                    if isinstance(meta_value, str) and search_term_lower in meta_value.lower():
                        matching_documents.append(doc)
                        break
            
            logger.info(f"'{search_term}' 검색 결과: {len(matching_documents)}개 문서")
            return matching_documents
            
        except Exception as e:
            logger.error(f"문서 내용 검색 실패: {e}")
            return []
    
    async def get_documents_by_filename(self, filename: str) -> List[Dict[str, Any]]:
        """
        파일명으로 문서 검색
        
        Args:
            filename: 파일명
            
        Returns:
            검색된 문서 목록
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 초기화되지 않았습니다")
            return []
        
        try:
            all_documents = await self.get_all_documents()
            matching_documents = []
            
            for doc in all_documents:
                metadata = doc.get('metadata', {})
                doc_filename = metadata.get('filename', '')
                
                if filename.lower() in doc_filename.lower():
                    matching_documents.append(doc)
            
            logger.info(f"파일명 '{filename}' 검색 결과: {len(matching_documents)}개 문서")
            return matching_documents
            
        except Exception as e:
            logger.error(f"파일명 검색 실패: {e}")
            return []
    
    async def get_document_count(self) -> int:
        """
        저장된 문서 개수 조회
        
        Returns:
            문서 개수
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 초기화되지 않았습니다")
            return 0
        
        try:
            keys = await self.get_all_document_keys()
            return len(keys)
            
        except Exception as e:
            logger.error(f"문서 개수 조회 실패: {e}")
            return 0
    
    async def is_document_exists(self, key: str) -> bool:
        """
        문서 존재 여부 확인
        
        Args:
            key: 문서 키
            
        Returns:
            존재 여부
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 초기화되지 않았습니다")
            return False
        
        try:
            return await self.redis_client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"문서 존재 확인 실패 ({key}): {e}")
            return False
    
    async def get_document_summary(self) -> Dict[str, Any]:
        """
        문서 저장소 요약 정보 조회
        
        Returns:
            요약 정보
        """
        await self._ensure_initialized()
        
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 초기화되지 않았습니다")
            return {}
        
        try:
            keys = await self.get_all_document_keys()
            documents = await self.get_all_documents()
            
            # 파일별 통계
            file_stats = {}
            for doc in documents:
                metadata = doc.get('metadata', {})
                filename = metadata.get('filename', 'unknown')
                
                if filename not in file_stats:
                    file_stats[filename] = {
                        'count': 0,
                        'total_length': 0,
                        'chunk_ids': []
                    }
                
                file_stats[filename]['count'] += 1
                file_stats[filename]['total_length'] += len(doc.get('text', ''))
                
                chunk_id = metadata.get('chunk_id')
                if chunk_id:
                    file_stats[filename]['chunk_ids'].append(chunk_id)
            
            summary = {
                'total_documents': len(documents),
                'total_keys': len(keys),
                'file_statistics': file_stats,
                'key_prefix': self.document_key_prefix,
                'redis_connected': self.redis_client is not None
            }
            
            logger.info(f"문서 저장소 요약: {summary['total_documents']}개 문서, {len(file_stats)}개 파일")
            return summary
            
        except Exception as e:
            logger.error(f"문서 저장소 요약 조회 실패: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        리포지토리 상태 확인
        
        Returns:
            상태 정보
        """
        await self._ensure_initialized()
        
        status = {
            'repository_type': 'RedisSearchRepository',
            'redis_connected': False,
            'document_count': 0,
            'key_prefix': self.document_key_prefix,
            'status': 'unhealthy'
        }
        
        if not self.redis_client:
            status['error'] = 'Redis 클라이언트 초기화 실패'
            return status
        
        try:
            # Redis 연결 확인
            await self.redis_client.ping()
            status['redis_connected'] = True
            
            # 문서 개수 확인
            status['document_count'] = await self.get_document_count()
            
            status['status'] = 'healthy'
            logger.info("Redis 검색 리포지토리 상태: 정상")
            
        except Exception as e:
            status['error'] = str(e)
            logger.error(f"Redis 검색 리포지토리 상태 확인 실패: {e}")
        
        return status
