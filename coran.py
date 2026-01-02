import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random
import requests

# --- 1. CONFIGURATION NOTIFICATIONS ---
URL_FORMSPREE = "https://formspree.io/f/xrebqybk"
EMAILJS_SERVICE_ID = "service_v9ebnic"  # Ton nouvel ID Outlook
EMAILJS_TEMPLATE_ID = "template_rghkouc"
EMAILJS_PUBLIC_KEY = "LUCKx4YnQSQ3ncrue"

# Fonction pour notifier Yael
def envoyer_alerte_yael(pseudo, type_alerte="Inscription"):
    donnees = {"Objet": f"🔔 Bilan Coran : {type_alerte}", "Utilisateur": pseudo}
    try: requests.post(URL_FORMSPREE, data=donnees)
    except: pass

# Fonction pour envoyer le mail automatique à l'utilisateur
def envoyer_confirmation_utilisateur(pseudo, email_dest):
    url = "https://api.emailjs.com/api/v1.0/email/send"
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "template_params": {
            "to_name": pseudo,
            "user_email": email_dest,  # Correspond à {{user_email}} dans EmailJS
            "message": "Ton compte Bilan Coran a été validé ! Tu peux maintenant te connecter."
        }
    }
    try: requests.post(url, json=payload)
    except: pass

# --- 2. CONFIGURATION SESSION ---
for key, val in {
    "auth": False, "user_connected": None, "is_admin": False, 
    "ramadan_mode": False, "langue": "Français", "page": "home", "view": "login"
}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 3. GESTION DES FICHIERS ---
dossier = os.path.dirname(__file__)
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv")
FORGOT_FILE = os.path.join(dossier, "forgot.csv")

def init_file(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["pseudo", "password", "role", "user_email"])
init_file(DEMANDES_FILE, ["pseudo", "password", "user_email"])
init_file(FORGOT_FILE, ["pseudo"])

# Protection Admin Yael
udb_check = pd.read_csv(USERS_FILE)
if "Yael" not in udb_check["pseudo"].values:
    yael_row = pd.DataFrame([["Yael", "Yassine05", "Admin", "admin@test.com"]], columns=["pseudo", "password", "role", "user_email"])
    pd.concat([udb_check, yael_row], ignore_index=True).to_csv(USERS_FILE, index=False)

def charger_data():
    suf = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
    f = os.path.join(dossier, f"sauvegarde_{suf}.csv")
    if not os.path.exists(f) or os.stat(f).st_size == 0:
        df = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df.index.name = "Nom"
        df.to_csv(f)
        return df
    return pd.read_csv(f, index_col=0)

# --- 4. TRADUCTIONS & STYLE ---
TRAD = {
    "Français": {"titre_norm": "📖 Bilan Coran", "titre_ram": "🌙 Bilan Ramadan", "etat": "📊 État actuel", "prog": "📊 Progrès", "maj": "📝 Maj", "calc": "🔄 Calcul", "plan": "📅 Plan", "params": "⚙️ Paramètres", "admin": "🔔 Notifs", "logout": "🔒 Quitter", "hadith_btn": "✨ HADITH", "wa": "💬 WhatsApp"},
    "العربية": {"titre_norm": "📖 حصيلة القرآن", "titre_ram": "🌙 حصيلة رمضان", "etat": "📊 الحالة", "prog": "📊 التقدم", "maj": "📝 تحديث", "calc": "🔄 حساب", "plan": "📅 جدول", "params": "⚙️ الإعدادات", "admin": "🔔 تنبيهات", "logout": "🔒 خروج", "hadith_btn": "✨ حديث", "wa": "💬 واتساب"}
}
L = TRAD[st.session_state["langue"]]
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"

st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"<style>h1,h2,h3,p,label,span {{color:{COLOR}!important; text-align:center;}} div.stButton>button {{width:100%; border-radius:10px; border:2px solid {COLOR}; color:{COLOR}; font-weight:bold;}}</style>", unsafe_allow_html=True)

# --- 5. ACCÈS & INSCRIPTION ---
if not st.session_state["auth"]:
    st.title("🔐 Accès")
    if st.session_state["view"] == "login":
        u = st.text_input("Pseudo")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            db = pd.read_csv(USERS_FILE)
            match = db[(db["pseudo"] == u) & (db["password"] == p)]
            if not match.empty:
                st.session_state["auth"], st.session_state["user_connected"] = True, u
                st.session_state["is_admin"] = (match.iloc[0]["role"] == "Admin")
                st.rerun()
            else: st.error("Erreur d'identifiants")
        if st.button("S'inscrire"): st.session_state["view"] = "signup"; st.rerun()

    elif st.session_state["view"] == "signup":
        nu = st.text_input("Pseudo choisi")
        ne = st.text_input("Email (obligatoire pour confirmation)")
        np = st.text_input("Mot de passe choisi", type="password")
        if st.button("Envoyer ma demande"):
            if nu and ne and np:
                ddb = pd.read_csv(DEMANDES_FILE)
                pd.concat([ddb, pd.DataFrame([[nu, np, ne]], columns=["pseudo", "password", "user_email"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
                envoyer_alerte_yael(nu, "Nouvelle Inscription")
                st.success("Demande envoyée !"); st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 6. NAVIGATION ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_connected']}")
    if st.button("🏠 Accueil"): st.session_state["page"] = "home"; st.rerun()
    if st.session_state["is_admin"]:
        nb = len(pd.read_csv(DEMANDES_FILE)) + len(pd.read_csv(FORGOT_FILE))
        if st.button(f"🔔 Notifs ({nb})"): st.session_state["page"] = "admin"; st.rerun()
    if st.button(L["logout"]): st.session_state["auth"] = False; st.rerun()

# --- 7. PAGE ADMIN (VALIDATION) ---
if st.session_state["page"] == "admin":
    st.title("🔔 Validation")
    ddb = pd.read_csv(DEMANDES_FILE)
    for i, r in ddb.iterrows():
        st.info(f"Demande de : **{r['pseudo']}** ({r['user_email']})")
        if st.button(f"✅ Valider {r['pseudo']}", key=f"v_{i}"):
            # Ajouter aux utilisateurs
            udb = pd.read_csv(USERS_FILE)
            pd.concat([udb, pd.DataFrame([[r['pseudo'], r['password'], "Membre", r['user_email']]], columns=["pseudo", "password", "role", "user_email"])], ignore_index=True).to_csv(USERS_FILE, index=False)
            
            # Init données Coran
            for m in ["lecture", "ramadan"]:
                path = os.path.join(dossier, f"sauvegarde_{m}.csv")
                tmp = pd.read_csv(path, index_col=0) if os.path.exists(path) else pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"], index=["Nom"])
                tmp.loc[r['pseudo']] = [1, 10, 0, 1]
                tmp.to_csv(path)
            
            # ENVOI DU MAIL AUTOMATIQUE
            envoyer_confirmation_utilisateur(r['pseudo'], r['user_email'])
            
            # Nettoyer
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False)
            st.success("Utilisateur validé et mail envoyé !"); st.rerun()
    st.stop()

# --- 8. PAGE ACCUEIL ---
st.title(L["titre_norm"])
df_view = charger_data()
if not df_view.empty:
    if not st.session_state["is_admin"]:
        df_view = df_view[df_view.index == st.session_state["user_connected"]]
    st.table(df_view)
