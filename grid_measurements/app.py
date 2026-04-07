import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.api import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=False)