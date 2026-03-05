"""
Novel Agent 后端服务 - 完整版
增加异常处理、重试机制和人工复审功能
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import json
import threading
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


class ManualReviewCompleteRequest(BaseModel):
    """人工复审完成请求"""
    review_id: int
    action: str  # "approve" | "reject" | "request_changes"
    reviewer_note: Optional[str] = ""


class RetryWriteRequest(BaseModel):
    """重试写作请求"""
    chapter_num: int
    max_retries: Optional[int] = 3


class RollbackRequest(BaseModel):
    """回滚请求"""
    chapter_num: int
    target_version: Optional[int] = None  # None 表示回滚到上一版本


# ========== 内存存储 ==========

class InMemoryStore:
    """内存存储（生产环境用数据库）"""
    
    def __init__(self):
        self.novels: Dict[int, Dict[str, Any]] = {}
        self.chapters: Dict[int, Dict[int, str]] = {}  # novel_id -> {chapter_num -> content}
        self.novel_id_counter = 1
        # 章节状态追踪（用于重试/回滚）
        self.chapter_status: Dict[int, Dict[int, Dict[str, Any]]] = {}
    
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
        self.chapter_status[novel_id] = {}
        
        return novel_id
    
    def get_novel(self, novel_id: int) -> Optional[Dict[str, Any]]:
        return self.novels.get(novel_id)
    
    def update_novel(self, novel_id: int, data: Dict[str, Any]):
        if novel_id in self.novels:
            self.novels[novel_id].update(data)
    
    def save_chapter(self, novel_id: int, chapter_num: int, content: str, status: str = "draft"):
        if novel_id in self.chapters:
            self.chapters[novel_id][chapter_num] = content
        
        # 记录状态
        if novel_id not in self.chapter_status:
            self.chapter_status[novel_id] = {}
        self.chapter_status[novel_id][chapter_num] = {
            "status": status,
            "last_error": None,
            "retry_count": 0
        }
    
    def get_chapter_status(self, novel_id: int, chapter_num: int) -> Optional[Dict[str, Any]]:
        if novel_id in self.chapter_status:
            return self.chapter_status[novel_id].get(chapter_num)
        return None
    
    def update_chapter_status(self, novel_id: int, chapter_num: int, status: str, error: str = None):
        if novel_id not in self.chapter_status:
            self.chapter_status[novel_id] = {}
        
        current = self.chapter_status[novel_id].get(chapter_num, {"retry_count": 0})
        self.chapter_status[novel_id][chapter_num] = {
            "status": status,
            "last_error": error,
            "retry_count": current.get("retry_count", 0) + (1 if error else 0)
        }


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


# ========== 引入重试和版本管理 ==========
from agents.retry import (
    AgentExecutor, RetryConfig, RetryStrategy,
    get_version_manager, get_manual_review_manager
)

# 初始化版本管理器
DB_PATH = "novel_agent.db"
version_manager = get_version_manager(DB_PATH)
review_manager = get_manual_review_manager(DB_PATH)


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
    chapters = list(store.chapters.get(novel_id, {}).keys())
    novel["chapters"] = chapters
    
    # 添加每个章节的状态
    chapter_details = []
    for ch_num in chapters:
        status_info = store.get_chapter_status(novel_id, ch_num)
        chapter_details.append({
            "chapter_num": ch_num,
            "status": status_info.get("status", "draft") if status_info else "draft",
            "error": status_info.get("last_error") if status_info else None,
            "retry_count": status_info.get("retry_count", 0) if status_info else 0
        })
    novel["chapter_details"] = chapter_details
    
    return novel


@app.post("/api/novel/{novel_id}/plan")
async def plan_novel(novel_id: int, background_tasks: BackgroundTasks):
    """生成大纲规划（带进度推送）"""
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # 导入进度推送函数
    from backend.websocket import (
        manager, AgentStage,
        create_stage_start_message, create_stage_progress_message,
        create_stage_complete_message, create_overall_progress_message
    )
    
    # 检查 WebSocket 连接状态
    from backend.websocket import manager
    
    def is_ws_connected():
        return manager.is_connected(novel_id)
    
    try:
        # 使用 mock 模式快速测试
        from agents.pipeline import NovelAgentPipeline
        
        p = NovelAgentPipeline(use_mock=True)
        
        # 推送开始
        if is_ws_connected():
            await manager.send_message(create_stage_start_message(AgentStage.PLANNING, 1, "开始需求分析"), novel_id)
            await manager.send_message(create_stage_progress_message(AgentStage.PLANNING, 30, "创建小说对象"), novel_id)
        
        # 创建并规划
        p.create_novel(novel["requirement"], novel["genre"])
        
        if is_ws_connected():
            await manager.send_message(create_stage_progress_message(AgentStage.PLANNING, 50, "开始规划"), novel_id)
            await manager.send_message(create_stage_complete_message(AgentStage.PLANNING, {}, "需求分析完成"), novel_id)
            await manager.send_message(create_stage_start_message(AgentStage.GENERATING_OUTLINE, 1, "生成大纲中"), novel_id)
            await manager.send_message(create_stage_progress_message(AgentStage.GENERATING_OUTLINE, 50, "AI 创作中..."), novel_id)
        
        result = p.plan()
        
        if "error" in result:
            if is_ws_connected():
                await manager.send_message(create_stage_complete_message(AgentStage.GENERATING_OUTLINE, result, "规划失败"), novel_id)
            return result
        
        if is_ws_connected():
            await manager.send_message(create_stage_progress_message(AgentStage.GENERATING_OUTLINE, 100, "大纲生成完成"), novel_id)
            await manager.send_message(create_stage_complete_message(AgentStage.GENERATING_OUTLINE, result, "大纲生成完成"), novel_id)
            await manager.send_message(create_stage_start_message(AgentStage.GENERATING_CHARACTERS, len(result.get("characters", [])), "生成角色中"), novel_id)
        
        for i, char in enumerate(result.get("characters", [])):
            progress = int((i + 1) / max(len(result.get("characters", [])), 1) * 100)
            if is_ws_connected():
                await manager.send_message(create_stage_progress_message(AgentStage.GENERATING_CHARACTERS, progress, f"生成角色: {char.get('name', '未知')}"), novel_id)
        
        if is_ws_connected():
            await manager.send_message(create_stage_complete_message(AgentStage.GENERATING_CHARACTERS, {"characters": result.get("characters", [])}, "角色生成完成"), novel_id)
            await manager.send_message(create_stage_start_message(AgentStage.GENERATING_WORLD, 1, "设定世界观"), novel_id)
            await manager.send_message(create_stage_progress_message(AgentStage.GENERATING_WORLD, 50, "世界观设定中"), novel_id)
            await manager.send_message(create_stage_complete_message(AgentStage.GENERATING_WORLD, result, "世界观设定完成"), novel_id)
            await manager.send_message(create_stage_start_message(AgentStage.GENERATING_FORESHADOWING, 1, "设计伏笔"), novel_id)
            await manager.send_message(create_stage_progress_message(AgentStage.GENERATING_FORESHADOWING, 50, "伏笔设计中"), novel_id)
            await manager.send_message(create_stage_complete_message(AgentStage.GENERATING_FORESHADOWING, result, "伏笔设计完成"), novel_id)
            await manager.send_message(create_stage_start_message(AgentStage.COMPLETED, 1, "规划完成"), novel_id)
            await manager.send_message(create_overall_progress_message(AgentStage.COMPLETED, 100, 100, {"status": "planned"}), novel_id)
        
        # 保存结果 - 将volumes和overall_rhythm包含在outline中
        outline_data = result.get("outline", {})
        outline_data["volumes"] = result.get("volumes", [])
        outline_data["overall_rhythm"] = result.get("overall_rhythm", {})
        
        store.update_novel(novel_id, {
            "status": "planned",
            "outline": outline_data,
            "characters": result.get("characters", []),
            "world_settings": result.get("world_settings", {}),
            "foreshadowing": result.get("foreshadowing", []),
            "title": result.get("title", "")
        })
        
        return {
            "status": "success",
            "title": result.get("title"),
            "outline": result.get("outline"),
            "volumes": result.get("volumes", []),
            "overall_rhythm": result.get("overall_rhythm", {}),
            "characters": result.get("characters", []),
            "chapters_count": len(result.get("outline", {}).get("chapters", []))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 卷管理 API ==========

@app.get("/api/novel/{novel_id}/volumes")
async def get_volumes(novel_id: int):
    """获取小说的所有卷"""
    try:
        from agents.memory.store import MemoryStore
        db_store = MemoryStore(DB_PATH)
        volumes = db_store.get_volumes(novel_id)
        
        # 也尝试从大纲中获取卷信息
        novel = store.get_novel(novel_id)
        outline_volumes = []
        if novel and novel.get("outline"):
            outline_volumes = novel["outline"].get("volumes", [])
        
        # 合并数据
        if volumes:
            return {
                "success": True,
                "volumes": volumes,
                "count": len(volumes)
            }
        elif outline_volumes:
            return {
                "success": True,
                "volumes": outline_volumes,
                "count": len(outline_volumes)
            }
        else:
            return {
                "success": True,
                "volumes": [],
                "count": 0,
                "message": "暂无卷信息"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/novel/{novel_id}/volumes/{volume_num}")
async def get_volume(novel_id: int, volume_num: int):
    """获取指定卷的详细信息"""
    try:
        from agents.memory.store import MemoryStore
        db_store = MemoryStore(DB_PATH)
        volumes = db_store.get_volumes(novel_id)
        
        volume = None
        for v in volumes:
            if v.get("volume_num") == volume_num:
                volume = v
                break
        
        if not volume:
            raise HTTPException(status_code=404, detail="Volume not found")
        
        return {
            "success": True,
            "volume": volume
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/novel/{novel_id}/rhythm")
async def get_overall_rhythm(novel_id: int):
    """获取整体节奏曲线"""
    try:
        # 从大纲中获取整体节奏
        novel = store.get_novel(novel_id)
        if not novel:
            raise HTTPException(status_code=404, detail="Novel not found")
        
        # 优先从大纲获取，其次从数据库
        overall_rhythm = novel.get("outline", {}).get("overall_rhythm", {})
        
        if not overall_rhythm:
            # 从卷信息计算整体节奏
            from agents.memory.store import MemoryStore
            db_store = MemoryStore(DB_PATH)
            volumes = db_store.get_volumes(novel_id)
            
            if volumes:
                total_chapters = novel.get("outline", {}).get("total_chapters", 100)
                overall_rhythm = _calculate_overall_rhythm(volumes, total_chapters)
        
        return {
            "success": True,
            "rhythm": overall_rhythm
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _calculate_overall_rhythm(volumes: List[Dict], total_chapters: int) -> Dict:
    """计算整体节奏曲线"""
    if not volumes:
        return {"points": [], "major_climaxes": []}
    
    major_climaxes = []
    num_volumes = len(volumes)
    
    # 每3-5卷设置一个整体高潮
    climax_interval = max(3, min(5, num_volumes // 3))
    for i in range(climax_interval - 1, num_volumes, climax_interval):
        if i < len(volumes):
            volume = volumes[i]
            overall_chapter = (volume.get("start_chapter", 0) + volume.get("end_chapter", 0)) // 2
            major_climaxes.append({
                "volume_num": volume.get("volume_num"),
                "chapter": overall_chapter,
                "title": volume.get("title"),
                "intensity": 10
            })
    
    # 构建整体节奏点
    points = []
    for i, volume in enumerate(volumes):
        rhythm_curve = volume.get("rhythm_curve", {})
        curve_points = rhythm_curve.get("points", [])
        
        for point in curve_points:
            volume_start = volume.get("start_chapter", 1)
            volume_end = volume.get("end_chapter", total_chapters)
            volume_size = volume_end - volume_start + 1
            
            overall_position = volume_start + (point.get("position", 0) / 100) * volume_size
            overall_position_percent = (overall_position / total_chapters) * 100
            
            points.append({
                "chapter": int(overall_position),
                "position": round(overall_position_percent, 1),
                "intensity": point.get("intensity", 5),
                "phase": point.get("phase", ""),
                "volume_num": volume.get("volume_num")
            })
    
    return {
        "points": points,
        "major_climaxes": major_climaxes,
        "total_volumes": num_volumes,
        "total_chapters": total_chapters
    }


@app.post("/api/novel/{novel_id}/volumes/{volume_num}")
async def update_volume(novel_id: int, volume_num: int, request: Dict):
    """更新卷信息"""
    try:
        from agents.memory.store import MemoryStore
        db_store = MemoryStore(DB_PATH)
        volumes = db_store.get_volumes(novel_id)
        
        volume_id = None
        for v in volumes:
            if v.get("volume_num") == volume_num:
                volume_id = v.get("id")
                break
        
        if not volume_id:
            raise HTTPException(status_code=404, detail="Volume not found")
        
        # 更新卷信息
        updates = {
            "title": request.get("title"),
            "introduction": request.get("introduction"),
            "theme": request.get("theme"),
            "core_conflict": request.get("core_conflict"),
            "plot_summary": request.get("plot_summary"),
            "key_events": request.get("key_events", []),
            "rhythm_curve": request.get("rhythm_curve", {}),
            "character_appearances": request.get("character_appearances", [])
        }
        
        db_store.update_volume(volume_id, updates)
        
        return {
            "success": True,
            "message": "卷信息已更新"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def execute_write_with_retry(novel_id: int, chapter_num: int, chapter_info: Dict, novel: Dict) -> Dict:
    """
    执行章节写作（带重试机制）
    """
    from agents.base import AgentContext
    from agents.writer.agents import WritingPipeline
    
    # 配置重试
    retry_config = RetryConfig(
        max_retries=3,
        initial_delay=1.0,
        strategy=RetryStrategy.EXPONENTIAL
    )
    executor = AgentExecutor(retry_config)
    
    def write_func():
        writer = WritingPipeline(use_mock=True)
        
        # 准备上下文
        context = AgentContext(
            outline=novel["outline"],
            characters=novel["characters"],
            world_settings=novel["world_settings"],
            foreshadowing=novel["foreshadowing"],
            current_chapter=chapter_num
        )
        
        result = writer.write_chapter(chapter_info, context)
        
        if not result.success:
            raise Exception(result.error or "写作失败")
        
        return result
    
    # 执行并重试
    exec_result = executor.execute(write_func)
    
    if not exec_result.success:
        # 保存错误状态
        store.update_chapter_status(novel_id, chapter_num, "failed", exec_result.error)
        return {
            "success": False,
            "error": exec_result.error,
            "chapter_num": chapter_num,
            "retries": exec_result.metadata.get("retries", 0)
        }
    
    # 写作成功，保存内容
    content = exec_result.data.data.get("content", "")
    
    # 保存到数据库版本管理
    version_num = version_manager.save_version(
        novel_id, chapter_num, content, status="draft"
    )
    
    # 保存到内存
    store.save_chapter(novel_id, chapter_num, content, status="draft")
    
    return {
        "success": True,
        "chapter_num": chapter_num,
        "version_num": version_num,
        "word_count": exec_result.data.data.get("word_count", 0),
        "content_preview": content[:200] + "...",
        "status": "draft",
        "retries": exec_result.metadata.get("retries", 0)
    }


@app.post("/api/novel/{novel_id}/chapter/{chapter_num}/write")
async def write_chapter(novel_id: int, chapter_num: int):
    """写章节（带异常捕获和自动重试）"""
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    if novel["status"] != "planned":
        raise HTTPException(status_code=400, detail="Please plan first")
    
    try:
        # 获取章节信息
        chapters = novel["outline"].get("chapters", [])
        chapter_info = None
        for ch in chapters:
            if ch.get("num") == chapter_num:
                chapter_info = ch
                break
        
        if not chapter_info:
            raise HTTPException(status_code=404, detail="Chapter not found in outline")
        
        # 执行写作（带重试）
        result = execute_write_with_retry(novel_id, chapter_num, chapter_info, novel)
        
        if not result.get("success"):
            return {
                "error": result.get("error"),
                "chapter_num": chapter_num,
                "status": "failed",
                "retries": result.get("retries", 0)
            }
        
        return result
        
    except Exception as e:
        logger.error(f"写章节异常: {e}")
        store.update_chapter_status(novel_id, chapter_num, "failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/novel/{novel_id}/chapter/{chapter_num}/retry")
async def retry_write_chapter(novel_id: int, chapter_num: int):
    """重试写章节"""
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # 获取章节信息
    chapters = novel["outline"].get("chapters", [])
    chapter_info = None
    for ch in chapters:
        if ch.get("num") == chapter_num:
            chapter_info = ch
            break
    
    if not chapter_info:
        raise HTTPException(status_code=404, detail="Chapter not found in outline")
    
    try:
        result = execute_write_with_retry(novel_id, chapter_num, chapter_info, novel)
        
        if not result.get("success"):
            return {
                "error": result.get("error"),
                "chapter_num": chapter_num,
                "status": "failed"
            }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/novel/{novel_id}/chapter/{chapter_num}/rollback")
async def rollback_chapter(novel_id: int, chapter_num: int, request: RollbackRequest):
    """回滚章节到上一版本"""
    try:
        # 执行回滚
        old_version = version_manager.get_latest_version_num(novel_id, chapter_num)
        
        if old_version <= 1:
            raise HTTPException(status_code=400, detail="没有可回滚的版本")
        
        # 回滚到上一版本
        rolled_back = version_manager.rollback(
            novel_id, 
            chapter_num, 
            request.target_version
        )
        
        if not rolled_back:
            raise HTTPException(status_code=400, detail="回滚失败")
        
        # 更新内存存储
        store.save_chapter(
            novel_id, 
            chapter_num, 
            rolled_back["content"], 
            status="rolled_back"
        )
        
        return {
            "success": True,
            "chapter_num": chapter_num,
            "version_num": rolled_back["version_num"],
            "content_preview": rolled_back["content"][:200] + "...",
            "message": f"已回滚到版本 {rolled_back['version_num']}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/novel/{novel_id}/chapter/{chapter_num}/versions")
async def get_chapter_versions(novel_id: int, chapter_num: int):
    """获取章节版本历史"""
    try:
        history = version_manager.get_version_history(novel_id, chapter_num)
        return {
            "chapter_num": chapter_num,
            "versions": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/novel/{novel_id}/chapter/{chapter_num}/version/{version_num}")
async def get_chapter_version(novel_id: int, chapter_num: int, version_num: int):
    """获取指定版本章节内容"""
    try:
        version = version_manager.get_version(novel_id, chapter_num, version_num)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")
        return version
    except HTTPException:
        raise
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


# ========== 人工复审 API ==========

@app.post("/api/novel/{novel_id}/chapter/{chapter_num}/request-review")
async def request_manual_review(novel_id: int, chapter_num: int):
    """请求人工复审"""
    try:
        # 获取最新版本
        version = version_manager.get_version(novel_id, chapter_num)
        if not version:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 创建复审请求
        review_id = review_manager.create_review_request(
            novel_id, chapter_num, version["version_num"]
        )
        
        # 更新章节状态
        store.update_chapter_status(novel_id, chapter_num, "pending_review")
        
        return {
            "success": True,
            "review_id": review_id,
            "message": "已提交人工复审请求"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reviews/pending")
async def get_pending_reviews():
    """获取待处理的复审请求"""
    try:
        reviews = review_manager.get_pending_reviews()
        return {
            "reviews": reviews,
            "count": len(reviews)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/novel/{novel_id}/reviews")
async def get_novel_reviews(novel_id: int):
    """获取小说的复审历史"""
    try:
        reviews = review_manager.get_review_history(novel_id)
        return {
            "novel_id": novel_id,
            "reviews": reviews
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reviews/{review_id}/complete")
async def complete_manual_review(review_id: int, request: ManualReviewCompleteRequest):
    """完成人工复审"""
    try:
        # 执行复审操作
        success = review_manager.complete_review(
            review_id,
            request.action,
            request.reviewer_note
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="复审请求不存在")
        
        # 获取复审详情
        reviews = review_manager.get_review_history()
        review = next((r for r in reviews if r["id"] == review_id), None)
        
        if review:
            # 根据复审结果处理章节
            if request.action == "approve":
                store.update_chapter_status(
                    review["novel_id"], 
                    review["chapter_num"], 
                    "approved"
                )
            elif request.action == "reject":
                store.update_chapter_status(
                    review["novel_id"], 
                    review["chapter_num"], 
                    "rejected"
                )
            elif request.action == "request_changes":
                store.update_chapter_status(
                    review["novel_id"], 
                    review["chapter_num"], 
                    "needs_revision"
                )
        
        return {
            "success": True,
            "message": f"复审完成: {request.action}",
            "review_id": review_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/novel/{novel_id}/chapter/{chapter_num}")
async def get_chapter(novel_id: int, chapter_num: int):
    """获取章节内容"""
    content = store.chapters.get(novel_id, {}).get(chapter_num)
    if not content:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # 获取版本信息
    version = version_manager.get_version(novel_id, chapter_num)
    
    return {
        "novel_id": novel_id,
        "chapter_num": chapter_num,
        "content": content,
        "word_count": len(content),
        "version": version
    }


@app.post("/api/novel/{novel_id}/write-all")
async def write_all_chapters(novel_id: int):
    """批量写所有章节（带进度推送）"""
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # 导入进度推送函数
    from backend.websocket import (
        manager, AgentStage,
        create_stage_start_message, create_stage_progress_message,
        create_stage_complete_message, create_overall_progress_message,
        create_chapter_progress_message, create_chapter_complete_message,
        create_completed_message
    )
    
    # 检查连接
    def is_ws_connected():
        return manager.is_connected(novel_id)
    
    try:
        # 推送开始
        if is_ws_connected():
            await manager.send_message(create_stage_start_message(AgentStage.WRITING_CHAPTERS, 1, "开始批量写作"), novel_id)
        
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
        
        chapters = novel["outline"].get("chapters", [])
        total_chapters = len(chapters)
        
        results = []
        
        for idx, ch in enumerate(chapters):
            chapter_num = ch.get("num")
            
            # 推送章节进度
            chapter_progress = int((idx + 1) / total_chapters * 100)
            if is_ws_connected():
                await manager.send_message(create_chapter_progress_message(chapter_num, total_chapters, chapter_progress), novel_id)
                await manager.send_message(create_stage_progress_message(AgentStage.WRITING_CHAPTERS, chapter_progress, f"写作第{chapter_num}章"), novel_id)
            
            # 写入章节
            result = p.write_chapter(chapter_num)
            results.append(result)
            
            # 推送章节完成
            if is_ws_connected():
                if "error" not in result:
                    content = result.get("content", "")
                    word_count = result.get("word_count", 0)
                    review = result.get("review", {})
                    await manager.send_message(create_chapter_complete_message(chapter_num, content, word_count, review), novel_id)
                else:
                    await manager.send_message({
                        "type": "error",
                        "chapter_num": chapter_num,
                        "error": result.get("error")
                    }, novel_id)
        
        # 保存章节（包括版本管理）
        for r in results:
            if "error" not in r:
                content = r.get("content", "")
                store.save_chapter(novel_id, r["chapter_num"], content)
                # 保存到版本管理
                version_manager.save_version(
                    novel_id, r["chapter_num"], content, status=r.get("status", "draft")
                )
        
        # 推送完成
        if is_ws_connected():
            total_words = sum(r.get("word_count", 0) for r in results if "error" not in r)
            await manager.send_message(create_stage_complete_message(AgentStage.WRITING_CHAPTERS, {"chapters": len(results)}, "所有章节写作完成"), novel_id)
            await manager.send_message(create_stage_start_message(AgentStage.COMPLETED, 1, "全部完成"), novel_id)
            await manager.send_message(create_completed_message(novel_id, total_chapters, total_words), novel_id)
        
        return {
            "status": "completed",
            "chapters_written": len([r for r in results if "error" not in r]),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 向量搜索 API ==========

class VectorSearchRequest(BaseModel):
    """向量搜索请求"""
    query: str
    novel_id: Optional[int] = None
    top_k: Optional[int] = 5
    include_content: Optional[bool] = True


class IndexChaptersRequest(BaseModel):
    """索引章节请求"""
    novel_id: int
    chapter_nums: Optional[List[int]] = None  # None 表示索引所有章节


# 初始化向量存储
def get_vector_store_instance():
    """获取向量存储实例"""
    from backend.vector_store import get_vector_store, ChapterVector
    return get_vector_store()


@app.post("/api/vector/index")
async def index_chapters(request: IndexChaptersRequest):
    """索引小说章节到向量库"""
    try:
        from backend.vector_store import get_vector_store, ChapterVector
        
        vector_store = get_vector_store()
        
        # 获取章节内容
        novel = store.get_novel(request.novel_id)
        if not novel:
            raise HTTPException(status_code=404, detail="Novel not found")
        
        chapters_data = store.chapters.get(request.novel_id, {})
        if not chapters_data:
            raise HTTPException(status_code=404, detail="No chapters found")
        
        # 确定要索引的章节
        if request.chapter_nums:
            chapters_to_index = {k: v for k, v in chapters_data.items() if k in request.chapter_nums}
        else:
            chapters_to_index = chapters_data
        
        # 创建章节向量
        chapter_vectors = []
        for chapter_num, content in chapters_to_index.items():
            # 从大纲中获取章节摘要
            summary = ""
            outline_chapters = novel.get("outline", {}).get("chapters", [])
            for oc in outline_chapters:
                if oc.get("num") == chapter_num:
                    summary = oc.get("title", "") + ": " + oc.get("summary", "")
                    break
            
            chapter_vec = ChapterVector(
                novel_id=request.novel_id,
                chapter_num=chapter_num,
                content=content,
                summary=summary
            )
            chapter_vectors.append(chapter_vec)
        
        # 批量添加到向量库
        result = vector_store.add_chapters(chapter_vectors)
        
        return {
            "success": True,
            "novel_id": request.novel_id,
            "indexed_count": result["success"],
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"索引章节失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vector/search")
async def search_similar_chapters(request: VectorSearchRequest):
    """向量语义搜索相似章节"""
    try:
        from backend.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        
        results = vector_store.search_similar_chapters(
            query=request.query,
            novel_id=request.novel_id,
            top_k=request.top_k or 5,
            include_content=request.include_content if request.include_content is not None else True
        )
        
        return {
            "success": True,
            "query": request.query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"向量搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vector/stats")
async def get_vector_stats():
    """获取向量库统计信息"""
    try:
        from backend.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        stats = vector_store.get_collection_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"获取向量统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/vector/novel/{novel_id}")
async def delete_novel_vectors(novel_id: int):
    """删除小说的向量索引"""
    try:
        from backend.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        success = vector_store.delete_novel_vectors(novel_id)
        
        return {
            "success": success,
            "novel_id": novel_id,
            "message": "向量索引已删除" if success else "删除失败"
        }
        
    except Exception as e:
        logger.error(f"删除向量索引失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vector/reset")
async def reset_vector_store():
    """重置向量库（删除所有数据）"""
    try:
        from backend.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        vector_store.reset()
        
        return {
            "success": True,
            "message": "向量库已重置"
        }
        
    except Exception as e:
        logger.error(f"重置向量库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== WebSocket 端点 ==========
from fastapi import WebSocket
from backend.websocket import (
    manager, handle_websocket,
    MessageType, AgentStage,
    create_stage_start_message, create_stage_progress_message,
    create_stage_complete_message, create_overall_progress_message,
    create_chapter_progress_message, create_chapter_complete_message,
    create_completed_message
)
import logging

logger = logging.getLogger(__name__)

# 添加 WebSocket 路由（在 if __name__ 之前）
@app.websocket("/ws/{novel_id}")
async def websocket_endpoint(websocket: WebSocket, novel_id: int):
    """WebSocket 实时通信"""
    logger.info(f"WebSocket connection: novel_id={novel_id}")
    await handle_websocket(websocket, novel_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
