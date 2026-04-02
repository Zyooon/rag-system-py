"""
텍스트 분할 처리기
Java 프로젝트의 TextSplitterProcessor와 유사한 기능 제공

텍스트 분할의 비즈니스 로직을 담당합니다:
- 문서 분할 - 다양한 전략으로 문서 분할
- 길이 기반 분할 - 문서 길이에 따른 자동 분할
- 전략 선택 - 용도에 맞는 분할 전략 선택
- 메타데이터 관리 - 분할 후 메타데이터 처리

분할 전략:
- 기본 분할: 일반 문서 처리용 표준 분할
- 정밀 분할: 검색 정확도를 높인 세분화 분할
- 속도 분할: 처리 속도를 높인 대용량 분할
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Tuple
from abc import ABC, abstractmethod

from config import settings
from .text_splitter_config import TextSplitterConfig, SplitterSettings, SplitQuality
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 로거 설정
logger = logging.getLogger(__name__)


class TextSplitterProcessor:
    """텍스트 분할 처리 전문 클래스"""
    
    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        
        # LangChain RecursiveCharacterTextSplitter 초기화
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],  # 문단 > 문장 > 단어 순서
            length_function=len,
            is_separator_regex=False
        )
    
    # ==================== 기본 분할 메서드 ====================
    
    def split_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """기본 설정으로 문서 리스트 분할"""
        return self.split_with_settings(documents, TextSplitterConfig.get_default_settings())
    
    # ==================== 긴 문서 분할 ====================
    
    def split_long_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """긴 문서만 분할 (LONG_DOCUMENT_THRESHOLD 이상인 문서만)"""
        result = []
        
        for doc in documents:
            split_docs = self.split_long_document(doc)
            result.extend(split_docs)
        
        logger.debug(f"긴 문서 분할 완료: {len(documents)}개 -> {len(result)}개 청크")
        return result
    
    def split_long_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """단일 긴 문서 분할 (LONG_DOCUMENT_THRESHOLD 이상인 경우만 분할)"""
        text = document.get("text", "")
        
        if len(text) <= TextSplitterConfig.LONG_DOCUMENT_THRESHOLD:
            logger.debug(f"문서 길이가 기준 미달: {len(text)}자 (기준: {TextSplitterConfig.LONG_DOCUMENT_THRESHOLD}자)")
            return [document]
        
        logger.debug(f"긴 문서 분할 시작: {len(text)}자")
        return self.split_document(document)
    
    # ==================== 핵심 분할 로직 ====================
    
    def split_with_settings(self, documents: List[Dict[str, Any]], settings_config: SplitterSettings) -> List[Dict[str, Any]]:
        """지정된 설정으로 문서 분할"""
        try:
            result = []
            
            for doc in documents:
                # 테이블 문서 감지 및 개별 분할
                if self.is_table_document(doc):
                    table_chunks = self.split_table_document(doc)
                    result.extend(table_chunks)
                    logger.debug(f"테이블 문서 분할: {self.count_table_rows(doc)}개 행 -> {len(table_chunks)}개 청크")
                else:
                    # 일반 문서는 기본 분할기 사용
                    normal_chunks = self.split_normal_document(doc, settings_config)
                    result.extend(normal_chunks)
                    logger.debug(f"일반 문서 분할: 1개 -> {len(normal_chunks)}개 청크")
            
            logger.debug(f"전체 문서 분할 완료: {len(documents)}개 -> {len(result)}개 청크 (설정: {settings_config})")
            return result
            
        except Exception as e:
            logger.error(f"문서 분할 실패: {settings_config} - {e}")
            return documents  # 실패 시 원본 반환
    
    def split_normal_document(self, document: Dict[str, Any], settings_config: SplitterSettings) -> List[Dict[str, Any]]:
        """일반 문서 분할 - LangChain RecursiveCharacterTextSplitter 사용"""
        text = document.get("text", "")
        metadata = document.get("metadata", {})
        
        if len(text) <= settings_config.chunk_size:
            return [{
                "text": text,
                "metadata": {
                    **metadata,
                    "chunk_index": 0,
                    "splitter_type": "no_split",
                    "parser_type": "recursive"
                }
            }]
        
        # LangChain RecursiveCharacterTextSplitter로 분할
        try:
            chunks = self.recursive_splitter.split_text(text)
            result = []
            
            for i, chunk_text in enumerate(chunks):
                if len(chunk_text.strip()) >= settings_config.min_chunk_size_chars:
                    chunk_metadata = {
                        **metadata,
                        "chunk_index": i,
                        "splitter_type": "recursive_character",
                        "parser_type": "recursive",
                        "chunk_length": len(chunk_text),
                        "start_char": text.find(chunk_text) if i == 0 else "unknown",
                        "end_char": text.find(chunk_text) + len(chunk_text) if i == 0 else "unknown"
                    }
                    
                    result.append({
                        "text": chunk_text.strip(),
                        "metadata": chunk_metadata
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"RecursiveCharacterTextSplitter 실패, 기본 분할기로 전환: {e}")
            return self._fallback_split_normal_document(document, settings_config)
    
    def _fallback_split_normal_document(self, document: Dict[str, Any], settings_config: SplitterSettings) -> List[Dict[str, Any]]:
        """기본 분할기 (fallback)"""
        text = document.get("text", "")
        metadata = document.get("metadata", {})
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text) and chunk_index < settings_config.max_num_chunks:
            end = start + settings_config.chunk_size
            
            # 문장 경계에서 분할 시도
            if end < len(text):
                end = self._find_sentence_boundary(text, start, end, settings_config.punctuation_marks)
            
            chunk_text = text[start:end].strip()
            
            # 최소 길이 확인
            if len(chunk_text) >= settings_config.min_chunk_size_chars:
                chunk_metadata = {
                    **metadata,
                    "chunk_index": chunk_index,
                    "splitter_type": "fallback_sentence_boundary",
                    "parser_type": "fallback",
                    "start_char": start,
                    "end_char": end,
                    "chunk_length": len(chunk_text)
                }
                
                chunks.append({
                    "text": chunk_text,
                    "metadata": chunk_metadata
                })
                
                chunk_index += 1
            
            # 겹침을 고려한 다음 시작 위치 계산
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
    
    def is_table_document(self, document: Dict[str, Any]) -> bool:
        """테이블 문서인지 감지 (내용 기반으로 개선)"""
        content = document.get("text", "")
        metadata = document.get("metadata", {})
        filename = metadata.get("filename", "")
        
        # 1. 파일명에 'table'이 포함된 경우 (기존 로직 유지)
        if "table" in filename.lower() or "TABLE" in filename:
            return True
        
        # 2. 내용 기반 테이블 감지
        lines = content.split('\n')
        table_row_count = 0
        has_header_separator = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # 테이블 형식 확인: | 내용 | 내용 |
            if re.match(r'^\|.*\|$', stripped_line):
                table_row_count += 1
                
                # 헤더 구분자 확인: |---|---| 또는 |:---|:---|
                if '---' in stripped_line and (':' in stripped_line or stripped_line.count('|') >= 3):
                    has_header_separator = True
        
        # 테이블 행이 3개 이상이고 헤더 구분자가 있으면 테이블로 간주
        return table_row_count >= 3 and has_header_separator
    
    def split_table_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """테이블 문서를 개별 행으로 분할"""
        content = document.get("text", "")
        metadata = document.get("metadata", {})
        
        lines = content.split("\n")
        current_chunk = ""
        chunk_index = 0
        result = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 빈 줄은 건너뛰기
            if not line:
                continue
            
            # 헤더 줄은 별도 청크로 처리
            if line.startswith("|") and ("---" in line or ":---" in line):
                if current_chunk:
                    result.append(self._create_table_chunk(current_chunk, metadata, chunk_index))
                    chunk_index += 1
                    current_chunk = ""
                result.append(self._create_table_chunk(line, metadata, chunk_index))
                chunk_index += 1
                continue
            
            # 테이블 데이터 행
            if line.startswith("|"):
                if current_chunk:
                    result.append(self._create_table_chunk(current_chunk, metadata, chunk_index))
                    chunk_index += 1
                current_chunk = line
            else:
                # 테이블이 아닌 내용은 현재 청크에 추가
                if current_chunk:
                    current_chunk += "\n" + line
        
        # 마지막 청크 추가
        if current_chunk:
            result.append(self._create_table_chunk(current_chunk, metadata, chunk_index))
        
        return result
    
    def _create_table_chunk(self, content: str, original_metadata: Dict[str, Any], chunk_index: int) -> Dict[str, Any]:
        """테이블 청크 생성"""
        new_metadata = original_metadata.copy()
        new_metadata.update({
            "chunk_index": chunk_index,
            "section_type": "table_row",
            "chunk_length": len(content)
        })
        
        return {
            "text": content,
            "metadata": new_metadata
        }
    
    def count_table_rows(self, document: Dict[str, Any]) -> int:
        """테이블 행 수 계산"""
        content = document.get("text", "")
        lines = content.split("\n")
        
        table_rows = 0
        for line in lines:
            line = line.strip()
            if line.startswith("|") and "---" not in line:
                table_rows += 1
        
        return table_rows
    
    # ==================== 문장 경계 찾기 ====================
    
    def _find_sentence_boundary(self, text: str, start: int, end: int, punctuation_marks: List[str]) -> int:
        """문장 경계 찾기"""
        # end 위치부터 역방향으로 문장 경계 찾기
        for i in range(end - 1, start - 1, -1):
            if text[i] in punctuation_marks:
                # 다음 문자가 공백이거나 문장 끝인지 확인
                if (i + 1 >= len(text) or 
                    text[i + 1].isspace() or 
                    text[i + 1] in punctuation_marks):
                    return i + 1
        
        # 문장 경계를 찾을 수 없으면 원래 end 반환
        return end
    
    # ==================== 통계 및 평가 ====================
    
    @staticmethod
    def create_split_statistics(original_documents: List[Dict[str, Any]], split_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """문서 분할 통계 정보 생성"""
        original_count = len(original_documents)
        split_count = len(split_documents)
        
        avg_original_length = sum(doc.get("text", "") for doc in original_documents) / original_count if original_count > 0 else 0
        avg_split_length = sum(doc.get("text", "") for doc in split_documents) / split_count if split_count > 0 else 0
        
        return {
            "original_count": original_count,
            "split_count": split_count,
            "split_ratio": split_count / original_count if original_count > 0 else 0,
            "avg_original_length": int(avg_original_length),
            "avg_split_length": int(avg_split_length)
        }
    
    def evaluate_split_quality(self, split_documents: List[Dict[str, Any]]) -> SplitQuality:
        """분할 품질 평가"""
        if not split_documents:
            return SplitQuality(0.0, "분할된 문서가 없습니다", False)
        
        # 평가 기준
        avg_length = sum(len(doc.get("text", "")) for doc in split_documents) / len(split_documents)
        
        is_optimal = 50 <= avg_length <= 500  # 적정 길이 범위
        score = self._calculate_quality_score(avg_length)
        message = self._create_quality_message(avg_length, is_optimal)
        
        return SplitQuality(score, message, is_optimal)
    
    def _calculate_quality_score(self, avg_length: float) -> float:
        """품질 점수 계산"""
        # 100-300자가 가장 이상적 (100점)
        if 100 <= avg_length <= 300:
            return 100.0
        # 50-100자 또는 300-500자 (80점)
        if (50 <= avg_length < 100) or (300 < avg_length <= 500):
            return 80.0
        # 20-50자 또는 500-800자 (60점)
        if (20 <= avg_length < 50) or (500 < avg_length <= 800):
            return 60.0
        # 그 외 (40점)
        return 40.0
    
    def _create_quality_message(self, avg_length: float, is_optimal: bool) -> str:
        """품질 메시지 생성"""
        if is_optimal:
            return f"좋은 분할 결과입니다 (평균 {avg_length:.0f}자)"
        elif avg_length < 50:
            return f"과도하게 분할되었습니다 (평균 {avg_length:.0f}자)"
        elif avg_length > 500:
            return f"분할이 부족합니다 (평균 {avg_length:.0f}자)"
        else:
            return f"일반적인 분할 결과입니다 (평균 {avg_length:.0f}자)"
    
    def split_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """텍스트를 청크로 분할 - LangChain RecursiveCharacterTextSplitter 사용"""
        if not text or len(text) <= self.chunk_size:
            return [{
                "text": text,
                "metadata": {
                    **metadata,
                    "chunk_index": 0,
                    "splitter_type": "no_split",
                    "parser_type": "recursive"
                }
            }]
        
        # LangChain RecursiveCharacterTextSplitter로 분할
        try:
            chunks = self.recursive_splitter.split_text(text)
            result = []
            
            for i, chunk_text in enumerate(chunks):
                if chunk_text.strip():
                    chunk_metadata = {
                        **metadata,
                        "chunk_index": i,
                        "splitter_type": "recursive_character",
                        "parser_type": "recursive",
                        "start_char": text.find(chunk_text) if i == 0 else "unknown",
                        "end_char": text.find(chunk_text) + len(chunk_text) if i == 0 else "unknown"
                    }
                    
                    result.append({
                        "text": chunk_text.strip(),
                        "metadata": chunk_metadata
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"RecursiveCharacterTextSplitter 실패, 기본 분할기로 전환: {e}")
            return self._fallback_split_text(text, metadata)
    
    def _fallback_split_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """기본 텍스트 분할기 (fallback)"""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 문장 경계에서 분할 시도
            if end < len(text):
                end = self._find_sentence_boundary(text, start, end, TextSplitterConfig.DEFAULT_PUNCTUATION_MARKS)
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_metadata = {
                    **metadata,
                    "chunk_index": chunk_index,
                    "splitter_type": "fallback_sentence_boundary",
                    "parser_type": "fallback",
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
