"""
프롬프트 모듈
RAG 시스템에서 사용하는 프롬프트 템플릿을 관리하는 모듈

Java 프로젝트의 PromptTemplate와 유사한 기능 제공
다양한 RAG 시나리오에 필요한 프롬프트 템플릿을 제공합니다:
- 기본 검색 답변 생성 프롬프트
- 출처 정보 포함 답변 생성 프롬프트
- 시스템 프롬프트
- RAG 전용 프롬프트
- 전문화된 프롬프트 (기술, 비즈니스)
- 유틸리티 메서드
"""

from .prompt_template import PromptTemplate

__all__ = [
    "PromptTemplate"
]
