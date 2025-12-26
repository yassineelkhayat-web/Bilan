import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random

# --- 1. CONFIGURATION INITIALE & SESSION ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if "ramadan_mode" not in st.session_state: st.session_state["ramadan_mode"] = False
if "page_params" not in st.session_state: st.session_state["page_params"] = False
if "langue" not in st.session_state: st.session_state["langue"] = "Français"
if "code_secret" not in st.session_state: st.session_state["code_secret"] = "Yassine05"

VERSION = "3.1"
LAST_UPDATE = "26/12/2025" 
AUTHOR = "Yael"

# --- 2. GESTION DES FICHIERS ET DATA ---
dossier = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(dossier, "config_dates.csv")

if os.path.exists(CONFIG_FILE):
    conf_df = pd.read_csv(CONFIG_FILE)
    st.session_state["debut_ramadan"] = date.fromisoformat(conf_df.iloc[0]["debut"])
    st.session_state["fin_ramadan"] = date.fromisoformat(conf_df.iloc[0]["fin"])
else:
    if "debut_ramadan" not in st.session_state: st.session_state["debut_ramadan"] = date(2025, 3, 1)
    if "fin_ramadan" not in st.session_state: st.session_state["fin_ramadan"] = date(2025, 3, 30)

COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"

def verifier_et_creer_sauvegarde(fichier_cible):
    if not os.path.exists(fichier_cible):
        autre_fichier = os.path.join(dossier, "sauvegarde_lecture.csv" if "ramadan" in fichier_cible else "sauvegarde_ramadan.csv")
        if os.path.exists(autre_fichier):
            df_existant = pd.read_csv(autre_fichier, index_col=0)
            noms = df_existant.index.tolist()
            df_nouveau = pd.DataFrame(index=noms, columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
            df_nouveau.index.name = "Nom"
            df_nouveau.fillna({"Page Actuelle": 1, "Rythme": 10, "Cycles Finis": 0, "Objectif Khatmas": 1}, inplace=True)
            df_nouveau.to_csv(fichier_cible)
            return df_nouveau
        else:
            df_vide = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
            df_vide.index.name = "Nom"; df_vide.to_csv(fichier_cible)
            return df_vide
    return pd.read_csv(fichier_cible, index_col=0)

def charger_hadith_aleatoire(langue):
    filename = os.path.join(dossier, "hadiths_fr.txt" if langue == "Français" else "hadiths_ar.txt")
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                lignes = [line.strip() for line in f.readlines() if line.strip()]
            if lignes:
                choix = random.choice(lignes)
                if "|" in choix:
                    texte, source = choix.split("|")
                    return texte.strip(), source.strip()
                return choix, "Riyad As-Salihin"
        return "Fichier non trouvé.", "Erreur"
    except Exception as e: return f"Erreur: {str(e)}", "Erreur"

# --- 3. TRADUCTIONS ---
TRAD = {
    "Français": {
        "titre_norm": "📖 Bilan de Lecture", "titre_ram": "🌙 Mode Ramadan Pro", "titre_params": "⚙️ Configuration",
        "acces": "🔐 Accès Sécurisé", "code_label": "Code d'accès :", "btn_unlock": "Déverrouiller",
        "params": "Paramètres", "add_pre": "Ajouter un prénom :", "btn_add": "➕ Ajouter",
        "del_pre": "Supprimer un profil :", "btn_del": "🗑️ Supprimer", "btn_logout": "🔒 Déconnexion",
        "etat": "📊 État actuel", "col_prog": "Progression", "exp_msg": "💬 Générer message",
        "echeance": "Échéance :", "copier": "Copier :", "exp_maj": "📝 Mise à jour",
        "pers": "Personne :", "pg_act": "Page actuelle :", "rythme": "Rythme :",
        "btn_save": "💾 Enregistrer", "exp_prec": "🔄 Date précise", "date_prec": "Date :",
        "pg_date": "Page à cette date :", "btn_recalc": "⚙️ Recalculer", "plan": "📅 Planning 30 jours",
        "lang_btn": "🌐 Langue / لغة", "new_pwd": "Nouveau code secret :", 
        "mode_ram_btn": "Mode Ramadan", "mode_norm_btn": "Mode Normal",
        "hadith_btn": "GÉNÉRER MESSAGE HADITH", "khatma": "Objectif Khatmas",
        "home_btn": "🏠 Accueil", "info": "Ajoutez des prénoms dans les paramètres.",
        "view_prog": "📊 Voir la progression visuelle",
        "avant_ram": "Il reste {} jours avant le début du Ramadan",
        "pendant_ram": "Il reste {} jours avant la fin du Ramadan",
        "date_deb": "Début du Ramadan :", "date_fin": "Fin du Ramadan :",
        "info_title": "ℹ️ Infos Logiciel"
    },
    "العربية": {
        "titre_norm": "📖 حصيلة القراءة", "titre_ram": "🌙 وضع رمضان", "titre_params": "⚙️ الإعدادات",
        "acces": "🔐 دخول آمن", "code_label": "رمز الدخول :", "btn_unlock": "فتح",
        "params": "الإعدادات", "add_pre": "إضافة اسم :", "btn_add": "إضافة +",
        "del_pre": "حذف ملف :", "btn_del": "🗑️ حذف", "btn_logout": "🔒 خروج",
        "etat": "📊 الحالة الراهنة", "col_prog": "التقدم", "exp_msg": "💬 إنشاء رسالة",
        "echeance": "الموعد :", "copier": "نسخ :", "exp_maj": "📝 تحديث",
        "pers": "الشخص :", "pg_act": "الصفحة الحالية :", "rythme": "المعدل :",
        "btn_save": "💾 حفظ", "exp_prec": "🔄 تاريخ دقيق", "date_prec": "التاريخ :",
        "pg_date": "الصفحة في هذا التاريخ :", "btn_recalc": "⚙️ إعادة الحساب", "plan": "📅 الجدول العام",
        "lang_btn": "🌐 اللغة", "new_pwd": "رمز جديد :", 
        "mode_ram_btn": "وضع رمضان", "mode_norm_btn": "الوضع العادي",
        "hadith_btn": "إنشاء رسالة حديث", "khatma": "هدف الختمات",
        "home_btn": "🏠 الرئيسية", "info": "أضف أسماء في الإعدادات.",
        "view_prog": "📊 عرض التقدم البصري",
        "avant_ram": "متبقي {} أيام على بداية رمضان",
        "pendant_ram": "متبقي {} أيام على نهاية رمضان",
        "date_deb": "بداية رمضان :", "date_fin": "نهاية رمضان :",
        "info_title": "ℹ️ معلومات البرنامج"
    }
}

L = TRAD.get(st.session_state["langue"], TRAD["Français"])

# --- 4. STYLE DYNAMIQUE ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #FFFFFF; }}
    h1, h2, h3, p, label, span {{ color: {COLOR} !important; }}
    div.stButton > button {{
        background-color: #FFFFFF !important; color: {COLOR} !important;
        border: 2px solid {COLOR} !important; border-radius: 10px !important;
        font-weight: bold !important; width: 100% !important; transition: 0.3s;
    }}
    div.stButton > button:hover {{ background-color: {COLOR} !important; color: #FFFFFF !important; }}
    .stProgress > div > div > div > div {{ background-color: {COLOR} !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. CHARGEMENT DATA ---
suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
DATA_FILE = os.path.join(dossier, f"sauvegarde_{suffixe}.csv")
df = verifier_et_creer_sauvegarde(DATA_FILE)

if not df.empty:
    if "Cycles Finis" not in df.columns: df["Cycles Finis"] = 0
    if "Objectif Khatmas" not in df.columns: df["Objectif Khatmas"] = 1

st.set_page_config(page_title="Bilan Coran", layout="wide")

# --- 6. AUTHENTIFICATION ---
if not st.session_state["auth"]:
    st.title(L["acces"])
    saisie = st.text_input(L["code_label"], type="password")
    if st.button(L["btn_unlock"]):
        if saisie == st.session_state["code_secret"]:
            st.session_state["auth"] = True; st.rerun()
        else:
            st.error("Code incorrect !")
    st.stop()

# --- 7. BARRE LATÉRALE ---
with st.sidebar:
    st.header("📌 Menu")
    if st.session_state["page_params"]:
        if st.button(L["home_btn"], use_container_width=True):
            st.session_state["page_params"] = False; st.rerun()
    if st.button(L["params"], use_container_width=True):
        st.session_state["page_params"] = True; st.rerun()
    st.divider()
    btn_label = L["mode_norm_btn"] if st.session_state["ramadan_mode"] else L["mode_ram_btn"]
    if st.button(btn_label, use_container_width=True):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]
        st.session_state["page_params"] = False; st.rerun()
    st.divider()
    if st.button(L["btn_logout"], use_container_width=True):
        st.session_state["auth"] = False; st.rerun()

# --- 8. PAGE CONFIGURATION ---
if st.session_state["page_params"]:
    st.title(L["titre_params"])
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🌐 Global")
        ch = st.selectbox(L["lang_btn"], list(TRAD.keys()), index=list(TRAD.keys()).index(st.session_state["langue"]))
        if ch != st.session_state["langue"]:
            st.session_state["langue"] = ch; st.rerun()
        
        st.divider()
        st.subheader("📅 Dates Ramadan")
        d_deb = st.date_input(L["date_deb"], st.session_state["debut_ramadan"])
        d_fin = st.date_input(L["date_fin"], st.session_state["fin_ramadan"])
        if st.button(L["btn_save"], key="dates"):
            st.session_state["debut_ramadan"] = d_deb
            st.session_state["fin_ramadan"] = d_fin
            pd.DataFrame({"debut": [d_deb.isoformat()], "fin": [d_fin.isoformat()]}).to_csv(CONFIG_FILE, index=False)
            st.success("Dates sauvegardées !")

        st.divider()
        st.subheader("🔑 Sécurité")
        new_p = st.text_input(L["new_pwd"], type="password")
        if st.button(L["btn_save"], key="pwd"):
            st.session_state["code_secret"] = new_p; st.success("OK")
            
        st.divider()
        with st.expander(L["info_title"]):
            st.write(f"👤 **Créateur :** {AUTHOR}")
            st.write(f"📅 **Dernière mise à jour :** {LAST_UPDATE}")
            st.write(f"🚀 **Version :** {VERSION}")

    with c2:
        st.subheader("👥 Profils")
        nom_s = st.text_input(L["add_pre"])
        if st.button(L["btn_add"]):
            if nom_s and nom_s not in df.index:
                df.loc[nom_s] = [1, 10, 0, 1]; df.to_csv(DATA_FILE); st.rerun()
        if not df.empty:
            st.divider()
            cible = st.selectbox(L["del_pre"], df.index)
            if st.button(L["btn_del"]):
                df = df.drop(cible); df.to_csv(DATA_FILE); st.rerun()
    st.stop()

# --- 9. PAGE ACCUEIL ---
st.title(f"{L['titre_ram'] if st.session_state['ramadan_mode'] else L['titre_norm']}")

aujourdhui = date.today()
if st.session_state["ramadan_mode"]:
    if aujourdhui < st.session_state["debut_ramadan"]:
        diff = (st.session_state["debut_ramadan"] - aujourdhui).days
        st.info(L["avant_ram"].format(diff))
    elif aujourdhui <= st.session_state["fin_ramadan"]:
        diff = (st.session_state["fin_ramadan"] - aujourdhui).days
        st.success(L["pendant_ram"].format(diff))

if not df.empty:
    st.subheader(L["etat"])
    recap = df.copy()
    if st.session_state["ramadan_mode"]:
        recap[L["col_prog"]] = (((recap["Page Actuelle"] + (recap["Cycles Finis"] * 604)) / (recap["Objectif Khatmas"] * 604)) * 100).round(1).astype(str) + "%"
    else:
        recap[L["col_prog"]] = (recap["Page Actuelle"] / 604 * 100).round(1).astype(str) + "%"
    for c in ["Page Actuelle", "Cycles Finis"]: recap[c] = recap[c].astype(int)
    recap["Rythme"] = recap["Rythme"].apply(lambda x: int(x) if x == int(x) else round(x, 1))
    st.table(recap)

    with st.expander(L["view_prog"]):
        for nom, row in df.iterrows():
            total = row["Objectif Khatmas"] * 604 if st.session_state["ramadan_mode"] else 604
            lu = (row["Page Actuelle"] + (row["Cycles Finis"] * 604)) if st.session_state["ramadan_mode"] else row["Page Actuelle"]
            st.write(f"**{nom}** ({int(min(1.0, lu/total)*100)}%)")
            st.progress(min(1.0, lu/total))

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1: 
        with st.expander(L["exp_msg"]):
            date_c = st.date_input(L["echeance"], aujourdhui + timedelta(days=1))
            jours = (date_c - aujourdhui).days
            msg = f"*Bilan {date_c.strftime('%d/%m')}* :\n\n"
            for n, r in df.iterrows():
                p = (int(r["Page Actuelle"]) + (int(r["Rythme"]) * jours)) % 604 or 1
                msg += f"• *{n.upper()}* : p.{int(p)}\n"
            st.text_area(L["copier"], value=msg, height=150)
    with col2: 
        with st.expander(L["exp_maj"]):
            user = st.selectbox(L["pers"], df.index, key="up")
            p_act = st.number_input(L["pg_act"], 1, 604, int(df.loc[user, "Page Actuelle"]))
            if st.session_state["ramadan_mode"]:
                k_obj = st.number_input(L["khatma"], 1, 10, int(df.loc[user, "Objectif Khatmas"]))
                c_finis = st.number_input("Khatmas finies", 0, 10, int(df.loc[user, "Cycles Finis"]))
                j_rest = max(1, (st.session_state["fin_ramadan"] - aujourdhui).days)
                if st.button(L["btn_save"], key="save_r"):
                    pages_rest = (k_obj * 604) - (p_act + (c_finis * 604))
                    nouveau_rythme = max(1, round(pages_rest / j_rest, 1))
                    df.loc[user] = [p_act, nouveau_rythme, c_finis, k_obj]; df.to_csv(DATA_FILE); st.rerun()
            else:
                r_act = st.number_input(L["rythme"], 1, 100, int(df.loc[user, "Rythme"]))
                if st.button(L["btn_save"], key="save_n"):
                    df.loc[user, ["Page Actuelle", "Rythme"]] = [p_act, r_act]; df.to_csv(DATA_FILE); st.rerun()
    with col3: 
        with st.expander(L["exp_prec"]):
            u_adj = st.selectbox(L["pers"], df.index, key="adj")
            d_adj = st.date_input(L["date_prec"], aujourdhui)
            p_adj = st.number_input(L["pg_date"], 1, 604)
            if st.button(L["btn_recalc"]):
                delta = (aujourdhui - d_adj).days
                nouv_p = (p_adj + (int(df.loc[u_adj, "Rythme"]) * delta)) % 604 or 1
                df.loc[u_adj, "Page Actuelle"] = int(nouv_p); df.to_csv(DATA_FILE); st.rerun()
        if st.session_state["ramadan_mode"]:
            st.divider()
            if st.button(L["hadith_btn"], use_container_width=True):
                h_txt, h_src = charger_hadith_aleatoire(st.session_state["langue"])
                st.session_state["h_msg"] = f"✨ *Hadith du jour* :\n\n{h_txt}\n\n📚 Source : {h_src}"
            if "h_msg" in st.session_state: st.text_area(L["copier"], value=st.session_state["h_msg"], height=150)
    st.divider()
    st.subheader(L["plan"])
    plan_df = pd.DataFrame(index=[(aujourdhui + timedelta(days=i)).strftime("%d/%m") for i in range(30)])
    for n, r in df.iterrows():
        plan_df[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 1) for i in range(30)]
    st.dataframe(plan_df, use_container_width=True)
else: st.info(L["info"])