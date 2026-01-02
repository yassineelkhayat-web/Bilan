import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random
import requests

# --- 1. CONFIGURATION API ---
URL_FORMSPREE = "https://formspree.io/f/xaqnjwgv"
EMAILJS_SERVICE_ID = "service_v9ebnic" 
EMAILJS_TEMPLATE_ID = "template_rghkouc"
EMAILJS_PUBLIC_KEY = "LUCKx4YnQSQ3ncrue"
EMAILJS_PRIVATE_KEY = "xnNMOnkv8TSM6N_fK9TCR"

def envoyer_mail(pseudo, email_dest, texte_alerte):
    url = "https://api.emailjs.com/api/v1.0/email/send"
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "accessToken": EMAILJS_PRIVATE_KEY,
        "template_params": {
            "to_name": pseudo,
            "user_email": email_dest,
            "message": texte_alerte
        }
    }
    try: requests.post(url, json=payload)
    except: pass

# --- 2. GESTION DES FICHIERS ---
dossier = os.path.dirname(__file__)
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv")
CODES_FILE = os.path.join(dossier, "combinaisons.txt")

def init_file(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["pseudo", "password", "role", "user_email"])
init_file(DEMANDES_FILE, ["pseudo", "password", "user_email"])

if not os.path.exists(CODES_FILE):
    with open(CODES_FILE, "w") as f:
        for _ in range(1000): f.write(str(random.randint(100000, 999999)) + "\n")

# Sécurité Admin Yael
udb_check = pd.read_csv(USERS_FILE)
if "Yael" not in udb_check["pseudo"].values:
    yael_row = pd.DataFrame([["Yael", "Yassine05", "Admin", "yassine.elkhayat@isv.be"]], columns=["pseudo", "password", "role", "user_email"])
    pd.concat([udb_check, yael_row], ignore_index=True).to_csv(USERS_FILE, index=False)

# --- 3. SESSION STATE ---
if "auth" not in st.session_state:
    st.session_state.update({
        "auth": False, "user_connected": None, "is_admin": False, 
        "ramadan_mode": False, "view": "login", "reset_step": 1, 
        "temp_code": "", "temp_email": "", "page": "home"
    })

def charger_data():
    suf = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
    f = os.path.join(dossier, f"sauvegarde_{suf}.csv")
    if not os.path.exists(f) or os.stat(f).st_size == 0:
        return pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
    return pd.read_csv(f, index_col=0)

# --- 4. AUTHENTIFICATION ---
if not st.session_state["auth"]:
    st.title("🔐 Accès Bilan Coran")
    
    # VUE CONNEXION
    if st.session_state["view"] == "login":
        u = st.text_input("Pseudo")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            db = pd.read_csv(USERS_FILE)
            match = db[(db["pseudo"].astype(str) == str(u)) & (db["password"].astype(str) == str(p))]
            if not match.empty:
                st.session_state.update({"auth": True, "user_connected": str(u), "is_admin": (match.iloc[0]["role"] == "Admin")})
                st.rerun()
            else: st.error("Identifiants incorrects.")
        
        col1, col2 = st.columns(2)
        if col1.button("S'inscrire"):
            st.session_state["view"] = "signup"
            st.rerun()
        if col2.button("Mot de passe oublié ?"):
            st.session_state.update({"view": "forgot", "reset_step": 1})
            st.rerun()

    # VUE INSCRIPTION
    elif st.session_state["view"] == "signup":
        st.subheader("📝 Demande d'inscription")
        nu = st.text_input("Choisis un Pseudo")
        ne = st.text_input("Ton Email")
        np = st.text_input("Choisis un Mot de passe", type="password")
        if st.button("Envoyer ma demande"):
            if nu and ne and np:
                ddb = pd.read_csv(DEMANDES_FILE)
                pd.concat([ddb, pd.DataFrame([[nu, np, ne]], columns=["pseudo", "password", "user_email"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
                requests.post(URL_FORMSPREE, data={"Objet": "Nouvelle Inscription", "User": nu, "Email": ne})
                st.success("Demande envoyée ! Yael doit maintenant te valider.")
                st.session_state["view"] = "login"
                st.rerun()
            else: st.warning("Remplis tous les champs.")
        if st.button("Retour"):
            st.session_state["view"] = "login"
            st.rerun()

    # VUE MOT DE PASSE OUBLIÉ
    elif st.session_state["view"] == "forgot":
        if st.session_state["reset_step"] == 1:
            fe = st.text_input("Email d'inscription")
            if st.button("Recevoir mon code"):
                db = pd.read_csv(USERS_FILE)
                if fe in db["user_email"].values:
                    with open(CODES_FILE, "r") as f: codes = f.read().splitlines()
                    code = random.choice(codes)
                    st.session_state.update({"temp_code": code, "temp_email": fe})
                    envoyer_mail(db[db["user_email"]==fe]["pseudo"].values[0], fe, f"Voici ton code de sécurité : {code}")
                    st.session_state["reset_step"] = 2
                    st.rerun()
                else: st.error("Email inconnu.")
        elif st.session_state["reset_step"] == 2:
            cs = st.text_input("Entre le code reçu par mail")
            if st.button("Vérifier"):
                if cs == st.session_state["temp_code"]: st.session_state["reset_step"] = 3; st.rerun()
                else: st.error("Code incorrect.")
        elif st.session_state["reset_step"] == 3:
            new_p = st.text_input("Nouveau mot de passe", type="password")
            if st.button("Changer le mot de passe"):
                db = pd.read_csv(USERS_FILE)
                db.loc[db["user_email"] == st.session_state["temp_email"], "password"] = new_p
                db.to_csv(USERS_FILE, index=False)
                st.success("Modifié ! Connecte-toi.")
                st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 5. APPLICATION (APRÈS CONNEXION) ---
df_complet = charger_data()
auj = date.today()

with st.sidebar:
    st.title(f"👤 {st.session_state['user_connected']}")
    if st.button("🏠 Accueil"): st.session_state["page"] = "home"; st.rerun()
    if st.session_state["is_admin"] and st.button("🛠️ Admin"): st.session_state["page"] = "admin"; st.rerun()
    st.divider()
    if st.button("🔒 Déconnexion"):
        st.session_state["auth"] = False
        st.rerun()

# PAGE ADMIN
if st.session_state["page"] == "admin":
    st.title("🛠️ Gestion des membres")
    ddb = pd.read_csv(DEMANDES_FILE)
    st.subheader(f"Demandes en attente ({len(ddb)})")
    for i, r in ddb.iterrows():
        c1, c2 = st.columns([3, 1])
        c1.write(f"**{r['pseudo']}** ({r['user_email']})")
        if c2.button("✅ Valider", key=f"val_{i}"):
            udb = pd.read_csv(USERS_FILE)
            pd.concat([udb, pd.DataFrame([[r['pseudo'], r['password'], "Membre", r['user_email']]], columns=["pseudo", "password", "role", "user_email"])], ignore_index=True).to_csv(USERS_FILE, index=False)
            # Créer ses données coran
            for m in ["lecture", "ramadan"]:
                path = os.path.join(dossier, f"sauvegarde_{m}.csv")
                tmp = pd.read_csv(path, index_col=0) if os.path.exists(path) else pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"], index=["Nom"])
                tmp.loc[r['pseudo']] = [1, 10, 0, 1]
                tmp.to_csv(path)
            envoyer_mail(r['pseudo'], r['user_email'], "Ton compte a été validé ! Connecte-toi.")
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False)
            st.rerun()
    st.stop()

# PAGE ACCUEIL
st.title("📖 Mon Bilan Coran")
st.write(f"Salam {st.session_state['user_connected']} !")
# (Ici tu peux rajouter ton tableau de suivi et tes graphiques)
