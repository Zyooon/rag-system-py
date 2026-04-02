"""
메타데이터 유틸리티
문서 파싱 및 분할 시 메타데이터 보존을 위한 공통 기능 제공
"""

from typing import Dict, Any
from datetime import datetime


class MetadataUtils:
    """메타데이터 관리 유틸리티 클래스"""
    
    @staticmethod
    def create_base_metadata(filename: str, source_type: str = "file") -> Dict[str, Any]:
        """
        기본 메타데이터 생성
        
        Args:
            filename: 파일명
            source_type: 소스 타입 (기본값: "file")
            
        Returns:
            기본 메타데이터 딕셔너리
        """
        return {
            "filename": filename,
            "source_type": source_type,
            "saved_at": datetime.now().isoformat(),
            "parser_type": "unknown"
        }
    
    @staticmethod
    def enhance_chunk_metadata(
        base_metadata: Dict[str, Any], 
        chunk_index: int, 
        parser_type: str,
        chunk_length: int = 0,
        additional_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        청크 메타데이터 강화
        
        Args:
            base_metadata: 기본 메타데이터
            chunk_index: 청크 인덱스
            parser_type: 파서 타입
            chunk_length: 청크 길이
            additional_metadata: 추가 메타데이터
            
        Returns:
            강화된 메타데이터
        """
        enhanced = {
            **base_metadata,
            "chunk_index": chunk_index,
            "parser_type": parser_type,
            "chunk_length": chunk_length,
            "processed_at": datetime.now().isoformat()
        }
        
        if additional_metadata:
            enhanced.update(additional_metadata)
        
        return enhanced
    
    @staticmethod
    def ensure_required_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        필수 메타데이터 필드 보장
        
        Args:
            metadata: 원본 메타데이터
            
        Returns:
            필수 필드가 보장된 메타데이터
        """
        required_fields = {
            "filename": "unknown",
            "source_type": "file",
            "saved_at": datetime.now().isoformat(),
            "parser_type": "unknown",
            "chunk_index": 0
        }
        
        # 기존 메타데이터에 없는 필수 필드 추가
        for field, default_value in required_fields.items():
            if field not in metadata:
                metadata[field] = default_value
        
        return metadata
    
    @staticmethod
    def create_chunk_metadata(
        filename: str,
        chunk_index: int,
        parser_type: str,
        chunk_length: int = 0,
        section_title: str = None,
        section_index: int = None,
        additional_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        완전한 청크 메타데이터 생성 (일회용)
        
        Args:
            filename: 파일명
            chunk_index: 청크 인덱스
            parser_type: 파서 타입
            chunk_length: 청크 길이
            section_title: 섹션 제목 (선택사항)
            section_index: 섹션 인덱스 (선택사항)
            additional_metadata: 추가 메타데이터 (선택사항)
            
        Returns:
            완전한 청크 메타데이터
        """
        metadata = {
            "filename": filename,
            "source_type": "file",
            "saved_at": datetime.now().isoformat(),
            "chunk_index": chunk_index,
            "parser_type": parser_type,
            "chunk_length": chunk_length,
            "processed_at": datetime.now().isoformat()
        }
        
        if section_title is not None:
            metadata["section_title"] = section_title
            
        if section_index is not None:
            metadata["section_index"] = section_index
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return metadata
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> bool:
        """
        메타데이터 유효성 검사
        
        Args:
            metadata: 검사할 메타데이터
            
        Returns:
            유효성 여부
        """
        required_fields = ["filename", "chunk_index", "parser_type"]
        
        for field in required_fields:
            if field not in metadata:
                return False
        
        # filename이 문자열이고 비어있지 않은지 확인
        if not isinstance(metadata.get("filename"), str) or not metadata["filename"].strip():
            return False
        
        # chunk_index가 정수인지 확인
        if not isinstance(metadata.get("chunk_index"), int) or metadata["chunk_index"] < 0:
            return False
        
        # parser_type이 문자열이고 비어있지 않은지 확인
        if not isinstance(metadata.get("parser_type"), str) or not metadata["parser_type"].strip():
            return False
        
        return True
    
    @staticmethod
    def get_metadata_summary(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        메타데이터 요약 정보 생성
        
        Args:
            metadata: 원본 메타데이터
            
        Returns:
            메타데이터 요약
        """
        return {
            "filename": metadata.get("filename", "unknown"),
            "chunk_index": metadata.get("chunk_index", 0),
            "parser_type": metadata.get("parser_type", "unknown"),
            "chunk_length": metadata.get("chunk_length", 0),
            "saved_at": metadata.get("saved_at"),
            "has_section": "section_title" in metadata,
            "additional_fields": len([k for k in metadata.keys() 
                                   if k not in ["filename", "chunk_index", "parser_type", 
                                              "chunk_length", "saved_at", "source_type", 
                                              "processed_at", "section_title", "section_index"]])
        }
