"""
规划阶段 Agent 实现
"""
from typing import Dict, Any, List
from agents.base import BaseAgent, AgentConfig, AgentType, AgentResponse, AgentContext
from agents.llm_client import LLMClient, MockLLMClient
from agents.prompts import (
    OUTLINE_PROMPT,
    CHARACTER_PROMPT,
    WORLD_BUILDING_PROMPT
)


class OutlineAgent(BaseAgent):
    """大纲生成 Agent"""
    
    def __init__(self, config: AgentConfig, use_mock: bool = False):
        super().__init__(config)
        if use_mock:
            self.llm = MockLLMClient()
        else:
            self.llm = LLMClient(
                provider="openai",
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
    
    def run(self, requirement: str, context: AgentContext) -> AgentResponse:
        """生成大纲"""
        try:
            total_chapters = context.outline.get("total_chapters", 100)
            prompt = OUTLINE_PROMPT.format(
                requirement=requirement,
                total_chapters=total_chapters
            )
            
            result = self.llm.chat_with_json(prompt)
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            return self.handle_error(e)


class CharacterDesignAgent(BaseAgent):
    """角色设计 Agent"""
    
    def __init__(self, config: AgentConfig, use_mock: bool = False):
        super().__init__(config)
        if use_mock:
            self.llm = MockLLMClient()
        else:
            self.llm = LLMClient(
                provider="openai",
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
    
    def run(self, outline: Dict[str, Any], context: AgentContext) -> AgentResponse:
        """设计角色"""
        try:
            prompt = CHARACTER_PROMPT.format(
                outline=outline
            )
            
            result = self.llm.chat_with_json(prompt)
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            return self.handle_error(e)


class WorldBuildingAgent(BaseAgent):
    """世界观架构 Agent"""
    
    def __init__(self, config: AgentConfig, use_mock: bool = False):
        super().__init__(config)
        if use_mock:
            self.llm = MockLLMClient()
        else:
            self.llm = LLMClient(
                provider="openai",
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
    
    def run(self, genre: str, outline: Dict[str, Any], context: AgentContext) -> AgentResponse:
        """构建世界观"""
        try:
            prompt = WORLD_BUILDING_PROMPT.format(
                genre=genre,
                outline=outline
            )
            
            result = self.llm.chat_with_json(prompt)
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            return self.handle_error(e)


class ForeshadowingAgent(BaseAgent):
    """伏笔规划 Agent"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
    
    def run(self, outline: Dict[str, Any], context: AgentContext) -> AgentResponse:
        """规划伏笔"""
        try:
            foreshadowing = []
            
            # 从大纲中提取潜在的伏笔点
            climax_points = outline.get("climax_points", [])
            chapters = outline.get("chapters", [])
            
            # 为每个高潮点设计伏笔
            for i, climax in enumerate(climax_points):
                if climax > 5:  # 跳过前期章节
                    foreshadowing.append({
                        "id": f"fs_{i+1}",
                        "type": "plot",
                        "description": f"关键伏笔{i+1}",
                        "importance": 8,
                        "plant_chapter": max(1, climax - 20),
                        "reveal_chapter": climax,
                        "status": "pending"
                    })
            
            return AgentResponse(
                success=True,
                data=foreshadowing,
                metadata={"agent": self.name}
            )
        except Exception as e:
            return self.handle_error(e)


class PlanningPipeline:
    """规划阶段流水线"""
    
    def __init__(self, use_mock: bool = False):
        self.outline_agent = OutlineAgent(
            AgentConfig(name="OutlineAgent", agent_type=AgentType.PLANNER),
            use_mock=use_mock
        )
        self.character_agent = CharacterDesignAgent(
            AgentConfig(name="CharacterAgent", agent_type=AgentType.PLANNER),
            use_mock=use_mock
        )
        self.world_agent = WorldBuildingAgent(
            AgentConfig(name="WorldAgent", agent_type=AgentType.PLANNER),
            use_mock=use_mock
        )
        self.foreshadowing_agent = ForeshadowingAgent(
            AgentConfig(name="ForeshadowingAgent", agent_type=AgentType.PLANNER)
        )
    
    def run(self, requirement: str, genre: str = "都市") -> Dict[str, Any]:
        """执行规划流程"""
        
        # 1. 生成大纲
        outline_result = self.outline_agent.run(requirement, AgentContext())
        if not outline_result.success:
            return {"error": outline_result.error}
        
        outline = outline_result.data
        context = AgentContext(outline=outline)
        
        # 2. 设计角色
        character_result = self.character_agent.run(outline, context)
        characters = character_result.data if character_result.success else []
        
        # 3. 构建世界观
        world_result = self.world_agent.run(genre, outline, context)
        world_settings = world_result.data if world_result.success else {}
        
        # 4. 规划伏笔
        fs_result = self.foreshadowing_agent.run(outline, context)
        foreshadowing = fs_result.data if fs_result.success else []
        
        return {
            "outline": outline,
            "characters": characters,
            "world_settings": world_settings,
            "foreshadowing": foreshadowing,
            "status": "planning_completed"
        }
