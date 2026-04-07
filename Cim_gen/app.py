import sys
from pathlib import Path

# Add both /app and /app/src to Python path
sys.path.extend([str(Path(__file__).parent), str(Path(__file__).parent / "src")])

from src.api import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)