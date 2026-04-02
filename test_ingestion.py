"""
데이터 로드 및 전처리 테스트 스크립트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from services import FileManager, ParseManager


async def test_document_ingestion():
    """문서 로드 및 파싱 테스트"""
    
    print("=== RAG 데이터 로드 및 전처리 테스트 ===\n")
    
    # 1. 파일 관리자 초기화
    file_manager = FileManager()
    parse_manager = ParseManager()
    
    # 2. 문서 폴더 생성
    documents_folder = file_manager.get_default_documents_path()
    print(f"문서 폴더: {documents_folder}")
    
    await file_manager.create_default_documents_folder()
    
    # 3. 폴더 상태 확인
    folder_status = file_manager.get_folder_status(str(documents_folder))
    print(f"폴더 상태: {folder_status}")
    
    # 4. 파일 읽기
    if folder_status["exists"] and folder_status["file_count"] > 0:
        print(f"\n=== 파일 읽기 시작 ===")
        file_contents = await file_manager.read_all_supported_files(documents_folder)
        
        print(f"총 {len(file_contents)}개 파일을 읽었습니다.\n")
        
        # 5. 각 파일 파싱 테스트
        print("=== 문서 파싱 테스트 ===")
        
        for i, file_content in enumerate(file_contents):
            print(f"\n[{i+1}] 파일: {file_content.filename}")
            print(f"크기: {file_content.file_size} bytes")
            
            # 문서 특징 분석
            parse_manager.analyze_document_features(file_content.content)
            
            # 파싱 실행
            parsed_chunks = parse_manager.parse_document(file_content.content, file_content.filename)
            
            print(f"파싱 결과: {len(parsed_chunks)}개 청크")
            
            # 첫 번째 청크 내용 미리보기
            if parsed_chunks:
                first_chunk = parsed_chunks[0]
                print(f"첫 번째 청크 미리보기:")
                print(f"- 텍스트: {first_chunk['text'][:100]}...")
                print(f"- 메타데이터: {first_chunk['metadata']}")
            
            print("-" * 50)
    else:
        print("처리할 파일이 없습니다.")
        print(f"테스트를 위해 {documents_folder} 폴더에 .txt, .md, .pdf, .docx 파일을 넣어주세요.")


def create_sample_documents():
    """샘플 문서 생성"""
    documents_folder = Path("./documents")
    documents_folder.mkdir(exist_ok=True)
    
    # 샘플 텍스트 파일
    sample_txt = """# RAG 시스템 개요

RAG(Retrieval-Augmented Generation)는 검색 증강 생성 기술입니다.

## 주요 특징

1. 문서 검색
2. 답변 생성
3. 출처 추적

## 활용 분야

- 고객 서비스
- 교육 시스템
- 연구 지원

RAG 시스템은 대규모 언어 모델의 성능을 향상시킵니다.
"""
    
    with open(documents_folder / "sample.txt", "w", encoding="utf-8") as f:
        f.write(sample_txt)
    
    # 샘플 마크다운 파일
    sample_md = """# 머신러닝 기초

## 개요

머신러닝은 데이터에서 패턴을 학습하는 알고리즘입니다.

### 지도학습

- 분류(Classification)
- 회귀(Regression)

### 비지도학습

- 클러스터링(Clustering)
- 차원 축소(Dimensionality Reduction)

## 주요 알고리즘

1. 선형 회귀
2. 결정 트리
3. 신경망
4. 서포트 벡터 머신

머신러닝은 다양한 분야에서 활용됩니다.
"""
    
    with open(documents_folder / "sample.md", "w", encoding="utf-8") as f:
        f.write(sample_md)
    
    print(f"샘플 문서를 {documents_folder} 폴더에 생성했습니다.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG 데이터 로드 테스트")
    parser.add_argument("--create-samples", action="store_true", 
                       help="샘플 문서 생성")
    
    args = parser.parse_args()
    
    if args.create_samples:
        create_sample_documents()
    
    # 메인 테스트 실행
    asyncio.run(test_document_ingestion())
