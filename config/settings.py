"""
RAG 시스템 설정 관리
Java 프로젝트의 application.properties와 유사한 기능 제공
"""

import os
from pathlib import Path
from typing import List, Optional, Dict
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # 애플리케이션 기본 설정
    app_name: str = Field(default="RAG System API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Ollama LLM 설정
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3", env="OLLAMA_MODEL")
    ollama_embedding_model: str = Field(default="bge-m3", env="OLLAMA_EMBEDDING_MODEL")
    
    # Redis 설정
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_rag_key_prefix: str = Field(default="rag:documents", env="REDIS_RAG_KEY_PREFIX")
    redis_embedding_key_prefix: str = Field(default="rag:embeddings", env="REDIS_EMBEDDING_KEY_PREFIX")
    
    # 텍스트 분할 설정
    chunk_size: int = Field(default=300, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    min_chunk_size_chars: int = Field(default=50, env="MIN_CHUNK_SIZE_CHARS")
    long_document_threshold: int = Field(default=800, env="LONG_DOCUMENT_THRESHOLD")
    
    # 정밀 검색 설정
    precise_chunk_size: int = Field(default=100, env="PRECISE_CHUNK_SIZE")
    precise_min_chunk_size_chars: int = Field(default=30, env="PRECISE_MIN_CHUNK_SIZE_CHARS")
    precise_max_num_chunks: int = Field(default=800, env="PRECISE_MAX_NUM_CHUNKS")
    
    # 속도 최적화 설정
    speed_chunk_size: int = Field(default=400, env="SPEED_CHUNK_SIZE")
    speed_min_chunk_size_chars: int = Field(default=100, env="SPEED_MIN_CHUNK_SIZE_CHARS")
    
    # 파서 우선순위 설정
    hierarchical_parser_priority: int = Field(default=1, env="HIERARCHICAL_PARSER_PRIORITY")
    markdown_parser_priority: int = Field(default=2, env="MARKDOWN_PARSER_PRIORITY")
    simple_line_parser_priority: int = Field(default=3, env="SIMPLE_LINE_PARSER_PRIORITY")
    
    # 시맨틱 청킹 설정
    semantic_chunk_size: int = Field(default=500, env="SEMANTIC_CHUNK_SIZE")
    semantic_chunk_overlap: int = Field(default=50, env="SEMANTIC_CHUNK_OVERLAP")
    semantic_similarity_threshold: float = Field(default=0.3, env="SEMANTIC_SIMILARITY_THRESHOLD")
    enable_semantic_chunking: bool = Field(default=True, env="ENABLE_SEMANTIC_CHUNKING")
    
    # 리랭킹 설정
    enable_reranking: bool = Field(default=True, env="ENABLE_RERANKING")
    rerank_top_k: int = Field(default=5, env="RERANK_TOP_K")
    rerank_threshold: float = Field(default=0.5, env="RERANK_THRESHOLD")
    cross_encoder_model: str = Field(default="jhgan/ko-sroberta-multitask", env="CROSS_ENCODER_MODEL")
    
    # 벡터 저장소 설정
    vector_store_type: str = Field(default="chroma", env="VECTOR_STORE_TYPE")
    chroma_persist_directory: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    chroma_collection_name: str = Field(default="rag_collection", env="CHROMA_COLLECTION_NAME")
    
    # 검색 설정
    search_threshold: float = Field(default=0.3, env="SEARCH_THRESHOLD")
    search_max_results: int = Field(default=5, env="SEARCH_MAX_RESULTS")
    search_top_k: int = Field(default=10, env="SEARCH_TOP_K")
    
    # 문서 처리 설정
    documents_folder: str = Field(default="./documents", env="DOCUMENTS_FOLDER")
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    
    # 지원되는 파일 형식
    supported_extensions: List[str] = Field(
        default=[".txt", ".md", ".pdf", ".docx"], 
        env="SUPPORTED_EXTENSIONS"
    )
    
    # 로깅 설정
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="./logs/rag_system.log", env="LOG_FILE")
    
    # Spring AI 호환성 설정
    spring_ai_compatibility_mode: bool = Field(default=True, env="SPRING_AI_COMPATIBILITY_MODE")
    
    @property
    def redis_url(self) -> str:
        """Redis 연결 URL 생성"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def documents_path(self) -> Path:
        """문서 폴더 경로 객체"""
        return Path(self.documents_folder)
    
    @property
    def chroma_path(self) -> Path:
        """Chroma DB 경로 객체"""
        return Path(self.chroma_persist_directory)
    
    @property
    def log_path(self) -> Path:
        """로그 파일 경로 객체"""
        return Path(self.log_file)
    
    def get_supported_extensions_str(self) -> str:
        """지원 확장자 문자열 반환 (Java 호환성)"""
        return ",".join(self.supported_extensions)


# 전역 설정 인스턴스
settings = Settings()
