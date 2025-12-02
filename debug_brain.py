import os
import sys
from pathlib import Path

# Setup paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_brain():
    print("🧠 Starting Brain Diagnostic...")
    
    # 1. Check Model File
    try:
        from src.utils.config import config
        model_path = config.get('engine.model_path')
        full_path = Path(model_path).resolve()
        
        print(f"📂 Model Path: {full_path}")
        
        if not full_path.exists():
            print("❌ ERROR: Model file does not exist!")
            return
            
        size_mb = full_path.stat().st_size / (1024 * 1024)
        print(f"📦 File Size: {size_mb:.2f} MB")
        
        if size_mb < 100:
            print("❌ ERROR: Model file is too small (Corrupted Download).")
            print("   Please delete it and download again.")
            return

    except Exception as e:
        print(f"❌ Config Error: {e}")
        return

    # 2. Try Loading Library
    print("\n📚 Importing llama_cpp...")
    try:
        from llama_cpp import Llama
        print("✅ Library imported successfully.")
    except ImportError:
        print("❌ ERROR: llama-cpp-python not installed.")
        return
    except Exception as e:
        print(f"❌ ERROR importing library: {e}")
        return

    # 3. Try Loading Model (The Crash Zone)
    print("\n🔥 Attempting to load model into RAM (This may crash)...")
    try:
        llm = Llama(
            model_path=str(full_path),
            n_ctx=2048,
            verbose=True
        )
        print("\n🎉 SUCCESS: The Brain is working!")
        print(f"   Generated Test: {llm('Hello', max_tokens=10)}")
    except Exception as e:
        print(f"\n❌ CRASH: {e}")

if __name__ == "__main__":
    test_brain()