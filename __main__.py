"""PPT-Generator CLI。

子命令：
    outline <主题>            生成 outline JSON（不渲染 .pptx）
    create <主题>             outline → 渲染 → .pptx 一条龙
    render <outline.json>     从已有 outline JSON 渲染 .pptx
    list-models               列支持的 LLM backend

示例：

    python -m ppt_gen outline "RAG 在企业落地的 15 分钟分享" -o outline.json
    python -m ppt_gen create "Q3 销售数据回顾" --color professional -o q3_review.pptx
    python -m ppt_gen render outline.json -o deck.pptx --color dark
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from outline_generator import LLMClient, Outline, OutlineGenerator, OutlineSlide


def _outline_to_pptx(outline: Outline, output_path: str, color_scheme: str = "professional") -> str:
    """把 Outline 对象渲染成 .pptx 文件。"""
    import pandas as pd
    from ppt_generator import PPTGenerator

    gen = PPTGenerator()
    gen.set_color_scheme(color_scheme)

    for s in outline.slides:
        if s.type == "title":
            gen.add_title_slide(title=s.title or outline.title,
                                subtitle=s.subtitle or outline.subtitle)
        elif s.type == "section":
            gen.add_section_header(s.title)
        elif s.type == "content":
            gen.add_content_slide(s.title, s.bullets or [])
        elif s.type == "comparison":
            # python-pptx 没有原生 comparison layout，用两栏并列文本近似
            left = s.left or {}
            right = s.right or {}
            combined = []
            if left.get("label"):
                combined.append(f"【{left['label']}】")
            combined.extend(left.get("bullets", []))
            if right.get("label"):
                combined.append(f"【{right['label']}】")
            combined.extend(right.get("bullets", []))
            gen.add_content_slide(s.title, combined)
        elif s.type == "chart":
            # ppt_generator.add_chart_slide 要 pd.DataFrame；
            # outline 给的是 {categories: [...], values: [...]}，转一次
            data = s.data or {}
            categories = data.get("categories", [])
            values = data.get("values", [])
            if categories and values and len(categories) == len(values):
                df = pd.DataFrame({"category": categories, "value": values})
                try:
                    gen.add_chart_slide(s.title, s.chart_type or "bar",
                                        df, "category", ["value"])
                except (ValueError, Exception):
                    # 渲染失败就降级到 content slide
                    bullets = [f"{c}: {v}" for c, v in zip(categories, values)]
                    gen.add_content_slide(s.title, bullets)
            else:
                gen.add_content_slide(s.title, s.bullets or ["（图表数据缺失）"])
        elif s.type == "summary":
            gen.add_content_slide(s.title, s.bullets or [])
        elif s.type == "thanks":
            gen.add_section_header(s.title or "Q&A")
        else:
            # 未知 type 走 content fallback
            gen.add_content_slide(s.title, s.bullets or [])

    gen.save(output_path)
    return output_path


# ---------------------------------------------------------------------------
# 子命令
# ---------------------------------------------------------------------------


def cmd_outline(args) -> int:
    gen = OutlineGenerator(LLMClient(backend=args.backend))
    outline = gen.generate(
        topic=args.topic,
        duration_minutes=args.duration,
        target_audience=args.audience,
    )
    out_text = json.dumps(outline.to_dict(), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(out_text, encoding="utf-8")
        sys.stderr.write(f"[ok] outline 已写入 {args.output} "
                         f"({len(outline.slides)} 页, fallback={outline.used_fallback})\n")
    else:
        print(out_text)
    return 0


def cmd_create(args) -> int:
    """outline → render 一条龙。"""
    gen = OutlineGenerator(LLMClient(backend=args.backend))
    outline = gen.generate(
        topic=args.topic,
        duration_minutes=args.duration,
        target_audience=args.audience,
    )

    output_path = args.output or "presentation.pptx"
    _outline_to_pptx(outline, output_path, color_scheme=args.color)

    summary = {
        "topic": args.topic,
        "outline_used_fallback": outline.used_fallback,
        "n_slides": len(outline.slides),
        "color_scheme": args.color,
        "output_pptx": str(Path(output_path).resolve()),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def cmd_render(args) -> int:
    """从已有 outline.json 渲染。"""
    src = Path(args.json_file)
    if not src.exists():
        sys.stderr.write(f"[error] 找不到 {src}\n")
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))

    slides = [OutlineSlide(**s) for s in data.get("slides", [])]
    outline = Outline(
        title=data.get("title", ""),
        subtitle=data.get("subtitle", ""),
        slides=slides,
        duration_minutes=int(data.get("duration_minutes", 15)),
        target_audience=data.get("target_audience", ""),
    )

    output_path = args.output or "presentation.pptx"
    _outline_to_pptx(outline, output_path, color_scheme=args.color)
    print(f"[ok] rendered {output_path}")
    return 0


def cmd_list_models(args) -> int:
    import os as _os
    rows = [
        ("openai",    "gpt-4o-mini",                "OPENAI_API_KEY"),
        ("anthropic", "claude-3-5-haiku-20241022",  "ANTHROPIC_API_KEY"),
        ("deepseek",  "deepseek-chat",              "DEEPSEEK_API_KEY"),
    ]
    print(f"{'backend':<12} {'default model':<32} {'env var'}")
    print("-" * 70)
    for backend, model, env in rows:
        configured = "yes" if _os.getenv(env) else "no"
        print(f"{backend:<12} {model:<32} {env}  (configured: {configured})")
    return 0


# ---------------------------------------------------------------------------
# argparse
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ppt_gen", description="PPT-Generator CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    common_color = ["professional", "vibrant", "minimal", "dark"]

    sp = sub.add_parser("outline", help="生成 outline JSON（不渲染 .pptx）")
    sp.add_argument("topic", help="一句话主题")
    sp.add_argument("--duration", type=int, default=15, help="分享时长（分钟）")
    sp.add_argument("--audience", default="工程师", help="目标受众")
    sp.add_argument("--backend", default="deepseek",
                    choices=["openai", "anthropic", "deepseek"])
    sp.add_argument("-o", "--output", help="输出 JSON 文件；缺省 stdout")
    sp.set_defaults(func=cmd_outline)

    sp = sub.add_parser("create", help="outline + 渲染 .pptx 一条龙")
    sp.add_argument("topic")
    sp.add_argument("--duration", type=int, default=15)
    sp.add_argument("--audience", default="工程师")
    sp.add_argument("--backend", default="deepseek",
                    choices=["openai", "anthropic", "deepseek"])
    sp.add_argument("--color", default="professional", choices=common_color)
    sp.add_argument("-o", "--output", help=".pptx 文件路径")
    sp.set_defaults(func=cmd_create)

    sp = sub.add_parser("render", help="从已有 outline.json 渲染 .pptx")
    sp.add_argument("json_file", help="outline JSON 路径")
    sp.add_argument("--color", default="professional", choices=common_color)
    sp.add_argument("-o", "--output", help=".pptx 文件路径")
    sp.set_defaults(func=cmd_render)

    sp = sub.add_parser("list-models")
    sp.set_defaults(func=cmd_list_models)

    return p


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
