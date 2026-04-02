"""
Markdown 문서 파서
Java 프로젝트의 MarkdownParser와 유사한 기능 제공
"""

import re
from typing import List, Dict, Any

from .document_parser import DocumentParser


class MarkdownParser(DocumentParser):
    """Markdown 형식 문서 파서"""
    
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
        Markdown 문서를 구조화된 청크로 파싱
        
        Args:
            content: 파싱할 원본 문서 내용
            base_metadata: 기본 메타데이터
            
        Returns:
            파싱된 청크 리스트
        """
        if not self.can_handle(content):
            return []
        
        # Markdown 구조 분석
        sections = self._parse_markdown_sections(content)
        
        # 섹션을 청크로 변환
        chunks = self._create_chunks_from_sections(sections)
        
        # 청크를 표준 형식으로 변환
        result = []
        for i, chunk_data in enumerate(chunks):
            chunk = self._create_chunk(
                chunk_data["text"],
                base_metadata,
                chunk_index=i,
                additional_metadata={
                    "chunk_type": "markdown_section",
                    "level": chunk_data.get("level", 0),
                    "title": chunk_data.get("title", ""),
                    "parser_strategy": "markdown"
                }
            )
            result.append(chunk)
        
        return result
    
    def can_handle(self, content: str) -> bool:
        """
        Markdown 문서 처리 가능 여부 확인
        
        Args:
            content: 확인할 문서 내용
            
        Returns:
            처리 가능 여부
        """
        if not super().can_handle(content):
            return False
        
        # Markdown 패턴 확인 (제목, 리스트, 코드 블록 등)
        markdown_patterns = [
            r'^#{1,6}\s+',      # 제목 (# ## ### 등)
            r'^\s*[-*+]\s+',    # 불릿 리스트
            r'^\s*\d+\.\s+',    # 번호 리스트
            r'^```',              # 코드 블록
            r'\*\*.*?\*\*',      # 굵은 글씨
            r'\*.*?\*',          # 기울임
            r'\[.*?\]\(.*?\)',   # 링크
        ]
        
        content_lines = content.split('\n')
        markdown_line_count = 0
        
        for line in content_lines[:20]:  # 처음 20줄만 확인
            for pattern in markdown_patterns:
                if re.search(pattern, line):
                    markdown_line_count += 1
                    break
        
        # 3줄 이상에 Markdown 패턴이 있으면 Markdown 문서로 간주
        return markdown_line_count >= 3
    
    def get_parser_name(self) -> str:
        """파서 이름 반환"""
        return "Markdown"
    
    def _parse_markdown_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Markdown 문서를 섹션으로 파싱
        
        Args:
            content: 원본 Markdown 내용
            
        Returns:
            섹션 정보 리스트
        """
        sections = []
        lines = content.split('\n')
        current_section = {
            "level": 0,
            "title": "",
            "content": [],
            "start_line": 0
        }
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # 제목 패턴 확인
            header_match = re.match(r'^(#{1,6})\s+(.+)', line)
            if header_match:
                # 이전 섹션 저장
                if current_section["content"]:
                    sections.append({
                        "level": current_section["level"],
                        "title": current_section["title"],
                        "text": "\n".join(current_section["content"]),
                        "start_line": current_section["start_line"]
                    })
                
                # 새 섹션 시작
                current_section = {
                    "level": len(header_match.group(1)),
                    "title": header_match.group(2).strip(),
                    "content": [],
                    "start_line": i
                }
            else:
                # 코드 블록 처리
                if line.startswith('```'):
                    current_section["content"].append(line)
                    i += 1
                    # 코드 블록 끝 찾기
                    while i < len(lines) and not lines[i].startswith('```'):
                        current_section["content"].append(lines[i])
                        i += 1
                    if i < len(lines):
                        current_section["content"].append(lines[i])
                else:
                    current_section["content"].append(line)
            
            i += 1
        
        # 마지막 섹션 저장
        if current_section["content"]:
            sections.append({
                "level": current_section["level"],
                "title": current_section["title"],
                "text": "\n".join(current_section["content"]),
                "start_line": current_section["start_line"]
            })
        
        return sections
    
    def _create_chunks_from_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        섹션들을 적절한 크기의 청크로 변환
        
        Args:
            sections: 섹션 정보 리스트
            
        Returns:
            청크 데이터 리스트
        """
        chunks = []
        
        for section in sections:
            section_text = section["text"]
            
            if len(section_text) <= self.max_chunk_size:
                # 섹션이 작으면 그대로 청크로 사용
                chunks.append(section)
            else:
                # 섹션이 크면 문단 단위로 분할
                sub_chunks = self._split_large_section(section)
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _split_large_section(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        큰 섹션을 여러 청크로 분할
        
        Args:
            section: 분할할 섹션
            
        Returns:
            분할된 청크 리스트
        """
        text = section["text"]
        chunks = []
        
        # 문단 단위로 분할
        paragraphs = re.split(r'\n\s*\n', text)
        current_chunk_text = ""
        current_chunk_size = 0
        chunk_index = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_chunk_size + para_size + 2 <= self.max_chunk_size:
                if current_chunk_text:
                    current_chunk_text += "\n\n" + para
                else:
                    current_chunk_text = para
                current_chunk_size += para_size + (2 if current_chunk_text != para else 0)
            else:
                # 현재 청크 저장
                if current_chunk_text:
                    chunk_data = {
                        "level": section["level"],
                        "title": section["title"] if chunk_index == 0 else f"{section['title']} (계속)",
                        "text": current_chunk_text,
                        "start_line": section["start_line"]
                    }
                    chunks.append(chunk_data)
                    chunk_index += 1
                
                # 새 청크 시작
                if para_size > self.max_chunk_size:
                    # 문단이 너무 길면 강제 분할
                    sub_paragraphs = self._split_long_paragraph(para)
                    for i, sub_para in enumerate(sub_paragraphs):
                        title_suffix = f" (계속 {i+1})" if i > 0 else ""
                        chunk_data = {
                            "level": section["level"],
                            "title": section["title"] + title_suffix,
                            "text": sub_para,
                            "start_line": section["start_line"]
                        }
                        chunks.append(chunk_data)
                    current_chunk_text = ""
                    current_chunk_size = 0
                else:
                    current_chunk_text = para
                    current_chunk_size = para_size
        
        # 마지막 청크 저장
        if current_chunk_text:
            title_suffix = f" (계속 {chunk_index})" if chunk_index > 0 else ""
            chunk_data = {
                "level": section["level"],
                "title": section["title"] + title_suffix,
                "text": current_chunk_text,
                "start_line": section["start_line"]
            }
            chunks.append(chunk_data)
        
        return chunks
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """
        긴 문단 분할
        
        Args:
            paragraph: 분할할 문단
            
        Returns:
            분할된 문단 리스트
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
        sentence_patterns = ['.', '!', '?', '\n']
        
        for i in range(end - 1, start - 1, -1):
            if text[i] in sentence_patterns:
                return i + 1
        
        return start
