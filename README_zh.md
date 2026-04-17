# MergeFile

[中文文档](README_zh.md) | [English Documentation](README.md)

一个强大的文件合并工具，支持通配符模式，可以将多个文件合并为XML或Markdown格式，特别适合为大语言模型（LLM）准备输入文档。

## 特性

- 🚀 **通配符支持**：支持 `*.py`、`**/*.md` 等通配符模式，轻松匹配嵌套目录
- 📝 **双格式输出**：支持XML和Markdown两种输出格式（默认Markdown）
- 🏷️ **智能语言识别**：自动根据文件扩展名识别代码语言（Markdown格式）
- 🔒 **安全保护**：防止输出文件在输入文件列表中，避免数据丢失
- ⚡ **强制覆盖**：使用 `-f` 或 `--force` 选项可覆盖已存在的输出文件
- 🚫 **排除模式**：支持 `--exclude` 选项排除特定文件或目录
- 🔍 **递归控制**：默认递归搜索，可使用 `--no-recursive` 禁用
- 💬 **自定义头部**：支持添加自定义头部注释说明
- 📊 **详细输出**：显示处理的文件列表和统计信息
- 🛡️ **错误恢复**：跳过不存在或无法读取的文件，继续处理其他文件
- 📦 **易于安装**：支持pip安装和开发模式安装

## 安装

### 从源码安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/gseismic/mergefile.py
cd mergefile.py

# 安装（使用现代pyproject.toml配置）
pip install .
```

### 开发模式安装

```bash
# 克隆仓库并进入目录
git clone https://github.com/gseismic/mergefile.py
cd mergefile.py

# 开发模式安装（可编辑模式）
pip install -e .

# 安装开发依赖（运行测试需要）
pip install -e ".[dev]"
```

## 使用方法

### 基本语法

```bash
mergefile [选项] <文件模式...> -o <输出文件>
```

### 命令行选项

| 选项 | 简写 | 说明 |
|------|------|------|
| `--output` | `-o` | **必需**，指定输出文件路径 |
| `--format` | | 输出格式：`xml` 或 `markdown`（默认：`markdown`） |
| `--header` | | 添加自定义头部注释 |
| `--force` | `-f` | 强制覆盖已存在的输出文件 |
| `--exclude` | | 排除匹配模式的文件（可多次使用） |
| `--no-recursive` | | 禁用递归搜索子目录 |
| `--version` | | 显示版本信息 |
| `--help` | `-h` | 显示帮助信息 |

### 通配符模式示例

#### 基本通配符
```bash
# 合并当前目录所有Python文件
mergefile *.py -o all_python.xml

# 合并src目录下所有Python文件
mergefile src/*.py -o src_code.md

# 合并多种类型文件
mergefile *.py *.md *.json -o combined.xml
```

#### 递归通配符（**）
```bash
# 递归合并所有Python文件（包括子目录）
mergefile **/*.py -o all_code.xml

# 合并src目录及其子目录下的所有文件
mergefile src/**/* -o src_all.md

# 合并特定目录下的所有Python文件
mergefile src/**/*.py tests/**/*.py -o codebase.xml
```

#### 排除模式
```bash
# 合并所有Python文件，但排除测试文件
mergefile **/*.py --exclude tests/ --exclude *_test.py -o source_only.md

# 合并配置文件，排除临时文件
mergefile config/**/* --exclude *.tmp --exclude *.bak -o configs.xml
```

### 安全保护示例

```bash
# 安全保护：输出文件不能在输入文件中
mergefile *.py -o output.py  # 错误：output_file 不能和 input_files 中的任何一个文件路径相同

# 强制覆盖已存在的文件
mergefile *.py -o existing.xml --force  # 覆盖已存在的文件

# 如果不使用--force，会报错
mergefile *.py -o existing.xml  # 错误：输出文件已存在，使用 -f 或 --force 选项强制覆盖
```

### 完整示例

#### 示例1：合并整个项目源代码
```bash
mergefile \
  --header "项目源代码 - 生成于 $(date)" \
  --format xml \
  **/*.py **/*.js **/*.html **/*.css \
  --exclude node_modules/ \
  --exclude __pycache__/ \
  --exclude *.min.js \
  -o project_documentation.xml
```

#### 示例2：为LLM准备训练数据
```bash
mergefile \
  --header "代码数据集 - Python和JavaScript" \
  --format markdown \
  src/**/*.py \
  static/**/*.js \
  --exclude tests/ \
  --exclude vendor/ \
  -o llm_training_data.md
```

#### 示例3：合并配置文件
```bash
mergefile \
  --header "应用配置文件集合" \
  config/*.json \
  config/*.yaml \
  config/*.toml \
  .env.example \
  --force \
  -o all_configs.md
```

## 输出格式

### Markdown格式（默认）

Markdown格式适合人类阅读，自动识别代码语言并添加语法高亮：

```markdown
# 说明

项目源代码 - 生成于 2024-01-01

## 文件列表

共合并了 3 个文件:

1. `src/main.py`
2. `src/utils/helper.py`
3. `config/settings.yaml`

## 文件内容

各文件内容详见下方:

---

### main.py

文件路径: `src/main.py`

```python
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
```

---
```

### XML格式

XML格式提供结构化数据，适合机器处理，使用CDATA块避免XML解析问题：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<file_documentation>
  <description>
    项目源代码 - 生成于 2024-01-01
  </description>

  <file_list>
    <item index="1" path="src/main.py" name="main.py" />
    <item index="2" path="src/utils/helper.py" name="helper.py" />
    <item index="3" path="config/settings.yaml" name="settings.yaml" />
  </file_list>

  <file_contents>
    <file name="main.py" path="src/main.py">
      <![CDATA[
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
      ]]>
    </file>
  </file_contents>
</file_documentation>
```

## 支持的文件类型

工具会自动识别100+种文件类型并在Markdown格式中应用相应的语法高亮：

| 类别 | 文件扩展名 | 语言标识 |
|------|-----------|----------|
| **编程语言** | `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.h`, `.cs`, `.php`, `.rb`, `.go`, `.rs`, `.swift`, `.kt`, `.scala`, `.r` | 对应语言 |
| **标记语言** | `.html`, `.xml`, `.css`, `.scss`, `.sass`, `.md`, `.tex` | 对应语言 |
| **配置文件** | `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf`, `.properties` | 对应语言 |
| **脚本语言** | `.sh`, `.bash`, `.zsh`, `.fish`, `.ps1`, `.bat`, `.cmd` | 对应语言 |
| **数据文件** | `.csv`, `.tsv`, `.sql` | 对应语言 |
| **其他** | `.dockerfile`, `.gitignore`, `.env`, `.log`, `.txt` | 对应语言 |

未列出的文件类型将使用 `text` 作为默认语言标识。

## 错误处理

MergeFile 设计了完善的错误处理机制：

### 文件访问错误
- **文件不存在**：显示警告信息，跳过该文件，继续处理其他文件
- **权限不足**：显示错误信息，跳过该文件
- **编码错误**：显示错误信息，在输出文件中标记编码错误

### 安全保护
- **输出文件在输入中**：立即停止并显示错误，防止数据丢失
- **输出文件已存在**：除非使用 `--force`，否则显示错误并停止

### 输入验证
- **无匹配文件**：显示错误并停止
- **无效参数**：显示详细的帮助信息

## 开发

### 项目结构
```
mergefile.py/
├── mergefile.py          # 主程序
├── pyproject.toml        # 项目配置和依赖
├── setup.py             # 传统安装脚本（兼容性）
├── README.md            # 本文档
├── LICENSE              # MIT许可证
├── test_wildcard.py     # 通配符功能测试
├── test_file_check.py   # 文件检查功能测试
└── test_cli_examples.py # 命令行示例测试
```

### 运行测试
```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行所有测试
pytest

# 运行特定测试文件
pytest test_wildcard.py -v
pytest test_file_check.py -v

# 运行测试并显示覆盖率
pytest --cov=mergefile
```

### 代码质量
```bash
# 代码格式化（Black）
black mergefile.py

# 代码检查（Flake8）
flake8 mergefile.py

# 类型检查（Mypy）
mypy mergefile.py
```

### 构建与发布
```bash
# 构建分发包
python -m build

# 上传到PyPI
twine upload dist/*
```

## 许可证

MIT 许可证 - 您可以自由使用、修改和分发本软件。
您可以直接将 `mergefile.py` 脚本复制到自己的项目中使用。

## 贡献

欢迎贡献！请随时提交 Issue 或 Pull Request。

### 贡献指南
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

### 待办功能
- [ ] 添加更多输出格式（JSON、HTML）
- [ ] 支持文件内容过滤（去除注释、空白行）
- [ ] 添加进度条显示
- [ ] 支持从配置文件读取选项
- [ ] 添加更多文件类型识别

## 版本历史

- **v1.0.0** (初始版本) - 基本文件合并功能
- **v1.1.0** (当前版本) - 添加通配符支持、安全保护、强制覆盖等高级功能

使用 `mergefile --version` 查看当前版本。