import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import random
from datetime import date, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Bilan Coran Pro", layout="wide", page_icon="🌙")

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
    # Création du fichier avec le compte Admin Yael par défaut
    df_init = pd.DataFrame([["yael@admin.com", "Yael", "Yassine05", "Validé", 1, 10]], 
                           columns=["email", "pseudo", "password", "statut", "page", "rythme"])
    df_init.to_csv(USERS_FILE, index=False)

def charger(): return pd.read_csv(USERS_FILE)
def sauver(df): df.to_csv(USERS_FILE, index=False)

# --- SESSION STATE ---
if "user_pseudo" not in st.session_state: st.session_state["user_pseudo"] = None

# --- AUTHENTIFICATION (PSEUDO / MDP) ---
if st.session_state["user_pseudo"] is None:
    st.title("🌙 Accès Bilan Coran")
    tab1, tab2, tab3 = st.tabs(["Connexion", "Inscription", "Mdp oublié"])
    df = charger()

    with tab1: # CONNEXION PAR PSEUDO
        ps = st.text_input("Pseudo", key="l_ps")
        pw = st.text_input("Mot de passe", type="password", key="l_pw")
        if st.button("Se connecter"):
            user = df[(df['pseudo'] == ps) & (df['password'].astype(str) == pw)]
            if not user.empty:
                if user.iloc[0]['statut'] == "Validé":
                    st.session_state["user_pseudo"] = ps
                    st.rerun()
                else:
                    st.warning("⏳ Ton compte est en attente de validation par Yael.")
            else: st.error("Pseudo ou mot de passe incorrect.")

    with tab2: # INSCRIPTION (AVEC EMAIL POUR LE CONTACT)
        st.subheader("Créer un compte")
        ne = st.text_input("Ton Email (pour recevoir la confirmation)", key="r_e")
        np = st.text_input("Choisis un Pseudo", key="r_p")
        nm = st.text_input("Choisis un Mot de passe", type="password", key="r_m")
        if st.button("S'inscrire"):
            if ne and np and nm:
                if np in df['pseudo'].values: st.error("Ce pseudo est déjà pris.")
                elif ne in df['email'].values: st.error("Cet email est déjà utilisé.")
                else:
                    new_row = pd.DataFrame([[ne, np, nm, "En attente", 1, 10]], columns=["email", "pseudo", "password", "statut", "page", "rythme"])
                    sauver(pd.concat([df, new_row]))
                    st.success("Demande envoyée ! Yael va valider ton compte et tu recevras un mail.")
            else: st.warning("Remplis tous les champs.")

    with tab3: # RÉCUPÉRATION PAR EMAIL
        st.subheader("Récupérer mes accès")
        fe = st.text_input("Email utilisé lors de l'inscription")
        if st.button("Envoyer mes identifiants"):
            user = df[df['email'] == fe]
            if not user.empty:
                corps = f"Salam,\n\nVoici tes accès :\nPseudo : {user.iloc[0]['pseudo']}\nMot de passe : {user.iloc[0]['password']}"
                if envoyer_email(fe, "Identifiants Coran", corps):
                    st.success("Email envoyé avec ton pseudo et mot de passe !")
            else: st.error("Email inconnu.")
    st.stop()

# --- ESPACE CONNECTÉ ---
df = charger()
user_idx = df[df['pseudo'] == st.session_state["user_pseudo"]].index[0]
user_data = df.loc[user_idx]

# --- SIDEBAR & ADMIN ---
with st.sidebar:
    st.header(f"👤 {user_data['pseudo']}")
    
    # ACCÈS ADMIN POUR YAEL
    if st.session_state["user_pseudo"] == "Yael":
        st.divider()
        st.subheader("🛠️ Panel Admin")
        attente = df[df['statut'] == "En attente"]
        for i, r in attente.iterrows():
            st.write(f"Valider **{r['pseudo']}** ?")
            if st.button(f"Confirmer {r['pseudo']}", key=f"v_{i}"):
                df.at[i, 'statut'] = "Validé"
                sauver(df)
                envoyer_email(r['email'], "Compte Validé !", f"Salam {r['pseudo']},\n\nYael a validé ton compte ! Tu peux te connecter avec ton pseudo.")
                st.rerun()

    st.divider()
    if st.button("🔒 Déconnexion"):
        st.session_state["user_pseudo"] = None
        st.rerun()

# --- CONTENU ---
st.title(f"📖 Bilan de {user_data['pseudo']}")

# Mise à jour progression
with st.expander("📝 Mettre à jour ma progression"):
    c1, c2 = st.columns(2)
    new_p = c1.number_input("Page actuelle", 1, 604, int(user_data['page']))
    new_r = c2.number_input("Pages par jour", 1, 100, int(user_data['rythme']))
    if st.button("💾 Sauvegarder"):
        df.at[user_idx, 'page'] = new_p
        df.at[user_idx, 'rythme'] = new_r
        sauver(df)
        st.success("Données synchronisées !")
        st.rerun()

# Planning 30 jours
st.subheader("📅 Mon Planning (30 jours)")
auj = date.today()
jours = [(auj + timedelta(days=i)).strftime("%d/%m") for i in range(30)]
pages = [(int(user_data['page']) + (int(user_data['rythme']) * i)) % 604 or 1 for i in range(30)]
st.dataframe(pd.DataFrame({"Date": jours, "Page attendue": pages}), use_container_width=True)
