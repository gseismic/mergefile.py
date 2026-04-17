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
                print(f"Warning: Pattern '{pattern}' did not match any files")
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
    exclude_patterns: Optional[List[str]] = None,
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
        exclude_patterns: 排除模式列表（支持通配符，如 --exclude tests/ --exclude *.tmp）

    Raises:
        ValueError: If output file is in input files list, or output file exists and force is not used
        IOError: If unable to write output file
    """
    # 扩展通配符模式
    input_files = expand_file_patterns(input_patterns)

    # 如果有排除模式，过滤文件
    if exclude_patterns:
        # 扩展排除模式
        excluded_files = expand_file_patterns(exclude_patterns)
        excluded_set = set(excluded_files)

        # 过滤掉被排除的文件
        filtered_files = []
        for file_path in input_files:
            if file_path not in excluded_set:
                filtered_files.append(file_path)
            else:
                print(f"Excluded file: {file_path}")

        input_files = filtered_files

    if not input_files:
        raise ValueError("No matching files found")

    # 将input_files中的路径转换为绝对路径，同时将output_file也转换为绝对路径
    abs_input_files = [os.path.abspath(f) for f in input_files]
    abs_output_file = os.path.abspath(output_file)

    # output_file 不能和 input_files 中的任何一个文件路径相同
    # 使用绝对路径进行比较
    if abs_output_file in abs_input_files:
        raise ValueError("output_file cannot be in input_files")

    # 检查输出文件是否已经存在（使用绝对路径）
    if os.path.exists(abs_output_file) and not force:
        raise ValueError(
            f"Output file already exists: {output_file}. Use -f or --force option to force overwrite."
        )

    try:
        with open(output_file, "w", encoding="utf-8") as out_f:
            if format_type == "xml":
                _write_xml_format(out_f, input_files, header)
            else:  # markdown
                _write_markdown_format(out_f, input_files, header)

        print(
            f"Successfully merged {len(input_files)} files to {output_file} (format: {format_type})"
        )
        print("Processed file list:")
        for i, file_path in enumerate(input_files, 1):
            print(f"  {i:3d}. {file_path}")
    except Exception as e:
        print(f"Error writing output file: {str(e)}")
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
            print(f"Warning: File {file_path} does not exist, skipped")
            out_f.write("      <error>File not found</error>\n")
        except UnicodeDecodeError:
            print(f"Error: File {file_path} decoding failed, check encoding format")
            out_f.write("      <error>Encoding error</error>\n")
        except Exception as e:
            print(f"Error: Failed to read file {file_path}: {str(e)}")
            out_f.write(f"      <error>Read error: {escape(str(e))}</error>\n")

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
            print(f"Warning: File {file_path} does not exist, skipped")
            out_f.write("File not found\n\n")
        except UnicodeDecodeError:
            print(f"Error: File {file_path} decoding failed, check encoding format")
            out_f.write("Encoding error\n\n")
        except Exception as e:
            print(f"Error: Failed to read file {file_path}: {str(e)}")
            out_f.write(f"Read error: {str(e)}\n\n")


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
    """Command line entry function"""
    parser = argparse.ArgumentParser(
        description="Merge multiple files into XML or Markdown format, suitable for LLM input\nSupports wildcard patterns (e.g., *.py, src/**/*.py)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Wildcard Pattern Examples:
  mergefile *.py -o output.xml                    # All .py files in current directory
  mergefile src/**/*.py -o output.xml            # All .py files in src directory (recursive)
  mergefile *.py *.md *.txt -o output.xml        # Multiple file types
  mergefile data/*.csv config/*.json -o output.xml # Files from multiple directories
  mergefile **/*.py --exclude tests/ -o output.xml # Exclude specific directories

File Pattern Examples:
  mergefile 1.py 2.csv data/xx.py -o output.xml
  mergefile --header "My project code" src/*.py -o merged.xml
  mergefile --header "Data file merge" data.csv config.json -o result.xml
        """,
    )
    parser.add_argument(
        "--version", action="version", version=f"mergefile {__version__}"
    )
    parser.add_argument(
        "patterns",
        nargs="+",
        help="Input file pattern list (supports wildcards like *.py, **/*.md). Note: Quote wildcard patterns (e.g., '**/*.py') to prevent shell expansion",
    )
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument("--header", help="Add custom header comment")
    parser.add_argument(
        "--format",
        choices=["xml", "markdown"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Disable recursive search (recursive by default)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Exclude patterns (can be used multiple times, e.g., --exclude tests/ --exclude *.tmp). Note: Quote wildcard patterns (e.g., '**/*.py') to prevent shell expansion",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force overwrite of existing output file",
    )

    args = parser.parse_args()

    if len(args.patterns) < 1:
        parser.error("At least one input file pattern is required")

    # 设置递归标志
    recursive = not args.no_recursive

    merge_files(
        args.patterns,
        args.output,
        args.header,
        args.format,
        recursive,
        args.force,
        exclude_patterns=args.exclude,
    )


if __name__ == "__main__":
    main()
