import streamlit as st
import time

st.set_page_config(page_title="Site en maintenance", layout="centered")

# --- STYLE BASIQUE ---
st.markdown("""
    <style>
    .reportview-container {
        background: #f0f2f6; /* Couleur de fond Streamlit par défaut */
    }
    .main .block-container {
        padding-top: 5rem;
        padding-bottom: 5rem;
    }
    h1 {
        color: #047857; /* Couleur principale de ton app */
        text-align: center;
        font-size: 3em;
        margin-bottom: 0.5em;
    }
    h3 {
        color: #C5A059; /* Couleur secondaire de ton app */
        text-align: center;
        font-size: 1.5em;
        margin-bottom: 2em;
    }
    p {
        color: #333333;
        text-align: center;
        font-size: 1.1em;
        line-height: 1.6;
    }
    .stAlert {
        text-align: left;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONTENU DE LA PAGE ---

st.title("🚧 Site en Maintenance 🚧")

st.info("Merci de votre patience !")

st.markdown("### Cher(e) utilisateur(trice),")

st.markdown("""
    <p>
    Nous effectuons actuellement une <b>mise à jour importante</b> de l'application
    afin d'améliorer ses fonctionnalités et sa sécurité.
    </p>
    <p>
    Pendant cette période, il se peut que le site ne soit pas accessible
    ou que les données ne soient pas à jour.
    </p>
    <p>
    Nous mettons tout en œuvre pour rétablir le service au plus vite.<br>
    Revenez nous voir très bientôt !
    </p>
    <br>
    <p>
    L'équipe de support.
    </p>
""", unsafe_allow_html=True)

# --- Animation simple pour montrer que le site n'est pas "figé" ---
progress_text = "Chargement des améliorations en cours..."
my_bar = st.progress(0, text=progress_text)

for percent_complete in range(100):
    time.sleep(0.05)
    my_bar.progress(percent_complete + 1, text=progress_text)
my_bar.empty()

st.success("Opération presque terminée ! ✨")
