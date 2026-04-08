import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="OralBiome - Connexion", page_icon="🦷", layout="wide")

# --- INITIALISATION DE LA MÉMOIRE ---
# 1. Gestion de la connexion
if 'utilisateur_connecte' not in st.session_state:
    st.session_state.utilisateur_connecte = False

# 2. Base de données patients (chargée uniquement si nécessaire)
if 'dossiers_patients' not in st.session_state:
    st.session_state.dossiers_patients = {}
    df_exemple = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversité (%)", "Status"])
    df_exemple.loc[0] = ["12/10/2023", "Examen Initial", 4.2, 0.8, 45, "🔴 Alerte"]
    df_exemple.loc[1] = ["15/11/2023", "Détartrage", 3.1, 0.4, 52, "🔴 Alerte"]
    df_exemple.loc[2] = ["20/01/2024", "Soin Carie", 2.8, 0.2, 68, "🟢 Stable"]
    st.session_state.dossiers_patients["Patient 001 - Jean Dupont"] = df_exemple


# ==========================================
# ÉCRAN DE CONNEXION (SI NON CONNECTÉ)
# ==========================================
if not st.session_state.utilisateur_connecte:
    
    # Création d'une mise en page centrée pour faire un beau formulaire
    col_vide1, col_centre, col_vide2 = st.columns([1, 1, 1])
    
    with col_centre:
        st.write("") # Espace en haut
        st.write("")
        
        # Affichage du logo centré
        try:
            logo_image = Image.open("image_19.png")
            st.image(logo_image, use_container_width=True) 
        except FileNotFoundError:
            st.markdown("<h1 style='text-align: center;'>🦷 OralBiome</h1>", unsafe_allow_html=True)
            
        st.markdown("<h3 style='text-align: center;'>Portail Praticien</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Le formulaire de connexion
        email_saisi = st.text_input("Adresse Email Professionnelle")
        mdp_saisi = st.text_input("Mot de passe", type="password") # Cache les caractères
        
        bouton_connexion = st.button("Se connecter à mon espace", use_container_width=True)
        
        # Vérification des identifiants (Les "clés" du MVP)
        if bouton_connexion:
            if email_saisi == "contact@oralbiome.com" and mdp_saisi == "mvp2024":
                # Succès : On change le statut et on relance la page
                st.session_state.utilisateur_connecte = True
                st.rerun()
            else:
                # Échec
                st.error("Identifiants incorrects. Veuillez réessayer.")


# ==========================================
# APPLICATION PRINCIPALE (SI CONNECTÉ)
# ==========================================
else:
    # --- BARRE LATÉRALE ---
    try:
        logo_image = Image.open("image_19.png")
        st.sidebar.image(logo_image, use_container_width=True) 
    except FileNotFoundError:
        st.sidebar.title("🦷 OralBiome")

    st.sidebar.markdown("---")
    
    # BOUTON DE DÉCONNEXION
    if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
        st.session_state.utilisateur_connecte = False
        st.rerun()
        
    st.sidebar.markdown("---")
    
    st.sidebar.header("Recherche Patient")
    patient_id = st.sidebar.text_input("Nom ou ID du patient", "Patient 001 - Jean Dupont")

    # Si le patient n'existe pas encore, on lui crée un dossier vide
    if patient_id not in st.session_state.dossiers_patients:
        st.session_state.dossiers_patients[patient_id] = pd.DataFrame(
            columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversité (%)", "Status"]
        )

    st.sidebar.markdown("---")
    st.sidebar.header("🔬 Analyse Rapide (Test du jour)")
    s_mutans = st.sidebar.slider("S. mutans (%)", 0.0, 10.0, 2.5, step=0.1)
    p_gingivalis = st.sidebar.slider("P. gingivalis (%)", 0.0, 5.0, 0.3, step=0.1)
    diversite = st.sidebar.slider("Diversité Globale", 0, 100, 75)

    risque_carieux = "Élevé" if s_mutans > 3.0 else "Faible"
    risque_paro = "Élevé" if p_gingivalis > 0.5 else "Faible"

    # --- TABLEAU DE BORD PRINCIPAL ---
    st.title(f"Dossier Médical : {patient_id}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Risque Carieux Actuel", risque_carieux, "Alerte" if risque_carieux == "Élevé" else "Normal", delta_color="inverse")
    with col2:
        st.metric("Risque Parodontal Actuel", risque_paro, "Alerte" if risque_paro == "Élevé" else "Normal", delta_color="inverse")
    with col3:
        st.metric("Score de Diversité Actuel", f"{diversite}/100")

    st.markdown("---")

    # --- RECOMMANDATIONS ---
    st.header("📋 Plan d'Action & Recommandations")

    if risque_carieux == "Élevé":
        st.warning("**Alerte Carieuse :** Le taux de bactéries acidogènes est trop élevé. \n* **Nutrition :** Réduire drastiquement les glucides fermentescibles et collants. \n* **Hygiène :** Prescrire un protocole anti-acide et un dentifrice reminéralisant spécifique.")
    if risque_paro == "Élevé":
        st.error("**Alerte Parodontale :** Présence anormale de pathogènes du complexe rouge. \n* **Clinique :** Évaluer la nécessité d'un surfaçage radiculaire. \n* **Hygiène :** Utilisation stricte de brossettes interdentaires et d'un bain de bouche ciblé.")
    if diversite < 50:
        st.info("**Dysbiose Orale :** La flore bactérienne est trop pauvre pour se défendre naturellement. \n* **Probiotiques :** Suggérer une cure de probiotiques oraux pendant 30 jours.")
    if risque_carieux == "Faible" and risque_paro == "Faible" and diversite >= 50:
        st.success("✅ **Profil Équilibré :** Le microbiome du patient est protecteur. Maintenir la routine actuelle.")

    st.markdown("---")

    # --- DOSSIER PATIENT LONGITUDINAL ---
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