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

VERSION = "5.1"
AUTHOR = "Yael"

# --- 2. GESTION DES FICHIERS ---
dossier = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(dossier, "config_dates.csv")
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv")
FORGOT_FILE = os.path.join(dossier, "forgot.csv")

def init_file(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["pseudo", "password", "role"])
init_file(DEMANDES_FILE, ["pseudo", "password"])
init_file(FORGOT_FILE, ["pseudo"])

# Vérification de l'Admin par défaut
df_users = pd.read_csv(USERS_FILE)
if "Yael" not in df_users["pseudo"].values:
    admin_row = pd.DataFrame([["Yael", "Yassine05", "Admin"]], columns=["pseudo", "password", "role"])
    df_users = pd.concat([df_users, admin_row], ignore_index=True)
    df_users.to_csv(USERS_FILE, index=False)

def verifier_et_creer_sauvegarde(fichier_cible):
    if not os.path.exists(fichier_cible) or os.stat(fichier_cible).st_size == 0:
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
        "titre_params": "⚙️ Configuration", "acces": "🔐 Connexion", 
        "user_label": "Pseudo :", "code_label": "Mot de passe :", 
        "btn_unlock": "Se connecter", "btn_signup": "Créer un compte", "btn_forgot": "Mot de passe oublié ?",
        "params": "Paramètres", "btn_logout": "🔒 Déconnexion", "etat": "📊 Mon État",
        "col_prog": "Progression", "btn_save": "💾 Enregistrer", 
        "plan": "📅 Mon Planning (7 jours)", "home_btn": "🏠 Accueil",
        "view_prog": "📊 Ma Progression Visuelle", "notif": "🔔 Notifications"
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
    div.stButton > button {{ border: 2px solid {COLOR} !important; border-radius: 10px !important; color: {COLOR} !important; font-weight: bold; width: 100%; }}
    div.stButton > button:hover {{ background-color: {COLOR} !important; color: white !important; }}
</style>""", unsafe_allow_html=True)

# --- 6. LOGIQUE CONNEXION / INSCRIPTION ---
if not st.session_state["auth"]:
    if st.session_state["view"] == "login":
        st.title(L["acces"])
        u_in = st.text_input(L["user_label"])
        p_in = st.text_input(L["code_label"], type="password")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(L["btn_unlock"]):
                user_match = df_users[(df_users["pseudo"] == u_in) & (df_users["password"] == p_in)]
                if not user_match.empty:
                    st.session_state["auth"] = True
                    st.session_state["user_connected"] = u_in
                    st.session_state["is_admin"] = (user_match.iloc[0]["role"] == "Admin")
                    st.rerun()
                else: st.error("Identifiants incorrects.")
        with c2:
            if st.button(L["btn_signup"]): st.session_state["view"] = "signup"; st.rerun()
        with c3:
            if st.button(L["btn_forgot"]):
                if u_in:
                    df_f = pd.read_csv(FORGOT_FILE)
                    if u_in not in df_f["pseudo"].values:
                        new_f = pd.DataFrame([[u_in]], columns=["pseudo"])
                        pd.concat([df_f, new_f], ignore_index=True).to_csv(FORGOT_FILE, index=False)
                    st.success("Signalé à Yael !")
                else: st.warning("Écris ton pseudo d'abord.")

    elif st.session_state["view"] == "signup":
        st.title("📝 Demande d'inscription")
        new_u = st.text_input("Choisis un Pseudo")
        new_p = st.text_input("Choisis un Mot de passe", type="password")
        conf_p = st.text_input("Confirme le Mot de passe", type="password")
        
        if st.button("Envoyer la demande"):
            if new_p != conf_p: st.error("Les mots de passe ne sont pas identiques.")
            elif new_u in df_users["pseudo"].values: st.error("Ce pseudo est déjà pris.")
            else:
                df_d = pd.read_csv(DEMANDES_FILE)
                if new_u not in df_d["pseudo"].values:
                    new_demande = pd.DataFrame([[new_u, new_p]], columns=["pseudo", "password"])
                    pd.concat([df_d, new_demande], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
                st.success("Demande envoyée ! Attend la validation de Yael.")
                if st.button("Retour à la connexion"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 7. BARRE LATÉRALE ---
with st.sidebar:
    st.header(f"👤 {st.session_state['user_connected']}")
    if st.button(L["home_btn"]): st.session_state["page_params"] = False; st.rerun()
    if st.button(L["params"]): st.session_state["page_params"] = "settings"; st.rerun()
    
    if st.session_state["is_admin"]:
        nb_attente = len(pd.read_csv(DEMANDES_FILE)) + len(pd.read_csv(FORGOT_FILE))
        if st.button(f"{L['notif']} ({nb_attente})"):
            st.session_state["page_params"] = "notif"; st.rerun()

    st.divider()
    if st.button(L["btn_logout"]): st.session_state["auth"] = False; st.rerun()

# --- 8. PAGES ADMIN & SETTINGS ---
if st.session_state["page_params"] == "notif" and st.session_state["is_admin"]:
    st.title("🔔 Notifications (Yael)")
    
    # Inscriptions
    st.subheader("Demandes d'inscription")
    df_d = pd.read_csv(DEMANDES_FILE)
    for i, r in df_d.iterrows():
        col1, col2, col3 = st.columns([2,1,1])
        col1.write(f"**{r['pseudo']}**")
        if col2.button("Approuver", key=f"app_{i}"):
            # Ajouter aux utilisateurs
            new_acc = pd.DataFrame([[r['pseudo'], r['password'], "Membre"]], columns=["pseudo", "password", "role"])
            pd.concat([pd.read_csv(USERS_FILE), new_acc], ignore_index=True).to_csv(USERS_FILE, index=False)
            # Créer sa ligne de données
            df.loc[r['pseudo']] = [1, 10, 0, 1]
            df.to_csv(DATA_FILE)
            df_d.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()
        if col3.button("Refuser", key=f"ref_{i}"):
            df_d.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()

    # MDP Oubliés
    st.divider()
    st.subheader("Mots de passe oubliés")
    df_f = pd.read_csv(FORGOT_FILE)
    for i, r in df_f.iterrows():
        col1, col2 = st.columns([2,2])
        col1.write(f"**{r['pseudo']}** attend un nouveau MDP.")
        n_p = col2.text_input("Nouveau MDP", key=f"fp_{i}")
        if col2.button("Changer et valider", key=f"fbtn_{i}"):
            u_db = pd.read_csv(USERS_FILE)
            u_db.loc[u_db["pseudo"] == r['pseudo'], "password"] = n_p
            u_db.to_csv(USERS_FILE, index=False)
            df_f.drop(i).to_csv(FORGOT_FILE, index=False); st.rerun()
    st.stop()

if st.session_state["page_params"] == "settings":
    st.title(L["titre_params"])
    if st.session_state["is_admin"]:
        st.subheader("Modifier un compte existant")
        cible = st.selectbox("Choisir l'utilisateur", df_users["pseudo"].values)
        n_p = st.text_input("Nouveau Mot de passe", type="password")
        if st.button("Mettre à jour"):
            df_users.loc[df_users["pseudo"] == cible, "password"] = n_p
            df_users.to_csv(USERS_FILE, index=False)
            st.success(f"Mot de passe de {cible} modifié !")
    else:
        st.info("Les paramètres avancés sont réservés à Yael.")
    st.stop()

# --- 9. PAGE ACCUEIL ---
st.title(L["titre_ram"] if st.session_state["ramadan_mode"] else L["titre_norm"])

# CONFIDENTIALITÉ : On filtre pour que l'utilisateur ne voie que lui (sauf si c'est Yael)
if st.session_state["is_admin"]:
    view_df = df
else:
    view_df = df[df.index == st.session_state["user_connected"]]

if not view_df.empty:
    st.subheader(L["etat"])
    recap = view_df.copy()
    total_pg = 604
    col_name = L["col_prog"]
    
    if st.session_state["ramadan_mode"]:
        recap[col_name] = (((recap["Page Actuelle"] + (recap["Cycles Finis"] * total_pg)) / (recap["Objectif Khatmas"] * total_pg)) * 100).round(1).astype(str) + "%"
    else:
        recap[col_name] = (recap["Page Actuelle"] / total_pg * 100).round(1).astype(str) + "%"
    
    st.table(recap)

    # Ma Progression Visuelle
    with st.expander(L["view_prog"]):
        for nom, row in view_df.iterrows():
            limit = row["Objectif Khatmas"] * total_pg if st.session_state["ramadan_mode"] else total_pg
            actuel = (row["Page Actuelle"] + (row["Cycles Finis"] * total_pg)) if st.session_state["ramadan_mode"] else row["Page Actuelle"]
            st.write(f"**{nom}**")
            st.progress(min(1.0, actuel/limit))

    # Mise à jour
    st.divider()
    col_maj, col_plan = st.columns(2)
    with col_maj:
        with st.expander("📝 Mettre à jour mon avancée", expanded=True):
            # L'utilisateur choisit son nom (ou Yael choisit qui elle veut)
            u_maj = st.selectbox("Profil", view_df.index)
            p_n = st.number_input("Page Actuelle", 1, 604, int(df.loc[u_maj, "Page Actuelle"]))
            r_n = st.number_input("Rythme (pages/jour)", 1, 100, int(df.loc[u_maj, "Rythme"]))
            if st.button(L["btn_save"]):
                df.loc[u_maj, ["Page Actuelle", "Rythme"]] = [p_n, r_n]
                df.to_csv(DATA_FILE); st.rerun()

    with col_plan:
        st.subheader(L["plan"])
        auj = date.today()
        # On affiche les 7 prochains jours
        planning = pd.DataFrame(index=[(auj + timedelta(days=i)).strftime("%d/%m") for i in range(7)])
        for n, r in view_df.iterrows():
            planning[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 1) for i in range(7)]
        st.dataframe(planning, use_container_width=True)
else:
    st.warning("Aucune donnée disponible. Attend que Yael crée ton profil.")
