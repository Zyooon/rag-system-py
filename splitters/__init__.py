"""
분할기 모듈
RAG 시스템의 텍스트 분할 기능 관리 모듈

Java 프로젝트의 Splitter 패키지와 유사한 기능 제공
- TextSplitterProcessor: 텍스트 분할 처리 전문 클래스
- TextSplitterConfig: 분할기 설정 관리
- SplitterSettings: 분할 설정 데이터 클래스
- SplitQuality: 분할 품질 평가

분할 전략:
- 기본 분할: 일반 문서 처리용 표준 분할
- 정밀 분할: 검색 정확도를 높인 세분화 분할 (100자 청크)
- 속도 분할: 처리 속도를 높인 대용량 분할 (400자 청크)
"""

from .text_splitter_processor import TextSplitterProcessor
from .text_splitter_config import TextSplitterConfig, SplitterSettings, SplitQuality

__all__ = [
    "TextSplitterProcessor",
    "TextSplitterConfig", 
    "SplitterSettings",
    "SplitQuality"
]
