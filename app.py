import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
from fpdf import FPDF

# --- GÉNÉRATION DU PDF ---
def generer_pdf(patient_nom, r_carieux, r_paro, diversite, historique_df):
    pdf = FPDF()
    pdf.add_page()
    
    # En-tête
    pdf.set_fill_color(27, 79, 138)
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_font("Helvetica", 'B', size=18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(200, 15, txt="OralBiome - Rapport Patient", ln=True, align='C')
    pdf.set_font("Helvetica", size=10)
    pdf.cell(200, 10, txt="Microbiome Oral Predictif", ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)

    # Infos patient
    pdf.set_font("Helvetica", 'B', size=12)
    pdf.cell(200, 8, txt=f"Patient : {patient_nom}", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(200, 8, txt=f"Date du rapport : {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(8)

    # Scores
    pdf.set_font("Helvetica", 'B', size=13)
    pdf.set_fill_color(214, 228, 247)
    pdf.cell(200, 8, txt="  Resultats de l'Analyse", ln=True, fill=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", size=11)
    
    couleur_carieux = (220, 53, 69) if r_carieux == "Eleve" else (40, 167, 69)
    couleur_paro = (220, 53, 69) if r_paro == "Eleve" else (40, 167, 69)
    
    pdf.set_text_color(*couleur_carieux)
    pdf.cell(200, 8, txt=f"  Risque Carieux : {r_carieux}", ln=True)
    pdf.set_text_color(*couleur_paro)
    pdf.cell(200, 8, txt=f"  Risque Parodontal : {r_paro}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 8, txt=f"  Score de Diversite : {diversite}/100", ln=True)
    pdf.ln(8)

    # Recommandations
    pdf.set_font("Helvetica", 'B', size=13)
    pdf.set_fill_color(214, 228, 247)
    pdf.cell(200, 8, txt="  Recommandations", ln=True, fill=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", size=11)
    
    if r_carieux == "Eleve":
        pdf.set_text_color(180, 100, 0)
        pdf.multi_cell(190, 7, txt="Alerte Carieuse : Le taux de bacteries acidogenes est trop eleve. Reduire la consommation de sucres rapides, renforcer le brossage apres chaque repas.")
        pdf.ln(3)
    if r_paro == "Eleve":
        pdf.set_text_color(180, 0, 0)
        pdf.multi_cell(190, 7, txt="Alerte Parodontale : Presence anormale de pathogenes du complexe rouge. Detartrage et surfacage recommandes. Consultation parodontale a envisager.")
        pdf.ln(3)
    if diversite < 50:
        pdf.set_text_color(0, 80, 160)
        pdf.multi_cell(190, 7, txt="Dysbiose Orale : Flore bacterienne appauvrie. Probiotiques oraux recommandes. Alimentation riche en fibres et legumes fermentescibles.")
        pdf.ln(3)
    if r_carieux == "Faible" and r_paro == "Faible" and diversite >= 50:
        pdf.set_text_color(40, 167, 69)
        pdf.multi_cell(190, 7, txt="Profil Equilibre : Le microbiome du patient est protecteur. Continuer les bonnes pratiques. Controle dans 6 mois.")
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # Historique
    if not historique_df.empty:
        pdf.set_font("Helvetica", 'B', size=13)
        pdf.set_fill_color(214, 228, 247)
        pdf.cell(200, 8, txt="  Historique des Analyses", ln=True, fill=True)
        pdf.ln(4)
        
        # En-têtes tableau
        pdf.set_font("Helvetica", 'B', size=9)
        pdf.set_fill_color(27, 79, 138)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(35, 7, "Date", border=1, fill=True)
        pdf.cell(45, 7, "Acte / Test", border=1, fill=True)
        pdf.cell(30, 7, "S. mutans (%)", border=1, fill=True)
        pdf.cell(30, 7, "P. gingiv. (%)", border=1, fill=True)
        pdf.cell(25, 7, "Diversite", border=1, fill=True)
        pdf.cell(25, 7, "Status", border=1, ln=True, fill=True)
        
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(0, 0, 0)
        for i, row in historique_df.iterrows():
            fill = i % 2 == 0
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(35, 6, str(row.get("Date", "")), border=1, fill=fill)
            pdf.cell(45, 6, str(row.get("Acte / Test", "")), border=1, fill=fill)
            pdf.cell(30, 6, str(row.get("S. mutans (%)", "")), border=1, fill=fill)
            pdf.cell(30, 6, str(row.get("P. gingiv. (%)", "")), border=1, fill=fill)
            pdf.cell(25, 6, str(row.get("Diversité (%)", "")), border=1, fill=fill)
            statut = str(row.get("Status", ""))
            statut_clean = statut.replace("🔴 ", "").replace("🟢 ", "")
            pdf.cell(25, 6, statut_clean, border=1, ln=True, fill=fill)

    # Pied de page
    pdf.ln(10)
    pdf.set_font("Helvetica", 'I', size=9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(200, 6, txt="Ce rapport est fourni a titre preventif et informatif. Il ne constitue pas un diagnostic medical.", ln=True, align='C')
    pdf.cell(200, 6, txt="OralBiome - Microbiome Oral Predictif | contact@oralbiome.com", ln=True, align='C')

    pdf_output = pdf.output()
    if isinstance(pdf_output, str):
        return pdf_output.encode('latin-1')
    return bytes(pdf_output)


# --- CONFIGURATION ---
st.set_page_config(page_title="OralBiome - Praticien", page_icon="🦷", layout="wide")

# --- CSS PERSONNALISÉ ---
st.markdown("""
<style>
    .patient-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 4px 0;
        cursor: pointer;
    }
    .patient-card:hover { border-color: #1B4F8A; background: #f0f6ff; }
    .patient-card.selected { border-color: #1B4F8A; background: #D6E4F7; }
    .badge-alerte { background: #dc3545; color: white; border-radius: 4px; padding: 2px 8px; font-size: 11px; }
    .badge-stable { background: #28a745; color: white; border-radius: 4px; padding: 2px 8px; font-size: 11px; }
    .stat-box { background: #f8f9fa; border-radius: 8px; padding: 10px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- DONNÉES PAR DÉFAUT ---
def donnees_initiales():
    patients = {}
    
    # Patient 1
    df1 = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversité (%)", "Status"])
    df1.loc[0] = ["12/10/2023", "Examen Initial", 4.2, 0.8, 45, "🔴 Alerte"]
    df1.loc[1] = ["08/04/2026", "Contrôle", 4.2, 0.3, 75, "🔴 Alerte"]
    patients["Jean Dupont"] = {
        "id": "P001", "nom": "Jean Dupont", "age": 42, "email": "jean.dupont@email.com",
        "telephone": "+32 472 123 456", "date_naissance": "15/03/1982",
        "historique": df1,
        "s_mutans": 4.2, "p_gingivalis": 0.3, "diversite": 75
    }
    
    # Patient 2
    df2 = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversité (%)", "Status"])
    df2.loc[0] = ["05/01/2024", "Examen Initial", 1.2, 0.1, 82, "🟢 Stable"]
    patients["Marie Martin"] = {
        "id": "P002", "nom": "Marie Martin", "age": 35, "email": "marie.martin@email.com",
        "telephone": "+32 478 654 321", "date_naissance": "22/07/1989",
        "historique": df2,
        "s_mutans": 1.2, "p_gingivalis": 0.1, "diversite": 82
    }
    
    # Patient 3
    df3 = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversité (%)", "Status"])
    df3.loc[0] = ["18/02/2025", "Examen Initial", 6.5, 1.8, 38, "🔴 Alerte"]
    patients["Pierre Bernard"] = {
        "id": "P003", "nom": "Pierre Bernard", "age": 58, "email": "pierre.bernard@email.com",
        "telephone": "+32 495 789 012", "date_naissance": "03/11/1966",
        "historique": df3,
        "s_mutans": 6.5, "p_gingivalis": 1.8, "diversite": 38
    }
    
    return patients

# --- INITIALISATION ---
if 'utilisateur_connecte' not in st.session_state:
    st.session_state.utilisateur_connecte = False
if 'patients' not in st.session_state:
    st.session_state.patients = donnees_initiales()
if 'patient_selectionne' not in st.session_state:
    st.session_state.patient_selectionne = "Jean Dupont"
if 'vue' not in st.session_state:
    st.session_state.vue = "dossier"  # dossier | liste | nouveau

# ==========================================
# ÉCRAN DE CONNEXION
# ==========================================
if not st.session_state.utilisateur_connecte:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.write("") 
        st.write("")
        try:
            logo = Image.open("image_19.png")
            st.image(logo, use_container_width=True)
        except:
            st.markdown("<h1 style='text-align:center;'>🦷 OralBiome</h1>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align:center; color:#1B4F8A;'>Portail Praticien</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#888;'>Microbiome Oral Prédictif</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        email = st.text_input("Adresse Email Professionnelle")
        mdp = st.text_input("Mot de passe", type="password")
        
        if st.button("Se connecter à mon espace", use_container_width=True, type="primary"):
            if email == "contact@oralbiome.com" and mdp == "mvp2024":
                st.session_state.utilisateur_connecte = True
                st.rerun()
            else:
                st.error("Identifiants incorrects. Utilisez contact@oralbiome.com / mvp2024")

# ==========================================
# APPLICATION PRINCIPALE
# ==========================================
else:
    # --- SIDEBAR ---
    try:
        logo = Image.open("image_19.png")
        st.sidebar.image(logo, use_container_width=True)
    except:
        st.sidebar.markdown("## 🦷 OralBiome")
    
    st.sidebar.markdown("---")
    
    # Navigation
    col_nav1, col_nav2 = st.sidebar.columns(2)
    with col_nav1:
        if st.button("👥 Patients", use_container_width=True):
            st.session_state.vue = "liste"
            st.rerun()
    with col_nav2:
        if st.button("➕ Nouveau", use_container_width=True):
            st.session_state.vue = "nouveau"
            st.rerun()
    
    st.sidebar.markdown("---")
    
    # Statistiques rapides du cabinet
    nb_patients = len(st.session_state.patients)
    nb_alertes = sum(
        1 for p in st.session_state.patients.values()
        if p["s_mutans"] > 3.0 or p["p_gingivalis"] > 0.5 or p["diversite"] < 50
    )
    
    st.sidebar.markdown("### 📊 Mon Cabinet")
    col_s1, col_s2 = st.sidebar.columns(2)
    with col_s1:
        st.sidebar.metric("Patients", nb_patients)
    with col_s2:
        st.sidebar.metric("Alertes", nb_alertes, delta=None)
    
    st.sidebar.markdown("---")
    
    # Liste patients dans sidebar
    st.sidebar.markdown("### 🔍 Accès Rapide")
    recherche = st.sidebar.text_input("Rechercher un patient...", placeholder="Nom ou ID")
    
    patients_filtres = {
        nom: data for nom, data in st.session_state.patients.items()
        if recherche.lower() in nom.lower() or recherche.lower() in data["id"].lower()
    } if recherche else st.session_state.patients
    
    for nom, data in patients_filtres.items():
        statut_icon = "🔴" if (data["s_mutans"] > 3.0 or data["p_gingivalis"] > 0.5 or data["diversite"] < 50) else "🟢"
        label = f"{statut_icon} {data['id']} — {nom}"
        if st.sidebar.button(label, use_container_width=True, 
                              type="primary" if nom == st.session_state.patient_selectionne else "secondary"):
            st.session_state.patient_selectionne = nom
            st.session_state.vue = "dossier"
            st.rerun()
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
        st.session_state.utilisateur_connecte = False
        st.rerun()

    # ==========================================
    # VUE : LISTE DES PATIENTS
    # ==========================================
    if st.session_state.vue == "liste":
        st.title("👥 Gestion des Patients")
        st.markdown(f"**{nb_patients} patients** dans votre cabinet · **{nb_alertes} alertes actives**")
        st.markdown("---")
        
        # Filtres
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtre_statut = st.selectbox("Filtrer par statut", ["Tous", "Alerte uniquement", "Stable uniquement"])
        with col_f2:
            tri = st.selectbox("Trier par", ["Nom", "ID", "Diversité (croissante)", "Risque (décroissant)"])
        with col_f3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Nouveau Patient", type="primary"):
                st.session_state.vue = "nouveau"
                st.rerun()
        
        st.markdown("---")
        
        # Tableau patients
        donnees_tableau = []
        for nom, data in st.session_state.patients.items():
            en_alerte = data["s_mutans"] > 3.0 or data["p_gingivalis"] > 0.5 or data["diversite"] < 50
            if filtre_statut == "Alerte uniquement" and not en_alerte:
                continue
            if filtre_statut == "Stable uniquement" and en_alerte:
                continue
            
            r_carieux = "⚠️ Élevé" if data["s_mutans"] > 3.0 else "✅ Faible"
            r_paro = "⚠️ Élevé" if data["p_gingivalis"] > 0.5 else "✅ Faible"
            statut = "🔴 Alerte" if en_alerte else "🟢 Stable"
            nb_visites = len(data["historique"])
            
            donnees_tableau.append({
                "ID": data["id"],
                "Nom": nom,
                "Âge": data["age"],
                "Risque Carieux": r_carieux,
                "Risque Parodontal": r_paro,
                "Diversité": f"{data['diversite']}/100",
                "Statut": statut,
                "Visites": nb_visites
            })
        
        if donnees_tableau:
            df_tableau = pd.DataFrame(donnees_tableau)
            st.dataframe(df_tableau, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("**Ouvrir un dossier :**")
            cols = st.columns(min(len(st.session_state.patients), 4))
            for i, (nom, data) in enumerate(st.session_state.patients.items()):
                with cols[i % 4]:
                    en_alerte = data["s_mutans"] > 3.0 or data["p_gingivalis"] > 0.5 or data["diversite"] < 50
                    icon = "🔴" if en_alerte else "🟢"
                    if st.button(f"{icon} {nom}", use_container_width=True):
                        st.session_state.patient_selectionne = nom
                        st.session_state.vue = "dossier"
                        st.rerun()
        else:
            st.info("Aucun patient correspond aux filtres sélectionnés.")

    # ==========================================
    # VUE : NOUVEAU PATIENT
    # ==========================================
    elif st.session_state.vue == "nouveau":
        st.title("➕ Nouveau Patient")
        st.markdown("---")
        
        with st.form("formulaire_nouveau_patient"):
            st.markdown("### Informations Personnelles")
            col1, col2 = st.columns(2)
            with col1:
                nouveau_nom = st.text_input("Nom complet *", placeholder="Ex: Sophie Lambert")
                nouvel_email = st.text_input("Email", placeholder="patient@email.com")
                nouvelle_ddn = st.date_input("Date de naissance", value=date(1985, 1, 1))
            with col2:
                nouvel_age = st.number_input("Âge", min_value=1, max_value=120, value=35)
                nouveau_tel = st.text_input("Téléphone", placeholder="+32 4XX XXX XXX")
            
            st.markdown("---")
            st.markdown("### Première Analyse (optionnel)")
            col3, col4, col5 = st.columns(3)
            with col3:
                init_s = st.number_input("S. mutans (%)", 0.0, 10.0, 2.0, step=0.1)
            with col4:
                init_p = st.number_input("P. gingivalis (%)", 0.0, 5.0, 0.2, step=0.1)
            with col5:
                init_div = st.number_input("Diversité (%)", 0, 100, 70)
            
            ajouter_analyse = st.checkbox("Enregistrer cette analyse comme examen initial", value=True)
            
            st.markdown("---")
            soumettre = st.form_submit_button("✅ Créer le dossier patient", use_container_width=True, type="primary")
            
            if soumettre:
                if not nouveau_nom.strip():
                    st.error("Le nom du patient est obligatoire.")
                elif nouveau_nom in st.session_state.patients:
                    st.error(f"Un patient nommé '{nouveau_nom}' existe déjà.")
                else:
                    # Générer ID
                    nb_existants = len(st.session_state.patients)
                    nouvel_id = f"P{str(nb_existants + 1).zfill(3)}"
                    
                    # Créer historique
                    df_nouveau = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversité (%)", "Status"])
                    if ajouter_analyse:
                        statut_init = "🔴 Alerte" if init_s > 3.0 or init_p > 0.5 or init_div < 50 else "🟢 Stable"
                        df_nouveau.loc[0] = [date.today().strftime("%d/%m/%Y"), "Examen Initial", init_s, init_p, init_div, statut_init]
                    
                    st.session_state.patients[nouveau_nom] = {
                        "id": nouvel_id,
                        "nom": nouveau_nom,
                        "age": nouvel_age,
                        "email": nouvel_email,
                        "telephone": nouveau_tel,
                        "date_naissance": nouvelle_ddn.strftime("%d/%m/%Y"),
                        "historique": df_nouveau,
                        "s_mutans": init_s if ajouter_analyse else 0.0,
                        "p_gingivalis": init_p if ajouter_analyse else 0.0,
                        "diversite": init_div if ajouter_analyse else 70
                    }
                    
                    st.session_state.patient_selectionne = nouveau_nom
                    st.session_state.vue = "dossier"
                    st.success(f"✅ Dossier créé pour {nouveau_nom} ({nouvel_id})")
                    st.rerun()

    # ==========================================
    # VUE : DOSSIER PATIENT
    # ==========================================
    else:
        patient = st.session_state.patients.get(st.session_state.patient_selectionne)
        
        if not patient:
            st.error("Patient introuvable.")
        else:
            s_mutans = patient["s_mutans"]
            p_gingivalis = patient["p_gingivalis"]
            diversite = patient["diversite"]
            
            risque_carieux = "Élevé" if s_mutans > 3.0 else "Faible"
            risque_paro = "Élevé" if p_gingivalis > 0.5 else "Faible"
            en_alerte = risque_carieux == "Élevé" or risque_paro == "Élevé" or diversite < 50
            
            # En-tête patient
            col_titre, col_actions = st.columns([3, 1])
            with col_titre:
                statut_badge = "🔴 En Alerte" if en_alerte else "🟢 Stable"
                st.markdown(f"## 🦷 {patient['nom']} `{patient['id']}` &nbsp; {statut_badge}", unsafe_allow_html=False)
                st.caption(f"Âge : {patient['age']} ans · {patient['email']} · {patient['telephone']}")
            with col_actions:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✏️ Modifier le profil", use_container_width=True):
                    st.session_state.vue = "modifier"
                    st.rerun()
            
            st.markdown("---")
            
            # Métriques
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Risque Carieux", risque_carieux,
                          "⚠️ Alerte" if risque_carieux == "Élevé" else "✅ Normal",
                          delta_color="inverse")
            with col2:
                st.metric("Risque Parodontal", risque_paro,
                          "⚠️ Alerte" if risque_paro == "Élevé" else "✅ Normal",
                          delta_color="inverse")
            with col3:
                st.metric("Score de Diversité", f"{diversite}/100")
            with col4:
                st.metric("Nb. de Visites", len(patient["historique"]))
            
            st.markdown("---")
            
            # Onglets
            tab1, tab2, tab3 = st.tabs(["📋 Recommandations & PDF", "📂 Historique", "🔬 Mise à jour Analyse"])
            
            with tab1:
                st.header("📋 Plan d'Action & Recommandations")
                if risque_carieux == "Élevé":
                    st.warning("**Alerte Carieuse :** Le taux de bactéries acidogènes est trop élevé.")
                if risque_paro == "Élevé":
                    st.error("**Alerte Parodontale :** Présence anormale de pathogènes du complexe rouge.")
                if diversite < 50:
                    st.info("**Dysbiose Orale :** La flore bactérienne est trop pauvre pour se défendre naturellement.")
                if not en_alerte:
                    st.success("✅ **Profil Équilibré :** Le microbiome du patient est protecteur.")
                
                st.markdown("<br>", unsafe_allow_html=True)
                pdf_bytes = generer_pdf(patient["nom"], risque_carieux, risque_paro, diversite, patient["historique"])
                st.download_button(
                    label="📄 Télécharger le Rapport Patient (PDF)",
                    data=pdf_bytes,
                    file_name=f"OralBiome_Rapport_{patient['id']}_{patient['nom'].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            
            with tab2:
                st.header("📂 Historique du Patient")
                if patient["historique"].empty:
                    st.info("Aucune analyse enregistrée pour ce patient.")
                else:
                    st.dataframe(patient["historique"], use_container_width=True, hide_index=True)
                    
                    # Graphique d'évolution si plus d'une visite
                    if len(patient["historique"]) > 1:
                        st.markdown("#### 📈 Évolution dans le temps")
                        df_graph = patient["historique"].copy()
                        df_graph.index = range(len(df_graph))
                        
                        col_g1, col_g2 = st.columns(2)
                        with col_g1:
                            st.line_chart(df_graph[["S. mutans (%)", "P. gingiv. (%)"]].astype(float))
                        with col_g2:
                            st.line_chart(df_graph[["Diversité (%)"]].astype(float))
            
            with tab3:
                st.header("🔬 Ajouter une Analyse / Intervention")
                with st.form("formulaire_ajout_analyse"):
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        nouvelle_date = st.date_input("Date", date.today())
                        nouvel_acte = st.selectbox("Intervention", [
                            "Examen Initial", "Contrôle Microbiome", "Détartrage",
                            "Soin Carie", "Surfaçage", "Probiotiques Prescrits", "Autre"
                        ])
                    with col_f2:
                        nouv_s = st.number_input("S. mutans mesuré (%)", 0.0, 10.0, s_mutans, step=0.1)
                        nouv_p = st.number_input("P. gingivalis mesuré (%)", 0.0, 5.0, p_gingivalis, step=0.1)
                    with col_f3:
                        nouv_div = st.number_input("Diversité mesurée (%)", 0, 100, diversite)
                        st.markdown("<br>", unsafe_allow_html=True)
                        bouton_ajout = st.form_submit_button("💾 Sauvegarder", use_container_width=True, type="primary")
                    
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
                        
                        # Mettre à jour l'historique ET les valeurs courantes
                        st.session_state.patients[st.session_state.patient_selectionne]["historique"] = pd.concat(
                            [patient["historique"], nouvelle_ligne], ignore_index=True
                        )
                        st.session_state.patients[st.session_state.patient_selectionne]["s_mutans"] = nouv_s
                        st.session_state.patients[st.session_state.patient_selectionne]["p_gingivalis"] = nouv_p
                        st.session_state.patients[st.session_state.patient_selectionne]["diversite"] = nouv_div
                        
                        st.success(f"✅ Analyse du {nouvelle_date.strftime('%d/%m/%Y')} sauvegardée.")
                        st.rerun()