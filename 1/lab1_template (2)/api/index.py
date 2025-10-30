from vercel_wsgi import handle

# Import Flask app from lab
from app.app import app as flask_app


def handler(request, response):
    return handle(request, response, flask_app)


