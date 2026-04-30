#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 mergefile 的通配符功能
"""

import os
import sys
import tempfile
from typing import Any, Dict, List

# 添加 mergefile 模块到路径 (在父目录)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mergefile


def create_test_structure(base_dir: str) -> None:
    """在指定目录创建测试目录结构"""
    # 切换到目标目录
    original_cwd = os.getcwd()
    os.chdir(base_dir)

    try:
        # 创建目录
        dirs = [
            "src",
            "src/utils",
            "src/models",
            "tests",
            "data",
            "docs",
            "config",
            "logs",
        ]

        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)

        # 创建测试文件
        files_content = {
            "main.py": "def main():\n    print('Hello from main')\n\nif __name__ == '__main__':\n    main()\n",
            "README.md": "# Test Project\n\nThis is a test project.\n",
            "requirements.txt": "requests>=2.25.0\npytest>=6.0.0\n",
            "src/__init__.py": "",
            "src/utils/__init__.py": "",
            "src/utils/helper.py": "def helper_function():\n    return 'Helper'\n",
            "src/utils/logger.py": "import logging\n\nlogger = logging.getLogger(__name__)\n",
            "src/models/user.py": "class User:\n    def __init__(self, name):\n        self.name = name\n",
            "src/models/product.py": "class Product:\n    def __init__(self, name, price):\n        self.name = name\n        self.price = price\n",
            "tests/test_main.py": "import pytest\n\ndef test_dummy():\n    assert True\n",
            "tests/test_utils.py": "import pytest\n\ndef test_helper():\n    assert True\n",
            "data/config.json": '{\n    "debug": true,\n    "port": 8080\n}\n',
            "data/settings.yaml": "database:\n  host: localhost\n  port: 5432\n",
            "docs/index.md": "# Documentation\n\nWelcome to the docs.\n",
            "config/app.cfg": "[app]\nname = test_app\nversion = 1.0.0\n",
            "logs/app.log": "2024-01-01 INFO: Application started\n2024-01-01 INFO: Configuration loaded\n",
            ".gitignore": "*.pyc\n__pycache__/\n*.log\n",
            ".env.example": "DATABASE_URL=postgresql://user:pass@localhost/db\nSECRET_KEY=your-secret-key\n",
        }

        for file_path, content in files_content.items():
            full_path = os.path.join(base_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        print(f"在 {base_dir} 创建了 {len(files_content)} 个测试文件")
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)


def test_wildcard_patterns() -> None:
    """测试通配符模式"""
    print("\n" + "=" * 60)
    print("测试通配符模式")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试目录结构
        create_test_structure(tmpdir)

        # 切换到临时目录进行测试
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            test_cases: List[Dict[str, Any]] = [
                {
                    "name": "测试当前目录所有Python文件",
                    "patterns": ["*.py"],
                    "expected_min_files": 1,  # main.py
                },
                {
                    "name": "测试src目录下所有Python文件",
                    "patterns": ["src/*.py"],
                    "expected_min_files": 1,  # src/__init__.py
                },
                {
                    "name": "测试递归搜索所有Python文件",
                    "patterns": ["**/*.py"],
                    "expected_min_files": 8,  # 所有.py文件
                },
                {
                    "name": "测试多种文件类型",
                    "patterns": ["*.py", "*.md", "*.txt"],
                    "expected_min_files": 3,  # main.py, README.md, requirements.txt
                },
                {
                    "name": "测试特定目录下的文件",
                    "patterns": ["src/**/*.py"],
                    "expected_min_files": 5,  # src目录下的所有.py文件
                },
                {
                    "name": "测试配置文件",
                    "patterns": ["config/*", "data/*.json", "data/*.yaml"],
                    "expected_min_files": 3,  # app.cfg, config.json, settings.yaml
                },
                {
                    "name": "测试点文件",
                    "patterns": [".*"],
                    "expected_min_files": 2,  # .gitignore, .env.example
                },
            ]

            for test_case in test_cases:
                print(f"\n测试: {test_case['name']}")
                print(f"模式: {test_case['patterns']}")

                try:
                    # 提取测试用例参数
                    patterns: list[str] = test_case["patterns"]
                    expected_min: int = test_case["expected_min_files"]

                    # 扩展文件模式
                    expanded_files = mergefile.expand_file_patterns(patterns)

                    print(f"找到文件数: {len(expanded_files)}")
                    if expanded_files:
                        print("文件列表:")
                        for i, file_path in enumerate(expanded_files[:5], 1):
                            rel_path = os.path.relpath(file_path, tmpdir)
                            print(f"  {i}. {rel_path}")
                        if len(expanded_files) > 5:
                            print(f"  ... 还有 {len(expanded_files) - 5} 个文件")

                    # 验证结果
                    assert len(expanded_files) >= expected_min, (
                        f"预期至少 {expected_min} 个文件，但找到 {len(expanded_files)} 个"
                    )

                    # 验证所有文件都存在
                    for file_path in expanded_files:
                        assert os.path.exists(file_path), f"文件不存在: {file_path}"
                        assert os.path.isfile(file_path), f"不是文件: {file_path}"

                    print("✓ 测试通过")

                except Exception as e:
                    print(f"✗ 测试失败: {str(e)}")
                    import traceback

                    traceback.print_exc()
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)


def test_merge_with_wildcards() -> None:
    """测试使用通配符合并文件"""
    print("\n" + "=" * 60)
    print("测试使用通配符合并文件")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试目录结构
        create_test_structure(tmpdir)

        # 切换到临时目录进行测试
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            test_cases: List[Dict[str, Any]] = [
                {
                    "name": "合并所有Python文件到XML",
                    "patterns": ["**/*.py"],
                    "output": "all_python.xml",
                    "format": "xml",
                    "header": "所有Python源代码",
                },
                {
                    "name": "合并配置文件和文档到Markdown",
                    "patterns": ["*.md", "config/*", "data/*.json", "data/*.yaml"],
                    "output": "config_docs.md",
                    "format": "markdown",
                    "header": "配置和文档",
                },
                {
                    "name": "合并src目录文件",
                    "patterns": ["src/**/*.py"],
                    "output": "src_code.xml",
                    "format": "xml",
                    "header": "源代码目录",
                },
            ]

            for test_case in test_cases:
                print(f"\n测试: {test_case['name']}")
                print(f"模式: {test_case['patterns']}")
                print(f"输出: {test_case['output']}")

                try:
                    # 提取测试用例参数
                    patterns: list[str] = test_case["patterns"]
                    output: str = test_case["output"]
                    header: str = test_case["header"]
                    format_type: str = test_case["format"]

                    output_path = os.path.join(tmpdir, output)

                    # 执行合并
                    mergefile.merge_files(
                        input_patterns=patterns,
                        output_file=output_path,
                        header=header,
                        format_type=format_type,
                    )

                    # 验证输出文件
                    assert os.path.exists(output_path), f"输出文件不存在: {output_path}"

                    # 检查文件大小
                    file_size = os.path.getsize(output_path)
                    print(f"输出文件大小: {file_size} 字节")
                    assert file_size > 0, "输出文件为空"

                    # 检查文件内容
                    with open(output_path, "r", encoding="utf-8") as f:
                        content = f.read()

                        # 验证头部
                        if header:
                            if format_type == "xml":
                                assert header in content
                            else:  # markdown
                                assert header in content

                        # 验证格式
                        if format_type == "xml":
                            assert "<?xml" in content
                            assert "<file_documentation>" in content
                        else:  # markdown
                            assert "# 说明" in content

                    print("✓ 测试通过")

                except Exception as e:
                    print(f"✗ 测试失败: {str(e)}")
                    import traceback

                    traceback.print_exc()
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)


def test_edge_cases() -> None:
    """测试边界情况"""
    print("\n" + "=" * 60)
    print("测试边界情况")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 切换到临时目录
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # 创建一些测试文件
            files = {
                "test1.py": "print('test1')",
                "test2.py": "print('test2')",
                "test3.txt": "text file",
                "subdir/test4.py": "print('test4')",
                "subdir/test5.md": "# Markdown",
            }

            for file_path, content in files.items():
                full_path = os.path.join(tmpdir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

            test_cases: List[Dict[str, Any]] = [
                {
                    "name": "测试不存在的模式",
                    "patterns": ["*.nonexistent"],
                    "should_fail": True,
                },
                {
                    "name": "测试混合存在和不存在的模式",
                    "patterns": ["*.py", "*.nonexistent"],
                    "should_fail": False,
                },
                {
                    "name": "测试空目录模式",
                    "patterns": ["empty_dir/*"],
                    "should_fail": True,
                },
                {
                    "name": "测试绝对路径模式",
                    "patterns": [os.path.join(tmpdir, "*.py")],
                    "should_fail": False,
                },
                {
                    "name": "测试相对路径模式",
                    "patterns": ["./*.py"],
                    "should_fail": False,
                },
            ]

            for test_case in test_cases:
                print(f"\n测试: {test_case['name']}")
                print(f"模式: {test_case['patterns']}")

                try:
                    # 提取测试用例参数
                    patterns: list[str] = test_case["patterns"]
                    should_fail: bool = test_case["should_fail"]

                    expanded_files = mergefile.expand_file_patterns(patterns)

                    if should_fail:
                        # 应该没有文件或只有警告
                        print(f"找到文件数: {len(expanded_files)}")
                        if len(expanded_files) == 0:
                            print("✓ 测试通过（如预期没有找到文件）")
                        else:
                            print("⚠ 找到了一些文件（可能不是预期的）")
                    else:
                        # 应该找到文件
                        assert len(expanded_files) > 0, "应该找到文件但没找到"
                        print(f"✓ 测试通过，找到 {len(expanded_files)} 个文件")

                except Exception as e:
                    if test_case["should_fail"]:
                        print(f"✓ 测试通过（如预期失败: {str(e)}）")
                    else:
                        print(f"✗ 测试失败: {str(e)}")
                        import traceback

                        traceback.print_exc()
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)


def test_output_in_input() -> None:
    """测试输出文件在输入文件中的情况"""
    print("\n" + "=" * 60)
    print("测试输出文件在输入文件中的情况")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 切换到临时目录
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # 创建测试文件
            test_file = "test.py"
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("print('test')")

            output_file = test_file  # 输出文件和输入文件相同

            try:
                mergefile.merge_files(
                    input_patterns=["*.py"],
                    output_file=output_file,
                    header="测试",
                    format_type="xml",
                )
                print("✗ 测试失败：应该抛出ValueError")
            except ValueError as e:
                if "output_file" in str(e) and "input_files" in str(e):
                    print("✓ 测试通过（正确抛出ValueError）")
                else:
                    print(f"✗ 测试失败：错误的错误消息: {str(e)}")
            except Exception as e:
                print(f"✗ 测试失败：抛出非ValueError异常: {type(e).__name__}: {str(e)}")
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)


def main() -> int:
    """主测试函数"""
    print("开始测试 mergefile 通配符功能")
    print("=" * 60)

    try:
        # 运行所有测试
        test_wildcard_patterns()
        test_merge_with_wildcards()
        test_edge_cases()
        test_output_in_input()

        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n测试过程中发生错误: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
