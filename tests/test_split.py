import os
import json
import shutil
import tempfile
import pytest
from mergefile import merge_files

@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing"""
    temp_dir = tempfile.mkdtemp()
    
    # Create subdirectories
    os.mkdir(os.path.join(temp_dir, "src"))
    os.mkdir(os.path.join(temp_dir, "tests"))
    os.mkdir(os.path.join(temp_dir, "docs"))
    
    # Create files
    with open(os.path.join(temp_dir, "src", "a.py"), "w") as f:
        f.write("print('a')\n" * 5)
    with open(os.path.join(temp_dir, "src", "b.py"), "w") as f:
        f.write("print('b')\n" * 5)
    with open(os.path.join(temp_dir, "tests", "test_a.py"), "w") as f:
        f.write("def test_a(): pass\n")
    with open(os.path.join(temp_dir, "docs", "readme.md"), "w") as f:
        f.write("# README\n")
    with open(os.path.join(temp_dir, "main.py"), "w") as f:
        f.write("import src.a\n")
        
    yield temp_dir
    
    shutil.rmtree(temp_dir)

def test_split_merge(temp_project):
    """Test the --split functionality"""
    output_base = os.path.join(temp_project, "merged.md")
    index_file = os.path.join(temp_project, "merged_index.json")
    
    # Patterns to match all files
    patterns = [os.path.join(temp_project, "**", "*")]
    
    # Run merge_files with split=True
    # We need to filter out directories manually because expand_file_patterns handles it
    # but for simplicity we just pass the patterns
    merge_files(
        patterns,
        output_base,
        split=True,
        max_files=9,
        force=True,
        recursive=True,
        format_type="markdown"
    )
    
    # Check if index file exists
    assert os.path.exists(index_file)
    
    with open(index_file, "r", encoding="utf-8") as f:
        index_data = json.load(f)
        
    # Verify metadata
    assert index_data["metadata"]["total_files"] >= 5
    assert index_data["metadata"]["total_chunks"] > 1
    
    # Verify that files are distributed across chunks
    merged_files = set()
    for entry in index_data["files"]:
        merged_files.add(entry["merged_file"])
        
        # Verify output file exists
        assert os.path.exists(os.path.join(temp_project, entry["merged_file"]))
        
        # Verify line ranges are valid
        assert entry["start_line"] > 0
        assert entry["end_line"] >= entry["start_line"]

def test_split_max_files(temp_project):
    """Test the --max-files constraint"""
    output_base = os.path.join(temp_project, "merged_limited.md")
    
    patterns = [os.path.join(temp_project, "**", "*")]
    
    # Set max_files to 2
    merge_files(
        patterns,
        output_base,
        split=True,
        max_files=2,
        force=True,
        recursive=True
    )
    
    index_file = os.path.join(temp_project, "merged_limited_index.json")
    with open(index_file, "r", encoding="utf-8") as f:
        index_data = json.load(f)
        
    assert index_data["metadata"]["total_chunks"] <= 2
