"""
向量检索模块 - ChromaDB 实现
用于小说内容的向量存储和相似章节检索

注意：本模块使用 ChromaDB 的内置嵌入功能，无需额外安装 sentence-transformers
"""
import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# ChromaDB 配置
import chromadb
from chromadb.config import Settings


@dataclass
class ChapterVector:
    """章节向量数据"""
    novel_id: int
    chapter_num: int
    content: str
    summary: str = ""
    metadata: Dict[str, Any] = None


class VectorStore:
    """向量存储管理器"""
    
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        """初始化向量存储
        
        Args:
            persist_directory: ChromaDB 持久化目录
        """
        self.persist_directory = persist_directory
        
        # 确保目录存在
        os.makedirs(persist_directory, exist_ok=True)
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 集合名称
        self.collection_name = "novel_chapters"
        
        # 初始化集合
        self._init_collection()
    
    def _init_collection(self):
        """初始化或获取集合"""
        try:
            # 尝试获取现有集合
            self.collection = self.client.get_collection(name=self.collection_name)
        except Exception:
            # 创建新集合（不使用 embedding function，使用 ChromaDB 内置默认嵌入）
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Novel chapters for semantic search"}
            )
    
    def _generate_id(self, novel_id: int, chapter_num: int) -> str:
        """生成向量 ID"""
        return f"novel_{novel_id}_chapter_{chapter_num}"
    
    def _get_text_for_embedding(self, chapter: ChapterVector) -> str:
        """获取用于嵌入的文本"""
        parts = []
        if chapter.summary:
            parts.append(f"章节摘要：{chapter.summary}")
        parts.append(f"章节内容：{chapter.content[:2000]}")  # 限制长度
        return "\n".join(parts)
    
    def add_chapter(self, chapter: ChapterVector) -> bool:
        """添加章节到向量库
        
        Args:
            chapter: 章节向量数据
            
        Returns:
            是否成功
        """
        try:
            doc_id = self._generate_id(chapter.novel_id, chapter.chapter_num)
            
            # 准备文档和元数据
            document = self._get_text_for_embedding(chapter)
            metadata = {
                "novel_id": chapter.novel_id,
                "chapter_num": chapter.chapter_num,
                "summary": chapter.summary or "",
                "content_preview": chapter.content[:500] if chapter.content else "",
                "word_count": len(chapter.content) if chapter.content else 0
            }
            
            # 先尝试 add（新增），失败后再 update（更新）
            try:
                self.collection.add(
                    ids=[doc_id],
                    documents=[document],
                    metadatas=[metadata]
                )
            except Exception as add_error:
                # 如果已存在，则更新
                try:
                    self.collection.update(
                        ids=[doc_id],
                        documents=[document],
                        metadatas=[metadata]
                    )
                except Exception as update_error:
                    print(f"Error updating chapter: {update_error}")
                    raise
            
            return True
        except Exception as e:
            print(f"Error adding chapter to vector store: {e}")
            return False
    
    def add_chapters(self, chapters: List[ChapterVector]) -> Dict[str, int]:
        """批量添加章节
        
        Args:
            chapters: 章节列表
            
        Returns:
            统计结果
        """
        success_count = 0
        fail_count = 0
        
        for chapter in chapters:
            if self.add_chapter(chapter):
                success_count += 1
            else:
                fail_count += 1
        
        return {
            "success": success_count,
            "failed": fail_count,
            "total": len(chapters)
        }
    
    def search_similar_chapters(
        self,
        query: str,
        novel_id: Optional[int] = None,
        top_k: int = 5,
        include_content: bool = True
    ) -> List[Dict[str, Any]]:
        """搜索相似章节
        
        Args:
            query: 查询文本
            novel_id: 可选，限定小说 ID
            top_k: 返回结果数量
            include_content: 是否包含完整内容
            
        Returns:
            相似章节列表
        """
        try:
            # 准备查询
            where_clause = {"novel_id": novel_id} if novel_id else None
            
            # 执行查询
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_clause,
                include=["metadatas", "distances", "documents"] if include_content else ["metadatas", "distances"]
            )
            
            # 整理结果
            similar_chapters = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    
                    chapter_info = {
                        "doc_id": doc_id,
                        "novel_id": metadata.get("novel_id"),
                        "chapter_num": metadata.get("chapter_num"),
                        "summary": metadata.get("summary", ""),
                        "word_count": metadata.get("word_count", 0),
                        "similarity_score": 1 - distance,  # 转换为相似度
                        "distance": distance
                    }
                    
                    if include_content and results.get("documents"):
                        chapter_info["content_preview"] = results["documents"][0][i][:1000]
                    
                    similar_chapters.append(chapter_info)
            
            return similar_chapters
            
        except Exception as e:
            print(f"Error searching similar chapters: {e}")
            return []
    
    def get_chapter_vector(self, novel_id: int, chapter_num: int) -> Optional[Dict[str, Any]]:
        """获取指定章节的向量信息
        
        Args:
            novel_id: 小说 ID
            chapter_num: 章节编号
            
        Returns:
            向量信息
        """
        try:
            doc_id = self._generate_id(novel_id, chapter_num)
            result = self.collection.get(ids=[doc_id], include=["metadatas", "documents"])
            
            if result and result.get("ids"):
                metadata = result["metadatas"][0]
                return {
                    "doc_id": doc_id,
                    "novel_id": metadata.get("novel_id"),
                    "chapter_num": metadata.get("chapter_num"),
                    "summary": metadata.get("summary", ""),
                    "content_preview": metadata.get("content_preview", ""),
                    "word_count": metadata.get("word_count", 0)
                }
            return None
            
        except Exception as e:
            print(f"Error getting chapter vector: {e}")
            return None
    
    def delete_novel_vectors(self, novel_id: int) -> bool:
        """删除小说的所有向量
        
        Args:
            novel_id: 小说 ID
            
        Returns:
            是否成功
        """
        try:
            # 获取该小说的所有向量 ID
            results = self.collection.get(
                where={"novel_id": novel_id},
                include=["metadatas"]
            )
            
            if results and results.get("ids"):
                self.collection.delete(ids=results["ids"])
            
            return True
        except Exception as e:
            print(f"Error deleting novel vectors: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            count = self.collection.count()
            return {
                "total_chapters": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            return {"error": str(e)}
    
    def reset(self):
        """重置集合（删除所有数据）"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self._init_collection()
        except Exception as e:
            print(f"Error resetting collection: {e}")


# 全局向量存储实例
_vector_store: Optional[VectorStore] = None


def get_vector_store(persist_directory: str = "./data/chroma_db") -> VectorStore:
    """获取全局向量存储实例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(persist_directory=persist_directory)
    return _vector_store


def init_vector_store(persist_directory: str = "./data/chroma_db") -> VectorStore:
    """初始化向量存储"""
    global _vector_store
    _vector_store = VectorStore(persist_directory=persist_directory)
    return _vector_store
