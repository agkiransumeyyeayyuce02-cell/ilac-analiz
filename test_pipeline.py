import os
from dotenv import load_dotenv
from modules.web_search import search_drug_info
from modules.llm_analyzer import analyze_drug
from modules.report_generator import generate_pdf_report

load_dotenv()

def test_full_pipeline(drug_name="Parol"):
    print(f"--- TEST BASLATILIYOR: {drug_name} ---")
    
    # 1. Web Arama Modulu
    print("\n1. Web aramasi yapiliyor...")
    web_info = search_drug_info(drug_name)
    print(f"Sorgu Tamamlandi: {len(web_info)} karakter veri bulundu.")
    
    # 2. LLM Analiz Modulu (Multi-model Test)
    print("\n2. AI Analizi yapiliyor (Sirayla Groq/Gemini denenecek)...")
    analysis = analyze_drug(drug_name, "Parasetamol", web_info)
    
    if "Hata" in analysis or "Analiz hatası" in analysis:
        print(f"!!! ANALIZ BASARISIZ: {analysis}")
    else:
        print("OK: ANALIZ BASARILI!")
        print("-" * 30)
        # Sadece ASCII kısımları yazdır veya hata alma ihtimaline karşı güvenli yazdır
        try:
            print(analysis[:500].encode('ascii', 'ignore').decode('ascii') + "...")
        except:
            print("Analiz metni olusturuldu.")
        print("-" * 30)
    
    # 3. PDF Rapor Modulu
    print("\n3. PDF Raporu olusturuluyor...")
    try:
        pdf_bytes = generate_pdf_report(drug_name, analysis)
        with open("test_report.pdf", "wb") as f:
            f.write(pdf_bytes)
        print(f"OK: PDF Basariyla Olusturuldu: {os.path.abspath('test_report.pdf')}")
    except Exception as e:
        print(f"HATA: PDF HATASI: {str(e)}")

if __name__ == "__main__":
    test_full_pipeline()
