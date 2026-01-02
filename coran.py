import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random
import requests

# --- 1. CONFIGURATION API ---
URL_FORMSPREE = "https://formspree.io/f/xaqnjwgv"
EMAILJS_SERVICE_ID = "service_v9ebnic" 
EMAILJS_TEMPLATE_ID = "template_rghkouc"
EMAILJS_PUBLIC_KEY = "LUCKx4YnQSQ3ncrue"
EMAILJS_PRIVATE_KEY = "xnNMOnkv8TSM6N_fK9TCR"

def envoyer_mail(pseudo, email_dest, message_contenu):
    url = "https://api.emailjs.com/api/v1.0/email/send"
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "accessToken": EMAILJS_PRIVATE_KEY,
        "template_params": {
            "to_name": pseudo,
            "user_email": email_dest,
            "message": message_contenu
        }
    }
    try: requests.post(url, json=payload)
    except: pass

# --- 2. GESTION DES FICHIERS & CODES ---
dossier = os.path.dirname(__file__)
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv")
CODES_FILE = os.path.join(dossier, "combinaisons.txt")

def init_file(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["pseudo", "password", "role", "user_email"])
init_file(DEMANDES_FILE, ["pseudo", "password", "user_email"])

# Génération des 1000 codes complexes
if not os.path.exists(CODES_FILE):
    with open(CODES_FILE, "w") as f:
        codes_gen = set()
        while len(codes_gen) < 1000:
            c = str(random.randint(100000, 999999))
            if len(set(c)) > 3: # Évite les codes trop simples comme 111222
                codes_gen.add(c)
        for c in codes_gen: f.write(c + "\n")

# Sécurité Admin Auto-Yael
udb_check = pd.read_csv(USERS_FILE)
if "Yael" not in udb_check["pseudo"].values:
    yael_row = pd.DataFrame([["Yael", "Yassine05", "Admin", "yassine.elkhayat@isv.be"]], 
                            columns=["pseudo", "password", "role", "user_email"])
    pd.concat([udb_check, yael_row], ignore_index=True).to_csv(USERS_FILE, index=False)

# --- 3. SESSION STATE ---
if "auth" not in st.session_state:
    st.session_state.update({
        "auth": False, "user_connected": None, "is_admin": False, 
        "ramadan_mode": False, "langue": "Français", "page": "home", 
        "view": "login", "reset_step": 1, "temp_email": "", "temp_code": ""
    })

def charger_data():
    suf = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
    f = os.path.join(dossier, f"sauvegarde_{suf}.csv")
    if not os.path.exists(f) or os.stat(f).st_size == 0:
        df = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df.index.name = "Nom"
        return df
    return pd.read_csv(f, index_col=0)

# --- 4. STYLE ---
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"
st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"<style>h1,h2,h3,p,label,span {{color:{COLOR}!important; text-align:center;}} div.stButton>button {{width:100%; border-radius:10px; border:2px solid {COLOR}; color:{COLOR}; font-weight:bold;}}</style>", unsafe_allow_html=True)

# --- 5. AUTHENTIFICATION & RÉCUPÉRATION ---
if not st.session_state["auth"]:
    st.title("🔐 Accès")
    
    if st.session_state["view"] == "login":
        u = st.text_input("Pseudo")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            db = pd.read_csv(USERS_FILE)
            match = db[(db["pseudo"].astype(str) == str(u)) & (db["password"].astype(str) == str(p))]
            if not match.empty:
                st.session_state.update({"auth": True, "user_connected": str(u), "is_admin": (match.iloc[0]["role"] == "Admin")})
                st.rerun()
            else: st.error("Identifiants incorrects.")
        c1, c2 = st.columns(2)
        if c1.button("S'inscrire"): st.session_state["view"] = "signup"; st.rerun()
        if c2.button("Mot de passe oublié ?"): st.session_state["view"] = "forgot"; st.session_state["reset_step"] = 1; st.rerun()

    elif st.session_state["view"] == "forgot":
        if st.session_state["reset_step"] == 1:
            fe = st.text_input("Email d'inscription")
            if st.button("Envoyer le code"):
                db = pd.read_csv(USERS_FILE)
                if fe in db["user_email"].values:
                    with open(CODES_FILE, "r") as f: codes = f.read().splitlines()
                    code = random.choice(codes)
                    st.session_state.update({"temp_code": code, "temp_email": fe, "reset_step": 2})
                    envoyer_mail(db[db["user_email"]==fe]["pseudo"].values[0], fe, f"Code de sécurité : {code}")
                    st.rerun()
                else: st.error("Email inconnu.")
        elif st.session_state["reset_step"] == 2:
            cs = st.text_input("Code reçu par mail")
            if st.button("Vérifier"):
                if cs == st.session_state["temp_code"]: st.session_state["reset_step"] = 3; st.rerun()
                else: st.error("Code erroné.")
        elif st.session_state["reset_step"] == 3:
            new_p = st.text_input("Nouveau mot de passe", type="password")
            if st.button("Mettre à jour"):
                db = pd.read_csv(USERS_FILE)
                db.loc[db["user_email"] == st.session_state["temp_email"], "password"] = new_p
                db.to_csv(USERS_FILE, index=False)
                st.success("Réussite ! Connecte-toi."); st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()

    elif st.session_state["view"] == "signup":
        nu, ne, np = st.text_input("Pseudo"), st.text_input("Email"), st.text_input("Mot de passe", type="password")
        if st.button("S'inscrire"):
            ddb = pd.read_csv(DEMANDES_FILE)
            pd.concat([ddb, pd.DataFrame([[nu, np, ne]], columns=["pseudo", "password", "user_email"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
            requests.post(URL_FORMSPREE, data={"User": nu, "Email": ne})
            st.success("Demande envoyée !"); st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 6. NAVIGATION ---
df_complet = charger_data()
auj = date.today()
df_view = df_complet if st.session_state["is_admin"] else df_complet[df_complet.index == st.session_state["user_connected"]]

with st.sidebar:
    st.title(f"👤 {st.session_state['user_connected']}")
    if st.button("🏠 Accueil"): st.session_state["page"] = "home"; st.rerun()
    if st.session_state["is_admin"] and st.button("🛠️ Admin"): st.session_state["page"] = "admin"; st.rerun()
    st.divider()
    if st.button("🌙/📖 Changer Mode"): st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]; st.rerun()
    if st.button("🔒 Quitter"): st.session_state["auth"] = False; st.rerun()

# --- 7. ADMINISTRATION ---
if st.session_state["page"] == "admin":
    st.title("🛠️ Administration")
    ddb = pd.read_csv(DEMANDES_FILE)
    st.subheader(f"⏳ Demandes ({len(ddb)})")
    for i, r in ddb.iterrows():
        c1, c2 = st.columns([3, 1])
        c1.write(f"**{r['pseudo']}**")
        if c2.button("✅", key=f"v_{i}"):
            udb = pd.read_csv(USERS_FILE)
            pd.concat([udb, pd.DataFrame([[r['pseudo'], r['password'], "Membre", r['user_email']]], columns=["pseudo", "password", "role", "user_email"])], ignore_index=True).to_csv(USERS_FILE, index=False)
            for m in ["lecture", "ramadan"]:
                path = os.path.join(dossier, f"sauvegarde_{m}.csv")
                tmp = pd.read_csv(path, index_col=0) if os.path.exists(path) else pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"], index=["Nom"])
                tmp.loc[r['pseudo']] = [1, 10, 0, 1]
                tmp.to_csv(path)
            envoyer_mail(r['pseudo'], r['user_email'], "Compte validé !")
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()

    st.divider()
    st.subheader("👥 Membres")
    udb = pd.read_csv(USERS_FILE)
    for i, r in udb.iterrows():
        if r['pseudo'] == "Yael": continue
        c1, c2, c3 = st.columns([2, 2, 1])
        c1.write(r['pseudo'])
        with c2: 
            if st.checkbox("👁️", key=f"e_{i}"): st.code(r['password'])
        if c3.button("🗑️", key=f"d_{i}"):
            udb.drop(i).to_csv(USERS_FILE, index=False)
            st.rerun()
    st.stop()

# --- 8. ACCUEIL ---
st.title("🌙 Ramadan" if st.session_state["ramadan_mode"] else "📖 Coran")
if not df_view.empty:
    st.table(df_view)
    with st.expander("📝 Mise à jour"):
        u_sel = st.selectbox("Qui ?", df_view.index)
        c1, c2 = st.columns(2)
        np = c1.number_input("Page", 1, 604, int(df_view.loc[u_sel, "Page Actuelle"]))
        nr = c2.number_input("Rythme", 1, 100, int(df_view.loc[u_sel, "Rythme"]))
        if st.button("💾"):
            df_complet.loc[u_sel, ["Page Actuelle", "Rythme"]] = [np, nr]
            df_complet.to_csv(os.path.join(dossier, f"sauvegarde_{'ramadan' if st.session_state['ramadan_mode'] else 'lecture'}.csv")); st.rerun()

    st.subheader("📅 Planning 30 jours")
    plan_df = pd.DataFrame(index=[(auj + timedelta(days=i)).strftime("%d/%m") for i in range(30)])
    for n, r in df_view.iterrows():
        plan_df[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 1) for i in range(30)]
    st.dataframe(plan_df, use_container_width=True)
