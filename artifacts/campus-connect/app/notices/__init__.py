from flask import Blueprint
notices_bp = Blueprint('notices', __name__)
from app.notices import routes
