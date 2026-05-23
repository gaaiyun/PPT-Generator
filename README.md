# PPT-Generator

一句话主题 → 结构化大纲 → 渲染成 PowerPoint 文件。

底层是 python-pptx，最上层加了 LLM 大纲生成器与 CLI，目标是「30 秒拿到能用的初稿，再人工微调」而不是「点击向导一个个填」。

## 一、它解决什么问题

平时被要求出一份分享 PPT 时，最磨人的不是排版，而是「确定章节结构」：

- 标题 → 背景 → 方案 → 数据 → 总结 这种骨架反复想反复改
- 章节切换页、内容页、对比页要在哪里放，做到一半才意识到结构不平衡
- 数据图要不要插、插在哪、用柱状图还是折线图

本项目把这一步交给 LLM：你给一句话主题 + 时长 + 受众，它生成结构化 outline JSON；再用 python-pptx 渲染成 .pptx。LLM 不可用时（家里断网、企业内网无外联）回退到内置规则模板，仍能给出可用的初稿。

## 二、架构

```
   一句话主题
        │
        ▼
   OutlineGenerator  (LLM 适配层，缺 key 时降级到规则模板)
        │
        ▼
   Outline JSON
   {
     "title": "...",
     "slides": [
       {"type": "title",  ...},
       {"type": "section",...},
       {"type": "content",...},
       {"type": "chart",  ...},
       {"type": "comparison", ...},
       {"type": "summary",...},
       {"type": "thanks", ...}
     ]
   }
        │
        ▼
   PPTGenerator  (python-pptx 渲染层，4 个配色方案)
        │
        ▼
   .pptx 文件
```

LLM 通过统一 ``LLMClient`` 适配三个 backend：

| Backend | 默认模型 | 环境变量 |
|---|---|---|
| openai | gpt-4o-mini | OPENAI_API_KEY |
| anthropic | claude-3-5-haiku-20241022 | ANTHROPIC_API_KEY |
| deepseek | deepseek-chat | DEEPSEEK_API_KEY |

七种幻灯片类型：``title`` / ``section`` / ``content`` / ``comparison`` / ``chart`` / ``summary`` / ``thanks``。

## 三、快速开始

### 安装

```bash
pip install -r requirements.txt
# 用 LLM 时再装对应 SDK（任选其一即可）
pip install openai                 # openai / deepseek 走同一个 SDK
pip install anthropic              # 走 anthropic backend
```

### CLI

```bash
# 1) 只生成 outline JSON（不渲染）
python __main__.py outline "RAG 在企业知识库落地的 15 分钟分享" \
    --duration 15 --audience 工程师 -o outline.json

# 2) 一条龙：outline + 渲染 .pptx
python __main__.py create "Q3 销售数据回顾" \
    --color professional -o q3_review.pptx

# 3) 从已有 outline 渲染（适合人工修过 outline.json 后再渲染）
python __main__.py render outline.json --color dark -o deck.pptx

# 4) 看 LLM backend 配置状态
python __main__.py list-models
```

不传 LLM key 时 CLI 不会失败，自动走规则模板（标题 + 5 个标准章节 + 数据图占位 + Q&A）。

### 库调用

```python
from outline_generator import OutlineGenerator, LLMClient
from ppt_generator import PPTGenerator

# 1) 生成 outline
outline = OutlineGenerator(LLMClient(backend="deepseek")).generate(
    topic="RAG 实践",
    duration_minutes=15,
    target_audience="工程师",
)

# 2) 渲染
gen = PPTGenerator()
gen.set_color_scheme("professional")
for s in outline.slides:
    if s.type == "title":
        gen.add_title_slide(s.title, s.subtitle)
    elif s.type == "content":
        gen.add_content_slide(s.title, s.bullets)
    elif s.type == "section":
        gen.add_section_header(s.title)
    # ... 其它类型见 __main__.py 的 _outline_to_pptx 函数
gen.save("deck.pptx")
```

### Streamlit Dashboard

```bash
streamlit run dashboard.py
```

提供图形化编辑：输入主题 → 看 outline 预览 → 调整 → 导出。

## 四、设计取舍

**为什么 outline → render 分两步？**

中间产物 outline.json 是可编辑的人类可读 JSON。LLM 给的 outline 经常需要小修（少一页对比、章节顺序换一下），分两步让用户能在 outline 层做改动，避免改 .pptx 二进制。

**为什么不让 LLM 直接生成 .pptx？**

- 模型生成大量 XML 容易出格式错误，渲染失败排查困难
- .pptx 是二进制，token 成本极高
- python-pptx 已经能稳定渲染，只把"结构决策"交给 LLM 才是分工合理

**为什么有规则版回退？**

- 企业内网环境无外网访问
- 演示前 5 分钟突然没网
- 用户没配 LLM key 也能跑出"能用"的初稿（虽然不如 LLM 版精致）

## 五、目录结构

```
.
├── __main__.py             CLI（outline / create / render / list-models）
├── outline_generator.py    LLM 大纲生成器 + LLMClient + Outline schema
├── ppt_generator.py        python-pptx 渲染层
├── template_manager.py     模板加载与管理
├── dashboard.py            Streamlit 图形界面
├── templates/              4 个预设配色 + .pptx 模板
├── tests/
│   ├── test_ppt_generator.py
│   ├── test_template_manager.py
│   └── test_outline_generator.py   LLM 适配 + fallback 测试
├── requirements.txt
└── README.md
```

## 六、测试

```bash
pytest tests/
```

OutlineGenerator 测试全部用 ``unittest.mock`` 注入假 LLM client，CI 不需要任何 LLM API key。

## License

MIT
