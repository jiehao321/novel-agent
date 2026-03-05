"""
完整的 Novel Agent Pipeline
整合所有 Agent，实现从需求到完稿的全流程
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from agents.base import AgentContext
from agents.planner.agents import PlanningPipeline
from agents.writer.agents import WritingPipeline
from agents.reviewer.agents import ReviewPipeline
from agents.memory.store import MemoryStore
import json


@dataclass
class Novel:
    """小说对象"""
    id: int = 0
    title: str = ""
    genre: str = "都市"
    requirement: str = ""
    status: str = "idle"  # idle, planning, writing, reviewing, completed
    
    outline: Dict[str, Any] = field(default_factory=dict)
    characters: List[Dict[str, Any]] = field(default_factory=list)
    world_settings: Dict[str, Any] = field(default_factory=dict)
    foreshadowing: List[Dict[str, Any]] = field(default_factory=list)
    
    chapters: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "genre": self.genre,
            "requirement": self.requirement,
            "status": self.status,
            "outline": self.outline,
            "characters": self.characters,
            "world_settings": self.world_settings,
            "foreshadowing": self.foreshadowing,
            "chapters": self.chapters
        }


class NovelAgentPipeline:
    """完整的小说 Agent 流水线"""
    
    def __init__(self, db_path: str = "novel_agent.db", use_mock: bool = True):
        # 初始化各阶段 Pipeline
        self.planner = PlanningPipeline(use_mock=use_mock)
        self.writer = WritingPipeline(use_mock=use_mock)
        self.reviewer = ReviewPipeline(use_mock=use_mock)
        
        # 初始化存储
        self.store = MemoryStore(db_path)
        
        # 当前小说
        self.current_novel: Optional[Novel] = None
        
        # 配置
        self.use_mock = use_mock
        self.max_retry = 3
    
    def create_novel(self, requirement: str, genre: str = "都市") -> Novel:
        """创建新小说"""
        novel = Novel(
            requirement=requirement,
            genre=genre,
            status="planning"
        )
        
        # 保存到数据库
        novel.id = self.store.save_novel(novel.to_dict())
        
        self.current_novel = novel
        return novel
    
    def plan(self) -> Dict[str, Any]:
        """执行规划阶段"""
        if not self.current_novel:
            raise ValueError("No novel created")
        
        # 执行规划
        result = self.planner.run(
            self.current_novel.requirement,
            self.current_novel.genre
        )
        
        if "error" in result:
            return result
        
        # 更新小说对象
        self.current_novel.outline = result.get("outline", {})
        self.current_novel.title = result.get("outline", {}).get("title", "未命名")
        
        # 处理characters - 可能是list或dict
        chars = result.get("characters", [])
        if isinstance(chars, dict):
            # 如果返回的是整个outline，创建默认角色
            chars = [
                {"name": "主角", "role": "主角", "psychology": {}, "behavior": {}, "relationships": []}
            ]
        self.current_novel.characters = chars
        
        # 确保world_settings是dict
        ws = result.get("world_settings", {})
        self.current_novel.world_settings = ws if isinstance(ws, dict) else {}
        
        # 确保foreshadowing是列表
        fs = result.get("foreshadowing", [])
        self.current_novel.foreshadowing = fs if isinstance(fs, list) else []
        
        # 保存到数据库
        self.store.save_novel(self.current_novel.to_dict())
        
        # 保存角色
        for char in self.current_novel.characters:
            if isinstance(char, dict):
                self.store.save_character(self.current_novel.id, char)
        
        # 保存卷结构
        volumes = result.get("volumes", [])
        if volumes:
            self.store.save_volumes(self.current_novel.id, volumes)
        
        self.current_novel.status = "planned"
        
        return {
            "status": "success",
            "title": self.current_novel.title,
            "outline": self.current_novel.outline,
            "volumes": volumes,
            "overall_rhythm": result.get("overall_rhythm", {}),
            "characters": self.current_novel.characters,
            "world_settings": self.current_novel.world_settings,
            "foreshadowing": self.current_novel.foreshadowing
        }
    
    def write_chapter(self, chapter_num: int) -> Dict[str, Any]:
        """写单个章节"""
        if not self.current_novel:
            raise ValueError("No novel created")
        
        # 获取章节信息
        chapters = self.current_novel.outline.get("chapters", [])
        chapter_info = None
        for ch in chapters:
            if ch.get("num") == chapter_num:
                chapter_info = ch
                break
        
        if not chapter_info:
            return {"error": f"Chapter {chapter_num} not found in outline"}
        
        # 准备上下文
        context = AgentContext(
            outline=self.current_novel.outline,
            characters=self.current_novel.characters,
            world_settings=self.current_novel.world_settings,
            foreshadowing=self.current_novel.foreshadowing,
            current_chapter=chapter_num,
            previous_content=self._get_previous_content(chapter_num)
        )
        
        # 写作
        result = self.writer.write_chapter(chapter_info, context)
        
        if not result.success:
            return {"error": result.error}
        
        content = result.data.get("content", "")
        
        # 审核
        review_result = self.reviewer.full_review(content, context)
        
        chapter_data = {
            "chapter_num": chapter_num,
            "content": content,
            "word_count": result.data.get("word_count", 0),
            "review": review_result,
            "status": "published" if review_result["approved"] else "draft"
        }
        
        # 保存章节
        self.store.save_chapter(
            self.current_novel.id,
            chapter_num,
            content
        )
        
        # 更新内存
        self.current_novel.chapters.append(chapter_data)
        
        return chapter_data
    
    def write_all_chapters(self) -> List[Dict[str, Any]]:
        """写所有章节"""
        if not self.current_novel:
            raise ValueError("No novel created")
        
        chapters = self.current_novel.outline.get("chapters", [])
        results = []
        
        for ch in chapters:
            chapter_num = ch.get("num")
            print(f"Writing chapter {chapter_num}...")
            
            result = self.write_chapter(chapter_num)
            results.append(result)
            
            # 打印进度
            if result.get("error"):
                print(f"  Error: {result['error']}")
            else:
                print(f"  Done! Status: {result.get('status')}")
        
        self.current_novel.status = "completed"
        
        return results
    
    def _get_previous_content(self, chapter_num: int) -> str:
        """获取前文内容摘要"""
        if not self.current_novel.chapters:
            return ""
        
        # 取前3章的内容摘要
        previous = []
        for ch in self.current_novel.chapters[-3:]:
            content = ch.get("content", "")
            # 取最后500字
            if len(content) > 500:
                previous.append(content[-500:])
            else:
                previous.append(content)
        
        return "\n".join(previous)
    
    def get_novel(self, novel_id: int) -> Novel:
        """获取小说"""
        data = self.store.get_novel(novel_id)
        if not data:
            raise ValueError(f"Novel {novel_id} not found")
        
        novel = Novel(
            id=data["id"],
            title=data.get("title", ""),
            genre=data.get("genre", "都市"),
            status=data.get("status", "idle")
        )
        novel.outline = data.get("outline", {})
        novel.characters = self.store.get_characters(novel_id)
        
        return novel
    
    def run(self, requirement: str, genre: str = "都市") -> Dict[str, Any]:
        """运行完整流程"""
        
        # 1. 创建小说
        print("1. Creating novel...")
        novel = self.create_novel(requirement, genre)
        print(f"   Novel created: {novel.id}")
        
        # 2. 规划阶段
        print("2. Planning...")
        plan_result = self.plan()
        if "error" in plan_result:
            return plan_result
        print(f"   Title: {plan_result['title']}")
        
        # 3. 写作阶段
        print("3. Writing chapters...")
        write_results = self.write_all_chapters()
        
        # 4. 返回结果
        return {
            "status": "completed",
            "novel_id": self.current_novel.id,
            "title": self.current_novel.title,
            "chapters": len(write_results),
            "chapters_detail": write_results
        }


# 测试
if __name__ == "__main__":
    pipeline = NovelAgentPipeline(use_mock=True)
    
    result = pipeline.run(
        requirement="写一个100万字的都市修仙小说，主角从修为尽失到成为武帝",
        genre="都市修仙"
    )
    
    print("\n=== Result ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
