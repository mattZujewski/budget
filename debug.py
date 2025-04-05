#!/usr/bin/env python
"""
Debug script to verify that all components of the budget app are working correctly.
Helps identify import or configuration issues before running the main application.
"""
import os
import sys
import importlib
import inspect
import traceback

# Add project root to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'configs'))

def check_module(module_name):
    """Try to import a module and report its status."""
    try:
        # Try importing from configs first
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
    except ImportError as e:
        try:
            # Then try importing from budget
            module = importlib.import_module(f'budget.{module_name}')
            print(f"✅ Successfully imported budget.{module_name}")
        except ImportError as import_error:
            # Detailed error reporting
            print(f"❌ Failed to import {module_name}")
            print("Error Details:")
            print(f"  Import Error: {import_error}")
            
            # Get traceback information
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            # Extract traceback details
            tb_details = traceback.extract_tb(exc_traceback)
            for filename, lineno, func, text in tb_details:
                print(f"  File: {filename}, Line: {lineno}, in {func}")
                if text:
                    print(f"    {text}")
            
            return False
    except Exception as e:
        print(f"❌ Error checking {module_name}")
        print("Error Details:")
        print(f"  Exception: {e}")
        
        # Get traceback information
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        # Extract traceback details
        tb_details = traceback.extract_tb(exc_traceback)
        for filename, lineno, func, text in tb_details:
            print(f"  File: {filename}, Line: {lineno}, in {func}")
            if text:
                print(f"    {text}")
        
        return False

    # Print classes in the module
    classes = [name for name, obj in inspect.getmembers(module, inspect.isclass) 
               if obj.__module__ == module.__name__]
    if classes:
        print(f"   Classes: {', '.join(classes)}")
    
    return True

def check_directory(dir_path):
    """Check if a directory exists and is writable."""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            print(f"✅ Created directory {dir_path}")
        except Exception as e:
            print(f"❌ Could not create directory {dir_path}")
            print(f"  Error: {e}")
            print(f"  Error Type: {type(e).__name__}")
            
            # Get traceback information
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb_details = traceback.extract_tb(exc_traceback)
            for filename, lineno, func, text in tb_details:
                print(f"  File: {filename}, Line: {lineno}, in {func}")
                if text:
                    print(f"    {text}")
            
            return False
    
    if os.access(dir_path, os.W_OK):
        print(f"✅ Directory {dir_path} exists and is writable")
        return True
    else:
        print(f"❌ Directory {dir_path} exists but is not writable")
        print(f"  Current Permissions: {oct(os.stat(dir_path).st_mode)[-3:]}")
        return False

def check_env_file():
    """Check if .env file exists and can be read."""
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                lines = f.readlines()
                print(f"✅ Found .env file with {len(lines)} lines")
            return True
        except Exception as e:
            print(f"❌ Could not read .env file")
            print(f"  Error: {e}")
            print(f"  Error Type: {type(e).__name__}")
            
            # Get traceback information
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb_details = traceback.extract_tb(exc_traceback)
            for filename, lineno, func, text in tb_details:
                print(f"  File: {filename}, Line: {lineno}, in {func}")
                if text:
                    print(f"    {text}")
            
            return False
    else:
        print("❌ .env file not found")
        return False

def main():
    """Run diagnostic checks on the budget application."""
    print("🔍 Budget App Diagnostics\n")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check current directory and structure
    print(f"Current directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    
    # Print Python path for debugging
    print("\nPython Path:")
    for path in sys.path:
        print(path)
    
    # Check if budget package is importable
    print("\n🧪 Testing imports:")
    modules_ok = True
    modules_ok &= check_module('budget')
    #modules_ok &= check_module('config')
    modules_ok &= check_module('logger')
    modules_ok &= check_module('parser')
    modules_ok &= check_module('categorize')
    modules_ok &= check_module('ai_tools')
    
    # Check directories
    print("\n🧪 Testing directories:")
    dirs_ok = True
    dirs_ok &= check_directory('data')
    dirs_ok &= check_directory('logs')
    
    # Check .env file
    print("\n🧪 Testing configuration:")
    env_ok = check_env_file()
    
    # Summary
    print("\n📊 Diagnostic Summary:")
    if modules_ok:
        print("✅ All modules imported successfully")
    else:
        print("❌ Some modules failed to import")
    
    if dirs_ok:
        print("✅ All directories are available and writable")
    else:
        print("❌ Some directories are missing or not writable")
    
    if env_ok:
        print("✅ Configuration (.env) file is available")
    else:
        print("❌ Configuration (.env) file is missing or unreadable")
    
    # Overall status
    print("\n📝 Conclusion:")
    if modules_ok and dirs_ok and env_ok:
        print("✅ Budget App appears to be correctly set up")
        return 0
    else:
        print("❌ Budget App has configuration issues that need to be fixed")
        return 1

if __name__ == "__main__":
    sys.exit(main())