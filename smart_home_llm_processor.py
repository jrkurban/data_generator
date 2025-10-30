import google.generativeai as genai
import json
import os

try:
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    if not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY ortam değişkeni bulunamadı.")
except Exception as e:
    print(f"Hata: API anahtarı yapılandırılamadı. {e}")

model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

# RAG için Bilgi Bankası (Kurallar)
KNOWLEDGE_BASE = """
- Ev sıcaklığı 20 derecenin altında (Kritik) veya 26 derecenin üstünde (Yüksek) olmamalıdır.
- Nem %40'ın altında (Kuru) veya %60'ın üstünde (Nemli) ise bu 'Orta' öncelikli bir durumdur.
- 'ERROR' içeren cihaz logları 'Kritik' önceliklidir.
- 'WARNING' içeren cihaz logları 'Yüksek' önceliklidir.
- 'maintenance' durumundaki sensörler 'Orta' önceliklidir.
"""


def analyze_single_log_line(log_line):
    """
    Kafka'dan gelen TEK BİR log satırını analiz eder.
    """

    prompt = f"""
    Sen bir akıllı ev asistanısın. Görevin, sana "GELEN VERİ" başlığı altında verilen anlık tek bir logu veya sensör verisini analiz etmektir.

    Bilgi Bankan (KB) ve Kuralların:
    {KNOWLEDGE_BASE}

    Görevin:
    1.  Bu tekil verinin "önemli" olup olmadığını belirle.
    2.  Bu veriye dayanarak bir eylem (todo) gerekip gerekmediğini belirle.

    Çıktını *sadece* şu JSON formatında ver:
    {{
      "is_alert": (true/false),
      "priority": "Kritik/Yüksek/Orta/Düşük",
      "alert_message": "Eğer önemliyse (örn: 'SICAKLIK KRİTİK SEVİYEDE DÜŞÜK!') veya 'Durum normal.'",
      "action_needed": "Eğer bir eylem gerekiyorsa (örn: 'Termostatı kontrol et.') veya null"
    }}

    --- GELEN VERİ ---
    {log_line}
    ---
    """

    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        analysis = json.loads(cleaned_response)
        return analysis

    except json.JSONDecodeError as e:
        print(f"LLM Analiz Hatası (JSON): {e}")
        print(f"Gemini'den gelen ham cevap: {response.text}")
        return None
    except Exception as e:
        print(f"LLM Analiz Hatası (API): {e}")
        return None