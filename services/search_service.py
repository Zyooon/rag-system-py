"""
검색 및 답변 생성 서비스
Java 프로젝트의 SearchService와 유사한 기능 제공
시맨틱 청킹과 리랭킹으로 검색 품질 향상
"""

import re
import asyncio
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

from repositories import RedisDocumentRepository, RedisSearchRepository
from dto import SourceInfo
from prompts import PromptTemplate
from config import settings
from constants import (
    MAP_KEY_ANSWER, MAP_KEY_SOURCES, METADATA_KEY_FILENAME, 
    DEFAULT_ENCODING, MSG_NO_KNOWLEDGE_BASE, MSG_NO_RELEVANT_INFO,
    MSG_NO_RELEVANT_INFO_FOUND, MSG_AI_ANSWER_ERROR
)


class SearchService:
    """검색 및 답변 생성 전담 서비스"""
    
    def __init__(self):
        self.redis_search_repository = RedisSearchRepository()
        self.redis_document_repository = RedisDocumentRepository()
        self.llm_service = None
        
        # 시맨틱 청킹 서비스
        if settings.enable_semantic_chunking:
            from .semantic_chunking_service import SemanticChunkingService
            self.semantic_chunking_service = SemanticChunkingService()
            print("✅ 시맨틱 청킹 서비스 활성화")
        else:
            self.semantic_chunking_service = None
            print("❌ 시맨틱 청킹 서비스 비활성화")
        
        # 리랭킹 서비스
        if settings.enable_reranking:
            from .reranking_service import RerankingService
            self.reranking_service = RerankingService()
            print("✅ 리랭킹 서비스 활성화")
        else:
            self.reranking_service = None
            print("❌ 리랭킹 서비스 비활성화")
        
        # LLM 서비스 초기화 (순환 임포트 방지)
        self._initialize_llm_service()
        
        self.similarity_threshold = 0.1  # 키워드 검색을 위해 임계값 낮춤
        self.max_search_results = settings.search_max_results * 2  # 검색 범위 확대
    
    def _initialize_llm_service(self):
        """LLM 서비스 초기화 (순환 임포트 방지)"""
        try:
            from services import LLMService
            self.llm_service = LLMService()
        except ImportError:
            print("LLM 서비스를 초기화할 수 없습니다")
            self.llm_service = None
    
    async def search_documents(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        문서 검색 (메타데이터 필터링 지원)
        
        Args:
            query: 검색 쿼리
            filters: 메타데이터 필터링 조건
            
        Returns:
            검색된 문서 리스트
        """
        try:
            print(f"🔍 문서 검색 시작: '{query}'")
            if filters:
                print(f"🎯 검색 필터: {filters}")
            
            # 1. ChromaDB에서 시맨틱 검색 (필터링 적용)
            chroma_results = await self.vector_store.similarity_search(
                query, 
                k=settings.search_top_k,
                threshold=settings.search_threshold,
                filters=filters
            )
            
            # 2. Redis에서 키워드 검색 (필터링 적용)
            redis_results = await self.redis_search_repository.get_all_documents(filters)
            
            # 3. 결과 병합 및 중복 제거
            all_results = self._merge_search_results(chroma_results, redis_results)
            
            print(f"📊 검색 결과: ChromaDB {len(chroma_results)}개, Redis {len(redis_results)}개 → 총 {len(all_results)}개")
            return all_results
            
        except Exception as e:
            print(f"문서 검색 실패: {e}")
            return []
    
    def _merge_search_results(self, chroma_results: List[Dict[str, Any]], 
                            redis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        ChromaDB와 Redis 검색 결과 병합
        
        Args:
            chroma_results: ChromaDB 검색 결과
            redis_results: Redis 검색 결과
            
        Returns:
            병합된 검색 결과
        """
        merged_results = []
        seen_texts = set()
        
        # ChromaDB 결과 우선 추가 (이미 유사도 점수 있음)
        for result in chroma_results:
            text = result.get('text', '')
            if text and text not in seen_texts:
                merged_results.append(result)
                seen_texts.add(text)
        
        # Redis 결과 추가 (중복 제외)
        for result in redis_results:
            text = result.get('text', '')
            if text and text not in seen_texts:
                # 키워드 유사도 점수 계산
                query = ""  # TODO: query 전달 방법 개선
                score = self._calculate_keyword_similarity(query, text)
                
                result['score'] = score
                result['similarity_score'] = score
                merged_results.append(result)
                seen_texts.add(text)
        
        # 점수순 정렬
        merged_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        return merged_results[:self.max_search_results]
    
    def _calculate_keyword_similarity(self, query: str, text: str) -> float:
        """
        키워드 기반 유사도 계산
        
        Args:
            query: 검색 쿼리
            text: 문서 텍스트
            
        Returns:
            유사도 점수 (0.0 - 1.0)
        """
        query_words = set(query.split())
        text_words = set(text.split())
        
        if not query_words:
            return 0.0
        
        # 교집합 단어 수 / 전체 쿼리 단어 수
        common_words = query_words.intersection(text_words)
        similarity = len(common_words) / len(query_words)
        
        return similarity
    
    async def search_and_answer_with_sources(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        사용자 질문에 대해 RAG를 통해 답변을 생성하고 출처 정보도 함께 반환
        메타데이터 필터링 지원
        
        Args:
            query: 사용자 질문
            filters: 메타데이터 필터링 조건
            
        Returns:
            답변과 출처 정보가 포함된 결과 맵
        """
        print(f"🔍 검색 시작: '{query}'")
        if filters:
            print(f"🎯 필터링 조건: {filters}")
        
        # 1. 1차 검색 (기존 방식 + 필터링)
        initial_documents = await self.search_documents(query, filters)
        print(f"📊 1차 검색 결과: {len(initial_documents)}개 문서")
        
        if not initial_documents:
            return {
                MAP_KEY_ANSWER: MSG_NO_KNOWLEDGE_BASE,
                MAP_KEY_SOURCES: SourceInfo(filename="unknown", content="", similarity_score=0.0)
            }
        
        # 2. 리랭킹 적용
        if self.reranking_service:
            reranked_documents = await self.reranking_service.rerank_documents(query, initial_documents)
            print(f"🎯 리랭킹 결과: {len(reranked_documents)}개 문서")
            
            # 리랭킹 통계 출력
            stats = await self.reranking_service.get_reranking_stats(query, initial_documents)
            print(f"📈 리랭킹 통계: 평균 점수 {stats.get('reranked_avg_score', 0):.3f}")
        else:
            reranked_documents = initial_documents
            print("⚠️ 리랭킹 스킵")
        
        # 3. 유사도 필터링 및 정렬
        filtered_docs = self._filter_and_sort_documents(reranked_documents)
        
        if not filtered_docs:
            return {
                MAP_KEY_ANSWER: MSG_NO_RELEVANT_INFO,
                MAP_KEY_SOURCES: SourceInfo(filename="unknown", content="", similarity_score=0.0)
            }
        
        # 4. 출처 정보 추출
        sources = self._extract_source_info(filtered_docs)
        
        # 5. 컨텍스트 생성
        context = self._build_context_with_indices(filtered_docs)
        
        if not context.strip():
            return {
                MAP_KEY_ANSWER: MSG_NO_RELEVANT_INFO_FOUND,
                MAP_KEY_SOURCES: SourceInfo(filename="unknown", content="", similarity_score=0.0)
            }
        
        # 6. 프롬프트 생성 및 LLM 호출
        prompt = PromptTemplate.create_search_with_sources_prompt(context, query)
        
        try:
            if self.llm_service is None:
                return {
                    MAP_KEY_ANSWER: "LLM 서비스가 초기화되지 않았습니다",
                    MAP_KEY_SOURCES: SourceInfo(filename="unknown", content="", similarity_score=0.0)
                }
            
            answer = await self.llm_service.generate_answer(prompt)
            
            # 7. 최적 출처 선택 (리랭킹 점수 고려)
            best_source = self._find_best_matching_source_with_reranking(answer, filtered_docs, sources)
            
            print(f"✅ 최종 출처: {best_source.filename} (점수: {best_source.similarity_score:.3f})")
            
            return {
                MAP_KEY_ANSWER: answer,
                MAP_KEY_SOURCES: best_source
            }
        except Exception as e:
            best_source = sources[0] if sources else SourceInfo(filename="unknown", content="", similarity_score=0.0)
            return {
                MAP_KEY_ANSWER: MSG_AI_ANSWER_ERROR + str(e),
                MAP_KEY_SOURCES: best_source
            }
    
    def _find_best_matching_source_with_reranking(self, answer: str, documents: List[Dict[str, Any]], sources: List[SourceInfo]) -> SourceInfo:
        """
        리랭킹 점수를 고려한 최적 출처 선택
        
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
        
        best_source = SourceInfo(filename="unknown", content="", similarity_score=0.0)
        
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
        
        # 적절한 출처를 찾지 못했다면 리랭킹 점수가 가장 높은 출처 선택
        if best_source.filename == "unknown" and sources:
            # 리랭킹 점수가 있는 문서 찾기
            best_rerank_source = None
            best_rerank_score = 0.0
            
            for source in sources:
                # 해당 문서의 리랭킹 점수 찾기
                for doc in documents:
                    if (doc.get('metadata', {}).get('filename') == source.filename and 
                        'rerank_score' in doc):
                        rerank_score = doc['rerank_score']
                        if rerank_score > best_rerank_score:
                            best_rerank_score = rerank_score
                            best_rerank_source = source
                            break
            
            best_source = best_rerank_source if best_rerank_source else sources[0]
        
        return best_source
    
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
            similarity_score = doc.get("score", 0.0)  # 키워드 검색은 'score' 필드 사용
            
            if similarity_score >= self.similarity_threshold:
                filtered_docs.append(doc)
        
        # 유사도 기준 내림차순 정렬
        filtered_docs.sort(
            key=lambda x: x.get("score", 0.0), 
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
            similarity_score = doc.get("score", 0.0)  # 키워드 검색은 'score' 필드 사용
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
        source_info = SourceInfo(filename="unknown", content="", similarity_score=0.0)
        
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
                    
                    # from_document 메서드를 사용하여 SourceInfo 생성
                    source_info = SourceInfo.from_document(doc)
                    source_info.content = chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content
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
        return SourceInfo.from_document(doc)
    
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
