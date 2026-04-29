from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_socketio import SocketIO
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()
socketio = SocketIO()

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins='*', async_mode='eventlet')

    from app.auth import auth_bp
    from app.campus import campus_bp
    from app.classroom import classroom_bp
    from app.chat import chat_bp
    from app.calendar import calendar_bp
    from app.notices import notices_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(campus_bp, url_prefix='')
    app.register_blueprint(classroom_bp, url_prefix='/classroom')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(calendar_bp, url_prefix='/calendar')
    app.register_blueprint(notices_bp, url_prefix='/notices')

    return app
