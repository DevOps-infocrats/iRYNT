# auto-generated placeholder
#!/usr/bin/env python
import os
from app import create_app

# Create the WSGI application object for the web server (e.g., gunicorn)
application = create_app(os.getenv('FLASK_ENV', 'production'))
