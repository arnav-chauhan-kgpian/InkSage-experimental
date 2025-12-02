#!/usr/bin/env python3
"""
InkSage Launcher
================

The primary entry point. It sets up the Python environment path
and launches the main application logic defined in `src.main`.
"""

import sys
import traceback
from pathlib import Path

def main():
    """Bootstrap the InkSage application."""
    
    # 1. Setup Environment
    # Ensure the project root is in the Python path so 'src' is importable
    project_root = Path(__file__).parent.resolve()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    try:
        print("✨ Initializing InkSage...")
        
        # 2. Handover to Source
        from src.main import main as app_entry
        return app_entry()
        
    except ImportError as e:
        print(f"❌ Dependency Error: {e}")
        print("   Please run: pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"❌ Critical Startup Error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())