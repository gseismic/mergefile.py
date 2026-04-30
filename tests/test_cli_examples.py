#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
命令行测试示例 - 演示 mergefile 的通配符功能
"""

import os
import subprocess
import sys
import tempfile

# 添加 mergefile 模块到路径 (在父目录)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mergefile


def create_test_project(base_dir: str) -> None:
    """创建一个测试项目结构"""
    # 切换到目标目录
    original_cwd = os.getcwd()
    os.chdir(base_dir)

    try:
        # 创建目录结构
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
            "main.py": """#!/usr/bin/env python
# 主程序文件
def main():
    print("Hello from main")

if __name__ == "__main__":
    main()
""",
            "README.md": """# 测试项目

这是一个用于演示 mergefile 通配符功能的测试项目。

## 功能
- 演示通配符匹配
- 测试文件合并
- 展示多种文件类型
""",
            "requirements.txt": """requests>=2.25.0
pytest>=6.0.0
black>=21.0
flake8>=3.8
""",
            "src/__init__.py": "# 源代码包初始化",
            "src/utils/__init__.py": "# 工具模块",
            "src/utils/helper.py": """# 工具函数模块
def add(a, b):
    '''加法函数'''
    return a + b

def multiply(a, b):
    '''乘法函数'''
    return a * b
""",
            "src/utils/logger.py": """# 日志模块
import logging

def setup_logger(name):
    '''设置日志记录器'''
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
""",
            "src/models/user.py": """# 用户模型
class User:
    '''用户类'''
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def get_info(self):
        '''获取用户信息'''
        return f"{self.name} <{self.email}>"
""",
            "src/models/product.py": """# 产品模型
class Product:
    '''产品类'''
    def __init__(self, name, price, category):
        self.name = name
        self.price = price
        self.category = category

    def display(self):
        '''显示产品信息'''
        return f"{self.name} (${self.price}) - {self.category}"
""",
            "tests/test_main.py": """# 测试主程序
import pytest

def test_addition():
    '''测试加法'''
    assert 1 + 1 == 2

def test_multiplication():
    '''测试乘法'''
    assert 2 * 3 == 6
""",
            "tests/test_utils.py": """# 测试工具函数
import pytest
from src.utils.helper import add, multiply

def test_add():
    '''测试加法函数'''
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_multiply():
    '''测试乘法函数'''
    assert multiply(2, 3) == 6
    assert multiply(0, 5) == 0
""",
            "data/config.json": """{
    "app_name": "TestApp",
    "version": "1.0.0",
    "debug": true,
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "test_db"
    },
    "features": ["auth", "api", "logging"]
}
""",
            "data/settings.yaml": """# 应用设置
app:
  name: "Test Application"
  version: "1.0.0"
  debug: true

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4

database:
  url: "postgresql://user:pass@localhost/db"
  pool_size: 10
""",
            "docs/index.md": """# 项目文档

欢迎阅读项目文档。

## 目录
1. [安装](#安装)
2. [使用](#使用)
3. [API参考](#api参考)

## 安装
```bash
pip install -r requirements.txt
```

## 使用
```python
from src.models.user import User
user = User("Alice", "alice@example.com")
print(user.get_info())
```
""",
            "config/app.cfg": """[app]
name = TestApp
version = 1.0.0
debug = true

[server]
host = 0.0.0.0
port = 8080
timeout = 30

[database]
url = sqlite:///test.db
pool_size = 5
""",
            ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual Environment
.env
.venv
env/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
""",
            ".env.example": """# 环境变量示例
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key-here
DEBUG=true
LOG_LEVEL=INFO
""",
        }

        for file_path, content in files_content.items():
            full_path = os.path.join(base_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        print(f"✅ 在 {base_dir} 创建了测试项目")
        print(f"📁 创建了 {len(files_content)} 个文件")

    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)


def run_cli_examples() -> None:
    """运行命令行示例"""
    print("🚀 开始演示 mergefile 通配符功能")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试项目
        create_test_project(tmpdir)

        # 切换到临时目录
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            print(f"\n📂 工作目录: {tmpdir}")
            print("\n📋 目录结构:")
            subprocess.run(
                [
                    "find",
                    ".",
                    "-type",
                    "f",
                    "-name",
                    "*.py",
                    "-o",
                    "-name",
                    "*.md",
                    "-o",
                    "-name",
                    "*.json",
                    "-o",
                    "-name",
                    "*.yaml",
                    "-o",
                    "-name",
                    "*.cfg",
                    "-o",
                    "-name",
                    "*.txt",
                ],
                capture_output=True,
                text=True,
            )

            examples = [
                {
                    "title": "示例 1: 合并所有Python文件到XML",
                    "command": "python -m mergefile mergefile.py **/*.py -o all_code.xml --header '所有Python源代码' --format xml --lang en",
                    "description": "递归查找所有Python文件并合并为XML格式",
                },
                {
                    "title": "示例 2: 合并源代码目录到Markdown",
                    "command": "python -m mergefile mergefile.py src/**/*.py -o src_docs.md --header '源代码文档' --format markdown --lang en",
                    "description": "合并src目录下的所有Python文件为Markdown格式",
                },
                {
                    "title": "示例 3: 合并配置文件和文档",
                    "command": "python -m mergefile mergefile.py *.md config/* data/*.json data/*.yaml -o config_docs.xml --header '配置和文档' --format xml --lang en",
                    "description": "合并多种类型的配置文件",
                },
                {
                    "title": "示例 4: 合并测试文件",
                    "command": "python -m mergefile mergefile.py tests/*.py -o tests.xml --header '测试代码' --format xml --lang en",
                    "description": "合并tests目录下的测试文件",
                },
                {
                    "title": "示例 5: 使用通配符过滤特定文件",
                    "command": "python -m mergefile mergefile.py **/*.py --exclude tests/ -o source_only.md --header '源代码（排除测试）' --format markdown --lang en",
                    "description": "合并所有Python文件，但排除tests目录",
                },
                {
                    "title": "示例 6: 合并点文件（配置文件）",
                    "command": "python -m mergefile mergefile.py .* -o dotfiles.xml --header '配置文件' --format xml --lang en",
                    "description": "合并所有以点开头的配置文件",
                },
            ]

            for i, example in enumerate(examples, 1):
                print(f"\n{'=' * 60}")
                print(f"{example['title']}")
                print(f"{'=' * 60}")
                print(f"📝 {example['description']}")
                print(f"💻 命令: {example['command']}")

                # 执行命令
                try:
                    # 替换 mergefile.py 为实际路径
                    cmd = example["command"].replace(
                        "python -m mergefile mergefile.py",
                        f"python {os.path.join(original_cwd, 'mergefile.py')}",
                    )

                    print("\n🔧 执行命令...")
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True
                    )

                    if result.returncode == 0:
                        print("✅ 执行成功")
                        print(f"📤 输出:\n{result.stdout}")

                        # 检查输出文件
                        output_file = cmd.split("-o ")[1].split()[0]
                        if os.path.exists(output_file):
                            file_size = os.path.getsize(output_file)
                            print(f"📄 输出文件: {output_file} ({file_size} 字节)")

                            # 显示文件前几行
                            with open(output_file, "r", encoding="utf-8") as f:
                                lines = f.readlines()[:10]
                            print("📖 文件预览（前10行）:")
                            for line in lines:
                                print(f"   {line.rstrip()}")
                            if file_size > sum(len(line) for line in lines):
                                print("   ...")
                        else:
                            print("❌ 输出文件未创建")
                    else:
                        print("❌ 执行失败")
                        print(f"错误输出:\n{result.stderr}")

                except Exception as e:
                    print(f"❌ 执行出错: {str(e)}")

            print(f"\n{'=' * 60}")
            print("🎉 所有示例演示完成！")
            print(f"{'=' * 60}")

            # 显示最终生成的文件
            print("\n📁 生成的文件:")
            subprocess.run(
                ["ls", "-la", "*.xml", "*.md"], capture_output=True, text=True
            )

        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)


def test_direct_api_calls() -> None:
    """直接调用API测试"""
    print("\n🔧 直接API调用测试")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        create_test_project(tmpdir)
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # 测试1: 扩展通配符
            print("\n📋 测试1: 扩展通配符模式")
            patterns = ["src/**/*.py", "tests/*.py"]
            expanded = mergefile.expand_file_patterns(patterns)
            print(f"模式: {patterns}")
            print(f"找到 {len(expanded)} 个文件:")
            for file in expanded[:5]:
                print(f"  - {os.path.relpath(file, tmpdir)}")
            if len(expanded) > 5:
                print(f"  ... 还有 {len(expanded) - 5} 个文件")

            # 测试2: 合并文件
            print("\n📋 测试2: 合并文件")
            output_file = os.path.join(tmpdir, "api_test.xml")
            mergefile.merge_files(
                input_patterns=["src/**/*.py"],
                output_file=output_file,
                header="API测试 - 源代码",
                format_type="xml",
            )

            if os.path.exists(output_file):
                print(f"✅ 成功创建: {output_file}")
                print(f"📏 文件大小: {os.path.getsize(output_file)} 字节")

            # 测试3: 测试边界情况
            print("\n📋 测试3: 测试边界情况")
            try:
                # 尝试将输出文件作为输入
                mergefile.merge_files(
                    input_patterns=["*.py"],
                    output_file=output_file,  # 已经存在的文件
                    header="测试",
                    format_type="xml",
                )
                print("❌ 应该抛出ValueError但未抛出")
            except ValueError as e:
                print(f"✅ 正确抛出ValueError: {str(e)}")

        finally:
            os.chdir(original_cwd)


def main() -> int:
    """主函数"""
    print("🔬 mergefile 通配符功能演示")
    print("=" * 60)

    try:
        # 测试直接API调用
        test_direct_api_calls()

        # 运行命令行示例
        run_cli_examples()

        print("\n🎯 演示总结:")
        print("✅ 支持递归通配符 (**/*.py)")
        print("✅ 支持多种文件类型匹配")
        print("✅ 支持排除模式")
        print("✅ 支持XML和Markdown格式")
        print("✅ 支持自定义头部注释")
        print("✅ 完善的错误处理")

    except KeyboardInterrupt:
        print("\n\n⏹️ 演示被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
