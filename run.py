import os
from dotenv import load_dotenv
load_dotenv()  # Charge .env avant tout
from app import create_app, db

# Crée l'application
app = create_app(config_name=os.environ.get('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    return {'db': db}

@app.before_request
def before_request():
    """Crée les tables si elles n'existent pas"""
    pass

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=app.config.get('DEBUG', False), host='0.0.0.0', port=5000)
