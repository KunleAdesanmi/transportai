import os
import sys

def check_env():
    print("🔍 Starting Environment Health Check...\n")
    
    # 1. Check if VENV is active
    if not hasattr(sys, 'real_prefix') and not (sys.base_prefix != sys.prefix):
        print("❌ ERROR: Virtual Environment (venv) is NOT active.")
        print("   Run: 'source venv/bin/activate' (Mac) or '.\\venv\\Scripts\\activate' (Win)\n")
    else:
        print("✅ Venv: Active")

    # 2. Check for critical files
    required_files = ['app/main.py', 'app/travel_logic.py', 'app/prompt.py', '.env', 'requirements.txt']
    for f in required_files:
        if os.path.exists(f):
            print(f"✅ File Found: {f}")
        else:
            print(f"❌ MISSING FILE: {f}")

    # 3. Check for .env contents (Don't print the actual keys!)
    if os.path.exists('.env'):
        with open('.env', 'r') as e:
            content = e.read()
            keys = ['OPENAI_API_KEY', 'TRANSPORT_API_ID', 'TRANSPORT_API_KEY', 'AWS_ACCESS_KEY_ID']
            for k in keys:
                if k in content:
                    print(f"✅ Key Found in .env: {k}")
                else:
                    print(f"⚠️  WARNING: {k} is missing from .env")

    # 4. Check if libraries are installed
    try:
        import fastapi
        import mangum
        import openai
        import boto3
        print("\n✅ All required Python libraries are installed in venv.")
    except ImportError as e:
        print(f"\n❌ LIBRARIES MISSING: {e}")
        print("   Run: 'pip install -r requirements.txt'")

if __name__ == "__main__":
    check_env()