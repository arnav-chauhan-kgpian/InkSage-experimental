#!/usr/bin/env python3
"""
InkSage Environment Diagnostic (PyTorch Edition)
Verifies Python version, libraries, and project structure.
"""

import sys
import importlib
import os
from pathlib import Path

# Add src to path for internal module checks
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_python_version():
    """InkSage uses modern type hinting and async features."""
    print("🐍 Testing Python version...")
    version = sys.version_info
    
    # We recommend 3.10+ for best PySide6 compatibility
    if version.major == 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"⚠️  Python {version.major}.{version.minor} - Recommended: 3.10+")
        return True

def test_dependencies():
    """Test required InkSage libraries."""
    print("\n📦 Testing libraries...")
    
    # (Package Name, Import Name)
    dependencies = [
        ("PySide6", "PySide6"),           # UI Framework
        ("torch", "torch"),               # AI Tensor Engine
        ("transformers", "transformers"), # AI Model Loader
        ("faster-whisper", "faster_whisper"), # Voice
        ("pynput", "pynput"),             # Keyboard Monitor
        ("pyyaml", "yaml"),               # Config
        ("pygetwindow", "pygetwindow"),   # Context Sniffer
    ]
    
    all_good = True
    
    for pkg_name, import_name in dependencies:
        try:
            importlib.import_module(import_name)
            print(f"✅ {pkg_name:<20} - Installed")
        except ImportError:
            print(f"❌ {pkg_name:<20} - MISSING")
            all_good = False
    
    if not all_good:
        print("\nFix missing libraries with:")
        print("pip install -r requirements.txt")
            
    return all_good

def test_project_structure():
    """Verify the modular architecture exists."""
    print("\n📁 Testing project structure...")
    
    required_files = [
        "src/main.py",
        "src/core/engine.py",
        "src/core/assistant.py",
        "src/core/context_sniffer.py",
        "src/ui/main_window.py",
        "src/ui/tray_icon.py",
        "config/settings.yaml",
    ]
    
    all_good = True
    
    for path_str in required_files:
        path = project_root / path_str
        if path.exists():
            print(f"✅ {path_str:<25} - Found")
        else:
            print(f"❌ {path_str:<25} - MISSING")
            all_good = False
            
    return all_good

def test_gpu_availability():
    """Check if PyTorch can see the GPU (Optional but recommended)."""
    print("\n🧠 Testing Compute Hardware...")
    
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ GPU Detected: {gpu_name}")
            print("   (InkSage will run fast)")
        else:
            print("⚠️  No GPU Detected (Running on CPU)")
            print("   (Inference might be slow. Ensure CUDA is installed if you have an NVIDIA card.)")
        return True
    except ImportError:
        return False # Handled by dependency check

def main():
    """Run diagnostics."""
    print("="*40)
    print(" 🔮 InkSage Environment Diagnostic")
    print("="*40 + "\n")
    
    tests = [
        test_python_version,
        test_dependencies,
        test_project_structure,
        test_gpu_availability
    ]
    
    results = []
    
    for test_func in tests:
        try:
            if test_func():
                results.append(True)
            else:
                results.append(False)
        except Exception as e:
            print(f"❌ Test Crashed: {e}")
            results.append(False)
            
    print("\n" + "="*40)
    
    if all(results):
        print("🎉 SUCCESS: InkSage is ready to launch.")
        print("   Run: python run_inksage.py")
    else:
        print("⚠️  ISSUES FOUND: Please review the errors above.")
        
    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())