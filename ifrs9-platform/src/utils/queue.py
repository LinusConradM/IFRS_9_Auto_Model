"""RabbitMQ message queue utilities"""
import pika
import json
import os
from typing import Callable, Any, Dict

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")


class QueueManager:
    """RabbitMQ queue manager"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self._connect()
    
    def _connect(self):
        """Establish connection to RabbitMQ"""
        try:
            parameters = pika.URLParameters(RABBITMQ_URL)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queues
            self.channel.queue_declare(queue='ecl_calculations', durable=True)
            self.channel.queue_declare(queue='ecl_calculations_dlx', durable=True)
            
        except Exception as e:
            print(f"RabbitMQ connection error: {e}")
    
    def publish_message(self, queue: str, message: Dict[str, Any]) -> bool:
        """
        Publish message to queue.
        
        Args:
            queue: Queue name
            message: Message payload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.channel:
                self._connect()
            
            self.channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            return True
        except Exception as e:
            print(f"Queue publish error: {e}")
            return False
    
    def consume_messages(self, queue: str, callback: Callable):
        """
        Consume messages from queue.
        
        Args:
            queue: Queue name
            callback: Callback function to process messages
        """
        try:
            if not self.channel:
                self._connect()
            
            def wrapper(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    callback(message)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    print(f"Message processing error: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(queue=queue, on_message_callback=wrapper)
            self.channel.start_consuming()
            
        except Exception as e:
            print(f"Queue consume error: {e}")
    
    def close(self):
        """Close connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()


# Global queue manager instance
queue_manager = QueueManager()
