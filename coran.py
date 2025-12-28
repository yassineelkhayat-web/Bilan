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

# --- 2. GESTION DES FICHIERS ---
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

# Sécurité Admin
udb_check = pd.read_csv(USERS_FILE)
if "Yael" not in udb_check["pseudo"].values:
    pd.concat([udb_check, pd.DataFrame([["Yael", "Yassine05", "Admin"]], columns=["pseudo", "password", "role"])], ignore_index=True).to_csv(USERS_FILE, index=False)

def charger_data():
    suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
    file = os.path.join(dossier, f"sauvegarde_{suffixe}.csv")
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        df = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df.index.name = "Nom"
        df.to_csv(file)
        return df
    return pd.read_csv(file, index_col=0)

# --- 3. TRADUCTIONS ---
TRAD = {
    "Français": {
        "titre": "📖 Bilan Coran", "etat": "📊 État actuel", "prog": "📊 Progression Visuelle",
        "maj": "📝 Mise à jour", "calc": "🔄 Calcul Date", "plan": "📅 Planning 30 jours",
        "lang": "🌐 Langue", "logout": "🔒 Déconnexion", "admin": "🔔 Notifs", "params": "⚙️ Paramètres"
    },
    "العربية": {
        "titre": "📖 حصيلة القرآن", "etat": "📊 الحالة الراهنة", "prog": "📊 التقدم البصري",
        "maj": "📝 تحديث", "calc": "🔄 حساب التاريخ", "plan": "📅 جدول 30 يوم",
        "lang": "🌐 اللغة", "logout": "🔒 خروج", "admin": "🔔 تنبيهات", "params": "⚙️ الإعدادات"
    }
}
L = TRAD[st.session_state["langue"]]

# --- 4. STYLE ---
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"
st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"<style>h1,h2,h3,p,label,span {{color:{COLOR}!important;}} div.stButton>button {{width:100%; border-radius:10px; border:2px solid {COLOR}; color:{COLOR}; font-weight:bold;}} div.stButton>button:hover {{background-color:{COLOR}; color:white;}} .stProgress > div > div > div > div {{background-color:{COLOR}!important;}}</style>", unsafe_allow_html=True)

# --- 5. AUTHENTIFICATION ---
if not st.session_state["auth"]:
    st.title("🔐 Accès")
    if st.session_state["view"] == "login":
        u = st.text_input("Pseudo")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            db = pd.read_csv(USERS_FILE)
            match = db[(db["pseudo"].astype(str) == str(u)) & (db["password"].astype(str) == str(p))]
            if not match.empty:
                st.session_state["auth"], st.session_state["user_connected"] = True, str(u)
                st.session_state["is_admin"] = (match.iloc[0]["role"] == "Admin")
                st.rerun()
            else: st.error("Erreur")
        c1, c2 = st.columns(2)
        if c1.button("S'inscrire"): st.session_state["view"] = "signup"; st.rerun()
        if c2.button("Mdp oublié ?"): st.session_state["view"] = "forgot"; st.rerun()
    # (Pages Signup et Forgot ici...)
    st.stop()

# --- 6. LOGIQUE ---
df_complet = charger_data()
auj = date.today()
df_view = df_complet if st.session_state["is_admin"] else df_complet[df_complet.index == st.session_state["user_connected"]]

with st.sidebar:
    st.title(f"👤 {st.session_state['user_connected']}")
    if st.button("🏠 Accueil"): st.session_state["page"] = "home"; st.rerun()
    if st.button(L["params"]): st.session_state["page"] = "params"; st.rerun()
    if st.session_state["is_admin"]:
        nb = len(pd.read_csv(DEMANDES_FILE)) + len(pd.read_csv(FORGOT_FILE))
        if st.button(f"{L['admin']} ({nb})"): st.session_state["page"] = "admin"; st.rerun()
    st.divider()
    if st.button("🌙 Mode Ramadan" if not st.session_state["ramadan_mode"] else "📖 Mode Normal"):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]; st.rerun()
    if st.button(L["logout"]): st.session_state["auth"] = False; st.rerun()

# --- PAGE PARAMÈTRES ---
if st.session_state["page"] == "params":
    st.title(L["params"])
    new_lang = st.selectbox(L["lang"], ["Français", "العربية"], index=0 if st.session_state["langue"]=="Français" else 1)
    if new_lang != st.session_state["langue"]: st.session_state["langue"] = new_lang; st.rerun()
    if st.session_state["is_admin"]:
        if st.button("🗑️ Supprimer un membre"):
            cible = st.selectbox("Qui supprimer ?", df_complet.index)
            df_complet.drop(cible).to_csv(os.path.join(dossier, f"sauvegarde_{'ramadan' if st.session_state['ramadan_mode'] else 'lecture'}.csv"))
            st.rerun()
    st.stop()

# --- PAGE ACCUEIL ---
st.title(L["titre"])

# Hadith Aléatoire
if st.button("✨ GÉNÉRER UN HADITH / حديث شريف"):
    h_file = "hadiths_fr.txt" if st.session_state["langue"] == "Français" else "hadiths_ar.txt"
    if os.path.exists(os.path.join(dossier, h_file)):
        with open(os.path.join(dossier, h_file), "r", encoding="utf-8") as f:
            lignes = f.readlines()
            if lignes: st.info(random.choice(lignes))

# 1. État Actuel
st.subheader(L["etat"])
st.table(df_view)

# 2. Progression Visuelle
with st.expander(L["prog"]):
    for n, r in df_view.iterrows():
        total = r["Objectif Khatmas"] * 604 if st.session_state["ramadan_mode"] else 604
        fait = (r["Page Actuelle"] + (r["Cycles Finis"] * 604)) if st.session_state["ramadan_mode"] else r["Page Actuelle"]
        st.write(f"**{n}**")
        st.progress(min(1.0, fait/total))

# 3. Outils
st.divider()
c1, c2, c3 = st.columns(3)
with c1:
    with st.expander("💬 WhatsApp"):
        dc = st.date_input("Echéance", auj + timedelta(days=1))
        msg = f"*Bilan {dc.strftime('%d/%m')}* :\n"
        for n, r in df_view.iterrows():
            p = (int(r["Page Actuelle"]) + (int(r["Rythme"]) * (dc - auj).days)) % 604 or 1
            msg += f"• *{n.upper()}* : p.{int(p)}\n"
        st.text_area("Copier :", msg)
with c2:
    with st.expander(L["maj"]):
        u_sel = st.selectbox("Qui ?", df_view.index)
        np = st.number_input("Page", 1, 604, int(df_view.loc[u_sel, "Page Actuelle"]))
        nr = st.number_input("Rythme", 1, 100, int(df_view.loc[u_sel, "Rythme"]))
        if st.button("Sauvegarder"):
            df_complet.loc[u_sel, ["Page Actuelle", "Rythme"]] = [np, nr]
            df_complet.to_csv(os.path.join(dossier, f"sauvegarde_{'ramadan' if st.session_state['ramadan_mode'] else 'lecture'}.csv")); st.rerun()
with c3:
    with st.expander(L["calc"]):
        dp = st.date_input("Vérifier date :", auj)
        p_prec = st.number_input("Page à cette date", 1, 604)
        if st.button("Calculer"):
            diff = (auj - dp).days
            rythme = int(df_view.loc[st.session_state['user_connected'], "Rythme"])
            nouvelle = (p_prec + (rythme * diff)) % 604 or 1
            df_complet.loc[st.session_state["user_connected"], "Page Actuelle"] = int(nouvelle)
            df_complet.to_csv(os.path.join(dossier, f"sauvegarde_{'ramadan' if st.session_state['ramadan_mode'] else 'lecture'}.csv")); st.rerun()

# 4. Planning
st.subheader(L["plan"])
plan_df = pd.DataFrame(index=[(auj + timedelta(days=i)).strftime("%d/%m") for i in range(30)])
for n, r in df_view.iterrows():
    plan_df[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 1) for i in range(30)]
st.dataframe(plan_df, use_container_width=True)
