from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ralf_model import RalfError, load_ralf_file

from .flatten import document_to_register_list
from .hierarchy import document_to_block_forest


def _parse_byte_offset(text: str) -> int:
    """解析 CLI 字节偏移：十进制、0x 十六进制或 Verilog 风格 'h/'d 字面量。"""
    s = text.strip()
    if not s:
        raise ValueError("基址偏移不能为空")
    if s.startswith("'"):
        body = s[1:]
        if body and body[0] in "bBdDhHoO":
            radix = {"b": 2, "B": 2, "d": 10, "D": 10, "h": 16, "H": 16, "o": 8, "O": 8}[
                body[0]
            ]
            return int(body[1:].replace("_", ""), radix)
        return int(body.replace("_", ""), 0)
    return int(s.replace("_", ""), 0)


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ralfconv",
        description="使用 ralf_model 解析 RALF 并输出 JSON（扁平列表或 block 层次结构）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python -m ralf_conv -i chip.ralf\n"
            "  python -m ralf_conv -i chip.ralf -o chip.json\n"
            "  python -m ralf_conv --format hierarchical -i top.ralf -o tree.json\n"
            "  python -m ralf_conv -i top.ralf -o out.json -I ./inc -I ./lib\n"
            "  python -m ralf_conv -i chip.ralf -o chip.json -b 0x4000_0000\n"
        ),
    )
    p.add_argument(
        "-i",
        "--input",
        dest="input_path",
        type=Path,
        required=True,
        metavar="PATH",
        help="输入 .ralf 文件路径",
    )
    p.add_argument(
        "-o",
        "--output",
        dest="output_path",
        type=Path,
        default=None,
        metavar="PATH",
        help="输出 .json 文件路径；省略则打印到标准输出",
    )
    p.add_argument(
        "-I",
        dest="include_dirs",
        type=Path,
        action="append",
        default=[],
        metavar="DIR",
        help="RALF `source` 搜索目录（可重复，对应该文件目录与显式 -I 列表）",
    )
    p.add_argument(
        "--format",
        dest="out_format",
        choices=("flat", "hierarchical"),
        default="flat",
        help=(
            "flat：寄存器扁平列表（path、address、lsb、width）；"
            "hierarchical：按 block 嵌套，字段名对齐 IP-XACT 常用 JSON 映射"
            "（baseAddress、addressOffset、size、bitOffset、bitWidth、addressBlocks 等）。"
        ),
    )
    p.add_argument(
        "-b",
        "--base-offset",
        dest="base_offset",
        type=_parse_byte_offset,
        default=0,
        metavar="ADDR",
        help=(
            "整体基址偏移（字节），加到所有 block 基址与寄存器绝对地址；"
            "支持十进制、0x 十六进制、Verilog 'h/'d 字面量"
        ),
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _make_parser().parse_args(argv)
    if args.input_path.suffix.lower() != ".ralf":
        print("错误: 输入须为 .ralf 文件。", file=sys.stderr)
        return 2
    if args.output_path is not None and args.output_path.suffix.lower() != ".json":
        print("错误: 输出须为 .json 文件。", file=sys.stderr)
        return 2
    try:
        doc = load_ralf_file(
            args.input_path,
            include_paths=tuple(args.include_dirs),
        )
        if args.out_format == "flat":
            rows = document_to_register_list(doc, base_offset=args.base_offset)
            payload = [r.as_mapping() for r in rows]
        else:
            forest = document_to_block_forest(doc, base_offset=args.base_offset)
            payload = [b.as_mapping() for b in forest]
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.output_path is None:
            print(text)
        else:
            args.output_path.parent.mkdir(parents=True, exist_ok=True)
            args.output_path.write_text(text, encoding="utf-8")
        return 0
    except (OSError, ValueError, RalfError) as e:
        print(f"错误: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
