from groq import Groq
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_KEY = os.getenv("GROQ_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Clients
client_groq = Groq(api_key=GROQ_KEY) if GROQ_KEY and "your_" not in GROQ_KEY else None
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

SYSTEM_PROMPT = """Sen deneyimli bir eczacı ve tıp bilgi asistanısın.
Kullanıcıya ilaçlar hakkında bilgi verirsin. Detaylı, anlaşılır ve profesyonel bir dil kullan.
MUTLAKA her cevabın sonuna şu uyarıyı ekle:

⚠️ UYARI: Bu bilgiler genel bilgilendirme amaçlıdır. Tıbbi tavsiye değildir.
Herhangi bir ilaç kullanmadan önce mutlaka doktorunuza veya eczacınıza danışınız.
Kendi kendinize ilaç kullanmayınız.
"""

def analyze_drug(
    drug_name: str,
    active_ingredient: str,
    web_info: str,
    language: str = "tr"
) -> str:
    """
    Groq ile başlar, hata alırsa sırasıyla Gemini modellerini (2.0, 1.5, Pro) dener.
    """
    prompt = f"""
İlaç Adı: {drug_name}
Etken Madde: {active_ingredient}

Web'den bulunan bilgiler:
{web_info[:3000] if web_info else "Web bilgisi bulunamadı."}

Lütfen şu başlıkları Türkçe olarak ÇOK KAPSAMLI ve AYRINTILI şekilde açıkla:

## 💊 İlaç Hakkında Genel Bilgi
(Bu ilaç nedir, temel olarak ne için üretilmiştir?)

## 🎯 Ne İşe Yarar / Hangi Hastalıklara İyi Gelir (Endikasyonlar)
(Hangi semptomları giderir? Hangi durumlarda doktorlar tarafından reçete edilir?)

## ⚗️ Etken Madde ve Etki Mekanizması
(Vücutta nasıl çalışır?)

## ⚠️ Yan Etkiler
- **Yaygın yan etkiler:** (Sık görülen hafif etkiler)
- **Ciddi yan etkiler:** (Hemen doktora başvurulması gereken durumlar)

## 🚫 Kimler Kullanmamalı (Kontrendikasyonlar)
(Hamileler, emzirenler, kronik hastalığı olanlar vb.)

## 💊 Doz Bilgisi (Genel)

## 🔄 Muadil / Eşdeğer İlaçlar

## 💡 Önemli Notlar ve Saklama Koşulları

Bilgi bulunamayan bölümlerde etken maddeye göre genel tıbbi bilgilerden yararlanarak detaylı yorumda bulun.
"""

    # 1. Groq Dene (Llama)
    if client_groq:
        try:
            response = client_groq.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq API Hatası: {str(e)}")

    # 2. Gemini Modellerini Sırayla Dene (Kota aşımına karşı dirençli)
    if GEMINI_KEY:
        models_to_try = [
            "gemini-2.0-flash",
            "gemini-flash-latest", # Usually 1.5 Flash
            "gemini-pro-latest",   # Usually 1.5/1.0 Pro
            "gemini-2.0-flash-lite", 
            "gemini-3.1-pro-preview"
        ]
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
                response = model.generate_content(full_prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                error_msg = str(e)
                # Eğer kota hatası (429) değilse ve model bulunamadı (404) değilse başka bir sorun olabilir
                print(f"Gemini {model_name} Hatası: {error_msg}")
                continue # Diğer modeli dene
                
    return "Hata: Tüm yapay zeka servisleri (Groq ve Gemini kotaları) şu an dolu. Lütfen 1 dakika sonra tekrar deneyin."

def quick_ingredient_analysis(ingredients_text: str) -> str:
    """Hızlı analiz."""
    return analyze_drug("Bilinmeyen İlaç", ingredients_text, "")


