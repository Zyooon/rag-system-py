"""
문서 파서 공통 인터페이스
Java 프로젝트의 DocumentParser와 유사한 기능 제공
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class DocumentParser(ABC):
    """문서 파서 공통 추상 클래스"""
    
    @abstractmethod
    def parse(self, content: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        문서 내용을 파싱하여 구조화된 청크 리스트로 변환
        
        Args:
            content: 파싱할 원본 문서 내용
            base_metadata: 문서에 추가할 기본 메타데이터 (파일명 등)
            
        Returns:
            파싱된 청크 딕셔너리 리스트. 각 청크는 'text'와 'metadata' 키를 가짐
            파싱 실패 시 빈 리스트 반환
            
        Raises:
            ValueError: content가 None이거나 비어있을 경우
        """
        pass
    
    def can_handle(self, content: str) -> bool:
        """
        이 파서가 지정된 문서 내용을 처리할 수 있는지 확인
        
        Args:
            content: 확인할 문서 내용
            
        Returns:
            처리 가능하면 True, 아니면 False
        """
        return content is not None and not content.strip().isspace()
    
    @abstractmethod
    def get_parser_name(self) -> str:
        """
        파서의 이름/타입을 반환
        
        Returns:
            파서를 식별하는 고유한 이름
        """
        pass
    
    def _create_chunk(self, text: str, base_metadata: Dict[str, Any], 
                     chunk_index: int = 0, additional_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        표준 청크 생성 헬퍼 메서드
        
        Args:
            text: 청크 텍스트
            base_metadata: 기본 메타데이터
            chunk_index: 청크 인덱스
            additional_metadata: 추가 메타데이터
            
        Returns:
            표준 청크 딕셔너리
        """
        metadata = base_metadata.copy()
        metadata["chunk_index"] = chunk_index
        metadata["parser"] = self.get_parser_name()
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return {
            "text": text.strip(),
            "metadata": metadata
        }
