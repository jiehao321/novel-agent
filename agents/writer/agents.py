"""
写作阶段 Agent 实现
"""
from typing import Dict, Any, List
from agents.base import BaseAgent, AgentConfig, AgentType, AgentResponse, AgentContext, count_words
from agents.llm_client import LLMClient, MockLLMClient
from agents.prompts import CHAPTER_PROMPT, SCENE_PROMPT, DIALOGUE_PROMPT
from agents.prompts import format_characters_for_prompt, format_outline_for_prompt


class WriterAgent(BaseAgent):
    """写手 Agent - 核心写作能力"""
    
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
        self.min_words = 3000
        self.max_words = 5000
    
    def run(self, chapter_info: Dict[str, Any], context: AgentContext) -> AgentResponse:
        """写章节"""
        try:
            # 准备章节信息
            chapter_num = chapter_info.get("num", 1)
            chapter_title = chapter_info.get("title", f"第{chapter_num}章")
            core_event = chapter_info.get("core_event", "")
            
            # 准备伏笔信息
            foreshadowing_to_plant = self._get_foreshadowing_to_plant(
                chapter_num, context.foreshadowing
            )
            
            # 准备角色信息
            characters_str = format_characters_for_prompt(context.characters)
            outline_str = format_outline_for_prompt(context.outline)
            
            prompt = CHAPTER_PROMPT.format(
                outline=outline_str,
                characters=characters_str,
                world_settings=context.world_settings,
                previous_content=context.previous_content,
                chapter_num=chapter_num,
                chapter_title=chapter_title,
                core_event=core_event,
                foreshadowing_to_plant=foreshadowing_to_plant,
                min_words=self.min_words,
                max_words=self.max_words,
                style="严谨"
            )
            
            # 调用 LLM
            content = self.llm.chat(prompt)
            
            # 检查字数（字符数）
            word_count = len(content)
            if word_count < 200:  # 放宽到200字符
                return AgentResponse(
                    success=False,
                    error=f"字数不足: {word_count}/200"
                )
            
            return AgentResponse(
                success=True,
                data={
                    "content": content,
                    "word_count": word_count,
                    "chapter_num": chapter_num
                },
                metadata={"agent": self.name}
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _get_foreshadowing_to_plant(self, chapter_num: int, foreshadowing: List[Dict]) -> str:
        """获取本章需要埋设的伏笔"""
        to_plant = []
        for fs in foreshadowing:
            if fs.get("plant_chapter") == chapter_num:
                to_plant.append(fs.get("description", ""))
        return ", ".join(to_plant) if to_plant else "无"


class SceneAgent(BaseAgent):
    """场景生成 Agent"""
    
    def __init__(self, config: AgentConfig, use_mock: bool = False):
        super().__init__(config)
        if use_mock:
            self.llm = MockLLMClient()
        else:
            self.llm = LLMClient(
                provider="openai",
                model=config.model,
                temperature=config.temperature,
                max_tokens=1000
            )
    
    def run(self, scene_type: str, mood: str, key_elements: List[str] = None) -> AgentResponse:
        """生成场景描写"""
        try:
            prompt = SCENE_PROMPT.format(
                scene_type=scene_type,
                mood=mood,
                key_elements=key_elements or []
            )
            
            content = self.llm.chat(prompt)
            
            return AgentResponse(
                success=True,
                data=content,
                metadata={"agent": self.name}
            )
        except Exception as e:
            return self.handle_error(e)


class DialogueAgent(BaseAgent):
    """对话 Agent"""
    
    def __init__(self, config: AgentConfig, use_mock: bool = False):
        super().__init__(config)
        if use_mock:
            self.llm = MockLLMClient()
        else:
            self.llm = LLMClient(
                provider="openai",
                model=config.model,
                temperature=config.temperature,
                max_tokens=2000
            )
    
    def run(
        self,
        speaker: Dict[str, Any],
        characters: List[Dict[str, Any]],
        scene: str,
        goal: str
    ) -> AgentResponse:
        """写作对话"""
        try:
            personality = speaker.get("psychology", {}).get("core_motivation", "")
            
            prompt = DIALOGUE_PROMPT.format(
                speaker=speaker.get("name", ""),
                personality=personality,
                scene=scene,
                goal=goal
            )
            
            content = self.llm.chat(prompt)
            
            return AgentResponse(
                success=True,
                data=content,
                metadata={"agent": self.name}
            )
        except Exception as e:
            return self.handle_error(e)


class AtmosphereAgent(BaseAgent):
    """氛围营造 Agent"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
    
    def run(self, mood: str, context: str) -> AgentResponse:
        """营造氛围"""
        # 使用规则生成氛围描写
        atmosphere_templates = {
            "紧张": "空气仿佛凝固了，连呼吸都变得困难...",
            "悲伤": "泪水模糊了视线，心中涌起无限的悲凉...",
            "愤怒": "怒火中烧，双拳紧握，指节发白...",
            "温馨": "阳光温暖地洒在脸上，一切都那么美好...",
        }
        
        content = atmosphere_templates.get(mood, "")
        
        return AgentResponse(
            success=True,
            data=content,
            metadata={"agent": self.name}
        )


class WritingPipeline:
    """写作阶段流水线"""
    
    def __init__(self, use_mock: bool = True):
        self.writer_agent = WriterAgent(
            AgentConfig(
                name="WriterAgent",
                agent_type=AgentType.WRITER,
                temperature=0.8
            ),
            use_mock=use_mock
        )
        self.scene_agent = SceneAgent(
            AgentConfig(name="SceneAgent", agent_type=AgentType.WRITER),
            use_mock=use_mock
        )
        self.dialogue_agent = DialogueAgent(
            AgentConfig(name="DialogueAgent", agent_type=AgentType.WRITER),
            use_mock=use_mock
        )
        self.atmosphere_agent = AtmosphereAgent(
            AgentConfig(name="AtmosphereAgent", agent_type=AgentType.WRITER)
        )
    
    def write_chapter(
        self,
        chapter_info: Dict[str, Any],
        context: AgentContext
    ) -> AgentResponse:
        """写章节"""
        return self.writer_agent.run(chapter_info, context)
    
    def write_chapters_batch(
        self,
        chapters: List[Dict[str, Any]],
        context: AgentContext
    ) -> List[Dict[str, Any]]:
        """批量写章节"""
        results = []
        
        for chapter in chapters:
            # 更新前文内容
            if results:
                context.previous_content = results[-1].get("content", "")[-500:]
            
            result = self.write_chapter(chapter, context)
            
            if result.success:
                results.append({
                    "chapter_num": chapter.get("num"),
                    "content": result.data.get("content", ""),
                    "word_count": result.data.get("word_count", 0)
                })
            else:
                results.append({
                    "chapter_num": chapter.get("num"),
                    "error": result.error
                })
        
        return results
