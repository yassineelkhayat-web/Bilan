import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random

# --- 1. CONFIGURATION & SÉCURITÉ ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if "user_connected" not in st.session_state: st.session_state["user_connected"] = None
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "ramadan_mode" not in st.session_state: st.session_state["ramadan_mode"] = False
if "langue" not in st.session_state: st.session_state["langue"] = "Français"
if "page" not in st.session_state: st.session_state["page"] = "home"
if "view" not in st.session_state: st.session_state["view"] = "login"

# --- 2. GESTION DES FICHIERS ---
dossier = os.path.dirname(__file__)
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv")
FORGOT_FILE = os.path.join(dossier, "forgot.csv")
CONFIG_FILE = os.path.join(dossier, "config_dates.csv")

def init_file(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["pseudo", "password", "role"])
init_file(DEMANDES_FILE, ["pseudo", "password"])
init_file(FORGOT_FILE, ["pseudo"])

# Admin par défaut
udb_init = pd.read_csv(USERS_FILE)
if "Yael" not in udb_init["pseudo"].values:
    admin_row = pd.DataFrame([["Yael", "Yassine05", "Admin"]], columns=["pseudo", "password", "role"])
    pd.concat([udb_init, admin_row], ignore_index=True).to_csv(USERS_FILE, index=False)

# Dates Ramadan
if os.path.exists(CONFIG_FILE):
    conf_df = pd.read_csv(CONFIG_FILE)
    st.session_state["debut_ramadan"] = date.fromisoformat(conf_df.iloc[0]["debut"])
    st.session_state["fin_ramadan"] = date.fromisoformat(conf_df.iloc[0]["fin"])
else:
    st.session_state["debut_ramadan"], st.session_state["fin_ramadan"] = date(2025, 3, 1), date(2025, 3, 30)

def charger_data():
    suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
    file = os.path.join(dossier, f"sauvegarde_{suffixe}.csv")
    if not os.path.exists(file):
        df = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df.index.name = "Nom"
        df.to_csv(file)
    return pd.read_csv(file, index_col=0)

# --- 3. STYLE RESPONSIVE ---
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"
st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"""
    <style>
    div.stButton>button {{ width: 100%; border-radius: 10px; border: 2px solid {COLOR}; color: {COLOR}; font-weight: bold; }}
    div.stButton>button:hover {{ background-color: {COLOR}; color: white; }}
    .stProgress > div > div > div > div {{ background-color: {COLOR} !important; }}
    h1, h2, h3 {{ color: {COLOR} !important; text-align: center; }}
    .stTable {{ font-size: 0.9rem !important; }}
    </style>
""", unsafe_allow_html=True)

df = charger_data()

# --- 4. AUTHENTIFICATION ---
if not st.session_state["auth"]:
    st.title("🔐 Accès")
    if st.session_state["view"] == "login":
        u_in = st.text_input("Pseudo")
        p_in = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            udb = pd.read_csv(USERS_FILE)
            match = udb[(udb["pseudo"] == u_in) & (udb["password"].astype(str) == p_in)]
            if not match.empty:
                st.session_state["auth"] = True
                st.session_state["user_connected"] = u_in
                st.session_state["is_admin"] = (match.iloc[0]["role"] == "Admin")
                st.rerun()
            else: st.error("Identifiants incorrects")
        if st.button("S'inscrire"): st.session_state["view"] = "signup"; st.rerun()
    
    elif st.session_state["view"] == "signup":
        nu = st.text_input("Nouveau Pseudo")
        np = st.text_input("Nouveau Mdp", type="password")
        if st.button("Envoyer la demande"):
            ddb = pd.read_csv(DEMANDES_FILE)
            pd.concat([ddb, pd.DataFrame([[nu, np]], columns=["pseudo", "password"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
            st.success("Demande envoyée à Yael !"); st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 5. NAVIGATION ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['user_connected']}")
    if st.button("🏠 Accueil"): st.session_state["page"] = "home"; st.rerun()
    if st.button("📊 Progression Visuelle"): st.session_state["page"] = "viz"; st.rerun()
    if st.session_state["is_admin"]:
        nb = len(pd.read_csv(DEMANDES_FILE)) + len(pd.read_csv(FORGOT_FILE))
        if st.button(f"🔔 Notifications ({nb})"): st.session_state["page"] = "admin"; st.rerun()
    st.divider()
    if st.button("🌙 Mode Ramadan" if not st.session_state["ramadan_mode"] else "📖 Mode Normal"):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]; st.rerun()
    if st.button("🚪 Déconnexion"): st.session_state["auth"] = False; st.rerun()

# --- 6. PAGE ACCUEIL ---
if st.session_state["page"] == "home":
    st.title("📖 Mon Bilan Coran")
    auj = date.today()
    
    # Compte à rebours
    if st.session_state["ramadan_mode"]:
        diff = (st.session_state["debut_ramadan"] - auj).days
        if diff > 0: st.info(f"⏳ J-{diff} avant Ramadan")
    
    # Données utilisateur
    u = st.session_state["user_connected"]
    if u in df.index:
        r = df.loc[u]
        
        # 1. Barre de progression visuelle (Remise)
        if st.session_state["ramadan_mode"]:
            total_pages = r["Objectif Khatmas"] * 604
            pages_faites = r["Page Actuelle"] + (r["Cycles Finis"] * 604)
            prog = min(1.0, pages_faites / total_pages)
            st.write(f"**Progression globale : {round(prog*100, 1)}%**")
            st.progress(prog)
        else:
            prog = min(1.0, r["Page Actuelle"] / 604)
            st.write(f"**Progression Khatma : {round(prog*100, 1)}%**")
            st.progress(prog)

        # 2. Mise à jour
        with st.expander("📝 Mettre à jour mon avancée", expanded=True):
            c1, c2 = st.columns(2)
            new_p = c1.number_input("Page Actuelle", 1, 604, int(r["Page Actuelle"]))
            if st.session_state["ramadan_mode"]:
                new_k = c2.number_input("Objectif Khatmas", 1, 10, int(r["Objectif Khatmas"]))
                new_c = c1.number_input("Khatmas Terminées", 0, 10, int(r["Cycles Finis"]))
                if st.button("Sauvegarder"):
                    j_rest = max(1, (st.session_state["fin_ramadan"] - auj).days)
                    new_r = max(1, round(((new_k * 604) - (new_p + (new_c * 604))) / j_rest, 1))
                    df.loc[u] = [new_p, new_r, new_c, new_k]
                    df.to_csv(os.path.join(dossier, f"sauvegarde_ramadan.csv"))
                    st.success("Mis à jour !"); st.rerun()
            else:
                new_ry = c2.number_input("Rythme (pages/jour)", 1, 100, int(r["Rythme"]))
                if st.button("Sauvegarder"):
                    df.loc[u, ["Page Actuelle", "Rythme"]] = [new_p, new_ry]
                    df.to_csv(os.path.join(dossier, f"sauvegarde_lecture.csv"))
                    st.success("Mis à jour !")

        # 3. Calcul précis (Remis)
        with st.expander("🔄 Calculer pour une date précise"):
            target_date = st.date_input("Choisir une date", auj + timedelta(days=7))
            jours = (target_date - auj).days
            page_future = (r["Page Actuelle"] + (r["Rythme"] * jours)) % 604 or 1
            st.metric(f"Le {target_date.strftime('%d/%m')}", f"Page {int(page_future)}")

        # 4. Planning 30 jours
        st.subheader("📅 Planning prévisionnel")
        plan = pd.DataFrame({
            "Date": [(auj + timedelta(days=i)).strftime("%d/%m") for i in range(30)],
            "Page": [int((r["Page Actuelle"] + (r["Rythme"] * i)) % 604 or 1) for i in range(30)]
        })
        st.dataframe(plan, use_container_width=True, hide_index=True)

# --- 7. PAGE ADMIN ---
elif st.session_state["page"] == "admin":
    st.title("🔔 Gestion des demandes")
    ddb = pd.read_csv(DEMANDES_FILE)
    if not ddb.empty:
        for i, r in ddb.iterrows():
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{r['pseudo']}** veut s'inscrire")
            if col2.button("✅", key=f"ok_{i}"):
                new_u = pd.DataFrame([[r['pseudo'], r['password'], "Membre"]], columns=["pseudo", "password", "role"])
                pd.concat([pd.read_csv(USERS_FILE), new_u], ignore_index=True).to_csv(USERS_FILE, index=False)
                # Création profil data
                suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
                temp_df = charger_data()
                temp_df.loc[r['pseudo']] = [1, 10, 0, 1]
                temp_df.to_csv(os.path.join(dossier, f"sauvegarde_{suffixe}.csv"))
                ddb.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()
    else: st.write("Aucune demande en attente.")

# --- 8. PAGE VISUELLE (TOUT LE MONDE) ---
elif st.session_state["page"] == "viz":
    st.title("📊 État des troupes")
    all_data = charger_data()
    for name, row in all_data.iterrows():
        st.write(f"**{name}** (Page {int(row['Page Actuelle'])})")
        val = min(1.0, row["Page Actuelle"] / 604)
        st.progress(val)
