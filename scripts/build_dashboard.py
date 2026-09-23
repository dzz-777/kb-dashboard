#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kb-dashboard · 看板渲染脚本

读取 agent 用 ima-mcp 拉取并整理好的结构 JSON，套用 assets/template.html
注入数据，输出一份自包含、可双击打开的 HTML 看板。

用法:
  python3 build_dashboard.py --data <结构.json> [--out <输出.html>] [--template <模板.html>]

输入 JSON 结构 (DATA):
{
  "generated_at": "2026-09-02 15:36",          # 快照时间字符串
  "scope": "main|company|material|all",          # 范围
  "libraries": [                                 # 一个或多个库
    {
      "id": "001a977664004911",
      "name": "戴宗宗的知识库",
      "note": "可选·诚实边界说明",
      "kpis": {"topFolders":9,"totalDocs":172,"methodCards":101,"metaLayer":15,"emptyAreas":3,"express":"薄"},
      "tree": [                                  # 结构树(根的子节点列表)
        {"name":"元层","count":15,"items":["..."]},
        {"name":"方法论中枢","count":101,"children":[{"name":"定位/品类","count":15},...]},
        {"name":"哲学","count":0,"empty":true}
      ],
      "topCounts": [["元层",15],["方法论中枢",101],...],     # 各顶层夹文档数(柱状图)
      "methodStage": [["定位/品类",15],...],                # 方法卡四环节(饼图,可空)
      "graph": {"nodes":[{"name":"...","count":N,"cat":0,"color":"#hex"}],"links":[{"source":0,"target":1}]}
    }
  ]
}
"""
import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE = os.path.join(HERE, "..", "assets", "template.html")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate(data):
    if not isinstance(data, dict):
        raise ValueError("顶层必须是 JSON 对象")
    libs = data.get("libraries")
    if not isinstance(libs, list) or not libs:
        raise ValueError("必须包含非空的 libraries 数组")
    for i, lib in enumerate(libs):
        for key in ("id", "name", "kpis"):
            if key not in lib:
                raise ValueError("libraries[%d] 缺少必填字段: %s" % (i, key))
        k = lib["kpis"]
        for key in ("topFolders", "totalDocs", "methodCards", "metaLayer", "emptyAreas"):
            if key not in k:
                # 补默认，避免渲染崩
                k[key] = 0
        if "express" not in k:
            k["express"] = "—"
    if "generated_at" not in data:
        data["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    if "scope" not in data:
        data["scope"] = "single"
    return data


def render(data, template_path, out_path):
    with open(template_path, "r", encoding="utf-8") as f:
        tpl = f.read()
    placeholder = "/*DATA_PLACEHOLDER*/"
    if placeholder not in tpl:
        raise ValueError("模板中未找到 %s 注入点" % placeholder)
    # 用紧凑但可读的中文 JSON 注入；ensure_ascii=False 保留中文
    injected = json.dumps(data, ensure_ascii=False, indent=2)
    html = tpl.replace(placeholder, injected)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


def main():
    ap = argparse.ArgumentParser(description="生成 ima 知识库看板 HTML")
    ap.add_argument("--data", required=True, help="结构 JSON 路径")
    ap.add_argument("--out", default=None, help="输出 HTML 路径(默认 ./kb_dashboard_YYYY-MM-DD.html)")
    ap.add_argument("--template", default=DEFAULT_TEMPLATE, help="模板 HTML 路径")
    args = ap.parse_args()

    try:
        data = validate(load_json(args.data))
    except Exception as e:
        print("❌ 数据校验失败: %s" % e, file=sys.stderr)
        sys.exit(1)

    if args.out is None:
        args.out = "kb_dashboard_%s.html" % datetime.now().strftime("%Y-%m-%d")

    try:
        out = render(data, args.template, args.out)
    except Exception as e:
        print("❌ 渲染失败: %s" % e, file=sys.stderr)
        sys.exit(1)

    size = os.path.getsize(out) / 1024.0
    print("✅ 看板已生成: %s (%.1f KB, %d 个库)" % (out, size, len(data["libraries"])))


if __name__ == "__main__":
    main()
