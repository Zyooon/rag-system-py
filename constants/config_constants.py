"""
설정 관련 상수 정의
Java 프로젝트의 ConfigConstants와 유사한 기능 제공
"""

# API 응답 맵 키
MAP_KEY_SAVED_COUNT = "saved_count"
MAP_KEY_DUPLICATE_COUNT = "duplicate_count"
MAP_KEY_TOTAL_COUNT = "total_count"
MAP_KEY_DOCUMENT_COUNT = "document_count"
MAP_KEY_MESSAGE = "message"
MAP_KEY_IS_INITIALIZED = "is_initialized"
MAP_KEY_LOADED_FILES = "loaded_files"
MAP_KEY_REDIS_CONNECTION = "redis_connection"
MAP_KEY_VECTOR_STORE_TYPE = "vector_store_type"
MAP_KEY_TOTAL_DELETED = "total_deleted"
MAP_KEY_RAG_KEYS_DELETED = "rag_keys_deleted"
MAP_KEY_EMBEDDING_KEYS_DELETED = "embedding_keys_deleted"
MAP_KEY_RAG_KEYS = "rag_keys"
MAP_KEY_EMBEDDING_KEYS = "embedding_keys"
MAP_KEY_ANSWER = "answer"
MAP_KEY_SOURCES = "sources"

# Redis 연결 상태
REDIS_CONNECTION_CONNECTED = "connected"
REDIS_CONNECTION_DISCONNECTED = "disconnected"

# 벡터 저장소 타입
VECTORSTORE_TYPE_SIMPLE_REDIS_BACKUP = "simple_redis_backup"

# 메시지 상수
MSG_REDIS_CONNECTION_CHECK = "Redis 연결 상태 확인"
MSG_REDIS_STATUS_CHECK_FAILED = "Redis 상태 확인 실패: "
MSG_REDIS_VECTORSTORE_DELETE_COMPLETE = "Redis 벡터 저장소 삭제 완료: 총 %d개 삭제 (RAG: %d, 임베딩: %d)"
MSG_REDIS_VECTORSTORE_DELETE_FAILED = "Redis 벡터 저장소 삭제 실패: "
MSG_REDIS_VECTORSTORE_BUILD_FAILED = "Redis 벡터 저장소 구축 실패: "
MSG_DOCUMENTS_RELOADED = "문서 다시 로드 완료: %d개 삭제됨"
MSG_DOCUMENT_RELOAD_FAILED = "문서 재로드 실패: "
MSG_REDIS_KEY_DELETE_ERROR = "Redis 키 삭제 오류: "

# 로그 메시지
LOG_DOCUMENT_STATUS_CHECK_FAILED = "문서 상태 확인 실패: {}"
LOG_METADATA_JSON_PARSE_FAILED = "메타데이터 JSON 파싱 실패: {}"
