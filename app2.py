import streamlit as st
import json
import os
import hashlib
import pandas as pd
import base64
from datetime import datetime
from streamlit_calendar import calendar

# --- 1. FUNKTIONEN ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

IMG_PATH = "logo.jpg" 
img_base64 = get_base64_of_bin_file(IMG_PATH)

USER_DB = "users.json"
GLOBAL_TERMINE = "global_termine.json"

def lade_global_termine():
    if os.path.exists(GLOBAL_TERMINE):
        with open(GLOBAL_TERMINE, "r") as f: return json.load(f)
    return []

def speichere_global_termine(termine):
    with open(GLOBAL_TERMINE, "w") as f: json.dump(termine, f)

def hash_pw(pw): return hashlib.sha256(str.encode(pw)).hexdigest()

def lade_benutzer():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f: return json.load(f)
    return {}

def speichere_benutzer(users):
    with open(USER_DB, "w") as f: json.dump(users, f)

def lade_user_daten(username):
    filename = f"noten_{username}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try: 
                d = json.load(f)
                if "noten" not in d: d["noten"] = []
                if "termine" not in d: d["termine"] = []
                return d
            except: return {"noten": [], "termine": []}
    return {"noten": [], "termine": []}

def speichere_user_daten(username, daten):
    filename = f"noten_{username}.json"
    with open(filename, "w") as f: json.dump(daten, f)

# --- 2. INITIALISIERUNG ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = "Dashboard"

# --- 3. LOGIN & REGISTRIERUNG ---
if not st.session_state.logged_in:
    st.set_page_config(page_title="Login - Techniker Zentrale", page_icon="🔐")
    st.title("🔐 Techniker Zentrale")
    t_log, t_reg = st.tabs(["Anmelden", "Registrieren"])
    with t_log:
        u = st.text_input("Benutzername", key="login_user")
        p = st.text_input("Passwort", type="password", key="login_pw")
        if st.button("Login"):
            db = lade_benutzer()
            if u in db and db[u] == hash_pw(p):
                st.session_state.logged_in, st.session_state.user = True, u
                st.session_state.daten = lade_user_daten(u)
                st.rerun()
            else: st.error("Benutzername oder Passwort falsch!")
    with t_reg:
        nu = st.text_input("Neuer User", key="reg_user")
        np = st.text_input("Neues PW", type="password", key="reg_pw")
        if st.button("Konto erstellen"):
            db = lade_benutzer()
            if nu and np and nu not in db:
                db[nu] = hash_pw(np); speichere_benutzer(db)
                st.success("Konto erstellt! Bitte oben anmelden.")
            else: st.error("Name vergeben oder Felder leer.")
    st.stop()

# --- 4. DESIGN ---
st.set_page_config(page_title="Techniker Zentrale", layout="wide")
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
    .manage-box {{ background: rgba(255, 255, 255, 0.08); border-radius: 15px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); }}
    .fach-card {{ padding: 10px; border-radius: 12px; text-align: center; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 10px; font-weight: bold; }}
    </style>
    <div class="logo-container"><img src="data:image/jpg;base64,{img_base64}"></div>
    """, unsafe_allow_html=True)

def back():
    if st.button("⬅️ Zurück"): st.session_state.page = "Dashboard"; st.rerun()

# --- 5. SEITEN ---
if st.session_state.page == "Dashboard":
    noten = st.session_state.daten.get("noten", [])
    s = sum(n["Note"]*n["Gewicht"] for n in noten) / sum(n["Gewicht"] for n in noten) if noten else 0.0
    s_display = f"{s:.2f}" if noten else "N/A"
    color = "#1e8449" if 0 < s < 1.5 else "#2ecc71" if 0 < s < 3.5 else "#f9d71c" if 0 < s < 4.5 else "#ff4b4b" if s >= 1.0 else "rgba(255,255,255,0.2)"
    
    c_g, c_s = st.columns([2, 1])
    c_g.title(f"Moin, {st.session_state.user}! 👋")
    c_s.markdown(f'<div class="mini-metric" style="background:{color}; color:{"black" if "f9d" in color else "white"}">Schnitt: <b>{s_display}</b></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    if c1.button("✍️\n\nNote eintragen", use_container_width=True): st.session_state.page = "Eintragen"; st.rerun()
    if c2.button("📊\n\nÜbersicht & Löschen", use_container_width=True): st.session_state.page = "Übersicht"; st.rerun()
    if c3.button("📅\n\nTermine verwalten", use_container_width=True): st.session_state.page = "Termine"; st.rerun()

    st.divider()
    all_ev = []
    for t in lade_global_termine(): all_ev.append({"title": f"📢 {t['Event']}", "start": t["Datum"], "backgroundColor": "#ff4b4b" if "SA" in t['Event'].upper() else "#3b7ab0"})
    for t in st.session_state.daten.get("termine", []): all_ev.append({"title": f"👤 {t['Event']}", "start": t["Datum"], "backgroundColor": "#27ae60"})
    calendar(events=all_ev, options={"locale": "de", "height": "450px"})
    if st.button("🚪 Logout"): st.session_state.logged_in = False; st.rerun()

elif st.session_state.page == "Eintragen":
    back()
    f_list = sorted(["Deutsch", "Mathe 1", "Mathe 2", "Physik", "IT", "KI", "Mechanik", "Englisch", "Elektrotechnik", "Konstruktion", "VWL/BWL", "Projektarbeit", "Steuerungstechnik"])
    f = st.selectbox("Fach", f_list)
    n = st.number_input("Note", 1.0, 6.0, 2.0, 0.1)
    g = st.radio("Gewichtung", [1, 2], format_func=lambda x: "Schulaufgabe (2x)" if x==2 else "Ex/KA (1x)")
    if st.button("Speichern"):
        st.session_state.daten["noten"].append({"Fach": f, "Note": n, "Gewicht": g, "ID": datetime.now().timestamp()})
        speichere_user_daten(st.session_state.user, st.session_state.daten); st.success("Gespeichert!")

elif st.session_state.page == "Termine":
    back()
    st.header("📅 Termine verwalten")
    t_art = st.radio("Typ", ["Privat (Nur ich)", "Klasse (Alle)"])
    ev = st.text_input("Bezeichnung")
    da = st.date_input("Datum")
    if st.button("Termin speichern"):
        if "Klasse" in t_art:
            tg = lade_global_termine(); tg.append({"Event": ev, "Datum": str(da), "User": st.session_state.user}); speichere_global_termine(tg)
        else:
            if "termine" not in st.session_state.daten: st.session_state.daten["termine"] = []
            st.session_state.daten["termine"].append({"Event": ev, "Datum": str(da)}); speichere_user_daten(st.session_state.user, st.session_state.daten)
        st.success("Erfolgreich hinzugefügt!"); st.rerun()
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📢 Klasse")
        tg = lade_global_termine()
        for i, t in enumerate(tg):
            c_text, c_del = st.columns([0.8, 0.2])
            c_text.write(f"**{t['Datum']}**: {t['Event']}")
            if c_del.button("🗑️", key=f"tg_{i}"):
                tg.pop(i); speichere_global_termine(tg); st.rerun()
    with col2:
        st.subheader("👤 Privat")
        tp = st.session_state.daten.get("termine", [])
        for i, t in enumerate(tp):
            c_text, c_del = st.columns([0.8, 0.2])
            c_text.write(f"**{t['Datum']}**: {t['Event']}")
            if c_del.button("🗑️", key=f"tp_{i}"):
                tp.pop(i); speichere_user_daten(st.session_state.user, st.session_state.daten); st.rerun()

elif st.session_state.page == "Übersicht":
    back()
    st.header("📊 Deine Übersicht")
    noten_liste = st.session_state.daten.get("noten", [])
    if not noten_liste:
        st.info("Noch keine Noten eingetragen.")
    else:
        df = pd.DataFrame(noten_liste)
        # Schnitte pro Fach berechnen
        df['w'] = df['Note'] * df['Gewicht']
        stats = df.groupby("Fach").agg({'w':'sum', 'Gewicht':'sum'})
        stats['s'] = stats['w'] / stats['Gewicht']
        
        # 1. Farbige Fach-Karten oben anzeigen
        top_cols = st.columns(4)
        for i, (fach, row) in enumerate(stats.iterrows()):
            sn = row['s']
            c = "#1e8449" if sn < 1.5 else "#2ecc71" if sn < 3.5 else "#f9d71c" if sn < 4.5 else "#ff4b4b"
            with top_cols[i % 4]:
                st.markdown(f'<div class="fach-card" style="background:{c}; color:{"black" if "f9d" in c else "white"};">{fach}<br>{sn:.2f}</div>', unsafe_allow_html=True)
        
        st.divider()
        # 2. Detail-Listen zum Löschen
        for f_name in sorted(df['Fach'].unique()):
            with st.container():
                st.markdown(f'<div class="manage-box"><h4>📦 {f_name}</h4>', unsafe_allow_html=True)
                for i, n in enumerate(noten_liste):
                    if n['Fach'] == f_name:
                        nc1, nc2, nc3 = st.columns([0.4, 0.4, 0.2])
                        nc1.write(f"Note: **{n['Note']}**")
                        nc2.write(f"Gewicht: {n['Gewicht']}x")
                        u_key = n.get('ID', f"old_{i}")
                        if nc3.button("🗑️", key=f"del_{i}_{u_key}"):
                            st.session_state.daten["noten"].remove(n)
                            speichere_user_daten(st.session_state.user, st.session_state.daten); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)