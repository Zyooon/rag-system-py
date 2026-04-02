"""
검색 및 답변 생성 서비스
Java 프로젝트의 SearchService와 유사한 기능 제공
"""

import re
import asyncio
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

from repositories import ChromaVectorStore, RedisDocumentRepository
from dto import SourceInfo
from prompts import PromptTemplate
from services import LLMService
from config import settings
from constants import (
    MAP_KEY_ANSWER, MAP_KEY_SOURCES, METADATA_KEY_FILENAME, 
    DEFAULT_ENCODING, MSG_NO_KNOWLEDGE_BASE, MSG_NO_RELEVANT_INFO,
    MSG_NO_RELEVANT_INFO_FOUND, MSG_AI_ANSWER_ERROR
)


class SearchService:
    """검색 및 답변 생성 전담 서비스"""
    
    def __init__(self):
        self.vector_store = ChromaVectorStore()
        self.redis_document_repository = RedisDocumentRepository()
        self.llm_service = LLMService()
        self.similarity_threshold = settings.search_threshold
        self.max_search_results = settings.search_max_results
    
    async def search_and_answer_with_sources(self, query: str) -> Dict[str, Any]:
        """
        사용자 질문에 대해 RAG를 통해 답변을 생성하고 출처 정보도 함께 반환
        
        Args:
            query: 사용자 질문
            
        Returns:
            답변과 출처 정보가 포함된 결과 맵
        """
        # 벡터 저장소에서 유사 문서 검색
        relevant_documents = await self.vector_store.similarity_search(
            query, 
            k=self.max_search_results,
            threshold=self.similarity_threshold
        )
        
        if not relevant_documents:
            return {
                MAP_KEY_ANSWER: MSG_NO_KNOWLEDGE_BASE,
                MAP_KEY_SOURCES: SourceInfo()
            }
        
        # 유사도 필터링 및 정렬
        filtered_docs = self._filter_and_sort_documents(relevant_documents)
        
        if not filtered_docs:
            return {
                MAP_KEY_ANSWER: MSG_NO_RELEVANT_INFO,
                MAP_KEY_SOURCES: SourceInfo()
            }
        
        # 출처 정보 추출
        sources = self._extract_source_info(filtered_docs)
        
        # 컨텍스트 생성
        context = self._build_context_with_indices(filtered_docs)
        
        if not context.strip():
            return {
                MAP_KEY_ANSWER: MSG_NO_RELEVANT_INFO_FOUND,
                MAP_KEY_SOURCES: SourceInfo()
            }
        
        # 프롬프트 생성 및 LLM 호출
        prompt = PromptTemplate.create_search_with_sources_prompt(context, query)
        
        try:
            answer = await self.llm_service.generate_answer(prompt)
            best_source = self._find_best_matching_source(answer, filtered_docs, sources)
            
            return {
                MAP_KEY_ANSWER: answer,
                MAP_KEY_SOURCES: best_source
            }
        except Exception as e:
            best_source = sources[0] if sources else SourceInfo()
            return {
                MAP_KEY_ANSWER: MSG_AI_ANSWER_ERROR + str(e),
                MAP_KEY_SOURCES: best_source
            }
    
    def _filter_and_sort_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        유사도 필터링 및 정렬
        
        Args:
            documents: 필터링할 문서 리스트
            
        Returns:
            필터링된 문서 리스트
        """
        filtered_docs = []
        
        for doc in documents:
            similarity_score = doc.get("similarity_score", 0.0)
            
            if similarity_score >= self.similarity_threshold:
                filtered_docs.append(doc)
        
        # 유사도 기준 내림차순 정렬
        filtered_docs.sort(
            key=lambda x: x.get("similarity_score", 0.0), 
            reverse=True
        )
        
        # 최대 결과 수 제한
        return filtered_docs[:self.max_search_results]
    
    def _extract_source_info(self, documents: List[Dict[str, Any]]) -> List[SourceInfo]:
        """
        문서에서 출처 정보 추출
        
        Args:
            documents: 출처 정보를 추출할 문서 리스트
            
        Returns:
            출처 정보 리스트
        """
        processed_chunks = set()
        sources = []
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            filename = metadata.get("filename", "unknown")
            similarity_score = doc.get("similarity_score", 0.0)
            content = doc.get("text", "")
            
            # README 파일 제외
            if filename.lower() == "readme":
                continue
            
            # 중복 청크 제거
            content_hash = str(hash(content))
            unique_key = f"{filename}|{similarity_score}|{content_hash}"
            
            if unique_key in processed_chunks:
                continue
            
            processed_chunks.add(unique_key)
            
            # Redis에서 원본 출처 정보 찾기
            try:
                source_info = asyncio.run(self._find_source_info_from_redis(content))
            except Exception as e:
                print(f"Redis 출처 정보 찾기 실패: {e}")
                source_info = self._create_source_info_from_document(doc)
            
            sources.append(source_info)
            
            # 최대 5개 출처 정보 제한
            if len(sources) >= 5:
                break
        
        return sources
    
    async def _find_source_info_from_redis(self, chunk_content: str) -> SourceInfo:
        """
        Redis에서 원본 출처 정보 찾기
        
        Args:
            chunk_content: 검색된 청크 내용
            
        Returns:
            출처 정보
        """
        source_info = SourceInfo(filename="unknown", content_preview="", similarity_score=0.0)
        
        try:
            # Redis에서 모든 문서 가져오기
            all_docs = await self.redis_document_repository.get_all_document_keys()
            
            for key in all_docs:
                doc = await self.redis_document_repository.get_document(key)
                if not doc:
                    continue
                
                original_content = doc.get("text", "")
                
                # 검색된 청크 내용이 Redis 원본 본문에 포함되어 있는지 확인
                if chunk_content.strip() in original_content:
                    metadata = doc.get("metadata", {})
                    actual_name = metadata.get("filename", "unknown")
                    
                    source_info.filename = actual_name
                    source_info.content_preview = chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content
                    return source_info
        
        except Exception as e:
            print(f"Redis 원본 매칭 중 오류 발생: {e}")
        
        return source_info
    
    def _create_source_info_from_document(self, doc: Dict[str, Any]) -> SourceInfo:
        """
        문서에서 출처 정보 생성
        
        Args:
            doc: 문서 데이터
            
        Returns:
            출처 정보
        """
        metadata = doc.get("metadata", {})
        content = doc.get("text", "")
        
        return SourceInfo(
            filename=metadata.get("filename", "unknown"),
            content_preview=content[:200] + "..." if len(content) > 200 else content,
            similarity_score=doc.get("similarity_score", 0.0)
        )
    
    def _build_context_with_indices(self, documents: List[Dict[str, Any]]) -> str:
        """
        참조 번호가 포함된 컨텍스트 생성
        
        Args:
            documents: 컨텍스트를 생성할 문서 리스트
            
        Returns:
            생성된 컨텍스트
        """
        context_parts = []
        
        for i, doc in enumerate(documents):
            metadata = doc.get("metadata", {})
            filename = metadata.get("filename", "unknown")
            content = doc.get("text", "")
            
            context_part = f"[{i + 1}] 파일명: {filename}\n내용: {content}\n"
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _create_search_with_sources_prompt(self, context: str, query: str) -> str:
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
"""
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """
        LLM 호출 (이전 메서드와 호환성)
        
        Args:
            prompt: LLM에 전달할 프롬프트
            
        Returns:
            LLM 응답
        """
        return await self.llm_service.generate_answer(prompt)
    
    def _find_best_matching_source(self, answer: str, documents: List[Dict[str, Any]], sources: List[SourceInfo]) -> SourceInfo:
        """
        답변의 참조 번호를 기반으로 정확한 출처 찾기
        
        Args:
            answer: LLM 답변
            documents: 관련 문서 리스트
            sources: 출처 정보 리스트
            
        Returns:
            가장 적절한 출처 정보
        """
        # 참조 번호 추출
        pattern = re.compile(r'\[(\d+)\]')
        matches = pattern.findall(answer)
        ref_numbers = set(int(num) for num in matches)
        
        best_source = SourceInfo(filename="unknown", content_preview="", similarity_score=0.0)
        
        # sources 리스트가 비어있으면 첫 번째 documents에서 SourceInfo 생성
        if not sources:
            if documents:
                best_source = self._create_source_info_from_document(documents[0])
            return best_source
        
        # 참조 번호에 해당하는 출처 찾기
        for ref_num in ref_numbers:
            doc_index = ref_num - 1
            if 0 <= doc_index < len(sources):
                source_info = sources[doc_index]
                
                if source_info.filename and source_info.filename != "unknown":
                    best_source = source_info
                    break
        
        # 적절한 출처를 찾지 못했다면 sources의 첫 번째 항목 사용
        if best_source.filename == "unknown" and sources:
            best_source = sources[0]
        
        return best_source
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Redis에 저장된 모든 문서를 조회하는 디버깅 메서드
        
        Returns:
            모든 문서 리스트
        """
        try:
            all_keys = await self.redis_document_repository.get_all_document_keys()
            documents = []
            
            for key in all_keys:
                doc = await self.redis_document_repository.get_document(key)
                if doc:
                    documents.append({
                        "id": key,
                        "filename": doc.get("metadata", {}).get("filename", "unknown"),
                        "content": doc.get("text", "")[:200] + "...",
                        "metadata": doc.get("metadata", {})
                    })
            
            return documents
        
        except Exception as e:
            print(f"문서 조회 실패: {e}")
            return []
