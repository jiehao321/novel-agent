"""
WebSocket 实时通信支持
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 活跃连接: {novel_id: [websockets]}
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, novel_id: int):
        """连接"""
        await websocket.accept()
        if novel_id not in self.active_connections:
            self.active_connections[novel_id] = []
        self.active_connections[novel_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, novel_id: int):
        """断开"""
        if novel_id in self.active_connections:
            if websocket in self.active_connections[novel_id]:
                self.active_connections[novel_id].remove(websocket)
    
    async def send_message(self, message: dict, novel_id: int):
        """发送消息"""
        if novel_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[novel_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # 清理断开的连接
            for ws in disconnected:
                self.disconnect(ws, novel_id)
    
    async def broadcast(self, message: dict):
        """广播消息"""
        for novel_id in self.active_connections:
            await self.send_message(message, novel_id)


# 全局管理器
manager = ConnectionManager()


# 消息类型
class MessageType:
    """消息类型"""
    PROGRESS = "progress"      # 进度更新
    STATUS = "status"          # 状态更新
    CHAPTER_COMPLETE = "chapter_complete"  # 章节完成
    ERROR = "error"            # 错误
    COMPLETED = "completed"     # 完成


async def handle_websocket(websocket: WebSocket, novel_id: int):
    """处理 WebSocket 连接"""
    await manager.connect(websocket, novel_id)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理消息
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, novel_id)
    except Exception as e:
        await manager.send_message({
            "type": MessageType.ERROR,
            "message": str(e)
        }, novel_id)


def create_progress_message(
    current: int,
    total: int,
    chapter: str = "",
    status: str = "writing"
) -> dict:
    """创建进度消息"""
    progress = int(current / total * 100) if total > 0 else 0
    return {
        "type": MessageType.PROGRESS,
        "data": {
            "current": current,
            "total": total,
            "progress": progress,
            "chapter": chapter,
            "status": status
        }
    }


def create_status_message(status: str, message: str) -> dict:
    """创建状态消息"""
    return {
        "type": MessageType.STATUS,
        "data": {
            "status": status,
            "message": message
        }
    }


def create_chapter_complete_message(chapter_num: int, content: str, word_count: int) -> dict:
    """创建章节完成消息"""
    return {
        "type": MessageType.CHAPTER_COMPLETE,
        "data": {
            "chapter_num": chapter_num,
            "word_count": word_count,
            "preview": content[:200] + "..." if len(content) > 200 else content
        }
    }


def create_completed_message(novel_id: int, total_chapters: int) -> dict:
    """创建完成消息"""
    return {
        "type": MessageType.COMPLETED,
        "data": {
            "novel_id": novel_id,
            "total_chapters": total_chapters,
            "message": "所有章节写作完成！"
        }
    }
