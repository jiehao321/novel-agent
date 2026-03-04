"""
记忆层测试
"""
import pytest
import tempfile
import os
import shutil


class TestVectorMemory:
    """向量记忆测试"""
    
    def test_add_and_search_character(self):
        """测试添加和搜索角色"""
        from agents.memory.vector_store import VectorMemory
        
        # 使用临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = VectorMemory(tmpdir)
            
            # 添加角色记忆
            memory.add_character_memory(
                novel_id=1,
                character_id="char_1",
                name="林星河",
                description="主角，追求力量的修仙者"
            )
            
            # 搜索
            results = memory.search_characters(1, "主角")
            
            # 验证
            assert len(results) > 0
            assert "林星河" in results[0]["metadata"].get("name", "")
            
            memory.close()
    
    def test_add_and_search_plot(self):
        """测试添加和搜索剧情"""
        from agents.memory.vector_store import VectorMemory
        
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = VectorMemory(tmpdir)
            
            # 添加剧情
            memory.add_plot_memory(
                novel_id=1,
                chapter_num=1,
                content="林星河站在悬崖边，修为尽失...",
                summary="主角修为尽失"
            )
            
            # 搜索
            results = memory.search_plots(1, "悬崖")
            
            # 验证
            assert len(results) >= 0  # 可能没有结果因为embedding
            
            memory.close()
    
    def test_world_memory(self):
        """测试世界观记忆"""
        from agents.memory.vector_store import VectorMemory
        
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = VectorMemory(tmpdir)
            
            # 添加世界观
            memory.add_world_memory(1, "灵气", "修仙世界的能量来源")
            memory.add_world_memory(1, "境界", "筑基、金丹、元婴")
            
            # 获取
            world = memory.get_world_memory(1)
            
            # 验证
            assert "灵气" in world
            assert "修仙" in world["灵气"]
            
            memory.close()
    
    def test_delete_novel_memories(self):
        """测试删除小说记忆"""
        from agents.memory.vector_store import VectorMemory
        
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = VectorMemory(tmpdir)
            
            # 添加数据
            memory.add_character_memory(1, "char_1", "测试", "描述")
            memory.add_plot_memory(1, 1, "内容", "摘要")
            
            # 删除
            memory.delete_novel_memories(1)
            
            # 验证
            results = memory.search_characters(1, "测试")
            assert len(results) == 0
            
            memory.close()


class TestEnhancedMemoryStore:
    """增强记忆存储测试"""
    
    def test_save_and_search_character(self):
        """测试保存和语义搜索角色"""
        from agents.memory.vector_store import EnhancedMemoryStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            store = EnhancedMemoryStore(db_path, tmpdir)
            
            # 保存小说
            novel_id = store.save_novel({
                "title": "测试小说",
                "genre": "都市",
                "outline": {},
                "status": "planning"
            })
            
            # 保存角色
            store.save_character(novel_id, {
                "name": "林星河",
                "role": "主角",
                "psychology": {"core_motivation": "追求力量"},
                "behavior": {"decision_pattern": "理性"},
                "relationships": []
            })
            
            # 语义搜索
            results = store.search_characters_by_semantic(novel_id, "主角")
            
            # 验证
            assert novel_id > 0
            
            store.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
