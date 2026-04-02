"""
파일 시스템 관리 서비스
Java 프로젝트의 FileManager와 유사한 기능 제공
"""

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from config import settings
from constants import (
    TXT_EXTENSION, MD_EXTENSION, PDF_EXTENSION, DOCX_EXTENSION,
    METADATA_KEY_FILENAME, METADATA_KEY_FILEPATH, METADATA_KEY_SAVED_AT,
    DEFAULT_ENCODING
)


@dataclass
class FileContent:
    """파일 내용 정보를 담는 데이터 클래스"""
    file_path: Path
    content: str
    metadata: Dict[str, Any]
    
    @property
    def filename(self) -> str:
        """파일명 반환"""
        return self.file_path.name
    
    @property
    def file_size(self) -> int:
        """파일 크기 반환"""
        return len(self.content.encode(DEFAULT_ENCODING))


class FileManager:
    """파일 시스템 관리 전문 서비스"""
    
    def __init__(self):
        self.documents_path = settings.documents_path
        
    def get_folder_path(self, folder_path: str) -> Path:
        """
        폴더 경로를 Path 객체로 변환
        
        Args:
            folder_path: 폴더 경로 (절대 또는 상대)
            
        Returns:
            Path 객체
        """
        path = Path(folder_path)
        return path if path.is_absolute() else Path.cwd() / path
    
    def get_default_documents_path(self) -> Path:
        """
        기본 문서 폴더 경로 반환
        
        Returns:
            기본 문서 폴더 Path
        """
        return Path.cwd() / settings.documents_folder
    
    async def create_folder_if_not_exists(self, folder: Path) -> bool:
        """
        폴더가 존재하지 않으면 생성
        
        Args:
            folder: 생성할 폴더 경로
            
        Returns:
            생성 성공 여부
        """
        try:
            if not folder.exists():
                folder.mkdir(parents=True, exist_ok=True)
                print(f"폴더 생성 완료: {folder}")
            return True
        except Exception as e:
            print(f"폴더 생성 실패: {folder} - {e}")
            return False
    
    async def create_default_documents_folder(self) -> bool:
        """
        기본 문서 폴더 생성
        
        Returns:
            생성 성공 여부
        """
        default_folder = self.get_default_documents_path()
        return await self.create_folder_if_not_exists(default_folder)
    
    def folder_exists(self, folder: Path) -> bool:
        """
        폴더 존재 여부 확인
        
        Args:
            folder: 확인할 폴더 경로
            
        Returns:
            존재 여부
        """
        return folder.exists() and folder.is_dir()
    
    async def read_file_content(self, file_path: Path) -> str:
        """
        파일 내용 읽기
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 내용
            
        Raises:
            FileNotFoundError: 파일이 없을 경우
            UnicodeDecodeError: 인코딩 오류 발생 시
        """
        try:
            # 파일 확장자에 따라 다른 읽기 방식 사용
            if file_path.suffix.lower() == PDF_EXTENSION:
                return await self._read_pdf_content(file_path)
            elif file_path.suffix.lower() == DOCX_EXTENSION:
                return await self._read_docx_content(file_path)
            else:
                # 텍스트 파일은 비동기로 읽기
                return await asyncio.to_thread(file_path.read_text, encoding=DEFAULT_ENCODING)
        except Exception as e:
            raise Exception(f"파일 읽기 실패: {file_path} - {e}")
    
    async def _read_pdf_content(self, file_path: Path) -> str:
        """PDF 파일 내용 읽기"""
        try:
            import pypdf
            
            content = []
            file = await asyncio.to_thread(open, file_path, 'rb')
            try:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text.strip():
                        content.append(page_text)
            finally:
                await asyncio.to_thread(file.close)
            
            return "\n".join(content)
        except ImportError:
            raise Exception("PDF 처리를 위해 pypdf 라이브러리가 필요합니다")
        except Exception as e:
            raise Exception(f"PDF 처리 실패: {e}")
    
    async def _read_docx_content(self, file_path: Path) -> str:
        """DOCX 파일 내용 읽기"""
        try:
            import docx
            
            doc = await asyncio.to_thread(docx.Document, file_path)
            content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text)
                
                return "\n".join(content)
        except ImportError:
            raise Exception("DOCX 처리를 위해 python-docx 라이브러리가 필요합니다")
        except Exception as e:
            raise Exception(f"DOCX 처리 실패: {e}")
    
    def create_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        파일 메타데이터 생성
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 메타데이터 맵
        """
        return {
            METADATA_KEY_FILENAME: file_path.name,
            METADATA_KEY_FILEPATH: str(file_path),
            METADATA_KEY_SAVED_AT: datetime.now().isoformat(),
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "file_extension": file_path.suffix.lower()
        }
    
    def is_supported_text_file(self, file_name: str) -> bool:
        """
        지원하는 텍스트 파일인지 확인
        
        Args:
            file_name: 파일명
            
        Returns:
            지원 여부
        """
        lower_name = file_name.lower()
        return any(lower_name.endswith(ext) for ext in [
            TXT_EXTENSION, MD_EXTENSION, PDF_EXTENSION, DOCX_EXTENSION
        ])
    
    def get_supported_files_in_folder(self, folder: Path) -> List[Path]:
        """
        폴더 내의 지원 파일 목록 반환
        
        Args:
            folder: 검색할 폴더
            
        Returns:
            지원 파일 Path 목록
        """
        if not self.folder_exists(folder):
            return []
        
        supported_files = []
        try:
            for file_path in folder.iterdir():
                if file_path.is_file() and self.is_supported_text_file(file_path.name):
                    supported_files.append(file_path)
        except Exception as e:
            print(f"파일 목록 읽기 실패: {folder} - {e}")
        
        print(f"지원 파일 {len(supported_files)}개 발견: {folder}")
        return supported_files
    
    async def read_all_supported_files(self, folder: Path) -> List[FileContent]:
        """
        폴더 내의 모든 지원 파일 내용과 메타데이터 읽기
        
        Args:
            folder: 대상 폴더
            
        Returns:
            파일 정보 리스트 (내용, 메타데이터)
        """
        file_contents = []
        supported_files = self.get_supported_files_in_folder(folder)
        
        # 병렬로 파일 읽기
        tasks = []
        for file_path in supported_files:
            task = self._read_single_file(file_path)
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    file_path = supported_files[i]
                    print(f"파일 읽기 실패: {file_path.name} - {result}")
                else:
                    file_contents.append(result)
        
        print(f"총 {len(file_contents)}개 파일 처리 완료")
        return file_contents
    
    async def _read_single_file(self, file_path: Path) -> FileContent:
        """단일 파일 읽기 (비동기)"""
        try:
            content = await self.read_file_content(file_path)
            metadata = self.create_file_metadata(file_path)
            
            print(f"파일 읽기 완료: {file_path.name} (길이: {len(content)})")
            return FileContent(file_path, content, metadata)
            
        except Exception as e:
            print(f"파일 읽기 실패: {file_path.name} - {e}")
            raise
    
    async def read_all_default_documents(self) -> List[FileContent]:
        """
        기본 문서 폴더의 모든 지원 파일 읽기
        
        Returns:
            파일 정보 리스트
        """
        default_folder = self.get_default_documents_path()
        return await self.read_all_supported_files(default_folder)
    
    async def ensure_folder_exists(self, folder_path: str) -> bool:
        """
        폴더 존재 확인 및 필요시 생성
        
        Args:
            folder_path: 폴더 경로
            
        Returns:
            폴더 존재 여부
        """
        folder = self.get_folder_path(folder_path)
        
        if not self.folder_exists(folder):
            if folder_path == settings.documents_folder:
                return await self.create_default_documents_folder()
            else:
                return await self.create_folder_if_not_exists(folder)
        
        return True
    
    def get_folder_status(self, folder_path: str) -> Dict[str, Any]:
        """
        폴더 상태 확인 결과 생성
        
        Args:
            folder_path: 폴더 경로
            
        Returns:
            폴더 상태 정보
        """
        folder = self.get_folder_path(folder_path)
        return self._get_folder_status(folder)
    
    def _get_folder_status(self, folder: Path) -> Dict[str, Any]:
        """
        파일 시스템 상태 정보 반환
        
        Args:
            folder: 확인할 폴더
            
        Returns:
            폴더 상태 정보
        """
        try:
            exists = self.folder_exists(folder)
            files = self.get_supported_files_in_folder(folder) if exists else []
            
            return {
                "exists": exists,
                "path": str(folder),
                "file_count": len(files),
                "files": [f.name for f in files]
            }
        except Exception as e:
            print(f"폴더 상태 확인 실패: {folder} - {e}")
            return {
                "exists": False,
                "path": str(folder),
                "error": str(e)
            }
