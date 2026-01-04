import os
import glob

MEMORY_DIR = ".claude/memory"

def clean_memory():
    print("🧹 [Hook] Cleaning up previous session memory...")
    if not os.path.exists(MEMORY_DIR):
        os.makedirs(MEMORY_DIR)
        return

    files = glob.glob(os.path.join(MEMORY_DIR, "*.json"))
    for f in files:
        try:
            os.remove(f)
            print(f"   - Removed: {os.path.basename(f)}")
        except Exception as e:
            print(f"   - Error removing {f}: {e}")
    print("✨ Memory clean complete.")

if __name__ == "__main__":
    clean_memory()
