import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random
import requests # Vérifie bien que cette ligne est présente !

# --- CONFIGURATION NOTIFICATIONS ---
URL_FORMSPREE = "https://formspree.io/f/xrebqybk"
EMAILJS_SERVICE_ID = "service_v9ebnic" 
EMAILJS_TEMPLATE_ID = "template_rghkouc"
EMAILJS_PUBLIC_KEY = "LUCKx4YnQSQ3ncrue"

def envoyer_alerte_yael(pseudo, type_alerte="Inscription"):
    donnees = {"Objet": f"🔔 Bilan Coran : {type_alerte}", "Utilisateur": pseudo}
    try: requests.post(URL_FORMSPREE, data=donnees)
    except: pass

def envoyer_confirmation_utilisateur(pseudo, email_dest):
    url = "https://api.emailjs.com/api/v1.0/email/send"
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "template_params": {
            "to_name": pseudo,
            "user_email": email_dest, # Correspond à {{user_email}} sur ton site
            "message": "Ton compte Bilan Coran a été validé !"
        }
    }
    # On capture la réponse pour savoir ce qui se passe
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.toast(f"✅ Mail envoyé à {pseudo} !", icon="📧")
        else:
            st.error(f"❌ Erreur EmailJS : {response.text}")
    except Exception as e:
        st.error(f"❌ Erreur de connexion : {e}")

# --- 1. CONFIGURATION ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if "user_connected" not in st.session_state: st.session_state["user_connected"] = None
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "ramadan_mode" not in st.session_state: st.session_state["ramadan_mode"] = False
if "langue" not in st.session_state: st.session_state["langue"] = "Français"
if "page" not in st.session_state: st.session_state["page"] = "home"
if "view" not in st.session_state: st.session_state["view"] = "login"

# --- 2. GESTION DES FICHIERS ---
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
    "Français": {"titre_norm": "📖 Bilan Coran", "titre_ram": "🌙 Bilan Ramadan", "etat": "📊 État actuel", "prog": "📊 Progrès", "maj": "📝 Maj", "calc": "🔄 Calcul", "plan": "📅 Plan", "params": "⚙️ Paramètres", "admin": "🔔 Notifs", "logout": "🔒 Quitter", "hadith_btn": "✨ HADITH", "wa": "💬 WhatsApp"},
    "العربية": {"titre_norm": "📖 حصيلة القرآن", "titre_ram": "🌙 حصيلة رمضان", "etat": "📊 الحالة", "prog": "📊 التقدم", "maj": "📝 تحديث", "calc": "🔄 حساب", "plan": "📅 جدول", "params": "⚙️ الإعدادات", "admin": "🔔 تنبيهات", "logout": "🔒 خروج", "hadith_btn": "✨ حديث", "wa": "💬 واتساب"}
}
L = TRAD[st.session_state["langue"]]
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"

st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"<style>h1,h2,h3,p,label,span {{color:{COLOR}!important; text-align:center;}} div.stButton>button {{width:100%; border-radius:10px; border:2px solid {COLOR}; color:{COLOR}; font-weight:bold;}}</style>", unsafe_allow_html=True)

# --- 4. AUTHENTIFICATION ---
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
        ne = st.text_input("Email (obligatoire)")
        np = st.text_input("Nouveau Mdp", type="password")
        if st.button("Envoyer ma demande"):
            if nu and ne and np:
                ddb = pd.read_csv(DEMANDES_FILE)
                pd.concat([ddb, pd.DataFrame([[nu, np, ne]], columns=["pseudo", "password", "user_email"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
                envoyer_alerte_yael(nu, "Nouvelle Inscription")
                st.success("Demande envoyée !"); st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 5. LOGIQUE ADMIN ---
if st.session_state["page"] == "admin":
    st.title("🔔 Validation")
    ddb = pd.read_csv(DEMANDES_FILE)
    for i, r in ddb.iterrows():
        st.info(f"Inscrire **{r['pseudo']}** ? (Email: {r['user_email']})")
        if st.button(f"✅ Valider {r['pseudo']}", key=f"v_{i}"):
            udb = pd.read_csv(USERS_FILE)
            pd.concat([udb, pd.DataFrame([[r['pseudo'], r['password'], "Membre", r['user_email']]], columns=["pseudo", "password", "role", "user_email"])], ignore_index=True).to_csv(USERS_FILE, index=False)
            
            # Init Coran
            for m in ["lecture", "ramadan"]:
                f = os.path.join(dossier, f"sauvegarde_{m}.csv")
                temp = pd.read_csv(f, index_col=0) if os.path.exists(f) else pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"], index=["Nom"])
                temp.loc[r['pseudo']] = [1, 10, 0, 1]
                temp.to_csv(f)
            
            # --- C'EST ICI QUE LE MAIL S'ENVOIE ---
            envoyer_confirmation_utilisateur(r['pseudo'], r['user_email'])
            
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False)
            st.rerun()
    st.stop()

# (Le reste du code accueil/planning reste identique...)
