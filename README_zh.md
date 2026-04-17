# MergeFile

[中文文档](README_zh.md) | [English Documentation](README.md)

一个强大的文件合并工具，支持通配符模式，可以将多个文件合并为XML或Markdown格式，特别适合为大语言模型（LLM）准备输入文档。

## 🚀 快速开始

### 基本用法
```bash
# 合并当前目录所有Python文件
mergefile *.py -o output.md

# 使用通配符合并文件（使用引号防止shell扩展）
mergefile '**/*.py' -o all_code.xml

# 合并多种文件类型
mergefile '*.py' '*.md' '*.json' -o combined.md
```

### 高级通配符用法
```bash
# 递归搜索并排除
mergefile '**/*.py' --exclude 'tests/**/*.py' -o source_code.md

# 多重排除
mergefile '**/*' --exclude 'node_modules/' --exclude '*.tmp' -o project_files.xml

# 强制覆盖已存在的输出文件
mergefile '*.py' -o output.md --force
```

### 重要提示：关于通配符
**始终用引号包裹通配符模式**以防止shell扩展：
```bash
# ✅ 正确：引号防止shell扩展通配符
mergefile '**/*.py' --exclude 'tests/**/*.py' -o output.md

# ❌ 错误：shell在mergefile看到之前就扩展了通配符
mergefile **/*.py --exclude tests/**/*.py -o output.md
```

## ✨ 特性

- 🚀 **高级通配符支持**：完整支持 `*.py`、`**/*.md`、`src/**/*.py` 等模式，需要正确使用引号
- 🚫 **智能排除**：使用 `--exclude` 选项排除文件/目录（支持通配符）
- 📝 **双格式输出**：XML用于结构化数据，Markdown用于人类可读输出（默认）
- 🏷️ **自动语言检测**：识别100+文件类型并应用正确的语法高亮
- 🔒 **安全第一**：防止输出文件在输入文件中，需要 `--force` 才能覆盖
- 🔍 **默认递归**：自动搜索子目录，可用 `--no-recursive` 禁用
- 💬 **自定义头部**：使用 `--header "您的描述"` 添加上下文
- 📊 **详细报告**：显示文件列表、计数和警告
- 🛡️ **错误恢复**：跳过问题文件，继续处理
- 📦 **现代打包**：使用 `pyproject.toml`，无需传统的 `setup.py`

## 📦 安装

### 快速安装
```bash
# 克隆并安装
git clone https://github.com/gseismic/mergefile.py
cd mergefile.py
pip install .
```

### 开发安装
```bash
# 可编辑安装，包含开发依赖
pip install -e ".[dev]"
```

### 直接使用（无需安装）
```bash
# 无需安装直接运行
python mergefile.py '**/*.py' -o output.md
```

## 📖 使用指南

### 命令语法
```bash
mergefile [选项] 模式... -o 输出文件
```

### 基本选项
| 选项 | 简写 | 必需 | 说明 |
|------|------|------|------|
| `--output` | `-o` | **是** | 输出文件路径 |
| `--format` | | 否 | `xml` 或 `markdown`（默认：`markdown`） |
| `--header` | | 否 | 自定义头部文本 |
| `--force` | `-f` | 否 | 覆盖已存在的输出文件 |
| `--exclude` | | 否 | 排除模式（可多次使用） |
| `--no-recursive` | | 否 | 禁用递归搜索 |
| `--help` | `-h` | 否 | 显示帮助 |

### ⚠️ 重要：通配符引号
**始终用引号包裹包含通配符的模式**以防止shell扩展：
```bash
# ✅ 正确 - mergefile处理通配符
mergefile '**/*.py' --exclude 'tests/**/*.py' -o output.md

# ❌ 错误 - shell在mergefile看到之前就扩展了
mergefile **/*.py --exclude tests/**/*.py -o output.md
```

### 🎯 实用示例

#### 基本文件合并
```bash
# 当前目录Python文件
mergefile '*.py' -o python_files.md

# 特定目录
mergefile 'src/*.py' -o src_code.xml

# 多种文件类型
mergefile '*.py' '*.md' '*.json' -o combined.md
```

#### 递归搜索 `**`
```bash
# 项目中所有Python文件
mergefile '**/*.py' -o all_python.xml

# src目录所有内容
mergefile 'src/**/*' -o src_all.md

# 多个目录
mergefile 'src/**/*.py' 'tests/**/*.py' -o codebase.md
```

#### 🚫 排除模式
```bash
# 排除测试目录
mergefile '**/*.py' --exclude 'tests/**/*.py' -o source_code.md

# 多重排除
mergefile '**/*.py' --exclude 'tests/' --exclude '*_test.py' -o production_code.xml

# 排除临时文件
mergefile 'config/**/*' --exclude '*.tmp' --exclude '*.bak' -o clean_configs.md

# 复杂排除
mergefile '**/*' --exclude 'node_modules/' --exclude '.git/' --exclude '*.log' -o project_files.xml
```

#### 高级用法
```bash
# 自定义头部
mergefile '**/*.py' --header "项目代码 - $(date)" -o documentation.md

# 强制覆盖
mergefile '*.py' -o existing.md --force

# XML格式用于结构化数据
mergefile '**/*.py' --format xml -o code_structure.xml

# 禁用递归
mergefile '*.py' --no-recursive -o current_dir_only.md
```

### 🔒 安全特性

```bash
# ❌ 错误：输出文件不能在输入文件中
mergefile '*.py' -o main.py
# 错误：output_file 不能和 input_files 中的任何一个文件路径相同

# ❌ 错误：输出文件已存在（使用--force）
mergefile '*.py' -o existing.md
# 错误：输出文件已存在: existing.md。使用 -f 或 --force 选项强制覆盖。

# ✅ 强制覆盖
mergefile '*.py' -o existing.md --force
# 成功：文件已覆盖

# ✅ 安全操作
mergefile '*.py' -o new_output.md
# 成功：新文件已创建
```

### 🏗️ 实际应用场景

#### 1. 完整项目文档
```bash
mergefile \
  --header "项目文档 - 生成于 $(date)" \
  --format xml \
  '**/*.py' '**/*.js' '**/*.html' '**/*.css' \
  --exclude 'node_modules/' \
  --exclude '__pycache__/' \
  --exclude '*.min.js' \
  -o project_docs.xml
```

#### 2. LLM训练数据准备
```bash
mergefile \
  --header "AI训练代码数据集" \
  --format markdown \
  'src/**/*.py' \
  'static/**/*.js' \
  --exclude 'tests/' \
  --exclude 'vendor/' \
  --exclude '*_test.py' \
  -o training_data.md
```

#### 3. 配置管理
```bash
mergefile \
  --header "应用程序配置" \
  'config/*.json' \
  'config/*.yaml' \
  'config/*.toml' \
  '.env.example' \
  --force \
  -o all_configs.md
```

#### 4. 代码审查包
```bash
mergefile \
  --header "代码审查 - 功能分支" \
  'src/**/*.py' \
  'tests/**/*.py' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  -o code_review_package.xml
```

#### 5. 重要文件备份
```bash
mergefile \
  --header "项目备份 - $(date)" \
  '**/*.py' '**/*.md' '**/*.json' '**/*.yaml' \
  --exclude 'venv/' \
  --exclude '.git/' \
  --exclude '*.log' \
  -o project_backup.md
```

## 📄 输出格式

### Markdown（默认）- 人类可读
适合文档和分享。自动检测100+文件类型并应用语法高亮。

```markdown
# 说明
项目分析 - 生成于 2024-01-01

## 文件列表
共合并了 3 个文件:

1. `src/main.py`
2. `src/utils/helper.py`
3. `config/settings.yaml`

## 文件内容

---

### main.py
文件路径: `src/main.py`

```python
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
```

### helper.py
文件路径: `src/utils/helper.py`

```python
def helper():
    return "Help!"
```
```

### XML - 机器可读
结构化格式，适合其他工具处理。使用CDATA避免XML问题。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<file_documentation>
  <description>项目分析 - 生成于 2024-01-01</description>
  
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

### 格式比较
| 方面 | Markdown | XML |
|------|----------|-----|
| **最适合** | 人类阅读、文档 | 机器处理、API |
| **语法高亮** | ✅ 是（100+语言） | ❌ 否 |
| **结构** | 简单章节 | 分层XML |
| **文件大小** | 较小

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

## 🛡️ 错误处理

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

### 常见问题与解决方案
| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `unrecognized arguments` | Shell在mergefile看到之前扩展了通配符 | **用引号包裹通配符模式**：`'**/*.py'` 而不是 `**/*.py` |
| `output_file 不能和 input_files 中的任何一个文件路径相同` | 输出文件在输入模式中 | 使用不同的输出文件名 |
| `输出文件已存在` | 输出文件已经存在 | 使用 `--force` 覆盖或选择不同的文件名 |
| `没有找到任何匹配的文件` | 模式没有匹配到任何文件 | 检查模式，使用 `*.py` 匹配当前目录，`**/*.py` 匹配递归搜索 |

## 🛠️ 开发

### 项目结构
```
mergefile.py/
├── mergefile.py          # 主程序
├── pyproject.toml        # 项目配置和依赖
├── README.md            # 本文档（英文）
├── README_zh.md         # 中文文档
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

# 现代代码检查（Ruff）
uvx ruff check mergefile.py
uvx ruff check . --fix
```

### 构建与发布
```bash
# 构建分发包
python -m build

# 上传到PyPI
twine upload dist/*

## 📄 许可证

MIT 许可证 - 您可以自由使用、修改和分发此软件。
欢迎直接将 `mergefile.py` 脚本复制到您自己的项目中使用。

## 🤝 贡献

欢迎贡献！请随时提交 Issues 或 Pull Requests。

### 贡献指南
1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m '添加一些很棒的功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

### TODO 功能
- [ ] 添加更多输出格式（JSON、HTML）
- [ ] 支持文件内容过滤（移除注释、空行）
- [ ] 添加进度条显示
- [ ] 支持从配置文件读取选项
- [ ] 添加更多文件类型识别

## 📈 版本历史

- **v1.0.0**（初始版本）- 基本文件合并功能
- **v1.1.0**（当前版本）- 添加通配符支持、安全保护、强制覆盖等高级功能

使用 `mergefile --version` 查看当前版本。

## ❓ 常见问题

### Q: 为什么需要用引号包裹通配符模式？
**A**: Shell（bash、zsh等）在将参数传递给程序之前会扩展通配符。当您输入 `**/*.py` 时，shell会将其扩展为文件列表。引号 `'**/*.py'` 告诉shell将模式原样传递给mergefile，然后由mergefile自己处理通配符扩展。

### Q: `*.py` 和 `**/*.py` 有什么区别？
**A**: `*.py` 仅匹配当前目录中的Python文件。`**/*.py` 匹配当前目录和所有子目录中的Python文件（递归）。

### Q: 可以排除多个模式吗？
**A**: 可以！多次使用 `--exclude`：`--exclude 'tests/' --exclude '*.tmp' --exclude 'node_modules/'`

### Q: 如果文件无法读取会怎样？
**A**: mergefile会显示警告并跳过该文件，继续处理其余文件。错误会在输出文件中注明。

### Q: mergefile安全吗？
**A**: 是的！mergefile具有多重安全特性：
- 没有 `--force` 不会覆盖文件
- 防止输出文件在输入文件中
- 对问题文件显示警告
- 即使某些文件失败也继续处理

### Q: 可以在脚本中使用mergefile吗？
**A**: 当然可以！mergefile设计用于交互式使用和脚本编写。使用XML格式时提供清晰的退出代码和机器可读输出。

### Q: 如何获取帮助？
**A**: 使用 `mergefile --help` 获取完整命令参考，或查看本文档中的示例。
```
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