import os
import sys
import subprocess
from pathlib import Path

def main():
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")

    print("=" * 60)
    print("   JobHelperGuru — AI Job Assistant & Application Tracker")
    print("=" * 60)
    print(f"Starting server at: http://{host}:{port}")
    print("Press Ctrl+C to stop.\n")

    # Ensure frontend build exists if possible
    dist_dir = Path("frontend/dist")
    if not dist_dir.exists():
        print("[Notice] Frontend dist folder not found. If running in production mode, run 'npm run build' in frontend/")

    import uvicorn
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    main()
