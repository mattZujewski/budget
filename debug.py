#!/usr/bin/env python
"""
Debug script to verify that all components of the budget app are working correctly.
Helps identify import or configuration issues before running the main application.
"""
import os
import sys
import importlib
import inspect

def check_module(module_name):
    """Try to import a module and report its status."""
    try:
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        
        # Print classes in the module
        classes = [name for name, obj in inspect.getmembers(module, inspect.isclass) 
                   if obj.__module__ == module.__name__]
        if classes:
            print(f"   Classes: {', '.join(classes)}")
        
        return True
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking {module_name}: {e}")
        return False

def check_directory(dir_path):
    """Check if a directory exists and is writable."""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            print(f"✅ Created directory {dir_path}")
        except Exception as e:
            print(f"❌ Could not create directory {dir_path}: {e}")
            return False
    
    if os.access(dir_path, os.W_OK):
        print(f"✅ Directory {dir_path} exists and is writable")
        return True
    else:
        print(f"❌ Directory {dir_path} exists but is not writable")
        return False

def check_env_file():
    """Check if .env file exists and can be read."""
    if os.path.exists('.env'):
        try:
            with open('.env', 'r') as f:
                lines = f.readlines()
                print(f"✅ Found .env file with {len(lines)} lines")
            return True
        except Exception as e:
            print(f"❌ Could not read .env file: {e}")
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
    
    # Check if budget package is importable
    print("\n🧪 Testing imports:")
    modules_ok = True
    modules_ok &= check_module('budget')
    modules_ok &= check_module('budget.config')
    modules_ok &= check_module('budget.logger')
    modules_ok &= check_module('budget.parser')
    modules_ok &= check_module('budget.categorize')
    modules_ok &= check_module('budget.ai_tools')
    # modules_ok &= check_module('budget.visualizer')  # Uncomment when implemented
    
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