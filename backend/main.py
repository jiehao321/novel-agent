"""
Novel Agent 后端服务 - 完整版
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import json
import threading

app = FastAPI(title="Novel Agent API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 数据模型 ==========

class NovelRequest(BaseModel):
    """小说创作请求"""
    requirement: str
    genre: Optional[str] = "都市"
    use_mock: Optional[bool] = True


class ChapterRequest(BaseModel):
    """章节写作请求"""
    novel_id: int
    chapter_num: int


class ReviewRequest(BaseModel):
    """审核请求"""
    novel_id: int
    chapter_num: int
    content: str


# ========== 内存存储 ==========

class InMemoryStore:
    """内存存储（生产环境用数据库）"""
    
    def __init__(self):
        self.novels: Dict[int, Dict[str, Any]] = {}
        self.chapters: Dict[int, Dict[int, str]] = {}  # novel_id -> {chapter_num -> content}
        self.novel_id_counter = 1
    
    def create_novel(self, requirement: str, genre: str) -> int:
        novel_id = self.novel_id_counter
        self.novel_id_counter += 1
        
        self.novels[novel_id] = {
            "id": novel_id,
            "requirement": requirement,
            "genre": genre,
            "status": "idle",
            "outline": {},
            "characters": [],
            "world_settings": {},
            "foreshadowing": []
        }
        self.chapters[novel_id] = {}
        
        return novel_id
    
    def get_novel(self, novel_id: int) -> Optional[Dict[str, Any]]:
        return self.novels.get(novel_id)
    
    def update_novel(self, novel_id: int, data: Dict[str, Any]):
        if novel_id in self.novels:
            self.novels[novel_id].update(data)
    
    def save_chapter(self, novel_id: int, chapter_num: int, content: str):
        if novel_id in self.chapters:
            self.chapters[novel_id][chapter_num] = content


# 全局存储
store = InMemoryStore()

# 全局 Pipeline（延迟初始化）
pipeline = None


def get_pipeline(use_mock: bool = True):
    """获取或创建 Pipeline"""
    global pipeline
    if pipeline is None:
        from agents.pipeline import NovelAgentPipeline
        pipeline = NovelAgentPipeline(use_mock=use_mock)
    return pipeline


# ========== API 端点 ==========

@app.get("/")
async def root():
    return {"message": "Novel Agent API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/novel/create")
async def create_novel(request: NovelRequest):
    """创建新小说"""
    try:
        novel_id = store.create_novel(request.requirement, request.genre)
        return {
            "novel_id": novel_id,
            "status": "created",
            "message": "Novel created. Use /api/novel/{novel_id}/plan to start planning."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/novel/{novel_id}")
async def get_novel(novel_id: int):
    """获取小说信息"""
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # 添加章节信息
    novel["chapters"] = list(store.chapters.get(novel_id, {}).keys())
    
    return novel


@app.post("/api/novel/{novel_id}/plan")
async def plan_novel(novel_id: int, background_tasks: BackgroundTasks):
    """生成大纲规划"""
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    try:
        # 使用 mock 模式快速测试
        from agents.pipeline import NovelAgentPipeline
        
        p = NovelAgentPipeline(use_mock=True)
        
        # 创建并规划
        p.create_novel(novel["requirement"], novel["genre"])
        result = p.plan()
        
        # 保存结果
        store.update_novel(novel_id, {
            "status": "planned",
            "outline": result.get("outline", {}),
            "characters": result.get("characters", []),
            "world_settings": result.get("world_settings", {}),
            "foreshadowing": result.get("foreshadowing", []),
            "title": result.get("title", "")
        })
        
        return {
            "status": "success",
            "title": result.get("title"),
            "outline": result.get("outline"),
            "characters": result.get("characters", []),
            "chapters_count": len(result.get("outline", {}).get("chapters", []))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/novel/{novel_id}/chapter/{chapter_num}/write")
async def write_chapter(novel_id: int, chapter_num: int):
    """写章节"""
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    if novel["status"] != "planned":
        raise HTTPException(status_code=400, detail="Please plan first")
    
    try:
        from agents.base import AgentContext
        from agents.writer.agents import WritingPipeline
        
        writer = WritingPipeline(use_mock=True)
        
        # 准备章节信息
        chapters = novel["outline"].get("chapters", [])
        chapter_info = None
        for ch in chapters:
            if ch.get("num") == chapter_num:
                chapter_info = ch
                break
        
        if not chapter_info:
            raise HTTPException(status_code=404, detail="Chapter not found in outline")
        
        # 准备上下文
        context = AgentContext(
            outline=novel["outline"],
            characters=novel["characters"],
            world_settings=novel["world_settings"],
            foreshadowing=novel["foreshadowing"],
            current_chapter=chapter_num
        )
        
        # 写作
        result = writer.write_chapter(chapter_info, context)
        
        if not result.success:
            return {"error": result.error, "chapter_num": chapter_num}
        
        if not result.data:
            return {"error": "No content generated", "chapter_num": chapter_num}
        
        content = result.data.get("content", "")
        
        # 保存
        store.save_chapter(novel_id, chapter_num, content)
        
        return {
            "chapter_num": chapter_num,
            "word_count": result.data.get("word_count", 0),
            "content_preview": content[:200] + "...",
            "status": "draft"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/novel/{novel_id}/chapter/{chapter_num}/review")
async def review_chapter(novel_id: int, chapter_num: int):
    """审核章节"""
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    content = store.chapters.get(novel_id, {}).get(chapter_num)
    if not content:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    try:
        from agents.base import AgentContext
        from agents.reviewer.agents import ReviewPipeline
        
        reviewer = ReviewPipeline(use_mock=True)
        
        context = AgentContext(
            outline=novel["outline"],
            characters=novel["characters"],
            world_settings=novel["world_settings"],
            foreshadowing=novel["foreshadowing"]
        )
        
        result = reviewer.full_review(content, context)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/novel/{novel_id}/chapter/{chapter_num}")
async def get_chapter(novel_id: int, chapter_num: int):
    """获取章节内容"""
    content = store.chapters.get(novel_id, {}).get(chapter_num)
    if not content:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    return {
        "novel_id": novel_id,
        "chapter_num": chapter_num,
        "content": content,
        "word_count": len(content)
    }


@app.post("/api/novel/{novel_id}/write-all")
async def write_all_chapters(novel_id: int):
    """批量写所有章节"""
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    try:
        from agents.pipeline import NovelAgentPipeline
        
        p = NovelAgentPipeline(use_mock=True)
        
        # 设置当前小说
        p.current_novel = type('Novel', (), novel)()
        p.current_novel.id = novel_id
        p.current_novel.outline = novel["outline"]
        p.current_novel.characters = novel["characters"]
        p.current_novel.world_settings = novel["world_settings"]
        p.current_novel.foreshadowing = novel["foreshadowing"]
        p.current_novel.chapters = []
        
        results = p.write_all_chapters()
        
        # 保存章节
        for r in results:
            if "error" not in r:
                store.save_chapter(novel_id, r["chapter_num"], r["content"])
        
        return {
            "status": "completed",
            "chapters_written": len([r for r in results if "error" not in r]),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ========== WebSocket 端点 ==========
from fastapi import WebSocket, WebSocketDisconnect
from backend.websocket import manager, handle_websocket

@app.websocket("/ws/{novel_id}")
async def websocket_endpoint(websocket: WebSocket, novel_id: int):
    """WebSocket 实时通信"""
    await handle_websocket(websocket, novel_id)
