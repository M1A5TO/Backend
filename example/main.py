#!/usr/bin/env python3
"""
Prosty przykład odbierania i wysyłania wiadomości do RabbitMQ.
"""

import os
import json
import logging
import signal
import sys
from dotenv import load_dotenv
import pika

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')

INPUT_QUEUE = os.getenv('INPUT_QUEUE', 'input_queue')
OUTPUT_QUEUE = os.getenv('OUTPUT_QUEUE', 'output_queue')


class RabbitMQProcessor:
    """Prosty procesor wiadomości RabbitMQ."""
    
    def __init__(self):
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Połącz się z RabbitMQ."""
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Utwórz kolejki (jeśli nie istnieją)
            self.channel.queue_declare(queue=INPUT_QUEUE, durable=True)
            self.channel.queue_declare(queue=OUTPUT_QUEUE, durable=True)
            
            logger.info(f"Połączono z RabbitMQ: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
        except Exception as e:
            logger.error(f"Błąd połączenia z RabbitMQ: {e}")
            raise
    
    def process_message(self, message_data: dict) -> dict:
        """
        Przetwórz wiadomość.
        
        TODO: Dodaj tutaj swoją logikę przetwarzania.
        """
        logger.info(f"Przetwarzam wiadomość: {message_data}")
        
        # Przykładowe przetwarzanie - zmień na swoje
        processed = {
            'original': message_data,
            'processed': True,
            'message': 'Wiadomość przetworzona'
        }
        
        return processed
    
    def on_message(self, ch, method, properties, body):
        """Obsługa otrzymanej wiadomości."""
        try:
            # Parsuj wiadomość JSON
            message_data = json.loads(body.decode('utf-8'))
            logger.info(f"Otrzymano wiadomość: {message_data}")
            
            # Przetwórz wiadomość
            processed_data = self.process_message(message_data)
            
            # Wyślij do kolejki wyjściowej
            self.channel.basic_publish(
                exchange='',
                routing_key=OUTPUT_QUEUE,
                body=json.dumps(processed_data),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Wiadomość trwała
                )
            )
            
            logger.info(f"Wiadomość wysłana do kolejki: {OUTPUT_QUEUE}")
            
            # Potwierdź przetworzenie wiadomości
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError as e:
            logger.error(f"Błędny format JSON: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Błąd przetwarzania: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start(self):
        """Rozpocznij nasłuchiwanie wiadomości."""
        try:
            self.channel.basic_consume(
                queue=INPUT_QUEUE,
                on_message_callback=self.on_message
            )
            
            logger.info(f"Oczekiwanie na wiadomości z kolejki '{INPUT_QUEUE}'. CTRL+C aby zakończyć")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Zatrzymywanie...")
            self.stop()
    
    def stop(self):
        """Zatrzymaj i zamknij połączenie."""
        if self.channel and not self.channel.is_closed:
            self.channel.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        logger.info("Połączenie zamknięte")


def signal_handler(signum, frame):
    """Obsługa sygnału zakończenia."""
    logger.info("Otrzymano sygnał zakończenia")
    sys.exit(0)


def main():
    """Główna funkcja aplikacji."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    processor = RabbitMQProcessor()
    
    try:
        processor.connect()
        processor.start()
    except Exception as e:
        logger.error(f"Błąd aplikacji: {e}")
        sys.exit(1)
    finally:
        processor.stop()


if __name__ == '__main__':
    main()
