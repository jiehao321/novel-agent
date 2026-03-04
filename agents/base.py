"""
Agent 基类和工具
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import re


class AgentType(Enum):
    """Agent 类型"""
    ORCHESTRATOR = "orchestrator"
    PLANNER = "planner"
    WRITER = "writer"
    REVIEWER = "reviewer"
    MEMORY = "memory"


class ReviewResult(Enum):
    """审核结果"""
    PASS = "pass"
    REVISE = "revise"
    REJECT = "reject"
    MANUAL = "manual"


@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str
    agent_type: AgentType
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout: int = 60
    retry_times: int = 3


@dataclass
class AgentContext:
    """Agent 上下文"""
    novel_id: int = 0
    outline: Dict[str, Any] = field(default_factory=dict)
    characters: List[Dict[str, Any]] = field(default_factory=list)
    world_settings: Dict[str, Any] = field(default_factory=dict)
    foreshadowing: List[Dict[str, Any]] = field(default_factory=list)
    chapters: List[Dict[str, Any]] = field(default_factory=list)
    current_chapter: int = 0
    previous_content: str = ""


@dataclass
class AgentResponse:
    """Agent 响应"""
    success: bool
    data: Any = None
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.agent_type = config.agent_type
    
    @abstractmethod
    def run(self, input_data: Any, context: AgentContext) -> AgentResponse:
        """执行任务"""
        pass
    
    def validate_input(self, input_data: Any) -> bool:
        """验证输入"""
        return True
    
    def handle_error(self, error: Exception) -> AgentResponse:
        """错误处理"""
        return AgentResponse(
            success=False,
            error=str(error)
        )


# 工具函数
def extract_json(text: str) -> Optional[Dict]:
    """从文本中提取 JSON"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except:
        pass
    
    # 尝试从代码块中提取
    pattern = r'```(?:json)?\s*(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except:
            continue
    
    # 尝试找到 JSON 对象
    pattern = r'\{[^{}]*\}'
    matches = re.findall(pattern, text)
    for match in matches:
        try:
            return json.loads(match)
        except:
            continue
    
    return None


def format_characters_for_prompt(characters: List[Dict[str, Any]]) -> str:
    """格式化角色信息用于 prompt"""
    result = []
    for char in characters:
        result.append(f"""
角色: {char.get('name', '未知')}
身份: {char.get('role', '未知')}
性格: {char.get('psychology', {}).get('core_motivation', '待定')}
""")
    return "\n".join(result)


def format_outline_for_prompt(outline: Dict[str, Any]) -> str:
    """格式化大纲用于 prompt"""
    return json.dumps(outline, ensure_ascii=False, indent=2)


def count_words(text: str) -> int:
    """统计字数"""
    # 中文按字符，英文按单词
    chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
    english = len(re.findall(r'[a-zA-Z]+', text))
    return chinese + english


def split_into_scenes(content: str) -> List[str]:
    """将章节内容分割成场景"""
    # 按空行或场景标记分割
    scenes = re.split(r'\n\s*\n', content)
    return [s.strip() for s in scenes if s.strip()]
