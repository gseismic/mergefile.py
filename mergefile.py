#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mergefile - 合并多个文件到XML或Markdown格式，适合提供给大模型阅读
支持通配符模式匹配文件和嵌套文件夹
"""

import argparse
import glob
import json
import os
from pathlib import Path
from typing import List, Optional, TextIO
from xml.sax.saxutils import escape

__version__ = "1.7.0"

CONFIG_FILE = Path.home() / ".mergefile.json"


def load_config() -> dict:
    """Load configuration from ~/.mergefile.json"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(config: dict) -> None:
    """Save configuration to ~/.mergefile.json"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass


# 国际化字符串定义
MESSAGES = {
    "zh": {
        "tip": "提示：您可以根据标记的行号进行阅读。",
        "description": "说明",
        "file_list": "文件列表",
        "merged_count": "共合并了 {} 个文件:",
        "file_contents": "文件内容",
        "details_below": "各文件内容详见下方:",
        "file_path": "文件路径",
        "error_file_not_found": "文件未找到",
        "error_encoding": "编码错误",
        "error_read": "读取错误: {}",
        "success": "成功合并了 {} 个文件到 {} (格式: {})",
        "processed_list": "已处理文件列表:",
        "split_success": "分文件合并完成，共生成 {} 个文件。",
        "index_generated": "索引文件已生成: {}",
        "index_title": "合并项目索引",
        "reading_tips": "阅读建议",
        "tips_content": [
            "1. 由于项目规模较大，已将内容拆分为多个合并文件。",
            "2. 请使用此索引在各合并分块中查找特定原始文件。",
            "3. 每个条目都提供了文件名、起始行号和结束行号，方便定位。",
            "4. 您可以根据行号快速跳转到目标代码段。"
        ],
        "chunk_summary": "分块统计",
        "chunk_file": "合并文件名",
        "file_count": "包含文件数",
        "line_count": "总行数",
        "file_list": "文件列表",
        "original_path": "原始路径",
        "start_line": "起始行",
        "end_line": "结束行",
    },
    "en": {
        "tip": "Tip: You can read according to the marked line numbers.",
        "description": "Description",
        "file_list": "File List",
        "merged_count": "Merged {} files:",
        "file_contents": "File Contents",
        "details_below": "See below for file contents:",
        "file_path": "File path",
        "error_file_not_found": "File not found",
        "error_encoding": "Encoding error",
        "error_read": "Read error: {}",
        "success": "Successfully merged {} files to {} (format: {})",
        "processed_list": "Processed file list:",
        "split_success": "Split merge completed, generated {} files.",
        "index_generated": "Index file generated: {}",
        "index_title": "Merged Project Index",
        "reading_tips": "Reading Tips",
        "tips_content": [
            "1. This project has been merged into multiple files due to its size.",
            "2. Use this index to locate specific files across the merged chunks.",
            "3. Each entry provides the filename, start line, and end line for navigation.",
            "4. You can use tools like `sed` or editor search to jump to specific lines."
        ],
        "chunk_summary": "Chunk Summary",
        "chunk_file": "Chunk File",
        "file_count": "File Count",
        "line_count": "Line Count",
        "file_list": "File List",
        "original_path": "Original Path",
        "start_line": "Start Line",
        "end_line": "End Line",
    },
}


class LineCounter:
    """Helper class to count lines in output without writing to a file"""

    def __init__(self, start_line: int = 1):
        self.current_line = start_line

    def write(self, text: str) -> None:
        """Count newlines in text to update current line"""
        self.current_line += text.count("\n")

    @property
    def line(self) -> int:
        """Current line number"""
        return self.current_line


def expand_file_patterns(patterns: List[str], recursive: bool = True) -> List[str]:
    """
    扩展通配符模式为具体的文件路径列表

    Args:
        patterns: 包含通配符的文件模式列表
        recursive: 是否允许递归搜索 (针对 ** 模式)

    Returns:
        扩展后的文件路径列表，按字母顺序排序
    """
    expanded_files = []

    for pattern in patterns:
        # 使用 glob 扩展通配符
        matched_files = glob.glob(pattern, recursive=recursive)

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
                    # 标准化路径以确保去重有效
                    expanded_files.append(os.path.normpath(file_path))

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
    language: str = "zh",
    split: bool = False,
    max_files: int = 9,
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
        language: 输出语言 ('zh' 或 'en')
        split: 是否开启分文件合并模式
        max_files: 分文件合并模式下的最大文件数

    Raises:
        ValueError: If output file is in input files list, or output file exists and force is not used
        IOError: If unable to write output file
    """
    # 扩展通配符模式
    input_files = expand_file_patterns(input_patterns, recursive=recursive)

    # 如果有排除模式，过滤文件
    if exclude_patterns:
        # 扩展排除模式
        excluded_files = expand_file_patterns(exclude_patterns, recursive=recursive)
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
        if split:
            _merge_files_split(
                input_files,
                output_file,
                header,
                format_type,
                force,
                language,
                max_files,
            )
        else:
            # 第一步：计算各文件在输出文件中的行号范围
            ranges, _ = _calculate_ranges(input_files, header, format_type, language)

            with open(output_file, "w", encoding="utf-8") as out_f:
                if format_type == "xml":
                    _write_xml_format(out_f, input_files, header, ranges, language)
                else:  # markdown
                    _write_markdown_format(out_f, input_files, header, ranges, language)

            msg = MESSAGES.get(language, MESSAGES["zh"])
            print(msg["success"].format(len(input_files), output_file, format_type))
            print(msg["processed_list"])
            for i, file_path in enumerate(input_files, 1):
                print(f"  {i:3d}. {file_path}")
    except Exception as e:
        print(f"Error writing output file: {str(e)}")
        raise


def _merge_files_split(
    input_files: List[str],
    output_file: str,
    header: Optional[str],
    format_type: str,
    force: bool,
    language: str,
    max_files: int,
) -> None:
    """处理分文件合并逻辑"""
    msg = MESSAGES.get(language, MESSAGES["zh"])

    # 1. 分组逻辑：按一级子目录分组
    if not input_files:
        return

    # 寻找共同前缀，以便更智能地分组
    if len(input_files) > 1:
        common_prefix = os.path.commonpath([os.path.dirname(f) for f in input_files])
    else:
        common_prefix = os.path.dirname(input_files[0])

    groups = {}  # group_name -> list of files
    for f in input_files:
        # 获取相对于共同前缀的路径
        try:
            rel_path = os.path.relpath(f, common_prefix)
            parts = Path(rel_path).parts
            if len(parts) > 1:
                group_name = parts[0]
            else:
                # 如果就在共同前缀目录下，或者是文件本身
                # 检查它是否是 common_prefix 下的文件
                if os.path.dirname(f) == common_prefix:
                    group_name = "."
                else:
                    group_name = os.path.basename(common_prefix) or "."
        except ValueError:
            # 如果不在同一个驱动器（Windows）等情况，回退到原始逻辑
            parts = Path(f).parts
            group_name = parts[0] if len(parts) > 1 else "."

        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append(f)

    # 如果分组超过 max_files，需要合并小分组
    sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)
    
    final_chunks = []
    if len(sorted_groups) <= max_files:
        final_chunks = [files for name, files in sorted_groups]
    else:
        # 简单合并：前 max_files-1 个大组独立，剩余的组合并到一起
        final_chunks = [files for name, files in sorted_groups[:max_files-1]]
        remaining_files = []
        for name, files in sorted_groups[max_files-1:]:
            remaining_files.extend(files)
        final_chunks.append(remaining_files)

    # 2. 执行合并并记录索引
    index_data = {
        "metadata": {
            "total_files": len(input_files),
            "total_chunks": len(final_chunks),
            "total_lines": 0,
            "format": format_type,
            "created_at": None,  # 可选添加时间戳
        },
        "chunks": [],
        "files": [],
    }

    base_name, ext = os.path.splitext(output_file)
    total_all_lines = 0
    
    for i, chunk_files in enumerate(final_chunks, 1):
        chunk_output = f"{base_name}_{i}{ext}"
        
        # 检查覆盖
        if os.path.exists(chunk_output) and not force:
            raise ValueError(f"Output file already exists: {chunk_output}. Use -f to overwrite.")

        # 计算该 chunk 的范围
        ranges, chunk_total_lines = _calculate_ranges(chunk_files, header, format_type, language)
        total_all_lines += chunk_total_lines

        with open(chunk_output, "w", encoding="utf-8") as out_f:
            if format_type == "xml":
                _write_xml_format(out_f, chunk_files, header, ranges, language)
            else:
                _write_markdown_format(out_f, chunk_files, header, ranges, language)
        
        # 记录 chunk 信息
        index_data["chunks"].append({
            "chunk_file": os.path.basename(chunk_output),
            "file_count": len(chunk_files),
            "line_count": chunk_total_lines
        })

        # 记录到索引
        for f_path in chunk_files:
            r_start, r_end = ranges.get(f_path, (0, 0))
            index_data["files"].append({
                "original_path": f_path,
                "merged_file": os.path.basename(chunk_output),
                "start_line": r_start,
                "end_line": r_end,
                "line_count": r_end - r_start + 1
            })
        
        print(msg["success"].format(len(chunk_files), chunk_output, format_type))

    index_data["metadata"]["total_lines"] = total_all_lines

    # 3. 写入索引文件 (JSON)
    json_index = f"{base_name}_index.json"
    with open(json_index, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=4, ensure_ascii=False)
    
    # 4. 写入索引文件 (Markdown)
    md_index = f"{base_name}_index.md"
    _write_markdown_index(md_index, index_data, language)

    print(msg["split_success"].format(len(final_chunks)))
    print(msg["index_generated"].format(md_index))


def _write_markdown_index(file_path: str, data: dict, language: str) -> None:
    """生成 Markdown 格式的索引文件"""
    msg = MESSAGES.get(language, MESSAGES["zh"])
    meta = data["metadata"]
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {msg['index_title']}\n\n")
        
        # 阅读建议
        f.write(f"## {msg['reading_tips']}\n")
        for tip in msg["tips_content"]:
            f.write(f"- {tip}\n")
        f.write("\n")
        
        # 分块统计
        f.write(f"## {msg['chunk_summary']}\n\n")
        f.write(f"| {msg['chunk_file']} | {msg['file_count']} | {msg['line_count']} |\n")
        f.write(f"| --- | --- | --- |\n")
        for chunk in data["chunks"]:
            f.write(f"| {chunk['chunk_file']} | {chunk['file_count']} | {chunk['line_count']} |\n")
        f.write("\n")
        
        # 文件列表 (按分块分组)
        f.write(f"## {msg['file_list']}\n\n")
        
        # 为了方便展示，我们将文件按分块重新组织
        files_by_chunk = {}
        for file_entry in data["files"]:
            chunk_name = file_entry["merged_file"]
            if chunk_name not in files_by_chunk:
                files_by_chunk[chunk_name] = []
            files_by_chunk[chunk_name].append(file_entry)
            
        for chunk_name in sorted(files_by_chunk.keys()):
            f.write(f"### {chunk_name}\n\n")
            f.write(f"| {msg['original_path']} | {msg['start_line']} | {msg['end_line']} | {msg['line_count']} |\n")
            f.write(f"| --- | --- | --- | --- |\n")
            for entry in files_by_chunk[chunk_name]:
                f.write(f"| `{entry['original_path']}` | {entry['start_line']} | {entry['end_line']} | {entry['line_count']} |\n")
            f.write("\n")


def _calculate_ranges(
    input_files: List[str], header: Optional[str], format_type: str, language: str
) -> tuple:
    """计算每个文件在输出文件中的起止行号和总行数"""
    # 进行模拟写入以计算准确的行号范围
    # 注意：模拟过程必须与实际写入过程（_write_*_format）在行数上完全保持一致
    return _do_calculate_ranges(input_files, header, format_type, language)


def _do_calculate_ranges(input_files, header, format_type, language):
    counter = LineCounter()
    ranges = {}
    msg = MESSAGES.get(language, MESSAGES["zh"])

    if format_type == "markdown":
        counter.write(f"# {msg['description']}\n\n")
        counter.write(f"{msg['tip']}\n\n")
        if header:
            counter.write(f"{header}\n\n")
        counter.write(f"## {msg['file_list']}\n\n")
        counter.write(f"{msg['merged_count'].format(len(input_files))}\n\n")
        for i, file_path in enumerate(input_files, 1):
            # 占位符 L000-L000 与真实行号占位一致，不改变行数
            counter.write(f"{i}. `{file_path}` L000-L0000\n")
        counter.write(f"\n## {msg['file_contents']}\n\n")
        counter.write(f"{msg['details_below']}\n\n")
        counter.write("---\n\n")

        for file_path in input_files:
            file_name = os.path.basename(file_path)
            start_line = counter.line
            counter.write(f"### {file_name} L000-L0000\n\n")
            counter.write(f"{msg['file_path']}: `{file_path}`\n\n")
            counter.write(f"```lang\n")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    counter.write(content)
                    if not content.endswith("\n"):
                        counter.write("\n")
            except FileNotFoundError:
                counter.write(f"{msg['error_file_not_found']}\n\n")
            except UnicodeDecodeError:
                counter.write(f"{msg['error_encoding']}\n\n")
            except Exception as e:
                counter.write(f"{msg['error_read'].format(str(e))}\n\n")
            counter.write("```\n\n")
            end_line = counter.line - 2  # 减去最后的 \n\n
            ranges[file_path] = (start_line, end_line)
    else:  # xml
        counter.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        counter.write("<file_documentation>\n")
        counter.write(f"  <tip>{msg['tip']}</tip>\n")
        if header:
            counter.write("  <description>\n")
            counter.write(f"    {header}\n")
            counter.write("  </description>\n\n")
        counter.write(f"  <file_list>\n")
        for i, file_path in enumerate(input_files, 1):
            file_name = os.path.basename(file_path)
            counter.write(f'    <item index="{i}" path="{file_path}" name="{file_name}" lines="L000-L0000" />\n')
        counter.write("  </file_list>\n\n")
        counter.write("  <file_contents>\n")
        for file_path in input_files:
            file_name = os.path.basename(file_path)
            start_line = counter.line
            counter.write(f'    <file name="{file_name}" path="{file_path}" lines="L000-L0000">\n')
            counter.write("      <![CDATA[\n")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    counter.write(content)
                    if not content.endswith("\n"):
                        counter.write("\n")
            except FileNotFoundError:
                counter.write(f"      <error>{msg['error_file_not_found']}</error>\n")
            except UnicodeDecodeError:
                counter.write(f"      <error>{msg['error_encoding']}</error>\n")
            except Exception as e:
                counter.write(f"      <error>{msg['error_read'].format(str(e))}</error>\n")
            counter.write("      ]]>\n")
            counter.write("    </file>\n")
            end_line = counter.line - 1
            ranges[file_path] = (start_line, end_line)
        counter.write("  </file_contents>\n")
        counter.write("</file_documentation>")

    return ranges, counter.line


def _write_xml_format(
    out_f: any,
    input_files: List[str],
    header: Optional[str],
    ranges: dict = None,
    language: str = "zh",
) -> None:
    """写入XML格式"""
    msg = MESSAGES.get(language, MESSAGES["zh"])
    # 写入XML头部
    out_f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    out_f.write("<file_documentation>\n")
    out_f.write(f"  <tip>{escape(msg['tip'])}</tip>\n")

    # 添加自定义头部
    if header:
        out_f.write("  <description>\n")
        out_f.write(f"    {escape(header)}\n")
        out_f.write("  </description>\n\n")

    # 添加文件列表
    out_f.write("  <file_list>\n")
    for i, file_path in enumerate(input_files, 1):
        file_name = os.path.basename(file_path)
        range_str = (
            f"L{ranges[file_path][0]}-L{ranges[file_path][1]}"
            if ranges and file_path in ranges
            else ""
        )
        out_f.write(
            f'    <item index="{i}" path="{escape(file_path)}" '
            f'name="{escape(file_name)}" lines="{range_str}" />\n'
        )
    out_f.write("  </file_list>\n\n")

    # 处理每个输入文件内容
    out_f.write("  <file_contents>\n")
    for file_path in input_files:
        file_name = os.path.basename(file_path)
        range_str = (
            f"L{ranges[file_path][0]}-L{ranges[file_path][1]}"
            if ranges and file_path in ranges
            else ""
        )
        out_f.write(
            f'    <file name="{escape(file_name)}" path="{escape(file_path)}" '
            f'lines="{range_str}">\n'
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
            out_f.write(f"      <error>{msg['error_file_not_found']}</error>\n")
        except UnicodeDecodeError:
            out_f.write(f"      <error>{msg['error_encoding']}</error>\n")
        except Exception as e:
            out_f.write(
                f"      <error>{msg['error_read'].format(escape(str(e)))}</error>\n"
            )

        out_f.write("    </file>\n")
    out_f.write("  </file_contents>\n")

    out_f.write("</file_documentation>")


def _write_markdown_format(
    out_f: any,
    input_files: List[str],
    header: Optional[str],
    ranges: dict = None,
    language: str = "zh",
) -> None:
    """写入Markdown格式"""
    msg = MESSAGES.get(language, MESSAGES["zh"])
    out_f.write(f"# {msg['description']}\n\n")
    out_f.write(f"{msg['tip']}\n\n")

    # 添加自定义头部
    if header:
        out_f.write(f"{header}\n\n")

    out_f.write(f"## {msg['file_list']}\n\n")
    out_f.write(f"{msg['merged_count'].format(len(input_files))}\n\n")
    for i, file_path in enumerate(input_files, 1):
        range_str = (
            f" L{ranges[file_path][0]}-L{ranges[file_path][1]}"
            if ranges and file_path in ranges
            else ""
        )
        out_f.write(f"{i}. `{file_path}`{range_str}\n")
    out_f.write(f"\n## {msg['file_contents']}\n\n")
    out_f.write(f"{msg['details_below']}\n\n")
    out_f.write("---\n\n")

    # 处理每个输入文件
    for file_path in input_files:
        file_name = os.path.basename(file_path)
        range_str = (
            f" L{ranges[file_path][0]}-L{ranges[file_path][1]}"
            if ranges and file_path in ranges
            else ""
        )
        out_f.write(f"### {file_name}{range_str}\n\n")
        out_f.write(f"{msg['file_path']}: `{file_path}`\n\n")

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
            out_f.write(f"{msg['error_file_not_found']}\n\n")
        except UnicodeDecodeError:
            out_f.write(f"{msg['error_encoding']}\n\n")
        except Exception as e:
            out_f.write(f"{msg['error_read'].format(str(e))}\n\n")


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
    parser.add_argument(
        "--lang",
        choices=["zh", "en"],
        help="Output language: en (English, default) or zh (Chinese).",
    )
    parser.add_argument(
        "--save-lang",
        action="store_true",
        help="Save the current language choice as the default in ~/.mergefile.json",
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Split output into multiple files based on subdirectories (max 9 files)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=9,
        help="Maximum number of output files when using --split (default: 9)",
    )
    args = parser.parse_args()

    if len(args.patterns) < 1:
        parser.error("At least one input file pattern is required")

    # 获取配置
    config = load_config()

    # 确定语言优先级：命令行参数 > 配置文件 > 默认(en)
    language = args.lang
    if not language:
        language = config.get("language", "en")

    # 只有当用户显式使用 --save-lang 时才保存到配置
    if args.save_lang:
        # 如果指定了 --lang，则保存该值；否则保存当前生效的语言
        lang_to_save = args.lang if args.lang else language
        config["language"] = lang_to_save
        save_config(config)
        msg = MESSAGES.get(lang_to_save, MESSAGES["en"])
        if lang_to_save == "zh":
            print(f"已保存默认语言: {lang_to_save}")
        else:
            print(f"Default language saved: {lang_to_save}")

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
        language=language,
        split=args.split,
        max_files=args.max_files,
    )


if __name__ == "__main__":
    main()
