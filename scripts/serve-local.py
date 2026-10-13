"""Start a local backend with project-isolated dependencies."""
import sys
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.environ.get('QUANTUM_RUNTIME_PATH', str(root / 'backend' / '.runtime')))
sys.path.insert(0, str(root))
import uvicorn

if __name__ == '__main__':
    uvicorn.run('backend.main:app', host='127.0.0.1', port=8000)
