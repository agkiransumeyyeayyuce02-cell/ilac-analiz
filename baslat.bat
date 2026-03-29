@echo off
echo ==============================================
echo Ilac Analiz Asistani Baslatiliyor...
echo Lutfen tarayicinin acilmasini bekleyin.
echo ==============================================
call .\venv\Scripts\activate.bat
streamlit run app.py
pause
