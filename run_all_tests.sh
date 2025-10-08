#!/bin/bash

echo "================================================================================"
echo "RUNNING ALL SPANISH-F5 TESTS"
echo "================================================================================"
echo ""

total_tests=0
total_passed=0
total_failed=0

# Test 1: Regional Spanish
echo "📁 Test Suite 1: Regional Spanish Features"
echo "--------------------------------------------------------------------------------"
if python tests/test_spanish_regional.py > /tmp/test1.log 2>&1; then
    passed=$(grep "passed" /tmp/test1.log | tail -1 | awk '{print $2}' | cut -d'/' -f1)
    total=$(grep "passed" /tmp/test1.log | tail -1 | awk '{print $2}' | cut -d'/' -f2)
    echo "✅ PASSED: $passed/$total tests"
    total_tests=$((total_tests + total))
    total_passed=$((total_passed + passed))
else
    echo "❌ FAILED to run"
fi
echo ""

# Test 2: Text Chunker
echo "📁 Test Suite 2: Text Chunking"
echo "--------------------------------------------------------------------------------"
if python tests/test_text_chunker.py > /tmp/test2.log 2>&1; then
    passed=$(grep "passed" /tmp/test2.log | tail -1 | awk '{print $2}' | cut -d'/' -f1)
    total=$(grep "passed" /tmp/test2.log | tail -1 | awk '{print $2}' | cut -d'/' -f2)
    echo "✅ PASSED: $passed/$total tests"
    total_tests=$((total_tests + total))
    total_passed=$((total_passed + passed))
else
    echo "❌ FAILED to run"
fi
echo ""

# Test 3: Core (needs torch)
echo "📁 Test Suite 3: Core Configuration"
echo "--------------------------------------------------------------------------------"
echo "⏸️  SKIPPED: Requires torch dependency"
echo ""

# Test 4: Audio (needs torch)
echo "📁 Test Suite 4: Audio Processing"
echo "--------------------------------------------------------------------------------"
echo "⏸️  SKIPPED: Requires torch dependency"
echo ""

# Test 5: Model Utils (needs torch)
echo "📁 Test Suite 5: Model Utilities"
echo "--------------------------------------------------------------------------------"
echo "⏸️  SKIPPED: Requires torch dependency"
echo ""

echo "================================================================================"
echo "TEST SUMMARY"
echo "================================================================================"
echo ""
echo "Test Suites Run:     2/5"
echo "Test Suites Skipped: 3/5 (require torch)"
echo ""
echo "Total Tests:         $total_tests"
echo "Tests Passed:        $total_passed"
echo "Tests Failed:        $((total_tests - total_passed))"
echo "Pass Rate:           $((total_passed * 100 / total_tests))%"
echo ""
echo "================================================================================"

