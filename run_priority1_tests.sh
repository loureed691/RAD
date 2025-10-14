#!/bin/bash
echo "=========================================================================="
echo "PRIORITY 1 - COMPREHENSIVE TEST SUITE"
echo "=========================================================================="
echo ""

echo "Test 1: Guardrails & Kill Switch"
echo "----------------------------------------------------------------------"
python3 test_priority1_guardrails.py
TEST1=$?
echo ""

echo "Test 2: Fees & Funding"
echo "----------------------------------------------------------------------"
python3 test_fees_and_funding.py
TEST2=$?
echo ""

echo "Test 3: Integration"
echo "----------------------------------------------------------------------"
python3 test_priority1_integration.py
TEST3=$?
echo ""

echo "=========================================================================="
echo "FINAL RESULTS"
echo "=========================================================================="
if [ $TEST1 -eq 0 ] && [ $TEST2 -eq 0 ] && [ $TEST3 -eq 0 ]; then
    echo "✅ ALL PRIORITY 1 TESTS PASSED"
    echo ""
    echo "Summary:"
    echo "  ✓ Guardrails tests: 6/6 passing"
    echo "  ✓ Fees & funding tests: 5/5 passing"
    echo "  ✓ Integration test: PASSED"
    echo ""
    echo "Total: 12 test cases + integration verification"
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    exit 1
fi
