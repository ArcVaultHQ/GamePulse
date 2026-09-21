import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)

try:
    from app import app
    print("✅ app imported successfully", flush=True)
except Exception as e:
    print(f"❌ Error: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == '__main__':
    app.run()