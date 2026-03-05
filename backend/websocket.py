"""
WebSocket 实时通信支持 - 简洁版
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.heartbeat_tasks: Dict[int, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, novel_id: int):
        """连接"""
        await websocket.accept()
        if novel_id not in self.active_connections:
            self.active_connections[novel_id] = []
        self.active_connections[novel_id].append(websocket)
        
        # 启动心跳
        if novel_id not in self.heartbeat_tasks:
            self.heartbeat_tasks[novel_id] = asyncio.create_task(
                self._heartbeat_loop(novel_id)
            )
        
        logger.info(f"WebSocket connected: novel_id={novel_id}")
    
    def disconnect(self, websocket: WebSocket, novel_id: int):
        """断开"""
        if novel_id in self.active_connections:
            if websocket in self.active_connections[novel_id]:
                self.active_connections[novel_id].remove(websocket)
            
            if not self.active_connections[novel_id]:
                self.active_connections.pop(novel_id, None)
                if novel_id in self.heartbeat_tasks:
                    self.heartbeat_tasks[novel_id].cancel()
                    self.heartbeat_tasks.pop(novel_id, None)
    
    async def _heartbeat_loop(self, novel_id: int):
        """心跳循环"""
        try:
            while True:
                await asyncio.sleep(30)
                if novel_id in self.active_connections:
                    await self.send_message({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    }, novel_id)
        except asyncio.CancelledError:
            pass
    
    async def send_message(self, message: dict, novel_id: int):
        """发送消息"""
        if novel_id not in self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections[novel_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Send error: {e}")
                disconnected.append(connection)
        
        for ws in disconnected:
            self.disconnect(ws, novel_id)
    
    async def broadcast(self, message: dict):
        """广播"""
        for novel_id in list(self.active_connections.keys()):
            await self.send_message(message, novel_id)
    
    def is_connected(self, novel_id: int) -> bool:
        return novel_id in self.active_connections and len(self.active_connections[novel_id]) > 0


manager = ConnectionManager()


# 消息类型
class MessageType:
    STAGE_PROGRESS = "stage_progress"
    STAGE_START = "stage_start"
    STAGE_COMPLETE = "stage_complete"
    STAGE_ERROR = "stage_error"
    PROGRESS = "progress"
    CHAPTER_PROGRESS = "chapter_progress"
    CHAPTER_COMPLETE = "chapter_complete"
    HEARTBEAT = "heartbeat"
    CONNECTED = "connected"
    ERROR = "error"
    COMPLETED = "completed"


# Agent 阶段
class AgentStage:
    IDLE = "idle"
    PLANNING = "planning"
    GENERATING_OUTLINE = "generating_outline"
    GENERATING_CHARACTERS = "generating_characters"
    GENERATING_WORLD = "generating_world"
    GENERATING_FORESHADOWING = "generating_foreshadowing"
    WRITING_CHAPTERS = "writing_chapters"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    
    @classmethod
    def get_stage_name(cls, stage: str) -> str:
        names = {
            cls.IDLE: "空闲",
            cls.PLANNING: "需求分析",
            cls.GENERATING_OUTLINE: "生成大纲",
            cls.GENERATING_CHARACTERS: "生成角色",
            cls.GENERATING_WORLD: "世界观设定",
            cls.GENERATING_FORESHADOWING: "伏笔设计",
            cls.WRITING_CHAPTERS: "章节写作",
            cls.REVIEWING: "审核优化",
            cls.COMPLETED: "完成"
        }
        return names.get(stage, stage)
    
    @classmethod
    def get_all_stages(cls) -> List[str]:
        return [
            cls.PLANNING,
            cls.GENERATING_OUTLINE,
            cls.GENERATING_CHARACTERS,
            cls.GENERATING_WORLD,
            cls.GENERATING_FORESHADOWING,
            cls.WRITING_CHAPTERS,
            cls.REVIEWING,
            cls.COMPLETED
        ]
    
    @classmethod
    def get_stage_weight(cls, stage: str) -> float:
        weights = {
            cls.PLANNING: 0.05,
            cls.GENERATING_OUTLINE: 0.15,
            cls.GENERATING_CHARACTERS: 0.10,
            cls.GENERATING_WORLD: 0.05,
            cls.GENERATING_FORESHADOWING: 0.05,
            cls.WRITING_CHAPTERS: 0.50,
            cls.REVIEWING: 0.08,
            cls.COMPLETED: 0.02
        }
        return weights.get(stage, 0.0)


async def handle_websocket(websocket: WebSocket, novel_id: int):
    """处理 WebSocket 连接"""
    await manager.connect(websocket, novel_id)
    
    try:
        # 发送连接确认
        await websocket.send_json({
            "type": MessageType.CONNECTED,
            "novel_id": novel_id,
            "message": "Connected successfully",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: novel_id={novel_id}")
        manager.disconnect(websocket, novel_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await manager.send_message({
            "type": MessageType.ERROR,
            "message": str(e)
        }, novel_id)
        manager.disconnect(websocket, novel_id)


# ========== 进度消息创建函数 ==========

def create_stage_progress_message(stage: str, progress: float, message: str = "", detail: dict = None) -> dict:
    return {
        "type": MessageType.STAGE_PROGRESS,
        "stage": stage,
        "stage_name": AgentStage.get_stage_name(stage),
        "progress": progress,
        "message": message,
        "detail": detail or {},
        "timestamp": datetime.now().isoformat()
    }


def create_stage_start_message(stage: str, total_items: int = 0, message: str = "") -> dict:
    return {
        "type": MessageType.STAGE_START,
        "stage": stage,
        "stage_name": AgentStage.get_stage_name(stage),
        "total_items": total_items,
        "message": message or f"开始 {AgentStage.get_stage_name(stage)}",
        "timestamp": datetime.now().isoformat()
    }


def create_stage_complete_message(stage: str, result: dict = None, message: str = "") -> dict:
    return {
        "type": MessageType.STAGE_COMPLETE,
        "stage": stage,
        "stage_name": AgentStage.get_stage_name(stage),
        "message": message or f"{AgentStage.get_stage_name(stage)} 完成",
        "result": result or {},
        "timestamp": datetime.now().isoformat()
    }


def create_overall_progress_message(current_stage: str, overall_progress: float, stage_progress: float, detail: dict = None) -> dict:
    stages = AgentStage.get_all_stages()
    current_index = stages.index(current_stage) if current_stage in stages else 0
    
    return {
        "type": MessageType.PROGRESS,
        "current_stage": current_stage,
        "current_stage_name": AgentStage.get_stage_name(current_stage),
        "overall_progress": overall_progress,
        "stage_progress": stage_progress,
        "stages": [
            {
                "id": s,
                "name": AgentStage.get_stage_name(s),
                "weight": int(AgentStage.get_stage_weight(s) * 100),
                "completed": s in stages[:current_index] or (s == current_stage and stage_progress >= 100)
            }
            for s in stages
        ],
        "detail": detail or {},
        "timestamp": datetime.now().isoformat()
    }


def create_chapter_progress_message(chapter_num: int, total_chapters: int, progress: float) -> dict:
    return {
        "type": MessageType.CHAPTER_PROGRESS,
        "chapter_num": chapter_num,
        "total_chapters": total_chapters,
        "progress": progress,
        "timestamp": datetime.now().isoformat()
    }


def create_chapter_complete_message(chapter_num: int, content: str, word_count: int, review_result: dict = None) -> dict:
    return {
        "type": MessageType.CHAPTER_COMPLETE,
        "chapter_num": chapter_num,
        "word_count": word_count,
        "preview": content[:200] + "..." if len(content) > 200 else content,
        "review_approved": review_result.get("approved") if review_result else None,
        "timestamp": datetime.now().isoformat()
    }


def create_completed_message(novel_id: int, total_chapters: int, total_words: int) -> dict:
    return {
        "type": MessageType.COMPLETED,
        "novel_id": novel_id,
        "total_chapters": total_chapters,
        "total_words": total_words,
        "message": "所有章节写作完成！",
        "timestamp": datetime.now().isoformat()
    }


# 兼容旧接口
def create_progress_message(current, total, chapter="", status="writing"):
    progress = int(current / total * 100) if total > 0 else 0
    return {
        "type": "progress",
        "data": {
            "current": current,
            "total": total,
            "progress": progress,
            "chapter": chapter,
            "status": status
        }
    }
