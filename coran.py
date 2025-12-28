import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONFIGURATION INITIALE ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if "user_connected" not in st.session_state: st.session_state["user_connected"] = None
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "ramadan_mode" not in st.session_state: st.session_state["ramadan_mode"] = False
if "page_params" not in st.session_state: st.session_state["page_params"] = False

# --- 2. FONCTION EMAIL SMTP ---
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
        st.error(f"Erreur technique Email : {e}")
        return False

# --- 3. GESTION DES FICHIERS ---
dossier = os.path.dirname(__file__)
USERS_FILE = os.path.join(dossier, "users.csv")

# SI TU AS SUPPRIMÉ LE FICHIER, CE BLOC VA LE RECRÉER PROPREMENT
if not os.path.exists(USERS_FILE):
    df_users = pd.DataFrame([["yael@admin.com", "Yael", "Yassine05", "Admin", "Validé"]], 
                           columns=["email", "pseudo", "password", "role", "statut"])
    df_users.to_csv(USERS_FILE, index=False)
    st.info("Base de données initialisée : Compte Yael créé.")
else:
    df_users = pd.read_csv(USERS_FILE)

def verifier_et_creer_sauvegarde(fichier_cible):
    if not os.path.exists(fichier_cible):
        df_vide = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df_vide.index.name = "Nom"
        # Initialise uniquement avec les utilisateurs validés
        for p in df_users[df_users["statut"] == "Validé"]["pseudo"]:
            df_vide.loc[p] = [1, 10, 0, 1]
        df_vide.to_csv(fichier_cible)
        return df_vide
    return pd.read_csv(fichier_cible, index_col=0)

# --- 4. STYLE ET COULEURS ---
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"
st.set_page_config(page_title="Bilan Coran Pro", layout="wide", page_icon="🌙")

st.markdown(f"""<style>
    h1, h2, h3, label {{ color: {COLOR} !important; }}
    div.stButton > button {{ 
        background-color: #FFFFFF !important; 
        color: {COLOR} !important; 
        border: 2px solid {COLOR} !important; 
        border-radius: 10px; 
        font-weight: bold; 
    }}
    div.stButton > button:hover {{ background-color: {COLOR} !important; color: #FFFFFF !important; }}
    .stProgress > div > div > div > div {{ background-color: {COLOR} !important; }}
</style>""", unsafe_allow_html=True)

# --- 5. AUTHENTIFICATION ---
if not st.session_state["auth"]:
    st.title("🔐 Accès Bilan Coran")
    tab_log, tab_reg, tab_forgot = st.tabs(["Connexion", "S'inscrire", "Mdp oublié"])
    
    with tab_log:
        u_input = st.text_input("Pseudo", placeholder="Yael")
        p_input = st.text_input("Mot de passe", type="password", placeholder="Yassine05")
        if st.button("Se connecter"):
            user_row = df_users[(df_users["pseudo"] == u_input) & (df_users["password"].astype(str) == p_input)]
            if not user_row.empty:
                if user_row.iloc[0]["statut"] == "Validé":
                    st.session_state["auth"] = True
                    st.session_state["user_connected"] = u_input
                    st.session_state["is_admin"] = (user_row.iloc[0]["role"] == "Admin")
                    st.rerun()
                else: st.warning("⏳ Compte en attente de validation.")
            else: st.error("Identifiants incorrects.")

    with tab_reg:
        re_e = st.text_input("Ton Email (pour les notifications)")
        re_p = st.text_input("Pseudo souhaité")
        re_m = st.text_input("Mot de passe souhaité", type="password")
        if st.button("S'inscrire"):
            if re_e and re_p and re_m:
                if re_p in df_users["pseudo"].values: st.error("Pseudo déjà pris.")
                else:
                    new_u = pd.DataFrame([[re_e, re_p, re_m, "Membre", "En attente"]], columns=["email", "pseudo", "password", "role", "statut"])
                    pd.concat([df_users, new_u]).to_csv(USERS_FILE, index=False)
                    st.success("Demande envoyée ! Yael devra valider ton compte.")
            else: st.warning("Veuillez remplir tous les champs.")

    with tab_forgot:
        fe = st.text_input("Email d'inscription")
        if st.button("Envoyer mes accès"):
            user = df_users[df_users["email"] == fe]
            if not user.empty:
                if envoyer_email(fe, "Accès Coran", f"Pseudo: {user.iloc[0]['pseudo']}\nPass: {user.iloc[0]['password']}"):
                    st.success("Email envoyé !")
            else: st.error("Email inconnu.")
    st.stop()

# --- 6. CHARGEMENT DATA LECTURE ---
suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
DATA_FILE = os.path.join(dossier, f"sauvegarde_{suffixe}.csv")
df_data = verifier_et_creer_sauvegarde(DATA_FILE)

# --- 7. SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_connected']}")
    if st.button("🏠 Accueil"): st.session_state["page_params"] = False; st.rerun()
    if st.button("⚙️ Paramètres"): st.session_state["page_params"] = True; st.rerun()
    
    if st.session_state["is_admin"]:
        st.divider()
        st.subheader("🛠️ Panel Admin")
        attente = df_users[df_users["statut"] == "En attente"]
        for i, r in attente.iterrows():
            st.write(f"Valider **{r['pseudo']}** ?")
            if st.button(f"Confirmer {r['pseudo']}", key=f"v_{i}"):
                df_users.loc[df_users["pseudo"] == r["pseudo"], "statut"] = "Validé"
                df_users.to_csv(USERS_FILE, index=False)
                df_data.loc[r["pseudo"]] = [1, 10, 0, 1]
                df_data.to_csv(DATA_FILE)
                envoyer_email(r["email"], "Compte Validé", f"Salam {r['pseudo']}, ton compte est prêt !")
                st.rerun()

    st.divider()
    btn_txt = "📖 Mode Normal" if st.session_state["ramadan_mode"] else "🌙 Mode Ramadan"
    if st.button(btn_txt):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]
        st.rerun()
    if st.button("🔒 Déconnexion"):
        st.session_state["auth"] = False
        st.rerun()

# --- 8. CONTENU ---
if st.session_state["page_params"]:
    st.title("⚙️ Paramètres")
    if st.session_state["is_admin"]:
        cible = st.selectbox("Supprimer un membre :", [p for p in df_users["pseudo"] if p != "Yael"])
        if st.button("🗑️ Supprimer"):
            df_users = df_users[df_users["pseudo"] != cible]
            df_users.to_csv(USERS_FILE, index=False)
            st.rerun()
    st.stop()

st.title("🌙 Mode Ramadan Pro" if st.session_state["ramadan_mode"] else "📖 Bilan de Lecture")

# Affichage Tableau
recap = df_data.copy()
if st.session_state["ramadan_mode"]:
    recap["Progression"] = (((recap["Page Actuelle"] + (recap["Cycles Finis"] * 604)) / (recap["Objectif Khatmas"] * 604)) * 100).round(1).astype(str) + "%"
else:
    recap["Progression"] = (recap["Page Actuelle"] / 604 * 100).round(1).astype(str) + "%"
st.table(recap)

# Mise à jour
with st.expander("📝 Ma progression"):
    me = st.session_state["user_connected"]
    p_act = st.number_input("Page actuelle :", 1, 604, int(df_data.loc[me, "Page Actuelle"]))
    if st.session_state["ramadan_mode"]:
        k_obj = st.number_input("Objectif Khatmas :", 1, 10, int(df_data.loc[me, "Objectif Khatmas"]))
        c_fin = st.number_input("Khatmas finies :", 0, 10, int(df_data.loc[me, "Cycles Finis"]))
        if st.button("💾 Enregistrer"):
            df_data.loc[me] = [p_act, 10, c_fin, k_obj]
            df_data.to_csv(DATA_FILE); st.success("OK !"); st.rerun()
    else:
        r_act = st.number_input("Rythme :", 1, 100, int(df_data.loc[me, "Rythme"]))
        if st.button("💾 Enregistrer"):
            df_data.loc[me, ["Page Actuelle", "Rythme"]] = [p_act, r_act]
            df_data.to_csv(DATA_FILE); st.success("OK !"); st.rerun()

# Planning 30 jours
st.subheader("📅 Mon Planning")
plan_df = pd.DataFrame(index=[(date.today() + timedelta(days=i)).strftime("%d/%m") for i in range(30)])
for n, r in df_data.iterrows():
    plan_df[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 604) for i in range(30)]
st.dataframe(plan_df, use_container_width=True)
