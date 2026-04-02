"""
프롬프트 템플릿
Java 프로젝트의 PromptTemplate와 유사한 기능 제공
"""

from typing import Dict, Any


class PromptTemplate:
    """프롬프트 템플릿 클래스"""
    
    @staticmethod
    def create_search_with_sources_prompt(context: str, query: str) -> str:
        """
        검색용 프롬프트 생성
        
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
