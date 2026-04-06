"""
리랭킹 서비스
Cross-Encoder를 사용한 검색 결과 재정렬
"""

import asyncio
import logging
from typing import List, Dict, Any, Tuple
import numpy as np

from sentence_transformers import CrossEncoder
from config import settings

logger = logging.getLogger(__name__)


class RerankingService:
    """리랭킹 서비스"""
    
    def __init__(self):
        # Cross-Encoder 모델 로드 (한국어 지원)
        try:
            self.cross_encoder = CrossEncoder('jhgan/ko-sroberta-multitask')
            logger.info("✅ Cross-Encoder 리랭커 로드 완료")
        except Exception as e:
            logger.error(f"❌ Cross-Encoder 리랭커 로드 실패: {e}")
            self.cross_encoder = None
        
        # 리랭킹 설정
        self.rerank_top_k = settings.rerank_top_k
        self.rerank_threshold = settings.rerank_threshold
    
    async def rerank_documents(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cross-Encoder로 문서 재랭킹
        
        Args:
            query: 사용자 질문
            documents: 검색된 문서 리스트
            
        Returns:
            재랭킹된 문서 리스트
        """
        if not self.cross_encoder or len(documents) <= 1:
            logger.info("🔄 리랭킹 스킵: 모델 없음 또는 문서 부족")
            return documents
        
        try:
            # 1. 질문-문서 쌍 생성
            query_doc_pairs = self._create_query_doc_pairs(query, documents)
            
            # 2. Cross-Encoder 점수 계산
            scores = await self._calculate_cross_encoder_scores(query_doc_pairs)
            
            # 3. 점수 기반 재정렬
            reranked_docs = self._apply_reranking(documents, scores)
            
            # 4. 임계값 필터링
            filtered_docs = self._filter_by_threshold(reranked_docs)
            
            logger.info(f"🎯 리랭킹 완료: {len(documents)} → {len(filtered_docs)}개 문서")
            return filtered_docs
            
        except Exception as e:
            logger.error(f"리랭킹 실패: {e}")
            return documents
    
    def _create_query_doc_pairs(self, query: str, documents: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
        """질문-문서 쌍 생성"""
        pairs = []
        for doc in documents:
            text = doc.get("text", "")
            if text.strip():
                pairs.append((query, text))
        return pairs
    
    async def _calculate_cross_encoder_scores(self, query_doc_pairs: List[Tuple[str, str]]) -> np.ndarray:
        """Cross-Encoder 점수 계산"""
        try:
            # 비동기 처리를 위해 스레드 풀 사용
            scores = await asyncio.to_thread(
                self.cross_encoder.predict,
                query_doc_pairs
            )
            return np.array(scores)
        except Exception as e:
            logger.error(f"Cross-Encoder 점수 계산 실패: {e}")
            raise
    
    def _apply_reranking(self, documents: List[Dict[str, Any]], scores: np.ndarray) -> List[Dict[str, Any]]:
        """점수 기반 재정렬"""
        # 점수를 문서에 추가
        scored_docs = []
        for doc, score in zip(documents, scores):
            doc_copy = doc.copy()
            doc_copy['rerank_score'] = float(score)
            doc_copy['rerank_method'] = 'cross_encoder'
            scored_docs.append(doc_copy)
        
        # 점수 기반 내림차순 정렬
        scored_docs.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        return scored_docs
    
    def _filter_by_threshold(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """임계값 기반 필터링"""
        filtered = []
        for doc in documents:
            score = doc.get('rerank_score', 0.0)
            if score >= self.rerank_threshold:
                filtered.append(doc)
        
        # 임계값 통과 문서가 없으면 상위 문서 반환
        if not filtered and documents:
            filtered = documents[:self.rerank_top_k]
        
        return filtered[:self.rerank_top_k]
    
    async def rerank_with_multiple_strategies(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        다중 전략 리랭킹
        
        Args:
            query: 사용자 질문
            documents: 검색된 문서 리스트
            
        Returns:
            다중 전략으로 재랭킹된 문서 리스트
        """
        if not self.cross_encoder:
            return documents
        
        try:
            # 1. Cross-Encoder 리랭킹
            cross_encoder_docs = await self.rerank_documents(query, documents)
            
            # 2. 유사도 점수와 리랭킹 점수 결합
            combined_docs = self._combine_scores(documents, cross_encoder_docs)
            
            # 3. 최종 정렬
            final_docs = sorted(combined_docs, key=lambda x: x.get('combined_score', 0), reverse=True)
            
            return final_docs[:self.rerank_top_k]
            
        except Exception as e:
            logger.error(f"다중 전략 리랭킹 실패: {e}")
            return documents
    
    def _combine_scores(self, original_docs: List[Dict[str, Any]], reranked_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """원본 점수와 리랭킹 점수 결합"""
        combined = []
        
        # 문서 ID 기반 매핑
        doc_map = {doc.get('text', ''): doc for doc in original_docs}
        
        for reranked_doc in reranked_docs:
            text = reranked_doc.get('text', '')
            original_doc = doc_map.get(text, {})
            
            # 점수 결합 (가중치 적용)
            similarity_score = original_doc.get('similarity_score', 0.0)
            rerank_score = reranked_doc.get('rerank_score', 0.0)
            
            # 가중치: 리랭킹 0.7, 유사도 0.3
            combined_score = (rerank_score * 0.7) + (similarity_score * 0.3)
            
            combined_doc = reranked_doc.copy()
            combined_doc.update({
                'combined_score': combined_score,
                'similarity_score': similarity_score,
                'rerank_weight': 0.7,
                'similarity_weight': 0.3
            })
            
            combined.append(combined_doc)
        
        return combined
    
    async def get_reranking_stats(self, query: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """리랭킹 통계 정보"""
        if not self.cross_encoder:
            return {"error": "Cross-Encoder 모델이 없습니다"}
        
        try:
            # 리랭킹 전후 비교
            original_scores = [doc.get('similarity_score', 0.0) for doc in documents]
            
            reranked_docs = await self.rerank_documents(query, documents)
            reranked_scores = [doc.get('rerank_score', 0.0) for doc in reranked_docs]
            
            stats = {
                "original_count": len(documents),
                "reranked_count": len(reranked_docs),
                "original_avg_score": np.mean(original_scores) if original_scores else 0,
                "reranked_avg_score": np.mean(reranked_scores) if reranked_scores else 0,
                "score_improvement": np.mean(reranked_scores) - np.mean(original_scores) if original_scores and reranked_scores else 0,
                "top_k_score": reranked_scores[0] if reranked_scores else 0,
                "threshold_applied": len([s for s in reranked_scores if s >= self.rerank_threshold])
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"리랭킹 통계 계산 실패: {e}")
            return {"error": str(e)}
