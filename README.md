# mySolarFuture - Rechentool fuer Solaranlagen

Gemeinsame Streamlit-Web-App fuer alle Solar-Berechnungen/Berichte. Eine
zentrale App (`app.py`) mit mehreren Seiten (`pages/`) statt mehrerer
getrennter Skripte - so lassen sich beliebig neue Rechner ergaenzen, ohne
Branding, Lastprofile oder Berechnungslogik zu duplizieren.

## Dateien im Repo
- `app.py`                     - Startseite/Einstieg der App (Navigation zu den Berichten)
- `pages/1_Neuanlage.py`       - Seite "Neuanlage-Bericht" (Solar-Empfehlungsbericht fuer Neukunden)
- `pages/2_Upgrade.py`         - Seite "Upgrade-Bericht" (Erweiterung 4 -> 6/8 Module fuer Bestandskunden)
- `generate_report_v5.py`      - Berechnungs-/PDF-Engine Neuanlage; liefert ausserdem Branding, Lastprofile
  und Helfer-Funktionen, die sich beide Berichte teilen
- `generate_upgrade_report.py` - Berechnungs-/PDF-Engine Upgrade-Bericht
- `requirements.txt`           - Python-Pakete
- `packages.txt`               - System-Paket poppler-utils (fuer die PDF-Vorschau)

## Lokal starten
```
pip install -r requirements.txt
streamlit run app.py
```
Die Seiten "Neuanlage" und "Upgrade" erscheinen automatisch in der Navigation links.

## Deployment auf Streamlit Community Cloud
1. Repo wie vorhanden auf GitHub pushen.
2. Auf share.streamlit.io einloggen -> "New app" -> Repo waehlen.
3. Main file path = `app.py`. Deploy.
4. `requirements.txt` und `packages.txt` werden automatisch installiert.
5. App-Link weitergeben (optional per Passwort schuetzen unter App-Settings).

## Weiterentwickeln: neuen Rechner ergaenzen
Diese App ist als gemeinsames Berechnungstool fuer Solaranlagen gedacht und
laesst sich beliebig erweitern:
1. Neue Berechnungs-/PDF-Logik als eigenes Modul im Repo-Root anlegen (analog
   zu `generate_report_v5.py` / `generate_upgrade_report.py`). Gemeinsame
   Bausteine (Branding, Lastprofile, Zeichenhelfer) aus `generate_report_v5.py`
   importieren statt zu duplizieren.
2. Eine neue Datei `pages/3_<Name>.py` mit der Streamlit-Eingabemaske
   anlegen (Formular -> Funktion aufrufen -> PDF zum Download anbieten,
   siehe `pages/1_Neuanlage.py` / `pages/2_Upgrade.py` als Vorlage).
3. Die Datei erscheint automatisch als neuer Tab in der Navigation - die
   Nummer im Dateinamen bestimmt die Reihenfolge.
4. Optional einen `st.page_link` in `app.py` ergaenzen.

## Hinweis
Preise, Modulzahl, Bestandsakku, Aktionsfrist und Strompreis sind in den
Formularen einstellbar - nichts muss im Code geaendert werden.
