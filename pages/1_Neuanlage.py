#!/usr/bin/env python3
"""
mySolarFuture - Web-Berechnung: Solar-Empfehlungsbericht (Neuanlage)
Seite "Neuanlage" im gemeinsamen Rechentool. Eingabe-Oberflaeche fuer generate_report().
Start lokal:  streamlit run app.py
"""
import base64
import tempfile

import streamlit as st

from generate_report_v5 import generate_report

st.set_page_config(page_title="mySolarFuture - Neuanlage-Bericht",
                   page_icon="☀️", layout="wide")

# ---- Kopfzeile / Branding ----
st.markdown(
    """
    <div style="background:#1f3a5f;padding:16px 22px;border-radius:10px;margin-bottom:18px">
      <span style="color:#ffffff;font-size:24px;font-weight:700">mySolarFuture</span>
      <span style="color:#9bd9c0;font-size:15px;margin-left:12px">Neuanlage-Bericht &middot; Web-Berechnung</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("Erstellt einen Solar-Empfehlungsbericht (Paketauswahl, Wirtschaftlichkeit) als PDF fuer Neukunden.")

# ============ EINGABEN ============
with st.form("neuanlage_form"):
    st.subheader("Kundendaten")
    c1, c2, c3 = st.columns(3)
    anrede = c1.selectbox("Anrede", ["Herr", "Frau"], index=0)
    name = c2.text_input("Vor- und Nachname", "Max Mustermann")
    street = c3.text_input("Straße & Nr.", "Musterstr. 5")
    c1, c2 = st.columns(2)
    city = c1.text_input("PLZ & Ort", "27755 Delmenhorst")
    consumption = c2.number_input("Jahresverbrauch (kWh)", 500, 20000, 4000, step=100)

    c1, c2, c3 = st.columns(3)
    orientation = c1.selectbox("Ausrichtung",
                               ["Süd", "Südost", "Südwest", "Ost", "West", "Ost-West"])
    montage_label = c2.selectbox("Montageart", ["Schrägdach", "Flachdach", "Balkon"])
    montage = {"Schrägdach": "Schraegdach", "Flachdach": "Flachdach", "Balkon": "Balkon"}[montage_label]
    report_type = "balkon" if montage_label == "Balkon" else "dach"
    electricity_price_ct = c3.number_input("Strompreis (ct/kWh)", 20.0, 60.0, 36.0, step=0.5,
                                           help="Aktueller Strompreis des Kunden")

    max_modules_label = st.selectbox(
        "Max. Modulanzahl (Dachanlage)",
        ["Keine Begrenzung", "4 Module", "6 Module"],
        index=0,
        help="Begrenzt durch Dachfläche - gilt nur für Dachanlagen",
    )
    max_modules_map = {"Keine Begrenzung": None, "4 Module": 4, "6 Module": 6}

    st.caption(
        "Dachanlage: automatische Paketauswahl (Solar Smart/Smart+/Pro/Max/Max+) je nach Jahresverbrauch.  ·  "
        "Balkon: feste Paketauswahl Solar Balkon / Balkon+ (2 Module, max. 800 W)."
    )

    submitted = st.form_submit_button("Bericht erstellen", type="primary")

# ============ AUSGABE ============
if submitted:
    if not name.strip():
        st.error("Bitte einen Kundennamen eingeben.")
        st.stop()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        out_path = tf.name
    try:
        generate_report(
            customer={"name": f"{anrede} {name.strip()}", "street": street, "city": city,
                      "consumption": int(consumption), "orientation": orientation},
            montage=montage,
            report_type=report_type,
            electricity_price=electricity_price_ct / 100,
            max_modules=max_modules_map[max_modules_label],
            output_path=out_path,
        )
    except Exception as e:
        st.error(f"Fehler beim Erstellen: {e}")
        st.stop()

    with open(out_path, "rb") as f:
        pdf_bytes = f.read()

    safe = name.strip().replace(" ", "_") or "Kunde"
    st.success("Bericht erstellt.")
    st.download_button("PDF herunterladen", pdf_bytes,
                       file_name=f"Solar-Bericht_{safe}.pdf",
                       mime="application/pdf", type="primary")

    # Vorschau (Seitenbilder, falls poppler verfuegbar)
    try:
        from pdf2image import convert_from_bytes
        st.markdown("**Vorschau**")
        for img in convert_from_bytes(pdf_bytes, dpi=110):
            st.image(img, use_container_width=True)
    except Exception:
        b64 = base64.b64encode(pdf_bytes).decode()
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700"></iframe>',
            unsafe_allow_html=True)
