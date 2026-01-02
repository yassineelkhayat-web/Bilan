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

def envoyer_mail(pseudo, email_dest, sujet_message):
    url = "https://api.emailjs.com/api/v1.0/email/send"
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "accessToken": EMAILJS_PRIVATE_KEY,
        "template_params": {
            "to_name": pseudo,
            "user_email": email_dest,
            "message": sujet_message
        }
    }
    try: requests.post(url, json=payload)
    except: pass

# --- 2. GESTION DES FICHIERS ---
dossier = os.path.dirname(__file__)
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv")

def init_file(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["pseudo", "password", "role", "user_email"])
init_file(DEMANDES_FILE, ["pseudo", "password", "user_email"])

# --- 3. SÉCURITÉ ADMIN (YAEL) ---
udb_check = pd.read_csv(USERS_FILE)
if "Yael" not in udb_check["pseudo"].values:
    yael_row = pd.DataFrame([["Yael", "Yassine05", "Admin", "yassine.elkhayat@isv.be"]], 
                            columns=["pseudo", "password", "role", "user_email"])
    pd.concat([udb_check, yael_row], ignore_index=True).to_csv(USERS_FILE, index=False)

# --- 4. INITIALISATION SESSION ---
for key, val in {
    "auth": False, "user_connected": None, "is_admin": False, 
    "ramadan_mode": False, "langue": "Français", "page": "home", "view": "login"
}.items():
    if key not in st.session_state: st.session_state[key] = val

def charger_data():
    suf = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
    f = os.path.join(dossier, f"sauvegarde_{suf}.csv")
    if not os.path.exists(f) or os.stat(f).st_size == 0:
        df = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df.index.name = "Nom"
        df.to_csv(f)
        return df
    return pd.read_csv(f, index_col=0)

# --- 5. STYLE & TRADUCTION ---
TRAD = {
    "Français": {"titre_norm": "📖 Bilan Coran", "titre_ram": "🌙 Bilan Ramadan", "etat": "📊 État actuel", "prog": "📊 Progrès", "maj": "📝 Maj", "calc": "🔄 Calcul", "plan": "📅 Plan", "params": "⚙️ Paramètres", "admin": "🛠️ Admin", "logout": "🔒 Quitter", "hadith_btn": "✨ HADITH", "wa": "💬 WhatsApp"},
    "العربية": {"titre_norm": "📖 حصيلة القرآن", "titre_ram": "🌙 حصيلة رمضان", "etat": "📊 الحالة", "prog": "📊 التقدم", "maj": "📝 تحديث", "calc": "🔄 حساب", "plan": "📅 جدول", "params": "⚙️ الإعدادات", "admin": "🛠️ إدارة", "logout": "🔒 خروج", "hadith_btn": "✨ حديث", "wa": "💬 واتساب"}
}
L = TRAD[st.session_state["langue"]]
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"

st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"<style>h1,h2,h3,p,label,span {{color:{COLOR}!important; text-align:center;}} div.stButton>button {{width:100%; border-radius:10px; border:2px solid {COLOR}; color:{COLOR}; font-weight:bold; height:3.5em;}}</style>", unsafe_allow_html=True)

# --- 6. AUTHENTIFICATION ---
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
        
        c1, c2 = st.columns(2)
        if c1.button("S'inscrire"): st.session_state["view"] = "signup"; st.rerun()
        if c2.button("Mot de passe oublié ?"): st.session_state["view"] = "forgot"; st.rerun()

    elif st.session_state["view"] == "forgot":
        st.subheader("Réinitialiser mon mot de passe")
        fe = st.text_input("Entre ton email d'inscription")
        if st.button("Vérifier l'email"):
            db = pd.read_csv(USERS_FILE)
            if fe in db["user_email"].values:
                pseudo = db[db["user_email"] == fe]["pseudo"].values[0]
                envoyer_mail(pseudo, fe, "Vous pouvez maintenant réinitialiser votre mot de passe sur l'application.")
                st.success("Email trouvé ! Vous pouvez maintenant modifier votre mot de passe ci-dessous.")
                st.session_state["reset_email_target"] = fe
                st.session_state["view"] = "reset_page"
                st.rerun()
            else: st.error("Email inconnu.")
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()

    elif st.session_state["view"] == "reset_page":
        st.subheader("Nouveau mot de passe")
        target = st.session_state.get("reset_email_target", "")
        new_p = st.text_input("Nouveau mot de passe", type="password")
        if st.button("Enregistrer"):
            db = pd.read_csv(USERS_FILE)
            db.loc[db["user_email"] == target, "password"] = new_p
            db.to_csv(USERS_FILE, index=False)
            st.success("Modifié ! Connectez-vous.")
            st.session_state["view"] = "login"; st.rerun()

    elif st.session_state["view"] == "signup":
        nu, ne = st.text_input("Pseudo"), st.text_input("Email")
        np = st.text_input("Mot de passe", type="password")
        if st.button("Envoyer ma demande"):
            ddb = pd.read_csv(DEMANDES_FILE)
            pd.concat([ddb, pd.DataFrame([[nu, np, ne]], columns=["pseudo", "password", "user_email"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
            requests.post(URL_FORMSPREE, data={"Objet": "Nouvelle Inscription", "User": nu})
            st.success("Demande envoyée !"); st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 7. NAVIGATION ---
df_complet = charger_data()
auj = date.today()
df_view = df_complet if st.session_state["is_admin"] else df_complet[df_complet.index == st.session_state["user_connected"]]

with st.sidebar:
    st.title(f"👤 {st.session_state['user_connected']}")
    if st.button("🏠 Accueil"): st.session_state["page"] = "home"; st.rerun()
    if st.button(L["params"]): st.session_state["page"] = "params"; st.rerun()
    if st.session_state["is_admin"]:
        if st.button(L["admin"]): st.session_state["page"] = "admin"; st.rerun()
    st.divider()
    if st.button("🌙/📖 Changer Mode"): st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]; st.rerun()
    if st.button(L["logout"]): st.session_state["auth"] = False; st.rerun()

# --- 8. PAGE ADMIN ---
if st.session_state["page"] == "admin":
    st.title("🛠️ Administration")
    
    st.subheader("⏳ Inscriptions en attente")
    ddb = pd.read_csv(DEMANDES_FILE)
    for i, r in ddb.iterrows():
        c1, c2 = st.columns([3, 1])
        c1.write(f"**{r['pseudo']}** ({r['user_email']})")
        if c2.button("✅ Valider", key=f"v_{i}"):
            udb = pd.read_csv(USERS_FILE)
            pd.concat([udb, pd.DataFrame([[r['pseudo'], r['password'], "Membre", r['user_email']]], columns=["pseudo", "password", "role", "user_email"])], ignore_index=True).to_csv(USERS_FILE, index=False)
            for m in ["lecture", "ramadan"]:
                path = os.path.join(dossier, f"sauvegarde_{m}.csv")
                tmp = pd.read_csv(path, index_col=0) if os.path.exists(path) else pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"], index=["Nom"])
                tmp.loc[r['pseudo']] = [1, 10, 0, 1]
                tmp.to_csv(path)
            envoyer_mail(r['pseudo'], r['user_email'], "Ton compte Bilan Coran est prêt !")
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()

    st.divider()
    st.subheader("👥 Gestion des Membres")
    udb = pd.read_csv(USERS_FILE)
    for i, r in udb.iterrows():
        if r['pseudo'] == "Yael": continue
        c1, c2, c3 = st.columns([2, 2, 1])
        c1.write(f"**{r['pseudo']}**")
        with c2:
            if st.checkbox("👁️", key=f"e_{i}"): st.code(r['password'])
            else: st.write("••••")
        if c3.button("🗑️", key=f"d_{i}"):
            udb.drop(i).to_csv(USERS_FILE, index=False)
            st.rerun()
    st.stop()

# --- 9. PAGE ACCUEIL ---
if st.session_state["page"] == "home":
    st.title(L["titre_ram"] if st.session_state["ramadan_mode"] else L["titre_norm"])
    
    if st.session_state["user_connected"] == "Yael" and st.button(L["hadith_btn"]):
        h_file = "hadiths_fr.txt" if st.session_state["langue"] == "Français" else "hadiths_ar.txt"
        if os.path.exists(os.path.join(dossier, h_file)):
            with open(os.path.join(dossier, h_file), "r", encoding="utf-8") as f:
                lignes = f.readlines()
                if lignes: st.info(random.choice(lignes))

    if not df_view.empty:
        st.subheader(L["etat"])
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
                    st.text_area("WhatsApp :", msg)
        with c2:
            with st.expander(L["maj"]):
                u_sel = st.selectbox("Qui ?", df_view.index)
                np = st.number_input("Page", 1, 604, int(df_view.loc[u_sel, "Page Actuelle"]))
                nr = st.number_input("Rythme", 1, 100, int(df_view.loc[u_sel, "Rythme"]))
                if st.button("💾 Sauver"):
                    df_complet.loc[u_sel, ["Page Actuelle", "Rythme"]] = [np, nr]
                    df_complet.to_csv(os.path.join(dossier, f"sauvegarde_{'ramadan' if st.session_state['ramadan_mode'] else 'lecture'}.csv")); st.rerun()
        with c3:
            with st.expander(L["calc"]):
                dp = st.date_input("Le...", auj - timedelta(days=1))
                p_prec = st.number_input("J'étais page", 1, 604)
                if st.button("🔄 Calculer"):
                    diff = (auj - dp).days
                    rythme = int(df_view.loc[st.session_state['user_connected'], "Rythme"])
                    nouvelle = (p_prec + (rythme * diff)) % 604 or 1
                    df_complet.loc[st.session_state["user_connected"], "Page Actuelle"] = int(nouvelle)
                    df_complet.to_csv(os.path.join(dossier, f"sauvegarde_{'ramadan' if st.session_state['ramadan_mode'] else 'lecture'}.csv")); st.rerun()

        st.subheader(L["plan"])
        plan_df = pd.DataFrame(index=[(auj + timedelta(days=i)).strftime("%d/%m") for i in range(30)])
        for n, r in df_view.iterrows():
            plan_df[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 1) for i in range(30)]
        st.dataframe(plan_df, use_container_width=True)

# --- 10. PAGE PARAMS ---
if st.session_state["page"] == "params":
    st.title(L["params"])
    new_l = st.selectbox("Langue", ["Français", "العربية"], index=0 if st.session_state["langue"]=="Français" else 1)
    if new_l != st.session_state["langue"]: st.session_state["langue"] = new_l; st.rerun()
