"""
시맨틱 청킹 서비스
문맥을 이해하여 의미가 끊기지 않는 청크 생성
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import numpy as np

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from config import settings

logger = logging.getLogger(__name__)


class SemanticChunkingService:
    """시맨틱 청킹 서비스"""
    
    def __init__(self):
        # 임베딩 모델 로드 (한국어 지원)
        try:
            self.embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')
            logger.info("[OK] 시맨틱 청킹 모델 로드 완료")
        except Exception as e:
            logger.error(f"[FAIL] 시맨틱 청킹 모델 로드 실패: {e}")
            self.embedding_model = None
        
        # 기본 텍스트 분할기
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.semantic_chunk_size,
            chunk_overlap=settings.semantic_chunk_overlap,
            separators=["\n\n", "\n", "。", "？", "！", "；", "．", "？", "！"]
        )
    
    async def semantic_chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        시맨틱 청킹으로 문서 분할
        
        Args:
            document: 분할할 문서
            
        Returns:
            시맨틱 청크 리스트
        """
        text = document.get("text", "")
        metadata = document.get("metadata", {})
        
        if not text.strip():
            return [document]
        
        if not self.embedding_model:
            # 모델이 없으면 기본 분할기 사용
            return await self._fallback_chunking(document)
        
        try:
            # 1. 문장 단위로 분할
            sentences = self._split_into_sentences(text)
            
            # 2. 문장 임베딩 생성
            embeddings = await self._generate_embeddings(sentences)
            
            # 3. 의미 경계점 찾기
            semantic_boundaries = self._find_semantic_boundaries(sentences, embeddings)
            
            # 4. 청크 생성
            chunks = self._create_semantic_chunks(sentences, semantic_boundaries, metadata)
            
            logger.info(f"🧠 시맨틱 청킹 완료: {len(chunks)}개 청크 생성")
            return chunks
            
        except Exception as e:
            logger.error(f"시맨틱 청킹 실패: {e}")
            return await self._fallback_chunking(document)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """문장 단위로 분할"""
        import re
        
        # 한국어 문장 분할 패턴
        sentence_patterns = [
            r'[^.!?]+[.!?]+',  # 일반 문장 종결 부호
            r'[^.!?]+[.!?]\s+',  # 문장 + 공백
            r'[^.!?]+[.!?]\n',  # 문장 + 줄바꿈
        ]
        
        sentences = []
        for pattern in sentence_patterns:
            matches = re.findall(pattern, text)
            sentences.extend([s.strip() for s in matches if s.strip()])
        
        return sentences if sentences else [text]
    
    async def _generate_embeddings(self, sentences: List[str]) -> np.ndarray:
        """문장 임베딩 생성"""
        try:
            # 비동기 처리를 위해 스레드 풀 사용
            embeddings = await asyncio.to_thread(
                self.embedding_model.encode,
                sentences,
                convert_to_numpy=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise
    
    def _find_semantic_boundaries(self, sentences: List[str], embeddings: np.ndarray) -> List[int]:
        """
        의미 경계점 찾기
        
        Args:
            sentences: 문장 리스트
            embeddings: 임베딩 배열
            
        Returns:
            경계점 인덱스 리스트
        """
        if len(sentences) <= 1:
            return [len(sentences)]
        
        # 인접 문장 간의 유사도 계산
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = cosine_similarity(
                embeddings[i:i+1], 
                embeddings[i+1:i+2]
            )[0][0]
            similarities.append(sim)
        
        # 유사도가 급격히 낮아지는 지점을 경계로 선택
        boundaries = []
        similarity_threshold = settings.semantic_similarity_threshold
        
        for i, sim in enumerate(similarities):
            if sim < similarity_threshold:
                boundaries.append(i + 1)
        
        # 마지막 경계 추가
        boundaries.append(len(sentences))
        
        return boundaries
    
    def _create_semantic_chunks(self, sentences: List[str], boundaries: List[int], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """시맨틱 청크 생성"""
        chunks = []
        start_idx = 0
        
        for i, end_idx in enumerate(boundaries):
            chunk_sentences = sentences[start_idx:end_idx]
            chunk_text = " ".join(chunk_sentences)
            
            if chunk_text.strip():
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "chunk_type": "semantic",
                    "sentence_count": len(chunk_sentences),
                    "semantic_boundary": True
                })
                
                chunks.append({
                    "text": chunk_text,
                    "metadata": chunk_metadata
                })
            
            start_idx = end_idx
        
        return chunks
    
    async def _fallback_chunking(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """기본 청킹으로 대체"""
        try:
            text = document.get("text", "")
            metadata = document.get("metadata", {})
            
            # 기본 분할기 사용
            chunks = self.text_splitter.split_text(text)
            
            result = []
            for i, chunk_text in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "chunk_type": "fallback",
                    "semantic_boundary": False
                })
                
                result.append({
                    "text": chunk_text,
                    "metadata": chunk_metadata
                })
            
            return result
            
        except Exception as e:
            logger.error(f"기본 청킹 실패: {e}")
            return [document]
    
    async def batch_semantic_chunk(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """배치 시맨틱 청킹"""
        all_chunks = []
        
        for doc in documents:
            chunks = await self.semantic_chunk_document(doc)
            all_chunks.extend(chunks)
        
        return all_chunks
