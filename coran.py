import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random

# --- 1. CONFIGURATION INITIALE ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if "user_connected" not in st.session_state: st.session_state["user_connected"] = None
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "ramadan_mode" not in st.session_state: st.session_state["ramadan_mode"] = False
if "page_params" not in st.session_state: st.session_state["page_params"] = False
if "langue" not in st.session_state: st.session_state["langue"] = "Français"
if "view" not in st.session_state: st.session_state["view"] = "login"

VERSION = "6.3"
LAST_UPDATE = "28/12/2025"
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

# Sécurité Admin par défaut
udb_init = pd.read_csv(USERS_FILE)
if "Yael" not in udb_init["pseudo"].values:
    admin_row = pd.DataFrame([["Yael", "Yassine05", "Admin"]], columns=["pseudo", "password", "role"])
    pd.concat([udb_init, admin_row], ignore_index=True).to_csv(USERS_FILE, index=False)

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

def charger_hadith_aleatoire(langue):
    filename = os.path.join(dossier, "hadiths_fr.txt" if langue == "Français" else "hadiths_ar.txt")
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                lignes = [l.strip() for l in f.readlines() if l.strip()]
            if lignes:
                choix = random.choice(lignes)
                return (choix.split("|")[0].strip(), choix.split("|")[1].strip()) if "|" in choix else (choix, "Riyad As-Salihin")
        return "Fichier Hadith manquant.", "Info"
    except: return "Erreur Hadith.", "Erreur"

# --- 3. TRADUCTIONS ---
TRAD = {
    "Français": {
        "titre_norm": "📖 Bilan de Lecture", "titre_ram": "🌙 Mode Ramadan Pro", "titre_params": "⚙️ Configuration",
        "acces": "🔐 Accès Sécurisé", "user_label": "Pseudo :", "code_label": "Mot de passe :", "btn_unlock": "Déverrouiller",
        "btn_signup": "Créer un compte", "btn_forgot": "Mdp oublié ?", "params": "Paramètres", "add_pre": "Ajouter un profil :",
        "btn_add": "➕ Ajouter", "del_pre": "Supprimer :", "btn_del": "🗑️ Supprimer", "btn_logout": "🔒 Déconnexion",
        "etat": "📊 État actuel", "col_prog": "Progression", "exp_msg": "💬 Générer message WhatsApp",
        "echeance": "Échéance :", "copier": "Copier :", "exp_maj": "📝 Mise à jour",
        "pers": "Personne :", "pg_act": "Page actuelle :", "rythme": "Rythme :",
        "btn_save": "💾 Enregistrer", "exp_prec": "🔄 Date précise", "date_prec": "Date :",
        "pg_date": "Page à cette date :", "btn_recalc": "⚙️ Recalculer", "plan": "📅 Planning 30 jours",
        "lang_btn": "🌐 Langue / لغة", "mode_ram_btn": "Mode Ramadan", "mode_norm_btn": "Mode Normal",
        "hadith_btn": "GÉNÉRER MESSAGE HADITH", "khatma": "Objectif Khatmas",
        "home_btn": "🏠 Accueil", "view_prog": "📊 Progression visuelle", "notif": "🔔 Notifications",
        "avant_ram": "Il reste {} jours avant le Ramadan", "pendant_ram": "Il reste {} jours avant la fin",
        "date_deb": "Début du Ramadan :", "date_fin": "Fin du Ramadan :", "info_title": "ℹ️ Infos Logiciel"
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
        "hadith_btn": "إنشاء رسالة حديث", "khatma": "هدف الختمات",
        "home_btn": "🏠 الرئيسية", "view_prog": "📊 التقدم البصري", "notif": "🔔 تنبيهات",
        "avant_ram": "متبقي {} أيام على رمضان", "pendant_ram": "متبقي {} أيام على نهاية رمضان",
        "date_deb": "بداية رمضان :", "date_fin": "نهاية رمضان :", "info_title": "ℹ️ معلومات"
    }
}
L = TRAD.get(st.session_state["langue"], TRAD["Français"])

# --- 4. STYLE ---
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"
st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"<style>h1,h2,h3,p,label,span{{color:{COLOR}!important;}} div.stButton>button{{border:2px solid {COLOR}!important; color:{COLOR}!important; border-radius:10px; font-weight:bold;}} div.stButton>button:hover{{background-color:{COLOR}!important; color:white!important;}} .stProgress > div > div > div > div {{ background-color: {COLOR} !important; }}</style>", unsafe_allow_html=True)

# --- 5. DATA ---
suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
DATA_FILE = os.path.join(dossier, f"sauvegarde_{suffixe}.csv")
df = verifier_et_creer_sauvegarde(DATA_FILE)

# --- 6. AUTHENTIFICATION ---
if not st.session_state["auth"]:
    if st.session_state["view"] == "login":
        st.title(L["acces"])
        u_in = st.text_input(L["user_label"])
        p_in = st.text_input(L["code_label"], type="password")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(L["btn_unlock"]):
                udb = pd.read_csv(USERS_FILE)
                match = udb[(udb["pseudo"] == u_in) & (udb["password"] == p_in)]
                if not match.empty:
                    st.session_state["auth"], st.session_state["user_connected"] = True, u_in
                    st.session_state["is_admin"] = (match.iloc[0]["role"] == "Admin")
                    st.rerun()
                else: st.error("Erreur")
        with c2: 
            if st.button(L["btn_signup"]): st.session_state["view"] = "signup"; st.rerun()
        with c3:
            if st.button(L["btn_forgot"]):
                if u_in:
                    fdb = pd.read_csv(FORGOT_FILE)
                    if u_in not in fdb["pseudo"].values:
                        pd.concat([fdb, pd.DataFrame([[u_in]], columns=["pseudo"])], ignore_index=True).to_csv(FORGOT_FILE, index=False)
                    st.success("Demande envoyée à Yael.")
                else: st.warning("Pseudo ?")
    elif st.session_state["view"] == "signup":
        st.title("📝 Inscription")
        nu, np, ncp = st.text_input("Pseudo"), st.text_input("Pass", type="password"), st.text_input("Confirm", type="password")
        if st.button("Envoyer"):
            if np == ncp and nu:
                ddb = pd.read_csv(DEMANDES_FILE)
                pd.concat([ddb, pd.DataFrame([[nu, np]], columns=["pseudo", "password"])], ignore_index=True).to_csv(DEMANDES_FILE, index=False)
                st.success("Ok !"); st.session_state["view"] = "login"
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
    if st.button(L["mode_norm_btn"] if st.session_state["ramadan_mode"] else L["mode_ram_btn"]):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]; st.rerun()
    if st.button(L["btn_logout"]): st.session_state["auth"] = False; st.rerun()

# --- 8. NOTIFICATIONS (GESTION YAEL) ---
if st.session_state["page_params"] == "notif" and st.session_state["is_admin"]:
    st.title("🔔 Notifications")
    # Inscriptions
    ddb = pd.read_csv(DEMANDES_FILE)
    for i, r in ddb.iterrows():
        c1, c2, c3 = st.columns([2,1,1])
        c1.write(f"Insc : **{r['pseudo']}**")
        if c2.button("✅", key=f"ok_{i}"):
            new_u = pd.DataFrame([[r['pseudo'], r['password'], "Membre"]], columns=["pseudo", "password", "role"])
            pd.concat([pd.read_csv(USERS_FILE), new_u], ignore_index=True).to_csv(USERS_FILE, index=False)
            df.loc[r['pseudo']] = [1, 10, 0, 1]; df.to_csv(DATA_FILE)
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()
        if c3.button("❌", key=f"no_{i}"):
            ddb.drop(i).to_csv(DEMANDES_FILE, index=False); st.rerun()
    # Mdp oubliés
    fdb = pd.read_csv(FORGOT_FILE)
    udb = pd.read_csv(USERS_FILE)
    for i, r in fdb.iterrows():
        st.divider()
        u_info = udb[udb["pseudo"] == r['pseudo']]
        if not u_info.empty:
            c1, c2, c3 = st.columns([2,2,1])
            c1.write(f"Mdp perdu : **{r['pseudo']}**\n(Ancien : `{u_info.iloc[0]['password']}`)")
            n_mdp = c2.text_input("Nouveau MDP", key=f"fval_{i}")
            if c3.button("💾", key=f"fsave_{i}"):
                if n_mdp:
                    udb.loc[udb["pseudo"] == r['pseudo'], "password"] = n_mdp
                    udb.to_csv(USERS_FILE, index=False)
                    fdb.drop(i).to_csv(FORGOT_FILE, index=False); st.rerun()
    st.stop()

# --- 9. CONFIGURATION ---
if st.session_state["page_params"] == "settings":
    st.title(L["titre_params"])
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(L["lang_btn"])
        ch = st.selectbox("", list(TRAD.keys()), index=list(TRAD.keys()).index(st.session_state["langue"]))
        if ch != st.session_state["langue"]: st.session_state["langue"] = ch; st.rerun()
        st.divider()
        st.subheader("📅 Dates")
        d1 = st.date_input(L["date_deb"], st.session_state["debut_ramadan"])
        d2 = st.date_input(L["date_fin"], st.session_state["fin_ramadan"])
        if st.button(L["btn_save"]):
            pd.DataFrame({"debut":[d1.isoformat()],"fin":[d2.isoformat()]}).to_csv(CONFIG_FILE, index=False)
            st.success("OK")
    with c2:
        st.subheader(L["add_pre"])
        nom_s = st.text_input("")
        if st.button(L["btn_add"]):
            if nom_s and nom_s not in df.index:
                df.loc[nom_s] = [1, 10, 0, 1]; df.to_csv(DATA_FILE); st.rerun()
        if not df.empty:
            st.divider()
            cible = st.selectbox(L["del_pre"], df.index)
            if st.button(L["btn_del"]):
                df = df.drop(cible); df.to_csv(DATA_FILE); st.rerun()
    st.stop()

# --- 10. ACCUEIL ---
st.title(L["titre_ram"] if st.session_state["ramadan_mode"] else L["titre_norm"])
auj = date.today()

if st.session_state["ramadan_mode"]:
    if auj < st.session_state["debut_ramadan"]:
        st.info(L["avant_ram"].format((st.session_state["debut_ramadan"] - auj).days))
    elif auj <= st.session_state["fin_ramadan"]:
        st.success(L["pendant_ram"].format((st.session_state["fin_ramadan"] - auj).days))

view_df = df if st.session_state["is_admin"] else df[df.index == st.session_state["user_connected"]]

if not view_df.empty:
    st.subheader(L["etat"])
    recap = view_df.copy()
    if st.session_state["ramadan_mode"]:
        recap[L["col_prog"]] = (((recap["Page Actuelle"] + (recap["Cycles Finis"] * 604)) / (recap["Objectif Khatmas"] * 604)) * 100).round(1).astype(str) + "%"
    else:
        recap[L["col_prog"]] = (recap["Page Actuelle"] / 604 * 100).round(1).astype(str) + "%"
    st.table(recap)

    with st.expander(L["view_prog"]):
        for n, r in view_df.iterrows():
            total = r["Objectif Khatmas"] * 604 if st.session_state["ramadan_mode"] else 604
            lu = (r["Page Actuelle"] + (r["Cycles Finis"] * 604)) if st.session_state["ramadan_mode"] else r["Page Actuelle"]
            st.write(f"**{n}**")
            st.progress(min(1.0, lu/total))

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.expander(L["exp_msg"]):
            dc = st.date_input(L["echeance"], auj + timedelta(days=1))
            diff = (dc - auj).days
            msg = f"*Bilan {dc.strftime('%d/%m')}* :\n\n"
            for n, r in view_df.iterrows():
                p = (int(r["Page Actuelle"]) + (int(r["Rythme"]) * diff)) % 604 or 1
                msg += f"• *{n.upper()}* : p.{int(p)}\n"
            st.text_area(L["copier"], msg, height=150)
    with c2:
        with st.expander(L["exp_maj"]):
            u = st.selectbox(L["pers"], view_df.index)
            pa = st.number_input(L["pg_act"], 1, 604, int(df.loc[u, "Page Actuelle"]))
            if st.session_state["ramadan_mode"]:
                ok = st.number_input(L["khatma"], 1, 10, int(df.loc[u, "Objectif Khatmas"]))
                cf = st.number_input("Khatmas finies", 0, 10, int(df.loc[u, "Cycles Finis"]))
                if st.button(L["btn_save"], key="r_save"):
                    j_rest = max(1, (st.session_state["fin_ramadan"] - auj).days)
                    ry = max(1, round(((ok * 604) - (pa + (cf * 604))) / j_rest, 1))
                    df.loc[u] = [pa, ry, cf, ok]; df.to_csv(DATA_FILE); st.rerun()
            else:
                ry = st.number_input(L["rythme"], 1, 100, int(df.loc[u, "Rythme"]))
                if st.button(L["btn_save"], key="n_save"):
                    df.loc[u, ["Page Actuelle", "Rythme"]] = [pa, ry]; df.to_csv(DATA_FILE); st.rerun()
    with c3:
        with st.expander(L["exp_prec"]):
            ua = st.selectbox(L["pers"], view_df.index, key="adj")
            da = st.date_input(L["date_prec"], auj)
            pda = st.number_input(L["pg_date"], 1, 604)
            if st.button(L["btn_recalc"]):
                delt = (auj - da).days
                np = (pda + (int(df.loc[ua, "Rythme"]) * delt)) % 604 or 1
                df.loc[ua, "Page Actuelle"] = int(np); df.to_csv(DATA_FILE); st.rerun()

    if st.session_state["ramadan_mode"]:
        st.divider()
        if st.button(L["hadith_btn"]):
            txt, src = charger_hadith_aleatoire(st.session_state["langue"])
            st.session_state["h_msg"] = f"✨ *Hadith* :\n\n{txt}\n\n📚 {src}"
        if "h_msg" in st.session_state: st.text_area(L["copier"], st.session_state["h_msg"])

    st.subheader(L["plan"])
    plan_df = pd.DataFrame(index=[(auj + timedelta(days=i)).strftime("%d/%m") for i in range(30)])
    for n, r in view_df.iterrows():
        plan_df[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 1) for i in range(30)]
    st.dataframe(plan_df, use_container_width=True)
else: st.info("Aucun profil.")
