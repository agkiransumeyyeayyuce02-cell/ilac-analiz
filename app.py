import streamlit as st
from PIL import Image
import io
import os
from dotenv import load_dotenv

from modules.ocr_reader import extract_text_from_image
from modules.gemini_vision import analyze_image_with_gemini
from modules.web_search import search_drug_info
from modules.llm_analyzer import analyze_drug, quick_ingredient_analysis
from modules.report_generator import generate_pdf_report
from utils.image_utils import preprocess_image
from utils.text_utils import clean_ocr_text, extract_drug_name

load_dotenv()

# ── Sayfa ayarları ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hekim & Eczacı Dijital Asistanı",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Profesyonel Tıbbi CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
    :root {
        --primary: #005f73;
        --secondary: #0a9396;
        --accent: #94d2bd;
        --bg: #f8f9fa;
    }
    .stApp { background-color: var(--bg); }
    .main-header {
        background: linear-gradient(135deg, #005f73 0%, #0a9396 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    .status-badge {
        padding: 4px 12px;
        border-radius: 20px;
        background: #e9ecef;
        font-size: 0.8rem;
        font-weight: 600;
        color: #495057;
    }
    .warning-banner {
        background: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    @media (max-width: 600px) {
        .main-header { padding: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# ── SideBar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=100) # Placeholder medical logo
    st.title("Dijital Eczacı")
    st.info("İlaç kutusunu taratın veya adını yazın, AI motorumuz (Gemini/Groq) anında analiz etsin.")
    
    st.divider()
    st.subheader("Hızlı Test")
    if st.button("Parol Analiz Et"):
        st.session_state.manual_drug = "Parol"
    if st.button("Aspirin Analiz Et"):
        st.session_state.manual_drug = "Aspirin"
    
    st.divider()
    st.caption("👤 Geliştirici: Sümeyye Ayyüce Ağkıran")

# ── Ana Başlık ───────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1 style='margin:0;'>💊 İlaç Analiz ve Raporlama Sistemi</h1>
    <p style='margin:0; opacity:0.9;'>Yapay Zeka Destekli Klinik Bilgi Asistanı</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="warning-banner">
    <strong>⚠️ YASAL UYARI:</strong> Bu uygulama yalnızca akademik ve bilgilendirme amaçlıdır. 
    Tıbbi bir teşhis, tedavi veya profesyonel tavsiye yerine geçmez. Karar vermeden önce bir hekime danışınız.
</div>
""", unsafe_allow_html=True)

# ── Giriş Alanı ────────────────────────────────────────────────────────────
main_col1, main_col2 = st.columns([1, 1])

with main_col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📸 Görsel Girişi")
    tab_cam, tab_file = st.tabs(["📷 Kamera", "📁 Dosya Yükle"])
    
    with tab_cam:
        camera_photo = st.camera_input("İlaç Kutusunu Merkeze Alın")
    
    with tab_file:
        uploaded_file = st.file_uploader(
            "Net bir fotoğraf seçin",
            type=["jpg", "jpeg", "png", "webp"],
            help="İlacın üzerindeki yazıların okunabilir olduğundan emin olun."
        )
    st.markdown('</div>', unsafe_allow_html=True)

with main_col2:
    st.markdown('<div class="card" style="height: 100%;">', unsafe_allow_html=True)
    st.subheader("✍️ Manuel Giriş")
    manual_input = st.text_input(
        "İlaç veya Etken Madde Adı", 
        value=st.session_state.get('manual_drug', ""),
        placeholder="Örn: Parasetamol, Ibuprofen..."
    )
    
    st.markdown("""
    <br>
    <p style='font-size:0.9rem; color:#666;'>
    <strong>İpucu:</strong> Görüntü analizi hem yazıları okur hem de kutunun tasarımından ilacı tanır. 
    Manuel girişte ise doğrudan web üzerindeki en güncel prospektüs verileri taranır.
    </p>
    """, unsafe_allow_html=True)
    
    analyze_btn = st.button(
        "🔍 ANALİZİ BAŞLAT",
        type="primary",
        use_container_width=True,
        disabled=(camera_photo is None and uploaded_file is None and not manual_input)
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ── Analiz Akışı ────────────────────────────────────────────────────────────
if analyze_btn:
    image_source = camera_photo or uploaded_file
    image = None
    if image_source:
        image = Image.open(io.BytesIO(image_source.getvalue()))
        image = preprocess_image(image)
        st.image(image, caption="Analize Hazır Görsel", width=300)

    drug_name = ""
    active_ingredient = ""
    gemini_data = {}

    with st.status("🧬 İlaç Tanımlanıyor...", expanded=True) as status:
        # ADIM 1: Görsel analiz
        if image:
            st.write("🔍 **Gemini 2.0 Vision** devrede...")
            try:
                gemini_data = analyze_image_with_gemini(image)
                drug_name = gemini_data.get("ilac_adi", "")
                active_ingredient = gemini_data.get("etken_madde", "")
                st.write(f"✨ Tespit Edilen: **{drug_name}**")
            except Exception:
                st.write("⚠️ Yapay zeka görme hatası, OCR moduna geçiliyor...")

            if not drug_name:
                st.write("🔡 Metinler taranıyor (EasyOCR)...")
                raw_text = extract_text_from_image(image)
                cleaned = clean_ocr_text(raw_text)
                drug_name = extract_drug_name(cleaned)
                active_ingredient = cleaned

        elif manual_input:
            drug_name = manual_input
            active_ingredient = manual_input

        # ADIM 2: Web / Bilgi Bankası Taraması
        st.write(f"🌐 **{drug_name}** için literatür taranıyor...")
        web_info = search_drug_info(drug_name)
        
        # ADIM 3: LLM Analizi
        st.write("🧠 Klinik yorum oluşturuluyor...")
        analysis = analyze_drug(drug_name, active_ingredient, web_info)

        status.update(label="✅ Analiz Raporu Hazır!", state="complete")

    # ── Sonuçların Sunumu ───────────────────────────────────────────────────
    st.divider()
    
    # Bilgi Kartları
    if gemini_data and "hata" not in gemini_data:
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1: st.metric("İlaç Adı", gemini_data.get("ilac_adi", "-"))
        with m_col2: st.metric("Etken Madde", gemini_data.get("etken_madde", "-"))
        with m_col3: st.metric("Form", gemini_data.get("form", "-"))

    # Ana Rapor Alanı (Hatayı önlemek için HTML div parçalamaktan kaçınıyoruz)
    with st.container(border=True):
        st.markdown(analysis)

    # İşlem butonları
    st.divider()
    res_col1, res_col2 = st.columns(2)
    
    with res_col1:
        st.download_button(
            label="📄 RESMİ RAPORU İNDİR (PDF)",
            data=generate_pdf_report(drug_name, analysis),
            file_name=f"Rapor_{drug_name}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with res_col2:
        # Streamlit'te butonlar otomatik rerun tetikler, on_click hatayı tetikleyebiliyordu.
        st.button("🔄 YENİ ANALİZ", use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────
st.divider()
f_col1, f_col2 = st.columns([2, 1])
with f_col1:
    st.caption("🚀 Teknoloji: Gemini 2.0 Flash · Groq LLaMA 3.1 · DuckDuckGo Semantic Search")
with f_col2:
    st.caption("🛡️ Veri Güvenliği: Yüklenen görseller kaydedilmez.")

