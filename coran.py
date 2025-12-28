import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random

# --- 1. CONFIGURATION INITIALE & SESSION ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if "user_connected" not in st.session_state: st.session_state["user_connected"] = None
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "ramadan_mode" not in st.session_state: st.session_state["ramadan_mode"] = False
if "page_params" not in st.session_state: st.session_state["page_params"] = False
if "langue" not in st.session_state: st.session_state["langue"] = "Français"
if "view" not in st.session_state: st.session_state["view"] = "login"

VERSION = "5.0"
LAST_UPDATE = "28/12/2025" 
AUTHOR = "Yael"

# --- 2. GESTION DES FICHIERS ---
dossier = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(dossier, "config_dates.csv")
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv") # Inscriptions en attente
FORGOT_FILE = os.path.join(dossier, "forgot.csv")     # Mdp oubliés

def init_file(file, columns):
    if not os.path.exists(file):
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["pseudo", "password", "role"])
init_file(DEMANDES_FILE, ["pseudo", "password"])
init_file(FORGOT_FILE, ["pseudo"])

# Vérification Admin par défaut
df_users = pd.read_csv(USERS_FILE)
if "Yael" not in df_users["pseudo"].values:
    df_users = pd.concat([df_users, pd.DataFrame([["Yael", "Yassine05", "Admin"]], columns=["pseudo", "password", "role"])], ignore_index=True)
    df_users.to_csv(USERS_FILE, index=False)

def verifier_et_creer_sauvegarde(fichier_cible):
    if not os.path.exists(fichier_cible):
        df_v = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df_v.index.name = "Nom"
        df_v.loc["Yael"] = [1, 10, 0, 1]
        df_v.to_csv(fichier_cible)
        return df_v
    return pd.read_csv(fichier_cible, index_col=0)

# --- 3. TRADUCTIONS ---
TRAD = {
    "Français": {
        "titre_norm": "📖 Mon Bilan Coran", "titre_ram": "🌙 Mode Ramadan Pro", 
        "acces": "🔐 Connexion", "user_label": "Pseudo :", "code_label": "Mot de passe :", 
        "btn_unlock": "Se connecter", "btn_signup": "Créer un compte", "btn_forgot": "Mot de passe oublié ?",
        "params": "Paramètres", "btn_logout": "🔒 Déconnexion", "etat": "📊 Mon État",
        "btn_save": "💾 Enregistrer", "plan": "📅 Mon Planning 30 jours", "home_btn": "🏠 Accueil",
        "view_prog": "📊 Ma Progression", "info_title": "ℹ️ Infos", "notif": "🔔 Notifications"
    }
}
L = TRAD["Français"]

# --- 4. CHARGEMENT DATA ---
suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
DATA_FILE = os.path.join(dossier, f"sauvegarde_{suffixe}.csv")
df = verifier_et_creer_sauvegarde(DATA_FILE)

# --- 5. STYLE ---
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"
st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"""<style>
    h1, h2, h3, p, label {{ color: {COLOR} !important; }}
    div.stButton > button {{ border: 2px solid {COLOR} !important; border-radius: 10px !important; color: {COLOR} !important; font-weight: bold; }}
    div.stButton > button:hover {{ background-color: {COLOR} !important; color: white !important; }}
</style>""", unsafe_allow_html=True)

# --- 6. LOGIQUE DE CONNEXION / INSCRIPTION ---
if not st.session_state["auth"]:
    if st.session_state["view"] == "login":
        st.title(L["acces"])
        u = st.text_input(L["user_label"])
        p = st.text_input(L["code_label"], type="password")
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button(L["btn_unlock"]):
                user_match = df_users[(df_users["pseudo"] == u) & (df_users["password"] == p)]
                if not user_match.empty:
                    st.session_state["auth"] = True
                    st.session_state["user_connected"] = u
                    st.session_state["is_admin"] = (user_match.iloc[0]["role"] == "Admin")
                    st.rerun()
                else: st.error("Pseudo ou mot de passe incorrect.")
        with col_b2:
            if st.button(L["btn_signup"]): st.session_state["view"] = "signup"; st.rerun()
        with col_b3:
            if st.button(L["btn_forgot"]):
                if u:
                    df_f = pd.read_csv(FORGOT_FILE)
                    if u not in df_f["pseudo"].values:
                        pd.concat([df_f, pd.DataFrame([[u]], columns=["pseudo"])], ignore_index=True).to_csv(FORGOT_FILE, index=False)
                    st.success("Demande envoyée à Yael.")
                else: st.warning("Entrez votre pseudo d'abord.")

    elif st.session_state["view"] == "signup":
        st.title("📝 Inscription")
        new_u = st.text_input("Choisir un pseudo")
        new_p = st.text_input("Mot de passe", type="password")
        conf_p = st.text_input("Confirmer le mot de passe", type="password")
        if st.button("Terminer l'inscription"):
            if new_p != conf_p: st.error("Les mots de passe ne correspondent pas.")
            elif new_u in df_users["pseudo"].values: st.error("Ce pseudo existe déjà.")
            else:
                df_d = pd.read_csv(DEMANDES_FILE)
                if new_u not in df_d["pseudo"].values:
                    pd.concat([df_d, pd.DataFrame([[new_u, new_p]], columns=["pseudo", "password"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
                st.success("Demande envoyée ! Attend que Yael l'approuve.")
                if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 7. BARRE LATÉRALE ---
with st.sidebar:
    st.header(f"👤 {st.session_state['user_connected']}")
    if st.button(L["home_btn"]): st.session_state["page_params"] = False; st.rerun()
    if st.button(L["params"]): st.session_state["page_params"] = True; st.rerun()
    
    if st.session_state["is_admin"]:
        st.divider()
        nb_demandes = len(pd.read_csv(DEMANDES_FILE)) + len(pd.read_csv(FORGOT_FILE))
        if st.button(f"{L['notif']} ({nb_demandes})"):
            st.session_state["page_params"] = "notif"; st.rerun()

    st.divider()
    if st.button(L["btn_logout"]): st.session_state["auth"] = False; st.rerun()

# --- 8. PAGES (PARAMS / NOTIFS) ---
if st.session_state["page_params"] == "notif" and st.session_state["is_admin"]:
    st.title("🔔 Notifications Admin")
    
    # Gestion des inscriptions
    st.subheader("Inscriptions en attente")
    df_d = pd.read_csv(DEMANDES_FILE)
    for i, row in df_d.iterrows():
        c1, c2, c3 = st.columns([2,1,1])
        c1.write(f"**{row['pseudo']}** veut s'inscrire.")
        if c2.button("Approuver", key=f"app_{i}"):
            # Ajouter au users
            new_u = pd.DataFrame([[row['pseudo'], row['password'], "Membre"]], columns=["pseudo", "password", "role"])
            pd.concat([pd.read_csv(USERS_FILE), new_u], ignore_index=True).to_csv(USERS_FILE, index=False)
            # Ajouter aux data
            df.loc[row['pseudo']] = [1, 10, 0, 1]; df.to_csv(DATA_FILE)
            # Supprimer la demande
            df_d.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()
        if c3.button("Refuser", key=f"ref_{i}"):
            df_d.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()

    # Gestion des mots de passe oubliés
    st.divider()
    st.subheader("Mots de passe oubliés")
    df_f = pd.read_csv(FORGOT_FILE)
    for i, row in df_f.iterrows():
        c1, c2 = st.columns([2,2])
        c1.write(f"**{row['pseudo']}** a oublié son mdp.")
        new_mdp_admin = c2.text_input("Nouveau MDP", key=f"new_p_{i}")
        if c2.button("Changer le MDP", key=f"btn_f_{i}"):
            u_db = pd.read_csv(USERS_FILE)
            u_db.loc[u_db["pseudo"] == row['pseudo'], "password"] = new_mdp_admin
            u_db.to_csv(USERS_FILE, index=False)
            df_f.drop(i).to_csv(FORGOT_FILE, index=False); st.rerun()
    st.stop()

# Page Paramètres
if st.session_state["page_params"] == True:
    st.title(L["titre_params"])
    if st.session_state["is_admin"]:
        st.subheader("Modifier le MDP de quelqu'un")
        u_cible = st.selectbox("Choisir un membre", df_users["pseudo"].values)
        mdp_cible = st.text_input("Nouveau mot de passe", type="password")
        if st.button("Mettre à jour le mot de passe"):
            df_users.loc[df_users["pseudo"] == u_cible, "password"] = mdp_cible
            df_users.to_csv(USERS_FILE, index=False)
            st.success("C'est fait !")
    else:
        st.info("Seul Yael peut modifier les paramètres globaux.")
    st.stop()

# --- 9. ACCUEIL (CONFIDENTIALITÉ APPLIQUÉE) ---
st.title(L["titre_ram"] if st.session_state["ramadan_mode"] else L["titre_norm"])

# Filtrage : Admin voit tout, Membre voit QUE sa ligne
if st.session_state["is_admin"]:
    display_df = df
else:
    display_df = df[df.index == st.session_state["user_connected"]]

if not display_df.empty:
    st.subheader(L["etat"])
    recap = display_df.copy()
    total_pg = 604
    if st.session_state["ramadan_mode"]:
        recap[L["col_prog"]] = (((recap["Page Actuelle"] + (recap["Cycles Finis"] * total_pg)) / (recap["Objectif Khatmas"] * total_pg)) * 100).round(1).astype(str) + "%"
    else:
        recap[L["col_prog"]] = (recap["Page Actuelle"] / total_pg * 100).round(1).astype(str) + "%"
    st.table(recap)

    # Progression Visuelle
    with st.expander(L["view_prog"]):
        for nom, row in display_df.iterrows():
            limit = row["Objectif Khatmas"] * total_pg if st.session_state["ramadan_mode"] else total_pg
            fait = (row["Page Actuelle"] + (row["Cycles Finis"] * total_pg)) if st.session_state["ramadan_mode"] else row["Page Actuelle"]
            st.write(f"**{nom}**")
            st.progress(min(1.0, fait/limit))

    # Mise à jour (Seulement pour soi ou Admin pour tous)
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("📝 Mettre à jour ma page", expanded=True):
            user_select = st.selectbox("Profil", display_df.index)
            p_n = st.number_input("Page actuelle", 1, 604, int(df.loc[user_select, "Page Actuelle"]))
            if st.button(L["btn_save"]):
                df.loc[user_select, "Page Actuelle"] = p_n
                df.to_csv(DATA_FILE); st.rerun()

    with col2:
        st.subheader(L["plan"])
        auj = date.today()
        plan = pd.DataFrame(index=[(auj + timedelta(days=i)).strftime("%d/%m") for i in range(7)])
        for n, r in display_df.iterrows():
            plan[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 1) for i in range(7)]
        st.dataframe(plan)
else:
    st.warning("Ton profil n'a pas encore été créé par l'Admin.")
