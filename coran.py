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

# --- 2. FONCTION EMAIL (AVEC AFFICHAGE D'ERREUR) ---
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

# Chargement / Création forcée du compte Yael
if not os.path.exists(USERS_FILE):
    df_users = pd.DataFrame([["yael@admin.com", "Yael", "Yassine05", "Admin", "Validé"]], 
                           columns=["email", "pseudo", "password", "role", "statut"])
    df_users.to_csv(USERS_FILE, index=False)
else:
    df_users = pd.read_csv(USERS_FILE)

def verifier_et_creer_sauvegarde(fichier_cible):
    if not os.path.exists(fichier_cible):
        df_vide = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df_vide.index.name = "Nom"
        # On n'ajoute que les validés
        valid_users = df_users[df_users["statut"] == "Validé"]["pseudo"]
        for p in valid_users:
            df_vide.loc[p] = [1, 10, 0, 1]
        df_vide.to_csv(fichier_cible)
        return df_vide
    return pd.read_csv(fichier_cible, index_col=0)

# --- 4. STYLE VISUEL ---
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"
st.set_page_config(page_title="Bilan Coran Pro", layout="wide", page_icon="🌙")

st.markdown(f"""<style>
    .main {{ background-color: #FFFFFF; }}
    h1, h2, h3, stMetric {{ color: {COLOR} !important; }}
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

# --- 5. ÉCRAN DE CONNEXION / INSCRIPTION ---
if not st.session_state["auth"]:
    st.title("🔐 Accès Bilan Coran")
    tab_log, tab_reg, tab_forgot = st.tabs(["Connexion", "S'inscrire", "Mdp oublié"])
    
    with tab_log:
        u_input = st.text_input("Pseudo (ex: Yael)")
        p_input = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            # On cherche le pseudo exact (sensible à la casse)
            user_row = df_users[(df_users["pseudo"] == u_input) & (df_users["password"].astype(str) == p_input)]
            if not user_row.empty:
                if user_row.iloc[0]["statut"] == "Validé":
                    st.session_state["auth"] = True
                    st.session_state["user_connected"] = u_input
                    st.session_state["is_admin"] = (user_row.iloc[0]["role"] == "Admin")
                    st.rerun()
                else:
                    st.warning("⏳ Ton compte est en attente de validation par Yael.")
            else:
                st.error("Pseudo ou mot de passe incorrect.")

    with tab_reg:
        re_e = st.text_input("Ton Email (obligatoire pour la validation)")
        re_p = st.text_input("Choisis un Pseudo")
        re_m = st.text_input("Choisis un Mot de passe", type="password")
        if st.button("Envoyer ma demande"):
            if re_e and re_p and re_m:
                if re_p in df_users["pseudo"].values: 
                    st.error("Ce pseudo est déjà utilisé.")
                else:
                    new_u = pd.DataFrame([[re_e, re_p, re_m, "Membre", "En attente"]], 
                                        columns=["email", "pseudo", "password", "role", "statut"])
                    df_users = pd.concat([df_users, new_u])
                    df_users.to_csv(USERS_FILE, index=False)
                    st.success("Demande enregistrée ! Attends que Yael valide ton compte.")
            else:
                st.warning("Merci de remplir tous les champs.")

    with tab_forgot:
        fe = st.text_input("Email d'inscription")
        if st.button("Récupérer mes accès"):
            user = df_users[df_users["email"] == fe]
            if not user.empty:
                sujet = "Tes accès Bilan Coran"
                corps = f"Salam,\n\nVoici tes identifiants :\nPseudo : {user.iloc[0]['pseudo']}\nMot de passe : {user.iloc[0]['password']}"
                if envoyer_email(fe, sujet, corps):
                    st.success("Email envoyé avec succès !")
            else:
                st.error("Email inconnu dans la base.")
    st.stop()

# --- 6. CHARGEMENT DES DONNÉES DE LECTURE ---
suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
DATA_FILE = os.path.join(dossier, f"sauvegarde_{suffixe}.csv")
df_data = verifier_et_creer_sauvegarde(DATA_FILE)

# --- 7. BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.title(f"Salut, {st.session_state['user_connected']} !")
    if st.button("🏠 Accueil"): st.session_state["page_params"] = False; st.rerun()
    if st.button("⚙️ Paramètres"): st.session_state["page_params"] = True; st.rerun()
    
    # PANEL ADMIN (VALIDATION)
    if st.session_state["is_admin"]:
        st.divider()
        st.subheader("🛠️ Panel Admin")
        attente = df_users[df_users["statut"] == "En attente"]
        if attente.empty:
            st.write("Aucune demande.")
        for i, r in attente.iterrows():
            st.write(f"Inscrire **{r['pseudo']}** ?")
            if st.button(f"✅ Valider", key=f"v_{i}"):
                # 1. Valider dans users.csv
                df_users.loc[df_users["pseudo"] == r["pseudo"], "statut"] = "Validé"
                df_users.to_csv(USERS_FILE, index=False)
                # 2. Créer sa ligne dans la sauvegarde de lecture
                df_data.loc[r["pseudo"]] = [1, 10, 0, 1]
                df_data.to_csv(DATA_FILE)
                # 3. Envoyer Email
                envoyer_email(r["email"], "Compte Validé !", f"Salam {r['pseudo']},\n\nYael a validé ton compte ! Tu peux maintenant te connecter avec ton pseudo.")
                st.success(f"{r['pseudo']} validé !")
                st.rerun()

    st.divider()
    btn_txt = "📖 Mode Normal" if st.session_state["ramadan_mode"] else "🌙 Mode Ramadan"
    if st.button(btn_txt):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]
        st.rerun()
    if st.button("🔒 Déconnexion"):
        st.session_state["auth"] = False
        st.rerun()

# --- 8. PAGE CONFIGURATION ---
if st.session_state["page_params"]:
    st.title("⚙️ Configuration")
    if st.session_state["is_admin"]:
        st.subheader("🗑️ Supprimer un membre")
        cible = st.selectbox("Choisir :", [p for p in df_users["pseudo"] if p != "Yael"])
        if st.button("🗑️ Supprimer définitivement"):
            df_users = df_users[df_users["pseudo"] != cible]
            df_users.to_csv(USERS_FILE, index=False)
            if cible in df_data.index: 
                df_data = df_data.drop(cible)
                df_data.to_csv(DATA_FILE)
            st.success("Membre supprimé.")
            st.rerun()
    else:
        st.info("Seul l'administrateur peut gérer les membres.")
    st.stop()

# --- 9. PAGE ACCUEIL (TABLEAU DE BORD) ---
st.title("🌙 Mode Ramadan Pro" if st.session_state["ramadan_mode"] else "📖 Bilan de Lecture")

# Table de progression
st.subheader("📊 État des troupes")
recap = df_data.copy()
if st.session_state["ramadan_mode"]:
    recap["Progression"] = (((recap["Page Actuelle"] + (recap["Cycles Finis"] * 604)) / (recap["Objectif Khatmas"] * 604)) * 100).round(1).astype(str) + "%"
else:
    recap["Progression"] = (recap["Page Actuelle"] / 604 * 100).round(1).astype(str) + "%"
st.table(recap)

# Mise à jour
st.divider()
col_update, col_msg = st.columns(2)

with col_update:
    with st.expander("📝 Ma progression", expanded=True):
        me = st.session_state["user_connected"]
        p_act = st.number_input("Ma page actuelle :", 1, 604, int(df_data.loc[me, "Page Actuelle"]))
        if st.session_state["ramadan_mode"]:
            k_obj = st.number_input("Objectif Khatmas :", 1, 10, int(df_data.loc[me, "Objectif Khatmas"]))
            c_fin = st.number_input("Khatmas finies :", 0, 10, int(df_data.loc[me, "Cycles Finis"]))
            if st.button("💾 Sauvegarder"):
                df_data.loc[me] = [p_act, df_data.loc[me, "Rythme"], c_fin, k_obj]
                df_data.to_csv(DATA_FILE)
                st.success("C'est enregistré !") ; st.rerun()
        else:
            r_act = st.number_input("Mon rythme (pages/jour) :", 1, 100, int(df_data.loc[me, "Rythme"]))
            if st.button("💾 Sauvegarder"):
                df_data.loc[me, ["Page Actuelle", "Rythme"]] = [p_act, r_act]
                df_data.to_csv(DATA_FILE)
                st.success("C'est enregistré !") ; st.rerun()

with col_msg:
    with st.expander("💬 WhatsApp"):
        me = st.session_state["user_connected"]
        msg = f"*Bilan Coran - {me}*\n📍 Page : {df_data.loc[me, 'Page Actuelle']}\n🚀 Demain : {(df_data.loc[me, 'Page Actuelle'] + df_data.loc[me, 'Rythme']) % 604}"
        st.text_area("Copie ce texte :", msg, height=120)
        st.info("Partage tes efforts avec les autres ! ✨")

# Planning 30 jours
st.subheader("📅 Mon Planning 30 jours")
plan_df = pd.DataFrame(index=[(date.today() + timedelta(days=i)).strftime("%d/%m") for i in range(30)])
for n, r in df_data.iterrows():
    plan_df[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 604) for i in range(30)]
st.dataframe(plan_df, use_container_width=True)
