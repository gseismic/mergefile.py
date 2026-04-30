# MergeFile

A powerful file merging tool with wildcard support that can combine multiple files into XML or Markdown format, especially suitable for preparing input documents for Large Language Models (LLM).

[中文文档](README_zh.md) | [English Documentation](README.md)

## ✨ Core Features

- 📍 **Line Range Tracking**: Automatically tracks the starting and ending line numbers of each file in the merged output (e.g., `L100-L200`) for easier navigation and LLM referencing.
- 🌍 **Multi-language Support**: Supports **English** (default) and **Chinese**.
  - **English**: `mergefile --lang en ...` (**Default**)
  - **Chinese**: `mergefile --lang zh ...`
  - **One-time Config**: `mergefile --lang zh --save-lang` (Saves Chinese as your permanent default in `~/.mergefile.json`)
- 🚀 **Advanced Wildcard Support**: Full support for recursive patterns like `**/*.py` with proper shell quoting.
- 🚫 **Smart Exclusion**: Easily exclude files or directories using the `--exclude` option.
- 📝 **Dual Format Output**: Choose between Markdown (best for human reading) or XML (best for machine processing).
- 🏷️ **Auto Language Detection**: Automatically recognizes 100+ file types and applies syntax highlighting in Markdown.

## 🚀 Quick Start

### Basic Usage
```bash
# Merge all Python files in current directory
mergefile *.py -o output.md

# Merge files with wildcards (use quotes to prevent shell expansion)
mergefile '**/*.py' -o all_code.xml

# Merge multiple file types
mergefile '*.py' '*.md' '*.json' -o combined.md
```

### Advanced Wildcard Usage
```bash
# Recursive search with exclusion
mergefile '**/*.py' --exclude 'tests/**/*.py' -o source_code.md

# Multiple exclusions
mergefile '**/*' --exclude 'node_modules/' --exclude '*.tmp' -o project_files.xml

# Force overwrite existing output
mergefile '*.py' -o output.md --force
```

### Important Note on Wildcards
**Always quote wildcard patterns** to prevent shell expansion:
```bash
# ✅ Correct: Quotes prevent shell from expanding wildcards
mergefile '**/*.py' --exclude 'tests/**/*.py' -o output.md

# ❌ Incorrect: Shell expands wildcards before mergefile sees them
mergefile **/*.py --exclude tests/**/*.py -o output.md
```

## ✨ Features

- 🚀 **Advanced Wildcard Support**: Full support for `*.py`, `**/*.md`, `src/**/*.py` patterns with proper shell quoting
- 🚫 **Smart Exclusion**: Exclude files/directories with `--exclude` option (supports wildcards)
- 📝 **Dual Format Output**: XML for structured data, Markdown for human-readable output (default)
- 🏷️ **Auto Language Detection**: 100+ file types recognized with proper syntax highlighting
- 🔒 **Safety First**: Prevents output file from being in input, requires `--force` to overwrite
- 🔍 **Recursive by Default**: Searches subdirectories automatically, disable with `--no-recursive`
- 💬 **Custom Headers**: Add context with `--header "Your description"`
- 📊 **Detailed Reporting**: Shows file list, counts, and warnings
- 📍 **Line Range Tracking**: Automatically tracks the line numbers of each file in the merged output (e.g., `L100-L200`) for easier navigation
- 🛡️ **Error Resilient**: Skips problematic files, continues processing
- 📦 **Modern Packaging**: Uses `pyproject.toml`, no legacy `setup.py` required

## 📦 Installation

### Quick Install
```bash
# Clone and install
git clone https://github.com/gseismic/mergefile.py
cd mergefile.py
pip install .
```

### Development Install
```bash
# Editable install with dev dependencies
pip install -e ".[dev]"
```

### Direct Usage (No Install)
```bash
# Run directly without installation
python mergefile.py '**/*.py' -o output.md
```

## 📖 Usage Guide

### Command Syntax
```bash
mergefile [OPTIONS] PATTERNS... -o OUTPUT_FILE
```

### Essential Options
| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--output` | `-o` | **Yes** | Output file path |
| `--format` | | No | `xml` or `markdown` (default: `markdown`) |
| `--header` | | No | Custom header text |
| `--force` | `-f` | No | Overwrite existing output file |
| `--exclude` | | No | Exclude pattern (use multiple times) |
| `--no-recursive` | | No | Disable recursive search |
| `--lang` | | No | Output language: `en` (default) or `zh` |
| `--save-lang` | | No | Save current language as default in config |
| `--help` | `-h` | No | Show help |

### ⚠️ Critical: Quoting Wildcards
**Always quote patterns with wildcards** to prevent shell expansion:
```bash
# ✅ Correct - mergefile handles the wildcards
mergefile '**/*.py' --exclude 'tests/**/*.py' -o output.md

# ❌ Wrong - shell expands before mergefile sees them
mergefile **/*.py --exclude tests/**/*.py -o output.md
```

### 🎯 Practical Examples

#### Basic File Merging
```bash
# Current directory Python files
mergefile '*.py' -o python_files.md

# Specific directory
mergefile 'src/*.py' -o src_code.xml

# Multiple file types
mergefile '*.py' '*.md' '*.json' -o combined.md
```

#### Recursive Search with `**`
```bash
# All Python files in project
mergefile '**/*.py' -o all_python.xml

# Everything in src directory
mergefile 'src/**/*' -o src_all.md

# Multiple directories
mergefile 'src/**/*.py' 'tests/**/*.py' -o codebase.md
```

#### 🚫 Exclusion Patterns
```bash
# Exclude test directories
mergefile '**/*.py' --exclude 'tests/**/*.py' -o source_code.md

# Multiple exclusions
mergefile '**/*.py' --exclude 'tests/' --exclude '*_test.py' -o production_code.xml

# Exclude temporary files
mergefile 'config/**/*' --exclude '*.tmp' --exclude '*.bak' -o clean_configs.md

# Complex exclusion
mergefile '**/*' --exclude 'node_modules/' --exclude '.git/' --exclude '*.log' -o project_files.xml
```

#### Advanced Usage
```bash
# With custom header
mergefile '**/*.py' --header "Project Code - $(date)" -o documentation.md

# Force overwrite
mergefile '*.py' -o existing.md --force

# XML format for structured data
mergefile '**/*.py' --format xml -o code_structure.xml

# Disable recursion
mergefile '*.py' --no-recursive -o current_dir_only.md
```

### 🔒 Safety Features

```bash
# ❌ Error: Output cannot be in input files
mergefile '*.py' -o main.py
# Error: output_file cannot be in input_files

# ❌ Error: Output exists (use --force)
mergefile '*.py' -o existing.md
# Error: Output file exists: existing.md. Use -f or --force option to force overwrite.

# ✅ Force overwrite
mergefile '*.py' -o existing.md --force
# Success: File overwritten

# ✅ Safe operation
mergefile '*.py' -o new_output.md
# Success: New file created
```

### 🏗️ Real-World Scenarios

#### 1. Complete Project Documentation
```bash
mergefile \
  --header "Project Documentation - Generated on $(date)" \
  --format xml \
  '**/*.py' '**/*.js' '**/*.html' '**/*.css' \
  --exclude 'node_modules/' \
  --exclude '__pycache__/' \
  --exclude '*.min.js' \
  -o project_docs.xml
```

#### 2. LLM Training Data Preparation
```bash
mergefile \
  --header "Code Dataset for AI Training" \
  --format markdown \
  'src/**/*.py' \
  'static/**/*.js' \
  --exclude 'tests/' \
  --exclude 'vendor/' \
  --exclude '*_test.py' \
  -o training_data.md
```

#### 3. Configuration Management
```bash
mergefile \
  --header "App Configurations" \
  'config/*.json' \
  'config/*.yaml' \
  'config/*.toml' \
  '.env.example' \
  --force \
  -o all_configs.md
```

#### 4. Code Review Package
```bash
mergefile \
  --header "Code Review - Feature Branch" \
  'src/**/*.py' \
  'tests/**/*.py' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  -o code_review_package.xml
```

#### 5. Backup Important Files
```bash
mergefile \
  --header "Project Backup - $(date)" \
  '**/*.py' '**/*.md' '**/*.json' '**/*.yaml' \
  --exclude 'venv/' \
  --exclude '.git/' \
  --exclude '*.log' \
  -o project_backup.md
```

## 📄 Output Formats

### Markdown (Default) - Human Readable
Perfect for documentation and sharing. Auto-detects 100+ file types with syntax highlighting.

```markdown
# Description
Project Analysis - Generated on 2024-01-01

## File List
Merged 3 files:

1. `src/main.py` L16-L22
2. `src/utils/helper.py` L24-L30
3. `config/settings.yaml` L32-L38

## File Contents

---

### main.py L16-L22
File path: `src/main.py`

```python
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
```

### helper.py
File path: `src/utils/helper.py`

```python
def helper():
    return "Help!"
```
```

### XML - Machine Readable
Structured format ideal for processing by other tools. Uses CDATA to avoid XML issues.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<file_documentation>
  <description>Project Analysis - Generated on 2024-01-01</description>
  
  <file_list>
    <item index="1" path="src/main.py" name="main.py" lines="L9-L15" />
    <item index="2" path="src/utils/helper.py" name="helper.py" lines="L16-L22" />
    <item index="3" path="config/settings.yaml" name="settings.yaml" lines="L23-L29" />
  </file_list>
  
  <file_contents>
    <file name="main.py" path="src/main.py" lines="L9-L15">
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

### Format Comparison
| Aspect | Markdown | XML |
|--------|----------|-----|
| **Best For** | Human reading, documentation | Machine processing, APIs |
| **Syntax Highlighting** | ✅ Yes (100+ languages) | ❌ No |
| **Structure** | Simple sections | Hierarchical XML |
| **File Size** | Smaller | Larger (due to XML tags) |
| **Readability** | Excellent | Good (with XML viewer) |
| **Default** | ✅ Yes | ❌ No |

## 📋 Supported File Types

The tool automatically recognizes 100+ file types and applies corresponding syntax highlighting in Markdown format:

| Category | File Extensions | Language Identifier |
|----------|----------------|---------------------|
| **Programming Languages** | `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.h`, `.cs`, `.php`, `.rb`, `.go`, `.rs`, `.swift`, `.kt`, `.scala`, `.r` | Corresponding language |
| **Markup Languages** | `.html`, `.xml`, `.css`, `.scss`, `.sass`, `.md`, `.tex` | Corresponding language |
| **Configuration Files** | `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf`, `.properties` | Corresponding language |
| **Scripting Languages** | `.sh`, `.bash`, `.zsh`, `.fish`, `.ps1`, `.bat`, `.cmd` | Corresponding language |
| **Data Files** | `.csv`, `.tsv`, `.sql` | Corresponding language |
| **Others** | `.dockerfile`, `.gitignore`, `.env`, `.log`, `.txt` | Corresponding language |

Unlisted file types will use `text` as the default language identifier.

## 🛡️ Error Handling

MergeFile has a comprehensive error handling mechanism:

### File Access Errors
- **File not found**: Shows warning, skips the file, continues processing other files
- **Permission denied**: Shows error, skips the file
- **Encoding error**: Shows error, marks encoding error in output file

### Safety Protection
- **Output file in input**: Immediately stops and shows error, preventing data loss
- **Output file exists**: Unless using `--force`, shows error and stops

### Input Validation
- **No matching files**: Shows error and stops
- **Invalid arguments**: Shows detailed help information

### Common Issues & Solutions
| Issue | Cause | Solution |
|-------|-------|----------|
| `unrecognized arguments` | Shell expanded wildcards before mergefile saw them | **Quote wildcard patterns**: `'**/*.py'` instead of `**/*.py` |
| `output_file cannot be in input_files` | Output file is in the input patterns | Use different output filename |
| `Output file exists` | Output file already exists | Use `--force` to overwrite or choose different name |
| `No matching files` | Pattern doesn't match any files | Check pattern, use `*.py` for current dir, `**/*.py` for recursive |

## 🛠️ Development

### Project Structure
```
mergefile.py/
├── mergefile.py          # Main program
├── pyproject.toml        # Project configuration and dependencies
├── README.md            # This document (English)
├── README_zh.md         # Chinese documentation
├── LICENSE              # MIT License
├── test_wildcard.py     # Wildcard functionality tests
├── test_file_check.py   # File check functionality tests
└── test_cli_examples.py # Command line examples tests
```

### Running Tests
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run specific test files
pytest test_wildcard.py -v
pytest test_file_check.py -v

# Run tests with coverage
pytest --cov=mergefile
```

### Code Quality
```bash
# Code formatting (Black)
black mergefile.py

# Code linting (Flake8)
flake8 mergefile.py

# Type checking (Mypy)
mypy mergefile.py

# Modern linting (Ruff)
uvx ruff check mergefile.py
uvx ruff check . --fix
```

### Building and Publishing
```bash
# Build distribution packages
python -m build

# Upload to PyPI
twine upload dist/*
```

## 📄 License

MIT License - You are free to use, modify, and distribute this software. 
Feel free to copy the `mergefile.py` script directly into your own projects and use it as needed.

## 🤝 Contributing

Contributions are welcome! Feel free to submit Issues or Pull Requests.

### Contribution Guidelines
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### TODO Features
- [ ] Add more output formats (JSON, HTML)
- [ ] Support file content filtering (remove comments, blank lines)
- [ ] Add progress bar display
- [ ] Support reading options from configuration file
- [ ] Add more file type recognition

## 📈 Version History

- **v1.0.0** (Initial version) - Basic file merging functionality
- **v1.1.0** - Added wildcard support, safety protection, force overwrite, and other advanced features
- **v1.2.0** - Added automatic line range tracking for input files in merged output
- **v1.3.0** - Added Multi-language support (`zh`/`en`) and automatic reading tips
- **v1.4.0** - Added French support (`fr`) and automatic language persistence
- **v1.5.0** - Added Spanish support (`es`)
- **v1.6.0** (Current version) - Simplified to EN/ZH, EN as default, added `--save-lang`

Use `mergefile --version` to view current version.

## ❓ FAQ

### Q: Why do I need to quote wildcard patterns?
**A**: Shells (bash, zsh, etc.) expand wildcards before passing them to programs. When you type `**/*.py`, the shell expands it to a list of files. Quotes `'**/*.py'` tell the shell to pass the pattern literally to mergefile, which then handles the wildcard expansion itself.

### Q: What's the difference between `*.py` and `**/*.py`?
**A**: `*.py` matches Python files in the current directory only. `**/*.py` matches Python files in the current directory and all subdirectories (recursive).

### Q: Can I exclude multiple patterns?
**A**: Yes! Use `--exclude` multiple times: `--exclude 'tests/' --exclude '*.tmp' --exclude 'node_modules/'`

### Q: What happens if a file can't be read?
**A**: mergefile shows a warning and skips that file, continuing with the rest. The error is noted in the output file.

### Q: Is mergefile safe to use?
**A**: Yes! mergefile has multiple safety features:
- Won't overwrite files without `--force`
- Prevents output file from being in input files
- Shows warnings for problematic files
- Continues processing even if some files fail

### Q: Can I use mergefile in scripts?
**A**: Absolutely! mergefile is designed for both interactive use and scripting. It provides clear exit codes and machine-readable output when using XML format.

### Q: How do I get help?
**A**: Use `mergefile --help` for full command reference, or check the examples in this README.

