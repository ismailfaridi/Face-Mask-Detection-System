from flask import Flask
from dotenv import load_dotenv
import os

def create_app():
    load_dotenv()
    
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    
    # Register blueprints
    from .blueprints.main import main_bp
    from .blueprints.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    return app