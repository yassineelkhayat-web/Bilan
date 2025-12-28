import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os

# --- 1. CONFIGURATION ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if "user_connected" not in st.session_state: st.session_state["user_connected"] = None
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "ramadan_mode" not in st.session_state: st.session_state["ramadan_mode"] = False
if "page" not in st.session_state: st.session_state["page"] = "home"
if "view" not in st.session_state: st.session_state["view"] = "login"

# --- 2. GESTION DES FICHIERS & SÉCURITÉ ADMIN ---
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

# --- BLOC DE SECOURS : CRÉATION AUTO DE YAEL ---
udb_check = pd.read_csv(USERS_FILE)
# On s'assure que Yael est présente et Admin
if "Yael" not in udb_check["pseudo"].values:
    yael_admin = pd.DataFrame([["Yael", "Yassine05", "Admin"]], columns=["pseudo", "password", "role"])
    udb_check = pd.concat([udb_check, yael_admin], ignore_index=True)
    udb_check.to_csv(USERS_FILE, index=False)
# -----------------------------------------------

def charger_data():
    suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
    file = os.path.join(dossier, f"sauvegarde_{suffixe}.csv")
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        df = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df.index.name = "Nom"
        df.to_csv(file)
        return df
    return pd.read_csv(file, index_col=0)

# --- 3. STYLE ---
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"
st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"<style>h1,h2,h3,p,label {{color:{COLOR}!important;}} div.stButton>button {{width:100%; border-radius:10px; border:2px solid {COLOR}; color:{COLOR}; font-weight:bold;}} div.stButton>button:hover {{background-color:{COLOR}; color:white;}} .stProgress > div > div > div > div {{background-color:{COLOR}!important;}}</style>", unsafe_allow_html=True)

# --- 4. AUTHENTIFICATION ---
if not st.session_state["auth"]:
    st.title("🔐 Accès")
    
    if st.session_state["view"] == "login":
        u = st.text_input("Pseudo")
        p = st.text_input("Mot de passe", type="password")
        
        if st.button("Se connecter"):
            db = pd.read_csv(USERS_FILE)
            # Vérification stricte (on convertit tout en texte pour éviter les bugs)
            match = db[(db["pseudo"].astype(str) == str(u)) & (db["password"].astype(str) == str(p))]
            
            if not match.empty:
                st.session_state["auth"] = True
                st.session_state["user_connected"] = str(u)
                st.session_state["is_admin"] = (match.iloc[0]["role"] == "Admin")
                st.rerun()
            else:
                st.error("Pseudo ou mot de passe incorrect.")
        
        c1, c2 = st.columns(2)
        if c1.button("Créer un compte"): st.session_state["view"] = "signup"; st.rerun()
        if c2.button("Mdp oublié ?"): st.session_state["view"] = "forgot"; st.rerun()

    elif st.session_state["view"] == "signup":
        nu = st.text_input("Pseudo choisi")
        np = st.text_input("Mdp choisi", type="password")
        if st.button("Envoyer Inscription"):
            if nu and np:
                ddb = pd.read_csv(DEMANDES_FILE)
                pd.concat([ddb, pd.DataFrame([[nu, np]], columns=["pseudo", "password"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
                st.success("Demande transmise !"); st.session_state["view"] = "login"; st.rerun()
            else: st.warning("Remplis tous les champs")
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()

    elif st.session_state["view"] == "forgot":
        fu = st.text_input("Pseudo pour la récupération")
        if st.button("Signaler à Yael"):
            if fu:
                fdb = pd.read_csv(FORGOT_FILE)
                if fu not in fdb["pseudo"].values:
                    pd.concat([fdb, pd.DataFrame([[fu]], columns=["pseudo"])], ignore_index=True).to_csv(FORGOT_FILE, index=False)
                st.success("Yael a été notifiée !"); st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 5. LOGIQUE PRINCIPALE ---
df = charger_data()
auj = date.today()

with st.sidebar:
    st.title(f"👤 {st.session_state['user_connected']}")
    if st.button("🏠 Accueil"): st.session_state["page"] = "home"; st.rerun()
    if st.session_state["is_admin"]:
        nb = len(pd.read_csv(DEMANDES_FILE)) + len(pd.read_csv(FORGOT_FILE))
        if st.button(f"🔔 Notifs ({nb})"): st.session_state["page"] = "admin"; st.rerun()
    st.divider()
    btn_txt = "📖 Mode Normal" if st.session_state["ramadan_mode"] else "🌙 Mode Ramadan"
    if st.button(btn_txt):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]; st.rerun()
    if st.button("🔒 Déconnexion"):
        st.session_state["auth"] = False; st.rerun()

# --- PAGE ADMIN ---
if st.session_state["page"] == "admin":
    st.title("🔔 Notifications")
    
    # Inscriptions
    st.subheader("📝 Inscriptions")
    ddb = pd.read_csv(DEMANDES_FILE)
    for i, r in ddb.iterrows():
        c1, c2, c3 = st.columns([2,1,1])
        c1.write(f"**{r['pseudo']}**")
        if c2.button("✅", key=f"acc_{i}"):
            udb = pd.read_csv(USERS_FILE)
            pd.concat([udb, pd.DataFrame([[r['pseudo'], r['password'], "Membre"]], columns=["pseudo", "password", "role"])], ignore_index=True).to_csv(USERS_FILE, index=False)
            for m in ["lecture", "ramadan"]:
                f = os.path.join(dossier, f"sauvegarde_{m}.csv")
                temp = pd.read_csv(f, index_col=0) if os.path.exists(f) else pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"], index=["Nom"])
                temp.loc[r['pseudo']] = [1, 10, 0, 1]
                temp.to_csv(f)
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()
        if c3.button("❌", key=f"ref_{i}"):
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()

    # Mdp oubliés
    st.subheader("🔑 Mots de passe oubliés")
    fdb = pd.read_csv(FORGOT_FILE)
    udb = pd.read_csv(USERS_FILE)
    for i, r in fdb.iterrows():
        user_info = udb[udb["pseudo"] == r["pseudo"]]
        ancien = user_info.iloc[0]["password"] if not user_info.empty else "Inconnu"
        st.info(f"User : {r['pseudo']} | Ancien : `{ancien}`")
        nv_mdp = st.text_input("Nouveau password :", key=f"p_{i}")
        if st.button("Changer & Effacer", key=f"b_{i}"):
            udb.loc[udb["pseudo"] == r["pseudo"], "password"] = nv_mdp
            udb.to_csv(USERS_FILE, index=False)
            fdb.drop(i).to_csv(FORGOT_FILE, index=False); st.rerun()
    st.stop()

# --- PAGE ACCUEIL ---
st.title("🌙 Bilan Coran" if st.session_state["ramadan_mode"] else "📖 Bilan Coran")
st.subheader("📊 État actuel")

if not df.empty:
    st.table(df)

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.expander("💬 WhatsApp"):
            dc = st.date_input("Echéance", auj + timedelta(days=1))
            msg = f"*Bilan {dc.strftime('%d/%m')}* :\n"
            for n, r in df.iterrows():
                p = (int(r["Page Actuelle"]) + (int(r["Rythme"]) * (dc - auj).days)) % 604 or 1
                msg += f"• *{n.upper()}* : p.{int(p)}\n"
            st.text_area("Copier :", msg)
    with c2:
        with st.expander("📝 Mise à jour"):
            u_sel = st.selectbox("Qui ?", df.index)
            np = st.number_input("Page", 1, 604, int(df.loc[u_sel, "Page Actuelle"]))
            nr = st.number_input("Rythme", 1, 100, int(df.loc[u_sel, "Rythme"]))
            if st.button("Sauvegarder"):
                df.loc[u_sel, ["Page Actuelle", "Rythme"]] = [np, nr]
                suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
                df.to_csv(os.path.join(dossier, f"sauvegarde_{suffixe}.csv")); st.rerun()
    with c3:
        with st.expander("🔄 Calcul Date"):
            dp = st.date_input("Vérifier date :", auj)
            p_prec = st.number_input("Page à cette date", 1, 604)
            if st.button("Calculer"):
                diff = (auj - dp).days
                nouvelle = (p_prec + (int(df.loc[st.session_state["user_connected"], "Rythme"]) * diff)) % 604 or 1
                df.loc[st.session_state["user_connected"], "Page Actuelle"] = int(nouvelle)
                suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
                df.to_csv(os.path.join(dossier, f"sauvegarde_{suffixe}.csv")); st.rerun()

    st.subheader("📅 Planning 30 jours")
    plan_df = pd.DataFrame(index=[(auj + timedelta(days=i)).strftime("%d/%m") for i in range(30)])
    for n, r in df.iterrows():
        plan_df[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 1) for i in range(30)]
    st.dataframe(plan_df, use_container_width=True)
