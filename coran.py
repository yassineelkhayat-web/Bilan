import streamlit as st
import pandas as pd
from datetime import date
import os
import random
import requests

# --- 1. CONFIGURATION API & CONSTANTES ---
EMAILJS_SERVICE_ID = "service_v9ebnic" 
EMAILJS_TEMPLATE_ID = "template_rghkouc"
EMAILJS_PUBLIC_KEY = "LUCKx4YnQSQ3ncrue"
EMAILJS_PRIVATE_KEY = "xnNMOnkv8TSM6N_fK9TCR"

def envoyer_mail_code(pseudo, email_dest, code):
    url = "https://api.emailjs.com/api/v1.0/email/send"
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "accessToken": EMAILJS_PRIVATE_KEY,
        "template_params": {
            "to_name": pseudo,
            "user_email": email_dest,
            "message": code  # Le code envoyé à EmailJS
        }
    }
    try:
        r = requests.post(url, json=payload)
        return r.status_code == 200
    except:
        return False

# --- 2. GESTION DES FICHIERS CSV ---
dossier = os.path.dirname(__file__)
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv")
CORAN_FILE = os.path.join(dossier, "suivi_coran.csv")
CODES_FILE = os.path.join(dossier, "combinaisons.txt")

def init_file(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["pseudo", "password", "role", "user_email"])
init_file(DEMANDES_FILE, ["pseudo", "password", "user_email"])
init_file(CORAN_FILE, ["date", "pseudo", "sourate", "verset_debut", "verset_fin", "type"])

if not os.path.exists(CODES_FILE):
    with open(CODES_FILE, "w") as f:
        for _ in range(500): f.write(str(random.randint(100000, 999999)) + "\n")

# Création automatique de l'admin Yael si absent
db_u = pd.read_csv(USERS_FILE)
if "Yael" not in db_u["pseudo"].values:
    new_admin = pd.DataFrame([["Yael", "Yassine05", "Admin", "yassine.elkhayat@isv.be"]], 
                             columns=["pseudo", "password", "role", "user_email"])
    pd.concat([db_u, new_admin], ignore_index=True).to_csv(USERS_FILE, index=False)

# --- 3. SESSION STATE ---
if "auth" not in st.session_state:
    st.session_state.update({
        "auth": False, "user": None, "role": "Membre", "view": "login",
        "reset_step": 1, "temp_code": "", "temp_email": ""
    })

# --- 4. INTERFACE CONNEXION / INSCRIPTION / MDP OUBLIÉ ---
if not st.session_state["auth"]:
    st.title("📖 Suivi Coran - Connexion")
    
    if st.session_state["view"] == "login":
        u = st.text_input("Pseudo")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            db = pd.read_csv(USERS_FILE)
            user_match = db[(db["pseudo"] == u) & (db["password"] == p)]
            if not user_match.empty:
                st.session_state.update({"auth": True, "user": u, "role": user_match.iloc[0]["role"]})
                st.rerun()
            else: st.error("Pseudo ou mot de passe incorrect.")
        
        st.divider()
        c1, c2 = st.columns(2)
        if c1.button("S'inscrire"): st.session_state["view"] = "signup"; st.rerun()
        if c2.button("Mot de passe oublié ?"): st.session_state["view"] = "forgot"; st.rerun()

    elif st.session_state["view"] == "signup":
        st.subheader("Demande d'inscription")
        nu = st.text_input("Choisis un Pseudo")
        ne = st.text_input("Ton Email")
        np = st.text_input("Mot de passe", type="password")
        if st.button("Envoyer la demande"):
            if nu and ne and np:
                ddb = pd.read_csv(DEMANDES_FILE)
                new_req = pd.DataFrame([[nu, np, ne]], columns=["pseudo", "password", "user_email"])
                pd.concat([ddb, new_req], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
                st.success("Demande envoyée à Yael !")
                st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()

    elif st.session_state["view"] == "forgot":
        st.subheader("Réinitialisation du mot de passe")
        if st.session_state["reset_step"] == 1:
            fe = st.text_input("Email du compte")
            if st.button("Recevoir mon code par mail"):
                db = pd.read_csv(USERS_FILE)
                if fe in db["user_email"].values:
                    with open(CODES_FILE, "r") as f: codes = f.read().splitlines()
                    code = random.choice(codes)
                    pseudo = db[db["user_email"] == fe]["pseudo"].values[0]
                    if envoyer_mail_code(pseudo, fe, code):
                        st.session_state.update({"temp_code": code, "temp_email": fe, "reset_step": 2})
                        st.rerun()
                    else: st.error("Erreur EmailJS.")
                else: st.error("Email inconnu.")
        
        elif st.session_state["reset_step"] == 2:
            verif = st.text_input("Entre le code à 6 chiffres reçu")
            if st.button("Vérifier le code"):
                if verif == st.session_state["temp_code"]:
                    st.session_state["reset_step"] = 3; st.rerun()
                else: st.error("Code incorrect.")

        elif st.session_state["reset_step"] == 3:
            new_pass = st.text_input("Nouveau mot de passe", type="password")
            if st.button("Enregistrer"):
                db = pd.read_csv(USERS_FILE)
                db.loc[db["user_email"] == st.session_state["temp_email"], "password"] = new_pass
                db.to_csv(USERS_FILE, index=False)
                st.success("Mot de passe mis à jour !"); st.session_state.update({"view": "login", "reset_step": 1}); st.rerun()
        
        if st.button("Retour"): st.session_state.update({"view": "login", "reset_step": 1}); st.rerun()
    st.stop()

# --- 5. ESPACE CONNECTÉ ---
st.sidebar.title(f"Salam, {st.session_state['user']}")
menu = ["Mon Suivi", "Ajouter un bilan"]
if st.session_state["role"] == "Admin": menu.append("Panel Admin")
choice = st.sidebar.radio("Menu", menu)

# --- PANEL ADMIN (Validation des comptes) ---
if choice == "Panel Admin":
    st.header("🛠️ Validation des nouveaux comptes")
    ddb = pd.read_csv(DEMANDES_FILE)
    if ddb.empty: st.info("Aucune demande en attente.")
    else:
        for i, row in ddb.iterrows():
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{row['pseudo']}** ({row['user_email']})")
            if col2.button("Valider", key=f"v_{i}"):
                udb = pd.read_csv(USERS_FILE)
                valid_user = pd.DataFrame([[row['pseudo'], row['password'], "Membre", row['user_email']]], 
                                          columns=["pseudo", "password", "role", "user_email"])
                pd.concat([udb, valid_user], ignore_index=True).to_csv(USERS_FILE, index=False)
                ddb.drop(i).to_csv(DEMANDES_FILE, index=False)
                st.rerun()

# --- MON SUIVI ---
elif choice == "Mon Suivi":
    st.header("📊 Mon historique de lecture")
    df = pd.read_csv(CORAN_FILE)
    my_df = df[df["pseudo"] == st.session_state["user"]]
    if my_df.empty: st.write("Aucune donnée enregistrée.")
    else: st.table(my_df.sort_values(by="date", ascending=False))

# --- AJOUTER UN BILAN ---
elif choice == "Ajouter un bilan":
    st.header("✍️ Enregistrer ma lecture")
    with st.form("bilan_form"):
        sourate = st.text_input("Nom de la Sourate")
        v_deb = st.number_input("Verset début", min_value=1, step=1)
        v_fin = st.number_input("Verset fin", min_value=1, step=1)
        t_lecture = st.selectbox("Type", ["Lecture", "Apprentissage", "Révision"])
        submit = st.form_submit_button("Sauvegarder")
        
        if submit:
            new_data = pd.DataFrame([[date.today(), st.session_state["user"], sourate, v_deb, v_fin, t_lecture]], 
                                    columns=["date", "pseudo", "sourate", "verset_debut", "verset_fin", "type"])
            df_c = pd.read_csv(CORAN_FILE)
            pd.concat([df_c, new_data], ignore_index=True).to_csv(CORAN_FILE, index=False)
            st.success("Bilan enregistré !")

if st.sidebar.button("Déconnexion"):
    st.session_state["auth"] = False
    st.rerun()
