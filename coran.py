import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import date, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Bilan Coran", layout="wide")

def envoyer_email(destinataire, sujet, corps):
    try:
        expediteur = st.secrets["gmail"]["sender_email"]
        password = st.secrets["gmail"]["password"]
        msg = MIMEMultipart()
        msg['From'] = expediteur
        msg['To'] = destinataire
        msg['Subject'] = sujet
        msg.attach(MIMEText(corps, 'plain'))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(expediteur, password)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# --- BASE DE DONNÉES ---
USERS_FILE = "users_db.csv"
if not os.path.exists(USERS_FILE):
    pd.DataFrame(columns=["email", "pseudo", "password", "statut", "page", "rythme"]).to_csv(USERS_FILE, index=False)

def charger(): return pd.read_csv(USERS_FILE)
def sauver(df): df.to_csv(USERS_FILE, index=False)

# --- AUTHENTIFICATION ---
if "user_email" not in st.session_state: st.session_state["user_email"] = None

if st.session_state["user_email"] is None:
    st.title("🌙 Application Coran")
    menu = ["Connexion", "Inscription", "Mot de passe oublié"]
    choix = st.tabs(menu)
    df = charger()

    with choix[0]: # CONNEXION
        e = st.text_input("Email")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            user = df[(df['email'] == e) & (df['password'].astype(str) == p)]
            if not user.empty:
                if user.iloc[0]['statut'] == "Validé":
                    st.session_state["user_email"] = e
                    st.rerun()
                else:
                    st.warning("Ton compte est en attente de confirmation par Yael.")
            else: st.error("Identifiants incorrects.")

    with choix[1]: # INSCRIPTION
        ne = st.text_input("Ton Email", key="reg_e")
        np = st.text_input("Ton Pseudo", key="reg_p")
        nm = st.text_input("Choisir un mot de passe", type="password", key="reg_m")
        if st.button("Envoyer ma demande"):
            if ne in df['email'].values: st.error("Email déjà utilisé.")
            else:
                new_row = pd.DataFrame([[ne, np, nm, "En attente", 1, 10]], columns=["email", "pseudo", "password", "statut", "page", "rythme"])
                sauver(pd.concat([df, new_row]))
                st.success("Demande envoyée ! Yael va confirmer ton inscription.")

    with choix[2]: # MOT DE PASSE OUBLIÉ
        fe = st.text_input("Email de récupération")
        if st.button("Recevoir mon mot de passe"):
            user = df[df['email'] == fe]
            if not user.empty:
                envoyer_email(fe, "Récupération Coran", f"Salam, ton mot de passe est : {user.iloc[0]['password']}")
                st.success("Email envoyé !")
    st.stop()

# --- ESPACE CONNECTÉ ---
df = charger()
user_data = df[df['email'] == st.session_state["user_email"]].iloc[0]

# PANEL ADMIN POUR TOI (YAEL)
if st.session_state["user_email"] == st.secrets["gmail"]["sender_email"]:
    with st.sidebar:
        st.subheader("🛠️ Panel Admin (Yael)")
        attente = df[df['statut'] == "En attente"]
        for i, r in attente.iterrows():
            st.write(f"Inscrire {r['pseudo']} ?")
            if st.button(f"Confirmer {r['pseudo']}", key=f"conf_{i}"):
                df.at[i, 'statut'] = "Validé"
                sauver(df)
                envoyer_email(r['email'], "Inscription Confirmée !", f"Salam {r['pseudo']}, Yael a validé ton compte ! Tu peux maintenant te connecter.")
                st.rerun()

# --- RESTE DE L'APP (PLANNING, ETC) ---
st.title(f"📖 Bilan de {user_data['pseudo']}")
# (Ajoute ici ton code de planning et progression...)
if st.button("Déconnexion"):
    st.session_state["user_email"] = None
    st.rerun()
