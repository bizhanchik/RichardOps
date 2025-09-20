# Routes package
# Import router from the routes.py file in the parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from routes import router