"""
텍스트 분할기 설정 관리
Java 프로젝트의 TextSplitterConfig와 유사한 기능 제공

이 클래스는 텍스트 분할기의 모든 설정 상수를 관리합니다:
- 분할 크기 - 청크의 최대/최소 크기 설정
- 임베딩 기준 - 벡터화를 위한 최소 길이 기준
- 수량 제한 - 생성할 청크의 최대 수량
- 구분자 - 문장 분리를 위한 구분자 문자들

설정 카테고리:
- 기본 설정: 일반 문서 처리용 표준 설정
- 정밀 검색: 더 세분화된 청크를 위한 설정
- 속도 최적화: 더 큰 청크를 위한 설정
"""

from dataclasses import dataclass
from typing import List


class TextSplitterConfig:
    """텍스트 분할기 설정 관리 클래스"""
    
    # ==================== 기본 설정 ====================
    
    # 기본 청크 크기 (토큰 단위)
    DEFAULT_CHUNK_SIZE = 300
    
    # 최소 청크 문자 수
    DEFAULT_MIN_CHUNK_SIZE_CHARS = 50
    
    # 임베딩 최소 길이
    DEFAULT_MIN_CHUNK_LENGTH_TO_EMBED = 20
    
    # 최대 청크 수
    DEFAULT_MAX_NUM_CHUNKS = 500
    
    # 구분자 유지 여부
    DEFAULT_KEEP_SEPARATOR = True
    
    # 기본 구분자 문자들
    DEFAULT_PUNCTUATION_MARKS = ['.', '\n', ']', '-', '|']
    
    # ==================== 정밀 검색 설정 ====================
    
    # 정밀 검색용 청크 크기 (더 세분화)
    PRECISE_CHUNK_SIZE = 100
    
    # 정밀 검색용 최소 청크 문자 수 (더 짧음)
    PRECISE_MIN_CHUNK_SIZE_CHARS = 30
    
    # 정밀 검색용 임베딩 최소 길이 (더 낮음)
    PRECISE_MIN_CHUNK_LENGTH_TO_EMBED = 10
    
    # 정밀 검색용 최대 청크 수 (더 많음)
    PRECISE_MAX_NUM_CHUNKS = 800
    
    # ==================== 속도 최적화 설정 ====================
    
    # 속도 최적화용 청크 크기 (더 큼)
    SPEED_CHUNK_SIZE = 400
    
    # 속도 최적화용 최소 청크 문자 수 (더 김)
    SPEED_MIN_CHUNK_SIZE_CHARS = 100
    
    # 속도 최적화용 임베딩 최소 길이
    SPEED_MIN_CHUNK_LENGTH_TO_EMBED = 10
    
    # 속도 최적화용 최대 청크 수 (더 많음)
    SPEED_MAX_NUM_CHUNKS = 1000
    
    # ==================== 문서 길이 기준 ====================
    
    # 긴 문서 기준 길이 (800자 이상이면 분할 대상)
    LONG_DOCUMENT_THRESHOLD = 800
    
    # ==================== 설정 조합 ====================
    
    @staticmethod
    def get_default_settings() -> 'SplitterSettings':
        """기본 설정 조합을 반환"""
        return SplitterSettings(
            chunk_size=TextSplitterConfig.DEFAULT_CHUNK_SIZE,
            min_chunk_size_chars=TextSplitterConfig.DEFAULT_MIN_CHUNK_SIZE_CHARS,
            min_chunk_length_to_embed=TextSplitterConfig.DEFAULT_MIN_CHUNK_LENGTH_TO_EMBED,
            max_num_chunks=TextSplitterConfig.DEFAULT_MAX_NUM_CHUNKS,
            keep_separator=TextSplitterConfig.DEFAULT_KEEP_SEPARATOR,
            punctuation_marks=TextSplitterConfig.DEFAULT_PUNCTUATION_MARKS
        )
    
    @staticmethod
    def get_precise_search_settings() -> 'SplitterSettings':
        """정밀 검색 설정 조합을 반환"""
        return SplitterSettings(
            chunk_size=TextSplitterConfig.PRECISE_CHUNK_SIZE,
            min_chunk_size_chars=TextSplitterConfig.PRECISE_MIN_CHUNK_SIZE_CHARS,
            min_chunk_length_to_embed=TextSplitterConfig.PRECISE_MIN_CHUNK_LENGTH_TO_EMBED,
            max_num_chunks=TextSplitterConfig.PRECISE_MAX_NUM_CHUNKS,
            keep_separator=TextSplitterConfig.DEFAULT_KEEP_SEPARATOR,
            punctuation_marks=TextSplitterConfig.DEFAULT_PUNCTUATION_MARKS
        )
    
    @staticmethod
    def get_speed_optimization_settings() -> 'SplitterSettings':
        """속도 최적화 설정 조합을 반환"""
        return SplitterSettings(
            chunk_size=TextSplitterConfig.SPEED_CHUNK_SIZE,
            min_chunk_size_chars=TextSplitterConfig.SPEED_MIN_CHUNK_SIZE_CHARS,
            min_chunk_length_to_embed=TextSplitterConfig.SPEED_MIN_CHUNK_LENGTH_TO_EMBED,
            max_num_chunks=TextSplitterConfig.SPEED_MAX_NUM_CHUNKS,
            keep_separator=TextSplitterConfig.DEFAULT_KEEP_SEPARATOR,
            punctuation_marks=TextSplitterConfig.DEFAULT_PUNCTUATION_MARKS
        )


@dataclass
class SplitterSettings:
    """분할기 설정을 담는 데이터클래스"""
    chunk_size: int
    min_chunk_size_chars: int
    min_chunk_length_to_embed: int
    max_num_chunks: int
    keep_separator: bool
    punctuation_marks: List[str]
    
    def __str__(self) -> str:
        return (f"SplitterSettings{{chunk_size={self.chunk_size}, "
                f"min_chars={self.min_chunk_size_chars}, "
                f"min_embed={self.min_chunk_length_to_embed}, "
                f"max_chunks={self.max_num_chunks}, "
                f"keep_sep={self.keep_separator}}}")


class SplitQuality:
    """분할 품질 평가 결과"""
    
    def __init__(self, score: float, message: str, is_optimal: bool):
        self.score = score
        self.message = message
        self.is_optimal = is_optimal
    
    def __str__(self) -> str:
        return (f"SplitQuality{{score={self.score:.1f}, "
                f"optimal={self.is_optimal}, "
                f"message='{self.message}'}}")
