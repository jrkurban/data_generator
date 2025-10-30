import google.generativeai as genai
import json
import os

# API anahtarınızı buraya VEYA bir ortam değişkenine ekleyin
# EN GÜVENLİ YÖNTEM: API anahtarını ortam değişkeni olarak ayarlayın
# export GOOGLE_API_KEY="YOUR_API_KEY"
try:
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
except Exception as e:
    print(f"Hata: GOOGLE_API_KEY ortam değişkeni bulunamadı. Lütfen API anahtarınızı ayarlayın. {e}")
    # Alternatif (daha az güvenli):
    # genai.configure(api_key="YOUR_API_KEY_HERE")

# Gemini modelini yapılandıralım
# gemini-1.5-pro-latest: En yetenekli model, RAG ve JSON için harika
# gemini-1.5-flash-latest: Daha hızlı, daha düşük maliyetli
model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")


def analyze_log_entry(log_line):
    """
    Tek bir log satırını analiz eder, önceliklendirir ve özetler.
    Gemini API kullanır.
    """

    # Gemini'ye JSON formatında cevap vermesini zorunlu kılmak için
    # gemini-1.5-pro-latest ve üstü için:
    # generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
    # model = genai.GenerativeModel('gemini-1.5-pro-latest', generation_config=generation_config)

    # 'flash' modeli için (veya daha basit bir yöntem olarak) prompt ile JSON'a zorlayacağız

    prompt = f"""
    Sen bir kıdemli DevOps mühendisisin. Sana bir log satırı verilecek. 
    Görevin bu logu analiz edip aşağıdaki 3 bilgiyi JSON formatında çıkarmak:
    1. 'priority': (Kritik, Yüksek, Orta, Düşük) - Bu logun aciliyet seviyesi.
    2. 'actionable': (true/false) - Bu log acil bir müdahale gerektiriyor mu?
    3. 'summary': (string) - Logun ne hakkında olduğunu 1 kısa cümle ile özetle.

    Sadece ve sadece bu 3 alanı içeren geçerli bir JSON objesi döndür. 
    Örnek: {{"priority": "Kritik", "actionable": true, "summary": "Ödeme servisinde 'OutOfMemoryError' hatası tespit edildi."}}

    Analiz edilecek log:
    {log_line}
    """

    try:
        response = model.generate_content(prompt)

        # Gemini'nin çıktısındaki markdown (```json ... ```) bloğunu temizle
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()

        # Temizlenmiş metni JSON'a çevir
        analysis = json.loads(cleaned_response)
        return analysis

    except json.JSONDecodeError as e:
        print(f"LLM Analiz Hatası (JSON): {e}")
        print(f"Gemini'den gelen ham cevap: {response.text}")
        return None
    except Exception as e:
        print(f"LLM Analiz Hatası (API): {e}")
        return None


def get_solution_recommendation(log_line):
    """
    Kritik bir hata için RAG (Bilgi Bankası) kullanarak çözüm önerir.
    Gemini API kullanır.
    """
    # Bilgi bankamızı (RAG) okuyalım
    try:
        with open("knowledge_base.txt", "r", encoding="utf-8") as f:
            kb = f.read()
    except FileNotFoundError:
        kb = "Bilgi bankası (knowledge_base.txt) bulunamadı."

    prompt = f"""
    Sen bir DevOps destek asistanısın. Şirketin teknik bilgi bankası (KB) aşağıdadır:
    --- KB BAŞLANGIÇ ---
    {kb}
    --- KB BİTİŞ ---

    Sana verilen hata logunu analiz et ve bu KB'ye dayanarak adım adım bir çözüm planı öner.
    Eğer KB'de çözüm yoksa, genel tecrübene dayanarak bir çözüm öner.
    Cevabını Markdown formatında ver.

    Çözüm gereken hata: 
    {log_line}
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"LLM Çözüm Hatası (API): {e}")
        return "Çözüm önerisi getirilirken bir hata oluştu."