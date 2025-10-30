import sys
import json
from kafka import KafkaConsumer
# Güncellenmiş fonksiyonu import ediyoruz:
from smart_home_llm_processor import analyze_single_log_line

KAFKA_BROKER = "localhost:9092"
SENSOR_TOPIC = "sensor_topic"
DEVICE_LOG_TOPIC = "device_log_topic"


def start_streaming_analyst():
    try:
        consumer = KafkaConsumer(
            SENSOR_TOPIC,
            DEVICE_LOG_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='latest',
            value_deserializer=lambda v: v.decode('utf-8')
        )
        print(f"Akıllı Ev Analiz Motoru (ANLIK MOD) başlatıldı.")
        print(f"Dinlenen topic'ler: {SENSOR_TOPIC}, {DEVICE_LOG_TOPIC}")

    except Exception as e:
        print(f"Kafka'ya bağlanılamadı: {e}")
        print("Lütfen Kafka'nın (örn: Docker) çalıştığından emin olun.")
        sys.exit(1)

    # --- BATCHING MANTIĞI TAMAMEN KALDIRILDI ---

    for message in consumer:
        # 1. Veriyi al
        log_line = f"[{message.topic}]: {message.value}"
        print(f"\n[VERİ GELDİ] -> {log_line}")

        print("... Analiz için Gemini'ye gönderiliyor ...")

        # 2. Her mesaj için LLM'i çağır
        analysis_result = analyze_single_log_line(log_line)

        # 3. Sonucu anında göster
        if analysis_result:
            print("--- ANLIK ANALİZ SONUCU ---")
            print(json.dumps(analysis_result, indent=2, ensure_ascii=False))
            print("-----------------------------")


if __name__ == "__main__":
    try:
        start_streaming_analyst()
    except KeyboardInterrupt:
        print("\nAnaliz motoru durduruluyor...")