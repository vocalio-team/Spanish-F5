#!/usr/bin/env python3
"""Analyze code coverage for the entire Spanish-F5 project."""

import os
import sys
from pathlib import Path
from collections import defaultdict

def count_lines(file_path):
    """Count lines in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Count non-empty, non-comment lines
            code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
            return len(lines), len(code_lines)
    except:
        return 0, 0

def analyze_module(module_path):
    """Analyze a module for test coverage."""
    py_files = list(Path(module_path).rglob("*.py"))
    py_files = [f for f in py_files if '__pycache__' not in str(f)]
    
    stats = {
        'files': [],
        'total_lines': 0,
        'total_code_lines': 0,
    }
    
    for py_file in py_files:
        total, code = count_lines(py_file)
        rel_path = os.path.relpath(py_file, 'src/f5_tts')
        stats['files'].append({
            'path': rel_path,
            'total_lines': total,
            'code_lines': code
        })
        stats['total_lines'] += total
        stats['total_code_lines'] += code
    
    return stats

def check_test_exists(module_name):
    """Check if tests exist for a module."""
    test_file = f"tests/test_{module_name}.py"
    return os.path.exists(test_file)

# Analyze project
src_path = "src/f5_tts"
modules = {}

# Group by top-level modules
for item in os.listdir(src_path):
    item_path = os.path.join(src_path, item)
    if os.path.isdir(item_path) and not item.startswith('__'):
        modules[item] = analyze_module(item_path)
    elif item.endswith('.py') and item != '__init__.py':
        # Root level files
        if 'root' not in modules:
            modules['root'] = {'files': [], 'total_lines': 0, 'total_code_lines': 0}
        total, code = count_lines(item_path)
        modules['root']['files'].append({
            'path': item,
            'total_lines': total,
            'code_lines': code
        })
        modules['root']['total_lines'] += total
        modules['root']['total_code_lines'] += code

# Print analysis
print("=" * 80)
print("SPANISH-F5 PROJECT CODE COVERAGE ANALYSIS")
print("=" * 80)
print()

total_files = 0
total_lines = 0
total_code = 0
tested_modules = 0
untested_modules = 0

print(f"{'Module':<20} {'Files':<8} {'Lines':<10} {'Code':<10} {'Tests':<10}")
print("-" * 80)

for module_name, stats in sorted(modules.items()):
    has_tests = "✅" if check_test_exists(module_name) else "❌"
    if check_test_exists(module_name):
        tested_modules += 1
    else:
        untested_modules += 1
    
    total_files += len(stats['files'])
    total_lines += stats['total_lines']
    total_code += stats['total_code_lines']
    
    print(f"{module_name:<20} {len(stats['files']):<8} {stats['total_lines']:<10} "
          f"{stats['total_code_lines']:<10} {has_tests:<10}")

print("-" * 80)
print(f"{'TOTAL':<20} {total_files:<8} {total_lines:<10} {total_code:<10} "
      f"{tested_modules}/{len(modules):<10}")
print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total modules: {len(modules)}")
print(f"Tested modules: {tested_modules}")
print(f"Untested modules: {untested_modules}")
print(f"Coverage: {(tested_modules/len(modules)*100):.1f}%")
print()

# Detailed breakdown
print("=" * 80)
print("UNTESTED MODULES (Need test coverage)")
print("=" * 80)

for module_name, stats in sorted(modules.items()):
    if not check_test_exists(module_name):
        print(f"\n{module_name}:")
        for file_info in sorted(stats['files'], key=lambda x: x['code_lines'], reverse=True):
            print(f"  - {file_info['path']:<40} ({file_info['code_lines']} code lines)")

print()
print("=" * 80)
print("TESTED MODULES")
print("=" * 80)

for module_name in sorted(modules.keys()):
    if check_test_exists(module_name):
        print(f"✅ {module_name}")

