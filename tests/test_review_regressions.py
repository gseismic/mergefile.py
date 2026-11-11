import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import mergefile


@pytest.mark.parametrize("name", ["result_index.json", "result_index.md"])
def test_split_checks_existing_indexes_before_writing(tmp_path, name):
    source = tmp_path / "source.txt"
    source.write_text("source", encoding="utf-8")
    index = tmp_path / name
    index.write_text("keep this", encoding="utf-8")

    with pytest.raises(ValueError, match="Output file already exists"):
        mergefile.merge_files([str(source)], str(tmp_path / "result.md"),
                              format_type="markdown", split=True)

    assert index.read_text(encoding="utf-8") == "keep this"
    assert not (tmp_path / "result_1.md").exists()


@pytest.mark.parametrize("name", ["result_1.md", "result_index.json", "result_index.md"])
@pytest.mark.parametrize("force", [False, True])
def test_split_never_overwrites_inputs(tmp_path, name, force):
    source = tmp_path / name
    source.write_text("original input", encoding="utf-8")

    with pytest.raises(ValueError, match="output_file cannot be in input_files"):
        mergefile.merge_files([str(source)], str(tmp_path / "result.md"),
                              format_type="markdown", split=True, force=force)

    assert source.read_text(encoding="utf-8") == "original input"
    assert not (tmp_path / "result_2.md").exists()


@pytest.mark.parametrize("link_type", ["symbolic", "hard"])
def test_force_does_not_overwrite_an_aliased_input(tmp_path, link_type):
    source = tmp_path / "source.txt"
    source.write_text("original input", encoding="utf-8")
    output = tmp_path / "output.md"
    try:
        if link_type == "symbolic":
            output.symlink_to(source)
        else:
            os.link(str(source), str(output))
    except OSError as exc:
        pytest.skip("links unavailable: {}".format(exc))

    with pytest.raises(ValueError, match="output_file cannot be in input_files"):
        mergefile.merge_files([str(source)], str(output), format_type="markdown", force=True)

    assert source.read_text(encoding="utf-8") == "original input"


def test_split_rejects_output_destinations_that_alias_each_other(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("source", encoding="utf-8")
    alias = tmp_path / "result_index.json"
    try:
        alias.symlink_to("result_1.md")
    except OSError as exc:
        pytest.skip("symbolic links unavailable: {}".format(exc))

    with pytest.raises(ValueError, match="Output files refer to the same file"):
        mergefile.merge_files([str(source)], str(tmp_path / "result.md"),
                              format_type="markdown", split=True, force=True)

    assert not (tmp_path / "result_1.md").exists()


def test_force_can_overwrite_unrelated_indexes(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("source", encoding="utf-8")
    for name in ("result_index.json", "result_index.md"):
        (tmp_path / name).write_text("old output", encoding="utf-8")

    mergefile.merge_files([str(source)], str(tmp_path / "result.md"),
                          format_type="markdown", split=True, force=True)

    assert json.loads((tmp_path / "result_index.json").read_text())["metadata"]["total_files"] == 1
    assert "old output" not in (tmp_path / "result_index.md").read_text()


@pytest.mark.parametrize("exclude", ["tests/", "tests/**/*.py"])
def test_exclusions_work_with_absolute_input_and_relative_patterns(tmp_path, monkeypatch, exclude):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "private.py").write_text("EXCLUDED", encoding="utf-8")
    (tmp_path / "tests_extra").mkdir()
    (tmp_path / "tests_extra" / "public.py").write_text("INCLUDED", encoding="utf-8")

    mergefile.merge_files([str(tmp_path / "**" / "*.py")], "result.md",
                          format_type="markdown", exclude_patterns=[exclude])

    output = (tmp_path / "result.md").read_text(encoding="utf-8")
    assert "EXCLUDED" not in output
    assert "INCLUDED" in output


def test_directory_exclusion_applies_to_symlinked_files_inside_it(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "outside.py").write_text("included", encoding="utf-8")
    try:
        (tmp_path / "tests" / "link.py").symlink_to(tmp_path / "outside.py")
    except OSError as exc:
        pytest.skip("symbolic links unavailable: {}".format(exc))

    mergefile.merge_files(["**/*.py"], "result.md", format_type="markdown",
                          exclude_patterns=["tests/"])

    output = (tmp_path / "result.md").read_text(encoding="utf-8")
    assert "outside.py" in output
    assert "tests/link.py" not in output


@pytest.mark.parametrize("format_type, extension", [("markdown", "md"), ("xml", "xml")])
def test_line_ranges_and_totals_after_decoding_failure(tmp_path, monkeypatch, format_type, extension):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a_bad.txt").write_bytes(b"\xff")
    (tmp_path / "z_good.txt").write_text("GOOD\n", encoding="utf-8")
    mergefile.merge_files(["*.txt"], "result." + extension, format_type=format_type,
                          split=True, max_files=1, language="en")

    index = json.loads((tmp_path / "result_index.json").read_text(encoding="utf-8"))
    chunk = index["chunks"][0]
    lines = (tmp_path / chunk["chunk_file"]).read_text(encoding="utf-8").splitlines()
    assert chunk["line_count"] == len(lines)
    assert index["metadata"]["total_lines"] == len(lines)
    for entry in index["files"]:
        name = Path(entry["original_path"]).name
        if format_type == "markdown":
            start = next(i for i, line in enumerate(lines, 1) if line.startswith("### " + name + " "))
            assert lines[entry["end_line"] - 1].startswith(("```", "Encoding error"))
        else:
            start = next(i for i, line in enumerate(lines, 1) if line.startswith('    <file name="' + name + '"'))
            assert lines[entry["end_line"] - 1].strip() == "</file>"
        assert entry["start_line"] == start
        assert entry["line_count"] == entry["end_line"] - start + 1


def test_xml_escapes_attributes_and_embedded_cdata_terminators(tmp_path):
    source = tmp_path / 'a"b.txt'
    text = 'first ]]> second ]]> third\n'
    source.write_text(text, encoding="utf-8")
    output = tmp_path / "result.xml"

    mergefile.merge_files([str(source)], str(output), header="a < b & c", format_type="xml")

    root = ET.parse(str(output)).getroot()
    item = root.find("./file_list/item")
    element = root.find("./file_contents/file")
    assert item.attrib["path"] == str(source)
    assert element.attrib["name"] == source.name
    assert text in element.text


def test_xml_reports_characters_that_xml_cannot_represent(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("before\x00after", encoding="utf-8")
    output = tmp_path / "result.xml"

    mergefile.merge_files([str(source)], str(output), format_type="xml", language="en")

    root = ET.parse(str(output)).getroot()
    assert "invalid in XML" in root.find("./file_contents/file/error").text


def test_markdown_keeps_nested_code_fences_inside_the_source_block(tmp_path):
    source = tmp_path / "README.md"
    content = "intro\n```python\nprint(42)\n```\n````\n# SOURCE HEADING\n"
    source.write_text(content, encoding="utf-8")
    output = tmp_path / "result.md"

    mergefile.merge_files([str(source)], str(output), format_type="markdown")

    lines = output.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("```") and line.endswith("markdown"))
    fence = lines[start][:-len("markdown")]
    end = lines.index(fence, start + 1)
    assert "\n".join(lines[start + 1:end]) + "\n" == content


def test_split_balances_many_files_in_the_same_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    expected = {"{:02d}.txt".format(i) for i in range(12)}
    for name in expected:
        (tmp_path / name).write_text("same size\n", encoding="utf-8")

    mergefile.merge_files(["*.txt"], "result.md", format_type="markdown",
                          split=True, max_files=3)

    index = json.loads((tmp_path / "result_index.json").read_text(encoding="utf-8"))
    assert index["metadata"]["total_chunks"] == 3
    assert {entry["original_path"] for entry in index["files"]} == expected
    assert [chunk["file_count"] for chunk in index["chunks"]] == [4, 4, 4]


def test_split_accepts_mixed_relative_and_absolute_inputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "relative.txt").write_text("relative", encoding="utf-8")
    (tmp_path / "absolute.txt").write_text("absolute", encoding="utf-8")
    mergefile.merge_files(["relative.txt", str(tmp_path / "absolute.txt")], "result.md",
                          format_type="markdown", split=True)
    index = json.loads((tmp_path / "result_index.json").read_text(encoding="utf-8"))
    assert {entry["original_path"] for entry in index["files"]} == {
        "relative.txt", str(tmp_path / "absolute.txt")
    }


@pytest.mark.parametrize("value", [0, -1, 1.5, "3", True])
def test_split_rejects_invalid_max_files_before_writing(tmp_path, value):
    source = tmp_path / "source.txt"
    source.write_text("source", encoding="utf-8")
    with pytest.raises(ValueError, match="positive integer"):
        mergefile.merge_files([str(source)], str(tmp_path / "result.md"),
                              split=True, max_files=value)
    assert not (tmp_path / "result_1.md").exists()


def test_save_language_without_merging(tmp_path):
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    script = Path(mergefile.__file__).resolve()
    result = subprocess.run([sys.executable, str(script), "--lang", "zh", "--save-lang"],
                            env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / ".mergefile.json").read_text())["language"] == "zh"


def test_cli_rejects_invalid_max_files(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("source", encoding="utf-8")
    result = subprocess.run([sys.executable, str(Path(mergefile.__file__).resolve()),
                             str(source), "-o", str(tmp_path / "result.md"),
                             "--split", "--max-files", "0"],
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert "positive integer" in result.stderr
    assert not (tmp_path / "result_1.md").exists()


def test_config_save_failure_is_not_reported_as_success(tmp_path, monkeypatch):
    monkeypatch.setattr(mergefile, "CONFIG_FILE", tmp_path / "missing" / "config.json")
    with pytest.raises(OSError):
        mergefile.save_config({"language": "zh"})


def test_existing_wildcard_test_propagates_assertion_failures(monkeypatch):
    from tests import test_wildcard

    def fail(*args, **kwargs):
        raise AssertionError("intentional failure")

    monkeypatch.setattr(mergefile, "expand_file_patterns", fail)
    with pytest.raises(AssertionError, match="intentional failure"):
        test_wildcard.test_wildcard_patterns()
