# RAG 시스템 메인 파일
# 기본적인 FastAPI 서버 구조

from fastapi import FastAPI

app = FastAPI(title="RAG System API", version="1.0.0")

@app.get("/")
async def root():
    """기본 엔드포인트"""
    return {"message": "RAG System API"}

@app.get("/health")
async def health_check():
    """상태 확인 엔드포인트"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)