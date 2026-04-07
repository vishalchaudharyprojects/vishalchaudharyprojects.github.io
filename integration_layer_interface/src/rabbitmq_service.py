import pika
import json
import logging
from functools import wraps
from retry import retry
from loguru import logger
import threading


class RabbitMQService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RabbitMQService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.connection = None
            self.channel = None
            self.connected = False
            self._initialized = True

    @retry(pika.exceptions.AMQPConnectionError, delay=5, jitter=(1, 3), max_delay=30, logger=logger)
    def connect(self, host='rabbitmq', port=5672, username='guest', password='guest'):
        """Establish connection to RabbitMQ with retry logic"""
        try:
            credentials = pika.PlainCredentials(username, password)
            parameters = pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.connected = True

            # Declare exchanges and queues
            self._declare_infrastructure()

            logger.success(f"Connected to RabbitMQ at {host}:{port}")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def _declare_infrastructure(self):
        """Declare all required exchanges and queues"""
        # Main exchange for workflow messages
        self.channel.exchange_declare(
            exchange='digital_twin.workflow',
            exchange_type='direct',
            durable=True
        )

        # Dead letter exchange
        self.channel.exchange_declare(
            exchange='digital_twin.dlx',
            exchange_type='fanout',
            durable=True
        )

        # Workflow queues
        queues = [
            ('aas.creation.queue', 'aas.creation'),
            ('aas.cim.linking.queue', 'aas.cim.linking'),
            ('cim.aas.linking.queue', 'cim.aas.linking'),
            ('workflow.status.queue', 'workflow.status')
        ]

        for queue_name, routing_key in queues:
            self.channel.queue_declare(
                queue=queue_name,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': 'digital_twin.dlx',
                    'x-dead-letter-routing-key': f'{queue_name}.dlq'
                }
            )
            self.channel.queue_bind(
                exchange='digital_twin.workflow',
                queue=queue_name,
                routing_key=routing_key
            )

        # Dead letter queues
        dlq_names = [f'{q[0]}.dlq' for q in queues]
        for dlq_name in dlq_names:
            self.channel.queue_declare(queue=dlq_name, durable=True)
            self.channel.queue_bind(
                exchange='digital_twin.dlx',
                queue=dlq_name,
                routing_key=dlq_name
            )

    def publish_message(self, exchange, routing_key, message, persistent=True):
        """Publish message to RabbitMQ"""
        if not self.connected:
            self.connect()

        properties = pika.BasicProperties(
            delivery_mode=2 if persistent else 1,  # 2 = persistent
            content_type='application/json'
        )

        try:
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=properties
            )
            logger.debug(f"Published message to {exchange}/{routing_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            self.reconnect()
            return False

    def consume_messages(self, queue_name, callback, auto_ack=False):
        """Start consuming messages from a queue"""
        if not self.connected:
            self.connect()

        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=auto_ack
            )
            logger.info(f"Started consuming from {queue_name}")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Failed to start consuming: {e}")
            self.reconnect()

    def reconnect(self):
        """Reconnect to RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except:
            pass

        self.connected = False
        self.connect()

    def close(self):
        """Close connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                self.connected = False
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")


# Singleton instance
rabbitmq_service = RabbitMQService()


def with_rabbitmq_connection(func):
    """Decorator to ensure RabbitMQ connection"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not rabbitmq_service.connected:
            rabbitmq_service.connect()
        return func(*args, **kwargs)

    return wrapper