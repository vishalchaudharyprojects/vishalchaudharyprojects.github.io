"""
RabbitMQ Consumer Service for CIM-first AAS workflow automation
"""

import json
from loguru import logger
from rabbitmq_service import rabbitmq_service

def cim_conversion_callback(ch, method, properties, body):
    """Callback for cim.converted events - triggers static data addition"""
    try:
        message = json.loads(body)
        logger.info(f"[Consumer] Received cim.converted: {message}")

        # Import and call static data addition
        from .aas_creator import process_single_csv

        equipment = message.get('equipment')
        cim_aas_path = message.get('cim_aas_path')

        if cim_aas_path:
            logger.info(f"[Consumer] Adding static data to CIM-based AAS: {cim_aas_path}")

            if equipment:
                # Add static data for specific equipment
                from pathlib import Path
                assets_dir = Path("/app/assets")
                csv_path = assets_dir / f"{equipment}.csv"

                if csv_path.exists():
                    result = process_single_csv(csv_path, emit_event=True)
                    if result:
                        logger.success(f"[Consumer] Static data added to CIM AAS: {result}")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        logger.error(f"[Consumer] Failed to add static data for {equipment}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                else:
                    logger.error(f"[Consumer] CSV file not found for equipment: {equipment}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            else:
                logger.error(f"[Consumer] Equipment name required for static data addition")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        else:
            logger.error(f"[Consumer] Invalid CIM conversion message: {message}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except Exception as e:
        logger.error(f"[Consumer] Error processing cim.converted: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_consumers():
    """Start RabbitMQ consumers for CIM-first workflow"""
    try:
        # Connect to RabbitMQ
        rabbitmq_service.connect()

        # Declare exchange
        rabbitmq_service.channel.exchange_declare(
            exchange='aas_events',
            exchange_type='topic',
            durable=True
        )

        # Create queue for cim.converted events
        queue_name = 'aas_events.cim_converted'
        rabbitmq_service.channel.queue_declare(queue=queue_name, durable=True)

        # Bind queue to exchange
        rabbitmq_service.channel.queue_bind(
            exchange='aas_events',
            queue=queue_name,
            routing_key='cim.converted'
        )

        # Start consuming
        rabbitmq_service.channel.basic_consume(
            queue=queue_name,
            on_message_callback=cim_conversion_callback,
            auto_ack=False
        )

        logger.success("[Consumer] RabbitMQ consumer started for cim.converted events")
        logger.info("[Consumer] Waiting for CIM conversion messages...")

        # Start consuming (this will block)
        rabbitmq_service.channel.start_consuming()

    except Exception as e:
        logger.error(f"[Consumer] Failed to start consumers: {e}")
        raise

if __name__ == '__main__':
    start_consumers()