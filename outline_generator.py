"""
LLM 大纲生成器 —— 把一句话主题变成可被 PPTGenerator 渲染的结构化 outline。

设计目标
========
你给一句"帮我做一个关于 RAG 在企业知识库落地的 15 分钟分享"这种粗略需求，
模块就生成结构化的 outline JSON：

    {
      "title": "RAG 在企业知识库落地实践",
      "subtitle": "从原型到生产的 15 分钟分享",
      "slides": [
        {"type": "title", "title": "...", "subtitle": "..."},
        {"type": "section", "title": "..."},
        {"type": "content", "title": "...", "bullets": ["...", "..."]},
        {"type": "comparison", "title": "...", "left": {...}, "right": {...}},
        {"type": "chart", "title": "...", "chart_type": "bar", "data": {...}},
        ...
      ]
    }

直接喂给 ``PPTGenerator`` 即可输出 .pptx。

LLM 适配
========
支持 openai / anthropic / deepseek 三个 backend，行为与
Multi-Agent-Trading-Simulator 的 LLMClient 保持一致：缺 key 时优雅回退到
规则版（从主题里抽 3-5 个常见小节，生成静态大纲）。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional


SYSTEM_PROMPT = """你是一名资深的演讲策划顾问。任务：把用户给的一句话主题，
扩展为一份结构化的 PPT 大纲。

设计原则：
1. 标题页 + 章节切换页 + 内容页交替，避免连续 5 页以上同类型
2. 每个内容页 bullet 不超过 5 条，每条不超过 25 字
3. 适合插数据图的地方明确写 "type": "chart" 并给出 chart_type + data
4. 在主题需要对比时（如方案 A vs B）用 "type": "comparison"
5. 结尾必有 1 页总结 + 1 页"谢谢/Q&A"

输出格式（严格 JSON，键名固定）：
{
  "title": "...",
  "subtitle": "...",
  "duration_minutes": 15,
  "target_audience": "...",
  "slides": [
    {"type": "title", "title": "...", "subtitle": "..."},
    {"type": "section", "title": "..."},
    {"type": "content", "title": "...", "bullets": ["...", "..."]},
    {"type": "comparison", "title": "...",
     "left": {"label": "...", "bullets": [...]},
     "right": {"label": "...", "bullets": [...]}},
    {"type": "chart", "title": "...", "chart_type": "bar|line|pie",
     "data": {"categories": [...], "values": [...]}},
    {"type": "summary", "title": "...", "bullets": [...]},
    {"type": "thanks", "title": "Q&A"}
  ]
}

只输出 JSON，不要前后缀文字。"""


LLMBackend = Literal["openai", "anthropic", "deepseek"]


@dataclass
class OutlineSlide:
    """单页幻灯片的结构化描述。"""

    type: str
    title: str = ""
    subtitle: str = ""
    bullets: List[str] = None
    left: Optional[Dict] = None
    right: Optional[Dict] = None
    chart_type: Optional[str] = None
    data: Optional[Dict] = None

    def __post_init__(self):
        if self.bullets is None:
            self.bullets = []

    def to_dict(self) -> dict:
        out = {"type": self.type, "title": self.title}
        if self.subtitle:
            out["subtitle"] = self.subtitle
        if self.bullets:
            out["bullets"] = self.bullets
        if self.left:
            out["left"] = self.left
        if self.right:
            out["right"] = self.right
        if self.chart_type:
            out["chart_type"] = self.chart_type
        if self.data:
            out["data"] = self.data
        return out


@dataclass
class Outline:
    title: str
    subtitle: str
    slides: List[OutlineSlide]
    duration_minutes: int = 15
    target_audience: str = ""
    used_fallback: bool = False

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "duration_minutes": self.duration_minutes,
            "target_audience": self.target_audience,
            "slides": [s.to_dict() for s in self.slides],
            "used_fallback": self.used_fallback,
        }


class LLMClient:
    """openai / anthropic / deepseek 统一调用接口。"""

    def __init__(
        self,
        backend: LLMBackend = "deepseek",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.backend = backend
        self.timeout = timeout
        self.api_key = api_key or self._default_key(backend)
        self.base_url = base_url or self._default_base_url(backend)
        self.model = model or self._default_model(backend)

    @staticmethod
    def _default_key(backend: LLMBackend) -> Optional[str]:
        return {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "deepseek": os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"),
        }.get(backend)

    @staticmethod
    def _default_base_url(backend: LLMBackend) -> Optional[str]:
        return {
            "deepseek": "https://api.deepseek.com/v1",
        }.get(backend)

    @staticmethod
    def _default_model(backend: LLMBackend) -> str:
        return {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-haiku-20241022",
            "deepseek": "deepseek-chat",
        }.get(backend, "gpt-4o-mini")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat(self, system: str, user: str) -> str:
        if not self.is_available():
            raise RuntimeError(f"{self.backend} backend 缺 API key")

        if self.backend == "anthropic":
            return self._call_anthropic(system, user)
        return self._call_openai_compatible(system, user)

    def _call_openai_compatible(self, system: str, user: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError("缺 openai SDK：pip install openai") from e
        client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or ""

    def _call_anthropic(self, system: str, user: str) -> str:
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise RuntimeError("缺 anthropic SDK：pip install anthropic") from e
        client = Anthropic(api_key=self.api_key, timeout=self.timeout)
        resp = client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.5,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text if resp.content else ""


class OutlineGenerator:
    """LLM 大纲生成器，缺 LLM 时回退到规则版静态模板。"""

    def __init__(self, llm_client: Optional[LLMClient] = None,
                 backend: LLMBackend = "deepseek"):
        self.llm_client = llm_client or LLMClient(backend=backend)

    def generate(
        self,
        topic: str,
        duration_minutes: int = 15,
        target_audience: str = "工程师",
    ) -> Outline:
        """主入口：从主题生成 outline。"""
        user_prompt = self._build_user_prompt(topic, duration_minutes, target_audience)

        if not self.llm_client.is_available():
            return self._fallback_outline(topic, duration_minutes, target_audience,
                                          reason="LLM API key 未配置")
        try:
            raw = self.llm_client.chat(SYSTEM_PROMPT, user_prompt)
            return self._parse_outline(raw)
        except Exception as e:
            return self._fallback_outline(topic, duration_minutes, target_audience,
                                          reason=f"LLM 调用失败: {type(e).__name__}: {e}")

    @staticmethod
    def _build_user_prompt(topic, duration, audience) -> str:
        return (
            f"主题：{topic}\n"
            f"时长：{duration} 分钟\n"
            f"目标受众：{audience}\n\n"
            f"按 system 要求输出大纲 JSON。每分钟约 1-2 页，所以"
            f"总页数约 {max(duration, 8)}-{duration * 2} 页。"
        )

    @staticmethod
    def _parse_outline(raw: str) -> Outline:
        data = json.loads(raw)
        slides = [OutlineSlide(**s) for s in data.get("slides", [])]
        return Outline(
            title=data.get("title", ""),
            subtitle=data.get("subtitle", ""),
            slides=slides,
            duration_minutes=int(data.get("duration_minutes", 15)),
            target_audience=data.get("target_audience", ""),
            used_fallback=False,
        )

    @staticmethod
    def _fallback_outline(topic, duration, audience, reason: str) -> Outline:
        """无 LLM 时的静态模板：5 个标准章节。"""
        slides = [
            OutlineSlide(type="title", title=topic, subtitle=f"面向 {audience}"),
            OutlineSlide(type="section", title="背景与问题"),
            OutlineSlide(type="content", title="为什么这事重要",
                         bullets=["现状与痛点", "外部驱动因素",
                                  "本次分享要回答的三个问题"]),
            OutlineSlide(type="section", title="解决方案"),
            OutlineSlide(type="content", title="核心方法",
                         bullets=["关键思路一", "关键思路二", "关键思路三"]),
            OutlineSlide(type="content", title="落地步骤",
                         bullets=["Step 1: 准备", "Step 2: 实施",
                                  "Step 3: 验证", "Step 4: 推广"]),
            OutlineSlide(type="section", title="实践数据"),
            OutlineSlide(type="chart", title="效果对比",
                         chart_type="bar",
                         data={"categories": ["指标 A", "指标 B", "指标 C"],
                               "values": [42, 75, 88]}),
            OutlineSlide(type="section", title="总结"),
            OutlineSlide(type="summary", title="三个 takeaway",
                         bullets=["Takeaway 1", "Takeaway 2", "Takeaway 3"]),
            OutlineSlide(type="thanks", title="Q&A"),
        ]
        return Outline(
            title=topic,
            subtitle=f"[规则版回退] {reason}",
            slides=slides,
            duration_minutes=duration,
            target_audience=audience,
            used_fallback=True,
        )
