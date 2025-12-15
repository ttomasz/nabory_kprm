# 📊 Informacje zbiorcze o naborach KPRM

Prosty dashboard Streamlit pokazujący informacje zbiorcze o naborach na stanowiska w służbie cywilnej.

[![Otwórz w Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://tt-nabory-kprm.streamlit.app/)

---

Komendy przydatne przy developmencie:
```
uv venv --python 3.13
uv pip install -r ./requirements.txt
uv run streamlit run --server.headless=true ./streamlit_app.py
uv pip install marimo[lsp] ruff
uv run marimo edit --headless eda.py
```
