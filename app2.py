import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Diagnose Techniker Zentrale")

# --- DIAGNOSE ABSCHNITT ---
st.title("🔍 Datenbank-Check")

# 1. Check: Existieren die Secrets überhaupt?
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    st.success("✅ Secrets wurden im korrekten Format [connections.gsheets] gefunden.")
else:
    st.error("❌ Fehler: Die Secrets fehlen oder sind falsch benannt! (Muss [connections.gsheets] sein)")
    st.info("Prüfe in Streamlit Cloud unter Settings -> Secrets, ob der Header [connections.gsheets] ganz oben steht.")
    st.stop()

# 2. Check: Verbindung aufbauen
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.success("✅ Verbindung zum GSheets-Modul steht.")
except Exception as e:
    st.error(f"❌ Verbindungsfehler: {e}")
    st.stop()

# 3. Check: Schreibtest
st.write("Versuche Test-Eintrag in Blatt 'users'...")
if st.button("Schreibrechte jetzt testen"):
    try:
        # Wir laden die aktuelle Tabelle
        test_df = conn.read(worksheet="users", ttl=0)
        # Wir hängen eine Test-Zeile an
        test_row = pd.DataFrame([{"username": "TEST_USER", "password": "123"}])
        new_df = pd.concat([test_df, test_row], ignore_index=True)
        
        # Der kritische Moment: Das Update
        conn.update(worksheet="users", data=new_df)
        st.balloons()
        st.success("🔥 WAHNSINN! Es hat geklappt! Schreibrechte sind aktiv.")
    except Exception as e:
        st.error(f"❌ SCHREIBFEHLER: {e}")
        st.warning("Das bedeutet meistens: Deine E-Mail (client_email) wurde in Google Sheets nicht als EDITOR hinzugefügt.")

st.divider()
st.info("Sobald dieser Test 'Grün' zeigt, können wir den richtigen App-Code wieder einfügen.")