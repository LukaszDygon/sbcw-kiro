#!/usr/bin/env python3
"""
Comprehensive test runner for SoftBankCashWire backend
"""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=False)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"\n{description} completed in {duration:.2f} seconds")
    
    if result.returncode == 0:
        print(f"✅ {description} PASSED")
    else:
        print(f"❌ {description} FAILED")
    
    return result.returncode == 0

def run_unit_tests():
    """Run unit tests"""
    return run_command(
        "python -m pytest tests/test_*_service.py tests/test_models.py -m 'not slow' -v",
        "Unit Tests"
    )

def run_integration_tests():
    """Run integration tests"""
    return run_command(
        "python -m pytest tests/test_api_integration.py tests/test_*_api.py -v",
        "API Integration Tests"
    )

def run_security_tests():
    """Run security tests"""
    return run_command(
        "python -m pytest tests/test_security.py -v",
        "Security Tests"
    )

def run_performance_tests():
    """Run performance tests"""
    return run_command(
        "python -m pytest tests/test_performance.py -v -s",
        "Performance Tests"
    )

def run_coverage_tests():
    """Run tests with coverage reporting"""
    return run_command(
        "python -m pytest --cov=services --cov=models --cov=api --cov-report=html --cov-report=term-missing --cov-fail-under=90",
        "Coverage Tests"
    )

def run_all_tests():
    """Run all test suites"""
    results = []
    
    print("🚀 Starting comprehensive test suite for SoftBankCashWire backend")
    
    # Run different test categories
    test_suites = [
        ("Unit Tests", run_unit_tests),
        ("Integration Tests", run_integration_tests),
        ("Security Tests", run_security_tests),
        ("Performance Tests", run_performance_tests),
    ]
    
    for suite_name, test_function in test_suites:
        print(f"\n🔄 Starting {suite_name}...")
        success = test_function()
        results.append((suite_name, success))
        
        if not success:
            print(f"⚠️  {suite_name} failed, but continuing with other tests...")
    
    # Generate final report
    print(f"\n{'='*80}")
    print("📊 FINAL TEST REPORT")
    print(f"{'='*80}")
    
    passed = 0
    failed = 0
    
    for suite_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{suite_name:<25} {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Summary: {passed} passed, {failed} failed out of {len(results)} test suites")
    
    if failed == 0:
        print("🎉 All test suites passed!")
        return True
    else:
        print(f"⚠️  {failed} test suite(s) failed")
        return False

def run_quick_tests():
    """Run quick smoke tests"""
    return run_command(
        "python -m pytest tests/test_models.py tests/test_auth_service.py tests/test_transaction_service.py -v --tb=short",
        "Quick Smoke Tests"
    )

def run_specific_test(test_path):
    """Run a specific test file or test function"""
    return run_command(
        f"python -m pytest {test_path} -v",
        f"Specific Test: {test_path}"
    )

def setup_test_environment():
    """Set up test environment"""
    print("🔧 Setting up test environment...")
    
    # Set test environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    # Install test dependencies if needed
    requirements_file = Path('requirements.txt')
    if requirements_file.exists():
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      capture_output=True)
    
    print("✅ Test environment ready")

def main():
    parser = argparse.ArgumentParser(description='Run SoftBankCashWire backend tests')
    parser.add_argument('--suite', choices=['unit', 'integration', 'security', 'performance', 'coverage', 'quick', 'all'], 
                       default='all', help='Test suite to run')
    parser.add_argument('--test', help='Specific test file or function to run')
    parser.add_argument('--setup', action='store_true', help='Set up test environment')
    parser.add_argument('--no-setup', action='store_true', help='Skip test environment setup')
    
    args = parser.parse_args()
    
    # Setup test environment unless explicitly skipped
    if not args.no_setup:
        setup_test_environment()
    
    # Run specific test if provided
    if args.test:
        success = run_specific_test(args.test)
        sys.exit(0 if success else 1)
    
    # Run selected test suite
    if args.suite == 'unit':
        success = run_unit_tests()
    elif args.suite == 'integration':
        success = run_integration_tests()
    elif args.suite == 'security':
        success = run_security_tests()
    elif args.suite == 'performance':
        success = run_performance_tests()
    elif args.suite == 'coverage':
        success = run_coverage_tests()
    elif args.suite == 'quick':
        success = run_quick_tests()
    elif args.suite == 'all':
        success = run_all_tests()
    else:
        print(f"Unknown test suite: {args.suite}")
        sys.exit(1)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()