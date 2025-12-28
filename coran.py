import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import random

# --- 1. CONFIGURATION INITIALE & SESSION ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if "user_connected" not in st.session_state: st.session_state["user_connected"] = None
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "ramadan_mode" not in st.session_state: st.session_state["ramadan_mode"] = False
if "page_params" not in st.session_state: st.session_state["page_params"] = False
if "langue" not in st.session_state: st.session_state["langue"] = "Français"

VERSION = "4.2"
LAST_UPDATE = "28/12/2025" 
AUTHOR = "Yael"

# --- 2. GESTION DES FICHIERS ET DATA ---
dossier = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(dossier, "config_dates.csv")
USERS_FILE = os.path.join(dossier, "users.csv")

# Initialisation du fichier des utilisateurs (Comptes)
if not os.path.exists(USERS_FILE):
    df_users = pd.DataFrame([["Yael", "Yassine05", "Admin"]], columns=["pseudo", "password", "role"])
    df_users.to_csv(USERS_FILE, index=False)
else:
    df_users = pd.read_csv(USERS_FILE)

# Chargement des dates du Ramadan
if os.path.exists(CONFIG_FILE):
    conf_df = pd.read_csv(CONFIG_FILE)
    st.session_state["debut_ramadan"] = date.fromisoformat(conf_df.iloc[0]["debut"])
    st.session_state["fin_ramadan"] = date.fromisoformat(conf_df.iloc[0]["fin"])
else:
    st.session_state["debut_ramadan"] = date(2025, 3, 1)
    st.session_state["fin_ramadan"] = date(2025, 3, 30)

def verifier_et_creer_sauvegarde(fichier_cible):
    if not os.path.exists(fichier_cible):
        df_vide = pd.DataFrame(columns=["Page Actuelle", "Rythme", "Cycles Finis", "Objectif Khatmas"])
        df_vide.index.name = "Nom"
        # On n'ajoute que Yael au départ
        df_vide.loc["Yael"] = [1, 10, 0, 1]
        df_vide.to_csv(fichier_cible)
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
        return "Fichier de hadiths manquant.", "Info"
    except Exception as e: return f"Erreur: {str(e)}", "Erreur"

# --- 3. TRADUCTIONS ---
TRAD = {
    "Français": {
        "titre_norm": "📖 Bilan de Lecture", "titre_ram": "🌙 Mode Ramadan Pro", "titre_params": "⚙️ Configuration",
        "acces": "🔐 Connexion", "user_label": "Pseudo :", "code_label": "Mot de passe :", "btn_unlock": "Se connecter",
        "params": "Paramètres", "add_pre": "Nouveau membre :", "new_mdp": "Mot de passe :", "btn_add": "➕ Créer le compte",
        "del_pre": "Supprimer un profil :", "btn_del": "🗑️ Supprimer", "btn_logout": "🔒 Déconnexion",
        "etat": "📊 État actuel", "col_prog": "Progression", "exp_msg": "💬 Générer message",
        "echeance": "Échéance :", "copier": "Copier :", "exp_maj": "📝 Mise à jour",
        "pers": "Personne :", "pg_act": "Page actuelle :", "rythme": "Rythme :",
        "btn_save": "💾 Enregistrer", "exp_prec": "🔄 Date précise", "date_prec": "Date :",
        "pg_date": "Page à cette date :", "btn_recalc": "⚙️ Recalculer", "plan": "📅 Planning 30 jours",
        "lang_btn": "🌐 Langue / لغة", "mode_ram_btn": "Mode Ramadan", "mode_norm_btn": "Mode Normal",
        "hadith_btn": "GÉNÉRER MESSAGE HADITH", "khatma": "Objectif Khatmas",
        "home_btn": "🏠 Accueil", "info": "Aucun profil disponible.",
        "view_prog": "📊 Voir la progression visuelle",
        "avant_ram": "Il reste {} jours avant le début du Ramadan",
        "pendant_ram": "Il reste {} jours avant la fin du Ramadan",
        "date_deb": "Début du Ramadan :", "date_fin": "Fin du Ramadan :",
        "info_title": "ℹ️ Infos Logiciel"
    },
    "العربية": {
        "titre_norm": "📖 حصيلة القراءة", "titre_ram": "🌙 وضع رمضان", "titre_params": "⚙️ الإعدادات",
        "acces": "🔐 دخول", "user_label": "الاسم :", "code_label": "كلمة المرور :", "btn_unlock": "دخول",
        "params": "الإعدادات", "add_pre": "عضو جديد :", "new_mdp": "كلمة المرور :", "btn_add": "إضافة +",
        "del_pre": "حذف ملف :", "btn_del": "🗑️ حذف", "btn_logout": "🔒 خروج",
        "etat": "📊 الحالة الراهنة", "col_prog": "التقدم", "exp_msg": "💬 إنشاء رسالة",
        "echeance": "الموعد :", "copier": "نسخ :", "exp_maj": "📝 تحديث",
        "pers": "الشخص :", "pg_act": "الصفحة الحالية :", "rythme": "المعدل :",
        "btn_save": "💾 حفظ", "exp_prec": "🔄 تاريخ دقيق", "date_prec": "التاريخ :",
        "pg_date": "الورقة في هذا التاريخ :", "btn_recalc": "⚙️ إعادة الحساب", "plan": "📅 الجدول",
        "lang_btn": "🌐 اللغة", "mode_ram_btn": "وضع رمضان", "mode_norm_btn": "الوضع العادي",
        "hadith_btn": "إنشاء رسالة حديث", "khatma": "هدف الختمات",
        "home_btn": "🏠 الرئيسية", "info": "لا يوجد ملفات.",
        "view_prog": "📊 عرض التقدم",
        "avant_ram": "متبقي {} أيام على رمضان",
        "pendant_ram": "متبقي {} أيام على نهاية رمضان",
        "date_deb": "بداية رمضان :", "date_fin": "نهاية رمضان :",
        "info_title": "ℹ️ معلومات"
    }
}

L = TRAD.get(st.session_state["langue"], TRAD["Français"])

# --- 4. CHARGEMENT DATA ---
suffixe = "ramadan" if st.session_state["ramadan_mode"] else "lecture"
DATA_FILE = os.path.join(dossier, f"sauvegarde_{suffixe}.csv")
df = verifier_et_creer_sauvegarde(DATA_FILE)

# Nettoyage des colonnes si besoin
if not df.empty:
    if "Cycles Finis" not in df.columns: df["Cycles Finis"] = 0
    if "Objectif Khatmas" not in df.columns: df["Objectif Khatmas"] = 1

# --- 5. STYLE & CONFIG ---
COLOR = "#C5A059" if st.session_state["ramadan_mode"] else "#047857"
st.set_page_config(page_title="Bilan Coran", layout="wide")
st.markdown(f"""<style>
    .stApp {{ background-color: #FFFFFF; }}
    h1, h2, h3, p, label, span {{ color: {COLOR} !important; }}
    div.stButton > button {{ background-color: #FFFFFF !important; color: {COLOR} !important; border: 2px solid {COLOR} !important; border-radius: 10px !important; font-weight: bold !important; width: 100% !important; }}
    div.stButton > button:hover {{ background-color: {COLOR} !important; color: #FFFFFF !important; }}
    .stProgress > div > div > div > div {{ background-color: {COLOR} !important; }}
</style>""", unsafe_allow_html=True)

# --- 6. AUTHENTIFICATION ---
if not st.session_state["auth"]:
    st.title(L["acces"])
    u_in = st.text_input(L["user_label"])
    p_in = st.text_input(L["code_label"], type="password")
    if st.button(L["btn_unlock"]):
        user_match = df_users[(df_users["pseudo"] == u_in) & (df_users["password"] == p_in)]
        if not user_match.empty:
            st.session_state["auth"] = True
            st.session_state["user_connected"] = u_in
            st.session_state["is_admin"] = (user_match.iloc[0]["role"] == "Admin")
            st.rerun()
        else:
            st.error("Identifiants incorrects")
    st.stop()

# --- 7. BARRE LATÉRALE ---
with st.sidebar:
    st.header(f"👤 {st.session_state['user_connected']}")
    if st.button(L["home_btn"]): st.session_state["page_params"] = False; st.rerun()
    if st.button(L["params"]): st.session_state["page_params"] = True; st.rerun()
    st.divider()
    btn_txt = L["mode_norm_btn"] if st.session_state["ramadan_mode"] else L["mode_ram_btn"]
    if st.button(btn_txt):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]
        st.rerun()
    st.divider()
    if st.button(L["btn_logout"]):
        st.session_state["auth"] = False; st.rerun()

# --- 8. PAGE CONFIGURATION ---
if st.session_state["page_params"]:
    st.title(L["titre_params"])
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🌐 Global")
        new_lang = st.selectbox(L["lang_btn"], list(TRAD.keys()), index=list(TRAD.keys()).index(st.session_state["langue"]))
        if new_lang != st.session_state["langue"]:
            st.session_state["langue"] = new_lang; st.rerun()
        
        st.divider()
        st.subheader("📅 Dates Ramadan")
        d_deb = st.date_input(L["date_deb"], st.session_state["debut_ramadan"])
        d_fin = st.date_input(L["date_fin"], st.session_state["fin_ramadan"])
        if st.button(L["btn_save"], key="save_dates"):
            pd.DataFrame({"debut": [d_deb.isoformat()], "fin": [d_fin.isoformat()]}).to_csv(CONFIG_FILE, index=False)
            st.session_state["debut_ramadan"], st.session_state["fin_ramadan"] = d_deb, d_fin
            st.success("Dates mises à jour")

    with c2:
        if st.session_state["is_admin"]:
            st.subheader("👥 Gestion Admin")
            nom_n = st.text_input(L["add_pre"])
            pass_n = st.text_input(L["new_mdp"], type="password")
            if st.button(L["btn_add"]):
                if nom_n and nom_n not in df_users["pseudo"].values:
                    # Ajouter aux comptes
                    new_acc = pd.DataFrame([[nom_n, pass_n, "Membre"]], columns=["pseudo", "password", "role"])
                    df_users = pd.concat([df_users, new_acc], ignore_index=True)
                    df_users.to_csv(USERS_FILE, index=False)
                    # Ajouter aux données
                    df.loc[nom_n] = [1, 10, 0, 1]
                    df.to_csv(DATA_FILE)
                    st.success(f"Compte {nom_n} créé !") ; st.rerun()
            
            st.divider()
            cible = st.selectbox(L["del_pre"], [u for u in df.index if u != "Yael"])
            if st.button(L["btn_del"]):
                df_users = df_users[df_users["pseudo"] != cible]
                df_users.to_csv(USERS_FILE, index=False)
                df = df.drop(cible); df.to_csv(DATA_FILE)
                st.rerun()
        else:
            st.info("Section réservée à l'administrateur (Yael)")
    st.stop()

# --- 9. PAGE ACCUEIL ---
st.title(f"{L['titre_ram'] if st.session_state['ramadan_mode'] else L['titre_norm']}")

# Compte à rebours
aujourdhui = date.today()
if st.session_state["ramadan_mode"]:
    if aujourdhui < st.session_state["debut_ramadan"]:
        st.info(L["avant_ram"].format((st.session_state["debut_ramadan"] - aujourdhui).days))
    elif aujourdhui <= st.session_state["fin_ramadan"]:
        st.success(L["pendant_ram"].format((st.session_state["fin_ramadan"] - aujourdhui).days))

# Affichage Tableau
if not df.empty:
    st.subheader(L["etat"])
    recap = df.copy()
    total_pg = 604
    if st.session_state["ramadan_mode"]:
        recap[L["col_prog"]] = (((recap["Page Actuelle"] + (recap["Cycles Finis"] * total_pg)) / (recap["Objectif Khatmas"] * total_pg)) * 100).round(1).astype(str) + "%"
    else:
        recap[L["col_prog"]] = (recap["Page Actuelle"] / total_pg * 100).round(1).astype(str) + "%"
    st.table(recap)

    # Barres de progression visuelles
    with st.expander(L["view_prog"]):
        for nom, row in df.iterrows():
            limit = row["Objectif Khatmas"] * total_pg if st.session_state["ramadan_mode"] else total_pg
            fait = (row["Page Actuelle"] + (row["Cycles Finis"] * total_pg)) if st.session_state["ramadan_mode"] else row["Page Actuelle"]
            st.write(f"**{nom}**")
            st.progress(min(1.0, fait/limit))

    # Actions : Mise à jour / Message / Recalcul
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.expander(L["exp_maj"], expanded=True):
            # Restriction : Membre = seulement soi-même, Admin = tout le monde
            mes_choix = df.index.tolist() if st.session_state["is_admin"] else [st.session_state["user_connected"]]
            u_maj = st.selectbox(L["pers"], mes_choix, key="u_maj")
            p_n = st.number_input(L["pg_act"], 1, 604, int(df.loc[u_maj, "Page Actuelle"]))
            
            if st.session_state["ramadan_mode"]:
                k_o = st.number_input(L["khatma"], 1, 10, int(df.loc[u_maj, "Objectif Khatmas"]))
                c_f = st.number_input("Khatmas finies", 0, 10, int(df.loc[u_maj, "Cycles Finis"]))
                if st.button(L["btn_save"], key="btn_save_ram"):
                    j_r = max(1, (st.session_state["fin_ramadan"] - aujourdhui).days)
                    rythme = max(1, round(((k_o * total_pg) - (p_n + (c_f * total_pg))) / j_r, 1))
                    df.loc[u_maj] = [p_n, rythme, c_f, k_o]
                    df.to_csv(DATA_FILE); st.rerun()
            else:
                r_n = st.number_input(L["rythme"], 1, 100, int(df.loc[u_maj, "Rythme"]))
                if st.button(L["btn_save"], key="btn_save_norm"):
                    df.loc[u_maj, ["Page Actuelle", "Rythme"]] = [p_n, r_n]
                    df.to_csv(DATA_FILE); st.rerun()

    with col2:
        with st.expander(L["exp_msg"]):
            date_c = st.date_input(L["echeance"], aujourdhui + timedelta(days=1))
            nb_j = (date_c - aujourdhui).days
            msg = f"*Bilan {date_c.strftime('%d/%m')}* :\n\n"
            for n, r in df.iterrows():
                target = (int(r["Page Actuelle"]) + (int(r["Rythme"]) * nb_j)) % 604 or 1
                msg += f"• *{n.upper()}* : p.{int(target)}\n"
            st.text_area(L["copier"], value=msg, height=150)

    with col3:
        with st.expander(L["exp_prec"]):
            u_adj = st.selectbox(L["pers"], mes_choix, key="u_adj")
            d_adj = st.date_input(L["date_prec"], aujourdhui)
            p_adj = st.number_input(L["pg_date"], 1, 604)
            if st.button(L["btn_recalc"]):
                diff_j = (aujourdhui - d_adj).days
                nouv = (p_adj + (int(df.loc[u_adj, "Rythme"]) * diff_j)) % 604 or 1
                df.loc[u_adj, "Page Actuelle"] = int(nouv)
                df.to_csv(DATA_FILE); st.rerun()
        
        # Bouton Hadith (uniquement en mode Ramadan)
        if st.session_state["ramadan_mode"]:
            st.divider()
            if st.button(L["hadith_btn"]):
                h_t, h_s = charger_hadith_aleatoire(st.session_state["langue"])
                st.session_state["h_msg"] = f"✨ *Hadith* :\n\n{h_t}\n\n📚 {h_s}"
            if "h_msg" in st.session_state:
                st.text_area("Copy Hadith", st.session_state["h_msg"], height=100)

    # Planning 30 jours
    st.divider()
    st.subheader(L["plan"])
    plan_data = {}
    dates_list = [(aujourdhui + timedelta(days=i)).strftime("%d/%m") for i in range(30)]
    for n, r in df.iterrows():
        plan_data[n] = [int((int(r["Page Actuelle"]) + (int(r["Rythme"]) * i)) % 604 or 1) for i in range(30)]
    st.dataframe(pd.DataFrame(plan_data, index=dates_list), use_container_width=True)

else:
    st.info(L["info"])
