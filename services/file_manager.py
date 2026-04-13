"""
File system management service
Provides functionality similar to Java project's FileManager
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
    """Data class containing file content information"""
    file_path: Path
    content: str
    metadata: Dict[str, Any]
    
    @property
    def filename(self) -> str:
        """Return filename"""
        return self.file_path.name
    
    @property
    def file_size(self) -> int:
        """Return file size"""
        return len(self.content.encode(DEFAULT_ENCODING))


class FileManager:
    """File system management specialized service"""
    
    def __init__(self):
        self.documents_path = settings.documents_path
        
    async def read_file_content(self, file_path: Path) -> str:
        """
        Read file content
        
        Args:
            file_path: File path
            
        Returns:
            File content
            
        Raises:
            FileNotFoundError: When file doesn't exist
            UnicodeDecodeError: When encoding error occurs
        """
        try:
            # Use different reading methods based on file extension
            if file_path.suffix.lower() == PDF_EXTENSION:
                return await self._read_pdf_content(file_path)
            elif file_path.suffix.lower() == DOCX_EXTENSION:
                return await self._read_docx_content(file_path)
            else:
                # Read text files asynchronously
                return await asyncio.to_thread(file_path.read_text, encoding=DEFAULT_ENCODING)
        except Exception as e:
            raise Exception(f"File read failed: {file_path} - {e}")
    
    async def _read_pdf_content(self, file_path: Path) -> str:
        """Read PDF file content"""
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
            raise Exception("pypdf library required for PDF processing")
        except Exception as e:
            raise Exception(f"PDF processing failed: {e}")
    
    async def _read_docx_content(self, file_path: Path) -> str:
        """Read DOCX file content"""
        try:
            import docx
            
            doc = await asyncio.to_thread(docx.Document, file_path)
            content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text)
                
            return "\n".join(content)
        except ImportError:
            raise Exception("python-docx library required for DOCX processing")
        except Exception as e:
            raise Exception(f"DOCX processing failed: {e}")
    
    def create_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Create file metadata
        
        Args:
            file_path: File path
            
        Returns:
            File metadata map
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
        Check if it's a supported text file
        
        Args:
            file_name: File name
            
        Returns:
            Support status
        """
        lower_name = file_name.lower()
        return any(lower_name.endswith(ext) for ext in [
            TXT_EXTENSION, MD_EXTENSION, PDF_EXTENSION, DOCX_EXTENSION
        ])
    
    def get_supported_files_in_folder(self, folder: Path) -> List[Path]:
        """
        Return list of supported files in folder
        
        Args:
            folder: Folder to search
            
        Returns:
            List of supported file Paths
        """
        if not folder.exists() or not folder.is_dir():
            return []
        
        supported_files = []
        try:
            for file_path in folder.iterdir():
                if file_path.is_file() and self.is_supported_text_file(file_path.name):
                    supported_files.append(file_path)
        except Exception as e:
            print(f"Failed to read file list: {folder} - {e}")
        
        print(f"Found {len(supported_files)} supported files: {folder}")
        return supported_files
    
    async def read_all_supported_files(self, folder: Path) -> List[FileContent]:
        """
        Read content and metadata of all supported files in folder
        
        Args:
            folder: Target folder
            
        Returns:
            List of file information (content, metadata)
        """
        file_contents = []
        supported_files = self.get_supported_files_in_folder(folder)
        
        # Read files in parallel
        tasks = []
        for file_path in supported_files:
            task = self._read_single_file(file_path)
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    file_path = supported_files[i]
                    print(f"File read failed: {file_path.name} - {result}")
                else:
                    file_contents.append(result)
        
        print(f"Total {len(file_contents)} files processed")
        return file_contents
    
    async def _read_single_file(self, file_path: Path) -> FileContent:
        """Read single file (asynchronous)"""
        try:
            content = await self.read_file_content(file_path)
            metadata = self.create_file_metadata(file_path)
            
            print(f"File read complete: {file_path.name} (length: {len(content)})")
            return FileContent(file_path, content, metadata)
            
        except Exception as e:
            print(f"File read failed: {file_path.name} - {e}")
            raise
    
    async def read_all_default_documents(self) -> List[FileContent]:
        """
        Read all supported files from default document folder
        
        Returns:
            List of file information
        """
        default_folder = Path.cwd() / settings.documents_folder
        return await self.read_all_supported_files(default_folder)
