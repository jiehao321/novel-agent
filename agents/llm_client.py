"""
LLM 调用封装
"""
import os
from typing import Dict, Any, Optional


class LLMClient:
    """LLM 客户端"""
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None
    
    def _init_client(self):
        """初始化客户端"""
        try:
            from langchain_openai import ChatOpenAI
            self._client = ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        except ImportError:
            raise ImportError("Please install langchain-openai")
    
    def chat(
        self,
        prompt: str,
        system_prompt: str = "",
        response_format: str = "text"
    ) -> str:
        """发送聊天请求"""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        if not self._client:
            self._init_client()
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        response = self._client.invoke(messages)
        
        if response_format == "json":
            return extract_json(response.content)
        return response.content
    
    def chat_with_json(
        self,
        prompt: str,
        system_prompt: str = ""
    ) -> Dict[str, Any]:
        """发送聊天请求并解析 JSON"""
        result = self.chat(prompt, system_prompt, response_format="json")
        if result is None:
            raise ValueError("Failed to parse JSON from response")
        return result


def extract_json(text: str) -> Optional[Dict]:
    """从文本中提取 JSON"""
    import json
    import re
    try:
        return json.loads(text)
    except:
        pass
    
    pattern = r'```(?:json)?\s*(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except:
            continue
    
    pattern = r'\[[\s\S]*\]'
    matches = re.findall(pattern, text)
    for match in matches:
        try:
            return json.loads(match)
        except:
            continue
    
    return None


# Mock 数据
MOCK_OUTLINE = """{
    "title": "星河武帝",
    "genre": "都市修仙",
    "theme": "逆天改命",
    "main_plot": {
        "beginning": "主角意外获得修仙传承",
        "development": "修炼升级，遇到敌人和伙伴",
        "climax": "与最大反派决战",
        "ending": "成为武帝，超脱世俗"
    },
    "sub_plots": [
        {"name": "爱情线", "description": "与女主角的感情发展"},
        {"name": "友情线", "description": "与伙伴的羁绊"}
    ],
    "chapters": [
        {"num": 1, "title": "陨落的天才", "core_event": "修为尽失", "foreshadowing": []},
        {"num": 2, "title": "神秘的传承", "core_event": "获得玉佩", "foreshadowing": []},
        {"num": 3, "title": "重新修炼", "core_event": "开始修炼", "foreshadowing": []}
    ],
    "climax_points": [1, 2, 3],
    "foreshadowing": [
        {"id": "fs_1", "description": "神秘玉佩", "plant_chapter": 1, "reveal_chapter": 3}
    ]
}"""

MOCK_CHARACTERS = """[
    {"name": "林星河", "role": "主角", "basic_info": {"age": 20, "gender": "男"}, "psychology": {"core_motivation": "找回修为"}, "behavior": {"decision_pattern": "理性"}, "relationships": []},
    {"name": "林清雪", "role": "女主角", "basic_info": {"age": 18, "gender": "女"}, "psychology": {"core_motivation": "帮助林星河"}, "behavior": {"decision_pattern": "感性"}, "relationships": []}
]"""

MOCK_CHAPTER = """第1章 陨落的天才

林星河站在悬崖边，任由冷风吹拂着他的衣袍。

三年前，他是林家最耀眼的天才，年仅十七岁便突破到了筑基期，被誉为百年难遇的奇才。可现在，他的修为尽失，整个人看起来比普通人还要虚弱。

"这就是所谓的天之骄子？"身后传来讥讽的声音。

林星河握紧拳头，指甲深深的刺入掌心。鲜血顺着手掌滴落，但他仿佛感觉不到疼痛。

那些曾经的赞美如今都变成了嘲笑，那些曾经讨好他的人如今都躲得远远的。

"总有一天，我会让你们后悔的。"林星河在心里暗暗发誓。

天空阴沉沉的，仿佛预示着什么事情即将发生。远处的山峰连绵起伏，山顶上覆盖着终年不化的积雪。

猎猎山风吹拂而过，卷起了地上的落叶，也吹动了林星河那件已经破旧不堪的长袍。

三年前的那个夜晚，仿佛噩梦一般挥之不去。当时的林星河，还是林家最年轻的天才，年仅十七岁便已经突破到了筑基期，成为家族百年以来最有可能突破金丹期的存在。

那时的他，意气风发，被誉为林家的希望之星。所有的族人都在议论纷纷，说林家出了一个千年难遇的天才。

可谁能想到，就在那个风雨交加的夜晚，一切都变了。

林星河的父母在外出历练时遭遇意外，双双陨落。而他，也在那场灾难中被人暗算，体内的灵气尽数散去，从此沦为一个废物。

曾经对他阿谀奉承的族人，如今见到他都躲得远远的。那些曾经被他帮助过的人，也纷纷改了面孔，仿佛从未认识过他。

"林星河，你这个废物，还站在这里干什么？还不快去打扫院子！"

身后传来的嘲讽声，让林星河的身体猛地一僵。他缓缓转过身去，看到了几个林家子弟正朝这边走来。

就在这时，天空中突然划过一道流星大小的火光，直接朝他砸来。

"轰！"

一声巨响过后，林星河整个人被埋在了尘土之中。

当他再次睁开眼睛的时候，发现自己躺在一个陌生的山洞里，胸前多了一块泛着青光的玉佩。"""


class MockLLMClient:
    """模拟 LLM 客户端（用于测试）"""
    
    def __init__(self, *args, **kwargs):
        pass
    
    def chat(self, prompt: str, system_prompt: str = "", response_format: str = "text") -> str:
        """返回模拟响应"""
        p = prompt.lower()
        
        # 优先精确匹配
        if "章节" in prompt and "写" in prompt:
            return MOCK_CHAPTER
        if "写第" in prompt:
            return MOCK_CHAPTER
        if "chapter" in p and "write" in p:
            return MOCK_CHAPTER
        
        # 其次按类型
        if "角色" in prompt and "大纲" not in prompt:
            return MOCK_CHARACTERS
        if "character" in p and "design" in p:
            return MOCK_CHARACTERS
        
        # 大纲
        if "大纲" in prompt:
            return MOCK_OUTLINE
        if "outline" in p:
            return MOCK_OUTLINE
        
        # 默认返回章节内容
        return MOCK_CHAPTER
    
    def chat_with_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """返回模拟 JSON 响应"""
        p = prompt.lower()
        
        if "角色" in prompt and "大纲" not in prompt:
            return extract_json(MOCK_CHARACTERS) or []
        
        if "大纲" in prompt or "outline" in p:
            return extract_json(MOCK_OUTLINE) or {}
        
        return {}
