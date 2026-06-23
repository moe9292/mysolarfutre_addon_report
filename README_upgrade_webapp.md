# Upgrade-Bericht - Web-Berechnung (Streamlit)

Web-Oberflaeche fuer den Upgrade-Bericht (4 -> 6/8 Module), analog zum Solarbericht.
Tobi gibt Kundendaten ein, klickt "Bericht erstellen", laedt das PDF herunter.

## Dateien im Repo
- `upgrade_app.py`           - die Streamlit-App (Startdatei)
- `generate_upgrade_report.py` - Berichtsgenerator
- `generate_report_v5.py`    - liefert Branding, Lastprofile, Helfer (gemeinsame Basis mit dem Solarbericht)
- `requirements.txt`         - Python-Pakete
- `packages.txt`             - System-Paket poppler-utils (fuer die PDF-Vorschau)

## Lokal starten
```
pip install -r requirements.txt
streamlit run upgrade_app.py
```

## Deployment auf Streamlit Community Cloud (wie beim Solarbericht)
1. Die fuenf Dateien oben in ein GitHub-Repo legen (oder in das bestehende Solarbericht-Repo).
2. Auf share.streamlit.io einloggen -> "New app" -> Repo waehlen.
3. Main file path = `upgrade_app.py`. Deploy.
4. `requirements.txt` und `packages.txt` werden automatisch installiert.
5. Tobi den App-Link geben (optional per Passwort schuetzen unter App-Settings).

## Als zweite Seite in die bestehende Solarbericht-App
Wenn die Solarbericht-App eine Streamlit-Multipage-App ist:
`upgrade_app.py` als `pages/2_Upgrade-Bericht.py` ablegen -> erscheint automatisch
als zweiter Tab in derselben App. (Den Branding-Header dann ggf. entfernen.)

## Hinweis
Preise, Modulzahl, Bestandsakku, Aktionsfrist und Strompreis sind in der App
einstellbar - nichts muss im Code geaendert werden.
