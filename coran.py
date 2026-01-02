import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random
import requests

# --- 1. CONFIGURATION API ---
EMAILJS_SERVICE_ID = "service_v9ebnic" 
EMAILJS_TEMPLATE_ID = "template_rghkouc"
EMAILJS_PUBLIC_KEY = "LUCKx4YnQSQ3ncrue"
EMAILJS_PRIVATE_KEY = "xnNMOnkv8TSM6N_fK9TCR"
FORMSPREE_URL = "https://formspree.io/f/mnpkenre"

def envoyer_email_code(pseudo, email_dest, code):
    """Utilisé uniquement pour le Mot de passe oublié via EmailJS"""
    url = "https://api.emailjs.com/api/v1.0/email/send"
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "accessToken": EMAILJS_PRIVATE_KEY,
        "template_params": {
            "to_name": pseudo,
            "user_email": email_dest,
            "message": f"Voici votre CODE DE RÉCUPÉRATION : {code}"
        }
    }
    try: requests.post(url, json=payload, timeout=10)
    except: pass

def envoyer_formspree_inscription(pseudo, email):
    """Utilisé pour les inscriptions (Formspree)"""
    try: requests.post(FORMSPREE_URL, data={"sujet": "Nouvelle Inscription", "pseudo": pseudo, "email": email}, timeout=10)
    except: pass

# --- 2. GESTION DES FICHIERS ---
dossier = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(dossier, "config_dates.csv")
USERS_FILE = os.path.join(dossier, "users.csv")
DEMANDES_FILE = os.path.join(dossier, "demandes.csv")
CODES_FILE = os.path.join(dossier, "combinaisons.txt")
SAUV_LECTURE = os.path.join(dossier, "sauvegarde_lecture.csv")
SAUV_RAMADAN = os.path.join(dossier, "sauvegarde_ramadan.csv")

def init_file(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USERS_FILE, ["email", "pseudo", "password", "role"])
init_file(DEMANDES_FILE, ["email", "pseudo", "password"])

# Correction cruciale : Charger d'abord, ajouter Yael SEULEMENT s'il est absent
udb_init = pd.read_csv(USERS_FILE)
if "Yael" not in udb_init["pseudo"].values:
    admin_row = pd.DataFrame([["yassine.elkhayat@isv.be", "Yael", "Yassine05", "Admin"]], columns=["email", "pseudo", "password", "role"])
    udb_init = pd.concat([udb_init, admin_row], ignore_index=True)
    udb_init.to_csv(USERS_FILE, index=False)

if not os.path.exists(CODES_FILE):
    with open(CODES_FILE, "w") as f:
        for _ in range(1000): f.write(str(random.randint(100000, 999999)) + "\n")

# --- 3. SESSION STATE ---
if "auth" not in st.session_state:
    st.session_state.update({
        "auth": False, "user_connected": None, "is_admin": False, 
        "ramadan_mode": False, "langue": "Français", "view": "login",
        "reset_step": 1, "temp_code": "", "temp_email": "", "page_params": False
    })

if os.path.exists(CONFIG_FILE):
    conf_df = pd.read_csv(CONFIG_FILE)
    st.session_state["debut_ramadan"] = date.fromisoformat(conf_df.iloc[0]["debut"])
    st.session_state["fin_ramadan"] = date.fromisoformat(conf_df.iloc[0]["fin"])
else:
    st.session_state["debut_ramadan"], st.session_state["fin_ramadan"] = date(2025, 3, 1), date(2025, 3, 30)

def verifier_et_creer_sauvegarde(fichier_cible):
    if not os.path.exists(fichier_cible) or os.stat(fichier_cible).st_size == 0:
        df_v = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df_v.index.name = "Nom"
        df_v.to_csv(fichier_cible)
        return df_v
    return pd.read_csv(fichier_cible, index_col=0)

# --- 4. TRADUCTIONS ---
TRAD = {
    "Français": {
        "titre_norm": "📖 Bilan de Lecture", "titre_ram": "🌙 Mode Ramadan Pro", "titre_params": "⚙️ Configuration",
        "acces": "🔐 Accès Sécurisé", "user_label": "Pseudo :", "code_label": "Mot de passe :", "btn_unlock": "Déverrouiller",
        "btn_signup": "Créer un compte", "btn_forgot": "Mdp oublié ?", "params": "Paramètres", "add_pre": "Ajouter :",
        "btn_add": "➕ Ajouter", "del_pre": "Supprimer :", "btn_del": "🗑️ Supprimer", "btn_logout": "🔒 Déconnexion",
        "etat": "📊 État actuel", "col_prog": "Progression", "exp_msg": "💬 WhatsApp Message",
        "echeance": "Échéance :", "copier": "Copier :", "exp_maj": "📝 Mise à jour",
        "pers": "Personne :", "pg_act": "Page actuelle :", "rythme": "Rythme :",
        "btn_save": "💾 Enregistrer", "exp_prec": "🔄 Date précise", "date_prec": "Date :",
        "pg_date": "Page à cette date :", "btn_recalc": "⚙️ Recalculer", "plan": "📅 Planning 30 jours",
        "lang_btn": "🌐 Langue", "mode_ram_btn": "Mode Ramadan", "mode_norm_btn": "Mode Normal",
        "hadith_btn": "GÉNÉRER HADITH", "khatma": "Objectif Khatmas", "home_btn": "🏠 Accueil",
        "view_prog": "📊 Progression visuelle", "notif": "🔔 Notifications", "date_deb": "Début Ramadan :", "date_fin": "Fin Ramadan :"
    },
    "العربية": {
        "titre_norm": "📖 حصيلة القراءة", "titre_ram": "🌙 وضع رمضان", "titre_params": "⚙️ الإعدادات",
        "acces": "🔐 دخول آمن", "user_label": "الاسم :", "code_label": "رمز الدخول :", "btn_unlock": "فتح",
        "btn_signup": "إنشاء حساب", "btn_forgot": "نسيت الرمز؟", "params": "الإعدادات", "add_pre": "إضافة اسم :",
        "btn_add": "إضافة +", "del_pre": "حذف :", "btn_del": "🗑️ حذف", "btn_logout": "🔒 خروج",
        "etat": "📊 الحالة الراهنة", "col_prog": "التقدم", "exp_msg": "💬 رسالة واتساب",
        "echeance": "الموعد :", "copier": "نسخ :", "exp_maj": "📝 تحديث",
        "pers": "الشخص :", "pg_act": "الصفحة الحالية :", "rythme": "المعدل :",
        "btn_save": "💾 حفظ", "exp_prec": "🔄 تاريخ دقيق", "date_prec": "التاريخ :",
        "pg_date": "الصفحة في التاريخ :", "btn_recalc": "⚙️ إعادة الحساب", "plan": "📅 الجدول ٣٠ يوم",
        "lang_btn": "🌐 اللغة", "mode_ram_btn": "وضع رمضان", "mode_norm_btn": "الوضع العادي",
        "hadith_btn": "إنشاء رسالة حديث", "khatma": "هدف الختمات", "home_btn": "🏠 الرئيسية",
        "view_prog": "📊 التقدم البصري", "notif": "تنبيهات", "date_deb": "بداية رمضان :", "date_fin": "نهاية رمضان :"
    }
}
L = TRAD.get(st.session_state["langue"], TRAD["Français"])

COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"
st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"<style>h1,h2,h3,p,label,span{{color:{COLOR}!important; text-align:center;}} div.stButton>button{{width:100%; border:2px solid {COLOR}; color:{COLOR}; border-radius:10px; font-weight:bold;}}</style>", unsafe_allow_html=True)

DATA_FILE = SAUV_RAMADAN if st.session_state["ramadan_mode"] else SAUV_LECTURE
df = verifier_et_creer_sauvegarde(DATA_FILE)

# --- 6. AUTHENTIFICATION ---
if not st.session_state["auth"]:
    if st.session_state["view"] == "login":
        st.title(L["acces"])
        u_in = st.text_input(L["user_label"])
        p_in = st.text_input(L["code_label"], type="password")
        if st.button(L["btn_unlock"]):
            udb = pd.read_csv(USERS_FILE)
            match = udb[(udb["pseudo"] == u_in) & (udb["password"].astype(str) == p_in)]
            if not match.empty:
                st.session_state.update({"auth": True, "user_connected": u_in, "is_admin": (match.iloc[0]["role"] == "Admin")})
                st.rerun()
            else: st.error("Identifiants incorrects")
        c1, c2 = st.columns(2)
        if c1.button(L["btn_signup"]): st.session_state["view"] = "signup"; st.rerun()
        if c2.button(L["btn_forgot"]): st.session_state["view"] = "forgot"; st.session_state["reset_step"] = 1; st.rerun()
    
    elif st.session_state["view"] == "forgot":
        st.subheader("🔑 Récupération de mot de passe")
        if st.session_state["reset_step"] == 1:
            fe = st.text_input("Email d'inscription")
            if st.button("Envoyer le code"):
                db = pd.read_csv(USERS_FILE)
                if fe in db["email"].values:
                    with open(CODES_FILE, "r") as f: codes = f.read().splitlines()
                    code = random.choice(codes)
                    st.session_state.update({"temp_code": code, "temp_email": fe, "reset_step": 2})
                    envoyer_email_code(db[db["email"]==fe]["pseudo"].values[0], fe, code)
                    st.success("Code envoyé via EmailJS")
                else: st.error("Email inconnu.")
        elif st.session_state["reset_step"] == 2:
            cs = st.text_input("Code reçu")
            if st.button("Vérifier"):
                if cs == st.session_state["temp_code"]: st.session_state["reset_step"] = 3; st.rerun()
                else: st.error("Code erroné.")
        elif st.session_state["reset_step"] == 3:
            np = st.text_input("Nouveau MDP", type="password")
            if st.button("Confirmer"):
                db = pd.read_csv(USERS_FILE)
                db.loc[db["email"] == st.session_state["temp_email"], "password"] = np
                db.to_csv(USERS_FILE, index=False)
                st.success("Mot de passe mis à jour !")
                st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
        
    elif st.session_state["view"] == "signup":
        st.title("📝 Inscription")
        ne, nu, np = st.text_input("Email"), st.text_input("Pseudo"), st.text_input("Mot de passe", type="password")
        if st.button("Envoyer la demande"):
            if ne and nu and np:
                ddb = pd.read_csv(DEMANDES_FILE)
                pd.concat([ddb, pd.DataFrame([[ne, nu, np]], columns=["email", "pseudo", "password"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
                envoyer_formspree_inscription(nu, ne)
                st.success("Demande envoyée via Formspree !"); st.session_state["view"] = "login"; st.rerun()
        if st.button("Retour"): st.session_state["view"] = "login"; st.rerun()
    st.stop()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.header(f"👤 {st.session_state['user_connected']}")
    if st.button(L["home_btn"]): st.session_state["page_params"] = False; st.rerun()
    if st.button(L["params"]): st.session_state["page_params"] = "settings"; st.rerun()
    if st.session_state["is_admin"]:
        nb_n = len(pd.read_csv(DEMANDES_FILE))
        if st.button(f"{L['notif']} ({nb_n})"): st.session_state["page_params"] = "notif"; st.rerun()
    st.divider()
    if st.button(L["mode_norm_btn"] if st.session_state["ramadan_mode"] else L["mode_ram_btn"]):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]; st.rerun()
    if st.button(L["btn_logout"]): st.session_state["auth"] = False; st.rerun()

# --- 8. VUES PRINCIPALES (NOTIF / SETTINGS / ACCUEIL) ---

if st.session_state["page_params"] == "notif" and st.session_state["is_admin"]:
    st.title("🔔 Panel Admin")
    ddb = pd.read_csv(DEMANDES_FILE)
    if ddb.empty: st.info("Aucune demande.")
    for i, r in ddb.iterrows():
        c1, c2, c3 = st.columns([3,1,1])
        c1.write(f"**{r['pseudo']}** ({r['email']})")
        if c2.button("✅ Accepter", key=f"ok_{i}"):
            udb = pd.read_csv(USERS_FILE)
            pd.concat([udb, pd.DataFrame([[r['email'], r['pseudo'], r['password'], "Membre"]], columns=["email", "pseudo", "password", "role"])], ignore_index=True).to_csv(USERS_FILE, index=False)
            for f in [SAUV_LECTURE, SAUV_RAMADAN]:
                tmp_df = verifier_et_creer_sauvegarde(f)
                tmp_df.loc[r['pseudo']] = [1, 10, 0, 1]
                tmp_df.to_csv(f)
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()
        if c3.button("❌ Refuser", key=f"no_{i}"):
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()

elif st.session_state["page_params"] == "settings":
    st.title(L["titre_params"])
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(L["lang_btn"])
        ch = st.selectbox("", list(TRAD.keys()), index=list(TRAD.keys()).index(st.session_state["langue"]))
        if ch != st.session_state["langue"]: st.session_state["langue"] = ch; st.rerun()
    with c2:
        st.subheader("Dates Ramadan")
        d1 = st.date_input(L["date_deb"], st.session_state["debut_ramadan"])
        d2 = st.date_input(L["date_fin"], st.session_state["fin_ramadan"])
        if st.button(L["btn_save"]):
            pd.DataFrame({"debut":[d1.isoformat()],"fin":[d2.isoformat()]}).to_csv(CONFIG_FILE, index=False); st.success("OK")

else:
    # --- ACCUEIL ---
    st.title(L["titre_ram"] if st.session_state["ramadan_mode"] else L["titre_norm"])
    auj = date.today()
    view_df = df if st.session_state["is_admin"] else df[df.index == st.session_state["user_connected"]]
    if not view_df.empty:
        st.subheader(L["etat"])
        recap = view_df.copy()
        recap[L["col_prog"]] = (recap["Page Actuelle"] / 604 * 100).round(1).astype(str) + "%"
        st.table(recap)
        # ... Reste du code d'affichage (expander, progression, etc.) inchangé
