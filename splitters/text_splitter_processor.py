"""
텍스트 분할 처리기
Java 프로젝트의 TextSplitterProcessor와 유사한 기능 제공
"""

import asyncio
from typing import List, Dict, Any
from abc import ABC, abstractmethod

from config import settings


class TextSplitterProcessor:
    """텍스트 분할 처리기"""
    
    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def split_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        문서 리스트를 청크로 분할
        
        Args:
            documents: 분할할 문서 리스트
            
        Returns:
            분할된 청크 리스트
        """
        all_chunks = []
        
        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            
            if text.strip():
                chunks = self.split_text(text, metadata)
                all_chunks.extend(chunks)
        
        return all_chunks
    
    def split_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 분할할 텍스트
            metadata: 기존 메타데이터
            
        Returns:
            분할된 청크 리스트
        """
        if not text or len(text) <= self.chunk_size:
            return [{
                "text": text,
                "metadata": {
                    **metadata,
                    "chunk_index": 0,
                    "splitter_type": "no_split"
                }
            }]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 문장 경계에서 분할 시도
            if end < len(text):
                end = self._find_sentence_boundary(text, start, end)
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_metadata = {
                    **metadata,
                    "chunk_index": chunk_index,
                    "splitter_type": "sentence_boundary",
                    "start_char": start,
                    "end_char": end
                }
                
                chunks.append({
                    "text": chunk_text,
                    "metadata": chunk_metadata
                })
                
                chunk_index += 1
            
            # 겹침을 고려한 다음 시작 위치 계산
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
    
    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """
        문장 경계 찾기
        
        Args:
            text: 전체 텍스트
            start: 시작 위치
            end: 끝 위치
            
        Returns:
            문장 경계 위치
        """
        # 문장 종결 문자
        sentence_endings = ['.', '!', '?', '\n', '。', '！', '？']
        
        # end 위치부터 역방향으로 문장 경계 찾기
        for i in range(end - 1, start - 1, -1):
            if text[i] in sentence_endings:
                # 다음 문자가 공백이거나 문장 끝인지 확인
                if (i + 1 >= len(text) or 
                    text[i + 1].isspace() or 
                    text[i + 1] in sentence_endings):
                    return i + 1
        
        # 문장 경계를 찾을 수 없으면 원래 end 반환
        return end
    
    def split_long_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        긴 문서 분할 (기존 분할 결과가 너무 긴 경우)
        
        Args:
            documents: 분할할 문서 리스트
            
        Returns:
            추가 분할된 문서 리스트
        """
        result = []
        
        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            
            # 문서가 너무 긴 경우 추가 분할
            if len(text) > self.chunk_size * 2:
                sub_chunks = self.split_text(text, metadata)
                for i, chunk in enumerate(sub_chunks):
                    chunk_metadata = {
                        **chunk.get("metadata", {}),
                        "original_chunk_index": metadata.get("chunk_index", 0),
                        "sub_chunk_index": i
                    }
                    result.append({
                        "text": chunk["text"],
                        "metadata": chunk_metadata
                    })
            else:
                result.append(doc)
        
        return result
