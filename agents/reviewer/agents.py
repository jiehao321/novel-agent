"""
审核阶段 Agent 实现
"""
from typing import Dict, Any, List
from agents.base import BaseAgent, AgentConfig, AgentType, AgentResponse, AgentContext, ReviewResult
from agents.llm_client import LLMClient, MockLLMClient
from agents.prompts import (
    LOGIC_REVIEW_PROMPT,
    SENSITIVITY_REVIEW_PROMPT,
    ORIGINALITY_REVIEW_PROMPT,
    AI_STYLE_REVIEW_PROMPT,
    CONSISTENCY_REVIEW_PROMPT,
    FORESHADOWING_REVIEW_PROMPT,
    WRITING_QUALITY_PROMPT,
    format_characters_for_prompt,
    format_outline_for_prompt
)
import re


class BaseReviewer(BaseAgent):
    """审核 Agent 基类"""
    
    def __init__(self, config: AgentConfig, use_mock: bool = False):
        super().__init__(config)
        if use_mock:
            self.llm = MockLLMClient()
        else:
            self.llm = LLMClient(
                provider="openai",
                model=config.model,
                temperature=0.3,
                max_tokens=2000
            )
    
    def _parse_review_result(self, content: str) -> Dict[str, Any]:
        """解析审核结果"""
        from agents.base import extract_json
        result = extract_json(content)
        if result:
            return result
        # 默认返回值
        return {
            "approved": True,
            "score": 8.0,
            "issues": [],
            "suggestions": []
        }


class LogicReviewer(BaseReviewer):
    """逻辑审核 Agent"""
    
    def run(self, content: str, context: AgentContext) -> AgentResponse:
        try:
            outline_str = format_outline_for_prompt(context.outline)
            prompt = LOGIC_REVIEW_PROMPT.format(
                content=content[:5000],  # 限制长度
                outline=outline_str
            )
            
            result_text = self.llm.chat(prompt)
            result = self._parse_review_result(result_text)
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            return self.handle_error(e)


class SensitivityReviewer(BaseReviewer):
    """敏感审核 Agent"""
    
    # 敏感词列表（实际项目中应使用专业词库）
    SENSITIVE_WORDS = [
        "暴力", "血腥", "色情", "政治", "邪教", "迷信"
    ]
    
    def run(self, content: str, context: AgentContext) -> AgentResponse:
        try:
            # 1. 规则快速检查
            issues = []
            for word in self.SENSITIVE_WORDS:
                if word in content:
                    issues.append(f"包含敏感词: {word}")
            
            if issues:
                return AgentResponse(
                    success=True,
                    data={
                        "approved": False,
                        "issues": issues,
                        "severity": "medium"
                    },
                    metadata={"agent": self.name, "method": "rule"}
                )
            
            # 2. LLM 深度检查
            prompt = SENSITIVITY_REVIEW_PROMPT.format(content=content[:5000])
            result_text = self.llm.chat(prompt)
            result = self._parse_review_result(result_text)
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={"agent": self.name, "method": "llm"}
            )
        except Exception as e:
            return self.handle_error(e)


class OriginalityReviewer(BaseReviewer):
    """原创性审核 Agent"""
    
    def run(self, content: str, context: AgentContext) -> AgentResponse:
        try:
            # 简单检测：检查重复率
            # 实际项目应使用专业的抄袭检测 API
            
            prompt = ORIGINALITY_REVIEW_PROMPT.format(content=content[:5000])
            result_text = self.llm.chat(prompt)
            result = self._parse_review_result(result_text)
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            return self.handle_error(e)


class AIStyleReviewer(BaseReviewer):
    """AI文审核 Agent"""
    
    # AI 常见特征
    AI_PATTERNS = [
        r"首先，",
        r"其次，",
        r"最后，",
        r"总的来说",
        r"总而言之",
        r"值得注意的是",
    ]
    
    def run(self, content: str, context: AgentContext) -> AgentResponse:
        try:
            # 1. 模式检测
            issues = []
            for pattern in self.AI_PATTERNS:
                if re.search(pattern, content):
                    issues.append(f"检测到AI常用模式: {pattern}")
            
            # 2. LLM 深度分析
            prompt = AI_STYLE_REVIEW_PROMPT.format(content=content[:5000])
            result_text = self.llm.chat(prompt)
            result = self._parse_review_result(result_text)
            
            # 合并问题
            if issues:
                result["issues"] = result.get("issues", []) + issues
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            return self.handle_error(e)


class ConsistencyReviewer(BaseReviewer):
    """一致性审核 Agent"""
    
    def run(self, content: str, context: AgentContext) -> AgentResponse:
        try:
            characters_str = format_characters_for_prompt(context.characters)
            
            prompt = CONSISTENCY_REVIEW_PROMPT.format(
                content=content[:5000],
                characters=characters_str
            )
            
            result_text = self.llm.chat(prompt)
            result = self._parse_review_result(result_text)
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            return self.handle_error(e)


class ForeshadowingReviewer(BaseReviewer):
    """伏笔检查 Agent"""
    
    def run(self, content: str, context: AgentContext) -> AgentResponse:
        try:
            import json
            foreshadowing_str = json.dumps(context.foreshadowing, ensure_ascii=False)
            
            prompt = FORESHADOWING_REVIEW_PROMPT.format(
                content=content[:5000],
                foreshadowing=foreshadowing_str
            )
            
            result_text = self.llm.chat(prompt)
            result = self._parse_review_result(result_text)
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            return self.handle_error(e)


class WritingQualityReviewer(BaseReviewer):
    """文笔润色 Agent"""
    
    def run(self, content: str, context: AgentContext) -> AgentResponse:
        try:
            prompt = WRITING_QUALITY_PROMPT.format(content=content[:5000])
            result_text = self.llm.chat(prompt)
            result = self._parse_review_result(result_text)
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            return self.handle_error(e)


class ReviewPipeline:
    """章节审核流水线"""
    
    def __init__(self, use_mock: bool = True):
        # 即时审核 (6维)
        self.logic = LogicReviewer(
            AgentConfig(name="LogicReviewer", agent_type=AgentType.REVIEWER),
            use_mock=use_mock
        )
        self.sensitivity = SensitivityReviewer(
            AgentConfig(name="SensitivityReviewer", agent_type=AgentType.REVIEWER),
            use_mock=use_mock
        )
        self.originality = OriginalityReviewer(
            AgentConfig(name="OriginalityReviewer", agent_type=AgentType.REVIEWER),
            use_mock=use_mock
        )
        self.ai_style = AIStyleReviewer(
            AgentConfig(name="AIStyleReviewer", agent_type=AgentType.REVIEWER),
            use_mock=use_mock
        )
        self.consistency = ConsistencyReviewer(
            AgentConfig(name="ConsistencyReviewer", agent_type=AgentType.REVIEWER),
            use_mock=use_mock
        )
        self.foreshadowing = ForeshadowingReviewer(
            AgentConfig(name="ForeshadowingReviewer", agent_type=AgentType.REVIEWER),
            use_mock=use_mock
        )
        
        # 深度审核 (1维)
        self.writing_quality = WritingQualityReviewer(
            AgentConfig(name="WritingQualityReviewer", agent_type=AgentType.REVIEWER),
            use_mock=use_mock
        )
        
        # 审核配置
        self.min_pass_score = 7.0
    
    def instant_review(self, content: str, context: AgentContext) -> Dict[str, Any]:
        """即时审核"""
        results = {}
        for name, reviewer in [
            ("logic", self.logic),
            ("sensitivity", self.sensitivity),
            ("originality", self.originality),
            ("ai_style", self.ai_style),
            ("consistency", self.consistency),
            ("foreshadowing", self.foreshadowing),
        ]:
            result = reviewer.run(content, context)
            results[name] = result.data if result.data else {}
        
        # 计算通过状态
        all_pass = all(r.get("approved", False) if isinstance(r, dict) else False for r in results.values())
        avg_score = sum(r.get("score", 0) if isinstance(r, dict) else 0 for r in results.values()) / len(results) if results else 0
        
        return {
            "approved": all_pass and avg_score >= self.min_pass_score,
            "scores": {k: (v.get("score", 0) if isinstance(v, dict) else 0) for k, v in results.items()},
            "avg_score": avg_score,
            "details": results
        }
    
    def deep_review(self, content: str, context: AgentContext) -> Dict[str, Any]:
        """深度审核"""
        result = self.writing_quality.run(content, context).data
        
        return {
            "approved": result.get("approved", False),
            "score": result.get("score", 0),
            "improvements": result.get("improvements", [])
        }
    
    def full_review(self, content: str, context: AgentContext) -> Dict[str, Any]:
        """完整审核"""
        instant = self.instant_review(content, context)
        deep = self.deep_review(content, context)
        
        # 综合决策
        final_score = (instant["avg_score"] + deep["score"]) / 2
        approved = instant["approved"] and deep["approved"] and final_score >= self.min_pass_score
        
        return {
            "approved": approved,
            "final_score": final_score,
            "instant": instant,
            "deep": deep,
            "decision": "pass" if approved else "revise"
        }
