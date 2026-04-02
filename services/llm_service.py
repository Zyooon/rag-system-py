"""
LLM 서비스
Ollama 모델 연결 및 답변 생성
"""

import asyncio
from typing import Optional, Dict, Any
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from config import settings


class LLMService:
    """LLM 서비스 클래스"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model_name = settings.ollama_model
        self.chat_model: Optional[ChatOllama] = None
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Ollama 모델 초기화"""
        try:
            self.chat_model = ChatOllama(
                base_url=self.base_url,
                model=self.model_name,
                temperature=0.1,  # RAG에는 낮은 온도가 적합
                timeout=30  # 타임아웃 설정
            )
            print(f"Ollama 모델 초기화 완료: {self.model_name} ({self.base_url})")
        except Exception as e:
            print(f"Ollama 모델 초기화 실패: {e}")
            self.chat_model = None
    
    async def generate_answer(self, prompt: str) -> str:
        """
        프롬프트를 기반으로 답변 생성
        
        Args:
            prompt: LLM에 전달할 프롬프트
            
        Returns:
            생성된 답변
        """
        if not self.chat_model:
            return "LLM 모델이 초기화되지 않았습니다. Ollama 서버를 확인해주세요."
        
        try:
            # 비동기 호출을 위해 asyncio.to_thread 사용
            response = await asyncio.to_thread(
                self.chat_model.invoke,
                prompt
            )
            
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            print(f"LLM 답변 생성 실패: {e}")
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def generate_answer_with_messages(self, system_prompt: str, user_prompt: str) -> str:
        """
        시스템 프롬프트와 사용자 프롬프트로 답변 생성
        
        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            
        Returns:
            생성된 답변
        """
        if not self.chat_model:
            return "LLM 모델이 초기화되지 않았습니다. Ollama 서버를 확인해주세요."
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # 비동기 호출
            response = await asyncio.to_thread(
                self.chat_model.invoke,
                messages
            )
            
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            print(f"LLM 답변 생성 실패: {e}")
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def health_check(self) -> Dict[str, Any]:
        """
        LLM 서비스 상태 확인
        
        Returns:
            상태 정보
        """
        try:
            if not self.chat_model:
                return {
                    "status": "unhealthy",
                    "error": "LLM 모델이 초기화되지 않음",
                    "model": self.model_name,
                    "base_url": self.base_url
                }
            
            # 간단한 테스트 질문으로 응답 확인
            test_response = await self.generate_answer("안녕하세요")
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "base_url": self.base_url,
                "test_response": test_response[:100] + "..." if len(test_response) > 100 else test_response
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.model_name,
                "base_url": self.base_url
            }
    
    def is_available(self) -> bool:
        """
        LLM 서비스 사용 가능 여부 확인
        
        Returns:
            사용 가능 여부
        """
        return self.chat_model is not None
    
    def get_model_info(self) -> Dict[str, str]:
        """
        모델 정보 반환
        
        Returns:
            모델 정보
        """
        return {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "provider": "Ollama",
            "status": "available" if self.is_available() else "unavailable"
        }
