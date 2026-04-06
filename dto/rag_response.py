"""
RAG 응답 DTO
Java 프로젝트의 RagResponse와 유사한 기능 제공
"""

from typing import Any, Optional, Dict
from pydantic import BaseModel


class SourceInfo(BaseModel):
    """출처 정보 모델 - Java SourceInfo와 호환"""
    filename: str
    chunk_id: Optional[str] = None
    similarity_score: Optional[float] = None
    content: Optional[str] = None
    
    # 하위 호환성을 위한 필드들
    chunk_index: Optional[int] = None
    content_preview: Optional[str] = None
    
    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "SourceInfo":
        """
        문서 데이터에서 SourceInfo 객체 생성
        
        Args:
            document: 문서 데이터 (text, metadata, similarity_score 포함)
            
        Returns:
            SourceInfo 객체
        """
        # 문서 내용 및 메타데이터 추출
        content = document.get("text", "")
        metadata = document.get("metadata", {})
        
        # 디버깅용 로그
        print(f"Document metadata keys: {list(metadata.keys())}")
        print(f"Document metadata: {metadata}")
        content_preview = content[:100] + "..." if len(content) > 100 else content
        print(f"Document content preview: {content_preview}")
        
        # 메타데이터에서 파일명 추출
        filename = metadata.get("filename", "")
        print(f"Extracted filename: {filename}")
        
        # 메타데이터에 파일명이 없으면 기본값 설정
        if not filename or filename == "unknown":
            filename = "unknown_file"
            print(f"Using default filename: {filename}")
        
        # 문서 내용에서 제목 추출
        lines = content.split("\n")
        document_title = ""
        
        print("First few lines for title extraction:")
        for i in range(min(len(lines), 5)):
            print(f"Line {i}: '{lines[i]}'")
        
        for i in range(min(len(lines), 10)):
            line = lines[i].strip()
            
            # 테이블 헤더는 제목으로 처리하지 않음
            if line.startswith("|") and "|" in line:
                continue
            
            # 대괄호 제목
            if line.startswith("[") and line.endswith("]"):
                document_title = line[1:-1].strip()
                print(f"Found bracket title: '{document_title}'")
                break
            # 마크다운 제목
            elif line.startswith("# "):
                document_title = line[2:].strip()
                print(f"Found markdown title: '{document_title}'")
                break
            # 제목: 형식
            elif line.startswith("제목:"):
                document_title = line[3:].strip()
                print(f"Found Korean title: '{document_title}'")
                break
        
        # 제목을 찾지 못했으면 파일명 기반으로 생성
        if not document_title:
            # 테이블 내용은 제외하고 파일명에서 제목 추출
            if "|" in content and "ITEM_" in content:
                # 테이블 내용에서 첫 번째 ITEM 내용 추출
                table_lines = content.split("\n")
                for line in table_lines:
                    trimmed_line = line.strip()
                    if trimmed_line.startswith("|") and "ITEM_" in trimmed_line:
                        # 테이블 행에서 ITEM 내용만 추출
                        parts = trimmed_line.split("|")
                        if len(parts) >= 3:
                            # ITEM_ID와 이름을 조합하여 content 생성
                            item_id = parts[1].strip()
                            item_name = parts[2].strip()
                            document_title = f"{item_id} {item_name}"
                            break
                
                # ITEM을 찾지 못한 경우 빈 문자열로 설정
                if not document_title:
                    document_title = "테이블 항목"
            else:
                document_title = filename.replace(".txt", "").replace(".md", "")
            print(f"Using fallback title: '{document_title}'")
        
        print(f"Final SourceInfo - filename: '{filename}', content: '{document_title}'")
        
        # 점수 및 ID 설정 (이미 포맷팅된 점수 사용)
        similarity_score = document.get("similarity_score", 0.0)
        
        # 점수가 이미 포맷팅되었는지 확인하고, 아니면 포맷팅
        if similarity_score is not None:
            if isinstance(similarity_score, str):
                try:
                    similarity_score = float(similarity_score)
                except ValueError:
                    similarity_score = 0.0
            
            # 소수점 2자리로 포맷팅 (이미 포맷팅되었더라도 안전하게 처리)
            similarity_score = round(float(similarity_score), 2)
        
        # 임계값 체크 (설정된 임계값과 비교)
        from config import settings
        search_threshold = getattr(settings, 'search_threshold', 0.3)
        
        if similarity_score < search_threshold:
            print(f"⚠️ 낮은 유사도 점수: {similarity_score:.2f} < 임계값 {search_threshold}")
        
        chunk_id = metadata.get("chunk_id")
        if chunk_id is not None:
            chunk_id = str(chunk_id)
        
        return cls(
            filename=filename,
            chunk_id=chunk_id,
            similarity_score=similarity_score,
            content=document_title,
            # 하위 호환성을 위한 필드들
            chunk_index=int(chunk_id) if chunk_id and chunk_id.isdigit() else None,
            content_preview=content_preview
        )
    
    def get_display_content(self) -> str:
        """표시용 내용 반환 (content가 없으면 content_preview 사용)"""
        return self.content if self.content else (self.content_preview or "")
    
    def get_similarity_display(self) -> str:
        """유사도 점수 표시용 문자열 반환"""
        if self.similarity_score is None:
            return "N/A"
        return f"{self.similarity_score:.2f}"


class RagResponse(BaseModel):
    """RAG 시스템 표준 응답 모델"""
    success: bool
    message: str
    data: Optional[Any] = None
    sources: Optional[SourceInfo] = None
    timestamp: Optional[str] = None
    
    @classmethod
    def success_response(cls, message: str, data: Any = None, sources: SourceInfo = None) -> "RagResponse":
        """성공 응답 생성"""
        from datetime import datetime
        return cls(
            success=True,
            message=message,
            data=data,
            sources=sources,
            timestamp=datetime.now().isoformat()
        )
    
    @classmethod
    def error_response(cls, message: str) -> "RagResponse":
        """오류 응답 생성"""
        from datetime import datetime
        return cls(
            success=False,
            message=message,
            timestamp=datetime.now().isoformat()
        )


class RagRequest(BaseModel):
    """RAG 요청 모델"""
    query: str
    max_results: Optional[int] = 5
    threshold: Optional[float] = 0.7
