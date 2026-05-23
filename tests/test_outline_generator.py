"""outline_generator 测试：LLM 适配 + fallback + JSON 解析。

不打真实 LLM；用 monkeypatch + MagicMock。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outline_generator import (
    LLMClient,
    Outline,
    OutlineGenerator,
    OutlineSlide,
)


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------


def test_llm_client_default_backend():
    c = LLMClient()
    assert c.backend == "deepseek"
    assert c.base_url == "https://api.deepseek.com/v1"


def test_llm_client_is_available_via_env(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert LLMClient(backend="deepseek").is_available() is False

    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-x")
    assert LLMClient(backend="deepseek").is_available() is True


def test_llm_client_chat_raises_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="缺 API key"):
        LLMClient(backend="openai").chat("sys", "user")


# ---------------------------------------------------------------------------
# OutlineGenerator fallback path
# ---------------------------------------------------------------------------


def test_fallback_outline_when_llm_unavailable(monkeypatch):
    """LLM 不可用时给出静态 outline，标记 used_fallback=True。"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    gen = OutlineGenerator()
    outline = gen.generate("RAG 在企业落地", duration_minutes=15)

    assert outline.used_fallback is True
    assert outline.title == "RAG 在企业落地"
    assert len(outline.slides) >= 5
    # 第一页必是 title
    assert outline.slides[0].type == "title"
    # 末页必含 thanks 类型
    assert any(s.type == "thanks" for s in outline.slides)


def test_fallback_when_llm_raises():
    """LLM 抛异常时也走 fallback，不 crash。"""
    fake = MagicMock(spec=LLMClient)
    fake.is_available.return_value = True
    fake.chat.side_effect = RuntimeError("net down")

    gen = OutlineGenerator(llm_client=fake)
    outline = gen.generate("AI 工程化", duration_minutes=20)

    assert outline.used_fallback is True
    assert outline.duration_minutes == 20


def test_fallback_when_llm_returns_invalid_json():
    """LLM 返回非法 JSON 时走 fallback。"""
    fake = MagicMock(spec=LLMClient)
    fake.is_available.return_value = True
    fake.chat.return_value = "not valid json"

    gen = OutlineGenerator(llm_client=fake)
    outline = gen.generate("x")
    assert outline.used_fallback is True


# ---------------------------------------------------------------------------
# OutlineGenerator LLM-success path
# ---------------------------------------------------------------------------


def test_parses_llm_response_into_outline():
    """LLM 返回合法 outline JSON 时，正确解析为 Outline 对象。"""
    fake = MagicMock(spec=LLMClient)
    fake.is_available.return_value = True
    fake.chat.return_value = json.dumps({
        "title": "RAG 实践",
        "subtitle": "from prototype to production",
        "duration_minutes": 15,
        "target_audience": "工程师",
        "slides": [
            {"type": "title", "title": "RAG 实践", "subtitle": "..."},
            {"type": "section", "title": "为什么是 RAG"},
            {"type": "content", "title": "三大痛点",
             "bullets": ["幻觉", "知识更新慢", "可解释性差"]},
            {"type": "chart", "title": "效果对比",
             "chart_type": "bar",
             "data": {"categories": ["前", "后"], "values": [62, 88]}},
            {"type": "comparison", "title": "方案对比",
             "left": {"label": "Naive RAG", "bullets": ["简单"]},
             "right": {"label": "GraphRAG", "bullets": ["可解释"]}},
            {"type": "summary", "title": "总结", "bullets": ["建议 1", "建议 2"]},
            {"type": "thanks", "title": "Q&A"},
        ],
    })

    gen = OutlineGenerator(llm_client=fake)
    outline = gen.generate("RAG 实践")

    assert outline.used_fallback is False
    assert outline.title == "RAG 实践"
    assert len(outline.slides) == 7
    assert outline.slides[3].type == "chart"
    assert outline.slides[3].data["values"] == [62, 88]
    assert outline.slides[4].type == "comparison"
    assert outline.slides[4].left["label"] == "Naive RAG"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def test_outline_slide_to_dict_omits_empty_fields():
    s = OutlineSlide(type="content", title="x", bullets=["a", "b"])
    d = s.to_dict()
    assert "title" in d
    assert "bullets" in d
    # 没传 subtitle / left / right / chart_type / data 不应出现
    assert "subtitle" not in d
    assert "left" not in d
    assert "chart_type" not in d


def test_outline_to_dict_includes_used_fallback_flag():
    outline = OutlineGenerator()._fallback_outline(
        "x", 15, "工程师", reason="test"
    )
    d = outline.to_dict()
    assert d["used_fallback"] is True
    assert d["duration_minutes"] == 15
