"""
맥락 기반 문서 재분할 서비스
Redis에 저장된 문서들을 맥락별로 재분하여 저장
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from repositories import RedisDocumentRepository
from parsers import HierarchicalParser
from config import settings


class ContextualRedocumentService:
    """맥락 기반 문서 재분할 서비스"""
    
    def __init__(self):
        self.redis_document_repository = RedisDocumentRepository()
        self.hierarchical_parser = HierarchicalParser()
    
    async def reprocess_all_documents(self) -> Dict[str, Any]:
        """
        Redis에 저장된 모든 문서를 맥락별로 재분할
        
        Returns:
            재분할 결과 통계
        """
        print("=== 맥락 기반 문서 재분할 시작 ===")
        
        # 1. 현재 저장된 모든 문서 가져오기
        all_documents = await self.redis_document_repository.get_all_documents()
        
        if not all_documents:
            print("저장된 문서가 없습니다.")
            return {
                "total_files": 0,
                "total_chunks_before": 0,
                "total_chunks_after": 0,
                "processed_files": 0,
                "message": "처리할 문서가 없습니다"
            }
        
        print(f"총 {len(all_documents)}개 청크 발견")
        
        # 2. 파일별로 그룹화
        file_groups = self._group_documents_by_file(all_documents)
        print(f"총 {len(file_groups)}개 파일 발견")
        
        # 3. 각 파일별로 재분할
        total_chunks_before = len(all_documents)
        total_chunks_after = 0
        processed_files = 0
        
        for filename, chunks in file_groups.items():
            print(f"\n파일 처리 중: {filename} ({len(chunks)}개 청크)")
            
            # 원본 내용 복원
            original_content = self._reconstruct_original_content(chunks)
            
            if not original_content:
                print(f"  내용 복원 실패: {filename}")
                continue
            
            # 맥락 기반 재분할
            reprocessed_chunks = await self._reprocess_file_content(filename, original_content)
            
            if reprocessed_chunks:
                # 기존 청크 삭제
                await self._delete_file_chunks(filename)
                
                # 새 청크 저장
                await self._save_reprocessed_chunks(filename, reprocessed_chunks)
                
                total_chunks_after += len(reprocessed_chunks)
                processed_files += 1
                
                print(f"  재분할 완료: {len(chunks)} → {len(reprocessed_chunks)}개 청크")
            else:
                print(f"  재분할 실패: {filename}")
        
        # 4. 결과 통계
        result = {
            "total_files": len(file_groups),
            "total_chunks_before": total_chunks_before,
            "total_chunks_after": total_chunks_after,
            "processed_files": processed_files,
            "chunk_ratio": total_chunks_after / total_chunks_before if total_chunks_before > 0 else 0,
            "message": f"{processed_files}개 파일 재분할 완료"
        }
        
        print(f"\n=== 재분할 결과 ===")
        print(f"처리 파일: {processed_files}/{len(file_groups)}")
        print(f"청크 변화: {total_chunks_before} → {total_chunks_after}")
        print(f"변화율: {result['chunk_ratio']:.2f}")
        
        return result
    
    def _group_documents_by_file(self, documents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """문서들을 파일별로 그룹화"""
        file_groups = {}
        
        for doc in documents:
            metadata = doc.get('metadata', {})
            filename = metadata.get('filename', 'unknown')
            
            if filename not in file_groups:
                file_groups[filename] = []
            
            file_groups[filename].append(doc)
        
        return file_groups
    
    def _reconstruct_original_content(self, chunks: List[Dict[str, Any]]) -> Optional[str]:
        """청크들을 원본 내용으로 복원"""
        if not chunks:
            return None
        
        # 청크 인덱스순으로 정렬
        sorted_chunks = sorted(chunks, key=lambda x: x.get('metadata', {}).get('chunk_index', 0))
        
        # 내용 연결
        content_parts = []
        for chunk in sorted_chunks:
            text = chunk.get('text', '')
            if text:
                content_parts.append(text)
        
        return '\n\n'.join(content_parts) if content_parts else None
    
    async def _reprocess_file_content(self, filename: str, content: str) -> Optional[List[Dict[str, Any]]]:
        """파일 내용을 맥락 기반으로 재분할"""
        try:
            # 기본 메타데이터 생성
            base_metadata = {
                'filename': filename,
                'source_type': 'file',
                'saved_at': datetime.now().isoformat(),
                'splitter_type': 'contextual_hierarchical'
            }
            
            # 파서로 분할
            parsed_chunks = self.hierarchical_parser.parse(content, base_metadata)
            
            if not parsed_chunks:
                print(f"  파싱 실패: {filename}")
                return None
            
            # 청크 인덱스 추가
            for i, chunk in enumerate(parsed_chunks):
                chunk['metadata']['chunk_index'] = i
                chunk['metadata']['start_char'] = 0  # TODO: 정확한 위치 계산
                chunk['metadata']['end_char'] = len(chunk.get('text', ''))
                chunk['metadata']['chunk_length'] = len(chunk.get('text', ''))
            
            return parsed_chunks
            
        except Exception as e:
            print(f"  재분할 오류: {filename} - {e}")
            return None
    
    async def _delete_file_chunks(self, filename: str) -> bool:
        """특정 파일의 모든 청크 삭제"""
        try:
            # 파일 관련 키 패턴
            key_pattern = f"{settings.redis_rag_key_prefix}:{filename}:*"
            
            # 키 삭제
            delete_result = await self.redis_document_repository.delete_keys_by_patterns([key_pattern])
            
            deleted_count = delete_result.get('rag_keys_deleted', 0)
            print(f"    기존 청크 삭제: {deleted_count}개")
            
            return deleted_count > 0
            
        except Exception as e:
            print(f"    청크 삭제 실패: {e}")
            return False
    
    async def _save_reprocessed_chunks(self, filename: str, chunks: List[Dict[str, Any]]) -> bool:
        """재분할된 청크들 저장"""
        try:
            save_result = await self.redis_document_repository.save_documents(chunks)
            
            saved_count = save_result.get('savedCount', 0)
            print(f"    새 청크 저장: {saved_count}개")
            
            return saved_count > 0
            
        except Exception as e:
            print(f"    청크 저장 실패: {e}")
            return False
    
    async def get_reprocessing_preview(self, filename: str) -> Dict[str, Any]:
        """
        특정 파일의 재분할 미리보기
        
        Args:
            filename: 미리보기할 파일명
            
        Returns:
            재분할 미리보기 정보
        """
        try:
            # 해당 파일의 모든 청크 가져오기
            all_documents = await self.redis_document_repository.get_all_documents()
            file_chunks = [doc for doc in all_documents 
                          if doc.get('metadata', {}).get('filename') == filename]
            
            if not file_chunks:
                return {
                    "filename": filename,
                    "found": False,
                    "message": "파일을 찾을 수 없습니다"
                }
            
            # 원본 내용 복원
            original_content = self._reconstruct_original_content(file_chunks)
            
            if not original_content:
                return {
                    "filename": filename,
                    "found": True,
                    "error": "내용 복원 실패"
                }
            
            # 맥락 기반 재분할 미리보기
            base_metadata = {
                'filename': filename,
                'source_type': 'file',
                'saved_at': datetime.now().isoformat(),
                'splitter_type': 'contextual_hierarchical'
            }
            
            reprocessed_chunks = self.hierarchical_parser.parse(original_content, base_metadata)
            
            if not reprocessed_chunks:
                return {
                    "filename": filename,
                    "found": True,
                    "error": "재분할 실패"
                }
            
            return {
                "filename": filename,
                "found": True,
                "current_chunks": len(file_chunks),
                "preview_chunks": len(reprocessed_chunks),
                "preview": [
                    {
                        "title": chunk.get('metadata', {}).get('title', '제목 없음'),
                        "content_preview": chunk.get('text', '')[:100] + '...' if len(chunk.get('text', '')) > 100 else chunk.get('text', ''),
                        "chunk_type": chunk.get('metadata', {}).get('chunk_type', 'unknown')
                    }
                    for chunk in reprocessed_chunks[:3]  # 처음 3개만 미리보기
                ]
            }
            
        except Exception as e:
            return {
                "filename": filename,
                "found": True,
                "error": str(e)
            }
