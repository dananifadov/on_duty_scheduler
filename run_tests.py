#!/usr/bin/env python3
"""
Test runner for on-duty scheduler
"""
import unittest
import sys
from pathlib import Path

def run_all_tests():
    """Run all tests in the tests directory"""
    # Add src to path
    src_path = Path(__file__).parent / 'src'
    sys.path.insert(0, str(src_path))
    
    # Discover and run tests
    test_dir = Path(__file__).parent / 'tests'
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
    
    return len(result.failures) + len(result.errors) == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

