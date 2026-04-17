# MergeFile

A powerful file merging tool with wildcard support that can combine multiple files into XML or Markdown format, especially suitable for preparing input documents for Large Language Models (LLM).

[中文文档](README_zh.md) | [English Documentation](README.md)

## Features

- 🚀 **Wildcard Support**: Supports wildcard patterns like `*.py`, `**/*.md`, easily matching nested directories
- 📝 **Dual Format Output**: Supports both XML and Markdown output formats (default: Markdown)
- 🏷️ **Smart Language Detection**: Automatically identifies code language by file extension (Markdown format)
- 🔒 **Safety Protection**: Prevents output file from being in the input file list, avoiding data loss
- ⚡ **Force Overwrite**: Use `-f` or `--force` option to overwrite existing output files
- 🚫 **Exclusion Patterns**: Supports `--exclude` option to exclude specific files or directories
- 🔍 **Recursion Control**: Recursive search by default, can be disabled with `--no-recursive`
- 💬 **Custom Header**: Supports adding custom header comments
- 📊 **Detailed Output**: Shows processed file list and statistics
- 🛡️ **Error Recovery**: Skips non-existent or unreadable files, continues processing others
- 📦 **Easy Installation**: Supports pip installation and development mode installation

## Installation

### Install from Source (Recommended)

This project uses modern `pyproject.toml` configuration (PEP 517/518). Installation is straightforward:

```bash
# Clone the repository
git clone https://github.com/gseismic/mergefile.py
cd mergefile.py

# Install using pyproject.toml (modern Python packaging)
pip install .
```

### Development Mode Installation

For development, install in editable mode with development dependencies:

```bash
# Clone the repository and enter directory
git clone https://github.com/gseismic/mergefile.py
cd mergefile.py

# Development mode installation (editable)
pip install -e .

# Install development dependencies from pyproject.toml
pip install -e ".[dev]"
```

## Usage

### Basic Syntax

```bash
mergefile [options] <file_patterns...> -o <output_file>
```

### Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | **Required**, specifies output file path |
| `--format` | | Output format: `xml` or `markdown` (default: `markdown`) |
| `--header` | | Add custom header comment |
| `--force` | `-f` | Force overwrite of existing output file |
| `--exclude` | | Exclude files matching pattern (can be used multiple times) |
| `--no-recursive` | | Disable recursive directory search |
| `--version` | | Display version information |
| `--help` | `-h` | Display help information |

### Wildcard Pattern Examples

#### Basic Wildcards
```bash
# Merge all Python files in current directory
mergefile *.py -o all_python.xml

# Merge all Python files in src directory
mergefile src/*.py -o src_code.md

# Merge multiple file types
mergefile *.py *.md *.json -o combined.xml
```

#### Recursive Wildcards (`**`)
```bash
# Recursively merge all Python files (including subdirectories)
mergefile **/*.py -o all_code.xml

# Merge all files in src directory and its subdirectories
mergefile src/**/* -o src_all.md

# Merge all Python files in specific directories
mergefile src/**/*.py tests/**/*.py -o codebase.xml
```

#### Exclusion Patterns
```bash
# Merge all Python files, excluding test files
mergefile **/*.py --exclude tests/ --exclude *_test.py -o source_only.md

# Merge configuration files, excluding temporary files
mergefile config/**/* --exclude *.tmp --exclude *.bak -o configs.xml
```

### Safety Protection Examples

```bash
# Safety protection: output file cannot be in input files
mergefile *.py -o output.py  # Error: output_file cannot be in input_files

# Force overwrite existing file
mergefile *.py -o existing.xml --force  # Overwrites existing file

# Without --force, it will error
mergefile *.py -o existing.xml  # Error: Output file exists, use -f or --force option to force overwrite
```

### Complete Examples

#### Example 1: Merge Entire Project Source Code
```bash
mergefile \
  --header "Project Source Code - Generated on $(date)" \
  --format xml \
  **/*.py **/*.js **/*.html **/*.css \
  --exclude node_modules/ \
  --exclude __pycache__/ \
  --exclude *.min.js \
  -o project_documentation.xml
```

#### Example 2: Prepare Training Data for LLM
```bash
mergefile \
  --header "Code Dataset - Python and JavaScript" \
  --format markdown \
  src/**/*.py \
  static/**/*.js \
  --exclude tests/ \
  --exclude vendor/ \
  -o llm_training_data.md
```

#### Example 3: Merge Configuration Files
```bash
mergefile \
  --header "Application Configuration Collection" \
  config/*.json \
  config/*.yaml \
  config/*.toml \
  .env.example \
  --force \
  -o all_configs.md
```

## Output Formats

### Markdown Format (Default)

Markdown format is human-readable, automatically detects code languages and adds syntax highlighting:

```markdown
# Description

Project Source Code - Generated on 2024-01-01

## File List

Merged 3 files:

1. `src/main.py`
2. `src/utils/helper.py`
3. `config/settings.yaml`

## File Contents

File contents are detailed below:

---

### main.py

File path: `src/main.py`

```python
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
```

---
```

### XML Format

XML format provides structured data, suitable for machine processing, using CDATA blocks to avoid XML parsing issues:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<file_documentation>
  <description>
    Project Source Code - Generated on 2024-01-01
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

## Supported File Types

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

## Error Handling

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

## Development

### Project Structure
```
mergefile.py/
├── mergefile.py          # Main program
├── pyproject.toml        # Project configuration and dependencies
├── setup.py             # Traditional installation script (compatibility)
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
```

### Building and Publishing
```bash
# Build distribution packages
python -m build

# Upload to PyPI
twine upload dist/*
```

## License

MIT License - You are free to use, modify, and distribute this software. 
Feel free to copy the `mergefile.py` script directly into your own projects and use it as needed.

## Contributing

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

## Version History

- **v1.0.0** (Initial version) - Basic file merging functionality
- **v1.1.0** (Current version) - Added wildcard support, safety protection, force overwrite, and other advanced features

Use `mergefile --version` to view current version.