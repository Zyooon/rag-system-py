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
