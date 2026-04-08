import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
from fpdf import FPDF

# --- FONCTION DE GÉNÉRATION DU PDF (VERSION FINALE) ---
def generer_pdf(patient_nom, r_carieux, r_paro, diversite):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    # Titre et contenu
    pdf.cell(200, 10, txt="OralBiome - Rapport Patient", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Patient : {patient_nom}", ln=True)
    pdf.cell(200, 10, txt=f"Date : {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Risque Carieux : {r_carieux}", ln=True)
    pdf.cell(200, 10, txt=f"Risque Parodontal : {r_paro}", ln=True)
    pdf.cell(200, 10, txt=f"Score de Diversite : {diversite}/100", ln=True)
    
    # On génère le PDF en format bytes pour Streamlit
    pdf_output = pdf.output()
    if isinstance(pdf_output, str):
        return pdf_output.encode('latin-1')
    return bytes(pdf_output)

# --- CONFIGURATION ---
st.set_page_config(page_title="OralBiome - Praticien", page_icon="🦷", layout="wide")

# --- INITIALISATION DE LA MÉMOIRE ---
if 'utilisateur_connecte' not in st.session_state:
    st.session_state.utilisateur_connecte = False

if 'dossiers_patients' not in st.session_state:
    st.session_state.dossiers_patients = {}
    df_exemple = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversité (%)", "Status"])
    df_exemple.loc[0] = ["12/10/2023", "Examen Initial", 4.2, 0.8, 45, "🔴 Alerte"]
    st.session_state.dossiers_patients["Patient 001 - Jean Dupont"] = df_exemple

# ==========================================
# ÉCRAN DE CONNEXION (SI NON CONNECTÉ)
# ==========================================
if not st.session_state.utilisateur_connecte:
    col_vide1, col_centre, col_vide2 = st.columns([1, 1, 1])
    with col_centre:
        st.write("") 
        st.write("")
        try:
            logo_image = Image.open("image_19.png")
            st.image(logo_image, use_container_width=True) 
        except FileNotFoundError:
            st.markdown("<h1 style='text-align: center;'>🦷 OralBiome</h1>", unsafe_allow_html=True)
            
        st.markdown("<h3 style='text-align: center;'>Portail Praticien</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        email_saisi = st.text_input("Adresse Email Professionnelle")
        mdp_saisi = st.text_input("Mot de passe", type="password")
        
        if st.button("Se connecter à mon espace", use_container_width=True):
            if email_saisi == "contact@oralbiome.com" and mdp_saisi == "mvp2024":
                st.session_state.utilisateur_connecte = True
                st.rerun()
            else:
                st.error("Identifiants incorrects.")

# ==========================================
# APPLICATION PRINCIPALE (SI CONNECTÉ)
# ==========================================
else:
    try:
        logo_image = Image.open("image_19.png")
        st.sidebar.image(logo_image, use_container_width=True) 
    except FileNotFoundError:
        st.sidebar.title("🦷 OralBiome")

    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
        st.session_state.utilisateur_connecte = False
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.header("Recherche Patient")
    patient_id = st.sidebar.text_input("Nom ou ID du patient", "Patient 001 - Jean Dupont")

    if patient_id not in st.session_state.dossiers_patients:
        st.session_state.dossiers_patients[patient_id] = pd.DataFrame(
            columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversité (%)", "Status"]
        )

    st.sidebar.markdown("---")
    st.sidebar.header("🔬 Analyse Rapide")
    s_mutans = st.sidebar.slider("S. mutans (%)", 0.0, 10.0, 2.5, step=0.1)
    p_gingivalis = st.sidebar.slider("P. gingivalis (%)", 0.0, 5.0, 0.3, step=0.1)
    diversite = st.sidebar.slider("Diversité Globale", 0, 100, 75)

    risque_carieux = "Élevé" if s_mutans > 3.0 else "Faible"
    risque_paro = "Élevé" if p_gingivalis > 0.5 else "Faible"

    st.title(f"Dossier Médical : {patient_id}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Risque Carieux", risque_carieux, "Alerte" if risque_carieux == "Élevé" else "Normal", delta_color="inverse")
    with col2:
        st.metric("Risque Parodontal", risque_paro, "Alerte" if risque_paro == "Élevé" else "Normal", delta_color="inverse")
    with col3:
        st.metric("Score de Diversité", f"{diversite}/100")

    st.markdown("---")

    # --- RECOMMANDATIONS & BOUTON PDF ---
    st.header("📋 Plan d'Action & Recommandations")

    if risque_carieux == "Élevé":
        st.warning("**Alerte Carieuse :** Le taux de bactéries acidogènes est trop élevé.")
    if risque_paro == "Élevé":
        st.error("**Alerte Parodontale :** Présence anormale de pathogènes du complexe rouge.")
    if diversite < 50:
        st.info("**Dysbiose Orale :** La flore bactérienne est trop pauvre pour se défendre naturellement.")
    if risque_carieux == "Faible" and risque_paro == "Faible" and diversite >= 50:
        st.success("✅ **Profil Équilibré :** Le microbiome du patient est protecteur.")

    # LE BOUTON DE TÉLÉCHARGEMENT
    st.markdown("<br>", unsafe_allow_html=True)
    pdf_bytes = generer_pdf(patient_id, risque_carieux, risque_paro, diversite)
    
    st.download_button(
        label="📄 Télécharger le Rapport Patient (PDF)",
        data=pdf_bytes,
        file_name=f"OralBiome_Rapport_{patient_id}.pdf",
        mime="application/pdf",
        type="primary"
    )

    st.markdown("---")

    st.header("📂 Historique du patient")
    st.dataframe(st.session_state.dossiers_patients[patient_id], use_container_width=True, hide_index=True)

    st.markdown("#### Ajouter une intervention au dossier")
    with st.form("formulaire_ajout"):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            nouvelle_date = st.date_input("Date", date.today())
            nouvel_acte = st.selectbox("Intervention", ["Examen Initial", "Détartrage", "Soin Carie", "Surfaçage", "Contrôle"])
        with col_f2:
            nouv_s = st.number_input("S. mutans mesuré", min_value=0.0, max_value=10.0, value=s_mutans, step=0.1)
            nouv_p = st.number_input("P. gingivalis mesuré", min_value=0.0, max_value=5.0, value=p_gingivalis, step=0.1)
        with col_f3:
            nouv_div = st.number_input("Diversité mesurée", min_value=0, max_value=100, value=diversite)
            st.markdown("<br>", unsafe_allow_html=True)
            bouton_ajout = st.form_submit_button("Sauvegarder dans l'historique", use_container_width=True)

        if bouton_ajout:
            nouveau_statut = "🔴 Alerte" if nouv_s > 3.0 or nouv_p > 0.5 or nouv_div < 50 else "🟢 Stable"
            nouvelle_ligne = pd.DataFrame({
                "Date": [nouvelle_date.strftime("%d/%m/%Y")], 
                "Acte / Test": [nouvel_acte], 
                "S. mutans (%)": [nouv_s], 
                "P. gingiv. (%)": [nouv_p], 
                "Diversité (%)": [nouv_div], 
                "Status": [nouveau_statut]
            })
            st.session_state.dossiers_patients[patient_id] = pd.concat(
                [st.session_state.dossiers_patients[patient_id], nouvelle_ligne], 
                ignore_index=True
            )
            st.rerun()