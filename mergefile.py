#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mergefile - 合并多个文件到XML或Markdown格式，适合提供给大模型阅读
支持通配符模式匹配文件和嵌套文件夹
"""

import argparse
import glob
import heapq
import json
import os
import re
from pathlib import Path
from typing import List, Optional
from xml.sax.saxutils import escape, quoteattr

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
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


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
        "original_path": "Original Path",
        "start_line": "Start Line",
        "end_line": "End Line",
    },
}


class LineCounter:
    """Helper class to count lines in output without writing to a file"""

    def __init__(self, start_line: int = 1):
        self.start_line = start_line
        self.current_line = start_line
        self.has_text = False
        self.ends_with_newline = False

    def write(self, text: str) -> None:
        """Count newlines in text to update current line"""
        self.current_line += text.count("\n")
        if text:
            self.has_text = True
            self.ends_with_newline = text.endswith("\n")

    @property
    def line(self) -> int:
        """Current line number"""
        return self.current_line

    @property
    def total_lines(self) -> int:
        """Number of lines written, excluding a position after a final newline."""
        if not self.has_text:
            return 0
        return self.current_line - self.start_line + int(not self.ends_with_newline)


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


def _path_keys(path: str) -> set:
    """Return both lexical and resolved paths for matching and containment."""
    absolute = os.path.normcase(os.path.abspath(path))
    resolved = os.path.normcase(os.path.realpath(absolute))
    return {absolute, resolved}


def _is_within(path: str, directory: str) -> bool:
    try:
        return os.path.commonpath([path, directory]) == directory
    except ValueError:  # Different drives on Windows.
        return False


def _exclude_files(
    input_files: List[str], patterns: List[str], recursive: bool
) -> List[str]:
    """Exclude matching files and everything beneath matching directories."""
    excluded_files = set()
    excluded_directories = set()
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=recursive)
        if not matches and os.path.exists(pattern):
            matches = [pattern]
        if not matches:
            print(f"Warning: Pattern '{pattern}' did not match any files")
        for match in matches:
            if os.path.isdir(match):
                excluded_directories.update(_path_keys(match))
            elif os.path.isfile(match):
                excluded_files.update(_path_keys(match))

    filtered_files = []
    for file_path in input_files:
        keys = _path_keys(file_path)
        excluded = bool(keys & excluded_files) or any(
            _is_within(key, directory)
            for key in keys
            for directory in excluded_directories
        )
        if excluded:
            print(f"Excluded file: {file_path}")
        else:
            filtered_files.append(file_path)
    return filtered_files


def _file_identity(path: str):
    """Identify existing hard links, in addition to resolved path matching."""
    try:
        info = os.stat(path)
        return info.st_dev, info.st_ino
    except OSError:
        return None


def _validate_output_files(
    input_files: List[str], output_files: List[str], force: bool
) -> None:
    """Check every destination before writing any of them."""
    input_paths = set()
    input_identities = set()
    for path in input_files:
        input_paths.update(_path_keys(path))
        identity = _file_identity(path)
        if identity is not None:
            input_identities.add(identity)

    output_paths = set()
    output_identities = set()
    for path in output_files:
        keys = _path_keys(path)
        identity = _file_identity(path)
        if keys & input_paths or (identity is not None and identity in input_identities):
            raise ValueError(f"output_file cannot be in input_files: {path}")
        if keys & output_paths or (identity is not None and identity in output_identities):
            raise ValueError(f"Output files refer to the same file: {path}")
        output_paths.update(keys)
        if identity is not None:
            output_identities.add(identity)
        if os.path.lexists(path) and not force:
            raise ValueError(
                f"Output file already exists: {path}. "
                "Use -f or --force option to force overwrite."
            )


_INVALID_XML_CHAR = re.compile(
    r"[^\x09\x0a\x0d\x20-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]"
)


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
        max_files: 分文件合并模式下的最大文件数，必须是正整数

    Raises:
        ValueError: If an output aliases an input, already exists without force,
            or an option is invalid
        IOError: If unable to write output file
    """
    if format_type not in ("xml", "markdown"):
        raise ValueError("format_type must be 'xml' or 'markdown'")
    if split and (
        isinstance(max_files, bool) or not isinstance(max_files, int) or max_files < 1
    ):
        raise ValueError("max_files must be a positive integer")

    # 扩展通配符模式
    input_files = expand_file_patterns(input_patterns, recursive=recursive)

    # 如果有排除模式，过滤文件
    if exclude_patterns:
        input_files = _exclude_files(input_files, exclude_patterns, recursive)

    if not input_files:
        raise ValueError("No matching files found")

    if format_type == "xml":
        for value in ([header] if header else []) + input_files:
            if _INVALID_XML_CHAR.search(value):
                raise ValueError(
                    "Header or input path contains a character invalid in XML 1.0"
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
            _validate_output_files(input_files, [output_file], force)
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


def _group_and_split_files(input_files: List[str], max_files: int) -> List[List[str]]:
    """Keep nearby files together while balancing chunks by source byte size."""
    absolute_paths = {path: os.path.abspath(path) for path in input_files}
    try:
        common_prefix = os.path.commonpath(
            [os.path.dirname(absolute_paths[path]) for path in input_files]
        )
    except ValueError:  # Files on different Windows drives have no common path.
        common_prefix = None

    groups = {}
    sizes = {}
    for path in input_files:
        absolute = absolute_paths[path]
        if common_prefix is None:
            group_name = os.path.splitdrive(absolute)[0]
        else:
            parts = Path(os.path.relpath(absolute, common_prefix)).parts
            group_name = parts[0] if len(parts) > 1 else "."
        groups.setdefault(group_name, []).append(path)
        try:
            sizes[path] = max(1, os.path.getsize(path))
        except OSError:
            # The writer will report unreadable or disappearing files.
            sizes[path] = 1

    chunk_count = min(max_files, len(input_files))
    total_size = sum(sizes.values())
    target_size = max(1, (total_size + chunk_count - 1) // chunk_count)
    batches = []
    for group_files in groups.values():
        batch = []
        batch_size = 0
        for path in group_files:
            size = sizes[path]
            if batch and batch_size + size > target_size:
                batches.append((batch, batch_size))
                batch = []
                batch_size = 0
            batch.append(path)
            batch_size += size
        if batch:
            batches.append((batch, batch_size))

    # Pack whole batches into the least-loaded chunk. A source file is never split.
    chunks = [[] for _ in range(chunk_count)]
    available = [(0, index) for index in range(chunk_count)]
    heapq.heapify(available)
    for batch, batch_size in sorted(batches, key=lambda item: item[1], reverse=True):
        current_size, index = heapq.heappop(available)
        chunks[index].extend(batch)
        heapq.heappush(available, (current_size + batch_size, index))
    return [chunk for chunk in chunks if chunk]


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

    # 1. 分组并在需要时拆分较大的目录
    if not input_files:
        return
    final_chunks = _group_and_split_files(input_files, max_files)

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
    chunk_outputs = [
        f"{base_name}_{i}{ext}" for i in range(1, len(final_chunks) + 1)
    ]
    json_index = f"{base_name}_index.json"
    md_index = f"{base_name}_index.md"
    _validate_output_files(input_files, chunk_outputs + [json_index, md_index], force)

    for chunk_files, chunk_output in zip(final_chunks, chunk_outputs):

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
    with open(json_index, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=4, ensure_ascii=False)
    
    # 4. 写入索引文件 (Markdown)
    _write_markdown_index(md_index, index_data, language)

    print(msg["split_success"].format(len(final_chunks)))
    print(msg["index_generated"].format(md_index))


def _write_markdown_index(file_path: str, data: dict, language: str) -> None:
    """生成 Markdown 格式的索引文件"""
    msg = MESSAGES.get(language, MESSAGES["zh"])
    
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
        f.write("| --- | --- | --- |\n")
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
            f.write("| --- | --- | --- | --- |\n")
            for entry in files_by_chunk[chunk_name]:
                f.write(f"| `{entry['original_path']}` | {entry['start_line']} | {entry['end_line']} | {entry['line_count']} |\n")
            f.write("\n")


def _calculate_ranges(
    input_files: List[str], header: Optional[str], format_type: str, language: str
) -> tuple:
    """计算每个文件在输出文件中的起止行号和总行数"""
    counter = LineCounter()
    ranges = {}
    if format_type == "markdown":
        _write_markdown_format(
            counter, input_files, header, language=language, collected_ranges=ranges
        )
    else:
        _write_xml_format(
            counter, input_files, header, language=language, collected_ranges=ranges
        )
    return ranges, counter.total_lines


def _write_xml_format(
    out_f: any,
    input_files: List[str],
    header: Optional[str],
    ranges: dict = None,
    language: str = "zh",
    collected_ranges: dict = None,
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
            f'    <item index="{i}" path={quoteattr(file_path)} '
            f'name={quoteattr(file_name)} lines="{range_str}" />\n'
        )
    out_f.write("  </file_list>\n\n")

    # 处理每个输入文件内容
    out_f.write("  <file_contents>\n")
    for file_path in input_files:
        start_line = out_f.line if collected_ranges is not None else None
        file_name = os.path.basename(file_path)
        range_str = (
            f"L{ranges[file_path][0]}-L{ranges[file_path][1]}"
            if ranges and file_path in ranges
            else ""
        )
        out_f.write(
            f'    <file name={quoteattr(file_name)} path={quoteattr(file_path)} '
            f'lines="{range_str}">\n'
        )

        try:
            with open(file_path, "r", encoding="utf-8") as in_f:
                content = in_f.read()
            if _INVALID_XML_CHAR.search(content):
                raise ValueError("Content contains characters invalid in XML 1.0")
        except FileNotFoundError:
            out_f.write(f"      <error>{msg['error_file_not_found']}</error>\n")
        except UnicodeDecodeError:
            out_f.write(f"      <error>{msg['error_encoding']}</error>\n")
        except Exception as e:
            out_f.write(
                f"      <error>{msg['error_read'].format(escape(str(e)))}</error>\n"
            )
        else:
            # Split embedded CDATA terminators without changing the parsed text.
            out_f.write("      <![CDATA[\n")
            out_f.write(content.replace("]]>", "]]]]><![CDATA[>"))
            if not content.endswith("\n"):
                out_f.write("\n")
            out_f.write("      ]]>\n")

        out_f.write("    </file>\n")
        if collected_ranges is not None:
            collected_ranges[file_path] = (start_line, out_f.line - 1)
    out_f.write("  </file_contents>\n")

    out_f.write("</file_documentation>")


def _write_markdown_format(
    out_f: any,
    input_files: List[str],
    header: Optional[str],
    ranges: dict = None,
    language: str = "zh",
    collected_ranges: dict = None,
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
        start_line = out_f.line if collected_ranges is not None else None
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
        except FileNotFoundError:
            out_f.write(f"{msg['error_file_not_found']}\n\n")
        except UnicodeDecodeError:
            out_f.write(f"{msg['error_encoding']}\n\n")
        except Exception as e:
            out_f.write(f"{msg['error_read'].format(str(e))}\n\n")
        else:
            _, ext = os.path.splitext(file_name)
            lang = _get_language_by_extension(ext)
            longest_fence = max(
                (len(match.group()) for match in re.finditer(r"`+", content)),
                default=0,
            )
            fence = "`" * max(3, longest_fence + 1)
            out_f.write(f"{fence}{lang}\n")
            out_f.write(content)
            if not content.endswith("\n"):
                out_f.write("\n")
            out_f.write(f"{fence}\n\n")
        if collected_ranges is not None:
            collected_ranges[file_path] = (start_line, out_f.line - 2)


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


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a positive integer")
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


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
        nargs="*",
        help="Input file pattern list (supports wildcards like *.py, **/*.md). Note: Quote wildcard patterns (e.g., '**/*.py') to prevent shell expansion",
    )
    parser.add_argument("-o", "--output", help="Output file path (required when merging)")
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
        help="Split output into balanced chunks, keeping nearby files together",
    )
    parser.add_argument(
        "--max-files",
        type=_positive_int,
        default=9,
        help="Positive maximum number of chunks when using --split (default: 9)",
    )
    args = parser.parse_args()

    save_only = args.save_lang and not args.patterns and args.output is None
    if not save_only:
        if not args.patterns:
            parser.error("At least one input file pattern is required")
        if args.output is None:
            parser.error("-o/--output is required when merging files")

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
        if lang_to_save == "zh":
            print(f"已保存默认语言: {lang_to_save}")
        else:
            print(f"Default language saved: {lang_to_save}")

    if save_only:
        return

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
