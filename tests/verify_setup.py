#!/usr/bin/env python3
"""
Setup Verification Script

Checks that all dependencies are installed and modules can be imported.
Run this before using the main tool to verify everything is working.
"""

import sys
import os


def check_python_version():
    """Check Python version is 3.8+."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ Python 3.8 or higher required")
        return False

    print("✓ Python version OK")
    return True


def check_dependencies():
    """Check all required dependencies are installed."""
    print("\nChecking dependencies...")

    dependencies = {
        'pandas': '2.1.0',
        'holidays': '0.36',
        'dateutil': '2.8.2',
        'tabulate': '0.9.0',
    }

    all_ok = True

    for module_name, min_version in dependencies.items():
        try:
            if module_name == 'dateutil':
                import dateutil
                module = dateutil
            else:
                module = __import__(module_name)

            # Try to get version
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {module_name}: {version}")

        except ImportError:
            print(f"✗ {module_name}: NOT INSTALLED (required >= {min_version})")
            all_ok = False

    return all_ok


def check_modules():
    """Check that project modules can be imported."""
    print("\nChecking project modules...")

    # Add parent directory to path to allow imports from root
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    modules = [
        'src.utils',
        'src.nem12_parser',
        'src.generic_interval_parser',
        'src.tou_config',
        'src.aggregator',
        'src.output_formatter',
        'meter_aggregator',
    ]

    all_ok = True

    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            print(f"✗ {module_name}: {str(e)}")
            all_ok = False
        except Exception as e:
            print(f"⚠ {module_name}: {str(e)} (may be OK)")

    return all_ok


def check_test_file():
    """Check if test NEM12 file exists."""
    print("\nChecking test data...")

    test_file = os.path.join(os.path.dirname(__file__), 'test_nem12.csv')
    if os.path.exists(test_file):
        print("✓ tests/test_nem12.csv found")
        return True
    else:
        print("⚠ tests/test_nem12.csv not found (optional)")
        return True


def check_documentation():
    """Check if documentation files exist."""
    print("\nChecking documentation...")

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs = ['README.md', 'QUICKSTART.md']

    for doc in docs:
        doc_path = os.path.join(parent_dir, doc)
        if os.path.exists(doc_path):
            print(f"✓ {doc}")
        else:
            print(f"⚠ {doc} not found")


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("NEM12 Meter Data Aggregation Tool - Setup Verification")
    print("=" * 70)

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project Modules", check_modules),
        ("Test Data", check_test_file),
        ("Documentation", check_documentation),
    ]

    all_passed = True

    for check_name, check_func in checks:
        try:
            result = check_func()
            if result is False:
                all_passed = False
        except Exception as e:
            print(f"\n✗ {check_name} check failed: {str(e)}")
            all_passed = False

    print("\n" + "=" * 70)

    if all_passed:
        print("✓ ALL CHECKS PASSED")
        print("\nYou're ready to use the tool!")
        print("Run: python meter_aggregator.py")
    else:
        print("✗ SOME CHECKS FAILED")
        print("\nPlease fix the issues above before running the tool.")
        print("\nTo install dependencies:")
        print("  source .venv/bin/activate")
        print("  pip install -r requirements.txt")

    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
