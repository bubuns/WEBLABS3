from vercel_wsgi import handle
from app import create_app


flask_app = create_app()


def handler(request, response):
    return handle(request, response, flask_app)


