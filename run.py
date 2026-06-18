#!/usr/bin/env python
import os
from app import create_app, db
from dotenv import load_dotenv

load_dotenv()

app = create_app(os.environ.get('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    return {'db': db}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
