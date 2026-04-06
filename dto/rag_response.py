"""
RAG 응답 DTO
Java 프로젝트의 RagResponse와 유사한 기능 제공
Pydantic 데이터 검증 자동화
"""

from typing import Any, Optional, Dict, List
from pydantic import BaseModel, Field, field_validator, model_validator


class SourceInfo(BaseModel):
    """출처 정보 모델 - Java SourceInfo와 호환 (Pydantic 검증 강화)"""
    filename: str = Field(..., min_length=1, description="파일명 (필수)")
    chunk_id: Optional[str] = Field(None, description="청크 ID")
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="유사도 점수 (0.0-1.0)")
    content: Optional[str] = Field(None, max_length=1000, description="내용 요약")
    
    # 하위 호환성을 위한 필드들
    chunk_index: Optional[int] = Field(None, ge=0, description="청크 인덱스")
    content_preview: Optional[str] = Field(None, max_length=500, description="내용 미리보기")
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """파일명 유효성 검증"""
        if not v or not v.strip():
            raise ValueError("파일명은 비워둘 수 없습니다")
        
        # 파일 확장자 확인
        valid_extensions = ['.txt', '.md', '.pdf', '.docx']
        if not any(v.lower().endswith(ext) for ext in valid_extensions):
            # 경고만 주고 허용 (유연성)
            pass
        
        return v.strip()
    
    @field_validator('similarity_score')
    @classmethod
    def validate_similarity_score(cls, v: Optional[float]) -> Optional[float]:
        """유사도 점수 유효성 검증"""
        if v is not None:
            # 소수점 2자리로 반올림
            v = round(float(v), 2)
            # 범위 체크는 Field에서 자동으로 처리
        return v
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        """내용 유효성 검증"""
        if v is not None:
            # 너무 긴 내용은 자르기
            if len(v) > 1000:
                v = v[:997] + "..."
            v = v.strip()
        return v
    
    @model_validator(mode='after')
    def validate_consistency(self) -> 'SourceInfo':
        """필드 간 일관성 검증"""
        # similarity_score가 있고 content가 없으면 filename에서 추출
        if self.similarity_score is not None and not self.content:
            if self.filename:
                # 파일명에서 확장자 제거하고 내용으로 사용
                base_name = self.filename.rsplit('.', 1)[0]
                self.content = base_name
        
        # chunk_id와 chunk_index 일관성
        if self.chunk_id and self.chunk_index is None:
            try:
                self.chunk_index = int(self.chunk_id.split('_')[-1])
            except (ValueError, IndexError):
                pass
        
        return self
    
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


class FilterRequest(BaseModel):
    """필터링 요청 모델 (Pydantic 검증 강화)"""
    filename: Optional[str] = Field(None, description="파일명 필터")
    file_type: Optional[str] = Field(None, description="파일 타입 필터")
    chunk_type: Optional[str] = Field(None, description="청크 타입 필터")
    date_range: Optional[Dict[str, str]] = Field(None, description="기간 필터")
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="최소 유사도 점수")
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: Optional[str]) -> Optional[str]:
        """파일명 필터 유효성 검증"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("파일명 필터는 비워둘 수 없습니다")
        return v
    
    @field_validator('file_type')
    @classmethod
    def validate_file_type(cls, v: Optional[str]) -> Optional[str]:
        """파일 타입 필터 유효성 검증"""
        if v is not None:
            v = v.strip().lower()
            valid_types = ['txt', 'md', 'pdf', 'docx']
            if v not in valid_types:
                raise ValueError(f"파일 타입은 {valid_types} 중 하나여야 합니다")
        return v
    
    @field_validator('chunk_type')
    @classmethod
    def validate_chunk_type(cls, v: Optional[str]) -> Optional[str]:
        """청크 타입 필터 유효성 검증"""
        if v is not None:
            v = v.strip().lower()
            valid_types = ['semantic', 'fallback', 'hierarchical', 'markdown']
            if v not in valid_types:
                raise ValueError(f"청크 타입은 {valid_types} 중 하나여야 합니다")
        return v
    
    @field_validator('date_range')
    @classmethod
    def validate_date_range(cls, v: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """기간 필터 유효성 검증"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("기간 필터는 객체 형태여야 합니다")
            
            start = v.get('start')
            end = v.get('end')
            
            if start and end:
                # 날짜 형식 검증 (간단한 검사)
                import re
                date_pattern = r'^\d{4}-\d{2}-\d{2}$'
                
                if not re.match(date_pattern, start):
                    raise ValueError("시작 날짜는 YYYY-MM-DD 형식이어야 합니다")
                
                if not re.match(date_pattern, end):
                    raise ValueError("종료 날짜는 YYYY-MM-DD 형식이어야 합니다")
                
                if start > end:
                    raise ValueError("시작 날짜는 종료 날짜보다 이전이어야 합니다")
        
        return v
    
    @field_validator('min_score')
    @classmethod
    def validate_min_score(cls, v: Optional[float]) -> Optional[float]:
        """최소 점수 필터 유효성 검증"""
        if v is not None:
            v = round(float(v), 2)
        return v


class FilteredSearchRequest(BaseModel):
    """필터링 검색 요청 모델"""
    query: str = Field(..., min_length=1, max_length=1000, description="검색 쿼리")
    filters: Optional[FilterRequest] = Field(None, description="필터링 조건")
    max_results: Optional[int] = Field(5, ge=1, le=50, description="최대 결과 수")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """쿼리 유효성 검증"""
        if not v or not v.strip():
            raise ValueError("쿼리는 비워둘 수 없습니다")
        return v.strip()


class SearchStats(BaseModel):
    """검색 통계 모델"""
    total_results: int = Field(..., ge=0, description="전체 결과 수")
    filtered_results: int = Field(..., ge=0, description="필터링된 결과 수")
    search_time: float = Field(..., ge=0, description="검색 시간 (초)")
    avg_similarity: Optional[float] = Field(None, ge=0.0, le=1.0, description="평균 유사도")
    
    @field_validator('search_time')
    @classmethod
    def validate_search_time(cls, v: float) -> float:
        """검색 시간 유효성 검증"""
        return round(float(v), 3)


class RagRequest(BaseModel):
    """RAG 요청 모델 (Pydantic 검증 강화)"""
    query: str = Field(..., min_length=1, max_length=1000, description="검색 쿼리 (필수)")
    max_results: Optional[int] = Field(5, ge=1, le=50, description="최대 결과 수 (1-50)")
    threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="유사도 임계값 (0.0-1.0)")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """쿼리 유효성 검증"""
        if not v or not v.strip():
            raise ValueError("쿼리는 비워둘 수 없습니다")
        
        v = v.strip()
        
        # 너무 짧은 쿼리 검증
        if len(v) < 1:
            raise ValueError("쿼리는 최소 1자 이상이어야 합니다")
        
        # 너무 긴 쿼리 자르기
        if len(v) > 1000:
            v = v[:997] + "..."
        
        return v
    
    @field_validator('max_results')
    @classmethod
    def validate_max_results(cls, v: Optional[int]) -> Optional[int]:
        """최대 결과 수 유효성 검증"""
        if v is not None:
            # 설정 값과 비교하여 조정
            from config import settings
            max_allowed = getattr(settings, 'search_max_results', 20)
            if v > max_allowed:
                v = max_allowed
        return v
    
    @field_validator('threshold')
    @classmethod
    def validate_threshold(cls, v: Optional[float]) -> Optional[float]:
        """임계값 유효성 검증"""
        if v is not None:
            # 소수점 2자리로 반올림
            v = round(float(v), 2)
        return v


class RagResponse(BaseModel):
    """RAG 시스템 표준 응답 모델 (Pydantic 검증 강화)"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., min_length=1, max_length=500, description="응답 메시지")
    data: Optional[Any] = Field(None, description="응답 데이터")
    sources: Optional[SourceInfo] = Field(None, description="출처 정보")
    timestamp: Optional[str] = Field(None, description="타임스탬프")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """메시지 유효성 검증"""
        if not v or not v.strip():
            raise ValueError("메시지는 비워둘 수 없습니다")
        return v.strip()
    
    @model_validator(mode='after')
    def add_timestamp(self) -> 'RagResponse':
        """타임스탬프 자동 추가"""
        if not self.timestamp:
            from datetime import datetime
            self.timestamp = datetime.now().isoformat()
        return self
    
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
