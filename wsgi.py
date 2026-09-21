import os
import sys

# مطمئن شو پوشه database وجود داره
os.makedirs("database", exist_ok=True)

try:
    from app import app
    print("✅ app imported successfully")
except Exception as e:
    print(f"❌ Error importing app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == '__main__':
    app.run()