import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import date, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Bilan Coran", layout="wide")

# Fonction d'envoi d'email via ton Gmail
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
    except Exception as e:
        st.error(f"Erreur d'envoi d'email : {e}")
        return False

# --- BASE DE DONNÉES UTILISATEURS ---
USERS_FILE = "users_db.csv"
if not os.path.exists(USERS_FILE):
    pd.DataFrame(columns=["email", "pseudo", "password", "statut", "page", "rythme"]).to_csv(USERS_FILE, index=False)

def charger(): return pd.read_csv(USERS_FILE)
def sauver(df): df.to_csv(USERS_FILE, index=False)

# --- GESTION DE LA CONNEXION ---
if "user_email" not in st.session_state: st.session_state["user_email"] = None

if st.session_state["user_email"] is None:
    st.title("🌙 Application Bilan Coran")
    tab1, tab2, tab3 = st.tabs(["Connexion", "Inscription", "Mot de passe oublié"])
    df = charger()

    with tab1: # CONNEXION
        e = st.text_input("Email", key="login_e")
        p = st.text_input("Mot de passe", type="password", key="login_p")
        if st.button("Se connecter"):
            user = df[(df['email'] == e) & (df['password'].astype(str) == p)]
            if not user.empty:
                if user.iloc[0]['statut'] == "Validé":
                    st.session_state["user_email"] = e
                    st.rerun()
                else:
                    st.warning("Ton compte est en attente de validation par Yael.")
            else: st.error("Email ou mot de passe incorrect.")

    with tab2: # INSCRIPTION
        st.subheader("Créer un compte")
        ne = st.text_input("Email", key="reg_e")
        np = st.text_input("Pseudo", key="reg_p")
        nm = st.text_input("Choisir un mot de passe", type="password", key="reg_m")
        if st.button("Envoyer ma demande"):
            if ne and np and nm:
                if ne in df['email'].values:
                    st.error("Cet email est déjà utilisé.")
                else:
                    new_row = pd.DataFrame([[ne, np, nm, "En attente", 1, 10]], columns=["email", "pseudo", "password", "statut", "page", "rythme"])
                    sauver(pd.concat([df, new_row]))
                    st.success("Demande envoyée ! Yael va confirmer ton inscription par mail.")
            else: st.warning("Veuillez remplir tous les champs.")

    with tab3: # MOT DE PASSE OUBLIÉ
        fe = st.text_input("Email de récupération")
        if st.button("Recevoir mon mot de passe"):
            user = df[df['email'] == fe]
            if not user.empty:
                mdp = user.iloc[0]['password']
                sujet = "Récupération de ton mot de passe Coran"
                corps = f"Salam,\n\nVoici ton mot de passe pour l'application : {mdp}"
                if envoyer_email(fe, sujet, corps):
                    st.success("Email envoyé ! Vérifie ta boîte de réception.")
            else: st.error("Email inconnu dans notre base.")
    st.stop()

# --- ESPACE UTILISATEUR CONNECTÉ ---
df = charger()
user_idx = df[df['email'] == st.session_state["user_email"]].index[0]
user_data = df.loc[user_idx]

# SIDEBAR AVEC PANEL ADMIN POUR YAEL
with st.sidebar:
    st.header(f"👤 {user_data['pseudo']}")
    
    # Si c'est TOI (l'admin)
    if st.session_state["user_email"] == st.secrets["gmail"]["sender_email"]:
        st.divider()
        st.subheader("🛠️ Panel Admin (Yael)")
        attente = df[df['statut'] == "En attente"]
        if not attente.empty:
            for i, r in attente.iterrows():
                st.write(f"Inscrire : **{r['pseudo']}**")
                if st.button(f"Confirmer {r['pseudo']}", key=f"conf_{i}"):
                    df.at[i, 'statut'] = "Validé"
                    sauver(df)
                    envoyer_email(r['email'], "Inscription Confirmée !", f"Salam {r['pseudo']},\n\nYael a validé ton compte ! Tu peux maintenant te connecter à l'application.")
                    st.success(f"Compte de {r['pseudo']} validé !")
                    st.rerun()
        else:
            st.write("Aucune inscription en attente.")

    st.divider()
    if st.button("🔒 Déconnexion"):
        st.session_state["user_email"] = None
        st.rerun()

# --- CONTENU DE L'APP (BILAN) ---
st.title(f"📖 Bilan de {user_data['pseudo']}")

# Mise à jour progression
with st.expander("📝 Mettre à jour ma progression"):
    c1, c2 = st.columns(2)
    new_p = c1.number_input("Page actuelle", 1, 604, int(user_data['page']))
    new_r = c2.number_input("Rythme (pages/jour)", 1, 100, int(user_data['rythme']))
    if st.button("💾 Sauvegarder"):
        df.at[user_idx, 'page'] = new_p
        df.at[user_idx, 'rythme'] = new_r
        sauver(df)
        st.success("Données enregistrées !")
        st.rerun()

# Planning 30 jours
st.subheader("📅 Mon Planning")
auj = date.today()
jours = [(auj + timedelta(days=i)).strftime("%d/%m") for i in range(30)]
pages = [(int(user_data['page']) + (int(user_data['rythme']) * i)) % 604 or 1 for i in range(30)]
df_plan = pd.DataFrame({"Date": jours, "Page attendue": pages})
st.dataframe(df_plan, use_container_width=True)

# WhatsApp
if st.button("💬 WhatsApp"):
    msg = f"*Bilan Coran*\n👤 {user_data['pseudo']}\n📍 Page actuelle : {user_data['page']}\n🚀 Demain : {(user_data['page']+user_data['rythme'])%604}"
    st.text_area("Copier :", msg)
