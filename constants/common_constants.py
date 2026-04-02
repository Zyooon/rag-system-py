"""
공통 상수 정의
Java 프로젝트의 CommonConstants와 유사한 기능 제공
"""

# ==================== 파일 확장자 ====================
TXT_EXTENSION = ".txt"
MD_EXTENSION = ".md"
PDF_EXTENSION = ".pdf"
DOCX_EXTENSION = ".docx"

# ==================== 문서 폴더 관련 ====================
DOCUMENTS_FOLDER_NAME = "documents"

# ==================== 시스템 속성 ====================
SYSTEM_USER_DIR = "user.dir"

# ==================== 메타데이터 키 ====================
METADATA_KEY_FILENAME = "filename"
METADATA_KEY_FILEPATH = "filepath"
METADATA_KEY_CHUNK_ID = "chunk_id"
METADATA_KEY_CHUNK_INDEX = "chunk_index"
METADATA_KEY_SAVED_AT = "saved_at"
METADATA_KEY_TITLE = "title"
METADATA_KEY_SECTION_TYPE = "section_type"
METADATA_KEY_START_LINE = "start_line"
METADATA_KEY_HEADER = "header"
METADATA_KEY_HEADER_LINE = "header_line"
METADATA_KEY_BODY_SUMMARY = "body_summary"
METADATA_KEY_H1 = "h1"
METADATA_KEY_H2 = "h2"
METADATA_KEY_H3 = "h3"
METADATA_KEY_HEADING_LEVEL = "heading_level"
METADATA_KEY_PARAGRAPH_INDEX = "paragraph_index"
METADATA_KEY_CHUNK_LENGTH = "chunk_length"
METADATA_KEY_DISTANCE = "distance"
METADATA_KEY_VECTOR_SCORE = "vector_score"
METADATA_KEY_FILE_CHUNK_INDEX = "file_chunk_index"

# ==================== 내용 키 ====================
KEY_CONTENT = "content"
KEY_METADATA = "metadata"
KEY_ERROR = "error"

# ==================== README 관련 ====================
README_FILENAME = "README.md"

# ==================== 기타 공통 상수 ====================
EMPTY_STRING = ""
NEWLINE = "\n"
SPACE = " "

# ==================== 파서 관련 상수 ====================
PARSER_HIERARCHICAL = "Hierarchical"
PARSER_BULLET = "Bullet"
PARSER_SIMPLE_LINE = "SimpleLine"
ERROR_UNKNOWN_PARSER = "알 수 없는 파서: "

# ==================== 정규식 패턴 ====================
PATTERN_HIERARCHICAL = "^(#{1,3}\\s+|\\d+\\.\\s+|\\[.*\\]|제목:)"
PATTERN_BULLET = "^(\\d+\\.\\s+|[-*]\\s+|•\\s+)"

# ==================== Map 키 상수 ====================
KEY_EXISTS = "exists"
KEY_PATH = "path"
KEY_FILE_COUNT = "file_count"
KEY_FILES = "files"
KEY_SAVED_AT = "saved_at"

# ==================== 기본 상수 ====================
DEFAULT_ENCODING = "utf-8"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_CHARSET = "UTF-8"
DEFAULT_SERVER_PORT = 8080

# ==================== 파서 관련 추가 상수 ====================
DEFAULT_PARENT_TITLE = "일반 항목"
SECTION_TYPE_BULLET = "bullet"
SECTION_TYPE_MARKDOWN = "markdown"
SECTION_TYPE_BULLET_WITH_HEADER = "bullet_with_header"
SECTION_TYPE_PARAGRAPH = "paragraph"

# ==================== 제목 레벨 ====================
HEADING_LEVEL_1 = "1"
HEADING_LEVEL_2 = "2"
HEADING_LEVEL_3 = "3"

# ==================== 길이 제한 상수 ====================
MAX_TITLE_LENGTH = 50
TRUNCATED_TITLE_LENGTH = 47
COLON_LIMIT_LENGTH = 30
MIN_TABLE_COLUMNS = 3
MAX_HEADER_LENGTH = 60
MAX_BODY_SUMMARY_LENGTH = 100
TRUNCATED_BODY_SUMMARY_LENGTH = 97
MAX_CHUNK_LENGTH = 500
MIN_CHUNK_LENGTH = 50
MIN_TITLE_LENGTH = 10

# ==================== 기타 상수 ====================
ELLIPSIS = "..."
WILDCARD = "*"

# ==================== 포맷 문자열 ====================
SECTION_FORMAT = "[%s]\n%s"
HIERARCHY_FORMAT = "[%s > %s > %s]\n%s"

# ==================== Markdown 관련 상수 ====================
MARKDOWN_HEADING_PATTERN = "^#{1,6}\\s+.+"
MARKDOWN_HEADING_PATTERN_1_3 = "^#{1,3}\\s+.+"
H1_PREFIX = "# "
H2_PREFIX = "## "
H3_PREFIX = "### "
TITLE_SEPARATOR = " > "
MIN_MARKDOWN_HEADINGS = 2

# ==================== 문장 분리 정규식 ====================
SENTENCE_SPLIT_REGEX = "(?<=[.!?])\\s+"
TITLE_SENTENCE_SPLIT_REGEX = "[.!?]"
PARAGRAPH_SEPARATOR = "\n\n"
