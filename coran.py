import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random
import requests # Nécessaire pour envoyer l'alerte mail

# --- 1. CONFIGURATION ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if "user_connected" not in st.session_state: st.session_state["user_connected"] = None
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "ramadan_mode" not in st.session_state: st.session_state["ramadan_mode"] = False
if "langue" not in st.session_state: st.session_state["langue"] = "Français"
if "page" not in st.session_state: st.session_state["page"] = "home"
if "view" not in st.session_state: st.session_state["view"] = "login"

# --- CONFIGURATION ALERTE MAIL (FORMSPREE) ---
URL_FORMSPREE = "https://formspree.io/f/xrebqybk"

def envoyer_alerte_mail(pseudo):
    donnees = {
        "sujet": "🔔 Nouvelle inscription sur Bilan Coran",
        "utilisateur": pseudo,
        "message": f"Salam Yael, l'utilisateur '{pseudo}' attend sa validation pour accéder à l'application."
    }
    try:
        requests.post(URL_FORMSPREE, data=donnees)
    except:
        pass # Évite de faire planter l'app si le réseau échoue

# --- 2. GESTION DES FICHIERS ---
dossier = os.path.dirname(__file__)
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv")
FORGOT_FILE = os.path.join(dossier, "forgot.csv")

def init_file(file, columns):
    if not os.path.exists(file):
        pd.DataFrame(columns=columns).to_csv(file, index=False)
    else:
        if os.stat(file).st_size == 0:
            pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["pseudo", "password", "role"])
init_file(DEMANDES_FILE, ["pseudo", "password"])
init_file(FORGOT_FILE, ["pseudo"])

# Bloc de secours Admin Yael
udb_check = pd.read_csv(USERS_FILE)
if "Yael" not in udb_check["pseudo"].values:
    yael_row = pd.DataFrame([["Yael", "Yassine05", "Admin"]], columns=["pseudo", "password", "role"])
    pd.concat([udb_check, yael_row], ignore_index=True).to_csv(USERS_FILE, index=False)

def charger_data():
    suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
    file = os.path.join(dossier, f"sauvegarde_{suffixe}.csv")
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        df = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df.index.name = "Nom"
        df.to_csv(file)
        return df
    return pd.read_csv(file, index_col=0)

# --- 3. TRADUCTIONS ---
TRAD = {
    "Français": {
        "titre_norm": "📖 Bilan Coran", "titre_ram": "🌙 Bilan Ramadan", "etat": "📊 État actuel",
        "prog": "📊 Progression Visuelle", "maj": "📝 Mise à jour", "calc": "🔄 Calcul Date",
        "plan": "📅 Planning 30 jours", "params": "⚙️ Paramètres", "admin": "🔔 Notifs",
        "logout": "🔒 Déconnexion", "hadith_btn": "✨ GÉNÉRER UN HADITH", "wa": "💬 WhatsApp"
    },
    "العربية": {
        "titre_norm": "📖 حصيلة القرآن", "titre_ram": "🌙 حصيلة رمضان", "etat": "📊 الحالة الراهنة",
        "prog": "📊 التقدم البصري", "maj": "📝 تحديث", "calc": "🔄 حساب التاريخ",
        "plan": "📅 جدول 30 يوم", "params": "⚙️ الإعدادات", "admin": "🔔 تنبيهات",
        "logout": "🔒 خروج", "hadith_btn": "✨ توليد حديث شريف", "wa": "💬 واتساب"
    }
}
L = TRAD[st.session_state["langue"]]

# --- 4. STYLE ---
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"
st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"<style>h1,h2,h3,p,label,span {{color:{COLOR}!important; text-align:center;}} div.stButton>button {{width:100%; border-radius:10px; border:2px solid {COLOR}; color:{COLOR}; font-weight:bold; height:3.5em;}} div.stButton>button:hover {{background-color:{COLOR}; color:white;}} .stProgress > div > div > div > div {{background-color:{COLOR}!important;}}</style>", unsafe_allow_html=True)

# --- 5. AUTHENTIFICATION ---
if not st.session_state["auth"]:
    st.title("🔐 Accès")
    if st.session_state["view"] == "login":
        u = st.text_input("Pseudo")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            db = pd.read_csv(USERS_FILE)
            match = db[(db["pseudo"].astype(str) == str(u)) & (db["password"].astype(str) == str(p))]
            if not match.empty:
                st.session_state["auth"], st.session_state["user_connected"] = True, str(u)
                st.session_state["is_admin"] = (match.iloc[0]["role"] == "Admin")
                st.rerun()
            else: st.error("Identifiants incorrects.")
        c1, c2 = st.columns(2)
        if c1.button("S'inscrire"): st.session_state["view"] = "signup"; st.rerun()
        if c2.button("Mdp oublié ?"): st.session_state["view"] = "forgot"; st.rerun()
    elif st.session_state["view"] == "signup":
        nu = st.text_input("Nouveau Pseudo")
        np = st.text_input("Nouveau Mdp", type="password")
        if st.button("Envoyer la demande"):
            if nu and np:
                ddb = pd.read_csv(DEMANDES_FILE)
                pd.concat([ddb, pd.DataFrame([[nu, np]], columns=["pseudo", "password"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
                
                # --- ENVOI DE L'ALERTE MAIL ---
                envoyer_alerte_mail(nu)
                
                st.success("C'est envoyé ! Tu recevras un mail de confirmation après validation."); st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    elif st.session_state["view"] == "forgot":
        fu = st.text_input("Entre ton Pseudo")
        if st.button("Notifier Yael"):
            fdb = pd.read_csv(FORGOT_FILE)
            if fu and fu not in fdb["pseudo"].values:
                pd.concat([fdb, pd.DataFrame([[fu]], columns=["pseudo"])], ignore_index=True).to_csv(FORGOT_FILE, index=False)
            
            # Optionnel: Tu peux aussi envoyer un mail pour les oublis de MDP
            envoyer_alerte_mail(f"MOT DE PASSE OUBLIÉ : {fu}")
            
            st.success("Demande transmise à Yael !"); st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 6. LOGIQUE D'AFFICHAGE ---
df_complet = charger_data()
auj = date.today()
df_view = df_complet if st.session_state["is_admin"] else df_complet[df_complet.index == st.session_state["user_connected"]]

with st.sidebar:
    st.title(f"👤 {st.session_state['user_connected']}")
    if st.button("🏠 Accueil"): st.session_state["page"] = "home"; st.rerun()
    if st.button(L["params"]): st.session_state["page"] = "params"; st.rerun()
    if st.session_state["is_admin"]:
        nb = len(pd.read_csv(DEMANDES_FILE)) + len(pd.read_csv(FORGOT_FILE))
        if st.button(f"{L['admin']} ({nb})"): st.session_state["page"] = "admin"; st.rerun()
    st.divider()
    m_label = "📖 Mode Normal" if st.session_state["ramadan_mode"] else "🌙 Mode Ramadan"
    if st.button(m_label):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]; st.rerun()
    if st.button(L["logout"]): st.session_state["auth"] = False; st.rerun()

# (Le reste de ton code original pour les pages Params, Admin et Accueil continue ici...)
# ...
