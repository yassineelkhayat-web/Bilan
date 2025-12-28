import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import random
from datetime import date, timedelta

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Bilan Coran Pro", layout="wide", page_icon="🌙")

# --- 2. FONCTION ENVOI EMAIL ---
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

# --- 3. GESTION DE LA BASE DE DONNÉES ---
USERS_FILE = "users_db.csv"
if not os.path.exists(USERS_FILE):
    # Création du fichier avec Yael comme Admin par défaut
    df_init = pd.DataFrame([["yael@admin.com", "Yael", "Yassine05", "Validé", 1, 10, 0, 1]], 
                           columns=["email", "pseudo", "password", "statut", "page", "rythme", "finies", "objectif"])
    df_init.to_csv(USERS_FILE, index=False)

def charger(): return pd.read_csv(USERS_FILE)
def sauver(df): df.to_csv(USERS_FILE, index=False)

# --- 4. SESSION STATE ---
if "user_pseudo" not in st.session_state: st.session_state["user_pseudo"] = None
if "ramadan_mode" not in st.session_state: st.session_state["ramadan_mode"] = False

HADITHS = [
    "Le meilleur d'entre vous est celui qui apprend le Coran et l'enseigne. | Bukhari",
    "Lisez le Coran ! Car il viendra au Jour de la Résurrection en intercesseur pour les siens. | Muslim",
    "Celui qui récite une lettre du Livre d'Allah a pour cela une bonne action. | Tirmidhi"
]

# --- 5. AUTHENTIFICATION ---
if st.session_state["user_pseudo"] is None:
    st.title("🌙 Accès Bilan Coran")
    tab1, tab2, tab3 = st.tabs(["Connexion", "Inscription", "Mdp oublié"])
    df = charger()

    with tab1: # CONNEXION PAR PSEUDO
        ps = st.text_input("Pseudo", key="login_pseudo")
        pw = st.text_input("Mot de passe", type="password", key="login_pw")
        if st.button("Se connecter"):
            user = df[(df['pseudo'] == ps) & (df['password'].astype(str) == pw)]
            if not user.empty:
                if user.iloc[0]['statut'] == "Validé":
                    st.session_state["user_pseudo"] = ps
                    st.rerun()
                else:
                    st.warning("⏳ Ton compte est en attente de validation par Yael.")
            else: st.error("Pseudo ou mot de passe incorrect.")

    with tab2: # INSCRIPTION
        ne = st.text_input("Ton Email (pour les notifications)", key="reg_email")
        np = st.text_input("Choisis un Pseudo", key="reg_pseudo")
        nm = st.text_input("Choisis un Mot de passe", type="password", key="reg_mdp")
        if st.button("S'inscrire"):
            if ne and np and nm:
                if np in df['pseudo'].values: st.error("Ce pseudo est déjà pris.")
                else:
                    new_row = pd.DataFrame([[ne, np, nm, "En attente", 1, 10, 0, 1]], 
                                         columns=["email", "pseudo", "password", "statut", "page", "rythme", "finies", "objectif"])
                    sauver(pd.concat([df, new_row]))
                    st.success("Demande envoyée ! Yael va valider ton compte bientôt.")
            else: st.warning("Remplis tous les champs.")

    with tab3: # MOT DE PASSE OUBLIÉ (VIA EMAIL)
        fe = st.text_input("Email utilisé à l'inscription")
        if st.button("Récupérer mes accès"):
            user = df[df['email'] == fe]
            if not user.empty:
                corps = f"Salam,\n\nVoici tes accès :\nPseudo : {user.iloc[0]['pseudo']}\nMot de passe : {user.iloc[0]['password']}"
                if envoyer_email(fe, "Identifiants Bilan Coran", corps):
                    st.success("Email envoyé avec ton pseudo et mot de passe !")
            else: st.error("Email introuvable.")
    st.stop()

# --- 6. ESPACE CONNECTÉ ---
df = charger()
user_idx = df[df['pseudo'] == st.session_state["user_pseudo"]].index[0]
user_data = df.loc[user_idx]

# --- SIDEBAR & ADMIN PANEL ---
with st.sidebar:
    st.header(f"👤 {user_data['pseudo']}")
    
    # Bouton Mode Ramadan
    if st.button("🌙 Mode Ramadan" if not st.session_state["ramadan_mode"] else "📖 Mode Normal"):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]
        st.rerun()

    # PANEL ADMIN (Visible uniquement par Yael)
    if st.session_state["user_pseudo"] == "Yael":
        st.divider()
        st.subheader("🛠️ Panel Admin")
        attente = df[df['statut'] == "En attente"]
        if not attente.empty:
            for i, r in attente.iterrows():
                st.write(f"Valider **{r['pseudo']}** ?")
                if st.button(f"Confirmer {r['pseudo']}", key=f"v_{i}"):
                    df.at[i, 'statut'] = "Validé"
                    sauver(df)
                    envoyer_email(r['email'], "Compte Validé !", f"Salam {r['pseudo']},\n\nYael a validé ton compte ! Tu peux te connecter.")
                    st.rerun()
        else: st.write("Aucune demande.")

    st.divider()
    if st.button("🔒 Déconnexion"):
        st.session_state["user_pseudo"] = None
        st.rerun()

# --- 7. CONTENU PRINCIPAL ---
st.title(f"📖 Bilan de {user_data['pseudo']}")
if st.session_state["ramadan_mode"]:
    st.subheader("🌙 MODE RAMADAN ACTIVÉ")

# MISE À JOUR
with st.expander("📝 Mettre à jour ma progression"):
    c1, c2 = st.columns(2)
    p_act = c1.number_input("Page actuelle", 1, 604, int(user_data['page']))
    r_act = c2.number_input("Rythme (pages/jour)", 1, 100, int(user_data['rythme']))
    
    if st.session_state["ramadan_mode"]:
        c3, c4 = st.columns(2)
        obj = c3.number_input("Objectif Khatmas", 1, 10, int(user_data.get('objectif', 1)))
        fin = c4.number_input("Khatmas finies", 0, 10, int(user_data.get('finies', 0)))
    
    if st.button("💾 Sauvegarder"):
        df.at[user_idx, 'page'] = p_act
        df.at[user_idx, 'rythme'] = r_act
        if st.session_state["ramadan_mode"]:
            df.at[user_idx, 'objectif'] = obj
            df.at[user_idx, 'finies'] = fin
        sauver(df)
        st.success("Données enregistrées !")
        st.rerun()

# PROGRESSION VISUELLE
st.subheader("📊 Progression")
if st.session_state["ramadan_mode"]:
    total_a_lire = user_data['objectif'] * 604
    lu = (user_data['page']) + (user_data['finies'] * 604)
    prog = min(100.0, (lu / total_a_lire) * 100)
    st.write(f"Khatma en cours : **{user_data['finies'] + 1} / {user_data['objectif']}**")
else:
    prog = (user_data['page'] / 604) * 100

st.progress(prog / 100)
st.write(f"Avancement global : **{prog:.1f}%**")

# PLANNING 30 JOURS
st.subheader("📅 Mon Planning (30 jours)")
auj = date.today()
jours = [(auj + timedelta(days=i)).strftime("%d/%m") for i in range(30)]
pages_prev = []
for i in range(30):
    p = (int(user_data['page']) + (int(user_data['rythme']) * i))
    p = p % 604 if p % 604 != 0 else 604
    pages_prev.append(int(p))

st.dataframe(pd.DataFrame({"Date": jours, "Page attendue": pages_prev}), use_container_width=True)

# WHATSAPP & HADITH
st.divider()
cw, ch = st.columns(2)
with cw:
    if st.button("💬 Générer message WhatsApp"):
        msg = f"*Bilan Coran - {user_data['pseudo']}*\n📍 Page : {user_data['page']}\n🚀 Objectif demain : {(user_data['page'] + user_data['rythme']) % 604}"
        st.text_area("Copie ce message :", msg)
with ch:
    if st.button("✨ Hadith du jour"):
        st.info(random.choice(HADITHS))
