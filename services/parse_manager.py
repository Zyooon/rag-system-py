"""
문서 파싱 관리 서비스
Java 프로젝트의 ParseManager와 유사한 기능 제공
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from parsers.document_parser import DocumentParser
from parsers.simple_line_parser import SimpleLineParser
from parsers.markdown_parser import MarkdownParser
from parsers.hierarchical_parser import HierarchicalParser
from splitters.text_splitter_processor import TextSplitterProcessor
from config import settings


class ParseManager:
    """문서 파싱 관리 전문 서비스 - 하이브리드 파싱 방식 지원"""
    
    def __init__(self):
        # 사용 가능한 파서들 초기화 (제안된 우선순위 적용)
        self.document_parsers = [
            MarkdownParser(max_chunk_size=settings.chunk_size, overlap=settings.chunk_overlap),
            HierarchicalParser(),
            SimpleLineParser(max_chunk_size=settings.chunk_size, overlap=settings.chunk_overlap)
        ]
        
        # TextSplitterProcessor 초기화 (하이브리드 방식용)
        self.text_splitter = TextSplitterProcessor()
        
        # 기본 파서 우선순위 설정 (계층적 구조 우선) - settings.py에서 가져오기
        self.default_parser_priorities = {
            "hierarchical": settings.hierarchical_parser_priority,    # 1., 1.1, (1) 같은 숫자 패턴 (불릿 포함) - 우선순위 최상
            "Markdown": settings.markdown_parser_priority,        # #, ## 같은 헤더 기반
            "SimpleLine": settings.simple_line_parser_priority       # 문단 단위 (\n\n)
        }
    
    def parse_document(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """
        문서 내용에 가장 적합한 파서를 선택하여 파싱 실행 (하이브리드 방식)
        
        Args:
            content: 원본 문서 내용
            filename: 파일명 (메타데이터용)
            
        Returns:
            파싱된 청크 리스트
        """
        print(f"문서 파싱 시작: {filename} (길이: {len(content)})")
        
        # 기본 메타데이터 생성
        base_metadata = {
            "filename": filename,
            "source_type": "file",
            "saved_at": datetime.now().isoformat(),
            "parser_type": "hybrid"
        }
        
        # 사용 가능한 파서들을 우선순위 순서로 정렬
        sorted_parsers = self._get_sorted_parsers()
        
        print(f"사용 가능한 파서: {[p.get_parser_name() for p in sorted_parsers]}")
        
        # 1단계: 구조적 파싱 시도
        structural_chunks = self._try_structural_parsing(content, base_metadata, sorted_parsers)
        
        if structural_chunks:
            print(f"구조적 파싱 성공: {filename} -> {len(structural_chunks)}개 청크")
            return structural_chunks
        
        # 2단계: 하이브리드 파싱 (구조적 분할 + 재귀적 분할)
        print(f"구조적 파싱 실패, 하이브리드 파싱 시도: {filename}")
        return self._hybrid_parsing(content, base_metadata)
    
    def _get_sorted_parsers(self) -> List[DocumentParser]:
        """
        파서 우선순위에 따라 정렬된 파서 리스트 반환
        
        Returns:
            우선순위 순서로 정렬된 DocumentParser 리스트
        """
        return sorted(self.document_parsers, key=self._get_parser_priority)
    
    def _try_structural_parsing(self, content: str, base_metadata: Dict[str, Any], sorted_parsers: List[DocumentParser]) -> List[Dict[str, Any]]:
        """
        구조적 파싱 시도 (기존 방식)
        
        Args:
            content: 원본 내용
            base_metadata: 기본 메타데이터
            sorted_parsers: 정렬된 파서 리스트
            
        Returns:
            구조적 파싱 결과 또는 빈 리스트
        """
        for parser in sorted_parsers:
            try:
                can_handle = parser.can_handle(content)
                print(f"{parser.get_parser_name()} can_handle: {can_handle}")
                
                if can_handle:
                    result = parser.parse(content, base_metadata)
                    
                    if self._is_good_parsing_result(result, content):
                        print(f"{parser.get_parser_name()} 선택됨: {len(result)}개 청크")
                        return result
                    
                    print(f"{parser.get_parser_name()} 파싱 결과 부적합: {len(result)}개 청크")
                else:
                    print(f"{parser.get_parser_name()} 처리 불가")
                
            except Exception as e:
                print(f"{parser.get_parser_name()} 파싱 실패: {e}")
        
        return []
    
    def _hybrid_parsing(self, content: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        하이브리드 파싱: 구조적 분할 + 재귀적 분할
        
        Args:
            content: 원본 내용
            base_metadata: 기본 메타데이터
            
        Returns:
            하이브리드 파싱 결과
        """
        print("하이브리드 파싱 시작: 구조적 분할 + 재귀적 분할")
        
        # 1단계: 구조적 시작점 찾기
        structural_sections = self._find_structural_sections(content)
        
        if not structural_sections:
            print("구조적 시작점 없음, LangChain RecursiveCharacterTextSplitter로 직접 분할")
            return self._fallback_recursive_splitting(content, base_metadata)
        
        # 2단계: 각 구조적 섹션을 재귀적 분할기로 처리
        final_chunks = []
        chunk_index = 0
        
        for i, section in enumerate(structural_sections):
            section_text = section["text"]
            section_title = section["title"]
            
            # 섹션이 너무 크면 재귀적 분할기 적용
            if len(section_text) > settings.chunk_size:
                print(f"섹션 '{section_title}' 재귀적 분할: {len(section_text)}자")
                section_chunks = self.text_splitter.split_text(section_text, {
                    **base_metadata,
                    "section_title": section_title,
                    "section_index": i,
                    "parser_type": "hybrid_recursive"
                })
                
                # 청크 인덱스 재조정
                for chunk in section_chunks:
                    chunk["metadata"]["chunk_index"] = chunk_index
                    chunk_index += 1
                    final_chunks.append(chunk)
            else:
                # 섹션이 작으면 그대로 사용
                chunk_metadata = {
                    **base_metadata,
                    "chunk_index": chunk_index,
                    "section_title": section_title,
                    "section_index": i,
                    "parser_type": "hybrid_structural",
                    "chunk_length": len(section_text)
                }
                
                final_chunks.append({
                    "text": section_text,
                    "metadata": chunk_metadata
                })
                chunk_index += 1
        
        print(f"하이브리드 파싱 완료: {len(final_chunks)}개 청크")
        return final_chunks
    
    def _find_structural_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        구조적 시작점 찾기 (강화된 패턴 지원)
        
        Args:
            content: 원본 내용
            
        Returns:
            구조적 섹션 리스트
        """
        lines = content.split('\n')
        sections = []
        current_section = ""
        current_title = "미분류"
        
        # 강화된 구조적 패턴
        structural_patterns = [
            r'^#{1,6}\s+(.+)$',           # 마크다운 제목
            r'^\d+\.\s+(.+)$',            # 1. 제목
            r'^\d+\.\d+\.\s+(.+)$',      # 1.1. 제목
            r'^\d+\.\d+\.\d+\.\s+(.+)$', # 1.1.1. 제목
            r'^\(\d+\)\s+(.+)$',          # (1) 제목
            r'^\[\d+\]\s+(.+)$',          # [1] 제목
            r'^[가-힣]+\.\s+(.+)$',        # 가. 제목
            r'^\([가-힣]\)\s+(.+)$',       # 가) 제목
            r'^ㄱ\.\s+(.+)$',              # ㄱ. 제목
            r'^ㄱ\)\s+(.+)$',               # ㄱ) 제목
            r'^[IVX]+\.\s+(.+)$',          # I. 제목
        ]
        
        for line in lines:
            line_stripped = line.strip()
            
            # 구조적 패턴 확인
            is_structural = False
            for pattern in structural_patterns:
                match = re.match(pattern, line_stripped)
                if match:
                    # 이전 섹션 저장
                    if current_section.strip():
                        sections.append({
                            "title": current_title,
                            "text": current_section.strip()
                        })
                    
                    # 새 섹션 시작
                    current_title = match.group(1) if match.groups() else line_stripped
                    current_section = line
                    is_structural = True
                    break
            
            if not is_structural:
                # 일반 내용은 현재 섹션에 추가
                if current_section:
                    current_section += "\n" + line
                else:
                    current_section = line
        
        # 마지막 섹션 저장
        if current_section.strip():
            sections.append({
                "title": current_title,
                "text": current_section.strip()
            })
        
        print(f"구조적 섹션 발견: {len(sections)}개")
        return sections
    
    def _fallback_recursive_splitting(self, content: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        최후의 수단: LangChain RecursiveCharacterTextSplitter로 직접 분할
        
        Args:
            content: 원본 내용
            base_metadata: 기본 메타데이터
            
        Returns:
            재귀적 분할 결과
        """
        print("최후의 수단: LangChain RecursiveCharacterTextSplitter 직접 분할")
        return self.text_splitter.split_text(content, {
            **base_metadata,
            "parser_type": "recursive_fallback"
        })
    
    def _get_parser_priority(self, parser: DocumentParser) -> int:
        """
        파서별 우선순위 반환 (낮을수록 높은 우선순위)
        
        Args:
            parser: 우선순위를 계산할 파서
            
        Returns:
            우선순위 값
        """
        parser_name = parser.get_parser_name()
        return self.default_parser_priorities.get(parser_name, 999)
    
    def get_available_parsers(self) -> Dict[str, int]:
        """
        사용 가능한 모든 파서 정보 반환 (디버깅용)
        
        Returns:
            파서 이름과 우선순위 정보
        """
        parser_info = {}
        
        for parser in self._get_sorted_parsers():
            parser_info[parser.get_parser_name()] = self._get_parser_priority(parser)
        
        return parser_info
    
    def parse_with_specific_parser(self, parser_name: str, content: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        특정 파서로 파싱 시도 (테스트용)
        
        Args:
            parser_name: 사용할 파서 이름
            content: 파싱할 내용
            base_metadata: 기본 메타데이터
            
        Returns:
            파싱 결과
        """
        target_parser = None
        for parser in self.document_parsers:
            if parser.get_parser_name() == parser_name:
                target_parser = parser
                break
        
        if target_parser:
            try:
                return target_parser.parse(content, base_metadata)
            except Exception as e:
                print(f"{parser_name} 파싱 실패: {e}")
                return []
        else:
            print(f"파서를 찾을 수 없음: {parser_name}")
            return []
    
    def _is_good_parsing_result(self, documents: List[Dict[str, Any]], original_content: str) -> bool:
        """
        파싱 결과의 품질 평가
        
        Args:
            documents: 파싱된 문서 리스트
            original_content: 원본 내용
            
        Returns:
            품질 평가 결과
        """
        if not documents:
            return False
        
        # 1. 최소 청크 수 확인 (너무 적게 나뉘면 안 좋음)
        if len(documents) < 1:
            return False
        
        # 2. 파싱된 내용의 총 길이가 원본의 70% 이상인지 확인 (HierarchicalParser는 더 높은 커버리지 필요)
        total_parsed_length = sum(len(doc.get("text", "")) for doc in documents)
        
        coverage_ratio = total_parsed_length / len(original_content)
        if coverage_ratio < 0.7:
            print(f"파싱 커버리지 낮음: {int(coverage_ratio * 100)}%")
            return False
        
        # 3. 각 청크의 평균 길이가 적절한지 확인 (너무 짧으면 안 좋음)
        avg_chunk_length = total_parsed_length / len(documents)
        if avg_chunk_length < 50 and len(documents) > 1:  # 여러 청크일 때만 평균 길이 체크
            print(f"청크 평균 길이 너무 짧음: {int(avg_chunk_length)}자")
            return False
        
        # 4. 청크가 너무 많이 나뉘었는지 확인 (과도한 분할 방지)
        if len(documents) > 50:
            print(f"청크 수 너무 많음: {len(documents)}개")
            return False
        
        return True
    
    def analyze_document_features(self, content: str) -> None:
        """
        문서 특징 분석 (디버깅용)
        
        Args:
            content: 분석할 내용
        """
        print("문서 특징 분석 시작")
        
        # 전체 라인 수
        total_lines = len(content.splitlines())
        print(f"전체 라인: {total_lines}")
        
        # 각 파서별 특징 분석
        for parser in self.document_parsers:
            self._analyze_parser_features(content, parser, total_lines)
    
    def _analyze_parser_features(self, content: str, parser: DocumentParser, total_lines: int) -> None:
        """
        특정 파서의 특징 분석
        
        Args:
            content: 분석할 내용
            parser: 분석할 파서
            total_lines: 전체 라인 수
        """
        parser_name = parser.get_parser_name()
        
        if parser_name == "Markdown":
            # Markdown 패턴 확인
            lines = content.splitlines()
            markdown_patterns = 0
            
            for line in lines:
                if re.match(r'^#{1,6}\s+', line):  # 제목
                    markdown_patterns += 1
                elif re.match(r'^\s*[-*+]\s+', line):  # 불릿 리스트
                    markdown_patterns += 1
                elif re.match(r'^\s*\d+\.\s+', line):  # 번호 리스트
                    markdown_patterns += 1
                elif line.startswith('```'):  # 코드 블록
                    markdown_patterns += 1
            
            percentage = (markdown_patterns * 100 // total_lines) if total_lines > 0 else 0
            print(f"{parser_name} 패턴: {markdown_patterns}개 ({percentage}%)")
            
        elif parser_name == "SimpleLine":
            # SimpleLineParser는 특별한 패턴이 없으므로 기본 정보만 출력
            print(f"{parser_name}: 일반 텍스트 파서 (특별한 패턴 없음)")
        
        elif parser_name == "Hierarchical":
            # 계층적 패턴 확인
            lines = content.splitlines()
            hierarchical_patterns = 0
            bullet_patterns = 0
            
            for line in lines:
                line_stripped = line.strip()
                if re.match(r'^\s*\d+\.\s+', line_stripped):  # 1., 2. ...
                    hierarchical_patterns += 1
                elif re.match(r'^\s*\d+\.\d+\s+', line_stripped):  # 1.1, 1.2 ...
                    hierarchical_patterns += 1
                elif re.match(r'^\s*\(\d+\)\s+', line_stripped):  # (1), (2) ...
                    hierarchical_patterns += 1
                elif re.match(r'^\s*[-*+•]\s+', line_stripped):  # 불릿
                    bullet_patterns += 1
                elif re.match(r'^\s*[가-힣]\.\s+', line_stripped):  # 가. 나. ...
                    hierarchical_patterns += 1
            
            total_patterns = hierarchical_patterns + bullet_patterns
            percentage = (total_patterns * 100 // total_lines) if total_lines > 0 else 0
            print(f"{parser_name} 패턴: 계층적 {hierarchical_patterns}개, 불릿 {bullet_patterns}개 ({percentage}%)")
        
        else:
            print(f"알 수 없는 파서: {parser_name}")
