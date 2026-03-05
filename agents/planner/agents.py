"""
规划阶段 Agent 实现
"""
from typing import Dict, Any, List
from agents.base import BaseAgent, AgentConfig, AgentType, AgentResponse, AgentContext
from agents.llm_client import LLMClient, MockLLMClient
from agents.prompts import (
    OUTLINE_PROMPT,
    VOLUME_PROMPT,
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


class VolumeDesignAgent(BaseAgent):
    """卷结构设计 Agent"""
    
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
    
    def run(self, requirement: str, outline: Dict[str, Any], context: AgentContext) -> AgentResponse:
        """设计卷结构"""
        try:
            import json
            total_chapters = outline.get("total_chapters", 100)
            
            # 根据章节数计算合适的卷数（每卷30-50章）
            total_volumes = max(2, min(10, total_chapters // 40))
            target_chapters_per_volume = total_chapters // total_volumes
            
            prompt = VOLUME_PROMPT.format(
                requirement=requirement,
                outline=json.dumps(outline, ensure_ascii=False),
                total_chapters=total_chapters,
                total_volumes=total_volumes,
                target_chapters_per_volume=target_chapters_per_volume
            )
            
            result = self.llm.chat_with_json(prompt)
            
            # 如果返回的不是列表，包装成列表
            if not isinstance(result, list):
                result = [result]
            
            return AgentResponse(
                success=True,
                data=result,
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
        self.volume_agent = VolumeDesignAgent(
            AgentConfig(name="VolumeAgent", agent_type=AgentType.PLANNER),
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
        
        # 2. 设计卷结构
        volume_result = self.volume_agent.run(requirement, outline, context)
        volumes = volume_result.data if volume_result.success else []
        
        # 3. 设计角色
        character_result = self.character_agent.run(outline, context)
        characters = character_result.data if character_result.success else []
        
        # 4. 构建世界观
        world_result = self.world_agent.run(genre, outline, context)
        world_settings = world_result.data if world_result.success else {}
        
        # 5. 规划伏笔
        fs_result = self.foreshadowing_agent.run(outline, context)
        foreshadowing = fs_result.data if fs_result.success else []
        
        # 计算整体节奏曲线
        overall_rhythm = self._calculate_overall_rhythm(volumes, outline.get("total_chapters", 100))
        
        return {
            "outline": outline,
            "volumes": volumes,
            "characters": characters,
            "world_settings": world_settings,
            "foreshadowing": foreshadowing,
            "overall_rhythm": overall_rhythm,
            "status": "planning_completed"
        }
    
    def _calculate_overall_rhythm(self, volumes: List[Dict], total_chapters: int) -> Dict[str, Any]:
        """计算整体节奏曲线"""
        if not volumes:
            return {"points": [], "major_climaxes": []}
        
        # 找出整体高潮点（每3-5卷一个）
        major_climaxes = []
        num_volumes = len(volumes)
        
        # 每3-5卷设置一个整体高潮
        climax_interval = max(3, min(5, num_volumes // 3))
        for i in range(climax_interval - 1, num_volumes, climax_interval):
            if i < len(volumes):
                volume = volumes[i]
                # 计算整体章节位置
                overall_chapter = (volume.get("start_chapter", 0) + volume.get("end_chapter", 0)) // 2
                major_climaxes.append({
                    "volume_num": volume.get("volume_num"),
                    "chapter": overall_chapter,
                    "title": volume.get("title"),
                    "intensity": 10
                })
        
        # 构建整体节奏点
        points = []
        for i, volume in enumerate(volumes):
            volume_progress = (i + 1) / num_volumes * 100
            # 找到卷内高潮点
            rhythm_curve = volume.get("rhythm_curve", {})
            curve_points = rhythm_curve.get("points", [])
            
            for point in curve_points:
                # 将卷内位置转换为整体位置
                volume_start = volume.get("start_chapter", 1)
                volume_end = volume.get("end_chapter", total_chapters)
                volume_size = volume_end - volume_start + 1
                
                overall_position = volume_start + (point.get("position", 0) / 100) * volume_size
                overall_position_percent = (overall_position / total_chapters) * 100
                
                points.append({
                    "chapter": int(overall_position),
                    "position": round(overall_position_percent, 1),
                    "intensity": point.get("intensity", 5),
                    "phase": point.get("phase", ""),
                    "volume_num": volume.get("volume_num")
                })
        
        return {
            "points": points,
            "major_climaxes": major_climaxes,
            "total_volumes": num_volumes,
            "total_chapters": total_chapters
        }
