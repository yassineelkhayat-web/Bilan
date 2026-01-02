import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random
import requests

# --- CONFIGURATION API ---
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
            "message": texte_alerte  # C'est cette variable qui doit être dans ton template EmailJS
        }
    }
    try:
        r = requests.post(url, json=payload)
        return r.status_code == 200
    except:
        return False

# --- GESTION DES FICHIERS ---
dossier = os.path.dirname(__file__)
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv")
CODES_FILE = os.path.join(dossier, "combinaisons.txt")

def init_file(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["pseudo", "password", "role", "user_email"])
init_file(DEMANDES_FILE, ["pseudo", "password", "user_email"])

# Génération des codes si besoin
if not os.path.exists(CODES_FILE):
    with open(CODES_FILE, "w") as f:
        for _ in range(1000):
            f.write(str(random.randint(100000, 999999)) + "\n")

# Sécurité Admin Yael
udb_check = pd.read_csv(USERS_FILE)
if "Yael" not in udb_check["pseudo"].values:
    yael_row = pd.DataFrame([["Yael", "Yassine05", "Admin", "yassine.elkhayat@isv.be"]], columns=["pseudo", "password", "role", "user_email"])
    pd.concat([udb_check, yael_row], ignore_index=True).to_csv(USERS_FILE, index=False)

# --- SESSION STATE ---
if "auth" not in st.session_state:
    st.session_state.update({"auth": False, "user_connected": None, "is_admin": False, "ramadan_mode": False, "view": "login", "reset_step": 1, "temp_code": "", "temp_email": ""})

# --- AUTHENTIFICATION ---
if not st.session_state["auth"]:
    st.title("🔐 Accès")
    
    if st.session_state["view"] == "login":
        u = st.text_input("Pseudo")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            db = pd.read_csv(USERS_FILE)
            match = db[(db["pseudo"].astype(str) == str(u)) & (db["password"].astype(str) == str(p))]
            if not match.empty:
                st.session_state.update({"auth": True, "user_connected": str(u), "is_admin": (match.iloc[0]["role"] == "Admin")})
                st.rerun()
            else: st.error("Erreur.")
        if st.button("Mot de passe oublié ?"):
            st.session_state.update({"view": "forgot", "reset_step": 1})
            st.rerun()

    elif st.session_state["view"] == "forgot":
        if st.session_state["reset_step"] == 1:
            fe = st.text_input("Email d'inscription")
            if st.button("Envoyer le code"):
                db = pd.read_csv(USERS_FILE)
                if fe in db["user_email"].values:
                    with open(CODES_FILE, "r") as f: codes = f.read().splitlines()
                    code = random.choice(codes)
                    st.session_state.update({"temp_code": code, "temp_email": fe})
                    success = envoyer_mail(db[db["user_email"]==fe]["pseudo"].values[0], fe, f"CODE DE SÉCURITÉ : {code}")
                    if success:
                        st.session_state["reset_step"] = 2
                        st.rerun()
                    else: st.error("Erreur d'envoi.")
                else: st.error("Email inconnu.")

        elif st.session_state["reset_step"] == 2:
            st.write(f"Code envoyé à {st.session_state['temp_email']}")
            cs = st.text_input("Code à 6 chiffres")
            if st.button("Vérifier"):
                if cs == st.session_state["temp_code"]:
                    st.session_state["reset_step"] = 3
                    st.rerun()
                else: st.error("Code faux.")

        elif st.session_state["reset_step"] == 3:
            new_p = st.text_input("Nouveau MDP", type="password")
            if st.button("Changer"):
                db = pd.read_csv(USERS_FILE)
                db.loc[db["user_email"] == st.session_state["temp_email"], "password"] = new_p
                db.to_csv(USERS_FILE, index=False)
                st.success("Réussi ! Connecte-toi.")
                st.session_state["view"] = "login"; st.rerun()
        if st.button("Annuler"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- RESTE DU CODE (ACCUEIL) ---
st.write(f"Bienvenue {st.session_state['user_connected']}")
if st.button("Déconnexion"):
    st.session_state["auth"] = False
    st.rerun()
