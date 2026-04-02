"""
메시지 상수 정의
Java 프로젝트의 MessageConstants와 유사한 기능 제공
"""

# ==================== 에러 관련 상수 ====================
ERROR_DOCUMENT_LOAD_FAILED = "문서 로드 실패: "
ERROR_VECTORSTORE_INIT_FAILED = "벡터 저장소 초기화 실패: "
ERROR_REDIS_LOAD_FAILED = "Redis 문서 로드 실패: "
ERROR_SEARCH_FAILED = "검색 실패: "
ERROR_INVALID_ARGUMENT = "잘못된 인자: "

# ==================== 에러 타입 ====================
ERROR_TYPE_INTERNAL_SERVER = "Internal Server Error"
ERROR_TYPE_RUNTIME = "Runtime Error"
ERROR_TYPE_RAG_SERVICE = "RAG Service Error"
ERROR_TYPE_INVALID_ARGUMENT = "Invalid Argument"

# ==================== API 응답 키 상수 ====================
RESPONSE_KEY_SUCCESS = "success"
RESPONSE_KEY_TIMESTAMP = "timestamp"
RESPONSE_KEY_ERROR = "error"
RESPONSE_KEY_MESSAGE = "message"
RESPONSE_KEY_PATH = "path"
RESPONSE_KEY_STATUS = "status"

# ==================== 사용자 응답 메시지 ====================
MSG_NO_RELEVANT_INFO = "관련 정보를 찾을 수 없습니다."
MSG_NO_RELIABLE_INFO = "질문과 관련된 충분히 신뢰할 수 있는 정보를 찾을 수 없습니다."
MSG_NO_KNOWLEDGE_BASE = "현재 지식 베이스(Redis)에 저장된 데이터가 없어 답변을 드릴 수 없습니다."

# ==================== 상태 메시지 상수 ====================
MSG_DOCUMENTS_LOADED = "문서가 로드되어 있습니다. (벡터 저장소 기준)"
MSG_DOCUMENTS_NOT_LOADED = "문서가 로드되지 않았습니다."
MSG_VECTORSTORE_MARKED_INITIALIZED = "벡터 저장소가 초기화되었음으로 표시됨"
MSG_FILE_LOAD_SUCCESS = "파일에서 Redis로 문서 로드가 완료되었습니다."
MSG_FILE_LOAD_FAILED_PREFIX = "로드 실패: "
MSG_ERROR_PREFIX = "오류 발생: "

# ==================== 메시지 상수 ====================
MSG_FOLDER_NOT_EXISTS = "폴더가 존재하지 않습니다."
MSG_NO_TEXT_FILES = "폴더에 텍스트 파일이 없습니다."
MSG_FILES_PROCESSED = "총 %d개 파일 처리 완료: %d개 저장, %d개 중복"

# ==================== 성공 메시지 ====================
MSG_VECTORSTORE_DATA_CLEANED = "벡터 저장소 데이터 정리 완료"
MSG_VECTORSTORE_INIT_ERROR = "벡터 저장소 초기화 오류"

# ==================== 시스템 메시지 ====================
MSG_SYSTEM_READY = "시스템이 준비되었습니다"
MSG_SYSTEM_NOT_READY = "시스템이 준비되지 않았습니다"
MSG_DOCUMENTS_LOADED = "문서가 로드되었습니다"
MSG_NO_DOCUMENTS_LOADED = "로드된 문서가 없습니다"

# ==================== 검색 관련 메시지 ====================
MSG_NO_RELEVANT_INFO_FOUND = "관련 정보를 찾을 수 없습니다"
MSG_AI_ANSWER_ERROR = "AI 답변 생성 중 오류: "

# ==================== 데이터 로드 요청 메시지 ====================
LOG_MANUAL_LOAD_REQUEST = "수동으로 데이터를 로드해주세요 (/load-from-files API 호출)."

# ==================== VectorStore 데이터 관련 메시지 ====================
MSG_VECTORSTORE_DATA_CLEANED = "VectorStore 데이터 정리 완료"
MSG_VECTORSTORE_CLEAN_ERROR = "VectorStore 데이터 정리 중 오류: {}"
MSG_VECTORSTORE_INIT_ERROR = "벡터 저장소 초기화 중 오류 발생"

# ==================== Redis 로드 관련 상수 ====================
MSG_REDIS_NO_DOCUMENTS = "Redis에 저장된 문서가 없습니다."
MSG_REDIS_LOAD_SUCCESS = "Redis에서 {}개 문서를 벡터 저장소에 로드했습니다."
MSG_REDIS_LOAD_FAILED = "Redis 문서 로드 실패: {}"
MSG_REDIS_LOAD_ERROR = "Redis 문서 로드 중 오류 발생"

# ==================== 문서 처리 메시지 ====================
LOG_DOCUMENT_PROCESS_FAILED = "문서 처리 실패: {} - {}"

# ==================== README 파일명 ====================
README_FILENAME = "README.md"
