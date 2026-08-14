import sys
from pathlib import Path

# Add parent to path and import the Flask app
BASE_DIR = Path(__file__).parent.parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import app as flask_app_module
app = flask_app_module.app
handler = flask_app_module.app
