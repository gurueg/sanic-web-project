from sanic import Blueprint
from .routes import bp

user_api = Blueprint.group(bp, url_prefix="/")