import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random

# --- 1. CONFIGURATION ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if "user_connected" not in st.session_state: st.session_state["user_connected"] = None
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "ramadan_mode" not in st.session_state: st.session_state["ramadan_mode"] = False
if "langue" not in st.session_state: st.session_state["langue"] = "Français"
if "page" not in st.session_state: st.session_state["page"] = "home"
if "view" not in st.session_state: st.session_state["view"] = "login"

# --- 2. FICHIERS ---
dossier = os.path.dirname(__file__)
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv")
FORGOT_FILE = os.path.join(dossier, "forgot.csv")

def init_file(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["pseudo", "password", "role"])
init_file(DEMANDES_FILE, ["pseudo", "password"])
init_file(FORGOT_FILE, ["pseudo"])

# Admin Yael
udb = pd.read_csv(USERS_FILE)
if "Yael" not in udb["pseudo"].values:
    pd.concat([udb, pd.DataFrame([["Yael", "Yassine05", "Admin"]], columns=["pseudo", "password", "role"])], ignore_index=True).to_csv(USERS_FILE, index=False)

def charger_data():
    suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
    file = os.path.join(dossier, f"sauvegarde_{suffixe}.csv")
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        df = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df.index.name = "Nom"
        df.to_csv(file)
        return df
    return pd.read_csv(file, index_col=0)

# --- 3. STYLE ET TRADUCTION ---
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"
st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"""
    <style>
    h1, h2, h3, label, p {{ color: {COLOR} !important; }}
    div.stButton > button {{ width: 100%; border-radius: 10px; border: 2px solid {COLOR}; color: {COLOR}; font-weight: bold; height: 3em; }}
    div.stButton > button:hover {{ background-color: {COLOR}; color: white; }}
    .stTable {{ font-size: 0.85rem !important; }}
    .stProgress > div > div > div > div {{ background-color: {COLOR} !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTIFICATION ---
if not st.session_state["auth"]:
    st.title("🔐 Accès Bilan")
    if st.session_state["view"] == "login":
        u = st.text_input("Pseudo")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Déverrouiller"):
            db = pd.read_csv(USERS_FILE)
            match = db[(db["pseudo"] == u) & (db["password"].astype(str) == p)]
            if not match.empty:
                st.session_state["auth"], st.session_state["user_connected"] = True, u
                st.session_state["is_admin"] = (match.iloc[0]["role"] == "Admin")
                st.rerun()
            else: st.error("Accès refusé")
        if st.button("Créer un compte"): st.session_state["view"] = "signup"; st.rerun()
    elif st.session_state["view"] == "signup":
        nu = st.text_input("Pseudo choisi")
        np = st.text_input("Mdp choisi", type="password")
        if st.button("Envoyer Demande"):
            ddb = pd.read_csv(DEMANDES_FILE)
            pd.concat([ddb, pd.DataFrame([[nu, np]], columns=["pseudo", "password"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
            st.success("Demande transmise !"); st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 5. LOGIQUE PRINCIPALE ---
df = charger_data()
auj = date.today()

# Barre latérale
with st.sidebar:
    st.title(f"👤 {st.session_state['user_connected']}")
    if st.button("🏠 Accueil"): st.session_state["page"] = "home"; st.rerun()
    if st.session_state["is_admin"]:
        nb = len(pd.read_csv(DEMANDES_FILE))
        if st.button(f"🔔 Demandes ({nb})"): st.session_state["page"] = "admin"; st.rerun()
    st.divider()
    btn_label = "📖 Mode Normal" if st.session_state["ramadan_mode"] else "🌙 Mode Ramadan"
    if st.button(btn_label):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]; st.rerun()
    if st.button("🔒 Déconnexion"):
        st.session_state["auth"] = False; st.rerun()

# --- PAGE ADMIN ---
if st.session_state["page"] == "admin":
    st.title("Gestion des inscriptions")
    ddb = pd.read_csv(DEMANDES_FILE)
    for i, r in ddb.iterrows():
        c1, c2 = st.columns([3,1])
        c1.write(f"Valider **{r['pseudo']}** ?")
        if c2.button("✅", key=f"ok_{i}"):
            udb = pd.read_csv(USERS_FILE)
            pd.concat([udb, pd.DataFrame([[r['pseudo'], r['password'], "Membre"]], columns=["pseudo", "password", "role"])], ignore_index=True).to_csv(USERS_FILE, index=False)
            # Ajout auto dans les data
            for m in ["lecture", "ramadan"]:
                f = os.path.join(dossier, f"sauvegarde_{m}.csv")
                temp = pd.read_csv(f, index_col=0) if os.path.exists(f) else pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"], index=["Nom"])
                temp.loc[r['pseudo']] = [1, 10, 0, 1]
                temp.to_csv(f)
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()
    st.stop()

# --- PAGE ACCUEIL (STRUCTURE 3.1) ---
st.title("🌙 Bilan Ramadan" if st.session_state["ramadan_mode"] else "📖 Bilan Lecture")

# 1. TABLEAU ÉTAT ACTUEL (En haut comme en 3.1)
st.subheader("📊 État actuel")
if not df.empty:
    recap = df.copy()
    if st.session_state["ramadan_mode"]:
        recap["Progression"] = (((recap["Page Actuelle"] + (recap["Cycles Finis"] * 604)) / (recap["Objectif Khatmas"] * 604)) * 100).round(1).astype(str) + "%"
    else:
        recap["Progression"] = (recap["Page Actuelle"] / 604 * 100).round(1).astype(str) + "%"
    st.table(recap)

    # 2. PROGRESSION VISUELLE
    with st.expander("📊 Progression Visuelle", expanded=False):
        for n, r in df.iterrows():
            total = r["Objectif Khatmas"] * 604 if st.session_state["ramadan_mode"] else 604
            fait = (r["Page Actuelle"] + (r["Cycles Finis"] * 604)) if st.session_state["ramadan_mode"] else r["Page Actuelle"]
            st.write(f"**{n}**")
            st.progress(min(1.0, fait/total))

    st.divider()

    # 3. OUTILS (COLONNES)
    c1, c2, c3 = st.columns(3)
    
    with c1: # WhatsApp
        with st.expander("💬 WhatsApp"):
            dc = st.date_input("Pour le :", auj + timedelta(days=1))
            diff = (dc - auj).days
            msg = f"*Bilan {dc.strftime('%d/%m')}* :\n"
            for n, r in df.iterrows():
                p = (int(r["Page Actuelle"]) + (int(r["Rythme"]) * diff)) % 604 or 1
                msg += f"• *{n.upper()}* : p.{int(p)}\n"
            st.text_area("Copier :", msg, height=120)

    with c2: # Mise à jour
        with st.expander("📝 Mise à jour"):
            u_name = st.selectbox("Qui ?", df.index)
            new_p = st.number_input("Page :", 1, 604, int(df.loc[u_name, "Page Actuelle"]))
            if st.session_state["ramadan_mode"]:
                new_ok = st.number_input("Objectif :", 1, 10, int(df.loc[u_name, "Objectif Khatmas"]))
                new_cf = st.number_input("Finies :", 0, 10, int(df.loc[u_name, "Cycles Finis"]))
                if st.button("Enregistrer"):
                    # Recalcul du rythme auto en mode Ramadan
                    j_rest = 30 # Moyenne si date non fixée
                    new_ry = max(1, round(((new_ok * 604) - (new_p + (new_cf * 604))) / j_rest, 1))
                    df.loc[u_name] = [new_p, new_ry, new_cf, new_ok]
                    df.to_csv(os.path.join(dossier, f"sauvegarde_ramadan.csv")); st.rerun()
            else:
                new_ry = st.number_input("Rythme :", 1, 100, int(df.loc[u_name, "Rythme"]))
                if st.button("Enregistrer "):
                    df.loc[u_name, ["Page Actuelle", "Rythme"]] = [new_p, new_ry]
                    df.to_csv(os.path.join(dossier, f"sauvegarde_lecture.csv")); st.rerun()

    with c3: # Date précise
        with st.expander("🔄 Date précise"):
            dp = st.date_input("Vérifier le :", auj)
            p_prec = st.number_input("Page à cette date :", 1, 604)
            if st.button("Recalculer"):
                diff_d = (auj - dp).days
                nouvelle_p = (p_prec + (int(df.loc[st.session_state["user_connected"], "Rythme"]) * diff_d)) % 604 or 1
                df.loc[st.session_state["user_connected"], "Page Actuelle"] = int(nouvelle_p)
                suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
                df.to_csv(os.path.join(dossier, f"sauvegarde_{suffixe}.csv")); st.rerun()

    # 4. PLANNING
    st.subheader("📅 Planning 30 jours")
    plan_df = pd.DataFrame(index=[(auj + timedelta(days=i)).strftime("%d/%m") for i in range(30)])
    for n, r in df.iterrows():
        plan_df[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 1) for i in range(30)]
    st.dataframe(plan_df, use_container_width=True)

else:
    st.info("Aucune donnée disponible. Ajoutez un membre via l'Admin ou l'Inscription.")
