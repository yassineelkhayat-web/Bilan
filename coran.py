import streamlit as st
import pandas as pd
import pyrebase
from datetime import date, timedelta
import random
import os

# --- INITIALISATION FIREBASE ---
firebaseConfig = {
    "apiKey": st.secrets["firebase"]["apiKey"],
    "authDomain": st.secrets["firebase"]["authDomain"],
    "projectId": st.secrets["firebase"]["projectId"],
    "storageBucket": st.secrets["firebase"]["storageBucket"],
    "messagingSenderId": st.secrets["firebase"]["messagingSenderId"],
    "appId": st.secrets["firebase"]["appId"],
    "databaseURL": st.secrets["firebase"]["databaseURL"]
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

# --- SESSION STATE ---
if "user" not in st.session_state: st.session_state["user"] = None
if "ramadan_mode" not in st.session_state: st.session_state["ramadan_mode"] = False
if "langue" not in st.session_state: st.session_state["langue"] = "Français"

# --- TRADUCTIONS ---
TRAD = {
    "Français": {
        "titre_norm": "📖 Bilan de Lecture", "titre_ram": "🌙 Mode Ramadan Pro",
        "login": "Connexion", "signup": "Inscription (Email)", "forgot": "Mdp oublié ?",
        "email": "Adresse Email :", "pass": "Mot de passe :", "btn_send": "Valider",
        "btn_reset": "Envoyer lien de récupération", "btn_logout": "🔒 Déconnexion",
        "hadith_btn": "GÉNÉRER MESSAGE HADITH", "exp_msg": "💬 WhatsApp",
        "plan": "📅 Planning 30 jours", "etat": "📊 Mon État"
    },
    "العربية": {
        "titre_norm": "📖 حصيلة القراءة", "titre_ram": "🌙 وضع رمضان",
        "login": "تسجيل الدخول", "signup": "إنشاء حساب", "forgot": "نسيت الرمز؟",
        "email": "البريد الإلكتروني :", "pass": "كلمة المرور :", "btn_send": "إرسال",
        "btn_reset": "إرسال رابط استعادة كلمة السر", "btn_logout": "🔒 خروج",
        "hadith_btn": "إنشاء رسالة حديث", "exp_msg": "💬 واتساب",
        "plan": "📅 الجدول ٣٠ يوم", "etat": "📊 حالتي"
    }
}
L = TRAD[st.session_state["langue"]]

# --- AUTHENTIFICATION ---
if st.session_state["user"] is None:
    st.title("🔐 " + L["login"])
    tab1, tab2, tab3 = st.tabs([L["login"], L["signup"], L["forgot"]])
    
    with tab1:
        e = st.text_input(L["email"], key="login_email")
        p = st.text_input(L["pass"], type="password", key="login_pass")
        if st.button(L["btn_send"], key="btn_login"):
            try:
                user = auth.sign_in_with_email_and_password(e, p)
                st.session_state["user"] = user
                st.rerun()
            except: st.error("Email ou mot de passe incorrect.")
            
    with tab2:
        e_reg = st.text_input(L["email"], key="reg_email")
        p_reg = st.text_input(L["pass"], type="password", key="reg_pass")
        if st.button(L["btn_send"], key="btn_reg"):
            try:
                auth.create_user_with_email_and_password(e_reg, p_reg)
                st.success("Compte créé ! Connectez-vous.")
            except: st.error("Erreur: Email déjà utilisé ou mot de passe trop court.")
            
    with tab3:
        e_forgot = st.text_input(L["email"], key="forgot_email")
        if st.button(L["btn_reset"]):
            try:
                auth.send_password_reset_email(e_forgot)
                st.success("Email envoyé ! Vérifie tes courriers indésirables (spams).")
            except: st.error("Email inconnu.")
    st.stop()

# --- APP PRINCIPALE ---
u_id = st.session_state["user"]['localId']
u_email = st.session_state["user"]['email']

# Sidebar
with st.sidebar:
    st.write(f"👤 {u_email}")
    if st.button(L["btn_logout"]):
        st.session_state["user"] = None
        st.rerun()
    st.divider()
    if st.button("🌙 Mode Ramadan" if not st.session_state["ramadan_mode"] else "📖 Mode Normal"):
        st.session_state["ramadan_mode"] = not st.session_state["ramadan_mode"]; st.rerun()

# Récupération données Firebase
data = db.child("users").child(u_id).get().val()
if not data:
    data = {"page": 1, "rythme": 10, "khatmas": 1, "finies": 0}
    db.child("users").child(u_id).set(data)

st.title(L["titre_ram"] if st.session_state["ramadan_mode"] else L["titre_norm"])

# Formulaire de mise à jour
with st.expander("📝 Mettre à jour mon bilan"):
    c1, c2 = st.columns(2)
    p_act = c1.number_input("Page actuelle", 1, 604, int(data["page"]))
    r_act = c2.number_input("Rythme (pages/jour)", 1, 100, int(data["rythme"]))
    if st.button("💾 Enregistrer"):
        db.child("users").child(u_id).update({"page": p_act, "rythme": r_act})
        st.success("Sauvegardé !"); st.rerun()

# Affichage État
st.subheader(L["etat"])
prog = (p_act / 604 * 100)
st.progress(prog / 100)
st.write(f"Tu es à la page **{p_act}**. Progression : **{prog:.1f}%**")

# Planning
st.subheader(L["plan"])
auj = date.today()
jours = [(auj + timedelta(days=i)).strftime("%d/%m") for i in range(15)]
pages = [(p_act + (r_act * i)) % 604 or 1 for i in range(15)]
df_plan = pd.DataFrame({"Date": jours, "Page attendue": pages})
st.dataframe(df_plan, use_container_width=True)

# WhatsApp
st.divider()
with st.expander(L["exp_msg"]):
    msg = f"*Bilan Coran ({u_email})*\nPage actuelle : {p_act}\nObjectif demain : {(p_act + r_act)%604}"
    st.text_area("Copier pour WhatsApp :", msg)
