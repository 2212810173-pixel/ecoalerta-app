# EcoAlerta v9.0 — UNAH (Ingeniería Ambiental)

Plataforma de ciencia ciudadana, denuncia ambiental y monitoreo participativo de **Calidad del Aire** y **Ruido Ambiental** en Huanta, Ayacucho.

## Ejecución rápida en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

- Sin `.streamlit/secrets.toml`, guarda automáticamente en `data/reportes.csv`.
- Para producción, copia `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml` y configura `[connections.gsheets]`, `[admin] pin`, `[privacidad] sal` y `[app] url`.
