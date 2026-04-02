"""
프롬프트 템플릿
Java 프로젝트의 PromptTemplate와 유사한 기능 제공

RAG 시스템에서 사용하는 프롬프트 템플릿을 관리하는 클래스

이 클래스는 다양한 RAG 시나리오에 필요한 프롬프트 템플릿을 제공합니다:
- 기본 검색 답변 생성 프롬프트
- 출처 정보 포함 답변 생성 프롬프트
- 시스템 프롬프트
- RAG 전용 프롬프트

주요 기능:
- 문서 내용 기반 답변 생성
- 출처 정보 참조 표시
- 자연스러운 한국어 답변 유도
- 참조 번호 기반 출처 추적 지원
"""

from typing import Dict, Any
from constants import (
    EMPTY_STRING, NEWLINE, SPACE,
    DEFAULT_PARENT_TITLE, SECTION_TYPE_BULLET,
    SECTION_TYPE_MARKDOWN, SECTION_TYPE_PARAGRAPH
)


class PromptTemplate:
    """RAG 시스템 프롬프트 템플릿 클래스"""
    
    # ==================== 기본 프롬프트 템플릿 ====================
    
    @staticmethod
    def create_search_with_sources_prompt(context_with_indices: str, query: str) -> str:
        """
        출처 정보 포함 답변 생성을 위한 프롬프트 템플릿
        
        이 템플릿은 다음과 같은 특징을 가집니다:
        - 각 정보의 출처를 참조 번호로 표시
        - 한국어 전용 답변 강제
        - 참조 번호 기반 출처 추적 지원
        - 자연스러운 답변 형식 유도
        
        Args:
            context_with_indices: 참조 번호가 포함된 문서 내용
            query: 사용자 질문
            
        Returns:
            포맷팅된 프롬프트 문자열
        """
        prompt = f"""당신은 정보의 근거를 정확히 밝히는 한국어 AI 어시스턴트입니다.
답변의 신뢰도를 위해 아래 지침을 엄격히 따르세요.

[중요 지침]
1. 모든 답변 문장은 [문서 내용]의 특정 번호 섹션에 근거해야 합니다.
2. 답변 문장이 끝날 때마다 해당 정보의 근거가 된 문서의 번호를 [번호] 형태로 붙이세요. (예: ...입니다[1].)
3. 문장을 지나치게 의역하지 마세요. 문서에 사용된 핵심 표현을 그대로 사용할수록 좋습니다.
4. 반드시 한국어로만 답변하세요.

[답변 형식 예시]
- 거꾸로 흐르는 시계는 사용자가 잠들었을 때만 시간을 정확히 맞춥니다[11].
- 맛있는 신문을 욕조물에 띄워두는 이유는 글자가 지워지지 않게 하기 위함입니다[15].

[문서 내용]
{context_with_indices}

[질문]
{query}

답변:
"""
        return prompt
    
    @staticmethod
    def create_system_prompt() -> str:
        """
        시스템 프롬프트 생성
        
        Returns:
            시스템 프롬프트
        """
        return """당신은 RAG(Retrieval-Augmented Generation) 시스템의 AI 도우미입니다.
주어진 문서를 바탕으로 정확하고 유용한 정보를 제공하세요.

답변 원칙:
1. 제공된 문서 내용만 기반으로 답변
2. 참조 번호를 사용하여 출처 명시
3. 문서에 없는 정보는 "모르겠습니다" 또는 "문서에 관련 정보가 없습니다"로 답변
4. 명확하고 간결한 한국어로 답변
5. 필요시 여러 문서의 정보를 종합하여 답변"""
    
    @staticmethod
    def create_rag_prompt(context: str, question: str) -> str:
        """
        RAG 전용 프롬프트 생성
        
        Args:
            context: 검색된 문서 컨텍스트
            question: 사용자 질문
            
        Returns:
            RAG 프롬프트
        """
        return f"""다음은 검색된 문서 내용입니다:

{context}

위 문서를 바탕으로 다음 질문에 답변해주세요: {question}

답변 요구사항:
- 문서 내용만 기반으로 답변
- 참조 번호로 출처 표시
- 정확한 정보 제공
- 간결한 한국어 답변"""
    
    # ==================== 고급 프롬프트 템플릿 ====================
    
    @staticmethod
    def create_simple_search_prompt(context: str, query: str) -> str:
        """
        간단한 검색용 프롬프트 생성
        
        Args:
            context: 검색된 문서 컨텍스트
            query: 사용자 질문
            
        Returns:
            생성된 프롬프트
        """
        prompt = f"""당신은 주어진 문서를 바탕으로 질문에 답변하는 도우미입니다.

다음 문서를 사용하여 질문에 답변하세요. 문서에 답변이 없다면 "문서에 관련 정보가 없습니다"라고 말하세요.

문서:
{context}

질문: {query}

답변 시 참조 번호를 사용하여 출처를 명시해주세요. 예: "이 정보는 [1]번 문서에 따르면..."

답변:
"""
        return prompt
    
    @staticmethod
    def create_detailed_search_prompt(context: str, query: str, sources_info: str = "") -> str:
        """
        상세한 검색용 프롬프트 생성
        
        Args:
            context: 검색된 문서 컨텍스트
            query: 사용자 질문
            sources_info: 출처 정보 (선택사항)
            
        Returns:
            상세 프롬프트
        """
        prompt = f"""당신은 전문적인 정보 검색 및 분석 AI 어시스턴트입니다.
주어진 문서를 철저히 분석하여 정확하고 상세한 답변을 제공하세요.

[분석 지침]
1. 문서의 내용을 정확히 이해하고 핵심 정보를 추출하세요
2. 여러 문서의 정보를 종합하여 일관된 답변을 구성하세요
3. 각 정보의 출처를 명확하게 표시하세요
4. 가능한 한 구체적이고 실용적인 정보를 제공하세요

[문서 내용]
{context}

{sources_info}

[질문]
{query}

[답변 형식]
1. 먼저 핵심 답변을 제시하세요
2. 그 다음 근거가 되는 문서 내용을 참조 번호와 함께 설명하세요
3. 필요시 추가적인 배경 정보나 관련 내용을 보충하세요
4. 모든 정보는 반드시 제공된 문서에 근거해야 합니다

답변:
"""
        return prompt
    
    @staticmethod
    def create_summary_prompt(context: str, topic: str) -> str:
        """
        문서 요약용 프롬프트 생성
        
        Args:
            context: 요약할 문서 내용
            topic: 요약 주제
            
        Returns:
            요약 프롬프트
        """
        return f"""다음 문서를 '{topic}'에 초점을 맞춰 요약해주세요.

[요약 지침]
1. 문서의 핵심 내용을 간결하게 정리하세요
2. 중요한 정보는 누락하지 마세요
3. 불필요한 세부 정보는 제외하세요
4. 명확하고 이해하기 쉽게 구성하세요

[문서 내용]
{context}

[요약]
"""
    
    @staticmethod
    def create_comparison_prompt(context1: str, context2: str, query: str) -> str:
        """
        두 문서 비교용 프롬프트 생성
        
        Args:
            context1: 첫 번째 문서 내용
            context2: 두 번째 문서 내용
            query: 비교 질문
            
        Returns:
            비교 프롬프트
        """
        return f"""다음 두 문서를 비교 분석하여 질문에 답변하세요.

[문서 1]
{context1}

[문서 2]
{context2}

[질문]
{query}

[비교 분석 지침]
1. 각 문서의 특징을 명확히 파악하세요
2. 공통점과 차이점을 체계적으로 비교하세요
3. 각 문서의 출처를 명시하세요
4. 객관적인 근거를 기반으로 비교结论을 도출하세요

답변:
"""
    
    # ==================== 전문화된 프롬프트 템플릿 ====================
    
    @staticmethod
    def create_technical_prompt(context: str, query: str) -> str:
        """
        기술 문서 전용 프롬프트
        
        Args:
            context: 기술 문서 내용
            query: 기술 질문
            
        Returns:
            기술 프롬프트
        """
        return f"""당신은 기술 문서 전문가입니다.
주어진 기술 문서를 바탕으로 정확하고 전문적인 답변을 제공하세요.

[기술 문서]
{context}

[기술 질문]
{query}

[답변 요구사항]
1. 기술적으로 정확한 정보 제공
2. 전문 용어를 올바르게 사용
3. 구체적인 기술 사양이나 매개변수 포함
4. 참조 번호로 근거 명시
5. 실용적인 기술 정보 제공

답변:
"""
    
    @staticmethod
    def create_business_prompt(context: str, query: str) -> str:
        """
        비즈니스 문서 전용 프롬프트
        
        Args:
            context: 비즈니스 문서 내용
            query: 비즈니스 질문
            
        Returns:
            비즈니스 프롬프트
        """
        return f"""당신은 비즈니스 분석 전문가입니다.
주어진 비즈니스 문서를 바탕으로 실용적인 비즈니스 인사이트를 제공하세요.

[비즈니스 문서]
{context}

[비즈니스 질문]
{query}

[답변 요구사항]
1. 비즈니스 관점에서 실용적인 정보 제공
2. 구체적인 데이터나 수치 기반으로 설명
3. 비즈니스 의사결정에 도움이 되는 정보 포함
4. 참조 번호로 근거 명시
5. 명확하고 간결한 비즈니스 용어 사용

답변:
"""
    
    # ==================== 유틸리티 메서드 ====================
    
    @staticmethod
    def format_context_with_sources(documents: list) -> str:
        """
        문서 목록을 참조 번호가 포함된 컨텍스트로 포맷팅
        
        Args:
            documents: 문서 리스트 (각 문서는 text, metadata 포함)
            
        Returns:
            포맷팅된 컨텍스트
        """
        context_parts = []
        
        for i, doc in enumerate(documents):
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            filename = metadata.get("filename", f"문서{i+1}")
            
            context_part = f"[{i+1}] 파일명: {filename}\n내용: {text}\n"
            context_parts.append(context_part)
        
        return NEWLINE.join(context_parts)
    
    @staticmethod
    def extract_key_information(context: str, max_length: int = 1000) -> str:
        """
        컨텍스트에서 핵심 정보 추출
        
        Args:
            context: 원본 컨텍스트
            max_length: 최대 길이
            
        Returns:
            추출된 핵심 정보
        """
        if len(context) <= max_length:
            return context
        
        # 문장 단위로 분리하여 중요한 부분 선택
        sentences = context.split('. ')
        key_sentences = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) + 2 <= max_length:
                key_sentences.append(sentence.strip())
                current_length += len(sentence) + 2
            else:
                break
        
        return '. '.join(key_sentences) + '.'
    
    @staticmethod
    def validate_prompt(prompt: str) -> bool:
        """
        프롬프트 유효성 검사
        
        Args:
            prompt: 검사할 프롬프트
            
        Returns:
            유효성 여부
        """
        if not prompt or len(prompt.strip()) == 0:
            return False
        
        # 필수 키워드 확인
        required_keywords = ['문서', '질문', '답변']
        for keyword in required_keywords:
            if keyword not in prompt:
                return False
        
        return True
