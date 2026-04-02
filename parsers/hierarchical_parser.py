"""
계층적 구조 문서 파서
Java 프로젝트의 HierarchicalParser와 유사한 기능 제공
숫자 기반 계층 구조를 인식하여 문서를 세밀하게 분할
"""

import re
from typing import List, Dict, Any, Tuple

from .document_parser import DocumentParser


class HierarchicalParser(DocumentParser):
    """계층적 구조 문서 파서"""
    
    def __init__(self, max_chunk_size: int = 1000, overlap: int = 100):
        """
        초기화
        
        Args:
            max_chunk_size: 최대 청크 크기
            overlap: 청크 간 겹침 크기
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        
        # 계층적 구조 패턴 정의 (자바와 동일)
        self.hierarchical_patterns = [
            # 1., 2., 3. ... 패턴
            r'^\s*(\d+)\.\s+(.+)$',
            # 1.1, 1.2, 2.1 ... 패턴
            r'^\s*(\d+)\.(\d+)\s+(.+)$',
            # 1.1.1, 1.1.2 ... 패턴
            r'^\s*(\d+)\.(\d+)\.(\d+)\s+(.+)$',
            # (1), (2), (3) ... 패턴
            r'^\s*\((\d+)\)\s+(.+)$',
            # 1), 2), 3) ... 패턴
            r'^\s*(\d+)\)\s+(.+)$',
            # ①, ②, ③ ... 패턴
            r'^\s*[①-⑳]\s+(.+)$',
            # 가. 나. 다. ... 패턴
            r'^\s*([가-힣])\.\s+(.+)$',
            # (가), (나), (다) ... 패턴
            r'^\s*\(([가-힣])\)\s+(.+)$',
            # 1항, 2항 ... 패턴
            r'^\s*(\d+)항\s+(.+)$',
            # 제1조, 제2조 ... 패턴
            r'^\s*제(\d+)조\s+(.+)$',
        ]
        
        # 글머리 기호 패턴 (BulletParser와 유사)
        self.bullet_patterns = [
            r'^\s*[-*+]\s+(.+)$',  # -, *, +
            r'^\s*•\s+(.+)$',      # •
            r'^\s*◦\s+(.+)$',      # ◦
            r'^\s*▪\s+(.+)$',      # ▪
            r'^\s*▫\s+(.+)$',      # ▫
        ]
        
        # 모든 패턴 컴파일
        self.compiled_hierarchical = [re.compile(pattern, re.MULTILINE) for pattern in self.hierarchical_patterns]
        self.compiled_bullets = [re.compile(pattern, re.MULTILINE) for pattern in self.bullet_patterns]
    
    def can_handle(self, content: str) -> bool:
        """
        파서가 해당 내용을 처리할 수 있는지 확인
        
        Args:
            content: 확인할 내용
            
        Returns:
            처리 가능 여부
        """
        lines = content.split('\n')
        hierarchical_count = 0
        bullet_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 계층적 패턴 확인
            for pattern in self.compiled_hierarchical:
                if pattern.match(line):
                    hierarchical_count += 1
                    break
            
            # 글머리 패턴 확인
            for pattern in self.compiled_bullets:
                if pattern.match(line):
                    bullet_count += 1
                    break
        
        # 계층적 구조나 글머리 기호가 일정 이상 있으면 처리 가능
        total_lines = len([l for l in lines if l.strip()])
        threshold = max(2, total_lines * 0.1)  # 최소 2개 또는 10%
        
        return (hierarchical_count + bullet_count) >= threshold
    
    def parse(self, content: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        계층적 구조를 기반으로 문서 파싱
        
        Args:
            content: 파싱할 원본 문서 내용
            base_metadata: 기본 메타데이터
            
        Returns:
            파싱된 청크 리스트
        """
        if not self.can_handle(content):
            return []
        
        # 문서를 섹션으로 분할
        sections = self._split_into_hierarchical_sections(content)
        
        # 섹션을 청크로 결합
        chunks = self._create_chunks_from_sections(sections)
        
        # 청크를 표준 형식으로 변환
        result = []
        for i, chunk_text in enumerate(chunks):
            if chunk_text.strip():
                chunk = self._create_chunk(
                    chunk_text.strip(),
                    base_metadata,
                    i,
                    len(chunks),
                    "hierarchical"
                )
                result.append(chunk)
        
        return result
    
    def _split_into_hierarchical_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        내용을 계층적 섹션으로 분할
        
        Args:
            content: 분할할 내용
            
        Returns:
            섹션 정보 리스트
        """
        sections = []
        lines = content.split('\n')
        current_section = None
        current_level = 0
        
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            
            if not line_stripped:
                # 빈 줄은 현재 섹션에 추가
                if current_section:
                    current_section['content'] += '\n' + line
                continue
            
            # 계층적 레벨 확인
            level, section_title = self._get_hierarchical_level(line_stripped)
            
            if level > 0:
                # 새로운 섹션 시작
                if current_section:
                    sections.append(current_section)
                
                current_section = {
                    'content': line,
                    'title': section_title,
                    'level': level,
                    'line_start': line_num + 1,
                    'line_end': line_num + 1
                }
                current_level = level
            else:
                # 일반 텍스트 라인
                if current_section:
                    current_section['content'] += '\n' + line
                    current_section['line_end'] = line_num + 1
                else:
                    # 첫 섹션 이전의 텍스트
                    current_section = {
                        'content': line,
                        'title': '서론',
                        'level': 0,
                        'line_start': line_num + 1,
                        'line_end': line_num + 1
                    }
        
        # 마지막 섹션 추가
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _get_hierarchical_level(self, line: str) -> Tuple[int, str]:
        """
        라인의 계층적 레벨과 제목 추출
        
        Args:
            line: 분석할 라인
            
        Returns:
            (레벨, 제목) 튜플
        """
        # 계층적 패턴 확인
        for i, pattern in enumerate(self.compiled_hierarchical):
            match = pattern.match(line)
            if match:
                groups = match.groups()
                if len(groups) >= 1:
                    title = groups[-1]  # 마지막 그룹이 제목
                    level = len(groups) - 1 + 1  # 그룹 수 - 1 + 1
                    return level, title
        
        # 글머리 패턴 확인
        for pattern in self.compiled_bullets:
            match = pattern.match(line)
            if match:
                title = match.group(1)
                return 1, title
        
        return 0, ""
    
    def _create_chunks_from_sections(self, sections: List[Dict[str, Any]]) -> List[str]:
        """
        섹션들을 청크로 결합
        
        Args:
            sections: 섹션 리스트
            
        Returns:
            청크 텍스트 리스트
        """
        chunks = []
        current_chunk = ""
        
        for section in sections:
            section_text = section['content'].strip()
            
            # 현재 청크에 섹션 추가 시 크기 확인
            if len(current_chunk) + len(section_text) <= self.max_chunk_size:
                # 현재 청크에 섹션 추가
                if current_chunk:
                    current_chunk += '\n\n' + section_text
                else:
                    current_chunk = section_text
            else:
                # 현재 청크 저장하고 새로 시작
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 섹션이 너무 크면 분할
                if len(section_text) > self.max_chunk_size:
                    sub_chunks = self._split_long_section(section_text)
                    chunks.extend(sub_chunks[:-1])  # 마지막 조각 제외
                    current_chunk = sub_chunks[-1]   # 마지막 조각으로 시작
                else:
                    current_chunk = section_text
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_long_section(self, section_text: str) -> List[str]:
        """
        긴 섹션을 더 작은 조각으로 분할
        
        Args:
            section_text: 분할할 섹션 텍스트
            
        Returns:
            분할된 텍스트 조각 리스트
        """
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', section_text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.max_chunk_size:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _create_chunk(self, content: str, base_metadata: Dict[str, Any], 
                    chunk_index: int, total_chunks: int, parser_type: str) -> Dict[str, Any]:
        """
        표준 청크 형식 생성
        
        Args:
            content: 청크 내용
            base_metadata: 기본 메타데이터
            chunk_index: 청크 인덱스
            total_chunks: 전체 청크 수
            parser_type: 파서 타입
            
        Returns:
            청크 딕셔너리
        """
        metadata = base_metadata.copy()
        metadata.update({
            'chunk_index': chunk_index,
            'total_chunks': total_chunks,
            'parser_type': parser_type,
            'chunk_size': len(content)
        })
        
        return {
            'text': content,
            'metadata': metadata
        }
