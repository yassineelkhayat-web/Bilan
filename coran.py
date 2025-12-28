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
if "view" not in st.session_state: st.session_state["view"] = "login"

VERSION = "5.2"
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

# Vérification Admin
df_users = pd.read_csv(USERS_FILE)
if "Yael" not in df_users["pseudo"].values:
    admin_row = pd.DataFrame([["Yael", "Yassine05", "Admin"]], columns=["pseudo", "password", "role"])
    df_users = pd.concat([df_users, admin_row], ignore_index=True)
    df_users.to_csv(USERS_FILE, index=False)

# Chargement dates Ramadan
if os.path.exists(CONFIG_FILE):
    conf_df = pd.read_csv(CONFIG_FILE)
    st.session_state["debut_ramadan"] = date.fromisoformat(conf_df.iloc[0]["debut"])
    st.session_state["fin_ramadan"] = date.fromisoformat(conf_df.iloc[0]["fin"])
else:
    st.session_state["debut_ramadan"] = date(2025, 3, 1)
    st.session_state["fin_ramadan"] = date(2025, 3, 30)

def verifier_et_creer_sauvegarde(fichier_cible):
    if not os.path.exists(fichier_cible) or os.stat(fichier_cible).st_size == 0:
        df_v = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df_v.index.name = "Nom"
        df_v.loc["Yael"] = [1, 10, 0, 1]
        df_v.to_csv(fichier_cible)
        return df_v
    df_load = pd.read_csv(fichier_cible, index_col=0)
    if "Cycles Finis" not in df_load.columns: df_load["Cycles Finis"] = 0
    if "Objectif Khatmas" not in df_load.columns: df_load["Objectif Khatmas"] = 1
    return df_load

# --- 3. TRADUCTIONS ---
TRAD = {
    "Français": {
        "titre_norm": "📖 Bilan de Lecture", "titre_ram": "🌙 Mode Ramadan Pro", 
        "acces": "🔐 Connexion", "user_label": "Pseudo :", "code_label": "Mot de passe :", 
        "btn_unlock": "Se connecter", "btn_signup": "Créer un compte", "btn_forgot": "Mdp oublié ?",
        "btn_logout": "🔒 Déconnexion", "col_prog": "Progression", "btn_save": "💾 Enregistrer",
        "home_btn": "🏠 Accueil", "notif": "🔔 Notifications", "params": "⚙️ Paramètres",
        "mode_ram_btn": "Passer au Mode Ramadan", "mode_norm_btn": "Passer au Mode Normal",
        "avant_ram": "Il reste {} jours avant le Ramadan", "pendant_ram": "Il reste {} jours avant la fin",
        "exp_maj": "📝 Mise à jour", "exp_prec": "🔄 Date précise", "btn_recalc": "⚙️ Recalculer"
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
st.markdown(f"<style>h1,h2,h3,p,label{{color:{COLOR}!important;}} div.stButton>button{{border:2px solid {COLOR}!important; color:{COLOR}!important; font-weight:bold; width:100%;}} div.stButton>button:hover{{background-color:{COLOR}!important; color:white!important;}}</style>", unsafe_allow_html=True)

# --- 6. AUTHENTIFICATION ---
if not st.session_state["auth"]:
    if st.session_state["view"] == "login":
        st.title(L["acces"])
        u_in = st.text_input(L["user_label"])
        p_in = st.text_input(L["code_label"], type="password")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(L["btn_unlock"]):
                match = df_users[(df_users["pseudo"] == u_in) & (df_users["password"] == p_in)]
                if not match.empty:
                    st.session_state["auth"] = True
                    st.session_state["user_connected"] = u_in
                    st.session_state["is_admin"] = (match.iloc[0]["role"] == "Admin")
                    st.rerun()
                else: st.error("Erreur d'identifiants.")
        with c2: 
            if st.button(L["btn_signup"]): st.session_state["view"] = "signup"; st.rerun()
        with c3:
            if st.button(L["btn_forgot"]):
                if u_in:
                    df_f = pd.read_csv(FORGOT_FILE)
                    if u_in not in df_f["pseudo"].values:
                        pd.concat([df_f, pd.DataFrame([[u_in]], columns=["pseudo"])], ignore_index=True).to_csv(FORGOT_FILE, index=False)
                    st.success("Yael a été prévenu.")
                else: st.warning("Pseudo requis.")
    elif st.session_state["view"] == "signup":
        st.title("📝 Inscription")
        nu, np, ncp = st.text_input("Pseudo"), st.text_input("Pass", type="password"), st.text_input("Confirme", type="password")
        if st.button("S'inscrire"):
            if np != ncp: st.error("Mots de passe différents.")
            elif nu in df_users["pseudo"].values: st.error("Pseudo déjà pris.")
            else:
                df_d = pd.read_csv(DEMANDES_FILE)
                pd.concat([df_d, pd.DataFrame([[nu, np]], columns=["pseudo", "password"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
                st.success("Demande envoyée !"); st.session_state["view"] = "login"
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.header(f"👤 {st.session_state['user_connected']}")
    if st.button(L["home_btn"]): st.session_state["page_params"] = False; st.rerun()
    if st.button(L["params"]): st.session_state["page_params"] = "settings"; st.rerun()
    if st.session_state["is_admin"]:
        nb_n = len(pd.read_csv(DEMANDES_FILE)) + len(pd.read_csv(FORGOT_FILE))
        if st.button(f"{L['notif']} ({nb_n})"): st.session_state["page_params"] = "notif"; st.rerun()
    st.divider()
    btn_m = L["mode_norm_btn"] if st.session_state["ramadan_mode"] else L["mode_ram_btn"]
    if st.button(btn_m):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]
        st.rerun()
    if st.button(L["btn_logout"]): st.session_state["auth"] = False; st.rerun()

# --- 8. PAGES SPECIALES ---
if st.session_state["page_params"] == "notif" and st.session_state["is_admin"]:
    st.title("🔔 Notifications Admin")
    df_d = pd.read_csv(DEMANDES_FILE)
    for i, r in df_d.iterrows():
        c1, c2 = st.columns([3,1])
        c1.write(f"**{r['pseudo']}** veut s'inscrire.")
        if c2.button("OK", key=f"a_{i}"):
            new_u = pd.DataFrame([[r['pseudo'], r['password'], "Membre"]], columns=["pseudo", "password", "role"])
            pd.concat([pd.read_csv(USERS_FILE), new_u], ignore_index=True).to_csv(USERS_FILE, index=False)
            df.loc[r['pseudo']] = [1, 10, 0, 1]; df.to_csv(DATA_FILE)
            df_d.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()
    
    st.divider()
    df_f = pd.read_csv(FORGOT_FILE)
    for i, r in df_f.iterrows():
        c1, c2 = st.columns([2,2])
        c1.write(f"Mdp oublié : **{r['pseudo']}**")
        pw = c2.text_input("Nouveau MDP", key=f"f_{i}")
        if c2.button("Changer", key=f"fb_{i}"):
            u_db = pd.read_csv(USERS_FILE)
            u_db.loc[u_db["pseudo"] == r['pseudo'], "password"] = pw
            u_db.to_csv(USERS_FILE, index=False)
            df_f.drop(i).to_csv(FORGOT_FILE, index=False); st.rerun()
    st.stop()

if st.session_state["page_params"] == "settings":
    st.title("⚙️ Paramètres")
    if st.session_state["is_admin"]:
        st.subheader("Dates Ramadan")
        deb = st.date_input("Début", st.session_state["debut_ramadan"])
        fin = st.date_input("Fin", st.session_state["fin_ramadan"])
        if st.button("Enregistrer les dates"):
            pd.DataFrame({"debut": [deb.isoformat()], "fin": [fin.isoformat()]}).to_csv(CONFIG_FILE, index=False)
            st.success("Dates enregistrées.")
    else: st.info("Réservé à Yael.")
    st.stop()

# --- 9. ACCUEIL ---
st.title(L["titre_ram"] if st.session_state["ramadan_mode"] else L["titre_norm"])
auj = date.today()

# Compte à rebours
if st.session_state["ramadan_mode"]:
    if auj < st.session_state["debut_ramadan"]:
        st.info(L["avant_ram"].format((st.session_state["debut_ramadan"] - auj).days))
    elif auj <= st.session_state["fin_ramadan"]:
        st.success(L["pendant_ram"].format((st.session_state["fin_ramadan"] - auj).days))

# Filtrage admin/membre
view_df = df if st.session_state["is_admin"] else df[df.index == st.session_state["user_connected"]]

if not view_df.empty:
    recap = view_df.copy()
    total_pg = 604
    if st.session_state["ramadan_mode"]:
        recap[L["col_prog"]] = (((recap["Page Actuelle"] + (recap["Cycles Finis"] * total_pg)) / (recap["Objectif Khatmas"] * total_pg)) * 100).round(1).astype(str) + "%"
    else:
        recap[L["col_prog"]] = (recap["Page Actuelle"] / total_pg * 100).round(1).astype(str) + "%"
    st.table(recap)

    # Actions
    st.divider()
    c_maj, c_prec = st.columns(2)
    
    with c_maj:
        with st.expander(L["exp_maj"], expanded=True):
            u_maj = st.selectbox("Choisir profil", view_df.index)
            p_n = st.number_input("Page Actuelle", 1, 604, int(df.loc[u_maj, "Page Actuelle"]))
            
            if st.session_state["ramadan_mode"]:
                obj_k = st.number_input("Objectif Khatmas", 1, 10, int(df.loc[u_maj, "Objectif Khatmas"]))
                cyc_f = st.number_input("Khatmas finies", 0, 10, int(df.loc[u_maj, "Cycles Finis"]))
                if st.button(L["btn_save"], key="save_ram"):
                    jours_restants = max(1, (st.session_state["fin_ramadan"] - auj).days)
                    pages_totales = (obj_k * total_pg) - (p_n + (cyc_f * total_pg))
                    rythme = max(1, round(pages_totales / jours_restants, 1))
                    df.loc[u_maj] = [p_n, rythme, cyc_f, obj_k]
                    df.to_csv(DATA_FILE); st.rerun()
            else:
                rythme_n = st.number_input("Rythme (p/jour)", 1, 100, int(df.loc[u_maj, "Rythme"]))
                if st.button(L["btn_save"], key="save_norm"):
                    df.loc[u_maj, ["Page Actuelle", "Rythme"]] = [p_n, rythme_n]
                    df.to_csv(DATA_FILE); st.rerun()

    with c_prec:
        with st.expander(L["exp_prec"]):
            u_adj = st.selectbox("Profil à ajuster", view_df.index, key="adj_u")
            d_adj = st.date_input("Date du relevé", auj)
            p_adj = st.number_input("Page à cette date", 1, 604)
            if st.button(L["btn_recalc"]):
                diff = (auj - d_adj).days
                nouvelle_page = (p_adj + (int(df.loc[u_adj, "Rythme"]) * diff)) % 604 or 1
                df.loc[u_adj, "Page Actuelle"] = int(nouvelle_page)
                df.to_csv(DATA_FILE); st.rerun()

    # Planning
    st.divider()
    st.subheader("📅 Planning (7 prochains jours)")
    planning = pd.DataFrame(index=[(auj + timedelta(days=i)).strftime("%d/%m") for i in range(7)])
    for n, r in view_df.iterrows():
        planning[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 1) for i in range(7)]
    st.dataframe(planning, use_container_width=True)
else:
    st.warning("Aucune donnée disponible. Contacte Yael.")
