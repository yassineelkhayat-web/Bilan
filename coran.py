import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random
import requests

# --- 1. CONFIGURATION NOTIFICATIONS ---
URL_FORMSPREE = "https://formspree.io/f/xrebqybk"
EMAILJS_SERVICE_ID = "service_v9ebnic"  # Ton service Outlook
EMAILJS_TEMPLATE_ID = "template_rghkouc"
EMAILJS_PUBLIC_KEY = "LUCKx4YnQSQ3ncrue"

def envoyer_alerte_yael(pseudo, type_alerte="Inscription"):
    donnees = {"Objet": f"🔔 Bilan Coran : {type_alerte}", "Utilisateur": pseudo}
    try: requests.post(URL_FORMSPREE, data=donnees)
    except: pass

def envoyer_confirmation_utilisateur(pseudo, email_dest):
    url = "https://api.emailjs.com/api/v1.0/email/send"
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "template_params": {
            "to_name": pseudo,
            "user_email": email_dest, # Correspond à {{user_email}} dans EmailJS
            "message": "Ton compte Bilan Coran a été validé ! Tu peux maintenant te connecter."
        }
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.toast(f"✅ Mail envoyé à {pseudo} !", icon="📧")
        else:
            st.error(f"❌ Erreur EmailJS : {response.text}")
    except: pass

# --- 2. CONFIGURATION SESSION ---
for key, val in {
    "auth": False, "user_connected": None, "is_admin": False, 
    "ramadan_mode": False, "langue": "Français", "page": "home", "view": "login"
}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 3. GESTION DES FICHIERS ---
dossier = os.path.dirname(__file__)
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv")
FORGOT_FILE = os.path.join(dossier, "forgot.csv")

def init_file(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["pseudo", "password", "role", "user_email"])
init_file(DEMANDES_FILE, ["pseudo", "password", "user_email"])
init_file(FORGOT_FILE, ["pseudo"])

# Protection Admin Yael
udb_check = pd.read_csv(USERS_FILE)
if "Yael" not in udb_check["pseudo"].values:
    yael_row = pd.DataFrame([["Yael", "Yassine05", "Admin", "yassine.elkhayat@isv.be"]], columns=["pseudo", "password", "role", "user_email"])
    pd.concat([udb_check, yael_row], ignore_index=True).to_csv(USERS_FILE, index=False)

def charger_data():
    suf = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
    f = os.path.join(dossier, f"sauvegarde_{suf}.csv")
    if not os.path.exists(f) or os.stat(f).st_size == 0:
        df = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df.index.name = "Nom"
        df.to_csv(f)
        return df
    return pd.read_csv(f, index_col=0)

# --- 4. STYLE & TRADUCTION ---
TRAD = {
    "Français": {"titre_norm": "📖 Bilan Coran", "titre_ram": "🌙 Bilan Ramadan", "etat": "📊 État actuel", "prog": "📊 Progrès", "maj": "📝 Maj", "calc": "🔄 Calcul", "plan": "📅 Plan", "params": "⚙️ Paramètres", "admin": "🔔 Notifs", "logout": "🔒 Quitter", "hadith_btn": "✨ HADITH", "wa": "💬 WhatsApp"},
    "العربية": {"titre_norm": "📖 حصيلة القرآن", "titre_ram": "🌙 حصيلة رمضان", "etat": "📊 الحالة", "prog": "📊 التقدم", "maj": "📝 تحديث", "calc": "🔄 حساب", "plan": "📅 جدول", "params": "⚙️ الإعدادات", "admin": "🔔 تنبيهات", "logout": "🔒 خروج", "hadith_btn": "✨ حديث", "wa": "💬 واتساب"}
}
L = TRAD[st.session_state["langue"]]
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"

st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"<style>h1,h2,h3,p,label,span {{color:{COLOR}!important; text-align:center;}} div.stButton>button {{width:100%; border-radius:10px; border:2px solid {COLOR}; color:{COLOR}; font-weight:bold; height:3em;}}</style>", unsafe_allow_html=True)

# --- 5. ACCÈS ---
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
            else: st.error("Identifiants incorrects.")
        if st.button("S'inscrire"): st.session_state["view"] = "signup"; st.rerun()

    elif st.session_state["view"] == "signup":
        nu = st.text_input("Nouveau Pseudo")
        ne = st.text_input("Ton Email")
        np = st.text_input("Nouveau Mdp", type="password")
        if st.button("Envoyer ma demande"):
            if nu and ne and np:
                ddb = pd.read_csv(DEMANDES_FILE)
                pd.concat([ddb, pd.DataFrame([[nu, np, ne]], columns=["pseudo", "password", "user_email"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
                envoyer_alerte_yael(nu, "Nouvelle Inscription")
                st.success("Demande envoyée !"); st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 6. LOGIQUE D'AFFICHAGE ---
df_complet = charger_data()
auj = date.today()
df_view = df_complet if st.session_state["is_admin"] else df_complet[df_complet.index == st.session_state["user_connected"]]

with st.sidebar:
    st.title(f"👤 {st.session_state['user_connected']}")
    if st.button("🏠 Accueil"): st.session_state["page"] = "home"; st.rerun()
    if st.button(L["params"]): st.session_state["page"] = "params"; st.rerun()
    if st.session_state["is_admin"]:
        nb = len(pd.read_csv(DEMANDES_FILE)) + len(pd.read_csv(FORGOT_FILE))
        if st.button(f"🔔 Notifs ({nb})"): st.session_state["page"] = "admin"; st.rerun()
    st.divider()
    m_label = "📖 Mode Normal" if st.session_state["ramadan_mode"] else "🌙 Mode Ramadan"
    if st.button(m_label): st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]; st.rerun()
    if st.button(L["logout"]): st.session_state["auth"] = False; st.rerun()

# --- PAGE PARAMÈTRES ---
if st.session_state["page"] == "params":
    st.title(L["params"])
    new_l = st.selectbox("Langue / اللغة", ["Français", "العربية"], index=0 if st.session_state["langue"]=="Français" else 1)
    if new_l != st.session_state["langue"]: st.session_state["langue"] = new_l; st.rerun()
    st.stop()

# --- PAGE ADMIN ---
if st.session_state["page"] == "admin":
    st.title("🔔 Notifications")
    ddb = pd.read_csv(DEMANDES_FILE)
    for i, r in ddb.iterrows():
        st.info(f"Inscrire **{r['pseudo']}** ({r['user_email']}) ?")
        if st.button(f"✅ Valider {r['pseudo']}", key=f"v_{i}"):
            udb = pd.read_csv(USERS_FILE)
            pd.concat([udb, pd.DataFrame([[r['pseudo'], r['password'], "Membre", r['user_email']]], columns=["pseudo", "password", "role", "user_email"])], ignore_index=True).to_csv(USERS_FILE, index=False)
            for m in ["lecture", "ramadan"]:
                f = os.path.join(dossier, f"sauvegarde_{m}.csv")
                temp = pd.read_csv(f, index_col=0) if os.path.exists(f) else pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"], index=["Nom"])
                temp.loc[r['pseudo']] = [1, 10, 0, 1]
                temp.to_csv(f)
            envoyer_confirmation_utilisateur(r['pseudo'], r['user_email'])
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()
    st.stop()

# --- PAGE ACCUEIL ---
st.title(L["titre_ram"] if st.session_state["ramadan_mode"] else L["titre_norm"])

if st.session_state["user_connected"] == "Yael":
    if st.button(L["hadith_btn"]):
        h_file = "hadiths_fr.txt" if st.session_state["langue"] == "Français" else "hadiths_ar.txt"
        if os.path.exists(os.path.join(dossier, h_file)):
            with open(os.path.join(dossier, h_file), "r", encoding="utf-8") as f:
                lignes = f.readlines()
                if lignes: st.info(random.choice(lignes))

st.subheader(L["etat"])
if not df_view.empty:
    st.table(df_view)

    with st.expander(L["prog"]):
        for n, r in df_view.iterrows():
            total = r["Objectif Khatmas"] * 604 if st.session_state["ramadan_mode"] else 604
            fait = (r["Page Actuelle"] + (r["Cycles Finis"] * 604)) if st.session_state["ramadan_mode"] else r["Page Actuelle"]
            st.write(f"**{n}**")
            st.progress(min(1.0, fait/total))

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.session_state["user_connected"] == "Yael":
            with st.expander(L["wa"]):
                dc = st.date_input("Échéance", auj + timedelta(days=1))
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
            if st.button("💾 Sauvegarder"):
                df_complet.loc[u_sel, ["Page Actuelle", "Rythme"]] = [np, nr]
                suf = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
                df_complet.to_csv(os.path.join(dossier, f"sauvegarde_{suf}.csv")); st.rerun()
    with c3:
        with st.expander(L["calc"]):
            dp = st.date_input("Date cible", auj)
            p_prec = st.number_input("Page à cette date", 1, 604)
            if st.button("🔄 Recalculer"):
                diff = (auj - dp).days
                rythme = int(df_view.loc[st.session_state['user_connected'], "Rythme"])
                nouvelle = (p_prec + (rythme * diff)) % 604 or 1
                df_complet.loc[st.session_state["user_connected"], "Page Actuelle"] = int(nouvelle)
                suf = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
                df_complet.to_csv(os.path.join(dossier, f"sauvegarde_{suf}.csv")); st.rerun()

    st.subheader(L["plan"])
    plan_df = pd.DataFrame(index=[(auj + timedelta(days=i)).strftime("%d/%m") for i in range(30)])
    for n, r in df_view.iterrows():
        plan_df[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 1) for i in range(30)]
    st.dataframe(plan_df, use_container_width=True)
