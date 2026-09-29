import pytest
import os
import glob

def test_no_hardcoded_secrets():
    # Scan for common secret keywords in src
    keywords = ['api_key', 'password', 'secret', 'token']
    src_files = glob.glob('src/**/*.py', recursive=True)
    for f in src_files:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read().lower()
            for kw in keywords:
                # Naive check, ensure we don't have hardcoded secrets
                assert f"{kw} =" not in content

def test_no_subprocess_usage():
    # Ensure no arbitrary command execution is used
    src_files = glob.glob('src/**/*.py', recursive=True)
    for f in src_files:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            assert "import subprocess" not in content
            assert "os.system" not in content
            assert "os.popen" not in content
            assert "eval(" not in content
            assert "exec(" not in content
