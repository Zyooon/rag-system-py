"""
설정 관련 상수 정의
Java 프로젝트의 ConfigConstants와 유사한 기능 제공
"""

# ==================== 설정 키 ====================
CONFIG_DOCUMENTS_FOLDER = "rag.documents.folder"
CONFIG_VECTORSTORE_TYPE = "rag.vectorstore.type"
CONFIG_VECTORSTORE_INDEX_NAME = "rag.redis.vectorstore.index-name"
CONFIG_VECTORSTORE_KEY_PREFIX = "rag.redis.vectorstore.key-prefix"
CONFIG_VECTORSTORE_EMBEDDING_PREFIX = "rag.redis.vectorstore.embedding-prefix"
CONFIG_SEARCH_THRESHOLD = "rag.search.threshold"
CONFIG_SEARCH_MAX_RESULTS = "rag.search.max-results"

# ==================== 기본값 ====================
DEFAULT_DOCUMENTS_FOLDER = "documents"
DEFAULT_VECTORSTORE_TYPE = "redis"
DEFAULT_SEARCH_THRESHOLD = 0.3
DEFAULT_MAX_RESULTS = 5
DEFAULT_OLLAMA_CHAT_MODEL = "llama3"
DEFAULT_OLLAMA_EMBEDDING_MODEL = "bge-m3"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_REDIS_HOST = "localhost"
DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DATABASE = 0

# ==================== Redis 관련 상수 ====================
REDIS_KEY_PREFIX = "rag:"
REDIS_DOCUMENT_KEY_PREFIX = "rag:document:"
REDIS_EMBEDDING_KEY_PREFIX = "embedding:"
VECTOR_INDEX_NAME = "vector_index"
VECTORSTORE_PREFIX = "rag:"

# ==================== 설정 맵 키 상수 ====================
MAP_KEY_DOCUMENTS_FOLDER = "documentsFolder"
MAP_KEY_PROCESSING_DOCUMENTS_FOLDER = "processingDocumentsFolder"
MAP_KEY_INDEX_NAME = "indexName"
MAP_KEY_KEY_PREFIX = "keyPrefix"
MAP_KEY_EMBEDDING_PREFIX = "embeddingPrefix"

# ==================== API 응답 맵 키 ====================
MAP_KEY_SAVED_COUNT = "savedCount"
MAP_KEY_DUPLICATE_COUNT = "duplicateCount"
MAP_KEY_TOTAL_COUNT = "totalCount"
MAP_KEY_DOCUMENT_COUNT = "documentCount"
MAP_KEY_MESSAGE = "message"
MAP_KEY_IS_INITIALIZED = "isInitialized"
MAP_KEY_LOADED_FILES = "loadedFiles"
MAP_KEY_REDIS_CONNECTION = "redis_connection"
MAP_KEY_VECTOR_STORE_TYPE = "vector_store_type"
MAP_KEY_TOTAL_DELETED = "totalDeleted"
MAP_KEY_RAG_KEYS_DELETED = "ragKeysDeleted"
MAP_KEY_EMBEDDING_KEYS_DELETED = "embeddingKeysDeleted"
MAP_KEY_RAG_KEYS = "ragKeys"
MAP_KEY_EMBEDDING_KEYS = "embeddingKeys"
MAP_KEY_ANSWER = "answer"
MAP_KEY_SOURCES = "sources"
MAP_KEY_SUCCESS = "success"
MAP_KEY_ORIGINAL_FILE_COUNT = "originalFileCount"

# ==================== 컨트롤러 관련 상수 ====================
REDIS_CONNECTION_CONNECTED = "connected"
REDIS_CONNECTION_DISCONNECTED = "disconnected"
VECTORSTORE_TYPE_SIMPLE_REDIS_BACKUP = "simple_with_redis_backup"

# ==================== 메시지 상수 ====================
MSG_REDIS_CONNECTION_CHECK = "Redis 연결 상태 확인"
MSG_REDIS_STATUS_CHECK_FAILED = "Redis 상태 확인 실패: "
MSG_REDIS_VECTORSTORE_DELETE_COMPLETE = "Redis Vector Store 삭제 완료 - 총 %d개 파일 삭제 (RAG: %d개, Embedding: %d개)"
MSG_REDIS_VECTORSTORE_DELETE_FAILED = "Redis Vector Store 삭제 실패: "
MSG_REDIS_VECTORSTORE_BUILD_FAILED = "Redis Vector Store 구축 실패: "
MSG_DOCUMENTS_RELOADED = "문서가 다시 로드되었습니다. (%d개 파일 삭제 후 재로드)"
MSG_DOCUMENT_RELOAD_FAILED = "문서 재로드 실패: "
MSG_REDIS_KEY_DELETE_ERROR = "Redis 키 삭제 중 오류: {}"

# ==================== SourceInfo 관련 상수 ====================
TITLE_PREFIX_BRACKET_START = "["
TITLE_PREFIX_BRACKET_END = "]"
TITLE_PREFIX_MARKDOWN = "# "
TITLE_PREFIX_KOREAN = "제목:"
SCORE_DECIMAL_FORMAT = "#.##"
UNKNOWN_FILENAME = "unknown.txt"
UNKNOWN = "Unknown"

# ==================== 리소스 경로 상수 ====================
RESOURCE_CLASSPATH_PREFIX = "classpath:"

# ==================== toString 포맷 ====================
VECTORSTORE_CONFIG_FORMAT = "VectorStoreConfig{documentsFolder='%s', processingDocumentsFolder='%s', indexName='%s', keyPrefix='%s', embeddingPrefix='%s'}"

# ==================== 메타데이터 관련 상수 ====================
METADATA_CHUNK_ID = "chunk_id"
METADATA_SAVED_AT = "saved_at"
METADATA_DISTANCE = "distance"
METADATA_VECTOR_SCORE = "vector_score"
JSON_KEY_METADATA = "metadata"

# ==================== 로그 메시지 ====================
LOG_DOCUMENT_STATUS_CHECK_FAILED = "문서 상태 확인 실패: {}"
LOG_METADATA_JSON_PARSE_FAILED = "메타데이터 JSON 파싱 실패: {}"
LOG_FILE_LOAD_FAILED = "파일에서 Redis로 데이터 로드 실패: {}"
LOG_UNEXPECTED_ERROR = "예상치 못한 오류: {}"
LOG_DOCUMENT_PROCESS_FAILED = "문서 처리 실패 ({}): {}"
LOG_REDIS_VECTORSTORE_STATUS_FAILED = "Redis 벡터 저장소 상태 확인 실패: {}"
LOG_REDIS_STATUS_CHECK_ERROR = "Redis 상태 확인 중 오류: {}"
