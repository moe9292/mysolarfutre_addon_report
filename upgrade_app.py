#!/usr/bin/env python3
"""
mySolarFuture - Web-Berechnung: Upgrade-Bericht (4 -> 6/8 Module)
Streamlit-App als Eingabe-Oberflaeche fuer generate_upgrade_report().
Start lokal:  streamlit run upgrade_app.py
"""
import base64
import tempfile
from datetime import date

import streamlit as st

from generate_upgrade_report import generate_upgrade_report

st.set_page_config(page_title="mySolarFuture - Upgrade-Bericht",
                   page_icon="\u2600\ufe0f", layout="wide")

# ---- Kopfzeile / Branding ----
st.markdown(
    """
    <div style="background:#1f3a5f;padding:16px 22px;border-radius:10px;margin-bottom:18px">
      <span style="color:#ffffff;font-size:24px;font-weight:700">mySolarFuture</span>
      <span style="color:#9bd9c0;font-size:15px;margin-left:12px">Upgrade-Bericht &middot; Web-Berechnung</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("Erstellt einen Erweiterungs-Bericht (4 \u2192 6 oder 8 Module) als PDF zum Versand an Bestandskunden.")

# ============ EINGABEN ============
with st.form("upgrade_form"):
    st.subheader("Kundendaten")
    c1, c2, c3 = st.columns(3)
    name = c1.text_input("Name", "Max Mustermann")
    street = c2.text_input("Stra\u00dfe & Nr.", "Musterstr. 5")
    city = c3.text_input("PLZ & Ort", "27755 Delmenhorst")
    c1, c2, c3 = st.columns(3)
    consumption = c1.number_input("Jahresverbrauch (kWh)", 1000, 20000, 4500, step=100)
    orientation = c2.selectbox("Ausrichtung",
                               ["S\u00fcd", "S\u00fcdost", "S\u00fcdwest", "Ost", "West", "Ost-West"])
    montage_label = c3.selectbox("Montageart", ["Schr\u00e4gdach", "Flachdach", "Balkon"])
    montage = {"Schr\u00e4gdach": "Schraegdach", "Flachdach": "Flachdach", "Balkon": "Balkon"}[montage_label]

    st.subheader("Aktuelle Anlage (Bestand)")
    c1, c2 = st.columns(2)
    base_label = c1.selectbox(
        "Vorhandener Speicher",
        ["Kein Akku", "1,92 kWh (1\u00d7 AB2000)", "3,84 kWh (2\u00d7 AB2000)", "5,76 kWh (3\u00d7 AB2000)"],
        index=1)
    baseline_battery = {"Kein Akku": 0.0, "1,92 kWh (1\u00d7 AB2000)": 1.92,
                        "3,84 kWh (2\u00d7 AB2000)": 3.84, "5,76 kWh (3\u00d7 AB2000)": 5.76}[base_label]
    smart_before = c2.checkbox("Smart Meter bereits vorhanden", value=False)

    st.subheader("Erweiterung & Preise")
    c1, c2, c3 = st.columns(3)
    target_modules = c1.selectbox("Ziel-Modulzahl", [6, 8], index=1)
    add_std = c2.number_input("Standard: zus\u00e4tzliche AB2000 (1,92 kWh)", 1, 6, 2)
    add_ent = c3.number_input("Einstieg: zus\u00e4tzliche AB2000 (1,92 kWh)", 1, 6, 1)
    c1, c2, c3 = st.columns(3)
    upgrade_price = c1.number_input("Preis Standard (EUR, inkl. Anmeldung)", 0, 20000, 4448, step=50)
    entry_price = c2.number_input("Preis Einstieg (EUR, inkl. Anmeldung)", 0, 20000, 3848, step=50)
    electricity_price = c3.number_input("Strompreis (EUR/kWh)", 0.10, 1.00, 0.34, step=0.01)
    c1, c2, c3 = st.columns(3)
    action_registration = c1.number_input("Aktion: Anmeldewert (EUR)", 0, 1000, 350, step=10)
    deadline = c2.date_input("Aktionsfrist", value=date(2026, 7, 31))
    arb_override = c3.number_input("Arbitrage EUR/Jahr (0 = automatisch)", 0, 1000, 0, step=10)

    submitted = st.form_submit_button("Bericht erstellen", type="primary")

# ============ AUSGABE ============
if submitted:
    if not name.strip():
        st.error("Bitte einen Kundennamen eingeben.")
        st.stop()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        out_path = tf.name
    try:
        generate_upgrade_report(
            customer={"name": name, "street": street, "city": city,
                      "consumption": int(consumption), "orientation": orientation},
            baseline_battery=baseline_battery,
            target_modules=int(target_modules),
            add_ab2000_std=int(add_std),
            add_ab2000_ent=int(add_ent),
            upgrade_price=int(upgrade_price),
            entry_price=int(entry_price),
            smart_before=bool(smart_before),
            montage=montage,
            electricity_price=float(electricity_price),
            action_registration=int(action_registration),
            action_deadline=deadline.strftime("%d.%m.%Y"),
            dyn_tariff_arb=(int(arb_override) if arb_override > 0 else None),
            out_path=out_path,
        )
    except Exception as e:
        st.error(f"Fehler beim Erstellen: {e}")
        st.stop()

    with open(out_path, "rb") as f:
        pdf_bytes = f.read()

    safe = name.strip().replace(" ", "_") or "Kunde"
    st.success("Bericht erstellt.")
    st.download_button("PDF herunterladen", pdf_bytes,
                       file_name=f"Upgrade-Bericht_{safe}.pdf",
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
