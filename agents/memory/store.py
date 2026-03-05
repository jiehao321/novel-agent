"""
记忆层 - 持久化存储
"""
import sqlite3
from typing import Dict, Any, List, Optional
import json


class MemoryStore:
    """SQLite 记忆存储"""
    
    def __init__(self, db_path: str = "novel_agent.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.init_tables()
    
    def init_tables(self):
        """初始化表结构"""
        cursor = self.conn.cursor()
        
        # 小说表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS novels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                genre TEXT,
                outline TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 卷表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS volumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER,
                volume_num INTEGER,
                title TEXT,
                introduction TEXT,
                start_chapter INTEGER,
                end_chapter INTEGER,
                theme TEXT,
                core_conflict TEXT,
                core_goal TEXT,
                plot_direction TEXT,
                chapter_groups TEXT,
                rhythm_curve TEXT,
                character_appearances TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (novel_id) REFERENCES novels(id)
            )
        """)
        
        # 角色表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER,
                name TEXT,
                role TEXT,
                psychology TEXT,
                behavior TEXT,
                relationships TEXT,
                FOREIGN KEY (novel_id) REFERENCES novels(id)
            )
        """)
        
        # 章节表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER,
                chapter_num INTEGER,
                content TEXT,
                status TEXT,
                review_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (novel_id) REFERENCES novels(id)
            )
        """)
        
        # 伏笔表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS foreshadowing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER,
                fs_type TEXT,
                description TEXT,
                importance INTEGER,
                plant_chapter INTEGER,
                reveal_chapter INTEGER,
                status TEXT,
                FOREIGN KEY (novel_id) REFERENCES novels(id)
            )
        """)
        
        self.conn.commit()
    
    def update_novel(self, novel_id: int, updates: Dict[str, Any]) -> bool:
        """更新小说信息"""
        cursor = self.conn.cursor()
        
        # 构建动态更新语句
        set_parts = []
        values = []
        for key in ["title", "genre", "outline", "status", "characters", "world_settings", "foreshadowing"]:
            if key in updates:
                set_parts.append(f"{key} = ?")
                if key == "outline":
                    values.append(json.dumps(updates[key], ensure_ascii=False))
                else:
                    values.append(updates[key])
        
        if not set_parts:
            return False
        
        values.append(novel_id)
        query = f"UPDATE novels SET {', '.join(set_parts)} WHERE id = ?"
        cursor.execute(query, values)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def save_novel(self, novel: Dict[str, Any]) -> int:
        """保存小说"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO novels (title, genre, outline, status) VALUES (?, ?, ?, ?)",
            (novel.get("title"), novel.get("genre"), 
             json.dumps(novel.get("outline", {}), ensure_ascii=False),
             novel.get("status", "planning"))
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def save_volume(self, volume: Dict[str, Any]) -> int:
        """保存卷信息"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO volumes (
                novel_id, volume_num, title, introduction, 
                start_chapter, end_chapter, theme, core_conflict,
                core_goal, plot_direction, chapter_groups, rhythm_curve, character_appearances
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            volume.get("novel_id"),
            volume.get("volume_num"),
            volume.get("title"),
            volume.get("introduction"),
            volume.get("start_chapter"),
            volume.get("end_chapter"),
            volume.get("theme"),
            volume.get("core_conflict"),
            volume.get("core_goal"),
            volume.get("plot_direction"),
            json.dumps(volume.get("chapter_groups", []), ensure_ascii=False),
            json.dumps(volume.get("rhythm_curve", {}), ensure_ascii=False),
            json.dumps(volume.get("character_appearances", []), ensure_ascii=False)
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def save_volumes(self, novel_id: int, volumes: List[Dict[str, Any]]):
        """批量保存卷信息"""
        cursor = self.conn.cursor()
        for volume in volumes:
            cursor.execute("""
                INSERT INTO volumes (
                    novel_id, volume_num, title, introduction, 
                    start_chapter, end_chapter, theme, core_conflict,
                    core_goal, plot_direction, chapter_groups, rhythm_curve, character_appearances
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                novel_id,
                volume.get("volume_num"),
                volume.get("title"),
                volume.get("introduction"),
                volume.get("start_chapter"),
                volume.get("end_chapter"),
                volume.get("theme"),
                volume.get("core_conflict"),
                volume.get("core_goal"),
                volume.get("plot_direction"),
                json.dumps(volume.get("chapter_groups", []), ensure_ascii=False),
                json.dumps(volume.get("rhythm_curve", {}), ensure_ascii=False),
                json.dumps(volume.get("character_appearances", []), ensure_ascii=False)
            ))
        self.conn.commit()
    
    def get_volumes(self, novel_id: int) -> List[Dict[str, Any]]:
        """获取小说的所有卷"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM volumes WHERE novel_id = ? ORDER BY volume_num", (novel_id,))
        rows = cursor.fetchall()
        
        volumes = []
        for row in rows:
            volumes.append({
                "id": row[0],
                "novel_id": row[1],
                "volume_num": row[2],
                "title": row[3],
                "introduction": row[4],
                "start_chapter": row[5],
                "end_chapter": row[6],
                "theme": row[7],
                "core_conflict": row[8],
                "core_goal": row[9],
                "plot_direction": row[10],
                "chapter_groups": json.loads(row[11]) if row[11] else [],
                "rhythm_curve": json.loads(row[12]) if row[12] else {},
                "character_appearances": json.loads(row[13]) if row[13] else []
            })
        return volumes
    
    def update_volume(self, volume_id: int, updates: Dict[str, Any]):
        """更新卷信息"""
        cursor = self.conn.cursor()
        
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ["title", "introduction", "theme", "core_conflict", "core_goal", "plot_direction"]:
                set_clauses.append(f"{key} = ?")
                values.append(value)
            elif key in ["chapter_groups", "rhythm_curve", "character_appearances"]:
                set_clauses.append(f"{key} = ?")
                values.append(json.dumps(value, ensure_ascii=False))
        
        if set_clauses:
            values.append(volume_id)
            cursor.execute(
                f"UPDATE volumes SET {', '.join(set_clauses)} WHERE id = ?",
                values
            )
            self.conn.commit()
    
    def delete_volumes(self, novel_id: int):
        """删除小说的所有卷"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM volumes WHERE novel_id = ?", (novel_id,))
        self.conn.commit()
    
    def save_character(self, novel_id: int, character: Dict[str, Any]):
        """保存角色"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO characters (novel_id, name, role, psychology, behavior, relationships) VALUES (?, ?, ?, ?, ?, ?)",
            (novel_id, character.get("name"), character.get("role"),
             json.dumps(character.get("psychology", {}), ensure_ascii=False),
             json.dumps(character.get("behavior", {}), ensure_ascii=False),
             json.dumps(character.get("relationships", []), ensure_ascii=False))
        )
        self.conn.commit()
    
    def save_chapter(self, novel_id: int, chapter_num: int, content: str):
        """保存章节"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO chapters (novel_id, chapter_num, content, status) VALUES (?, ?, ?, ?)",
            (novel_id, chapter_num, content, "draft")
        )
        self.conn.commit()
    
    def get_novel(self, novel_id: int) -> Optional[Dict[str, Any]]:
        """获取小说"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM novels WHERE id = ?", (novel_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "title": row[1],
                "genre": row[2],
                "outline": json.loads(row[3]),
                "status": row[4]
            }
        return None
    
    def get_characters(self, novel_id: int) -> List[Dict[str, Any]]:
        """获取角色列表"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM characters WHERE novel_id = ?", (novel_id,))
        rows = cursor.fetchall()
        return [{"id": r[0], "name": r[2], "role": r[3]} for r in rows]
    
    def close(self):
        """关闭连接"""
        self.conn.close()
