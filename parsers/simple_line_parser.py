"""
일반 텍스트 문서 파서
Java 프로젝트의 SimpleLineParser와 유사한 기능 제공
"""

import re
from typing import List, Dict, Any

from .document_parser import DocumentParser


class SimpleLineParser(DocumentParser):
    """일반 텍스트 문서 파서"""
    
    def __init__(self, max_chunk_size: int = 1000, overlap: int = 100):
        """
        초기화
        
        Args:
            max_chunk_size: 최대 청크 크기
            overlap: 청크 간 겹침 크기
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
    
    def parse(self, content: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        일반 텍스트를 문단 단위로 파싱
        
        Args:
            content: 파싱할 원본 문서 내용
            base_metadata: 기본 메타데이터
            
        Returns:
            파싱된 청크 리스트
        """
        if not self.can_handle(content):
            return []
        
        # 빈 줄 기준으로 문단 분리
        paragraphs = self._split_into_paragraphs(content)
        
        # 문단을 청크로 결합
        chunks = self._create_chunks_from_paragraphs(paragraphs)
        
        # 청크를 표준 형식으로 변환
        result = []
        for i, chunk_text in enumerate(chunks):
            if chunk_text.strip():
                chunk = self._create_chunk(
                    chunk_text, 
                    base_metadata, 
                    chunk_index=i,
                    additional_metadata={
                        "chunk_type": "paragraph",
                        "parser_strategy": "simple_line"
                    }
                )
                result.append(chunk)
        
        return result
    
    def can_handle(self, content: str) -> bool:
        """
        일반 텍스트 처리 가능 여부 확인 (항상 True)
        
        Args:
            content: 확인할 문서 내용
            
        Returns:
            처리 가능 여부
        """
        return super().can_handle(content)
    
    def get_parser_name(self) -> str:
        """파서 이름 반환"""
        return "SimpleLine"
    
    def _split_into_paragraphs(self, content: str) -> List[str]:
        """
        내용을 문단으로 분리
        
        Args:
            content: 원본 내용
            
        Returns:
            문단 리스트
        """
        # 여러 줄바꿈을 단일 줄바꿈으로 정규화
        normalized = re.sub(r'\n\s*\n', '\n\n', content.strip())
        
        # 문단 분리
        paragraphs = normalized.split('\n\n')
        
        # 빈 문단 제거 및 정리
        cleaned_paragraphs = []
        for para in paragraphs:
            cleaned = para.strip()
            if cleaned:
                cleaned_paragraphs.append(cleaned)
        
        return cleaned_paragraphs
    
    def _create_chunks_from_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """
        문단들을 청크로 결합
        
        Args:
            paragraphs: 문단 리스트
            
        Returns:
            청크 텍스트 리스트
        """
        if not paragraphs:
            return []
        
        chunks = []
        current_chunk = ""
        current_size = 0
        
        for i, paragraph in enumerate(paragraphs):
            para_size = len(paragraph)
            
            # 현재 청크에 문단을 추가해도 크기 제한을 넘지 않는 경우
            if current_size + para_size + 2 <= self.max_chunk_size:  # +2 for newlines
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_size += para_size + (2 if current_chunk != paragraph else 0)
            else:
                # 현재 청크 저장
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 새 청크 시작
                if para_size > self.max_chunk_size:
                    # 문단이 너무 긴 경우, 강제로 분할
                    sub_chunks = self._split_long_paragraph(paragraph)
                    chunks.extend(sub_chunks[:-1])  # 마지막 조각은 다음에 사용
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
                    current_size = len(current_chunk)
                else:
                    current_chunk = paragraph
                    current_size = para_size
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """
        긴 문단을 여러 청크로 분할
        
        Args:
            paragraph: 분할할 문단
            
        Returns:
            분할된 청크 리스트
        """
        chunks = []
        start = 0
        
        while start < len(paragraph):
            end = start + self.max_chunk_size
            
            if end >= len(paragraph):
                chunks.append(paragraph[start:])
                break
            
            # 문장 경계 찾기
            sentence_end = self._find_sentence_boundary(paragraph, start, end)
            
            if sentence_end > start:
                chunks.append(paragraph[start:sentence_end].strip())
                start = sentence_end
            else:
                # 문장 경계를 찾을 수 없으면 강제 분할
                chunks.append(paragraph[start:end].strip())
                start = end
        
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
        # 문장 종결 문자 패턴
        sentence_patterns = ['.', '!', '?', '\n']
        
        # end 위치부터 역방향으로 문장 경계 찾기
        for i in range(end - 1, start - 1, -1):
            if text[i] in sentence_patterns:
                return i + 1
        
        # 문장 경계를 찾을 수 없으면 start 반환
        return start
