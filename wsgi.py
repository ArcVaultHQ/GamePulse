import os
import sys

os.makedirs("database", exist_ok=True)

try:
    from app import app
    print("✅ app imported successfully", flush=True)
except MemoryError:
    print("❌ MemoryError: RAM کافی نیست", flush=True)
    sys.exit(1)
except ImportError as e:
    print(f"❌ ImportError: {e}", flush=True)
    sys.exit(1)
except Exception as e:
    print(f"❌ Startup Error: {type(e).__name__}: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == '__main__':
    app.run()