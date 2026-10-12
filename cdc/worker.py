"""At-least-once Kafka consumer with SQLite offset deduplication."""
import json
import os
import sqlite3
from pathlib import Path
from confluent_kafka import Consumer, KafkaException
from .processing import apply_event, initialize


def main():
    path = Path(os.getenv("CDC_STORE", "artifacts/cdc.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    initialize(db)
    topic = os.getenv("KAFKA_TOPIC", "orders.public.orders")
    consumer = Consumer({"bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"),
                         "group.id": "cdc-materializer-v1", "auto.offset.reset": "earliest",
                         "enable.auto.commit": False})
    consumer.subscribe([topic])
    try:
        while True:
            msg = consumer.poll(1)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())
            # Debezium delete events are followed by an optional null tombstone.
            if msg.value() is not None:
                envelope = json.loads(msg.value())
                payload = envelope.get("payload", envelope)
                if payload:
                    apply_event(db, payload, msg.topic(), msg.partition(), msg.offset())
            consumer.commit(msg, asynchronous=False)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        db.close()


if __name__ == "__main__":
    main()
