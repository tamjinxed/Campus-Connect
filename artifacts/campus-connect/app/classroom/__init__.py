from flask import Blueprint
classroom_bp = Blueprint('classroom', __name__)
from app.classroom import routes
