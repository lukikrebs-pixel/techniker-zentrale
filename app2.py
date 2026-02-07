import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar
import pandas as pd
import base64
import os
from datetime import datetime
import hashlib
import uuid

# --- 1. KONFIGURATION & VERBINDUNG ---
st.set_page_config(page_title="Techniker Zentrale", layout="wide", page_icon="🎓")

# Verbindung zur Google Tabelle (Nutzt die Daten aus den Streamlit Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. FUNKTIONEN ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return ""

def hash_pw(pw): 
    return hashlib.sha256(str.encode(pw)).hexdigest()

def load_sheet(name):
    try:
        # ttl=0 sorgt dafür, dass die Daten immer frisch von Google geladen werden
        df = conn.read(worksheet=name, ttl=0)
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

def save_sheet(name, df):
    conn.update(worksheet=name, data=df)

# Logo laden (muss im selben Ordner wie app2.py liegen)
img_base64 = get_base64_of_bin_file("logo.jpg")

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'page' not in st.session_state: 
    st.session_state.page = "Dashboard"

# --- 4. LOGIN & REGISTRIERUNG ---
if not st.session_state.logged_in:
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #3b7ab0; color: white; }}
        </style>
        """, unsafe_allow_html=True)
    
    st.title("🔐 Techniker Zentrale Login")
    t_log, t_reg = st.tabs(["Anmelden", "Registrieren"])
    
    with t_log:
        u = st.text_input("Benutzername", key="login_user")
        p = st.text_input("Passwort", type="password", key="login_pw")
        if st.button("Login"):
            users_df = load_sheet("users")
            if not users_df.empty and ((users_df['username'] == u) & (users_df['password'] == hash_pw(p))).any():
                st.session_state.logged_in, st.session_state.user = True, u
                st.rerun()
            else: 
                st.error("Benutzername oder Passwort falsch!")
            
    with t_reg:
        nu = st.text_input("Neuer User", key="reg_user")
        np = st.text_input("Neues PW", type="password", key="reg_pw")
        if st.button("Konto erstellen"):
            users_df = load_sheet("users")
            if nu and np:
                if not users_df.empty and (users_df['username'] == nu).any():
                    st.error("Name bereits vergeben!")
                else:
                    new_user = pd.DataFrame([{"username": nu, "password": hash_pw(np)}])
                    save_sheet("users", pd.concat([users_df, new_user], ignore_index=True))
                    st.success("Konto erstellt! Bitte anmelden.")
            else: 
                st.error("Bitte alle Felder ausfüllen.")
    st.stop()

# --- 5. DESIGN & CSS (EINGELOGGT) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #3b7ab0; color: white; }}
    .logo-container {{ position: fixed; top: 20px; right: 20px; z-index: 1000; }}
    .logo-container img {{ width: 110px; border-radius: 5px; }}
    div.stButton > button {{
        background: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px !important; color: white !important;
        padding: 20px !important; min-height: 80px !important;
    }}
    .mini-metric {{ padding: 15px; border-radius: 15px; text-align: center; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); }}
    .manage-box {{ background: rgba(255, 255, 255, 0.08); border-radius: 15px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); color: white; }}
    .fach-card {{ padding: 10px; border-radius: 12px; text-align: center; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 10px; font-weight: bold; }}
    </style>
    <div class="logo-container"><img src="data:image/jpg;base64,{img_base64}"></div>
    """, unsafe_allow_html=True)

def back():
    if st.button("⬅️ Zurück"): 
        st.session_state.page = "Dashboard"
        st.rerun()

# --- 6. SEITEN-LOGIK ---
if st.session_state.page == "Dashboard":
    noten_df = load_sheet("noten")
    user_noten = noten_df[noten_df['username'] == st.session_state.user] if not noten_df.empty else pd.DataFrame()
    
    # Schnitt berechnen
    if not user_noten.empty:
        s = (user_noten['Note'] * user_noten['Gewicht']).sum() / user_noten['Gewicht'].sum()
        s_display = f"{s:.2f}"
    else: 
        s, s_display = 0.0, "N/A"
    
    color = "#1e8449" if 0 < s < 1.5 else "#2ecc71" if 0 < s < 3.5 else "#f9d71c" if 0 < s < 4.5 else "#ff4b4b" if s >= 1.0 else "rgba(255,255,255,0.2)"
    
    c_g, c_s = st.columns([2, 1])
    c_g.title(f"Moin, {st.session_state.user}! 👋")
    c_s.markdown(f'<div class="mini-metric" style="background:{color}; color:{"black" if "f9d" in color else "white"}">Schnitt: <b>{s_display}</b></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    if c1.button("✍️\n\nNote eintragen", use_container_width=True): 
        st.session_state.page = "Eintragen"; st.rerun()
    if c2.button("📊\n\nÜbersicht & Löschen", use_container_width=True): 
        st.session_state.page = "Übersicht"; st.rerun()
    if c3.button("📅\n\nTermine verwalten", use_container_width=True): 
        st.session_state.page = "Termine"; st.rerun()

    # Kalender Events sammeln
    all_ev = []
    # 1. Klassen-Termine
    tk = load_sheet("termine_klasse")
    if not tk.empty:
        for _, t in tk.iterrows(): 
            all_ev.append({"title": f"📢 {t['Event']}", "start": str(t["Datum"]), "backgroundColor": "#ff4b4b"})
    
    # 2. Private Termine
    tp = load_sheet("termine_privat")
    if not tp.empty:
        user_tp = tp[tp['username'] == st.session_state.user]
        for _, t in user_tp.iterrows(): 
            all_ev.append({"title": f"👤 {t['Event']}", "start": str(t["Datum"]), "backgroundColor": "#27ae60"})
    
    calendar(events=all_ev, options={"locale": "de", "height": "450px"})
    
    if st.button("🚪 Logout"): 
        st.session_state.logged_in = False
        st.rerun()

elif st.session_state.page == "Eintragen":
    back()
    f_list = sorted(["Deutsch", "Mathe 1", "Mathe 2", "Physik", "IT", "KI", "Mechanik", "Englisch", "Elektrotechnik", "Konstruktion", "VWL/BWL", "Projektarbeit", "Steuerungstechnik"])
    f = st.selectbox("Fach", f_list)
    n = st.number_input("Note", 1.0, 6.0, 2.0, 0.1)
    g = st.radio("Gewichtung", [1, 2], format_func=lambda x: "Schulaufgabe (2x)" if x==2 else "Ex/KA (1x)")
    if st.button("Speichern"):
        noten_df = load_sheet("noten")
        new_note = pd.DataFrame([{"username": st.session_state.user, "Fach": f, "Note": n, "Gewicht": g, "ID": str(uuid.uuid4())}])
        save_sheet("noten", pd.concat([noten_df, new_note], ignore_index=True))
        st.success("Note erfolgreich in Google Sheets gespeichert!")

elif st.session_state.page == "Termine":
    back()
    st.header("📅 Termine verwalten")
    t_art = st.radio("Typ", ["Privat (Nur ich)", "Klasse (Alle)"])
    ev = st.text_input("Bezeichnung")
    da = st.date_input("Datum")
    if st.button("Termin speichern"):
        sheet = "termine_klasse" if "Klasse" in t_art else "termine_privat"
        df = load_sheet(sheet)
        new_t = {"Event": ev, "Datum": str(da)}
        if "Privat" in t_art: 
            new_t["username"] = st.session_state.user
        else: 
            new_t["User"] = st.session_state.user
        save_sheet(sheet, pd.concat([df, pd.DataFrame([new_t])], ignore_index=True))
        st.success("Termin gespeichert!")

elif st.session_state.page == "Übersicht":
    back()
    noten_df = load_sheet("noten")
    if noten_df.empty or not (noten_df['username'] == st.session_state.user).any():
        st.info("Noch keine Noten eingetragen.")
    else:
        df = noten_df[noten_df['username'] == st.session_state.user].copy()
        df['w'] = df['Note'] * df['Gewicht']
        stats = df.groupby("Fach").agg({'w':'sum', 'Gewicht':'sum'})
        stats['s'] = stats['w'] / stats['Gewicht']
        
        top_cols = st.columns(4)
        for i, (fach, row) in enumerate(stats.iterrows()):
            sn = row['s']
            c = "#1e8449" if sn < 1.5 else "#2ecc71" if sn < 3.5 else "#f9d71c" if sn < 4.5 else "#ff4b4b"
            with top_cols[i % 4]:
                st.markdown(f'<div class="fach-card" style="background:{c}; color:{"black" if "f9d" in c else "white"};">{fach}<br>{sn:.2f}</div>', unsafe_allow_html=True)
        
        st.divider()
        for f_name in sorted(df['Fach'].unique()):
            st.markdown(f'<div class="manage-box"><h4>📦 {f_name}</h4>', unsafe_allow_html=True)
            f_noten = df[df['Fach'] == f_name]
            for _, n in f_noten.iterrows():
                nc1, nc2, nc3 = st.columns([0.4, 0.4, 0.2])
                nc1.write(f"Note: **{n['Note']}**")
                nc2.write(f"Gewicht: {n['Gewicht']}x")
                if nc3.button("🗑️", key=f"del_{n['ID']}"):
                    new_df = noten_df[noten_df['ID'] != n['ID']]
                    save_sheet("noten", new_df)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)