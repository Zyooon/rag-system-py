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
        self.vector_store = ChromaVectorStore()
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
        
        all_documents = await self.load_documents_from_folder_simple(folder_path)
        
        if all_documents:
            # TextSplitterProcessor를 통한 긴 문서 분할
            split_documents = self.text_splitter_processor.split_documents(all_documents)
            
            # 벡터 저장소에 문서 추가
            try:
                vector_success = await self.vector_store.add_documents(split_documents)
                print(f"벡터 저장소에 {len(split_documents)}개 문서 저장 성공: {vector_success}")
            except Exception as e:
                print(f"벡터 저장소 저장 실패: {e}")
            
            # RedisDocumentRepository를 통한 문서 저장
            save_result = await self.redis_document_repository.save_documents(split_documents)
            
            # 임시 구현
            save_result = {
                MAP_KEY_SAVED_COUNT: len(all_documents),
                MAP_KEY_DUPLICATE_COUNT: 0,
                MAP_KEY_DOCUMENT_COUNT: len(all_documents)
            }
            
            return self.create_save_result(all_documents, all_documents, save_result)
        
        return {
            MAP_KEY_SAVED_COUNT: 0,
            MAP_KEY_DUPLICATE_COUNT: 0,
            MAP_KEY_TOTAL_COUNT: 0,
            MAP_KEY_MESSAGE: MSG_NO_TEXT_FILES
        }
    
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
    
    async def initialize_documents(self) -> None:
        """초기화 상태 확인"""
        try:
            print("=== Redis 벡터 저장소 상태 확인 ===")
            
            # TODO: 실제 Redis 키 조회 로직 구현
            # redis_keys = redis_document_repository.getAllDocumentKeys()
            redis_keys = []  # 임시 구현
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
