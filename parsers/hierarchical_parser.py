"""
계층적 구조 문서 파서
Java 프로젝트의 HierarchicalParser와 유사한 기능 제공
구조화된 텍스트, 번호 목록, Markdown 형식을 지원하여 맥락별 분할
"""

import re
from typing import List, Dict, Any, Tuple, Optional

from .document_parser import DocumentParser


class HierarchicalParser(DocumentParser):
    """계층적 구조 문서 파서"""
    
    def __init__(self):
        """초기화"""
        # 현재 제목 상태 (자바와 동일)
        self.current_h1 = ""  # 대제목 (Level 1)
        self.current_h2 = ""  # 중제목 (Level 2)
        self.current_h3 = ""  # 소제목 (Level 3)
        
        # 제목 패턴 정의 (마크다운 형식 우선) - 자바와 동일
        self.heading_patterns = [
            # 마크다운 제목 형식 (우선순위 높음)
            re.compile(r"^###\s+(.+)$"),         # ### 소소제목
            re.compile(r"^##\s+(.+)$"),          # ## 소제목  
            re.compile(r"^#\s+(.+)$"),           # # 제목
            
            # 마크다운 목록 형식
            re.compile(r"^-\s*\*\*(.+?)\*\*:\s*(.+)$"), # Markdown 굵은 글씨 항목
            re.compile(r"^-\s+(.+)$"),            # 일반 목록 항목
            
            # 기타 구조화된 형식
            re.compile(r"^\d+\.\d+\.\s+(.+)$"), # 1.1. 소제목
            re.compile(r"^\d+\.\s+(.+)$"),     # 1. 제목
            re.compile(r"^\[(.+)\]$"),            # [제목] - 대괄호 제목
            re.compile(r"^제목:\s*(.+)$"),       # 제목: 내용
            re.compile(r"^\|.*\|$")            # 표 형식 (테이블)
        ]
    
    def can_handle(self, content: str) -> bool:
        """
        파서가 해당 내용을 처리할 수 있는지 확인
        
        Args:
            content: 확인할 내용
            
        Returns:
            처리 가능 여부
        """
        lines = content.split('\n')
        total_lines = len([l for l in lines if l.strip()])
        
        if total_lines < 5:  # 너무 짧은 문서는 처리하지 않음
            return False
        
        # 불릿형 데이터 확인
        if self._contains_bullets_with_headers(content):
            return True
        
        # Markdown 형식 확인
        if self._is_markdown_document(content):
            return True
        
        # 일반 구조화된 문서 확인
        return any(self._is_heading(line) for line in lines if line.strip())
    
    def parse(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        텍스트를 구조화된 문서 목록으로 파싱
        
        Args:
            content: 파싱할 텍스트 내용
            metadata: 기본 메타데이터
            
        Returns:
            구조화된 문서 목록
        """
        # 불릿형 데이터를 위한 부모-자식 구조 파싱
        if self._contains_bullets_with_headers(content):
            return self._parse_bullet_with_header(content, metadata)
        
        # Markdown 형식 감지 및 처리
        if self._is_markdown_document(content):
            return self._parse_markdown_document(content, metadata)
        
        # 기존的一般 파싱 로직
        return self._parse_general_document(content, metadata)
    
    def _is_heading(self, line: str) -> bool:
        """라인이 제목인지 확인"""
        if not line.strip():
            return False
        
        for pattern in self.heading_patterns:
            if pattern.match(line):
                return True
        return False
    
    def _is_list_item(self, line: str) -> bool:
        """라인이 목록 항목인지 확인"""
        if not line.strip():
            return False
        
        # 목록 항목 패턴 확인 - 자바와 동일
        return (re.match(r"^\-\s+(.+)$", line) or           # - 항목
                re.match(r"^\d+\.\s+(.+)$", line) or      # 1. 항목
                re.match(r"^\*\s+(.+)$", line) or          # * 항목
                re.match(r"^•\s+(.+)$", line) or            # • 항목
                line.startswith("- **") or                # - **굵은글씨**
                line.startswith("기능:") or               # 기능: 내용
                line.startswith("특징:") or               # 특징: 내용
                line.startswith("효능:") or               # 효능: 내용
                line.startswith("배터리:") or             # 배터리: 내용
                re.match(r"^[가-힣]+:.*$", line))         # 한글 단어: 내용
    
    def _contains_bullets_with_headers(self, content: str) -> bool:
        """
        불릿형 데이터가 있는지 확인 (부모-자식 구조)
        sample-bullet.txt 같은 진짜 불릿 문서만 true 반환
        sample-odd.txt는 무조건 일반 불릿으로 처리
        """
        lines = content.split('\n')
        has_numbered_header = False
        has_bullets = False
        numbered_header_count = 0
        
        for line in lines:
            trimmed_line = line.strip()
            
            # 숫자 헤더 확인 (1. 항목, 2. 항목...)
            if re.match(r'^\d+\.\s+.+$', trimmed_line):
                has_numbered_header = True
                numbered_header_count += 1
            
            # 불릿 확인 (- 항목)
            if re.match(r'^-\s+.+$', trimmed_line):
                has_bullets = True
        
        # 진짜 불릿 문서인지 확인 (숫자 헤더가 2개 이상이고 불릿도 있어야 함)
        return has_numbered_header and has_bullets and numbered_header_count >= 2
    
    def _is_markdown_document(self, content: str) -> bool:
        """Markdown 문서인지 확인"""
        lines = content.split('\n')
        markdown_patterns = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 마크다운 패턴 확인
            if (re.match(r'^#+\s+', line) or          # # 제목
                re.match(r'^\*\*.*\*\*$', line) or    # **굵은글씨**
                re.match(r'^\*.*\*$', line) or        # *기울임*
                re.match(r'^```', line) or            # 코드 블록
                re.match(r'^\|.*\|$', line) or       # 표
                re.match(r'^-\s+', line) or          # 목록
                re.match(r'^\d+\.\s+', line)):       # 번호 목록
                markdown_patterns += 1
        
        # 마크다운 패턴이 일정 이상 있으면 마크다운 문서로 간주
        total_lines = len([l for l in lines if l.strip()])
        return total_lines >= 5 and markdown_patterns >= 2
    
    def _parse_bullet_with_header(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """불릿형 데이터 파싱 (부모-자식 구조)"""
        lines = content.split('\n')
        result = []
        
        current_header = ""
        current_body = []
        header_line_num = -1
        
        for i, line in enumerate(lines):
            trimmed_line = line.strip()
            
            # 새로운 아이템 시작 확인
            if self._is_new_item_start(trimmed_line):
                # 이전 아이템 저장
                if current_header and current_body:
                    self._save_current_chunk(result, current_header, current_body, header_line_num, metadata)
                
                # 신규 아이템 시작
                current_header = trimmed_line
                current_body = []
                header_line_num = i
            # 내용 누적: 다음 숫자가 나오기 전까지의 모든 불릿(-)들을 해당 아이템 조각에 다 집어넣어
            elif trimmed_line and not current_header == "":
                current_body.append(line)
        
        # 마지막 아이템 저장
        if current_header and current_body:
            self._save_current_chunk(result, current_header, current_body, header_line_num, metadata)
        
        return result
    
    def _is_new_item_start(self, line: str) -> bool:
        """
        새로운 아이템 시작인지 엄격하게 확인 (가짜 제목 방지)
        """
        # 1. "숫자. " 형식인지 확인 (줄의 시작점에서 숫자+점+공백+내용)
        if not re.match(r'^\d+\.\s+.+$', line):
            return False
        
        # 2. 추가 검증: 제목은 보통 한 줄 내외(50자 미만)이므로 길이 체크
        if len(line) > 50:
            return False
        
        # 3. 불릿으로 시작하는 줄은 무조건 내용으로 간주 (숫자 무시)
        if line.startswith("-") or line.startswith("*") or line.startswith("•"):
            return False
        
        return True
    
    def _save_current_chunk(self, result: List[Dict[str, Any]], header: str, 
                           body: List[str], header_line_num: int, metadata: Dict[str, Any]):
        """현재 아이템 조각 저장"""
        if header and body:
            content = header + '\n' + '\n'.join(body)
            
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'title': self._extract_title(header),
                'header_line': header_line_num,
                'chunk_type': 'bullet_item'
            })
            
            result.append({
                'text': content,
                'metadata': chunk_metadata
            })
    
    def _extract_title(self, line: str) -> str:
        """제목 추출 (자바와 동일)"""
        # 번호 접두사 제거
        title = re.sub(r'^\d+\.?\d*\.?\s*', '', line)
        # 대괄호 제거
        title = re.sub(r'^\[|\]$', '', title)
        # "제목:" 접두사 제거
        title = re.sub(r'^제목:\s*', '', title)
        return title.strip()
    
    def _parse_markdown_document(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Markdown 문서 파싱"""
        # 간단한 Markdown 파싱 구현
        lines = content.split('\n')
        result = []
        current_section = ""
        current_content = []
        current_title = ""
        
        for line in lines:
            trimmed_line = line.strip()
            
            # 제목 확인
            if re.match(r'^#+\s+', trimmed_line):
                # 이전 섹션 저장
                if current_section and current_content:
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'title': current_title,
                        'section_type': 'markdown'
                    })
                    
                    result.append({
                        'text': current_section,
                        'metadata': chunk_metadata
                    })
                
                # 새 섹션 시작
                current_title = re.sub(r'^#+\s+', '', trimmed_line)
                current_section = line
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
                else:
                    current_section = line
                    current_content = []
        
        # 마지막 섹션 저장
        if current_section and current_content:
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'title': current_title or '미분류',
                'section_type': 'markdown'
            })
            
            result.append({
                'text': current_section,
                'metadata': chunk_metadata
            })
        
        return result
    
    def _parse_general_document(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """일반 문서 파싱"""
        lines = content.split('\n')
        result = []
        
        # 제목 상태 초기화
        self.current_h1 = ""
        self.current_h2 = ""
        self.current_h3 = ""
        
        current_content = []
        
        for line in lines:
            trimmed_line = line.strip()
            
            # 제목 확인
            if self._is_heading(trimmed_line):
                # 이전 내용 저장
                if current_content:
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'title': self._get_current_title(),
                        'h1': self.current_h1,
                        'h2': self.current_h2,
                        'h3': self.current_h3
                    })
                    
                    result.append({
                        'text': '\n'.join(current_content),
                        'metadata': chunk_metadata
                    })
                
                # 새 제목 처리
                self._update_heading_state(trimmed_line)
                current_content = [line]
            else:
                current_content.append(line)
        
        # 마지막 내용 저장
        if current_content:
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'title': self._get_current_title(),
                'h1': self.current_h1,
                'h2': self.current_h2,
                'h3': self.current_h3
            })
            
            result.append({
                'text': '\n'.join(current_content),
                'metadata': chunk_metadata
            })
        
        return result
    
    def _update_heading_state(self, line: str) -> None:
        """제목 상태 업데이트"""
        for pattern in self.heading_patterns:
            match = pattern.match(line)
            if match:
                title = match.group(1) if match.groups() else match.group(0)
                
                # 제목 레벨에 따라 상태 업데이트
                if pattern.pattern.startswith(r'^###'):
                    self.current_h3 = title
                elif pattern.pattern.startswith(r'^##'):
                    self.current_h2 = title
                    self.current_h3 = ""
                elif pattern.pattern.startswith(r'^#\s'):
                    self.current_h1 = title
                    self.current_h2 = ""
                    self.current_h3 = ""
                else:
                    # 기타 제목 패턴
                    self.current_h2 = title
                    self.current_h3 = ""
                break
    
    def _get_current_title(self) -> str:
        """현재 제목 가져오기"""
        if self.current_h3:
            return self.current_h3
        elif self.current_h2:
            return self.current_h2
        elif self.current_h1:
            return self.current_h1
        else:
            return "미분류"
    
    def get_parser_name(self) -> str:
        """파서 이름 반환"""
        return "hierarchical"
