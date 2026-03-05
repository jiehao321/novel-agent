"""
异常处理、重试与回滚机制
提供 Agent 执行异常捕获、自动重试、章节回滚功能
"""
import time
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """重试策略"""
    IMMEDIATE = "immediate"  # 立即重试
    LINEAR = "linear"       # 线性等待
    EXPONENTIAL = "exponential"  # 指数退避


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    initial_delay: float = 1.0  # 初始延迟（秒）
    max_delay: float = 30.0     # 最大延迟（秒）
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0  # 退避倍数


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    data: Any = None
    error: str = ""
    attempt: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentExecutor:
    """Agent 执行器 - 带异常捕获和自动重试"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> ExecutionResult:
        """
        执行函数并自动重试
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
        
        Returns:
            ExecutionResult: 执行结果
        """
        last_error = None
        
        for attempt in range(1, self.config.max_retries + 1):
            try:
                logger.info(f"执行尝试 {attempt}/{self.config.max_retries}")
                
                result = func(*args, **kwargs)
                
                # 检查结果是否表示失败
                if self._is_failure(result):
                    last_error = self._get_error_message(result)
                    logger.warning(f"执行失败: {last_error}")
                else:
                    return ExecutionResult(
                        success=True,
                        data=result,
                        attempt=attempt,
                        metadata={"retries": attempt - 1}
                    )
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"执行异常: {last_error}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.config.max_retries:
                delay = self._calculate_delay(attempt)
                logger.info(f"等待 {delay:.1f}s 后重试...")
                time.sleep(delay)
        
        return ExecutionResult(
            success=False,
            error=last_error or "未知错误",
            attempt=self.config.max_retries,
            metadata={"retries": self.config.max_retries}
        )
    
    def _is_failure(self, result: Any) -> bool:
        """检查结果是否表示失败"""
        if isinstance(result, dict):
            return "error" in result and result.get("error")
        if hasattr(result, "success"):
            return not result.success
        return False
    
    def _get_error_message(self, result: Any) -> str:
        """获取错误消息"""
        if isinstance(result, dict):
            return result.get("error", "未知错误")
        if hasattr(result, "error"):
            return result.error
        return "未知错误"
    
    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        if self.config.strategy == RetryStrategy.IMMEDIATE:
            return 0
        elif self.config.strategy == RetryStrategy.LINEAR:
            return self.config.initial_delay * attempt
        else:  # EXPONENTIAL
            delay = self.config.initial_delay * (self.config.backoff_multiplier ** (attempt - 1))
            return min(delay, self.config.max_delay)


class ChapterVersionManager:
    """章节版本管理器 - 实现自动回滚"""
    
    def __init__(self, db_path: str = "novel_agent.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def _init_tables(self):
        """初始化版本管理表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 章节版本表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapter_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER NOT NULL,
                chapter_num INTEGER NOT NULL,
                version_num INTEGER NOT NULL,
                content TEXT NOT NULL,
                word_count INTEGER,
                status TEXT DEFAULT 'draft',
                review_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT DEFAULT 'system',
                UNIQUE (novel_id, chapter_num, version_num)
            )
        """)
        
        # 章节操作日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapter_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER NOT NULL,
                chapter_num INTEGER NOT NULL,
                action TEXT NOT NULL,
                old_version INTEGER,
                new_version INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 人工复审表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS manual_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER NOT NULL,
                chapter_num INTEGER NOT NULL,
                version_num INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                reviewer_note TEXT,
                reviewer_action TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_version(
        self,
        novel_id: int,
        chapter_num: int,
        content: str,
        status: str = "draft",
        review_result: Dict = None,
        created_by: str = "system"
    ) -> int:
        """
        保存章节新版本
        
        Returns:
            int: 新版本号
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 获取当前最新版本号
        cursor.execute("""
            SELECT MAX(version_num) FROM chapter_versions 
            WHERE novel_id = ? AND chapter_num = ?
        """, (novel_id, chapter_num))
        
        row = cursor.fetchone()
        current_version = row[0] if row and row[0] else 0
        new_version = current_version + 1
        
        # 插入新版本
        word_count = len(content)
        cursor.execute("""
            INSERT INTO chapter_versions 
            (novel_id, chapter_num, version_num, content, word_count, status, review_result, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            novel_id, chapter_num, new_version, content, word_count,
            status, json.dumps(review_result, ensure_ascii=False) if review_result else None,
            created_by
        ))
        
        # 记录日志
        cursor.execute("""
            INSERT INTO chapter_logs 
            (novel_id, chapter_num, action, new_version)
            VALUES (?, ?, ?, ?)
        """, (novel_id, chapter_num, "version_created", new_version))
        
        conn.commit()
        conn.close()
        
        logger.info(f"保存章节版本: novel={novel_id}, chapter={chapter_num}, version={new_version}")
        
        return new_version
    
    def get_version(
        self,
        novel_id: int,
        chapter_num: int,
        version_num: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定版本的章节内容
        
        Args:
            novel_id: 小说ID
            chapter_num: 章节号
            version_num: 版本号（None 表示最新版本）
        
        Returns:
            章节内容字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if version_num is None:
            # 获取最新版本
            cursor.execute("""
                SELECT * FROM chapter_versions 
                WHERE novel_id = ? AND chapter_num = ?
                ORDER BY version_num DESC LIMIT 1
            """, (novel_id, chapter_num))
        else:
            cursor.execute("""
                SELECT * FROM chapter_versions 
                WHERE novel_id = ? AND chapter_num = ? AND version_num = ?
            """, (novel_id, chapter_num, version_num))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "novel_id": row[1],
                "chapter_num": row[2],
                "version_num": row[3],
                "content": row[4],
                "word_count": row[5],
                "status": row[6],
                "review_result": json.loads(row[7]) if row[7] else None,
                "created_at": row[8],
                "created_by": row[9]
            }
        return None
    
    def get_version_history(
        self,
        novel_id: int,
        chapter_num: int
    ) -> list:
        """获取版本历史"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT version_num, status, word_count, created_at, created_by
            FROM chapter_versions 
            WHERE novel_id = ? AND chapter_num = ?
            ORDER BY version_num DESC
        """, (novel_id, chapter_num))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "version_num": r[0],
                "status": r[1],
                "word_count": r[2],
                "created_at": r[3],
                "created_by": r[4]
            }
            for r in rows
        ]
    
    def rollback(
        self,
        novel_id: int,
        chapter_num: int,
        target_version: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        回滚到指定版本
        
        Args:
            novel_id: 小说ID
            chapter_num: 章节号
            target_version: 目标版本号（None 表示回滚到上一版本）
        
        Returns:
            回滚后的版本信息
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if target_version is None:
            # 获取上一版本
            cursor.execute("""
                SELECT version_num FROM chapter_versions 
                WHERE novel_id = ? AND chapter_num = ?
                ORDER BY version_num DESC LIMIT 1 OFFSET 1
            """, (novel_id, chapter_num))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            target_version = row[0]
        
        # 获取目标版本内容
        version = self.get_version(novel_id, chapter_num, target_version)
        if not version:
            conn.close()
            return None
        
        # 创建新版本（复制目标版本内容）
        new_version = self.save_version(
            novel_id, chapter_num, version["content"],
            status="rolled_back",
            created_by="system"
        )
        
        # 记录回滚日志
        cursor.execute("""
            INSERT INTO chapter_logs 
            (novel_id, chapter_num, action, old_version, new_version)
            VALUES (?, ?, ?, ?, ?)
        """, (novel_id, chapter_num, "rollback", target_version, new_version))
        
        conn.commit()
        conn.close()
        
        logger.info(f"章节回滚: novel={novel_id}, chapter={chapter_num}, to_version={new_version}")
        
        return self.get_version(novel_id, chapter_num, new_version)
    
    def get_latest_version_num(self, novel_id: int, chapter_num: int) -> int:
        """获取最新版本号"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT MAX(version_num) FROM chapter_versions 
            WHERE novel_id = ? AND chapter_num = ?
        """, (novel_id, chapter_num))
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row and row[0] else 0


class ManualReviewManager:
    """人工复审管理器"""
    
    def __init__(self, db_path: str = "novel_agent.db"):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def create_review_request(
        self,
        novel_id: int,
        chapter_num: int,
        version_num: int
    ) -> int:
        """创建人工复审请求"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO manual_reviews 
            (novel_id, chapter_num, version_num, status)
            VALUES (?, ?, ?, 'pending')
        """, (novel_id, chapter_num, version_num))
        
        review_id = cursor.lastrowid
        
        # 记录操作日志
        cursor.execute("""
            INSERT INTO chapter_logs 
            (novel_id, chapter_num, action, details)
            VALUES (?, ?, ?, ?)
        """, (novel_id, chapter_num, "review_requested", 
              json.dumps({"review_id": review_id})))
        
        conn.commit()
        conn.close()
        
        return review_id
    
    def get_pending_reviews(self) -> list:
        """获取待处理的复审请求"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT mr.id, mr.novel_id, mr.chapter_num, mr.version_num, 
                   mr.status, mr.reviewer_note, mr.created_at,
                   cv.content
            FROM manual_reviews mr
            LEFT JOIN chapter_versions cv ON 
                mr.novel_id = cv.novel_id AND 
                mr.chapter_num = cv.chapter_num AND 
                mr.version_num = cv.version_num
            WHERE mr.status = 'pending'
            ORDER BY mr.created_at ASC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0],
                "novel_id": r[1],
                "chapter_num": r[2],
                "version_num": r[3],
                "status": r[4],
                "reviewer_note": r[5],
                "created_at": r[6],
                "content": r[7]
            }
            for r in rows
        ]
    
    def complete_review(
        self,
        review_id: int,
        action: str,  # "approve" | "reject" | "request_changes"
        reviewer_note: str = ""
    ) -> bool:
        """
        完成人工复审
        
        Args:
            review_id: 复审ID
            action: 审核动作
            reviewer_note: 审核备注
        
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 获取复审信息
        cursor.execute("""
            SELECT novel_id, chapter_num, version_num FROM manual_reviews 
            WHERE id = ?
        """, (review_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        
        novel_id, chapter_num, version_num = row
        
        # 更新复审状态
        cursor.execute("""
            UPDATE manual_reviews 
            SET status = ?, reviewer_note = ?, reviewer_action = ?, 
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (action, reviewer_note, action, review_id))
        
        # 更新章节状态
        status_map = {
            "approve": "approved",
            "reject": "rejected",
            "request_changes": "needs_revision"
        }
        
        cursor.execute("""
            UPDATE chapter_versions 
            SET status = ?
            WHERE novel_id = ? AND chapter_num = ? AND version_num = ?
        """, (status_map.get(action, "pending"), novel_id, chapter_num, version_num))
        
        # 记录日志
        cursor.execute("""
            INSERT INTO chapter_logs 
            (novel_id, chapter_num, action, details)
            VALUES (?, ?, ?, ?)
        """, (novel_id, chapter_num, "review_completed",
              json.dumps({"review_id": review_id, "action": action, "note": reviewer_note})))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_review_history(
        self,
        novel_id: int = None,
        chapter_num: int = None
    ) -> list:
        """获取复审历史"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM manual_reviews WHERE 1=1"
        params = []
        
        if novel_id is not None:
            query += " AND novel_id = ?"
            params.append(novel_id)
        
        if chapter_num is not None:
            query += " AND chapter_num = ?"
            params.append(chapter_num)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0],
                "novel_id": r[1],
                "chapter_num": r[2],
                "version_num": r[3],
                "status": r[4],
                "reviewer_note": r[5],
                "reviewer_action": r[6],
                "created_at": r[7],
                "completed_at": r[8]
            }
            for r in rows
        ]


# 全局单例
_version_manager: Optional[ChapterVersionManager] = None
_manual_review_manager: Optional[ManualReviewManager] = None


def get_version_manager(db_path: str = "novel_agent.db") -> ChapterVersionManager:
    """获取版本管理器单例"""
    global _version_manager
    if _version_manager is None:
        _version_manager = ChapterVersionManager(db_path)
    return _version_manager


def get_manual_review_manager(db_path: str = "novel_agent.db") -> ManualReviewManager:
    """获取人工复审管理器单例"""
    global _manual_review_manager
    if _manual_review_manager is None:
        _manual_review_manager = ManualReviewManager(db_path)
    return _manual_review_manager
