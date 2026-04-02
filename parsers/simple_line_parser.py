"""
일반 텍스트 문서 파서
Java 프로젝트의 SimpleLineParser와 유사한 기능 제공
"""

import re
from typing import List, Dict, Any
from datetime import datetime

from .document_parser import DocumentParser


class SimpleLineParser(DocumentParser):
    """일반 텍스트 문서 파서"""
    
    def __init__(self, max_chunk_size: int = 200, overlap: int = 20):
        """
        초기화
        
        Args:
            max_chunk_size: 최대 청크 크기 (기본값 200으로 더 줄임)
            overlap: 청크 간 겹침 크기 (기본값 20으로 더 줄임)
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
    
    def parse(self, content: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        일반 텍스트를 문단 및 문장 단위로 파싱 (강화된 버전)
        
        Args:
            content: 파싱할 원본 문서 내용
            base_metadata: 기본 메타데이터
            
        Returns:
            파싱된 청크 리스트
        """
        if not self.can_handle(content):
            return []
        
        # 메타데이터에 시간 정보 추가
        enhanced_metadata = {
            **base_metadata,
            "saved_at": datetime.now().isoformat(),
            "parser_type": "simple_line_enhanced"
        }
        
        # 1단계: 문단 분리
        paragraphs = self._split_into_paragraphs(content)
        
        # 2단계: 문단을 청크로 결합 (문장 단위 분할 강화)
        chunks = self._create_chunks_from_paragraphs_enhanced(paragraphs)
        
        # 3단계: 청크를 표준 형식으로 변환
        result = []
        for i, chunk_text in enumerate(chunks):
            if chunk_text.strip():
                chunk = self._create_chunk(
                    chunk_text, 
                    enhanced_metadata, 
                    chunk_index=i,
                    additional_metadata={
                        "chunk_type": "paragraph_enhanced",
                        "parser_strategy": "simple_line_sentence_aware",
                        "chunk_length": len(chunk_text)
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
        내용을 문단으로 분리 (강화된 버전 - 문장 단위 분할 포함)
        
        Args:
            content: 원본 내용
            
        Returns:
            문단 리스트
        """
        # 여러 줄바꿈을 단일 줄바꿈으로 정규화
        normalized = re.sub(r'\n\s*\n', '\n\n', content.strip())
        
        # 문단 분리 시도
        paragraphs = normalized.split('\n\n')
        
        # 문단이 너무 크거나 1개만 있으면 문장 단위로 강제 분할
        if len(paragraphs) <= 1 or any(len(p.strip()) > 300 for p in paragraphs):
            return self._force_sentence_splitting(content)
        
        # 빈 문단 제거 및 정리
        cleaned_paragraphs = []
        for para in paragraphs:
            cleaned = para.strip()
            if cleaned:
                cleaned_paragraphs.append(cleaned)
        
        return cleaned_paragraphs
    
    def _force_sentence_splitting(self, content: str) -> List[str]:
        """
        강제 문장 단위 분할
        
        Args:
            content: 분할할 내용
            
        Returns:
            문장 리스트
        """
        # 문장 분할 패턴
        sentence_patterns = [
            r'(?<=[.!?])\s+(?=[A-Z가-힣])',  # 문장 끝 + 공백 + 대문자/한글
            r'(?<=[.!?])\s+',                # 문장 끝 + 공백
            r'(?<=[,;])\s+',                  # 쉼표/세미콜론 + 공백
        ]
        
        sentences = [content]
        
        for pattern in sentence_patterns:
            new_sentences = []
            for sentence in sentences:
                if len(sentence) > 200:  # 너무 긴 문장만 분할
                    split_parts = re.split(pattern, sentence)
                    split_parts = [s.strip() for s in split_parts if s.strip()]
                    if len(split_parts) > 1:
                        new_sentences.extend(split_parts)
                    else:
                        new_sentences.append(sentence)
                else:
                    new_sentences.append(sentence)
            sentences = new_sentences
        
        return sentences
    
    def _create_chunks_from_paragraphs_enhanced(self, paragraphs: List[str]) -> List[str]:
        """
        문단들을 청크로 결합 (문장 단위 분할 강화)
        
        Args:
            paragraphs: 문단 리스트
            
        Returns:
            청크 텍스트 리스트
        """
        if not paragraphs:
            return []
        
        chunks = []
        
        # 문장 단위로 분할된 경우 각 문장을 개별 청크로 처리
        if len(paragraphs) > 3:  # 문장 단위로 분할된 것으로 간주
            for paragraph in paragraphs:
                if len(paragraph.strip()) > 10:  # 최소 길이 체크
                    chunks.append(paragraph.strip())
        else:
            # 기존 문단 결합 로직
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
                        # 문단이 너무 긴 경우, 강제로 문장 단위 분할
                        sub_chunks = self._split_long_paragraph_by_sentences(paragraph)
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
    
    def _split_long_paragraph_by_sentences(self, paragraph: str) -> List[str]:
        """
        긴 문단을 문장 단위로 분할 (강화된 버전)
        
        Args:
            paragraph: 분할할 문단
            
        Returns:
            분할된 청크 리스트
        """
        # 문장 분할 패턴 (더 정교한 버전)
        sentence_patterns = [
            r'(?<=[.!?])\s+(?=[A-Z가-힣])',  # 문장 끝 + 공백 + 대문자/한글
            r'(?<=[.!?])\s+',                # 문장 끝 + 공백
            r'(?<=\.\s)\s+',                 # 마침표+공백+공백
            r'(?<=\n)\s+',                   # 줄바꿈 + 공백
            r'(?<=[,;])\s+',                  # 쉼표/세미콜론 + 공백 (문맥 분할용)
            r'\s{2,}',                        # 여러 공백
        ]
        
        # 먼저 문장으로 분할 시도
        sentences = []
        current_text = paragraph
        
        for pattern in sentence_patterns:
            if len(sentences) <= 1:  # 아직 잘 분할되지 않았다면 다음 패턴 시도
                sentences = re.split(pattern, current_text)
                sentences = [s.strip() for s in sentences if s.strip()]
        
        # 문장 분할이 실패하면 기본 방식으로
        if len(sentences) <= 1:
            sentences = self._fallback_sentence_split(paragraph)
        
        # 문장들을 청크 크기에 맞게 결합
        return self._combine_sentences_to_chunks(sentences)
    
    def _fallback_sentence_split(self, text: str) -> List[str]:
        """
        기본 문장 분할 방식
        
        Args:
            text: 분할할 텍스트
            
        Returns:
            분할된 문장 리스트
        """
        # 기본 문장 종결 문자로 분할
        sentences = []
        start = 0
        
        for i, char in enumerate(text):
            if char in '.!?':
                # 문장 끝 발견
                sentence = text[start:i+1].strip()
                if sentence:
                    sentences.append(sentence)
                start = i+1
        
        # 마지막 조각 추가
        if start < len(text):
            remaining = text[start:].strip()
            if remaining:
                sentences.append(remaining)
        
        return sentences
    
    def _combine_sentences_to_chunks(self, sentences: List[str]) -> List[str]:
        """
        문장들을 청크 크기에 맞게 결합
        
        Args:
            sentences: 문장 리스트
            
        Returns:
            결합된 청크 리스트
        """
        if not sentences:
            return []
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 현재 청크에 문장을 추가해도 크기 제한을 넘지 않는 경우
            if len(current_chunk) + len(sentence) + 1 <= self.max_chunk_size:  # +1 for space
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                # 현재 청크 저장
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 문장이 너무 긴 경우 강제 분할
                if len(sentence) > self.max_chunk_size:
                    forced_chunks = self._force_split_long_text(sentence)
                    chunks.extend(forced_chunks[:-1])  # 마지막 조각은 다음에 사용
                    current_chunk = forced_chunks[-1] if forced_chunks else ""
                else:
                    current_chunk = sentence
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _force_split_long_text(self, text: str) -> List[str]:
        """
        긴 텍스트를 강제로 분할
        
        Args:
            text: 분할할 텍스트
            
        Returns:
            분할된 텍스트 리스트
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.max_chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # 공백에서 분할 시도
            space_pos = text.rfind(' ', start, end)
            if space_pos > start:
                chunks.append(text[start:space_pos])
                start = space_pos + 1
            else:
                # 공백이 없으면 강제 분할
                chunks.append(text[start:end])
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
