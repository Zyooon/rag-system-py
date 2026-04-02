"""
문서 파싱 관리 서비스
Java 프로젝트의 ParseManager와 유사한 기능 제공
"""

import re
from typing import List, Dict, Any, Optional

from parsers.document_parser import DocumentParser
from parsers.simple_line_parser import SimpleLineParser
from parsers.markdown_parser import MarkdownParser
from config import settings


class ParseManager:
    """문서 파싱 관리 전문 서비스"""
    
    def __init__(self):
        # 사용 가능한 파서들 초기화
        self.document_parsers = [
            MarkdownParser(max_chunk_size=settings.chunk_size, overlap=settings.chunk_overlap),
            SimpleLineParser(max_chunk_size=settings.chunk_size, overlap=settings.chunk_overlap)
        ]
        
        # 기본 파서 우선순위 설정
        self.default_parser_priorities = {
            "Markdown": 1,
            "SimpleLine": 2
        }
    
    def parse_document(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """
        문서 내용에 가장 적합한 파서를 선택하여 파싱 실행
        
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
            "source_type": "file"
        }
        
        # 사용 가능한 파서들을 우선순위 순서로 정렬
        sorted_parsers = self._get_sorted_parsers()
        
        # 각 파서를 시도하여 최상의 결과 선택
        for parser in sorted_parsers:
            try:
                result = parser.parse(content, base_metadata)
                
                if self._is_good_parsing_result(result, content):
                    print(f"{parser.get_parser_name()} 선택됨: {filename} -> {len(result)}개 청크")
                    return result
                
                print(f"{parser.get_parser_name()} 파싱 결과 부적합: {len(result)}개 청크")
                
            except Exception as e:
                print(f"{parser.get_parser_name()} 파싱 실패: {e}")
        
        # 모든 파서가 실패한 경우, 가장 낮은 우선순위의 파서로 기본 파싱
        fallback_parser = sorted_parsers[-1]
        print(f"모든 파서 실패, {fallback_parser.get_parser_name()}로 기본 파싱: {filename}")
        return fallback_parser.parse(content, base_metadata)
    
    def _get_sorted_parsers(self) -> List[DocumentParser]:
        """
        파서 우선순위에 따라 정렬된 파서 리스트 반환
        
        Returns:
            우선순위 순서로 정렬된 DocumentParser 리스트
        """
        return sorted(self.document_parsers, key=self._get_parser_priority)
    
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
        if len(documents) < 2:
            return False
        
        # 2. 파싱된 내용의 총 길이가 원본의 50% 이상인지 확인
        total_parsed_length = sum(len(doc.get("text", "")) for doc in documents)
        
        coverage_ratio = total_parsed_length / len(original_content)
        if coverage_ratio < 0.5:
            print(f"파싱 커버리지 낮음: {int(coverage_ratio * 100)}%")
            return False
        
        # 3. 각 청크의 평균 길이가 적절한지 확인 (너무 짧으면 안 좋음)
        avg_chunk_length = total_parsed_length / len(documents)
        if avg_chunk_length < 20:
            print(f"청크 평균 길이 너무 짧음: {int(avg_chunk_length)}자")
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
        
        else:
            print(f"알 수 없는 파서: {parser_name}")
