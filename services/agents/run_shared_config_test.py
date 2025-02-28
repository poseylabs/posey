#!/usr/bin/env python
"""
Simple script to test the shared configuration loading functionality
"""
import os
import sys
import importlib

def main():
    # Add the current directory to the path
    sys.path.insert(0, os.getcwd())
    
    # Import the test module
    try:
        test_module = importlib.import_module("tests.test_shared_config")
        
        # Run the test
        import unittest
        suite = unittest.TestLoader().loadTestsFromModule(test_module)
        result = unittest.TextTestRunner().run(suite)
        
        # Report the result
        if result.wasSuccessful():
            print("\nAll tests passed! Shared configuration loading is working correctly.")
            return 0
        else:
            print("\nSome tests failed. Shared configuration loading is not working correctly.")
            return 1
            
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
