import os
# Prevent OpenMP runtime collision crashes on Apple Silicon / macOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import sys
from pathlib import Path
import uvicorn

# Ensure proper utf-8 stream encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add current directory to path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from app.core.config import settings

if __name__ == "__main__":
    print(f"[*] Starting {settings.PROJECT_NAME} on http://localhost:8000")
    print(f"[*] OpenAPI Documentation available at http://localhost:8000/docs")
    print(f"[*] Health Probe: http://localhost:8000/api/v1/health")
    print(f"[*] Readiness Probe: http://localhost:8000/api/v1/ready")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
