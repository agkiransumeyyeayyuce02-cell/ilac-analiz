from fpdf import FPDF
import io
import os
from datetime import datetime

class ClinicalReport(FPDF):
    def __init__(self, font_family="Helvetica"):
        super().__init__()
        self.custom_font = font_family

    def header(self):
        # Logo placeholder (Text based)
        self.set_font(self.custom_font, 'B', 18)
        self.set_text_color(0, 0, 0) # Black
        self.cell(0, 10, 'DIJITAL ECZACI ASISTANI', ln=True, align='L')
        self.set_font(self.custom_font, '', 8)
        self.cell(0, 5, 'Yapay Zeka Destekli Klinik Analiz Raporu', ln=True, align='L')
        self.ln(5)
        self.line(10, 27, 200, 27) # Horizontal line

    def footer(self):
        self.set_y(-25)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.set_font(self.custom_font, '', 8)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, f'Geliştirici: Sümeyye Ayyüce Ağkıran | Sayfa {self.page_no()}', align='C')

def generate_pdf_report(drug_name: str, analysis_text: str) -> bytes:
    """
    Profesyonel klinik görünümde PDF oluşturur.
    """
    # Font Ayarları (Windows Uyumluluk) - En başta yapıyoruz
    win_fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    arial_ttf = os.path.join(win_fonts, "arial.ttf")
    arial_bd_ttf = os.path.join(win_fonts, "arialbd.ttf")
    
    # Geçici bir nesne ile fontu kontrol et
    font_family = "DejaVu"
    if not os.path.exists(arial_ttf):
        font_family = "Helvetica"

    pdf = ClinicalReport(font_family=font_family)
    pdf.set_auto_page_break(auto=True, margin=30)

    # Fontları önce ekle, sonra sayfayı aç
    if font_family == "DejaVu":
        pdf.add_font("DejaVu", "", arial_ttf, uni=True)
        pdf.add_font("DejaVu", "B", arial_bd_ttf, uni=True)

    pdf.add_page()

    # ── BAŞLIK BİLGİLERİ ──────────────────────────────────────────────────
    pdf.ln(5)
    pdf.set_font(font_family, "B", 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"İlaç Analiz Özeti: {drug_name.upper()}", ln=True)
    
    pdf.set_font(font_family, "", 9)
    pdf.cell(0, 5, f"Rapor No: {datetime.now().strftime('%Y%m%d%H%M')}", ln=True)
    pdf.cell(0, 5, f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True)
    pdf.ln(8)

    # ── FERAGATNAME (UYARI) ────────────────────────────────────────────────
    pdf.set_fill_color(240, 240, 240) # Light grey for neutral clinical look
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(font_family, "B", 10)
    pdf.multi_cell(0, 8, 
        "DİKKAT: BU BİR TIBBİ TAVSİYE DEĞİLDİR. SADECE BİLGİLENDİRME AMAÇLIDIR. "
        "İLAÇ KULLANIMI İÇİN DOKTORUNUN TALİMATLARINA UYUNUZ.", 
        border=1, align='C', fill=True)
    pdf.ln(10)

    # ── ANALİZ İÇERİĞİ (Markdown Temizleme ve Yazma) ──────────────────────
    pdf.set_font(font_family, "", 11)
    
    lines = analysis_text.split('\n')
    for line in lines:
        if line.startswith('##'):
            pdf.ln(3)
            pdf.set_font(font_family, "B", 13)
            clean_line = line.replace('##', '').strip()
            pdf.cell(0, 10, clean_line, ln=True)
            pdf.set_font(font_family, "", 11)
        elif line.strip():
            clean_line = line.replace('**', '').replace('*', '').replace('⚠️', '').strip()
            pdf.multi_cell(0, 6, clean_line)
            pdf.ln(1)

    # PDF'i bytes olarak döndür
    pdf_output = pdf.output(dest="S")
    if isinstance(pdf_output, str):
        return pdf_output.encode("latin-1")
    return bytes(pdf_output)
