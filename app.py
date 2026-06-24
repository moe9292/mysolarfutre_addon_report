#!/usr/bin/env python3
"""
mySolarFuture - Rechentool fuer Solaranlagen (Startseite)
Gemeinsame Streamlit-App fuer alle Berechnungen/Berichte. Neue Rechner als
weitere Datei unter pages/ ablegen - sie erscheinen automatisch in der
Navigation links.
Start lokal:  streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="mySolarFuture - Rechentool", page_icon="☀️", layout="wide")

st.markdown(
    """
    <div style="background:#1f3a5f;padding:16px 22px;border-radius:10px;margin-bottom:18px">
      <span style="color:#ffffff;font-size:24px;font-weight:700">mySolarFuture</span>
      <span style="color:#9bd9c0;font-size:15px;margin-left:12px">Rechentool f&uuml;r Solaranlagen</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("Über die Navigation links können Sie einen Bericht erstellen:")
st.page_link("pages/1_Neuanlage.py", label="Neuanlage-Bericht", icon="☀️")
st.page_link("pages/2_Upgrade.py", label="Upgrade-Bericht (4 → 6/8 Module)", icon="🔁")

st.divider()
st.caption(
    "Beide Berichte teilen sich Branding, Lastprofile und Berechnungslogik "
    "(generate_report_v5.py, generate_upgrade_report.py). Weitere Rechner können "
    "jederzeit als neue Datei unter pages/ ergänzt werden."
)
