import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
from fpdf import FPDF

# ============================================================
# MOTEUR DE RECOMMANDATIONS NUTRITIONNELLES
# ============================================================
def generer_recommandations(s_mutans, p_gingivalis, diversite):
    plan = {
        "priorites": [],
        "aliments_favoriser": [],
        "aliments_eviter": [],
        "probiotiques": [],
        "hygiene": [],
        "suivi_semaines": 24,
        "profil_label": "",
        "profil_description": ""
    }

    nb_alertes = sum([s_mutans > 3.0, p_gingivalis > 0.5, diversite < 50])
    if nb_alertes == 0:
        plan["profil_label"] = "🟢 Microbiome Equilibre"
        plan["profil_description"] = "Votre flore buccale est protectrice. Continuez vos bonnes habitudes et revenez dans 6 mois pour un controle de routine."
        plan["suivi_semaines"] = 24
    elif nb_alertes == 1:
        plan["profil_label"] = "🟡 Desequilibre Modere"
        plan["profil_description"] = "Un desequilibre est detecte. Des ajustements alimentaires et d'hygiene cibles peuvent corriger la situation en 2 a 3 mois."
        plan["suivi_semaines"] = 12
    else:
        plan["profil_label"] = "🔴 Dysbiose Active"
        plan["profil_description"] = "Plusieurs marqueurs sont en alerte. Un plan d'action renforce est necessaire. Un suivi dans 6 a 8 semaines est recommande."
        plan["suivi_semaines"] = 8

    # RISQUE CARIEUX
    if s_mutans > 3.0:
        plan["priorites"].append({
            "icone": "🦠",
            "titre": "Reduire les bacteries acidogenes (S. mutans)",
            "urgence": "Elevee" if s_mutans > 6.0 else "Moderee",
            "explication": f"Votre taux de S. mutans est de {s_mutans}% (normal < 3%). Ces bacteries fermentent les sucres et produisent des acides qui dissolvent l'email.",
            "actions": [
                "Brossage 2 min minimum apres chaque repas sucre",
                "Fil dentaire quotidien le soir avant le coucher",
                "Bain de bouche fluore 1x/jour (sans alcool)",
                "Eviter de grignoter entre les repas — chaque prise alimentaire relance la production d'acides 20 min"
            ]
        })
        plan["aliments_eviter"] += [
            "Bonbons et sucreries (surtout les bonbons acides)",
            "Sodas et boissons sucrees — meme les 'light' sont acidifiants",
            "Pain blanc, viennoiseries — fermentation rapide en sucres",
            "Chocolat au lait et barres sucrees entre les repas",
            "Jus de fruits (meme naturels) — haute teneur en fructose",
            "Miel et sirop d'erable en quantites importantes"
        ]
        plan["aliments_favoriser"] += [
            "Fromage a pate dure (Gruyere, Comte) — neutralise les acides et remineralise",
            "Yaourt nature sans sucre — probiotiques naturels favorables",
            "Legumes crus et croquants — stimulent la salive protectrice",
            "The vert sans sucre — riche en polyphenols antibacteriens",
            "Eau plate — la meilleure boisson entre les repas",
            "Noix et amandes — alcalinisants naturels"
        ]
        plan["probiotiques"].append({
            "nom": "Lactobacillus reuteri (souche DSM 17938)",
            "forme": "Comprimes a sucer, 1x/jour apres le brossage du soir",
            "duree": "3 mois minimum",
            "benefice": "Inhibe directement S. mutans et reduit la plaque acide",
            "marques": "BioGaia Prodentis, Sunstar GUM PerioBalance"
        })

    # RISQUE PARODONTAL
    if p_gingivalis > 0.5:
        plan["priorites"].append({
            "icone": "🩸",
            "titre": "Eliminer les pathogenes parodontaux (complexe rouge)",
            "urgence": "Elevee" if p_gingivalis > 1.5 else "Moderee",
            "explication": f"Votre taux de P. gingivalis est de {p_gingivalis}% (normal < 0.5%). Ces bacteries attaquent les tissus qui maintiennent vos dents en place.",
            "actions": [
                "Nettoyage interdentaire quotidien (brossettes ou fil) — PRIORITE N°1",
                "Brossage de la langue matin et soir avec un gratte-langue",
                "Consultation parodontale recommandee si gencives qui saignent",
                "Arret ou reduction du tabac si applicable — multiplie x3 le risque parodontal"
            ]
        })
        plan["aliments_eviter"] += [
            "Tabac sous toutes formes — reduit l'oxygenation des gencives",
            "Alcool en exces — desseche la muqueuse et favorise la dysbiose",
            "Viandes rouges en exces — favorisent l'inflammation systemique",
            "Sucres raffines — nourrissent directement P. gingivalis",
            "Aliments ultra-transformes riches en omega-6 pro-inflammatoires"
        ]
        plan["aliments_favoriser"] += [
            "Poissons gras (saumon, maquereau, sardines) 2-3x/semaine — omega-3 anti-inflammatoires",
            "Myrtilles, framboises — polyphenols qui inhibent P. gingivalis",
            "Legumes verts feuillus (epinards, roquette) — riches en nitrates benefiques",
            "Huile d'olive extra vierge — oleocanthal aux proprietes anti-inflammatoires",
            "Ail et oignon crus — allicine antibacterienne naturelle",
            "Agrumes (avec moderation) — vitamine C pour la sante des gencives"
        ]
        plan["probiotiques"].append({
            "nom": "Lactobacillus reuteri + Lactobacillus salivarius",
            "forme": "Comprimes ou pastilles a dissoudre en bouche, 2x/jour",
            "duree": "3 a 6 mois",
            "benefice": "Deplace P. gingivalis des poches gingivales, reduit le saignement",
            "marques": "Sunstar GUM PerioBalance, Blis K12 (Streptococcus salivarius)"
        })

    # DYSBIOSE
    if diversite < 50:
        plan["priorites"].append({
            "icone": "🌱",
            "titre": "Restaurer la diversite microbienne orale",
            "urgence": "Moderee" if diversite > 30 else "Elevee",
            "explication": f"Votre score de diversite est de {diversite}/100 (optimal > 65). Une flore appauvrie ne peut pas se defendre contre les bacteries pathogenes.",
            "actions": [
                "Diversifier l'alimentation — objectif : 30 plantes differentes par semaine",
                "Reduire les bains de bouche antiseptiques quotidiens — ils detruisent aussi les bonnes bacteries",
                "Augmenter les fibres prebiotiques (poireaux, ail, oignon, asperges)",
                "Hydratation suffisante — 1.5L d'eau/jour minimum pour maintenir le flux salivaire"
            ]
        })
        plan["aliments_favoriser"] += [
            "Legumes racines varies — fibres prebiotiques nourrissent les bonnes bacteries",
            "Pomme avec la peau — pectine prebiotique",
            "Legumineuses (lentilles, pois chiches) — fibres fermentescibles",
            "Cereales completes — inuline et FOS prebiotiques",
            "Legumes fermentes (choucroute, kimchi cru) — source directe de bacteries benefiques",
            "The Pu-erh et kombucha (sans sucre ajoute) — prebiotiques naturels"
        ]
        plan["aliments_eviter"] += [
            "Bains de bouche antiseptiques quotidiens (chlorhexidine) — sauf prescription",
            "Antibiotiques inutiles — demandez toujours si necessaire",
            "Fast-food regulier — appauvrissent la diversite microbienne"
        ]
        plan["probiotiques"].append({
            "nom": "Streptococcus salivarius K12 + M18",
            "forme": "Pastilles a sucer le soir apres le brossage",
            "duree": "2 a 3 mois, puis entretien 1 mois/trimestre",
            "benefice": "Recolonise la flore orale avec des especes protectrices",
            "marques": "BLIS K12, Nasal Guard Throat Guard"
        })

    # PROFIL EQUILIBRE
    if nb_alertes == 0:
        plan["priorites"].append({
            "icone": "✅",
            "titre": "Maintenir l'equilibre de votre microbiome",
            "urgence": "Routine",
            "explication": "Votre microbiome oral est en bonne sante. L'objectif est de preserver cet equilibre sur le long terme.",
            "actions": [
                "Continuer le brossage 2x/jour avec une brosse souple",
                "Fil dentaire ou brossettes interdentaires 1x/jour",
                "Alimentation variee et riche en fibres",
                "Controle microbiome dans 6 mois"
            ]
        })
        plan["aliments_favoriser"] += [
            "Alimentation mediterraneenne variee — ideale pour le microbiome",
            "Eau comme boisson principale",
            "Produits laitiers fermentes (yaourt, kefir) en quantite moderee",
            "Legumes cruciferes (brocoli, chou) — sulforaphane protecteur"
        ]

    # HYGIÈNE
    plan["hygiene"] = [
        {
            "moment": "🌅 Matin",
            "actions": [
                "Brossage 2 min avec brosse souple (electrique si possible)",
                "Brossage de la langue de l'arriere vers l'avant",
                "Bain de bouche non-alcoolise si recommande"
            ]
        },
        {
            "moment": "🌙 Soir (le plus important)",
            "actions": [
                "Fil dentaire ou brossettes AVANT le brossage",
                "Brossage 2 min minimum",
                "Probiotique oral a dissoudre (si prescrit)",
                "Ne plus rien manger ni boire (sauf eau) apres"
            ]
        },
        {
            "moment": "🍽️ Apres les repas",
            "actions": [
                "Attendre 30 min avant de brosser (l'email est fragilise par les acides)",
                "Boire un verre d'eau pour rincer",
                "Chewing-gum sans sucre au xylitol (5 min) si pas de brossage possible"
            ]
        }
    ]

    plan["aliments_favoriser"] = list(dict.fromkeys(plan["aliments_favoriser"]))
    plan["aliments_eviter"] = list(dict.fromkeys(plan["aliments_eviter"]))
    return plan



# ============================================================
# NETTOYAGE TEXTE POUR FPDF
# ============================================================
def clean(text):
    """Nettoie un texte pour fpdf : remplace les caracteres unicode problematiques."""
    if not isinstance(text, str):
        text = str(text)
    replacements = {
        "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": '-', "\u2014": '-', "\u2026": '...', "\u00a0": ' ',
        "\u2022": '-', "\u00ab": '"', "\u00bb": '"',
        "\u00e0": 'a', "\u00e2": 'a', "\u00e9": 'e', "\u00e8": 'e',
        "\u00ea": 'e', "\u00eb": 'e', "\u00ee": 'i', "\u00ef": 'i',
        "\u00f4": 'o', "\u00f9": 'u', "\u00fb": 'u', "\u00fc": 'u',
        "\u00e7": 'c', "\u00c0": 'A', "\u00c9": 'E', "\u00c8": 'E',
        "\u00ce": 'I', "\u00d4": 'O', "\u00d9": 'U', "\u00db": 'U',
        "\u00c7": 'C',
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode('latin-1', errors='replace').decode('latin-1')


# ============================================================
# GENERATION PDF
# ============================================================
def generer_pdf(patient_nom, r_carieux, r_paro, diversite, historique_df, plan):
    pdf = FPDF()
    pdf.add_page()

    # En-tete
    pdf.set_fill_color(27, 79, 138)
    pdf.rect(0, 0, 210, 32, 'F')
    pdf.set_font("Helvetica", 'B', size=18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(200, 16, txt=clean("OralBiome - Rapport Patient"), ln=True, align='C')
    pdf.set_font("Helvetica", size=10)
    pdf.cell(200, 10, txt=clean("Microbiome Oral Predictif | Rapport Personnalise"), ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    pdf.set_font("Helvetica", 'B', size=12)
    pdf.cell(100, 8, txt=clean(f"Patient : {patient_nom}"), ln=False)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(100, 8, txt=clean(f"Date : {date.today().strftime('%d/%m/%Y')}"), ln=True, align='R')
    pdf.ln(4)

    # Profil
    profil_label = plan["profil_label"].replace("🟢", "").replace("🟡", "").replace("🔴", "").strip()
    nb_alertes = sum([r_carieux == "Eleve" or r_carieux == "Eleve", r_paro == "Eleve", diversite < 50])
    if "Equilibre" in profil_label:
        pdf.set_fill_color(40, 167, 69)
    elif "Modere" in profil_label:
        pdf.set_fill_color(220, 180, 0)
    else:
        pdf.set_fill_color(220, 53, 69)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", 'B', size=12)
    pdf.cell(190, 9, txt=clean(f"  Profil : {profil_label}"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(190, 6, txt=plan["profil_description"])
    pdf.ln(4)

    # Resultats
    pdf.set_font("Helvetica", 'B', size=12)
    pdf.set_fill_color(214, 228, 247)
    pdf.cell(190, 8, txt=clean("  Resultats de l'Analyse"), ln=True, fill=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", size=11)
    for label, valeur in [("Risque Carieux", r_carieux), ("Risque Parodontal", r_paro)]:
        c = (220, 53, 69) if valeur in ["Eleve", "Eleve"] else (40, 167, 69)
        pdf.set_text_color(*c)
        pdf.cell(190, 7, txt=clean(f"  {label} : {valeur}"), ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 7, txt=clean(f"  Score de Diversite : {diversite}/100  (optimal > 65)"), ln=True)
    pdf.ln(6)

    # Priorites
    if plan["priorites"]:
        pdf.set_font("Helvetica", 'B', size=12)
        pdf.set_fill_color(214, 228, 247)
        pdf.cell(190, 8, txt=clean("  Plan d'Action"), ln=True, fill=True)
        pdf.ln(3)
        for i, p in enumerate(plan["priorites"]):
            pdf.set_font("Helvetica", 'B', size=11)
            pdf.set_text_color(27, 79, 138)
            pdf.cell(190, 7, txt=clean(f"  Priorite {i+1} : {p['titre']}"), ln=True)
            pdf.set_font("Helvetica", 'I', size=9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(185, 5, txt=clean(f"    {p['explication']}"))
            pdf.set_font("Helvetica", size=10)
            pdf.set_text_color(0, 0, 0)
            for action in p["actions"]:
                pdf.cell(190, 6, txt=clean(f"    - {action}"), ln=True)
            pdf.ln(3)

    # Nouvelle page : Nutrition
    pdf.add_page()
    pdf.set_fill_color(27, 79, 138)
    pdf.rect(0, 0, 210, 12, 'F')
    pdf.set_font("Helvetica", 'B', size=13)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 12, txt=clean("  Plan Nutritionnel Personnalise - OralBiome"), ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    if plan["aliments_favoriser"] or plan["aliments_eviter"]:
        pdf.set_font("Helvetica", 'B', size=11)
        pdf.set_fill_color(212, 237, 218)
        pdf.cell(93, 8, txt=clean("  Aliments a Favoriser"), ln=False, fill=True)
        pdf.set_fill_color(248, 215, 218)
        pdf.cell(97, 8, txt=clean("  Aliments a Limiter / Eviter"), ln=True, fill=True)
        pdf.ln(2)
        pdf.set_font("Helvetica", size=9)
        max_items = max(len(plan["aliments_favoriser"]), len(plan["aliments_eviter"]))
        for i in range(max_items):
            fav = plan["aliments_favoriser"][i][:50] if i < len(plan["aliments_favoriser"]) else ""
            evi = plan["aliments_eviter"][i][:53] if i < len(plan["aliments_eviter"]) else ""
            fill = i % 2 == 0
            pdf.set_fill_color(240, 255, 240) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.cell(93, 6, txt=clean(f"  {fav}"), border=0, ln=False, fill=fill)
            pdf.set_fill_color(255, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.cell(97, 6, txt=clean(f"  {evi}"), border=0, ln=True, fill=fill)
        pdf.ln(5)

    if plan["probiotiques"]:
        pdf.set_font("Helvetica", 'B', size=12)
        pdf.set_fill_color(214, 228, 247)
        pdf.cell(190, 8, txt=clean("  Probiotiques Oraux Recommandes"), ln=True, fill=True)
        pdf.ln(2)
        for prob in plan["probiotiques"]:
            pdf.set_font("Helvetica", 'B', size=10)
            pdf.set_text_color(27, 79, 138)
            pdf.cell(190, 6, txt=clean(f"  {prob['nom']}"), ln=True)
            pdf.set_font("Helvetica", size=9)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(190, 5, txt=clean(f"    Forme : {prob['forme']}"), ln=True)
            pdf.cell(190, 5, txt=clean(f"    Duree : {prob['duree']}"), ln=True)
            pdf.cell(190, 5, txt=clean(f"    Benefice : {prob['benefice']}"), ln=True)
            pdf.cell(190, 5, txt=clean(f"    Produits : {prob['marques']}"), ln=True)
            pdf.ln(3)

    # Hygiene
    pdf.set_font("Helvetica", 'B', size=12)
    pdf.set_fill_color(214, 228, 247)
    pdf.cell(190, 8, txt=clean("  Protocole d'Hygiene Personnalise"), ln=True, fill=True)
    pdf.ln(2)
    for moment_data in plan["hygiene"]:
        moment = moment_data["moment"].encode('ascii', 'ignore').decode('ascii').strip()
        pdf.set_font("Helvetica", 'B', size=10)
        pdf.set_text_color(27, 79, 138)
        pdf.cell(190, 6, txt=clean(f"  {moment}"), ln=True)
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(0, 0, 0)
        for action in moment_data["actions"]:
            pdf.cell(190, 5, txt=clean(f"    - {action}"), ln=True)
        pdf.ln(2)

    # Suivi
    pdf.ln(3)
    pdf.set_fill_color(255, 243, 205)
    pdf.set_font("Helvetica", 'B', size=11)
    pdf.cell(190, 8, txt=clean(f"  Prochain controle recommande : dans {plan['suivi_semaines']} semaines"), ln=True, fill=True)

    # Pied de page
    pdf.ln(6)
    pdf.set_font("Helvetica", 'I', size=8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(190, 5, txt=clean("Ce rapport est fourni a titre preventif et informatif. Il ne constitue pas un diagnostic medical."))
    pdf.cell(190, 5, txt=clean("OralBiome - Microbiome Oral Predictif | contact@oralbiome.com"), ln=True, align='C')

    pdf_output = pdf.output()
    return pdf_output.encode('latin-1') if isinstance(pdf_output, str) else bytes(pdf_output)


# ============================================================
# CONFIGURATION APP
# ============================================================
st.set_page_config(page_title="OralBiome - Praticien", page_icon="🦷", layout="wide")

st.markdown("""
<style>
    .reco-card { background:#f8f9fa; border-left:4px solid #1B4F8A; border-radius:6px; padding:14px 18px; margin:8px 0; }
    .reco-card-green { border-left-color:#28a745; background:#f0fff4; }
    .reco-card-red { border-left-color:#dc3545; background:#fff5f5; }
    .reco-card-orange { border-left-color:#fd7e14; background:#fff8f0; }
    .pill-green { display:inline-block; background:#d4edda; border-radius:20px; padding:4px 12px; margin:3px; font-size:13px; }
    .pill-red { display:inline-block; background:#f8d7da; border-radius:20px; padding:4px 12px; margin:3px; font-size:13px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# DONNÉES INITIALES
# ============================================================
def donnees_initiales():
    patients = {}
    df1 = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversité (%)", "Status"])
    df1.loc[0] = ["12/10/2023", "Examen Initial", 4.2, 0.8, 45, "🔴 Alerte"]
    df1.loc[1] = ["08/04/2026", "Controle", 4.2, 0.3, 75, "🔴 Alerte"]
    patients["Jean Dupont"] = {
        "id": "P001", "nom": "Jean Dupont", "age": 42,
        "email": "jean.dupont@email.com", "telephone": "+32 472 123 456",
        "date_naissance": "15/03/1982", "historique": df1,
        "s_mutans": 4.2, "p_gingivalis": 0.3, "diversite": 75
    }
    df2 = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversité (%)", "Status"])
    df2.loc[0] = ["05/01/2024", "Examen Initial", 1.2, 0.1, 82, "🟢 Stable"]
    patients["Marie Martin"] = {
        "id": "P002", "nom": "Marie Martin", "age": 35,
        "email": "marie.martin@email.com", "telephone": "+32 478 654 321",
        "date_naissance": "22/07/1989", "historique": df2,
        "s_mutans": 1.2, "p_gingivalis": 0.1, "diversite": 82
    }
    df3 = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversité (%)", "Status"])
    df3.loc[0] = ["18/02/2025", "Examen Initial", 6.5, 1.8, 38, "🔴 Alerte"]
    patients["Pierre Bernard"] = {
        "id": "P003", "nom": "Pierre Bernard", "age": 58,
        "email": "pierre.bernard@email.com", "telephone": "+32 495 789 012",
        "date_naissance": "03/11/1966", "historique": df3,
        "s_mutans": 6.5, "p_gingivalis": 1.8, "diversite": 38
    }
    return patients


# ============================================================
# INIT SESSION
# ============================================================
if 'utilisateur_connecte' not in st.session_state:
    st.session_state.utilisateur_connecte = False
if 'patients' not in st.session_state:
    st.session_state.patients = donnees_initiales()
if 'patient_selectionne' not in st.session_state:
    st.session_state.patient_selectionne = "Jean Dupont"
if 'vue' not in st.session_state:
    st.session_state.vue = "dossier"


# ============================================================
# CONNEXION
# ============================================================
if not st.session_state.utilisateur_connecte:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.write(""); st.write("")
        try:
            st.image(Image.open("image_19.png"), use_container_width=True)
        except:
            st.markdown("<h1 style='text-align:center;'>🦷 OralBiome</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center; color:#1B4F8A;'>Portail Praticien</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#888;'>Microbiome Oral Predictif</p>", unsafe_allow_html=True)
        st.markdown("---")
        email = st.text_input("Email Professionnel")
        mdp = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter", use_container_width=True, type="primary"):
            if email == "contact@oralbiome.com" and mdp == "mvp2024":
                st.session_state.utilisateur_connecte = True
                st.rerun()
            else:
                st.error("Identifiants incorrects. Utilisez contact@oralbiome.com / mvp2024")

# ============================================================
# APP PRINCIPALE
# ============================================================
else:
    # SIDEBAR
    try:
        st.sidebar.image(Image.open("image_19.png"), use_container_width=True)
    except:
        st.sidebar.markdown("## 🦷 OralBiome")

    st.sidebar.markdown("---")
    c1, c2 = st.sidebar.columns(2)
    with c1:
        if st.button("👥 Patients", use_container_width=True):
            st.session_state.vue = "liste"; st.rerun()
    with c2:
        if st.button("➕ Nouveau", use_container_width=True):
            st.session_state.vue = "nouveau"; st.rerun()

    st.sidebar.markdown("---")
    nb_patients = len(st.session_state.patients)
    nb_alertes = sum(1 for p in st.session_state.patients.values()
                     if p["s_mutans"] > 3.0 or p["p_gingivalis"] > 0.5 or p["diversite"] < 50)
    st.sidebar.markdown("### 📊 Mon Cabinet")
    sc1, sc2 = st.sidebar.columns(2)
    sc1.metric("Patients", nb_patients)
    sc2.metric("Alertes", nb_alertes)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Acces Rapide")
    recherche = st.sidebar.text_input("Rechercher...", placeholder="Nom ou ID")
    patients_filtres = {n: d for n, d in st.session_state.patients.items()
                        if recherche.lower() in n.lower() or recherche.lower() in d["id"].lower()} if recherche else st.session_state.patients

    for nom, data in patients_filtres.items():
        icon = "🔴" if (data["s_mutans"] > 3.0 or data["p_gingivalis"] > 0.5 or data["diversite"] < 50) else "🟢"
        is_selected = nom == st.session_state.patient_selectionne
        if st.sidebar.button(f"{icon} {data['id']} — {nom}", use_container_width=True,
                              type="primary" if is_selected else "secondary"):
            st.session_state.patient_selectionne = nom
            st.session_state.vue = "dossier"; st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Se deconnecter", use_container_width=True):
        st.session_state.utilisateur_connecte = False; st.rerun()

    # ==========================================
    # VUE LISTE
    # ==========================================
    if st.session_state.vue == "liste":
        st.title("👥 Gestion des Patients")
        st.markdown(f"**{nb_patients} patients** · **{nb_alertes} alertes actives**")
        st.markdown("---")
        cf1, cf2, cf3 = st.columns(3)
        with cf1:
            filtre = st.selectbox("Filtrer", ["Tous", "Alerte uniquement", "Stable uniquement"])
        with cf3:
            if st.button("➕ Nouveau Patient", type="primary"):
                st.session_state.vue = "nouveau"; st.rerun()
        st.markdown("---")
        donnees = []
        for nom, data in st.session_state.patients.items():
            en_alerte = data["s_mutans"] > 3.0 or data["p_gingivalis"] > 0.5 or data["diversite"] < 50
            if filtre == "Alerte uniquement" and not en_alerte: continue
            if filtre == "Stable uniquement" and en_alerte: continue
            donnees.append({
                "ID": data["id"], "Nom": nom, "Age": data["age"],
                "Risque Carieux": "Eleve" if data["s_mutans"] > 3.0 else "Faible",
                "Risque Parodontal": "Eleve" if data["p_gingivalis"] > 0.5 else "Faible",
                "Diversite": f"{data['diversite']}/100",
                "Statut": "Alerte" if en_alerte else "Stable",
                "Visites": len(data["historique"])
            })
        if donnees:
            st.dataframe(pd.DataFrame(donnees), use_container_width=True, hide_index=True)
            st.markdown("---")
            cols = st.columns(min(len(st.session_state.patients), 4))
            for i, (nom, data) in enumerate(st.session_state.patients.items()):
                en_alerte = data["s_mutans"] > 3.0 or data["p_gingivalis"] > 0.5 or data["diversite"] < 50
                with cols[i % 4]:
                    if st.button(f"{'🔴' if en_alerte else '🟢'} {nom}", use_container_width=True):
                        st.session_state.patient_selectionne = nom
                        st.session_state.vue = "dossier"; st.rerun()

    # ==========================================
    # VUE NOUVEAU PATIENT
    # ==========================================
    elif st.session_state.vue == "nouveau":
        st.title("➕ Nouveau Patient")
        st.markdown("---")
        with st.form("form_nouveau"):
            st.markdown("### Informations Personnelles")
            c1, c2 = st.columns(2)
            with c1:
                nouveau_nom = st.text_input("Nom complet *")
                nouvel_email = st.text_input("Email")
                nouvelle_ddn = st.date_input("Date de naissance", value=date(1985, 1, 1))
            with c2:
                nouvel_age = st.number_input("Age", 1, 120, 35)
                nouveau_tel = st.text_input("Telephone")
            st.markdown("---")
            st.markdown("### Premiere Analyse (optionnel)")
            c3, c4, c5 = st.columns(3)
            with c3: init_s = st.number_input("S. mutans (%)", 0.0, 10.0, 2.0, step=0.1)
            with c4: init_p = st.number_input("P. gingivalis (%)", 0.0, 5.0, 0.2, step=0.1)
            with c5: init_div = st.number_input("Diversite (%)", 0, 100, 70)
            ajouter = st.checkbox("Enregistrer comme examen initial", value=True)
            soumettre = st.form_submit_button("Creer le dossier", use_container_width=True, type="primary")
            if soumettre:
                if not nouveau_nom.strip():
                    st.error("Le nom est obligatoire.")
                elif nouveau_nom in st.session_state.patients:
                    st.error("Ce patient existe deja.")
                else:
                    nid = f"P{str(len(st.session_state.patients) + 1).zfill(3)}"
                    df_n = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversité (%)", "Status"])
                    if ajouter:
                        s = "🔴 Alerte" if init_s > 3.0 or init_p > 0.5 or init_div < 50 else "🟢 Stable"
                        df_n.loc[0] = [date.today().strftime("%d/%m/%Y"), "Examen Initial", init_s, init_p, init_div, s]
                    st.session_state.patients[nouveau_nom] = {
                        "id": nid, "nom": nouveau_nom, "age": nouvel_age,
                        "email": nouvel_email, "telephone": nouveau_tel,
                        "date_naissance": nouvelle_ddn.strftime("%d/%m/%Y"),
                        "historique": df_n,
                        "s_mutans": init_s if ajouter else 0.0,
                        "p_gingivalis": init_p if ajouter else 0.0,
                        "diversite": init_div if ajouter else 70
                    }
                    st.session_state.patient_selectionne = nouveau_nom
                    st.session_state.vue = "dossier"; st.rerun()

    # ==========================================
    # VUE DOSSIER
    # ==========================================
    else:
        patient = st.session_state.patients.get(st.session_state.patient_selectionne)
        if not patient:
            st.error("Patient introuvable.")
        else:
            s_mutans = patient["s_mutans"]
            p_gingivalis = patient["p_gingivalis"]
            diversite = patient["diversite"]
            risque_carieux = "Eleve" if s_mutans > 3.0 else "Faible"
            risque_paro = "Eleve" if p_gingivalis > 0.5 else "Faible"
            en_alerte = risque_carieux == "Eleve" or risque_paro == "Eleve" or diversite < 50

            # Generer le plan
            plan = generer_recommandations(s_mutans, p_gingivalis, diversite)

            # En-tete
            badge = "🔴 En Alerte" if en_alerte else "🟢 Stable"
            st.markdown(f"## 🦷 {patient['nom']}  `{patient['id']}`  —  {badge}")
            st.caption(f"Age : {patient['age']} ans  ·  {patient['email']}  ·  {patient['telephone']}")
            st.markdown("---")

            # Metriques
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Risque Carieux", risque_carieux, "Alerte" if risque_carieux == "Eleve" else "Normal", delta_color="inverse")
            m2.metric("Risque Parodontal", risque_paro, "Alerte" if risque_paro == "Eleve" else "Normal", delta_color="inverse")
            m3.metric("Score de Diversite", f"{diversite}/100")
            m4.metric("Visites", len(patient["historique"]))
            st.markdown("---")

            # Profil
            st.markdown(f"### {plan['profil_label']}")
            st.info(plan["profil_description"])
            st.markdown(f"**Prochain controle recommande : dans {plan['suivi_semaines']} semaines**")
            st.markdown("---")

            # ONGLETS
            tab1, tab2, tab3, tab4 = st.tabs([
                "🚨 Plan d'Action",
                "🥗 Nutrition & Probiotiques",
                "🪥 Hygiene",
                "📂 Historique & PDF"
            ])

            # ---- ONGLET 1 : PLAN D'ACTION ----
            with tab1:
                st.header("🚨 Priorites & Actions Immediates")
                st.caption("Actions classees par ordre de priorite selon votre profil bacterien.")
                st.markdown("---")
                for i, p in enumerate(plan["priorites"]):
                    if p["urgence"] == "Elevee":
                        couleur = "reco-card-red"
                        badge_urgence = "🔴 Urgence Elevee"
                    elif p["urgence"] == "Moderee":
                        couleur = "reco-card-orange"
                        badge_urgence = "🟡 Moderee"
                    else:
                        couleur = "reco-card-green"
                        badge_urgence = "🟢 Routine"

                    st.markdown(f"#### {p['icone']} Priorite {i+1} — {p['titre']}  `{badge_urgence}`")
                    st.markdown(f"<div class='reco-card {couleur}'><em>{p['explication']}</em></div>", unsafe_allow_html=True)
                    for action in p["actions"]:
                        st.markdown(f"- {action}")
                    st.markdown("---")

            # ---- ONGLET 2 : NUTRITION ----
            with tab2:
                st.header("🥗 Plan Nutritionnel Personnalise")
                st.caption("Etabli selon votre profil bacterien par notre nutritionniste clinique.")
                st.markdown("---")

                col_fav, col_evi = st.columns(2)
                with col_fav:
                    st.markdown("### ✅ Aliments a Favoriser")
                    st.markdown("*Ces aliments soutiennent votre microbiome oral*")
                    for aliment in plan["aliments_favoriser"]:
                        st.markdown(f"<span class='pill-green'>{aliment}</span>", unsafe_allow_html=True)

                with col_evi:
                    st.markdown("### ❌ Aliments a Limiter")
                    st.markdown("*Ces aliments fragilisent votre flore buccale*")
                    for aliment in plan["aliments_eviter"]:
                        st.markdown(f"<span class='pill-red'>{aliment}</span>", unsafe_allow_html=True)

                st.markdown("---")
                st.header("💊 Probiotiques Oraux Cibles")
                st.caption("Selectionnes specifiquement pour votre profil bacterien.")

                if plan["probiotiques"]:
                    for prob in plan["probiotiques"]:
                        with st.expander(f"🧫 {prob['nom']}", expanded=True):
                            pc1, pc2 = st.columns(2)
                            with pc1:
                                st.markdown(f"**Forme :** {prob['forme']}")
                                st.markdown(f"**Duree :** {prob['duree']}")
                            with pc2:
                                st.markdown(f"**Benefice :** {prob['benefice']}")
                                st.markdown(f"**Produits :** `{prob['marques']}`")
                else:
                    st.success("Aucun probiotique specifique necessaire. Maintenez une alimentation variee.")

            # ---- ONGLET 3 : HYGIÈNE ----
            with tab3:
                st.header("🪥 Protocole d'Hygiene Personnalise")
                st.caption("Routine adaptee a votre profil bacterien specifique.")
                st.markdown("---")
                for moment_data in plan["hygiene"]:
                    st.markdown(f"### {moment_data['moment']}")
                    for action in moment_data["actions"]:
                        st.markdown(f"- {action}")
                    st.markdown("")
                st.markdown("---")
                st.markdown("### Le conseil de notre nutritionniste")
                if risque_paro == "Eleve":
                    st.info("Le nettoyage interdentaire est PLUS important que le brossage. Des gencives saines se brossent, mais elles se nettoient surtout entre les dents. 5 minutes de fil dentaire le soir valent mieux que 10 minutes de brossage.")
                elif risque_carieux == "Eleve":
                    st.warning("Le timing des repas est aussi important que l'hygiene. Chaque prise alimentaire relance la production d'acides pendant 20 minutes. Reduire la frequence des grignotages est cle.")
                else:
                    st.success("Votre routine est efficace. Continuez et revenez dans 6 mois pour verifier que l'equilibre se maintient.")

            # ---- ONGLET 4 : HISTORIQUE & PDF ----
            with tab4:
                st.header("📂 Historique du Patient")
                if patient["historique"].empty:
                    st.info("Aucune analyse enregistree.")
                else:
                    st.dataframe(patient["historique"], use_container_width=True, hide_index=True)
                    if len(patient["historique"]) > 1:
                        st.markdown("#### Evolution dans le temps")
                        df_g = patient["historique"].copy()
                        df_g.index = range(len(df_g))
                        gc1, gc2 = st.columns(2)
                        with gc1:
                            st.line_chart(df_g[["S. mutans (%)", "P. gingiv. (%)"]].astype(float))
                        with gc2:
                            st.line_chart(df_g[["Diversité (%)"]].astype(float))

                st.markdown("---")
                st.header("🔬 Ajouter une Intervention")
                with st.form("form_ajout"):
                    fa1, fa2, fa3 = st.columns(3)
                    with fa1:
                        nd = st.date_input("Date", date.today())
                        na = st.selectbox("Intervention", ["Examen Initial", "Controle Microbiome", "Detartrage", "Soin Carie", "Surfacage", "Probiotiques Prescrits", "Autre"])
                    with fa2:
                        ns = st.number_input("S. mutans (%)", 0.0, 10.0, s_mutans, step=0.1)
                        np_ = st.number_input("P. gingivalis (%)", 0.0, 5.0, p_gingivalis, step=0.1)
                    with fa3:
                        nd2 = st.number_input("Diversite (%)", 0, 100, diversite)
                        st.markdown("<br>", unsafe_allow_html=True)
                        sauver = st.form_submit_button("Sauvegarder", use_container_width=True, type="primary")
                    if sauver:
                        st_val = "🔴 Alerte" if ns > 3.0 or np_ > 0.5 or nd2 < 50 else "🟢 Stable"
                        nl = pd.DataFrame({
                            "Date": [nd.strftime("%d/%m/%Y")], "Acte / Test": [na],
                            "S. mutans (%)": [ns], "P. gingiv. (%)": [np_],
                            "Diversité (%)": [nd2], "Status": [st_val]
                        })
                        st.session_state.patients[st.session_state.patient_selectionne]["historique"] = pd.concat(
                            [patient["historique"], nl], ignore_index=True)
                        st.session_state.patients[st.session_state.patient_selectionne]["s_mutans"] = ns
                        st.session_state.patients[st.session_state.patient_selectionne]["p_gingivalis"] = np_
                        st.session_state.patients[st.session_state.patient_selectionne]["diversite"] = nd2
                        st.success("Sauvegarde avec succes.")
                        st.rerun()

                st.markdown("---")
                st.header("📄 Rapport PDF Complet")
                st.caption("Le rapport inclut le plan d'action, la nutrition, les probiotiques et l'hygiene.")
                pdf_bytes = generer_pdf(patient["nom"], risque_carieux, risque_paro, diversite, patient["historique"], plan)
                st.download_button(
                    label="Telecharger le Rapport Patient Complet (PDF)",
                    data=pdf_bytes,
                    file_name=f"OralBiome_{patient['id']}_{patient['nom'].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )