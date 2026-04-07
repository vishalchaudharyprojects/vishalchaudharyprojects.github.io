from flask import Flask
from loguru import logger
import sys
import os
import threading


def create_app():
    app = Flask(__name__)

    # Add the src directory to Python path - FIXED
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    logger.info(f"Python path configured: {sys.path}")

    # Import and register blueprints
    try:
        from api.routes import api_bp  # FIXED: Remove src. prefix
        app.register_blueprint(api_bp, url_prefix='/api')
        logger.success("API blueprint registered successfully")
    except ImportError as e:
        logger.error(f"Could not import API routes: {e}")
        logger.error(f"Files in api directory: {os.listdir(os.path.join(src_path, 'api'))}")

    @app.route('/')
    def index():
        return {"message": "AAS Generation Service API"}

    @app.route('/health')
    def health():
        return {"status": "healthy"}

    # Start RabbitMQ consumers in background thread
    def start_consumer_thread():
        try:
            logger.info("Starting RabbitMQ consumers...")
            from src.rabbitmq_consumer import start_consumers  # FIXED: Remove src. prefix
            start_consumers()
        except Exception as e:
            logger.error(f"Consumer thread failed: {e}")

    # Start consumers in background
    consumer_thread = threading.Thread(target=start_consumer_thread, daemon=True)
    consumer_thread.start()
    logger.info("RabbitMQ consumer thread started")

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)