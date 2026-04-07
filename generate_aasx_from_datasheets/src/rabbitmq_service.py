#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A thread-safe, singleton RabbitMQ service module.

This module provides a robust, reusable, and thread-safe class `RabbitMQService`
for interacting with a RabbitMQ message broker. It is designed using the Singleton
pattern to ensure only one connection is managed throughout an application's lifecycle.
It includes automatic connection retries with exponential backoff and jitter.
"""

# --- Standard and Third-Party Imports ---
import json
import threading
from functools import wraps

import pika
from loguru import logger
from retry import retry


# --- RabbitMQ Service Class Definition ---

class RabbitMQService:
    """
    A thread-safe Singleton class to manage RabbitMQ connections and operations.

    This service handles connecting, publishing, consuming, and gracefully closing
    the RabbitMQ connection. The Singleton pattern ensures that all parts of an
    application share a single connection instance, preventing resource exhaustion
    and simplifying state management.

    Attributes:
        connection: The pika.BlockingConnection object.
        channel: The pika.channel.Channel object.
        connected (bool): A flag indicating the connection status.
    """
    # --- Singleton Implementation ---
    _instance = None  # Class attribute to hold the single instance
    _lock = threading.Lock()  # Lock to ensure thread-safe instance creation

    def __new__(cls):
        """
        Controls the creation of a new instance (Singleton pattern).

        This method ensures that only one instance of RabbitMQService is ever created.
        It uses a double-checked locking mechanism for thread safety and efficiency.
        """
        if cls._instance is None:
            # Acquire a lock to prevent race conditions during instantiation
            with cls._lock:
                # Second check: in case another thread created the instance while
                # the current thread was waiting for the lock.
                if cls._instance is None:
                    cls._instance = super(RabbitMQService, cls).__new__(cls)
                    # Add a flag to ensure __init__ is called only once.
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Initializes the RabbitMQService instance attributes.

        This method is guarded by an `_initialized` flag to ensure that the
        initialization logic runs only once, the very first time the singleton
        instance is created.
        """
        if not getattr(self, '_initialized', False):
            self.connection = None
            self.channel = None
            self.connected = False
            self._initialized = True

    # --- Core Connection Logic ---
    @retry(pika.exceptions.AMQPConnectionError, delay=5, jitter=(1, 3), max_delay=30, logger=logger)
    def connect(self, host='rabbitmq', port=5672, username='guest', password='guest'):
        """
        Establish a connection to the RabbitMQ server with automatic retries.

        The @retry decorator will automatically attempt to reconnect if an
        AMQPConnectionError occurs.

        Args:
            host (str): The RabbitMQ server hostname.
            port (int): The RabbitMQ server port.
            username (str): The username for authentication.
            password (str): The password for authentication.

        Raises:
            pika.exceptions.AMQPConnectionError: If the connection cannot be established
                                                after all retry attempts.
        """
        try:
            # Define credentials and connection parameters
            credentials = pika.PlainCredentials(username, password)
            parameters = pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=credentials,
                heartbeat=600,  # Keep the connection alive even if idle
                blocked_connection_timeout=300  # Timeout for blocked connections
            )

            # Establish a blocking connection
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.connected = True

            logger.success(f"Successfully connected to RabbitMQ at {host}:{port}")

        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}. Retrying...")
            # Re-raise the exception to allow the @retry decorator to catch it
            raise

    # --- Messaging Operations ---
    def publish_message(self, exchange, routing_key, message, persistent=True):
        """
        Publishes a message to a specific exchange with a routing key.

        Args:
            exchange (str): The name of the exchange to publish to.
            routing_key (str): The routing key for the message.
            message (dict): The message payload (will be JSON-serialized).
            persistent (bool): If True, marks the message for disk storage on the broker.

        Returns:
            bool: True if the message was published successfully, False otherwise.
        """
        if not self.connected:
            logger.warning("Not connected. Attempting to connect before publishing.")
            self.connect()

        # Define message properties
        properties = pika.BasicProperties(
            delivery_mode=2 if persistent else 1,  # 2 = persistent message
            content_type='application/json'
        )

        try:
            # Publish the message
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(message),  # Ensure the body is a string (JSON)
                properties=properties
            )
            logger.debug(f"Published message to exchange '{exchange}' with routing key '{routing_key}'")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}. Attempting to reconnect.")
            # If publishing fails, the connection might be dead. Try reconnecting.
            self.reconnect()
            return False

    def consume_messages(self, queue_name, callback, auto_ack=False):
        """
        Starts consuming messages from a specified queue.

        This is a blocking operation. It will run indefinitely, waiting for messages.

        Args:
            queue_name (str): The name of the queue to consume from.
            callback (function): The function to call when a message is received.
                                 It must accept (ch, method, properties, body).
            auto_ack (bool): If True, messages are acknowledged automatically.
                             Set to False (default) for better reliability.
        """
        if not self.connected:
            logger.warning("Not connected. Attempting to connect before consuming.")
            self.connect()

        try:
            # Set Quality of Service: Don't dispatch a new message to a worker
            # until it has processed and acknowledged the previous one.
            self.channel.basic_qos(prefetch_count=1)

            # Register the consumer callback
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=auto_ack
            )

            logger.info(f"Started consuming messages from queue '{queue_name}'. Waiting for messages...")
            self.channel.start_consuming()  # Start the blocking consumer loop
        except Exception as e:
            logger.error(f"Failed to start consuming: {e}. Attempting to reconnect.")
            self.reconnect()

    # --- Connection Housekeeping ---
    def reconnect(self):
        """
        Handles the reconnection logic by closing the old connection and creating a new one.
        """
        logger.info("Attempting to reconnect to RabbitMQ...")
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            # Log error but proceed, as the main goal is to reconnect
            logger.error(f"Error while closing existing connection during reconnect: {e}")
        finally:
            self.connected = False
            self.connect()  # Establish a new connection

    def close(self):
        """
        Gracefully closes the connection to RabbitMQ.
        """
        try:
            if self.connection and self.connection.is_open:
                logger.info("Closing RabbitMQ connection.")
                self.connection.close()
                self.connected = False
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")


# --- Singleton Instance ---
# This is the single, global instance of the service that will be imported
# and used by other parts of the application.
rabbitmq_service = RabbitMQService()


# --- Decorator for Convenience ---
def with_rabbitmq_connection(func):
    """
    A decorator to ensure a RabbitMQ connection is active before executing a function.

    This simplifies function calls by abstracting away the need to manually check
    for a connection every time.

    Args:
        func (function): The function to be wrapped.

    Returns:
        function: The wrapped function.
    """
    @wraps(func)  # Preserves the original function's metadata (name, docstring, etc.)
    def wrapper(*args, **kwargs):
        """Wrapper function that checks for connection before execution."""
        if not rabbitmq_service.connected:
            logger.debug(f"Decorator '{func.__name__}': RabbitMQ not connected. Connecting...")
            rabbitmq_service.connect()
        # Execute the original function
        return func(*args, **kwargs)
    return wrapper