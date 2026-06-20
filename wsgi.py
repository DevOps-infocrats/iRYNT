import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'production'))
