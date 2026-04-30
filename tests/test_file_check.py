#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试文件检查和强制覆盖功能
"""

import os
import subprocess
import sys
import tempfile

# 添加 mergefile 模块到路径 (在父目录)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mergefile


def test_output_in_input() -> None:
    """测试输出文件在输入文件中的情况"""
    print("=" * 60)
    print("测试 1: 输出文件在输入文件中")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # 创建测试文件
            with open("test.py", "w", encoding="utf-8") as f:
                f.write('print("Hello")')

            print("创建测试文件: test.py")
            print("尝试将输出文件设置为同一个文件...")

            try:
                mergefile.merge_files(
                    input_patterns=["*.py"],
                    output_file="test.py",
                    header="测试",
                    format_type="xml",
                )
                # 如果没抛出异常，则测试失败
                assert False, "应该抛出ValueError但未抛出"
            except ValueError as e:
                # 检查错误消息是否正确
                assert "output_file cannot be in input_files" in str(e), (
                    f"错误的错误消息: {str(e)}"
                )
                print(f"✅ 测试通过: {str(e)}")
            except Exception as e:
                # 抛出了其他异常，测试失败
                assert False, f"抛出非ValueError异常: {type(e).__name__}: {str(e)}"
        finally:
            os.chdir(original_cwd)


def test_output_exists_no_force() -> None:
    """测试输出文件已存在但未使用强制覆盖"""
    print("\n" + "=" * 60)
    print("测试 2: 输出文件已存在且未使用强制覆盖")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # 创建测试文件
            with open("input.py", "w", encoding="utf-8") as f:
                f.write('print("Input")')

            # 创建已存在的输出文件
            with open("output.xml", "w", encoding="utf-8") as f:
                f.write("Existing content")

            print("创建输入文件: input.py")
            print("创建已存在的输出文件: output.xml")
            print("尝试合并文件（未使用强制覆盖）...")

            try:
                mergefile.merge_files(
                    input_patterns=["*.py"],
                    output_file="output.xml",
                    header="测试",
                    format_type="xml",
                )
                # 如果没抛出异常，则测试失败
                assert False, "应该抛出ValueError但未抛出"
            except ValueError as e:
                # 检查错误消息是否正确
                assert "Output file already exists" in str(e), (
                    f"错误的错误消息: {str(e)}"
                )
                assert "force overwrite" in str(e), f"错误的错误消息: {str(e)}"
                print(f"✅ 测试通过: {str(e)}")
            except Exception as e:
                # 抛出了其他异常，测试失败
                assert False, f"抛出非ValueError异常: {type(e).__name__}: {str(e)}"
        finally:
            os.chdir(original_cwd)


def test_output_exists_with_force() -> None:
    """测试输出文件已存在但使用强制覆盖"""
    print("\n" + "=" * 60)
    print("测试 3: 输出文件已存在且使用强制覆盖")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # 创建测试文件
            with open("input.py", "w", encoding="utf-8") as f:
                f.write('print("Input")')

            # 创建已存在的输出文件
            with open("output.xml", "w", encoding="utf-8") as f:
                f.write("Existing content that should be overwritten")

            print("创建输入文件: input.py")
            print("创建已存在的输出文件: output.xml")
            print("尝试合并文件（使用强制覆盖）...")

            mergefile.merge_files(
                input_patterns=["*.py"],
                output_file="output.xml",
                header="测试",
                format_type="xml",
                force=True,
            )

            # 验证文件是否被覆盖
            with open("output.xml", "r", encoding="utf-8") as f:
                content = f.read()

            # 检查文件内容是否正确
            assert "<?xml" in content, "输出文件不是有效的XML格式"
            assert "print" in content, "输出文件没有包含输入文件的内容"
            print("✅ 测试通过: 文件被成功覆盖")
        finally:
            os.chdir(original_cwd)


def test_normal_case() -> None:
    """测试正常情况（输出文件不存在且不在输入文件中）"""
    print("\n" + "=" * 60)
    print("测试 4: 正常情况（输出文件不存在且不在输入文件中）")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # 创建测试文件
            with open("input1.py", "w", encoding="utf-8") as f:
                f.write('print("File 1")')

            with open("input2.py", "w", encoding="utf-8") as f:
                f.write('print("File 2")')

            print("创建输入文件: input1.py, input2.py")
            print("输出文件: output.xml（不存在）")
            print("尝试合并文件...")

            mergefile.merge_files(
                input_patterns=["*.py"],
                output_file="output.xml",
                header="正常测试",
                format_type="xml",
            )

            # 验证文件是否创建成功
            assert os.path.exists("output.xml"), "输出文件未创建"

            with open("output.xml", "r", encoding="utf-8") as f:
                content = f.read()

            # 检查文件内容是否正确
            assert "<?xml" in content, "输出文件不是有效的XML格式"
            assert "File 1" in content, "输出文件没有包含第一个输入文件的内容"
            assert "File 2" in content, "输出文件没有包含第二个输入文件的内容"
            print("✅ 测试通过: 文件合并成功")
        finally:
            os.chdir(original_cwd)


def test_cli_force_option() -> None:
    """测试命令行强制覆盖选项"""
    print("\n" + "=" * 60)
    print("测试 5: 命令行强制覆盖选项")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # 创建测试文件
            with open("test.py", "w", encoding="utf-8") as f:
                f.write('print("Test")')

            # 创建已存在的输出文件
            with open("existing.xml", "w", encoding="utf-8") as f:
                f.write("Old content")

            print("创建测试文件: test.py")
            print("创建已存在的输出文件: existing.xml")

            # 测试不带强制覆盖选项（应该失败）
            print("\n测试不带强制覆盖选项...")
            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(original_cwd, "mergefile.py"),
                    "*.py",
                    "-o",
                    "existing.xml",
                    "--format",
                    "xml",
                    "--lang",
                    "en",
                ],
                capture_output=True,
                text=True,
            )

            # 检查命令应该失败
            assert result.returncode != 0, "不带强制覆盖选项时应该失败但未失败"
            assert "Output file already exists" in result.stderr, (
                f"错误消息不正确: {result.stderr}"
            )
            print("✅ 不带强制覆盖选项时正确失败")

            # 测试带强制覆盖选项（应该成功）
            print("\n测试带强制覆盖选项...")
            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(original_cwd, "mergefile.py"),
                    "*.py",
                    "-o",
                    "existing.xml",
                    "--format",
                    "xml",
                    "--force",
                    "--lang",
                    "en",
                ],
                capture_output=True,
                text=True,
            )

            # 检查命令应该成功
            assert result.returncode == 0, (
                f"带强制覆盖选项时失败，返回码: {result.returncode}"
            )
            assert "Successfully merged" in result.stdout, (
                f"输出消息不正确: {result.stdout}"
            )
            print("✅ 带强制覆盖选项时成功")
        finally:
            os.chdir(original_cwd)


def main() -> int:
    """主测试函数 - 用于独立运行测试"""
    print("开始测试文件检查和强制覆盖功能")
    print("=" * 60)

    tests = [
        ("测试输出文件在输入文件中", test_output_in_input),
        ("测试输出文件已存在且未使用强制覆盖", test_output_exists_no_force),
        ("测试输出文件已存在且使用强制覆盖", test_output_exists_with_force),
        ("测试正常情况", test_normal_case),
        ("测试命令行强制覆盖选项", test_cli_force_option),
    ]

    passed = 0
    failed = 0
    failed_tests = []

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ {test_name} - 通过")
        except AssertionError as e:
            failed += 1
            failed_tests.append(test_name)
            print(f"❌ {test_name} - 失败: {str(e)}")
        except Exception as e:
            failed += 1
            failed_tests.append(test_name)
            print(f"❌ {test_name} - 异常: {type(e).__name__}: {str(e)}")

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"总测试数: {len(tests)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")

    if failed_tests:
        print(f"失败的测试: {', '.join(failed_tests)}")

    if failed == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n❌ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
