from sanic import Blueprint
from .routes import bp

admin_api = Blueprint.group(bp, url_prefix="/admin")
