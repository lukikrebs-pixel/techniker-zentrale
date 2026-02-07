import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
from datetime import datetime
from streamlit_calendar import calendar

# --- 1. INITIALISIERUNG & VERBINDUNG ---
st.set_page_config(page_title="Techniker Zentrale", layout="wide")

# Google Sheets Verbindung
conn = st.connection("gsheets", type=GSheetsConnection)

def hash_pw(pw): 
    return hashlib.sha256(str.encode(pw)).hexdigest()

# --- 2. DATEN-FUNKTIONEN (CRUD) ---
def get_table(sheet_name):
    return conn.read(worksheet=sheet_name, ttl=0)

def save_table(sheet_name, df):
    conn.update(worksheet=sheet_name, data=df)
    st.cache_data.clear()

# --- 3. LOGIN & REGISTRIERUNG ---
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'page' not in st.session_state: 
    st.session_state.page = "Dashboard"

if not st.session_state.logged_in:
    st.title("🔐 Techniker Zentrale")
    t_log, t_reg = st.tabs(["Anmelden", "Registrieren"])
    
    with t_log:
        u = st.text_input("Benutzername", key="login_user")
        p = st.text_input("Passwort", type="password", key="login_pw")
        if st.button("Login"):
            users_df = get_table("users")
            hashed_p = hash_pw(p)
            user_match = users_df[(users_df["username"] == u) & (users_df["password"] == hashed_p)]
            if not user_match.empty:
                st.session_state.logged_in, st.session_state.user = True, u
                st.rerun()
            else:
                st.error("Falscher Nutzer oder Passwort!")
                
    with t_reg:
        nu = st.text_input("Neuer User", key="reg_user")
        np = st.text_input("Neues PW", type="password", key="reg_pw")
        if st.button("Konto erstellen"):
            users_df = get_table("users")
            if nu and np and nu not in users_df["username"].values:
                new_user = pd.DataFrame([{"username": nu, "password": hash_pw(np)}])
                updated_df = pd.concat([users_df, new_user], ignore_index=True)
                save_table("users", updated_df)
                st.success("Konto erstellt! Bitte anmelden.")
            else:
                st.error("Name vergeben oder Felder leer.")
    st.stop()

# --- 4. DESIGN (Style bleibt wie bei dir) ---
st.markdown("""
    <style>
    .stApp { background-color: #3b7ab0; color: white; }
    div.stButton > button {
        background: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px !important; color: white !important;
        padding: 20px !important; min-height: 80px !important;
    }
    .mini-metric { padding: 15px; border-radius: 15px; text-align: center; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SEITEN-LOGIK ---
if st.session_state.page == "Dashboard":
    # Noten laden
    all_noten = get_table("noten")
    user_noten = all_noten[all_noten["username"] == st.session_state.user]
    
    # Schnitt berechnen
    if not user_noten.empty:
        s = (user_noten["note"] * user_noten["gewicht"]).sum() / user_noten["gewicht"].sum()
        s_display = f"{s:.2f}"
    else:
        s_display = "N/A"

    st.title(f"Moin, {st.session_state.user}!👋")
    st.markdown(f'<div class="mini-metric">Dein Schnitt: <b>{s_display}</b></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    if c1.button("✍️\n\nNote eintragen"): st.session_state.page = "Eintragen"; st.rerun()
    if c2.button("📊\n\nÜbersicht"): st.session_state.page = "Übersicht"; st.rerun()
    if c3.button("📅\n\nTermine"): st.session_state.page = "Termine"; st.rerun()

    # Kalender Events laden
    t_k = get_table("termine_klasse")
    t_p = get_table("termine_privat")
    t_p = t_p[t_p["username"] == st.session_state.user]
    
    events = []
    for _, t in t_k.iterrows(): events.append({"title": f"📢 {t['event']}", "start": str(t['datum']), "color": "#ff4b4b"})
    for _, t in t_p.iterrows(): events.append({"title": f"👤 {t['event']}", "start": str(t['datum']), "color": "#27ae60"})
    
    calendar(events=events, options={"locale": "de", "height": "400px"})

elif st.session_state.page == "Eintragen":
    if st.button("⬅️ Zurück"): st.session_state.page = "Dashboard"; st.rerun()
    f = st.selectbox("Fach", ["Mathe", "Physik", "IT", "Elektrotechnik", "Englisch", "VWL"])
    n = st.number_input("Note", 1.0, 6.0, 2.0, 0.1)
    g = st.radio("Gewichtung", [1, 2])
    
    if st.button("Speichern"):
        noten_df = get_table("noten")
        new_note = pd.DataFrame([{"username": st.session_state.user, "fach": f, "note": n, "gewicht": g, "datum": str(datetime.now().date())}])
        updated_df = pd.concat([noten_df, new_note], ignore_index=True)
        save_table("noten", updated_df)
        st.success("Note in Google Sheets gespeichert!")

# ... (Analoge Logik für Termine und Übersicht)