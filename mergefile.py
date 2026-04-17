#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mergefile - 合并多个文件到XML或Markdown格式，适合提供给大模型阅读
支持通配符模式匹配文件和嵌套文件夹
"""

import argparse
import glob
import os
from typing import List, Optional, TextIO
from xml.sax.saxutils import escape

__version__ = "1.1.0"


def expand_file_patterns(patterns: List[str]) -> List[str]:
    """
    扩展通配符模式为具体的文件路径列表

    Args:
        patterns: 包含通配符的文件模式列表

    Returns:
        扩展后的文件路径列表，按字母顺序排序
    """
    expanded_files = []

    for pattern in patterns:
        # 使用 glob 扩展通配符
        matched_files = glob.glob(pattern, recursive=True)

        if not matched_files:
            # 如果没有匹配到文件，检查是否是直接的文件路径
            if os.path.isfile(pattern):
                expanded_files.append(pattern)
            else:
                print(f"警告: 模式 '{pattern}' 没有匹配到任何文件")
        else:
            # 过滤掉目录，只保留文件
            for file_path in matched_files:
                if os.path.isfile(file_path):
                    expanded_files.append(file_path)

    # 去重并排序
    unique_files = sorted(set(expanded_files))
    return unique_files


def merge_files(
    input_patterns: List[str],
    output_file: str,
    header: Optional[str] = None,
    format_type: str = "xml",
    recursive: bool = True,
    force: bool = False,
) -> None:
    """
    将多个文件合并到一个输出文件中，支持通配符模式

    Args:
        input_patterns: 输入文件模式列表（支持通配符）
        output_file: 输出文件路径
        header: 自定义头部注释
        format_type: 输出格式 ('xml' 或 'markdown')
        recursive: 是否递归搜索子目录
        force: 是否强制覆盖已存在的输出文件

    Raises:
        ValueError: 如果输出文件在输入文件列表中，或者输出文件已存在且未使用强制覆盖
        IOError: 如果无法写入输出文件
    """
    # 扩展通配符模式
    input_files = expand_file_patterns(input_patterns)

    if not input_files:
        raise ValueError("没有找到任何匹配的文件")

    # 将input_files中的路径转换为绝对路径，同时将output_file也转换为绝对路径
    abs_input_files = [os.path.abspath(f) for f in input_files]
    abs_output_file = os.path.abspath(output_file)

    # output_file 不能和 input_files 中的任何一个文件路径相同
    # 使用绝对路径进行比较
    if abs_output_file in abs_input_files:
        raise ValueError("output_file 不能和 input_files 中的任何一个文件路径相同")

    # 检查输出文件是否已经存在（使用绝对路径）
    if os.path.exists(abs_output_file) and not force:
        raise ValueError(
            f"输出文件已存在: {output_file}。使用 -f 或 --force 选项强制覆盖。"
        )

    try:
        with open(output_file, "w", encoding="utf-8") as out_f:
            if format_type == "xml":
                _write_xml_format(out_f, input_files, header)
            else:  # markdown
                _write_markdown_format(out_f, input_files, header)

        print(
            f"成功合并 {len(input_files)} 个文件到 {output_file} (格式: {format_type})"
        )
        print("处理的文件列表:")
        for i, file_path in enumerate(input_files, 1):
            print(f"  {i:3d}. {file_path}")
    except Exception as e:
        print(f"写入输出文件时出错: {str(e)}")
        raise


def _write_xml_format(
    out_f: TextIO, input_files: List[str], header: Optional[str]
) -> None:
    """写入XML格式"""
    # 写入XML头部
    out_f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    out_f.write("<file_documentation>\n")

    # 添加自定义头部
    if header:
        out_f.write("  <description>\n")
        out_f.write(f"    {escape(header)}\n")
        out_f.write("  </description>\n\n")

    # 添加文件列表
    out_f.write("  <file_list>\n")
    for i, file_path in enumerate(input_files, 1):
        file_name = os.path.basename(file_path)
        out_f.write(
            f'    <item index="{i}" path="{escape(file_path)}" '
            f'name="{escape(file_name)}" />\n'
        )
    out_f.write("  </file_list>\n\n")

    # 处理每个输入文件内容
    out_f.write("  <file_contents>\n")
    for file_path in input_files:
        file_name = os.path.basename(file_path)
        out_f.write(
            f'    <file name="{escape(file_name)}" path="{escape(file_path)}">\n'
        )

        try:
            with open(file_path, "r", encoding="utf-8") as in_f:
                content = in_f.read()
                # 使用CDATA包裹内容，避免XML解析问题
                out_f.write("      <![CDATA[\n")
                out_f.write(content)
                if not content.endswith("\n"):
                    out_f.write("\n")
                out_f.write("      ]]>\n")
        except FileNotFoundError:
            print(f"警告: 文件 {file_path} 不存在，已跳过")
            out_f.write("      <error>文件不存在</error>\n")
        except UnicodeDecodeError:
            print(f"错误: 文件 {file_path} 解码失败，请检查编码格式")
            out_f.write("      <error>编码错误</error>\n")
        except Exception as e:
            print(f"错误: 读取文件 {file_path} 时出错: {str(e)}")
            out_f.write(f"      <error>读取错误: {escape(str(e))}</error>\n")

        out_f.write("    </file>\n")
    out_f.write("  </file_contents>\n")

    out_f.write("</file_documentation>")


def _write_markdown_format(
    out_f: TextIO, input_files: List[str], header: Optional[str]
) -> None:
    """写入Markdown格式"""
    out_f.write("# 说明\n\n")

    # 添加自定义头部
    if header:
        out_f.write(f"{header}\n\n")

    out_f.write("## 文件列表\n\n")
    out_f.write(f"共合并了 {len(input_files)} 个文件:\n\n")
    for i, file_path in enumerate(input_files, 1):
        out_f.write(f"{i}. `{file_path}`\n")
    out_f.write("\n## 文件内容\n\n")
    out_f.write("各文件内容详见下方:\n\n")
    out_f.write("---\n\n")

    # 处理每个输入文件
    for file_path in input_files:
        file_name = os.path.basename(file_path)
        out_f.write(f"### {file_name}\n\n")
        out_f.write(f"文件路径: `{file_path}`\n\n")

        try:
            with open(file_path, "r", encoding="utf-8") as in_f:
                content = in_f.read()
                # 根据文件扩展名确定代码块语言
                _, ext = os.path.splitext(file_name)
                lang = _get_language_by_extension(ext)
                out_f.write(f"```{lang}\n")
                out_f.write(content)
                if not content.endswith("\n"):
                    out_f.write("\n")
                out_f.write("```\n\n")
        except FileNotFoundError:
            print(f"警告: 文件 {file_path} 不存在，已跳过")
            out_f.write("文件不存在\n\n")
        except UnicodeDecodeError:
            print(f"错误: 文件 {file_path} 解码失败，请检查编码格式")
            out_f.write("编码错误\n\n")
        except Exception as e:
            print(f"错误: 读取文件 {file_path} 时出错: {str(e)}")
            out_f.write(f"读取错误: {str(e)}\n\n")


def _get_language_by_extension(ext: str) -> str:
    """根据文件扩展名返回代码块语言标识"""
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".cs": "csharp",
        ".php": "php",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".r": "r",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".xml": "xml",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".conf": "ini",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "zsh",
        ".fish": "fish",
        ".ps1": "powershell",
        ".bat": "batch",
        ".cmd": "batch",
        ".dockerfile": "dockerfile",
        ".md": "markdown",
        ".tex": "latex",
        ".csv": "csv",
        ".tsv": "csv",
        ".txt": "text",
        ".log": "text",
        ".properties": "properties",
        ".gradle": "groovy",
        ".lua": "lua",
        ".pl": "perl",
        ".pm": "perl",
        ".t": "perl",
        ".ex": "elixir",
        ".exs": "elixir",
        ".erl": "erlang",
        ".hrl": "erlang",
        ".clj": "clojure",
        ".cljs": "clojure",
        ".cljc": "clojure",
        ".edn": "clojure",
        ".hs": "haskell",
        ".lhs": "haskell",
        ".scm": "scheme",
        ".ss": "scheme",
        ".rkt": "racket",
        ".jl": "julia",
        ".dart": "dart",
        ".elm": "elm",
        ".purs": "purescript",
        ".coffee": "coffeescript",
        ".litcoffee": "coffeescript",
        ".vue": "vue",
        ".svelte": "svelte",
        ".astro": "astro",
    }
    return language_map.get(ext.lower(), "text")


def main() -> None:
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description="合并多个文件到XML或Markdown格式，适合提供给大模型阅读\n支持通配符模式（如 *.py, src/**/*.py）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
通配符模式示例:
  mergefile *.py -o output.xml                    # 当前目录所有.py文件
  mergefile src/**/*.py -o output.xml            # src目录下所有.py文件（递归）
  mergefile *.py *.md *.txt -o output.xml        # 多种类型文件
  mergefile data/*.csv config/*.json -o output.xml # 多个目录的文件
  mergefile **/*.py --exclude tests/ -o output.xml # 排除特定目录

文件模式示例:
  mergefile 1.py 2.csv data/xx.py -o output.xml
  mergefile --header "这是我的项目代码" src/*.py -o merged.xml
  mergefile --header "数据文件合并" data.csv config.json -o result.xml
        """,
    )
    parser.add_argument(
        "--version", action="version", version=f"mergefile {__version__}"
    )
    parser.add_argument(
        "patterns",
        nargs="+",
        help="输入文件模式列表（支持通配符如 *.py, **/*.md）",
    )
    parser.add_argument("-o", "--output", required=True, help="输出文件路径")
    parser.add_argument("--header", help="添加自定义头部注释")
    parser.add_argument(
        "--format",
        choices=["xml", "markdown"],
        default="markdown",
        help="输出格式 (默认: markdown)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="禁用递归搜索（默认启用递归）",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="排除模式（可多次使用，如 --exclude tests/ --exclude *.tmp）",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="强制覆盖已存在的输出文件",
    )

    args = parser.parse_args()

    if len(args.patterns) < 1:
        parser.error("至少需要一个输入文件模式")

    # 设置递归标志
    recursive = not args.no_recursive

    # 处理排除模式（简化版本，实际应用中可能需要更复杂的过滤）
    filtered_patterns = []
    for pattern in args.patterns:
        # 这里简化处理，实际应用中可能需要更复杂的排除逻辑
        should_exclude = False
        for exclude_pattern in args.exclude:
            # 简单的字符串匹配检查
            if exclude_pattern in pattern:
                should_exclude = True
                break

        if not should_exclude:
            filtered_patterns.append(pattern)
        else:
            print(f"排除模式: {pattern}")

    if not filtered_patterns:
        parser.error("所有输入模式都被排除，没有文件可处理")

    merge_files(
        filtered_patterns, args.output, args.header, args.format, recursive, args.force
    )


if __name__ == "__main__":
    main()
