# Prosty przykład RabbitMQ Processor

Minimalistyczny przykład aplikacji Python, która:
1. **Odbiera wiadomości** z kolejki RabbitMQ
2. **Przetwarza dane** (miejsce na Twój kod)
3. **Wysyła wyniki** do kolejnej kolejki RabbitMQ

## Struktura

```
rabbitmq_processor_example/
├── Dockerfile              # Obraz Docker
├── docker-compose.yml      # Konfiguracja z RabbitMQ
├── requirements.txt        # Zależności (pika, python-dotenv)
├── main.py                 # Główna aplikacja
└── README.md               # Ten plik
```

## Szybki start

### 1. Uruchom z Docker Compose

```bash
docker compose up -d
```

### 2. Zobacz logi

```bash
docker compose logs -f processor
```

### 3. Zatrzymaj

```bash
docker compose down
```

## Konfiguracja

Zmienne środowiskowe (opcjonalne, domyślne wartości w nawiasach):

```bash
RABBITMQ_HOST=rabbitmq          # Host RabbitMQ
RABBITMQ_PORT=5672              # Port RabbitMQ
RABBITMQ_USER=guest             # Użytkownik
RABBITMQ_PASSWORD=guest         # Hasło
INPUT_QUEUE=input_queue         # Nazwa kolejki wejściowej
OUTPUT_QUEUE=output_queue      # Nazwa kolejki wyjściowej
```

## Dodanie własnej logiki

Edytuj metodę `process_message()` w pliku `main.py`:

```python
def process_message(self, message_data: dict) -> dict:
    # Twoja logika tutaj
    processed = {
        'original': message_data,
        'your_field': 'your_value'
    }
    return processed
```

## Format wiadomości

### Wejściowa kolejka (INPUT_QUEUE)

```json
{
  "id": "123",
  "data": "example"
}
```

### Wyjściowa kolejka (OUTPUT_QUEUE)

```json
{
  "original": { ... },
  "processed": true,
  "message": "Wiadomość przetworzona"
}
```

## RabbitMQ Management UI

Po uruchomieniu dostępne na: http://localhost:15672
- Login: `guest` (domyślnie)
- Hasło: `guest` (domyślnie)

## Lokalne uruchomienie (bez Dockera)

1. Uruchom RabbitMQ:
   ```bash
   docker compose up -d rabbitmq
   ```

2. Zainstaluj zależności:
   ```bash
   pip install -r requirements.txt
   ```

3. Uruchom aplikację:
   ```bash
   python main.py
   ```

## Testowanie

Możesz wysłać testową wiadomość używając Management UI lub skryptu Python:

```python
import pika
import json

connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)
channel = connection.channel()

channel.queue_declare(queue='input_queue', durable=True)

message = {'id': '123', 'data': 'test'}
channel.basic_publish(
    exchange='',
    routing_key='input_queue',
    body=json.dumps(message)
)

print("Wiadomość wysłana")
connection.close()
```
