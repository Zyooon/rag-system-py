"""
RAG 시스템 통합 관리 서비스
Java 프로젝트의 RagManagementService와 유사한 기능 제공
"""

import asyncio
import json
from typing import List, Dict, Any, Set
from pathlib import Path

from services import FileManager, ParseManager
from splitters import TextSplitterProcessor
from repositories import RedisDocumentRepository, ChromaVectorStore
from config import settings
from constants import (
    MAP_KEY_SAVED_COUNT, MAP_KEY_DUPLICATE_COUNT, MAP_KEY_TOTAL_COUNT, MAP_KEY_DOCUMENT_COUNT,
    MAP_KEY_MESSAGE, MAP_KEY_IS_INITIALIZED, MAP_KEY_LOADED_FILES, MAP_KEY_REDIS_CONNECTION,
    MAP_KEY_VECTOR_STORE_TYPE, MAP_KEY_TOTAL_DELETED, MAP_KEY_RAG_KEYS_DELETED,
    MAP_KEY_EMBEDDING_KEYS_DELETED, MAP_KEY_RAG_KEYS, MAP_KEY_EMBEDDING_KEYS,
    TXT_EXTENSION, MD_EXTENSION, METADATA_KEY_FILENAME, METADATA_KEY_FILEPATH,
    METADATA_KEY_SAVED_AT, KEY_EXISTS, KEY_FILES, REDIS_CONNECTION_CONNECTED,
    VECTORSTORE_TYPE_SIMPLE_REDIS_BACKUP, MSG_REDIS_CONNECTION_CHECK,
    MSG_REDIS_STATUS_CHECK_FAILED, MSG_REDIS_VECTORSTORE_DELETE_COMPLETE,
    MSG_REDIS_VECTORSTORE_DELETE_FAILED, MSG_REDIS_VECTORSTORE_BUILD_FAILED,
    MSG_DOCUMENTS_RELOADED, MSG_DOCUMENT_RELOAD_FAILED, MSG_VECTORSTORE_DATA_CLEANED,
    MSG_VECTORSTORE_INIT_ERROR, MSG_FOLDER_NOT_EXISTS, MSG_NO_TEXT_FILES
)


class RagManagementService:
    """RAG 시스템 통합 관리 서비스"""
    
    def __init__(self):
        self.file_manager = FileManager()
        self.parse_manager = ParseManager()
        self.text_splitter_processor = TextSplitterProcessor()
        self.redis_document_repository = RedisDocumentRepository()
        
        # 시맨틱 청킹 서비스
        if settings.enable_semantic_chunking:
            from .semantic_chunking_service import SemanticChunkingService
            self.semantic_chunking_service = SemanticChunkingService()
            print("RAG 관리: 시맨틱 청킹 서비스 활성화")
        else:
            self.semantic_chunking_service = None
            print("RAG 관리: 시맨틱 청킹 서비스 비활성화")
        
        # 벡터 저장소 초기화 (순환 임포트 방지)
        from repositories import ChromaVectorStore
        self.vector_store = ChromaVectorStore()
        
        # 임베딩 서비스 설정
        from services import EmbeddingService
        embedding_service = EmbeddingService()
        self.vector_store._set_embedding_service(embedding_service)
        
        self.is_initialized = False
    
    # ==================== 문서 처리 기능 ====================
    
    async def save_documents_to_redis(self) -> Dict[str, Any]:
        """현재 documents 폴더의 모든 문서를 Redis에 저장하는 메서드"""
        result = await self.save_documents_from_folder_with_duplicate_check(settings.documents_folder)
        
        # 문서 저장 후 초기화 상태 업데이트
        await self.initialize_documents()
        
        return result
    
    async def load_documents_from_folder(self, folder_path: str) -> None:
        """특정 폴더의 모든 텍스트 파일을 자동으로 로드하는 메서드"""
        if not await self.file_manager.ensure_folder_exists(folder_path):
            print(f"폴더 생성 실패: {folder_path}")
            return
        
        all_documents = await self.process_files_in_folder(folder_path)
        
        if all_documents:
            final_documents = self.create_final_documents(all_documents)
            print(f"문서 처리 완료: {len(final_documents)}개 최종 문서 생성")
    
    async def save_documents_from_folder_with_duplicate_check(self, folder_path: str) -> Dict[str, Any]:
        """특정 폴더의 문서들을 Redis에 저장하는 메서드 (중복 방지)"""
        folder_status = self.file_manager.get_folder_status(folder_path)
        
        if not folder_status.get(KEY_EXISTS, False):
            return {
                MAP_KEY_SAVED_COUNT: 0,
                MAP_KEY_DUPLICATE_COUNT: 0,
                MAP_KEY_TOTAL_COUNT: 0,
                MAP_KEY_MESSAGE: MSG_FOLDER_NOT_EXISTS
            }
        
        # 순수 텍스트 파일만 가져오기 (파싱 없음)
        raw_documents = await self.load_raw_documents_from_folder(folder_path)
        
        if raw_documents:
            # ParseManager를 통한 전략적 문서 분할
            processed_documents = []
            for doc in raw_documents:
                content = doc.get('text', '')
                filename = doc.get('metadata', {}).get('filename', 'unknown')
                
                # ParseManager로 최적의 파서 선택 및 분할
                parsed_chunks = self.parse_manager.parse_document(content, filename)
                processed_documents.extend(parsed_chunks)
            
            # 시맨틱 청킹 적용
            if self.semantic_chunking_service:
                print(f"🧠 시맨틱 청킹 적용: {len(processed_documents)}개 문서")
                semantic_chunks = await self.semantic_chunking_service.batch_semantic_chunk(processed_documents)
                processed_documents = semantic_chunks
                print(f"[TARGET] 시맨틱 청킹 결과: {len(processed_documents)}개 청크")
            else:
                print("⚠️ 시맨틱 청킹 스킵")
            
            # 크기 최적화 (TextSplitterProcessor)
            processed_documents = self._optimize_chunk_sizes(processed_documents)
            
            # 벡터 저장소에 문서 추가
            try:
                vector_success = await self.vector_store.add_documents(processed_documents)
                print(f"벡터 저장소에 {len(processed_documents)}개 문서 저장 성공: {vector_success}")
            except Exception as e:
                print(f"벡터 저장소 저장 실패: {e}")
            
            # RedisDocumentRepository를 통한 문서 저장
            save_result = await self.redis_document_repository.save_documents(processed_documents)
            
            # 임시 구현
            save_result = {
                MAP_KEY_SAVED_COUNT: len(raw_documents),
                MAP_KEY_DUPLICATE_COUNT: 0,
                MAP_KEY_DOCUMENT_COUNT: len(processed_documents)
            }
            
            return self.create_save_result(raw_documents, processed_documents, save_result)
    
    def _optimize_chunk_sizes(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        TextSplitterProcessor로 청크 크기 최적화
        
        Args:
            chunks: 파서로 1차 분할된 청크 리스트
            
        Returns:
            크기 최적화된 청크 리스트
        """
        from datetime import datetime
        
        optimized_chunks = []
        max_chunk_size = settings.chunk_size
        
        for i, chunk in enumerate(chunks):
            text = chunk.get('text', '')
            metadata = chunk.get('metadata', {})
            
            # 청크가 최대 크기를 초과하는 경우만 재분할
            if len(text) > max_chunk_size:
                # TextSplitterProcessor로 재분할
                oversized_chunks = [chunk]  # 개별 청크로 처리
                split_chunks = self.text_splitter_processor.split_documents(oversized_chunks)
                
                # 재분할된 청크에 메타데이터 업데이트
                for j, split_chunk in enumerate(split_chunks):
                    split_chunk['metadata'].update(metadata)
                    split_chunk['metadata']['chunk_index'] = len(optimized_chunks)
                    split_chunk['metadata']['splitter_type'] = 'size_optimized'
                    split_chunk['metadata']['saved_at'] = datetime.now().isoformat()
                    split_chunk['metadata']['original_parser'] = metadata.get('splitter_type', 'unknown')
                    split_chunk['metadata']['parent_chunk_index'] = i
                    
                    optimized_chunks.append(split_chunk)
                
                print(f"청크 크기 최적화: {len(text)} → {len(split_chunks)}개 작은 청크")
            else:
                # 크기가 적절하면 그대로 사용
                chunk['metadata']['chunk_index'] = len(optimized_chunks)
                chunk['metadata']['saved_at'] = datetime.now().isoformat()
                optimized_chunks.append(chunk)
        
        print(f"크기 최적화 완료: {len(chunks)} → {len(optimized_chunks)}개 청크")
        return optimized_chunks
    
    # ==================== 벡터 저장소 관리 기능 ====================
    
    async def clear_store(self) -> Dict[str, Any]:
        """벡터 저장소 초기화"""
        result = {}
        try:
            self.is_initialized = False
            
            # 1. 벡터 저장소 정리
            try:
                vector_clear_success = await self.vector_store.clear()
                print(f"벡터 저장소 정리 성공: {vector_clear_success}")
            except Exception as e:
                print(f"벡터 저장소 정리 실패: {e}")
                vector_clear_success = False
            
            # 2. Redis 키 패턴 삭제
            key_patterns = self.redis_document_repository.get_key_patterns()
            delete_results = await self.redis_document_repository.delete_keys_by_patterns(key_patterns)
            
            rag_deleted = delete_results.get(self.redis_document_repository.get_full_key_pattern(), 0)
            embedding_deleted = delete_results.get(self.redis_document_repository.get_embedding_key_pattern(), 0)
            total_deleted = rag_deleted + embedding_deleted
            
            print(f"벡터 저장소 초기화 완료: 총 {total_deleted}개 키 삭제됨")
            
        except Exception as e:
            print(f"벡터 저장소 초기화 실패: {e}")
            result[MAP_KEY_TOTAL_DELETED] = 0
            result[MAP_KEY_MESSAGE] = MSG_VECTORSTORE_INIT_ERROR
        
        return result
    
    async def get_status_with_files(self) -> Dict[str, Any]:
        """시스템 상태 정보 반환"""
        status = {}
        status[MAP_KEY_IS_INITIALIZED] = self.is_initialized
        
        if self.is_initialized:
            vector_store_count = 0
            loaded_files = set()
            
            try:
                # FileManager를 통해 파일 목록 가져오기
                folder_status = self.file_manager.get_folder_status(settings.documents_folder)
                
                if folder_status.get(KEY_EXISTS, False):
                    files = folder_status.get(KEY_FILES, [])
                    
                    for file_name in files:
                        lower_file_name = file_name.lower()
                        if lower_file_name.endswith(TXT_EXTENSION) or lower_file_name.endswith(MD_EXTENSION):
                            loaded_files.add(file_name)
                    
                    vector_store_count = len(loaded_files) * 3  # Java와 동일한 계산
            
            except Exception as e:
                print(f"문서 상태 확인 실패: {e}")
                vector_store_count = 0
            
            # TODO: 실제 Redis 키 조회 로직 구현
            redis_keys = await self.redis_document_repository.get_all_document_keys()
            
            if redis_keys:
                status[MAP_KEY_RAG_KEYS_DELETED] = redis_keys
                
                # Redis에 저장된 메타데이터에서 파일명 추출
                for key in redis_keys:
                    try:
                        doc = await self.redis_document_repository.get_document(key)
                        if doc:
                            metadata = doc.get("metadata", {})
                            
                            if isinstance(metadata, dict):
                                filename = metadata.get(METADATA_KEY_FILENAME)
                                if filename:
                                    loaded_files.add(filename)
                            elif isinstance(metadata, str):
                                try:
                                    meta_map = json.loads(metadata)
                                    filename = meta_map.get(METADATA_KEY_FILENAME)
                                    if filename:
                                        loaded_files.add(filename)
                                except Exception as json_ex:
                                    print(f"메타데이터 JSON 파싱 실패: {json_ex}")
                    
                    except Exception as e:
                        print(f"Redis 키 {key} 처리 실패: {e}")
            
            status[MAP_KEY_LOADED_FILES] = list(loaded_files)
            status[MAP_KEY_DOCUMENT_COUNT] = vector_store_count
            status[MAP_KEY_TOTAL_COUNT] = len(redis_keys)
        
        return status
    
    async def get_documents_list(self) -> List[Dict[str, Any]]:
        """저장된 문서 목록을 파일별로 그룹화하여 반환 (파일명과 청크 수만)"""
        try:
            # Redis에 저장된 모든 문서 키 가져오기
            documents = await self.redis_document_repository.get_all_document_keys()
            
            if not documents:
                return []
            
            # 파일별로 그룹화
            file_groups = {}
            for key in documents:
                # 키에서 파일명 추출 (rag:documents:filename:chunk_index 형식)
                parts = key.split(':')
                if len(parts) >= 3:
                    filename = parts[2]  # rag:documents:filename:chunk_index
                    
                    if filename not in file_groups:
                        file_groups[filename] = 0
                    file_groups[filename] += 1
            
            # 파일별 정보 생성 (파일명과 청크 수만)
            document_list = []
            for filename, chunk_count in file_groups.items():
                document_info = {
                    "filename": filename,
                    "total_chunks": chunk_count
                }
                document_list.append(document_info)
            
            return document_list
            
        except Exception as e:
            print(f"문서 목록 조회 실패: {e}")
            return []
    
    async def initialize_documents(self) -> None:
        """초기화 상태 확인"""
        try:
            print("=== Redis 벡터 저장소 상태 확인 ===")
            
            # Redis에서 실제 키 조회
            redis_keys = await self.redis_document_repository.get_all_document_keys()
            document_count = len(redis_keys)
            
            if document_count > 0:
                self.is_initialized = True
                print(f"Redis 벡터 저장소에 {document_count}개의 문서가 있습니다.")
                print("시스템이 준비되었습니다.")
            else:
                self.is_initialized = False
                print("Redis 벡터 저장소에 데이터가 없습니다.")
                print("수동으로 데이터를 로드해주세요 (/load-from-files API 호출).")
        
        except Exception as e:
            print(f"벡터 저장소 초기화 실패: {e}")
            self.is_initialized = False
    
    # ==================== private helper methods ====================
    
    async def process_files_in_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """폴더 내의 모든 파일 처리"""
        all_documents = []
        folder = Path(folder_path)
        
        file_contents = await self.file_manager.read_all_supported_files(folder)
        
        for file_content in file_contents:
            try:
                content = file_content.content
                filename = file_content.filename
                
                # ParseManager를 통해 최적의 파서 자동 선택
                parsed_documents = self.parse_manager.parse_document(content, filename)
                
                # TODO: TextSplitterProcessor를 통한 긴 문서 분할
                # final_documents = text_splitter_processor.split_long_documents(parsed_documents)
                final_documents = parsed_documents  # 임시 구현
                
                all_documents.extend(final_documents)
            
            except Exception as e:
                print(f"문서 처리 실패: {file_content.filename} - {e}")
        
        return all_documents
    
    def create_final_documents(self, all_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """최종 문서 생성"""
        final_documents = []
        global_chunk_index = 0
        
        for original_doc in all_documents:
            metadata = original_doc.get("metadata", {}).copy()
            metadata["chunk_index"] = global_chunk_index
            
            final_documents.append({
                "text": original_doc.get("text", ""),
                "metadata": metadata
            })
            global_chunk_index += 1
        
        return final_documents
    
    def create_save_result(self, original_docs: List[Dict[str, Any]], 
                         split_docs: List[Dict[str, Any]], 
                         save_result: Dict[str, Any]) -> Dict[str, Any]:
        """저장 결과 생성"""
        return {
            MAP_KEY_SAVED_COUNT: save_result.get(MAP_KEY_SAVED_COUNT, 0),
            MAP_KEY_DUPLICATE_COUNT: save_result.get(MAP_KEY_DUPLICATE_COUNT, 0),
            MAP_KEY_TOTAL_COUNT: len(original_docs),
            MAP_KEY_DOCUMENT_COUNT: len(split_docs),
            MAP_KEY_MESSAGE: "문서 저장 완료"
        }
    
    async def load_raw_documents_from_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """폴더에서 순수 텍스트 문서만 가져오기 (파싱 없음)"""
        raw_documents = []
        folder = Path(folder_path)
        
        file_contents = await self.file_manager.read_all_supported_files(folder)
        
        for file_content in file_contents:
            try:
                # 순수 텍스트와 기본 메타데이터만 저장
                document = {
                    "text": file_content.content,
                    "metadata": {
                        METADATA_KEY_FILENAME: file_content.filename,
                        METADATA_KEY_FILEPATH: str(file_content.file_path),
                        METADATA_KEY_SAVED_AT: file_content.metadata.get(METADATA_KEY_SAVED_AT, "")
                    }
                }
                raw_documents.append(document)
                print(f"원본 텍스트 로드: {file_content.filename} (길이: {len(file_content.content)})")
            
            except Exception as e:
                print(f"원본 텍스트 로드 실패: {file_content.filename} - {e}")
        
        return raw_documents
    
    async def load_documents_from_folder_simple(self, folder_path: str) -> List[Dict[str, Any]]:
        """단순 문서 로드"""
        all_documents = []
        folder = Path(folder_path)
        
        file_contents = await self.file_manager.read_all_supported_files(folder)
        
        for file_content in file_contents:
            try:
                content = file_content.content
                filename = file_content.filename
                
                # ParseManager를 통해 최적의 파서 자동 선택
                parsed_documents = self.parse_manager.parse_document(content, filename)
                
                if not parsed_documents:
                    print(f"파싱 실패: {filename} (파서 선택 불가)")
                else:
                    print(f"ParseManager로 {len(parsed_documents)}개 조각 분할: {filename}")
                
                # 최종 Fallback: 정말 아무것도 안 되면 전체 저장
                if not parsed_documents:
                    fallback_metadata = {
                        METADATA_KEY_FILENAME: filename,
                        METADATA_KEY_FILEPATH: str(file_content.file_path),
                        METADATA_KEY_SAVED_AT: "2024-01-01T00:00:00"  # 임시
                    }
                    document = {
                        "text": content,
                        "metadata": fallback_metadata
                    }
                    all_documents.append(document)
                    print(f"전체 문서로 저장: {filename}")
                else:
                    all_documents.extend(parsed_documents)
                    print(f"총 {len(parsed_documents)}개 조각 저장: {filename}")
            
            except Exception as e:
                print(f"문서 처리 실패: {file_content.filename} - {e}")
        
        return all_documents
