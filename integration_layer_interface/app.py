from flask import Flask
from src.api.routes import bp as api_bp
from src.rabbitmq_service import rabbitmq_service
from loguru import logger
import os
import atexit


def create_app():
    app = Flask(__name__)

    # Initialize RabbitMQ connection on app startup
    def init_rabbitmq():
        try:
            rabbitmq_service.connect(
                host=os.getenv('RABBITMQ_HOST', 'rabbitmq'),
                port=int(os.getenv('RABBITMQ_PORT', 5672)),
                username=os.getenv('RABBITMQ_USER', 'guest'),
                password=os.getenv('RABBITMQ_PASSWORD', 'guest')
            )
            logger.info("RabbitMQ connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ: {e}")

    # Initialize RabbitMQ when the app starts
    with app.app_context():
        init_rabbitmq()

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return {"message": "Integration Layer Interface API", "status": "running"}

    @app.route('/health')
    def health():
        return {
            "status": "healthy",
            "rabbitmq_connected": rabbitmq_service.connected
        }, 200

    # Cleanup on shutdown
    @atexit.register
    def cleanup():
        rabbitmq_service.close()
        logger.info("Application shutdown complete")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=False)