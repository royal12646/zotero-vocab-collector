from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vocab_collector.collector import Collector
from vocab_collector.config import Config, load_env_file
from vocab_collector.enrich import Enricher
from vocab_collector.exporter import write_xlsx
from vocab_collector.zotero import ZoteroClient, ZoteroError


ROOT = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按高亮颜色收集 Zotero 论文生词")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="检查 Zotero 和 PDF 依赖")
    collect = sub.add_parser("collect", help="提取高亮并生成本地 Excel")
    collect.add_argument("--paper-key", help="只导出指定 Zotero 论文 key")
    collect.add_argument("--enrich", action="store_true", help="补充翻译")
    collect.add_argument("--output", type=Path, default=ROOT / "output" / "vocabulary.xlsx")
    return parser


def doctor(config: Config) -> int:
    print(f"目标高亮颜色: {config.highlight_color}")
    try:
        status = ZoteroClient().status()
        print(f"Zotero: 已连接，版本 {status.get('version', '未知')}")
    except ZoteroError as exc:
        print(f"Zotero: 未就绪 - {exc}")
    try:
        import pymupdf  # noqa: F401
        print("PDF 原句恢复: PyMuPDF 已安装")
    except ImportError:
        print("PDF 原句恢复: 缺少 PyMuPDF，请安装 requirements.txt")
    print("输出方式: 本地 Excel（不使用 Airtable）")
    return 0


def main() -> int:
    load_env_file(ROOT / ".env")
    config = Config.from_environment()
    args = build_parser().parse_args()
    if args.command == "doctor":
        return doctor(config)
    try:
        rows = Collector(ZoteroClient(), config.highlight_color).collect(args.paper_key)
    except ZoteroError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2
    if args.enrich:
        enricher = Enricher(config.mymemory_email, ROOT / "output" / "enrichment-cache.json")
        rows = [enricher.enrich(row) for row in rows]
    try:
        write_xlsx(rows, args.output)
    except PermissionError:
        print(f"错误: 无法写入 {args.output}，请关闭正在打开该文件的 Excel 或其他程序后重试。", file=sys.stderr)
        return 2
    print(f"已写入 {len(rows)} 条记录: {args.output.resolve()}")
    summary = {"ok": sum(row.context_status == "ok" for row in rows), "需核对": sum(row.context_status != "ok" for row in rows)}
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
