"""
ChromaDB 向量记忆层
实现语义检索、相似度匹配
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import json
import os


class VectorMemory:
    """ChromaDB 向量记忆"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self._init_collections()
    
    def _init_collections(self):
        """初始化集合"""
        # 角色记忆集合
        try:
            self.characters = self.client.get_or_create_collection("characters")
        except:
            self.client.reset()
            self.characters = self.client.get_or_create_collection("characters")
        
        # 剧情记忆集合
        try:
            self.plots = self.client.get_or_create_collection("plots")
        except:
            self.plots = self.client.get_or_create_collection("plots")
        
        # 世界观记忆集合
        try:
            self.world = self.client.get_or_create_collection("world")
        except:
            self.world = self.client.get_or_create_collection("world")
    
    # ========== 角色记忆 ==========
    
    def add_character_memory(
        self,
        novel_id: int,
        character_id: str,
        name: str,
        description: str,
        embedding: List[float] = None
    ):
        """添加角色记忆"""
        self.characters.add(
            ids=[f"{novel_id}_{character_id}"],
            documents=[description],
            metadatas=[{
                "novel_id": novel_id,
                "character_id": character_id,
                "name": name
            }]
        )
    
    def search_characters(
        self,
        novel_id: int,
        query: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """搜索角色记忆"""
        results = self.characters.query(
            query_texts=[query],
            n_results=n_results,
            where={"novel_id": novel_id}
        )
        
        return self._format_results(results)
    
    # ========== 剧情记忆 ==========
    
    def add_plot_memory(
        self,
        novel_id: int,
        chapter_num: int,
        content: str,
        summary: str = ""
    ):
        """添加剧情记忆"""
        self.plots.add(
            ids=[f"{novel_id}_ch{chapter_num}"],
            documents=[content[:10000]],  # 限制长度
            metadatas=[{
                "novel_id": novel_id,
                "chapter_num": chapter_num,
                "summary": summary
            }]
        )
    
    def search_plots(
        self,
        novel_id: int,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """搜索剧情"""
        results = self.plots.query(
            query_texts=[query],
            n_results=n_results,
            where={"novel_id": novel_id}
        )
        
        return self._format_results(results)
    
    # ========== 世界观记忆 ==========
    
    def add_world_memory(
        self,
        novel_id: int,
        key: str,
        value: str
    ):
        """添加世界观记忆"""
        self.world.add(
            ids=[f"{novel_id}_{key}"],
            documents=[value],
            metadatas=[{
                "novel_id": novel_id,
                "key": key
            }]
        )
    
    def get_world_memory(
        self,
        novel_id: int
    ) -> Dict[str, str]:
        """获取世界观记忆"""
        results = self.world.get(
            where={"novel_id": novel_id}
        )
        
        world = {}
        if results and results.get("ids"):
            for i, id_ in enumerate(results["ids"]):
                key = results["metadatas"][i].get("key", "")
                world[key] = results["documents"][i]
        
        return world
    
    # ========== 工具方法 ==========
    
    def _format_results(self, results) -> List[Dict[str, Any]]:
        """格式化查询结果"""
        if not results or not results.get("ids"):
            return []
        
        formatted = []
        for i, id_ in enumerate(results["ids"]):
            formatted.append({
                "id": id_,
                "content": results["documents"][i] if i < len(results["documents"]) else "",
                "metadata": results["metadatas"][i] if i < len(results["metadatas"]) else {}
            })
        
        return formatted
    
    def delete_novel_memories(self, novel_id: int):
        """删除小说的所有记忆"""
        # 删除角色记忆
        char_results = self.characters.get(where={"novel_id": novel_id})
        if char_results.get("ids"):
            self.characters.delete(ids=char_results["ids"])
        
        # 删除剧情记忆
        plot_results = self.plots.get(where={"novel_id": novel_id})
        if plot_results.get("ids"):
            self.plots.delete(ids=plot_results["ids"])
        
        # 删除世界观记忆
        world_results = self.world.get(where={"novel_id": novel_id})
        if world_results.get("ids"):
            self.world.delete(ids=world_results["ids"])
    
    def close(self):
        """关闭连接"""
        # ChromaDB 不需要显式关闭


class EnhancedMemoryStore:
    """增强版记忆存储 - SQLite + ChromaDB"""
    
    def __init__(self, db_path: str = "novel_agent.db", chroma_path: str = "./chroma_db"):
        # SQLite 存储
        import sqlite3
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()
        
        # ChromaDB 向量存储
        self.vector = VectorMemory(chroma_path)
    
    def _init_tables(self):
        """初始化SQLite表"""
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
                description TEXT,
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
                summary TEXT,
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
    
    def save_character(self, novel_id: int, character: Dict[str, Any]):
        """保存角色并添加到向量存储"""
        cursor = self.conn.cursor()
        
        # 保存到SQLite
        cursor.execute(
            "INSERT INTO characters (novel_id, name, role, psychology, behavior, relationships, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (novel_id, 
             character.get("name"), 
             character.get("role"),
             json.dumps(character.get("psychology", {}), ensure_ascii=False),
             json.dumps(character.get("behavior", {}), ensure_ascii=False),
             json.dumps(character.get("relationships", []), ensure_ascii=False),
             json.dumps(character, ensure_ascii=False))
        )
        self.conn.commit()
        
        # 添加到向量存储
        char_id = cursor.lastrowid
        description = f"{character.get('name')} - {character.get('role')}: {character.get('psychology', {}).get('core_motivation', '')}"
        self.vector.add_character_memory(
            novel_id=novel_id,
            character_id=str(char_id),
            name=character.get("name", ""),
            description=description
        )
    
    def save_chapter(self, novel_id: int, chapter_num: int, content: str, summary: str = ""):
        """保存章节并添加到向量存储"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO chapters (novel_id, chapter_num, content, summary, status) VALUES (?, ?, ?, ?, ?)",
            (novel_id, chapter_num, content, summary, "draft")
        )
        self.conn.commit()
        
        # 添加到向量存储
        self.vector.add_plot_memory(
            novel_id=novel_id,
            chapter_num=chapter_num,
            content=content,
            summary=summary
        )
    
    def search_characters_by_semantic(self, novel_id: int, query: str) -> List[Dict[str, Any]]:
        """语义搜索角色"""
        return self.vector.search_characters(novel_id, query)
    
    def search_plots_by_semantic(self, novel_id: int, query: str) -> List[Dict[str, Any]]:
        """语义搜索剧情"""
        return self.vector.search_plots(novel_id, query)
    
    def save_world_settings(self, novel_id: int, world_settings: Dict[str, Any]):
        """保存世界观设置"""
        # 保存到向量存储
        for key, value in world_settings.items():
            if isinstance(value, (str, dict, list)):
                value_str = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
                self.vector.add_world_memory(novel_id, key, value_str)
    
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
                "outline": json.loads(row[3]) if row[3] else {},
                "status": row[4]
            }
        return None
    
    def get_characters(self, novel_id: int) -> List[Dict[str, Any]]:
        """获取角色列表"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM characters WHERE novel_id = ?", (novel_id,))
        rows = cursor.fetchall()
        return [{"id": r[0], "name": r[2], "role": r[3]} for r in rows]
    
    def delete_novel(self, novel_id: int):
        """删除小说及所有相关记忆"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM novels WHERE id = ?", (novel_id,))
        cursor.execute("DELETE FROM characters WHERE novel_id = ?", (novel_id,))
        cursor.execute("DELETE FROM chapters WHERE novel_id = ?", (novel_id,))
        cursor.execute("DELETE FROM foreshadowing WHERE novel_id = ?", (novel_id,))
        self.conn.commit()
        
        # 删除向量记忆
        self.vector.delete_novel_memories(novel_id)
    
    def close(self):
        """关闭连接"""
        self.conn.close()
        self.vector.close()
