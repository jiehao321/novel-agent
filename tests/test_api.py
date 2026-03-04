"""
Novel Agent 单元测试
覆盖所有 API 端点
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入前重置模块
import importlib
if 'backend.main' in sys.modules:
    del sys.modules['backend.main']

from backend.main import app

# 每次创建新的TestClient
def get_client():
    return TestClient(app)


class TestHealthEndpoint:
    """健康检查端点测试"""
    
    def test_root(self):
        """测试根路径"""
        client = get_client()
        response = client.get("/")
        assert response.status_code == 200
        assert "Novel Agent API" in response.json()["message"]
    
    def test_health(self):
        """测试健康检查"""
        client = get_client()
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestNovelEndpoints:
    """小说相关端点测试"""
    
    def test_create_novel(self):
        """测试创建小说"""
        client = get_client()
        response = client.post(
            "/api/novel/create",
            json={
                "requirement": "写一个3章的都市修仙小说",
                "genre": "都市修仙",
                "use_mock": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "novel_id" in data
        assert data["status"] == "created"
    
    def test_get_novel(self):
        """测试获取小说信息"""
        client = get_client()
        # 先创建
        create_resp = client.post(
            "/api/novel/create",
            json={"requirement": "测试小说", "genre": "都市", "use_mock": True}
        )
        novel_id = create_resp.json()["novel_id"]
        
        # 获取
        response = client.get(f"/api/novel/{novel_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == novel_id
    
    def test_get_novel_not_found(self):
        """测试获取不存在的小说"""
        client = get_client()
        response = client.get("/api/novel/99999")
        assert response.status_code == 404


class TestPlanEndpoints:
    """规划相关端点测试"""
    
    def test_plan_novel(self):
        """测试生成大纲"""
        client = get_client()
        # 创建小说
        create_resp = client.post(
            "/api/novel/create",
            json={"requirement": "测试小说", "genre": "都市", "use_mock": True}
        )
        novel_id = create_resp.json()["novel_id"]
        
        # 生成大纲
        response = client.post(f"/api/novel/{novel_id}/plan")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "title" in data


class TestChapterEndpoints:
    """章节相关端点测试"""
    
    def test_write_all_chapters(self):
        """测试批量写所有章节"""
        client = get_client()
        # 创建并规划
        create_resp = client.post(
            "/api/novel/create",
            json={"requirement": "测试", "genre": "都市", "use_mock": True}
        )
        novel_id = create_resp.json()["novel_id"]
        client.post(f"/api/novel/{novel_id}/plan")
        
        # 批量写作
        response = client.post(f"/api/novel/{novel_id}/write-all")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"


class TestPipeline:
    """Pipeline 测试"""
    
    def test_planning_pipeline(self):
        """测试规划流程"""
        from agents.pipeline import PlanningPipeline
        
        pipeline = PlanningPipeline(use_mock=True)
        result = pipeline.run("测试需求", "都市")
        
        assert "outline" in result
        assert "characters" in result
    
    def test_writer_pipeline(self):
        """测试写作流程"""
        from agents.writer.agents import WriterAgent
        from agents.base import AgentContext, AgentConfig, AgentType
        
        config = AgentConfig(name='TestWriter', agent_type=AgentType.WRITER)
        agent = WriterAgent(config, use_mock=True)
        
        context = AgentContext(
            outline={'title': '测试', 'chapters': [{'num': 1, 'title': '第一章', 'core_event': 'test'}]},
            characters=[],
            world_settings={},
            foreshadowing=[]
        )
        
        result = agent.run({'num': 1, 'title': '第一章', 'core_event': 'test'}, context)
        assert result.success
    
    def test_reviewer_pipeline(self):
        """测试审核流程"""
        from agents.reviewer.agents import ReviewPipeline
        from agents.base import AgentContext
        
        pipeline = ReviewPipeline(use_mock=True)
        
        content = "这是一段测试内容" * 50  # 确保足够长
        context = AgentContext(
            outline={},
            characters=[],
            world_settings={},
            foreshadowing=[]
        )
        
        result = pipeline.full_review(content, context)
        assert "approved" in result


class TestMemoryStore:
    """记忆存储测试"""
    
    def test_save_and_get_novel(self):
        """测试保存和获取小说"""
        from agents.memory.store import MemoryStore
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        store = MemoryStore(db_path)
        
        novel_data = {
            "title": "测试小说",
            "genre": "都市",
            "outline": {"title": "测试"},
            "status": "planning"
        }
        
        novel_id = store.save_novel(novel_data)
        assert novel_id > 0
        
        retrieved = store.get_novel(novel_id)
        assert retrieved["title"] == "测试小说"
        
        store.close()
        os.unlink(db_path)
    
    def test_save_character(self):
        """测试保存角色"""
        from agents.memory.store import MemoryStore
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        store = MemoryStore(db_path)
        
        novel_id = store.save_novel({
            "title": "测试",
            "genre": "都市",
            "outline": {},
            "status": "planning"
        })
        
        character = {
            "name": "张三",
            "role": "主角",
            "psychology": {"core_motivation": "成为强者"},
            "behavior": {"decision_pattern": "理性"},
            "relationships": []
        }
        
        store.save_character(novel_id, character)
        
        characters = store.get_characters(novel_id)
        assert len(characters) > 0
        
        store.close()
        os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
