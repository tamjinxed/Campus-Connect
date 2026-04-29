from flask import Blueprint
campus_bp = Blueprint('campus', __name__)
from app.campus import routes
