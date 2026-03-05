"""
Prompt 模板库
"""

# ========== 规划阶段 Prompt ==========

OUTLINE_PROMPT = """你是一个专业的小说大纲设计师。根据用户需求创作一个完整的小说大纲。

## 用户需求
{requirement}

## 要求
1. 主线剧情：完整的故事线，有起承转合
2. 支线剧情：至少3条，与主线呼应
3. 章节规划：{total_chapters}章，每章有核心事件
4. 高潮分布：至少{total_chapters}个高潮点
5. 伏笔系统：至少10个伏笔，有埋设和回收计划
6. 卷结构：将章节分成多卷，每卷30-50章，每卷有独立的主题和冲突

## 输出格式
请返回 JSON 格式的大纲：
```json
{{
    "title": "小说标题",
    "genre": "题材类型",
    "theme": "核心主题",
    "total_chapters": {total_chapters},
    "total_volumes": 3-5卷,
    "main_plot": {{
        "beginning": "开头",
        "development": "发展",
        "climax": "高潮",
        "ending": "结局"
    }},
    "sub_plots": [
        {{"name": "支线1", "description": "描述"}}
    ],
    "chapters": [
        {{"num": 1, "title": "章节标题", "core_event": "核心事件", "volume": 1, "foreshadowing": []}}
    ],
    "climax_points": [1, 20, 50, 80, 100],
    "foreshadowing": [
        {{"id": "fs_1", "description": "伏笔描述", "plant_chapter": 1, "reveal_chapter": 50}}
    ]
}}
```"""

VOLUME_PROMPT = """你是一个专业的小说卷结构规划师。根据大纲设计极度详细的卷结构。

## 大纲信息
{outline}

## 用户需求
{requirement}

## 要求
将{total_chapters}章分成{total_volumes}卷，每卷{target_chapters_per_volume}章左右。

每一卷必须包含以下极度详细的信息：

### 1. 卷基础信息
- 卷名：简洁有力的标题
- 卷简介：200-300字介绍
- 起止章节：卷包含的章节范围
- 卷主题：该卷的核心主题
- 卷核心冲突：该卷的主要矛盾

### 2. 卷核心流程
- 这一卷的核心目标是什么，主角要完成什么（50-100字）

### 3. 剧情走向
- 从开头到结尾的整体变化，详细描述每一阶段（200-400字）

### 4. 章节规划（极度详细）
每卷下的章节要分组，每组10章左右，每组包含：
- 组标题：如"第1-10章：山村平静生活"
- 每章详细规划（必须包含以下5项）：
  - 章节内容概述：150-200字
  - 冲突点：人物矛盾、困难、阻碍（每章至少1个冲突）
  - 爽点：打脸、逆袭、突破、装逼、收获（每章至少1个爽点）
  - 钩子：章节结尾的悬念（每章必须有钩子）
  - 情绪曲线：平缓/紧张/激烈/回落

### 5. 节奏曲线
- 每卷的节奏：铺垫% → 发展% → 高潮% → 回落%

## 输出格式
请返回 JSON 格式的卷结构列表：
```json
[
    {{
        "volume_num": 1,
        "title": "少年崛起",
        "introduction": "卷简介",
        "start_chapter": 1,
        "end_chapter": {target_chapters_per_volume},
        "theme": "逆天改命",
        "core_conflict": "与命运抗争",
        "core_goal": "主角从山村少年成长为门派核心弟子",
        "plot_direction": "山村生活 → 意外发现古玉 → 触发传承 → 加入门派 → 修炼入门 → 门派大比 → 一鸣惊人 → 获得秘境资格",
        "chapter_groups": [
            {{
                "title": "第1-10章：山村平静生活",
                "chapters": [
                    {{
                        "chapter_num": 1,
                        "title": "陨落的天才",
                        "summary": "章节内容概述150-200字...",
                        "conflict": "主角修为尽失，被族人嘲笑",
                        "爽点": "主角意外激活古玉，展现天赋",
                        "hook": "古玉显示唯有离开此地才能解开身世之谜",
                        "emotion_curve": "平缓→紧张→激烈"
                    }},
                    {{
                        "chapter_num": 2,
                        "title": "神秘的传承",
                        "summary": "章节内容概述...",
                        "conflict": "村长儿子要抢古玉",
                        "爽点": "主角意外激活古玉，获得传承",
                        "hook": "古玉中传来神秘声音",
                        "emotion_curve": "紧张→激烈→回落"
                    }}
                ]
            }},
            {{
                "title": "第11-20章：身世之谜",
                "chapters": []
            }}
        ],
        "rhythm_curve": {{
            "type": "standard",
            "preparation": 80,
            "development": 0,
            "climax": 20,
            "falling": 0,
            "points": [
                {{"position": 0, "intensity": 3, "phase": "铺垫"}},
                {{"position": 25, "intensity": 5, "phase": "铺垫"}},
                {{"position": 50, "intensity": 7, "phase": "铺垫"}},
                {{"position": 75, "intensity": 8, "phase": "发展"}},
                {{"position": 90, "intensity": 10, "phase": "高潮"}},
                {{"position": 100, "intensity": 6, "phase": "回落"}}
            ]
        }},
        "character_appearances": [
            {{"name": "林星河", "status": "出场", "description": "主角"}}
        ]
    }}
]
```"""

CHARACTER_PROMPT = """你是一个专业的小说角色设计师。根据大纲创作完整的角色档案。

## 大纲
{outline}

## 要求
为每个重要角色创建详细档案，包含：
1. 基础信息：姓名、年龄、性别、外貌
2. 心理档案：核心动机、内心恐惧、潜在欲望、心理防线
3. 行为档案：决策模式、解决问题方式、人际互动风格
4. 关系网络：与其他角色的关系
5. 角色弧线：成长变化

## 输出格式
JSON 格式的角色列表：
```json
[
    {{
        "name": "角色名",
        "role": "主角/配角/反派",
        "basic_info": {{"age": 20, "gender": "男", "appearance": "外貌描述"}},
        "psychology": {{
            "core_motivation": "核心动机",
            "inner_fear": "内心恐惧",
            "hidden_desire": "潜在欲望",
            "psychological_defense": "心理防线"
        }},
        "behavior": {{
            "decision_pattern": "决策模式",
            "problem_solving": "解决问题方式"
        }},
        "relationships": [
            {{"target": "其他角色", "type": "friend/enemy/love", "history": "关系历史"}}
        ]
    }}
]
```"""

WORLD_BUILDING_PROMPT = """你是一个专业的小说世界观架构师。根据题材创建完整的世界观。

## 题材: {genre}
## 大纲: {outline}

## 要求
1. 规则体系：修炼/魔法/科技/社会经济
2. 势力分布：主要势力及其格局
3. 历史设定：起源和发展
4. 地理环境：主要地点
5. 世界观秘密：可以埋设伏笔的秘密

## 输出格式
JSON 格式：
```json
{{
    "rules": {{
        "power_system": "力量体系",
        "economy": "经济体系",
        "society": "社会结构"
    }},
    "factions": [
        {{"name": "势力名", "description": "描述", "goals": ["目标"]}}
    ],
    "history": "历史背景",
    "geography": {{
        "locations": [
            {{"name": "地名", "description": "描述", "importance": "重要性"}}
        ]
    }},
    "secrets": ["秘密1", "秘密2"]
}}
```"""

# ========== 写作阶段 Prompt ==========

CHAPTER_PROMPT = """你是一个专业的小说作家。根据以下信息创作高质量的小说章节。

## 小说大纲
{outline}

## 角色档案
{characters}

## 世界观
{world_settings}

## 前文摘要
{previous_content}

## 当前章节信息
- 章节号: {chapter_num}
- 章节标题: {chapter_title}
- 核心事件: {core_event}
- 需要埋设的伏笔: {foreshadowing_to_plant}

## 写作要求
1. **画面感第一**：让读者能"看到"画面，用具体细节而非抽象描述
2. **展示而非告知**：通过动作、语言、环境来表达，而非直接陈述
3. **角色一致性**：保持角色性格、行为、语言风格一致
4. **节奏张弛**：有铺垫有高潮，不要平铺直叙
5. **伏笔埋设**：在适当位置埋设伏笔
6. **字数要求**：{min_words}-{max_words}字

## 写作风格
- 语言风格: {style}
- 句式偏好: 长短句结合
- 描写手法: 环境+心理+动作+对话均衡

请直接输出章节内容，不要有其他格式。
"""

SCENE_PROMPT = """你是一个场景描写专家。根据以下信息生成生动的场景描写。

## 场景类型: {scene_type}
## 情绪基调: {mood}
## 关键元素: {key_elements}

## 要求
1. 调动了视觉、听觉、嗅觉、味觉、触觉
2. 与情节氛围一致
3. 有细节有画面感
4. 100-300字

直接输出场景描写内容。
"""

DIALOGUE_PROMPT = """你是一个对话写作专家。根据角色信息创作符合人设的对话。

## 说话角色: {speaker}
## 角色性格: {personality}
## 场景: {scene}
## 对话目标: {goal}

## 要求
1. 语言风格符合角色性格
2. 有言外之意（潜台词）
3. 推动情节发展
4. 展示角色关系

请创作对话内容。
"""

# ========== 审核阶段 Prompt ==========

LOGIC_REVIEW_PROMPT = """你是一个小说审核专家。审核章节的逻辑合理性。

## 待审核内容
{content}

## 大纲
{outline}

## 审核要点
1. 剧情是否合理，因果关系是否清晰
2. 角色动机是否充分
3. 情节发展是否突兀

## 输出格式
```json
{{
    "approved": true/false,
    "score": 8.5,
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1"]
}}
```
"""

SENSITIVITY_REVIEW_PROMPT = """你是一个内容审核专家。检查内容是否违规。

## 待审核内容
{content}

## 审核要点
1. 涉黄内容
2. 涉暴内容
3. 政治敏感
4. 封建迷信
5. 其他违规内容

## 输出格式
```json
{{
    "approved": true/false,
    "issues": ["问题1"],
    "severity": "low/medium/high"
}}
```
"""

ORIGINALITY_REVIEW_PROMPT = """你是一个原创性检测专家。检测内容是否存在抄袭/套路化。

## 待审核内容
{content}

## 审核要点
1. 是否存在明显抄袭
2. 是否过度套路化
3. 是否有创新点

## 输出格式
```json
{{
    "approved": true/false,
    "score": 8.0,
    "issues": [],
    "innovations": ["创新点1"]
}}
```
"""

AI_STYLE_REVIEW_PROMPT = """你是一个AI文风检测专家。检测内容是否有AI味。

## 待审核内容
{content}

## 审核要点
1. 句式是否单调重复
2. 是否有流水账问题
3. 情感表达是否缺失
4. 是否有明显的AI生成痕迹

## 输出格式
```json
{{
    "approved": true/false,
    "score": 7.5,
    "issues": ["问题1"],
    "improvements": ["改进建议"]
}}
```
"""

CONSISTENCY_REVIEW_PROMPT = """你是一个一致性审核专家。检测内容是否前后一致。

## 待审核内容
{content}

## 角色信息
{characters}

## 审核要点
1. 角色性格是否一致
2. 角色行为是否合理
3. 时间线是否正确
4. 设定是否统一

## 输出格式
```json
{{
    "approved": true/false,
    "issues": ["问题1"]
}}
```
"""

FORESHADOWING_REVIEW_PROMPT = """你是一个伏笔审核专家。检测伏笔埋设和回收情况。

## 待审核内容
{content}

## 伏笔列表
{foreshadowing}

## 审核要点
1. 伏笔是否自然埋设
2. 是否有呼应
3. 伏笔状态是否正确

## 输出格式
```json
{{
    "approved": true/false,
    "planted": ["fs_1"],
    "issues": []
}}
```
"""

WRITING_QUALITY_PROMPT = """你是一个文笔审核专家。审核章节的写作质量。

## 待审核内容
{content}

## 审核要点
1. 描写质量（环境、心理、动作）
2. 句式变化
3. 情感渲染
4. 文字感染力

## 输出格式
```json
{{
    "approved": true/false,
    "score": 8.0,
    "improvements": ["改进建议"]
}}
```
"""


def format_characters_for_prompt(characters):
    """格式化角色信息用于 prompt"""
    result = []
    for char in characters:
        result.append(f"""
角色: {char.get('name', '未知')}
身份: {char.get('role', '未知')}
性格: {char.get('psychology', {}).get('core_motivation', '待定')}
""")
    return "\n".join(result)


def format_outline_for_prompt(outline):
    """格式化大纲用于 prompt"""
    import json
    return json.dumps(outline, ensure_ascii=False, indent=2)
