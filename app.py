import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
import io

# ============================================================
# PDF — reportlab
# ============================================================
def generer_pdf(patient_nom, r_carieux, r_paro, diversite, historique_df, plan):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=15*mm, rightMargin=15*mm,
                                topMargin=15*mm, bottomMargin=15*mm)

        styles = getSampleStyleSheet()
        BLUE       = colors.HexColor('#0A1628')
        TEAL       = colors.HexColor('#00C2A8')
        LIGHT_TEAL = colors.HexColor('#E0F7F5')
        GREEN      = colors.HexColor('#28a745')
        RED        = colors.HexColor('#dc3545')
        ORANGE     = colors.HexColor('#fd7e14')
        GRAY_BG    = colors.HexColor('#F7F9FC')

        title_style = ParagraphStyle('Title', fontSize=18, textColor=colors.white,
                                     alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=4)
        sub_style   = ParagraphStyle('Sub', fontSize=10, textColor=colors.HexColor('#A8D8D3'),
                                     alignment=TA_CENTER, fontName='Helvetica', spaceAfter=6)
        h1_style    = ParagraphStyle('H1', fontSize=13, textColor=BLUE,
                                     fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=4)
        h2_style    = ParagraphStyle('H2', fontSize=11, textColor=BLUE,
                                     fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=3)
        body_style  = ParagraphStyle('Body', fontSize=10, fontName='Helvetica', spaceAfter=3, leading=14)
        italic_style= ParagraphStyle('Italic', fontSize=9, fontName='Helvetica-Oblique',
                                     textColor=colors.HexColor('#555555'), spaceAfter=4)
        small_style = ParagraphStyle('Small', fontSize=8, fontName='Helvetica',
                                     textColor=colors.grey, alignment=TA_CENTER)

        elems = []

        # EN-TETE
        header_data = [[Paragraph("OralBiome — Rapport Patient", title_style)],
                       [Paragraph("Microbiome Oral Prédictif | Rapport Personnalisé", sub_style)]]
        header_table = Table(header_data, colWidths=[180*mm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BLUE),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        elems.append(header_table)
        elems.append(Spacer(1, 5*mm))

        info_data = [[
            Paragraph(f"<b>Patient :</b> {patient_nom}", body_style),
            Paragraph(f"<b>Date :</b> {date.today().strftime('%d/%m/%Y')}", body_style)
        ]]
        info_table = Table(info_data, colWidths=[90*mm, 90*mm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_TEAL),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elems.append(info_table)
        elems.append(Spacer(1, 4*mm))

        profil    = plan["profil_label"]
        nb_al     = sum([r_carieux=="Eleve", r_paro=="Eleve", diversite<50])
        pf_color  = GREEN if nb_al==0 else ORANGE if nb_al==1 else RED
        pf_data   = [[Paragraph(f"<b>Profil : {profil}</b>", ParagraphStyle('PF', fontSize=12,
                      textColor=colors.white, fontName='Helvetica-Bold'))]]
        pf_table  = Table(pf_data, colWidths=[180*mm])
        pf_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), pf_color),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elems.append(pf_table)
        elems.append(Paragraph(plan["profil_description"], italic_style))
        elems.append(Spacer(1, 3*mm))

        elems.append(Paragraph("Résultats de l'Analyse", h1_style))
        elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_TEAL))
        res_data = [
            [Paragraph("<b>Risque Carieux</b>", body_style),
             Paragraph(f"<font color='{'#dc3545' if r_carieux=='Eleve' else '#28a745'}'><b>{r_carieux}</b></font>", body_style)],
            [Paragraph("<b>Risque Parodontal</b>", body_style),
             Paragraph(f"<font color='{'#dc3545' if r_paro=='Eleve' else '#28a745'}'><b>{r_paro}</b></font>", body_style)],
            [Paragraph("<b>Score de Diversité</b>", body_style),
             Paragraph(f"<b>{diversite}/100</b> (optimal > 65)", body_style)],
            [Paragraph("<b>Prochain contrôle</b>", body_style),
             Paragraph(f"Dans <b>{plan['suivi_semaines']} semaines</b>", body_style)],
        ]
        res_table = Table(res_data, colWidths=[90*mm, 90*mm])
        res_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), GRAY_BG),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.white),
        ]))
        elems.append(res_table)
        elems.append(Spacer(1, 5*mm))

        if plan["priorites"]:
            elems.append(Paragraph("Plan d'Action — Priorités", h1_style))
            elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_TEAL))
            for i, p in enumerate(plan["priorites"]):
                urgence = p["urgence"]
                bg     = colors.HexColor('#fff5f5') if urgence=="Elevee" else colors.HexColor('#fff8f0') if urgence=="Moderee" else colors.HexColor('#f0fff4')
                badge  = "URGENCE ÉLEVÉE" if urgence=="Elevee" else "MODÉRÉE" if urgence=="Moderee" else "ROUTINE"
                elems.append(Paragraph(f"Priorité {i+1} — {p['titre']} [{badge}]", h2_style))
                expl_data = [[Paragraph(p['explication'], italic_style)]]
                expl_table = Table(expl_data, colWidths=[180*mm])
                expl_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), bg),
                    ('LEFTPADDING', (0,0), (-1,-1), 10),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ]))
                elems.append(expl_table)
                for action in p["actions"]:
                    elems.append(Paragraph(f"• {action}", body_style))
                elems.append(Spacer(1, 3*mm))

        elems.append(Paragraph("Plan Nutritionnel Personnalisé", h1_style))
        elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_TEAL))
        if plan["aliments_favoriser"] or plan["aliments_eviter"]:
            header_nutr = [[
                Paragraph("<b>Aliments à Favoriser</b>", ParagraphStyle('NH', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white)),
                Paragraph("<b>Aliments à Limiter / Éviter</b>", ParagraphStyle('NH2', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white))
            ]]
            nutr_header_table = Table(header_nutr, colWidths=[90*mm, 90*mm])
            nutr_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,0), GREEN),
                ('BACKGROUND', (1,0), (1,0), RED),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
            ]))
            elems.append(nutr_header_table)
            max_items = max(len(plan["aliments_favoriser"]), len(plan["aliments_eviter"]))
            nutr_rows = []
            for i in range(max_items):
                fav = plan["aliments_favoriser"][i] if i < len(plan["aliments_favoriser"]) else ""
                evi = plan["aliments_eviter"][i]    if i < len(plan["aliments_eviter"])    else ""
                nutr_rows.append([Paragraph(fav, body_style), Paragraph(evi, body_style)])
            nutr_table = Table(nutr_rows, colWidths=[90*mm, 90*mm])
            nutr_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f0fff4')),
                ('BACKGROUND', (1,0), (1,-1), colors.HexColor('#fff5f5')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('LINEBELOW', (0,0), (-1,-2), 0.3, colors.white),
            ]))
            elems.append(nutr_table)
            elems.append(Spacer(1, 5*mm))

        if plan["probiotiques"]:
            elems.append(Paragraph("Probiotiques Oraux Recommandés", h1_style))
            elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_TEAL))
            for prob in plan["probiotiques"]:
                elems.append(Paragraph(f"<b>{prob['nom']}</b>", h2_style))
                prob_data = [
                    [Paragraph("<b>Forme :</b>", body_style), Paragraph(prob['forme'], body_style)],
                    [Paragraph("<b>Durée :</b>", body_style), Paragraph(prob['duree'], body_style)],
                    [Paragraph("<b>Bénéfice :</b>", body_style), Paragraph(prob['benefice'], body_style)],
                    [Paragraph("<b>Produits :</b>", body_style), Paragraph(prob['marques'], body_style)],
                ]
                prob_table = Table(prob_data, colWidths=[40*mm, 140*mm])
                prob_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), GRAY_BG),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LEFTPADDING', (0,0), (-1,-1), 8),
                    ('LINEBELOW', (0,0), (-1,-2), 0.3, colors.white),
                ]))
                elems.append(prob_table)
                elems.append(Spacer(1, 3*mm))

        elems.append(Paragraph("Protocole d'Hygiène Personnalisé", h1_style))
        elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_TEAL))
        for moment_data in plan["hygiene"]:
            elems.append(Paragraph(f"<b>{moment_data['moment']}</b>", h2_style))
            for action in moment_data["actions"]:
                elems.append(Paragraph(f"• {action}", body_style))
            elems.append(Spacer(1, 2*mm))

        if not historique_df.empty:
            elems.append(Spacer(1, 5*mm))
            elems.append(Paragraph("Historique des Analyses", h1_style))
            elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_TEAL))
            hist_header = [["Date", "Acte / Test", "S. mutans", "P. gingiv.", "Diversité", "Statut"]]
            hist_rows   = []
            for _, row in historique_df.iterrows():
                statut = str(row.get("Status","")).replace("🔴 ","").replace("🟢 ","")
                hist_rows.append([
                    str(row.get("Date","")), str(row.get("Acte / Test","")),
                    str(row.get("S. mutans (%)","")) + "%", str(row.get("P. gingiv. (%)","")) + "%",
                    str(row.get("Diversité (%)","") or row.get("Diversite (%)","")) + "%", statut
                ])
            hist_data  = hist_header + hist_rows
            hist_table = Table(hist_data, colWidths=[28*mm, 45*mm, 25*mm, 25*mm, 25*mm, 25*mm])
            hist_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), BLUE),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [GRAY_BG, colors.white]),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 5),
                ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#dddddd')),
            ]))
            elems.append(hist_table)

        elems.append(Spacer(1, 5*mm))
        suivi_data  = [[Paragraph(f"Prochain contrôle recommandé : dans {plan['suivi_semaines']} semaines",
                                   ParagraphStyle('SV', fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#856404')))]]
        suivi_table = Table(suivi_data, colWidths=[180*mm])
        suivi_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fff3cd')),
            ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        elems.append(suivi_table)
        elems.append(Spacer(1, 5*mm))

        footer_data  = [[Paragraph("Ce rapport est fourni à titre préventif et informatif. Il ne constitue pas un diagnostic médical.", small_style)],
                        [Paragraph("OralBiome — Microbiome Oral Prédictif | contact@oralbiome.com", small_style)]]
        footer_table = Table(footer_data, colWidths=[180*mm])
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_TEAL),
            ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elems.append(footer_table)
        doc.build(elems)
        return buffer.getvalue()

    except ImportError:
        content_lines = [
            f"OralBiome - Rapport Patient",
            f"Patient: {patient_nom}",
            f"Date: {date.today().strftime('%d/%m/%Y')}",
            f"",
            f"Risque Carieux: {r_carieux}",
            f"Risque Parodontal: {r_paro}",
            f"Diversite: {diversite}/100",
            f"",
            f"Profil: {plan['profil_label']}",
            f"Prochain controle: dans {plan['suivi_semaines']} semaines",
            f"",
            f"ATTENTION: Installez reportlab pour un rapport complet.",
        ]
        return "\n".join(content_lines).encode('ascii', errors='replace')


# ============================================================
# MOTEUR DE RECOMMANDATIONS
# ============================================================
def generer_recommandations(s_mutans, p_gingivalis, diversite):
    plan = {
        "priorites": [], "aliments_favoriser": [], "aliments_eviter": [],
        "probiotiques": [], "hygiene": [],
        "suivi_semaines": 24, "profil_label": "", "profil_description": ""
    }

    nb = sum([s_mutans > 3.0, p_gingivalis > 0.5, diversite < 50])
    if nb == 0:
        plan["profil_label"]       = "🟢 Microbiome Équilibré"
        plan["profil_description"] = "Votre flore buccale est protectrice. Continuez vos bonnes habitudes et revenez dans 6 mois."
        plan["suivi_semaines"]     = 24
    elif nb == 1:
        plan["profil_label"]       = "🟡 Déséquilibre Modéré"
        plan["profil_description"] = "Un déséquilibre est détecté. Des ajustements ciblés peuvent corriger la situation en 2 à 3 mois."
        plan["suivi_semaines"]     = 12
    else:
        plan["profil_label"]       = "🔴 Dysbiose Active"
        plan["profil_description"] = "Plusieurs marqueurs sont en alerte. Un plan d'action renforcé est nécessaire. Suivi dans 6 à 8 semaines recommandé."
        plan["suivi_semaines"]     = 8

    if s_mutans > 3.0:
        plan["priorites"].append({
            "icone": "🦠", "titre": "Réduire les bactéries acidogènes (S. mutans)",
            "urgence": "Elevee" if s_mutans > 6.0 else "Moderee",
            "explication": f"Taux de S. mutans : {s_mutans}% (normal < 3%). Ces bactéries produisent des acides qui dissolvent l'émail.",
            "actions": [
                "Brossage 2 min minimum après chaque repas sucré",
                "Fil dentaire quotidien le soir avant le coucher",
                "Bain de bouche fluoré 1x/jour sans alcool",
                "Éviter de grignoter entre les repas"
            ]
        })
        plan["aliments_eviter"]    += ["Bonbons et sucreries", "Sodas et boissons sucrées", "Pain blanc et viennoiseries", "Chocolat au lait entre les repas", "Jus de fruits (fructose élevé)"]
        plan["aliments_favoriser"] += ["Fromage à pâte dure (Gruyère, Comté)", "Yaourt nature sans sucre", "Légumes crus et croquants", "Thé vert sans sucre", "Eau plate entre les repas", "Noix et amandes"]
        plan["probiotiques"].append({"nom": "Lactobacillus reuteri (souche DSM 17938)", "forme": "Comprimés à sucer 1x/jour après brossage du soir", "duree": "3 mois minimum", "benefice": "Inhibe S. mutans et réduit la plaque acide", "marques": "BioGaia Prodentis, Sunstar GUM PerioBalance"})

    if p_gingivalis > 0.5:
        plan["priorites"].append({
            "icone": "🩸", "titre": "Éliminer les pathogènes parodontaux (complexe rouge)",
            "urgence": "Elevee" if p_gingivalis > 1.5 else "Moderee",
            "explication": f"Taux de P. gingivalis : {p_gingivalis}% (normal < 0.5%). Ces bactéries attaquent l'os qui maintient vos dents.",
            "actions": [
                "Nettoyage interdentaire quotidien — PRIORITÉ N°1",
                "Brossage de la langue matin et soir",
                "Consultation parodontale si gencives qui saignent",
                "Arrêt du tabac si applicable (multiplie ×3 le risque)"
            ]
        })
        plan["aliments_eviter"]    += ["Tabac sous toutes formes", "Alcool en excès", "Viandes rouges en excès", "Sucres raffinés", "Aliments ultra-transformés"]
        plan["aliments_favoriser"] += ["Poissons gras 2-3×/semaine (oméga-3)", "Myrtilles et framboises (polyphénols)", "Légumes verts feuillus (nitrates)", "Huile d'olive extra vierge", "Ail et oignon crus (allicine)", "Agrumes modérés (vitamine C)"]
        plan["probiotiques"].append({"nom": "Lactobacillus reuteri + Lactobacillus salivarius", "forme": "Pastilles à dissoudre en bouche 2x/jour", "duree": "3 à 6 mois", "benefice": "Réduit P. gingivalis et le saignement gingival", "marques": "Sunstar GUM PerioBalance, Blis K12"})

    if diversite < 50:
        plan["priorites"].append({
            "icone": "🌱", "titre": "Restaurer la diversité microbienne orale",
            "urgence": "Moderee" if diversite > 30 else "Elevee",
            "explication": f"Score de diversité : {diversite}/100 (optimal > 65). Une flore appauvrie ne se défend pas contre les pathogènes.",
            "actions": [
                "Diversifier : objectif 30 plantes différentes par semaine",
                "Réduire les bains de bouche antiseptiques quotidiens",
                "Augmenter les fibres prébiotiques (poireau, ail, oignon)",
                "Boire 1,5 L d'eau par jour minimum"
            ]
        })
        plan["aliments_favoriser"] += ["Légumes racines variés (fibres prébiotiques)", "Pomme avec la peau (pectine)", "Légumineuses (lentilles, pois chiches)", "Céréales complètes", "Légumes fermentés (choucroute, kimchi)", "Kombucha sans sucre ajouté"]
        plan["aliments_eviter"]    += ["Bains de bouche antiseptiques quotidiens", "Antibiotiques inutiles", "Fast-food régulier"]
        plan["probiotiques"].append({"nom": "Streptococcus salivarius K12 + M18", "forme": "Pastilles à sucer le soir après brossage", "duree": "2 à 3 mois puis entretien trimestriel", "benefice": "Recolonise la flore avec des espèces protectrices", "marques": "BLIS K12, Nasal Guard Throat Guard"})

    if nb == 0:
        plan["priorites"].append({
            "icone": "✅", "titre": "Maintenir l'équilibre de votre microbiome",
            "urgence": "Routine",
            "explication": "Votre microbiome oral est en bonne santé. Préservez cet équilibre sur le long terme.",
            "actions": ["Brossage 2×/jour avec brosse souple", "Fil dentaire 1×/jour", "Alimentation variée riche en fibres", "Contrôle dans 6 mois"]
        })
        plan["aliments_favoriser"] += ["Alimentation méditerranéenne variée", "Eau comme boisson principale", "Produits laitiers fermentés (yaourt, kéfir)", "Légumes crucifères (brocoli, chou)"]

    plan["hygiene"] = [
        {"moment": "☀️ Matin", "actions": ["Brossage 2 min brosse souple (électrique recommandée)", "Brossage de la langue arrière vers avant", "Bain de bouche non-alcoolisé si recommandé"]},
        {"moment": "🌙 Soir (le plus important)", "actions": ["Fil dentaire ou brossettes AVANT le brossage", "Brossage 2 min minimum", "Probiotique oral à dissoudre si prescrit", "Ne plus rien manger ni boire après (sauf eau)"]},
        {"moment": "🍽️ Après les repas", "actions": ["Attendre 30 min avant de brosser (émail fragilisé)", "Boire un verre d'eau pour rincer", "Chewing-gum xylitol 5 min si pas de brossage possible"]}
    ]

    plan["aliments_favoriser"] = list(dict.fromkeys(plan["aliments_favoriser"]))
    plan["aliments_eviter"]    = list(dict.fromkeys(plan["aliments_eviter"]))
    return plan


# ============================================================
# CONFIGURATION PAGE
# ============================================================
st.set_page_config(page_title="OralBiome", page_icon="🦷", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,600;1,9..144,300&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.stApp {
    background: #F0F4F8;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1100px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A1628 0%, #0D1E38 60%, #0F2545 100%);
    border-right: 1px solid rgba(0,194,168,0.15);
}
[data-testid="stSidebar"] * { color: #E8EEF5 !important; }
[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(0,194,168,0.3) !important;
    color: #E8EEF5 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(0,194,168,0.2) !important; }

/* ── Sidebar metric blocks ── */
.sidebar-metric {
    background: rgba(0,194,168,0.1);
    border: 1px solid rgba(0,194,168,0.2);
    border-radius: 10px;
    padding: 10px 14px;
    text-align: center;
    margin: 4px 0;
}
.sidebar-metric .val { font-size: 1.6rem; font-weight: 700; color: #00C2A8 !important; }
.sidebar-metric .lbl { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: #8A9BB5 !important; }

/* ── Sidebar nav buttons ── */
.nav-btn {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 14px; border-radius: 8px; margin: 2px 0;
    cursor: pointer; transition: all .2s;
    font-size: 0.85rem; font-weight: 500;
    background: transparent; border: none;
    color: #A8B8CC !important; width: 100%;
}
.nav-btn:hover { background: rgba(0,194,168,0.12); color: #00C2A8 !important; }
.nav-btn.active { background: rgba(0,194,168,0.18); color: #00C2A8 !important; border-left: 3px solid #00C2A8; }

/* ── Page header card ── */
.page-hero {
    background: linear-gradient(135deg, #0A1628 0%, #112240 50%, #0D2137 100%);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.page-hero::before {
    content: '';
    position: absolute; top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(0,194,168,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.page-hero h1 { font-family: 'Fraunces', serif; font-size: 1.9rem; font-weight: 400; color: #FFFFFF; margin: 0 0 4px 0; }
.page-hero p  { color: #8A9BB5; font-size: 0.9rem; margin: 0; }
.page-hero .badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(0,194,168,0.15); border: 1px solid rgba(0,194,168,0.3);
    color: #00C2A8; border-radius: 20px; padding: 4px 12px;
    font-size: 0.78rem; font-weight: 600; letter-spacing: 0.05em;
    margin-top: 10px;
}
.page-hero .badge-red {
    background: rgba(220,53,69,0.15); border-color: rgba(220,53,69,0.3); color: #FF6B7A;
}

/* ── KPI cards ── */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
.kpi-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 18px 20px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 8px rgba(10,22,40,0.06);
    transition: transform .2s, box-shadow .2s;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(10,22,40,0.1); }
.kpi-card .kpi-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #8A9BB5; margin-bottom: 6px; }
.kpi-card .kpi-value { font-size: 1.55rem; font-weight: 700; color: #0A1628; line-height: 1.1; }
.kpi-card .kpi-sub   { font-size: 0.75rem; margin-top: 4px; }
.kpi-card .kpi-bar   { height: 4px; border-radius: 2px; margin-top: 10px; background: #E2E8F0; }
.kpi-card .kpi-fill  { height: 100%; border-radius: 2px; transition: width .6s ease; }
.kpi-ok   { border-top: 3px solid #00C2A8; }
.kpi-warn { border-top: 3px solid #F59E0B; }
.kpi-bad  { border-top: 3px solid #EF4444; }

/* ── Section cards ── */
.section-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 24px 26px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 8px rgba(10,22,40,0.05);
    margin-bottom: 16px;
}
.section-title {
    font-family: 'Fraunces', serif;
    font-size: 1.1rem; font-weight: 400; color: #0A1628;
    margin: 0 0 16px 0; padding-bottom: 12px;
    border-bottom: 1px solid #E2E8F0;
    display: flex; align-items: center; gap: 8px;
}

/* ── Priority cards ── */
.priority-card {
    border-radius: 12px; padding: 16px 18px; margin-bottom: 12px;
    border-left: 4px solid;
}
.priority-high   { background: #FFF5F5; border-color: #EF4444; }
.priority-medium { background: #FFFBEB; border-color: #F59E0B; }
.priority-low    { background: #F0FDF9; border-color: #00C2A8; }
.priority-card h4 { margin: 0 0 4px 0; font-size: 0.95rem; font-weight: 600; color: #0A1628; }
.priority-card p  { margin: 0 0 8px 0; font-size: 0.82rem; color: #5A7090; font-style: italic; }
.priority-card ul { margin: 0; padding-left: 16px; }
.priority-card li { font-size: 0.83rem; color: #374151; margin-bottom: 3px; }
.badge-urgence {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em;
    margin-left: 8px; vertical-align: middle;
}
.badge-high   { background: #FEE2E2; color: #DC2626; }
.badge-medium { background: #FEF3C7; color: #D97706; }
.badge-low    { background: #D1FAF3; color: #047857; }

/* ── Nutrition pills ── */
.pill-wrap { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.pill {
    padding: 5px 14px; border-radius: 20px;
    font-size: 0.8rem; font-weight: 500;
    transition: transform .15s;
}
.pill:hover { transform: scale(1.04); }
.pill-green { background: #E6FBF7; color: #047857; border: 1px solid #A7F3D0; }
.pill-red   { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }

/* ── Probiotic card ── */
.probiotic-card {
    background: linear-gradient(135deg, #F0F9FF 0%, #E0F7F5 100%);
    border: 1px solid #BAE6FD; border-radius: 12px; padding: 16px 18px; margin-bottom: 10px;
}
.probiotic-card h4 { margin: 0 0 10px 0; font-size: 0.9rem; font-weight: 600; color: #0A1628; }
.probiotic-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.probiotic-item { font-size: 0.8rem; color: #374151; }
.probiotic-item span { font-weight: 600; color: #0A1628; }

/* ── Hygiene timeline ── */
.hygiene-step {
    display: flex; gap: 14px; margin-bottom: 16px;
}
.hygiene-dot {
    width: 36px; height: 36px; border-radius: 50%;
    background: linear-gradient(135deg, #0A1628, #1B4F8A);
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0; margin-top: 2px;
}
.hygiene-content h4 { margin: 0 0 6px 0; font-size: 0.9rem; font-weight: 600; color: #0A1628; }
.hygiene-content ul { margin: 0; padding-left: 14px; }
.hygiene-content li { font-size: 0.82rem; color: #4B5563; margin-bottom: 3px; }

/* ── Table styling ── */
.stDataFrame { border-radius: 12px !important; overflow: hidden !important; }
[data-testid="stDataFrameResizable"] { border-radius: 12px !important; }

/* ── Login card ── */
.login-wrapper {
    max-width: 420px; margin: 0 auto; padding-top: 2rem;
}
.login-card {
    background: #FFFFFF; border-radius: 20px;
    padding: 40px; box-shadow: 0 8px 40px rgba(10,22,40,0.1);
    border: 1px solid #E2E8F0;
}
.login-logo { text-align: center; margin-bottom: 28px; }
.login-logo h1 { font-family: 'Fraunces', serif; font-size: 2rem; color: #0A1628; margin: 0; }
.login-logo p  { color: #8A9BB5; font-size: 0.85rem; margin: 4px 0 0 0; }
.login-divider { height: 1px; background: #E2E8F0; margin: 20px 0; }

/* ── Welcome screen ── */
.welcome-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-top: 24px; }
.welcome-card {
    background: #FFFFFF; border-radius: 16px; padding: 28px 24px;
    border: 1px solid #E2E8F0; box-shadow: 0 2px 12px rgba(10,22,40,0.06);
    text-align: center; transition: transform .2s, box-shadow .2s;
    cursor: pointer;
}
.welcome-card:hover { transform: translateY(-4px); box-shadow: 0 10px 30px rgba(10,22,40,0.12); }
.welcome-card .wc-icon { font-size: 2.5rem; margin-bottom: 14px; }
.welcome-card h3 { font-family: 'Fraunces', serif; font-size: 1.2rem; font-weight: 400; color: #0A1628; margin: 0 0 8px 0; }
.welcome-card p  { font-size: 0.83rem; color: #5A7090; margin: 0; line-height: 1.5; }
.welcome-card .wc-btn {
    display: inline-block; margin-top: 18px; padding: 9px 22px; border-radius: 8px;
    font-size: 0.82rem; font-weight: 600; text-decoration: none;
}
.wc-primary .wc-btn { background: #0A1628; color: #FFFFFF; }
.wc-secondary .wc-btn { background: #E0F7F5; color: #047857; }

/* ── Streamlit native overrides ── */
.stButton button {
    border-radius: 9px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    transition: all .2s !important;
}
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #0A1628, #1B4F8A) !important;
    border: none !important;
    color: #FFFFFF !important;
}
.stButton button[kind="primary"]:hover {
    background: linear-gradient(135deg, #0D2137, #2460A7) !important;
    box-shadow: 0 4px 12px rgba(10,22,40,0.25) !important;
    transform: translateY(-1px) !important;
}
.stTextInput input, .stSelectbox select, .stNumberInput input, .stDateInput input {
    border-radius: 9px !important;
    border: 1px solid #CBD5E1 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: #F0F4F8 !important;
    border-radius: 12px !important; padding: 4px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: #5A7090 !important;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #0A1628 !important;
    box-shadow: 0 1px 6px rgba(10,22,40,0.1) !important;
}
.stAlert { border-radius: 10px !important; }
.stExpander { border-radius: 10px !important; border: 1px solid #E2E8F0 !important; }

/* ── Patient list row ── */
.patient-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 16px; border-radius: 10px; margin-bottom: 8px;
    background: #FFFFFF; border: 1px solid #E2E8F0;
    transition: box-shadow .2s;
}
.patient-row:hover { box-shadow: 0 3px 12px rgba(10,22,40,0.08); }
.patient-row .pr-name { font-weight: 600; color: #0A1628; font-size: 0.9rem; }
.patient-row .pr-sub  { font-size: 0.75rem; color: #8A9BB5; }
.patient-row .pr-badge {
    padding: 3px 10px; border-radius: 20px; font-size: 0.73rem; font-weight: 600;
}
.pr-ok   { background: #D1FAF3; color: #047857; }
.pr-warn { background: #FEE2E2; color: #DC2626; }

/* ── Info box ── */
.info-box {
    background: linear-gradient(135deg, #EFF6FF, #E0F7F5);
    border: 1px solid #BAE6FD; border-radius: 10px;
    padding: 12px 16px; margin: 12px 0;
    font-size: 0.83rem; color: #0A1628;
}
.info-box strong { color: #00C2A8; }

/* ── Divider ── */
.ob-divider { height: 1px; background: linear-gradient(90deg, transparent, #CBD5E1, transparent); margin: 20px 0; }

/* ── Charts label override ── */
.stMetric { background: white; border-radius: 12px; padding: 16px !important; border: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# DONNÉES INITIALES
# ============================================================
def donnees_initiales():
    patients = {}

    df1 = pd.DataFrame(columns=["Date","Acte / Test","S. mutans (%)","P. gingiv. (%)","Diversite (%)","Status"])
    df1.loc[0] = ["12/10/2023","Examen Initial",4.2,0.8,45,"Alerte"]
    df1.loc[1] = ["08/04/2026","Contrôle",4.2,0.3,75,"Stable"]
    patients["Jean Dupont"] = {
        "id":"P001","nom":"Jean Dupont","age":42,"email":"jean.dupont@email.com",
        "telephone":"+32 472 123 456","date_naissance":"15/03/1982",
        "historique":df1,"s_mutans":4.2,"p_gingivalis":0.3,"diversite":75,"code_patient":"OB-P001"
    }

    df2 = pd.DataFrame(columns=["Date","Acte / Test","S. mutans (%)","P. gingiv. (%)","Diversite (%)","Status"])
    df2.loc[0] = ["05/01/2024","Examen Initial",1.2,0.1,82,"Stable"]
    patients["Marie Martin"] = {
        "id":"P002","nom":"Marie Martin","age":35,"email":"marie.martin@email.com",
        "telephone":"+32 478 654 321","date_naissance":"22/07/1989",
        "historique":df2,"s_mutans":1.2,"p_gingivalis":0.1,"diversite":82,"code_patient":"OB-P002"
    }

    df3 = pd.DataFrame(columns=["Date","Acte / Test","S. mutans (%)","P. gingiv. (%)","Diversite (%)","Status"])
    df3.loc[0] = ["18/02/2025","Examen Initial",6.5,1.8,38,"Alerte"]
    patients["Pierre Bernard"] = {
        "id":"P003","nom":"Pierre Bernard","age":58,"email":"pierre.bernard@email.com",
        "telephone":"+32 495 789 012","date_naissance":"03/11/1966",
        "historique":df3,"s_mutans":6.5,"p_gingivalis":1.8,"diversite":38,"code_patient":"OB-P003"
    }
    return patients


# ============================================================
# INIT SESSION
# ============================================================
if 'mode'             not in st.session_state: st.session_state.mode             = "choix"
if 'connecte'         not in st.session_state: st.session_state.connecte         = False
if 'patients'         not in st.session_state: st.session_state.patients         = donnees_initiales()
if 'patient_sel'      not in st.session_state: st.session_state.patient_sel      = "Jean Dupont"
if 'vue'              not in st.session_state: st.session_state.vue              = "dossier"
if 'patient_connecte' not in st.session_state: st.session_state.patient_connecte = None


# ============================================================
# HELPERS UI
# ============================================================
def render_kpi(label, value, sub, status="ok", bar_pct=None):
    cls   = {"ok":"kpi-ok","warn":"kpi-warn","bad":"kpi-bad"}.get(status,"kpi-ok")
    color = {"ok":"#00C2A8","warn":"#F59E0B","bad":"#EF4444"}.get(status,"#00C2A8")
    sub_color = {"ok":"color:#047857","warn":"color:#D97706","bad":"color:#DC2626"}.get(status,"")
    bar_html = ""
    if bar_pct is not None:
        bar_html = f"""
        <div class="kpi-bar">
          <div class="kpi-fill" style="width:{bar_pct}%;background:{color};"></div>
        </div>"""
    return f"""
    <div class="kpi-card {cls}">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-sub" style="{sub_color}">{sub}</div>
      {bar_html}
    </div>"""

def status_patient(p):
    return p["s_mutans"] > 3.0 or p["p_gingivalis"] > 0.5 or p["diversite"] < 50

def profil_sans_emoji(label):
    return label.replace("🟢","").replace("🟡","").replace("🔴","").strip()


# ============================================================
# ÉCRAN CHOIX
# ============================================================
if st.session_state.mode == "choix":
    st.markdown("""
    <div style="text-align:center;padding:40px 0 20px;">
      <div style="font-family:'Fraunces',serif;font-size:3rem;color:#0A1628;letter-spacing:-0.02em;">🦷 OralBiome</div>
      <div style="color:#8A9BB5;font-size:1rem;margin-top:6px;">Microbiome Oral Prédictif — Wallonie, Belgique</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="welcome-grid">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="welcome-card wc-primary">
          <div class="wc-icon">🩺</div>
          <h3>Praticien</h3>
          <p>Tableau de bord complet, gestion des dossiers patients, analyses et génération de rapports.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("Connexion Praticien", use_container_width=True, type="primary"):
            st.session_state.mode = "praticien"; st.rerun()

    with col2:
        st.markdown("""
        <div class="welcome-card wc-secondary">
          <div class="wc-icon">🧑</div>
          <h3>Patient</h3>
          <p>Consultez votre rapport personnalisé, plan nutritionnel et historique d'analyses.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("Espace Patient", use_container_width=True):
            st.session_state.mode = "patient"; st.rerun()

    with col3:
        st.markdown("""
        <div class="welcome-card">
          <div class="wc-icon">🔬</div>
          <h3>À propos</h3>
          <p>OralBiome analyse votre microbiome oral pour une prévention dentaire et systémique personnalisée.</p>
        </div>""", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box" style="margin-top:8px;">
          <strong>contact@oralbiome.com</strong><br>
          Wallonie · Version 1.0 · 2026
        </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# PORTAIL PATIENT
# ============================================================
elif st.session_state.mode == "patient":

    if st.session_state.patient_connecte is None:
        # ── Login patient ──
        st.markdown("""
        <div class="login-wrapper">
          <div class="login-card">
            <div class="login-logo">
              <h1>🦷 OralBiome</h1>
              <p>Espace Patient — Accès sécurisé</p>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        _, col, _ = st.columns([1,1.2,1])
        with col:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            code = st.text_input("Code patient", placeholder="Ex : OB-P001", label_visibility="visible")
            st.caption("Votre code vous a été communiqué par votre praticien.")
            if st.button("Accéder à mon dossier", use_container_width=True, type="primary"):
                found = next((n for n,d in st.session_state.patients.items() if d.get("code_patient")==code.strip()), None)
                if found:
                    st.session_state.patient_connecte = found; st.rerun()
                else:
                    st.error("Code invalide. Vérifiez avec votre praticien.")
            st.markdown("<div class='login-divider'></div>", unsafe_allow_html=True)
            if st.button("← Retour à l'accueil", use_container_width=True):
                st.session_state.mode = "choix"; st.rerun()
            st.caption("Codes démo : OB-P001 · OB-P002 · OB-P003")

    else:
        patient     = st.session_state.patients[st.session_state.patient_connecte]
        s_mutans    = patient["s_mutans"]
        p_gingivalis= patient["p_gingivalis"]
        diversite   = patient["diversite"]
        r_carieux   = "Élevé" if s_mutans    > 3.0 else "Faible"
        r_paro      = "Élevé" if p_gingivalis > 0.5 else "Faible"
        en_alerte   = r_carieux=="Élevé" or r_paro=="Élevé" or diversite<50
        plan        = generer_recommandations(s_mutans, p_gingivalis, diversite)
        prenom      = patient['nom'].split()[0]

        # Sidebar patient
        with st.sidebar:
            st.markdown(f"""
            <div style="padding:20px 0 10px; text-align:center;">
              <div style="font-family:'Fraunces',serif;font-size:1.6rem;color:#00C2A8;">🦷 OralBiome</div>
              <div style="font-size:0.75rem;color:#4A6080;margin-top:2px;">Microbiome Oral Prédictif</div>
            </div>""", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown(f"""
            <div style="padding:12px 0;">
              <div style="font-size:0.75rem;color:#4A6080;text-transform:uppercase;letter-spacing:0.06em;">Patient</div>
              <div style="font-weight:600;font-size:1rem;margin-top:2px;">{patient['nom']}</div>
              <div style="font-size:0.75rem;color:#4A6080;font-family:monospace;">{patient['code_patient']}</div>
            </div>""", unsafe_allow_html=True)
            st.markdown("---")
            statut_txt = "🔴 En alerte" if en_alerte else "🟢 Équilibré"
            st.markdown(f"""
            <div class="sidebar-metric"><div class="val">{statut_txt}</div><div class="lbl">Statut</div></div>
            <div class="sidebar-metric"><div class="val">{plan['suivi_semaines']} sem</div><div class="lbl">Prochain contrôle</div></div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            if st.button("Se déconnecter", use_container_width=True):
                st.session_state.patient_connecte = None; st.rerun()
            if st.button("← Accueil", use_container_width=True):
                st.session_state.patient_connecte = None; st.session_state.mode = "choix"; st.rerun()

        # Hero
        badge_cls = "badge badge-red" if en_alerte else "badge"
        st.markdown(f"""
        <div class="page-hero">
          <h1>Bonjour, {prenom} 👋</h1>
          <p>Rapport de microbiome oral personnalisé — {date.today().strftime('%d %B %Y')}</p>
          <span class="{badge_cls}">{'⚠ ' if en_alerte else '✓ '}{profil_sans_emoji(plan['profil_label'])}</span>
        </div>""", unsafe_allow_html=True)

        # KPI row
        sm_st  = "bad"  if s_mutans    > 3.0 else "ok"
        pg_st  = "bad"  if p_gingivalis > 0.5 else "ok"
        div_st = "bad"  if diversite   < 50   else "warn" if diversite < 65 else "ok"

        st.markdown(f"""
        <div class="kpi-row">
          {render_kpi("S. mutans", f"{s_mutans}%", "Normal < 3%", sm_st, min(s_mutans/10*100,100))}
          {render_kpi("P. gingivalis", f"{p_gingivalis}%", "Normal < 0.5%", pg_st, min(p_gingivalis/5*100,100))}
          {render_kpi("Diversité", f"{diversite}/100", "Optimal > 65", div_st, diversite)}
          {render_kpi("Prochain contrôle", f"{plan['suivi_semaines']} sem", profil_sans_emoji(plan['profil_label']), "ok")}
        </div>""", unsafe_allow_html=True)

        # Onglets
        tp1, tp2, tp3, tp4, tp5 = st.tabs(["📊 Mon Profil","🚨 Mes Actions","🥗 Nutrition","🪥 Hygiène","📥 Rapport PDF"])

        with tp1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🔬 Analyse du microbiome</div>', unsafe_allow_html=True)

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"""
                <div style="text-align:center;padding:12px;">
                  <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;color:#8A9BB5;">S. mutans</div>
                  <div style="font-size:2.2rem;font-weight:700;color:{'#EF4444' if s_mutans>3 else '#00C2A8'};">{s_mutans}%</div>
                  <div style="font-size:0.75rem;color:#8A9BB5;">Normal &lt; 3%</div>
                </div>""", unsafe_allow_html=True)
                if s_mutans > 3:
                    st.error("Taux trop élevé — risque carieux actif")
                else:
                    st.success("Taux normal — émail protégé")

            with col_b:
                st.markdown(f"""
                <div style="text-align:center;padding:12px;">
                  <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;color:#8A9BB5;">P. gingivalis</div>
                  <div style="font-size:2.2rem;font-weight:700;color:{'#EF4444' if p_gingivalis>0.5 else '#00C2A8'};">{p_gingivalis}%</div>
                  <div style="font-size:0.75rem;color:#8A9BB5;">Normal &lt; 0.5%</div>
                </div>""", unsafe_allow_html=True)
                if p_gingivalis > 0.5:
                    st.error("Taux trop élevé — risque parodontal")
                else:
                    st.success("Taux normal — gencives protégées")

            with col_c:
                div_color = "#EF4444" if diversite<50 else "#F59E0B" if diversite<65 else "#00C2A8"
                st.markdown(f"""
                <div style="text-align:center;padding:12px;">
                  <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;color:#8A9BB5;">Diversité</div>
                  <div style="font-size:2.2rem;font-weight:700;color:{div_color};">{diversite}/100</div>
                  <div style="font-size:0.75rem;color:#8A9BB5;">Optimal &gt; 65</div>
                </div>""", unsafe_allow_html=True)
                if   diversite < 50: st.error("Flore appauvrie — vulnérabilité accrue")
                elif diversite < 65: st.warning("Flore modérée — peut être améliorée")
                else:                st.success("Flore riche et protectrice")

            st.markdown('</div>', unsafe_allow_html=True)

            if not patient["historique"].empty:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">📅 Historique des analyses</div>', unsafe_allow_html=True)
                st.dataframe(patient["historique"], use_container_width=True, hide_index=True)
                if len(patient["historique"]) > 1:
                    df_g = patient["historique"].copy().reset_index(drop=True)
                    gc1, gc2 = st.columns(2)
                    with gc1:
                        st.caption("Evolution bactérienne")
                        st.line_chart(df_g[["S. mutans (%)", "P. gingiv. (%)"]].astype(float))
                    with gc2:
                        st.caption("Diversité microbienne")
                        d_col = [c for c in df_g.columns if "iversit" in c]
                        if d_col: st.line_chart(df_g[d_col].astype(float))
                st.markdown('</div>', unsafe_allow_html=True)

        with tp2:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🚨 Plan d\'action prioritaire</div>', unsafe_allow_html=True)
            for i, p in enumerate(plan["priorites"]):
                urg   = p["urgence"]
                cls   = "priority-high" if urg=="Elevee" else "priority-medium" if urg=="Moderee" else "priority-low"
                bcls  = "badge-high"    if urg=="Elevee" else "badge-medium"    if urg=="Moderee" else "badge-low"
                btxt  = "URGENT"        if urg=="Elevee" else "MODÉRÉ"          if urg=="Moderee" else "ROUTINE"
                li_items = "".join(f"<li>{a}</li>" for a in p["actions"])
                st.markdown(f"""
                <div class="priority-card {cls}">
                  <h4>{p['icone']} Action {i+1} — {p['titre']}
                    <span class="badge-urgence {bcls}">{btxt}</span>
                  </h4>
                  <p>{p['explication']}</p>
                  <ul>{li_items}</ul>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with tp3:
            col_f, col_e = st.columns(2)
            with col_f:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">✅ Aliments à favoriser</div>', unsafe_allow_html=True)
                pills = "".join(f'<span class="pill pill-green">{a}</span>' for a in plan["aliments_favoriser"])
                st.markdown(f'<div class="pill-wrap">{pills}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with col_e:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">❌ Aliments à limiter</div>', unsafe_allow_html=True)
                pills = "".join(f'<span class="pill pill-red">{a}</span>' for a in plan["aliments_eviter"])
                st.markdown(f'<div class="pill-wrap">{pills}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            if plan["probiotiques"]:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">💊 Probiotiques recommandés</div>', unsafe_allow_html=True)
                for prob in plan["probiotiques"]:
                    st.markdown(f"""
                    <div class="probiotic-card">
                      <h4>🧫 {prob['nom']}</h4>
                      <div class="probiotic-grid">
                        <div class="probiotic-item"><span>Forme :</span> {prob['forme']}</div>
                        <div class="probiotic-item"><span>Durée :</span> {prob['duree']}</div>
                        <div class="probiotic-item"><span>Bénéfice :</span> {prob['benefice']}</div>
                        <div class="probiotic-item"><span>Produits :</span> {prob['marques']}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        with tp4:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🪥 Protocole d\'hygiène personnalisé</div>', unsafe_allow_html=True)
            for m in plan["hygiene"]:
                li_items = "".join(f"<li>{a}</li>" for a in m["actions"])
                st.markdown(f"""
                <div class="hygiene-step">
                  <div class="hygiene-content">
                    <h4>{m['moment']}</h4>
                    <ul>{li_items}</ul>
                  </div>
                </div>""", unsafe_allow_html=True)
                st.markdown('<div class="ob-divider"></div>', unsafe_allow_html=True)

            if   r_paro     == "Élevé": st.info("💡 Le nettoyage interdentaire est plus important que le brossage. 5 min de fil dentaire le soir = protection maximale.")
            elif r_carieux  == "Élevé": st.warning("⏱ Le timing des repas est aussi important que l'hygiène. Chaque prise alimentaire relance les acides pendant 20 min.")
            else:                        st.success("✅ Votre routine est efficace. Continuez et revenez dans 6 mois.")
            st.markdown('</div>', unsafe_allow_html=True)

        with tp5:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📥 Télécharger mon rapport complet</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="info-box">
              Ce rapport PDF personnalisé contient votre <strong>profil bactérien</strong>,
              votre <strong>plan d'action</strong>, votre <strong>nutrition</strong>,
              vos <strong>probiotiques</strong> et votre <strong>protocole d'hygiène</strong>.
            </div>""", unsafe_allow_html=True)
            try:
                pdf_bytes = generer_pdf(patient["nom"], r_carieux, r_paro, diversite, patient["historique"], plan)
                st.download_button(
                    label="📥 Télécharger mon Rapport OralBiome (PDF)",
                    data=pdf_bytes,
                    file_name=f"OralBiome_Rapport_{patient['id']}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
                st.success("Rapport prêt. Partagez-le avec votre médecin si besoin.")
            except Exception as e:
                st.error(f"Erreur PDF : {e}")
                st.info("Ajoutez 'reportlab' dans requirements.txt")
            st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# PORTAIL PRATICIEN
# ============================================================
elif st.session_state.mode == "praticien":

    if not st.session_state.connecte:
        st.markdown("""
        <div class="login-wrapper">
          <div class="login-card">
            <div class="login-logo">
              <h1>🦷 OralBiome</h1>
              <p>Portail Praticien — Accès sécurisé</p>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        _, col, _ = st.columns([1,1.2,1])
        with col:
            email = st.text_input("Email professionnel", placeholder="contact@oralbiome.com")
            mdp   = st.text_input("Mot de passe", type="password")
            if st.button("Connexion", use_container_width=True, type="primary"):
                if email == "contact@oralbiome.com" and mdp == "mvp2024":
                    st.session_state.connecte = True; st.rerun()
                else:
                    st.error("Identifiants incorrects. Utilisez contact@oralbiome.com / mvp2024")
            st.markdown("<div class='ob-divider'></div>", unsafe_allow_html=True)
            if st.button("← Retour à l'accueil", use_container_width=True):
                st.session_state.mode = "choix"; st.rerun()

    else:
        # ── Sidebar praticien ──
        with st.sidebar:
            st.markdown("""
            <div style="padding:20px 0 10px; text-align:center;">
              <div style="font-family:'Fraunces',serif;font-size:1.6rem;color:#00C2A8;">🦷 OralBiome</div>
              <div style="font-size:0.72rem;color:#4A6080;margin-top:2px;">Portail Praticien</div>
            </div>""", unsafe_allow_html=True)
            st.markdown("---")

            nb_patients = len(st.session_state.patients)
            nb_alertes  = sum(1 for p in st.session_state.patients.values() if status_patient(p))

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f'<div class="sidebar-metric"><div class="val">{nb_patients}</div><div class="lbl">Patients</div></div>', unsafe_allow_html=True)
            with col_b:
                st.markdown(f'<div class="sidebar-metric"><div class="val" style="color:{"#FF6B7A" if nb_alertes else "#00C2A8"}">{nb_alertes}</div><div class="lbl">Alertes</div></div>', unsafe_allow_html=True)

            st.markdown("---")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("👥 Patients", use_container_width=True):
                    st.session_state.vue = "liste"; st.rerun()
            with b2:
                if st.button("➕ Nouveau", use_container_width=True):
                    st.session_state.vue = "nouveau"; st.rerun()

            st.markdown("---")
            rech = st.text_input("🔍 Rechercher...", placeholder="Nom ou ID")
            pf   = {n: d for n,d in st.session_state.patients.items()
                    if rech.lower() in n.lower() or rech.lower() in d["id"].lower()} if rech else st.session_state.patients

            st.markdown("<div style='font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;color:#4A6080;margin-bottom:8px;'>Accès rapide</div>", unsafe_allow_html=True)
            for nom, data in pf.items():
                icon    = "🔴" if status_patient(data) else "🟢"
                is_sel  = nom == st.session_state.patient_sel
                btn_type= "primary" if is_sel else "secondary"
                if st.button(f"{icon} {data['id']} — {nom}", use_container_width=True, type=btn_type):
                    st.session_state.patient_sel = nom; st.session_state.vue = "dossier"; st.rerun()

            st.markdown("---")
            if st.button("🚪 Déconnecter", use_container_width=True):
                st.session_state.connecte = False; st.rerun()
            if st.button("← Accueil", use_container_width=True):
                st.session_state.connecte = False; st.session_state.mode = "choix"; st.rerun()

        # ── VUE LISTE ──
        if st.session_state.vue == "liste":
            st.markdown(f"""
            <div class="page-hero">
              <h1>👥 Gestion des patients</h1>
              <p>{nb_patients} patients enregistrés · {nb_alertes} alertes actives</p>
            </div>""", unsafe_allow_html=True)

            lf1, lf2, lf3 = st.columns([2,2,1])
            with lf1:
                filtre = st.selectbox("Filtrer par statut", ["Tous","Alerte uniquement","Stable uniquement"])
            with lf3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("➕ Nouveau patient", type="primary"):
                    st.session_state.vue = "nouveau"; st.rerun()

            donnees = []
            for nom, data in st.session_state.patients.items():
                ea = status_patient(data)
                if filtre == "Alerte uniquement" and not ea: continue
                if filtre == "Stable uniquement" and     ea: continue
                donnees.append({
                    "ID": data["id"], "Nom": nom, "Âge": data["age"],
                    "Code": data.get("code_patient",""),
                    "Risque Carieux":   "⚠ Élevé"  if data["s_mutans"]    > 3.0 else "✓ Faible",
                    "Risque Paro":      "⚠ Élevé"  if data["p_gingivalis"]> 0.5 else "✓ Faible",
                    "Diversité":        f"{data['diversite']}/100",
                    "Statut":           "🔴 Alerte" if ea else "🟢 Stable",
                    "Visites":          len(data["historique"])
                })

            if donnees:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(donnees), use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("**Ouvrir un dossier :**")
                cols = st.columns(min(len(st.session_state.patients), 4))
                for i, (nom, data) in enumerate(st.session_state.patients.items()):
                    with cols[i % 4]:
                        icon = "🔴" if status_patient(data) else "🟢"
                        if st.button(f"{icon} {nom}", use_container_width=True):
                            st.session_state.patient_sel = nom; st.session_state.vue = "dossier"; st.rerun()

        # ── VUE NOUVEAU ──
        elif st.session_state.vue == "nouveau":
            st.markdown("""
            <div class="page-hero">
              <h1>➕ Nouveau patient</h1>
              <p>Créer un dossier et enregistrer la première analyse</p>
            </div>""", unsafe_allow_html=True)

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            with st.form("form_nouveau"):
                nc1, nc2 = st.columns(2)
                with nc1:
                    nn       = st.text_input("Nom complet *")
                    ne       = st.text_input("Email")
                    nd_nais  = st.date_input("Date de naissance", value=date(1985, 1, 1))
                with nc2:
                    na  = st.number_input("Âge", 1, 120, 35)
                    nt  = st.text_input("Téléphone")

                st.markdown('<div class="ob-divider"></div>', unsafe_allow_html=True)
                st.markdown("**Première analyse microbiome**")
                nc3, nc4, nc5 = st.columns(3)
                with nc3: is_ = st.number_input("S. mutans (%)",    0.0, 10.0, 2.0, step=0.1)
                with nc4: ip_ = st.number_input("P. gingivalis (%)",0.0,  5.0, 0.2, step=0.1)
                with nc5: id_ = st.number_input("Diversité (%)",      0,  100,   70)
                aj  = st.checkbox("Enregistrer comme examen initial", value=True)
                sub = st.form_submit_button("Créer le dossier", use_container_width=True, type="primary")

                if sub:
                    if not nn.strip():
                        st.error("Le nom est obligatoire.")
                    elif nn in st.session_state.patients:
                        st.error("Ce patient existe déjà.")
                    else:
                        nid    = f"P{str(len(st.session_state.patients)+1).zfill(3)}"
                        code_p = f"OB-{nid}"
                        df_n   = pd.DataFrame(columns=["Date","Acte / Test","S. mutans (%)","P. gingiv. (%)","Diversite (%)","Status"])
                        if aj:
                            s = "Alerte" if is_ > 3.0 or ip_ > 0.5 or id_ < 50 else "Stable"
                            df_n.loc[0] = [date.today().strftime("%d/%m/%Y"),"Examen Initial",is_,ip_,id_,s]
                        st.session_state.patients[nn] = {
                            "id":nid,"nom":nn,"age":na,"email":ne,"telephone":nt,
                            "date_naissance":nd_nais.strftime("%d/%m/%Y"),
                            "historique":df_n,
                            "s_mutans":is_ if aj else 0.0,
                            "p_gingivalis":ip_ if aj else 0.0,
                            "diversite":id_ if aj else 70,
                            "code_patient":code_p
                        }
                        st.session_state.patient_sel = nn; st.session_state.vue = "dossier"
                        st.success(f"Dossier créé ! Code patient : **{code_p}**")
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ── VUE DOSSIER ──
        else:
            patient = st.session_state.patients.get(st.session_state.patient_sel)
            if not patient:
                st.error("Patient introuvable.")
            else:
                s_mutans     = patient["s_mutans"]
                p_gingivalis = patient["p_gingivalis"]
                diversite    = patient["diversite"]
                r_carieux    = "Élevé" if s_mutans    > 3.0 else "Faible"
                r_paro       = "Élevé" if p_gingivalis > 0.5 else "Faible"
                en_alerte    = r_carieux=="Élevé" or r_paro=="Élevé" or diversite<50
                plan         = generer_recommandations(s_mutans, p_gingivalis, diversite)

                badge_cls = "badge badge-red" if en_alerte else "badge"
                st.markdown(f"""
                <div class="page-hero">
                  <h1>🦷 {patient['nom']} <span style="font-size:1rem;font-family:'DM Sans',sans-serif;color:#4A7FAA;font-weight:400;">{patient['id']}</span></h1>
                  <p>{patient['age']} ans · {patient['email']} · Tél : {patient.get('telephone','')} · Né(e) le {patient.get('date_naissance','')}</p>
                  <span class="{badge_cls}">{'⚠ ' if en_alerte else '✓ '}{profil_sans_emoji(plan['profil_label'])}</span>
                </div>""", unsafe_allow_html=True)

                # KPIs
                sm_st  = "bad"  if s_mutans    > 3.0 else "ok"
                pg_st  = "bad"  if p_gingivalis > 0.5 else "ok"
                div_st = "bad"  if diversite   < 50   else "warn" if diversite < 65 else "ok"

                st.markdown(f"""
                <div class="kpi-row">
                  {render_kpi("Risque Carieux",    r_carieux,             f"S. mutans : {s_mutans}%",    sm_st,  min(s_mutans/10*100,100))}
                  {render_kpi("Risque Parodontal", r_paro,                f"P. gingiv. : {p_gingivalis}%", pg_st, min(p_gingivalis/5*100,100))}
                  {render_kpi("Diversité",          f"{diversite}/100",    "Optimal > 65",                div_st, diversite)}
                  {render_kpi("Visites",            len(patient['historique']), f"Code : {patient.get('code_patient','')}","ok")}
                </div>""", unsafe_allow_html=True)

                # Code patient
                st.markdown(f"""
                <div class="info-box">
                  Code d'accès patient : <strong>{patient.get('code_patient','')}</strong>
                  — Communiquez ce code au patient pour qu'il accède à son portail en ligne.
                </div>""", unsafe_allow_html=True)

                tab1, tab2, tab3, tab4 = st.tabs(["🚨 Plan d'Action","🥗 Nutrition & Probiotiques","🪥 Hygiène","📂 Historique & PDF"])

                with tab1:
                    st.markdown('<div class="section-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">🎯 Priorités cliniques</div>', unsafe_allow_html=True)
                    for i, p in enumerate(plan["priorites"]):
                        urg  = p["urgence"]
                        cls  = "priority-high" if urg=="Elevee" else "priority-medium" if urg=="Moderee" else "priority-low"
                        bcls = "badge-high"    if urg=="Elevee" else "badge-medium"    if urg=="Moderee" else "badge-low"
                        btxt = "URGENT"        if urg=="Elevee" else "MODÉRÉ"          if urg=="Moderee" else "ROUTINE"
                        li_items = "".join(f"<li>{a}</li>" for a in p["actions"])
                        st.markdown(f"""
                        <div class="priority-card {cls}">
                          <h4>{p['icone']} Priorité {i+1} — {p['titre']}
                            <span class="badge-urgence {bcls}">{btxt}</span>
                          </h4>
                          <p>{p['explication']}</p>
                          <ul>{li_items}</ul>
                        </div>""", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with tab2:
                    col_f, col_e = st.columns(2)
                    with col_f:
                        st.markdown('<div class="section-card">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">✅ À favoriser</div>', unsafe_allow_html=True)
                        pills = "".join(f'<span class="pill pill-green">{a}</span>' for a in plan["aliments_favoriser"])
                        st.markdown(f'<div class="pill-wrap">{pills}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col_e:
                        st.markdown('<div class="section-card">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">❌ À limiter</div>', unsafe_allow_html=True)
                        pills = "".join(f'<span class="pill pill-red">{a}</span>' for a in plan["aliments_eviter"])
                        st.markdown(f'<div class="pill-wrap">{pills}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    if plan["probiotiques"]:
                        st.markdown('<div class="section-card">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">💊 Probiotiques</div>', unsafe_allow_html=True)
                        for prob in plan["probiotiques"]:
                            st.markdown(f"""
                            <div class="probiotic-card">
                              <h4>🧫 {prob['nom']}</h4>
                              <div class="probiotic-grid">
                                <div class="probiotic-item"><span>Forme :</span> {prob['forme']}</div>
                                <div class="probiotic-item"><span>Durée :</span> {prob['duree']}</div>
                                <div class="probiotic-item"><span>Bénéfice :</span> {prob['benefice']}</div>
                                <div class="probiotic-item"><span>Produits :</span> {prob['marques']}</div>
                              </div>
                            </div>""", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                with tab3:
                    st.markdown('<div class="section-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">🪥 Protocole personnalisé</div>', unsafe_allow_html=True)
                    for m in plan["hygiene"]:
                        li_items = "".join(f"<li>{a}</li>" for a in m["actions"])
                        st.markdown(f"""
                        <div class="hygiene-step">
                          <div class="hygiene-content">
                            <h4>{m['moment']}</h4>
                            <ul>{li_items}</ul>
                          </div>
                        </div>""", unsafe_allow_html=True)
                        st.markdown('<div class="ob-divider"></div>', unsafe_allow_html=True)

                    if   r_paro    == "Élevé": st.info("💡 Le nettoyage interdentaire est la priorité absolue pour ce patient.")
                    elif r_carieux == "Élevé": st.warning("⏱ Le timing des repas est aussi important que l'hygiène pour ce profil carieux.")
                    else:                       st.success("✅ Routine efficace. Contrôle dans 6 mois.")
                    st.markdown('</div>', unsafe_allow_html=True)

                with tab4:
                    st.markdown('<div class="section-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">📅 Historique</div>', unsafe_allow_html=True)
                    if not patient["historique"].empty:
                        st.dataframe(patient["historique"], use_container_width=True, hide_index=True)
                        if len(patient["historique"]) > 1:
                            df_g = patient["historique"].copy().reset_index(drop=True)
                            gc1, gc2 = st.columns(2)
                            with gc1:
                                st.caption("Évolution bactérienne")
                                st.line_chart(df_g[["S. mutans (%)", "P. gingiv. (%)"]].astype(float))
                            with gc2:
                                d_col = [c for c in df_g.columns if "iversit" in c]
                                if d_col:
                                    st.caption("Diversité microbienne")
                                    st.line_chart(df_g[d_col].astype(float))
                    else:
                        st.info("Aucune analyse enregistrée.")
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="section-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">➕ Ajouter une intervention</div>', unsafe_allow_html=True)
                    with st.form("form_ajout"):
                        fa1, fa2, fa3 = st.columns(3)
                        with fa1:
                            nd   = st.date_input("Date", date.today())
                            nact = st.selectbox("Intervention", ["Examen Initial","Contrôle Microbiome","Détartrage","Soin Carie","Surfaçage","Probiotiques Prescrits","Autre"])
                        with fa2:
                            ns  = st.number_input("S. mutans (%)",    0.0, 10.0, float(s_mutans),    step=0.1)
                            np_ = st.number_input("P. gingivalis (%)",0.0,  5.0, float(p_gingivalis), step=0.1)
                        with fa3:
                            nd2   = st.number_input("Diversité (%)", 0, 100, int(diversite))
                            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                            sauver = st.form_submit_button("Sauvegarder", use_container_width=True, type="primary")
                        if sauver:
                            st_val = "Alerte" if ns > 3.0 or np_ > 0.5 or nd2 < 50 else "Stable"
                            nl = pd.DataFrame({
                                "Date":[nd.strftime("%d/%m/%Y")],"Acte / Test":[nact],
                                "S. mutans (%)":[ns],"P. gingiv. (%)":[np_],
                                "Diversite (%)":[nd2],"Status":[st_val]
                            })
                            st.session_state.patients[st.session_state.patient_sel]["historique"] = pd.concat(
                                [patient["historique"], nl], ignore_index=True)
                            st.session_state.patients[st.session_state.patient_sel]["s_mutans"]    = ns
                            st.session_state.patients[st.session_state.patient_sel]["p_gingivalis"] = np_
                            st.session_state.patients[st.session_state.patient_sel]["diversite"]   = nd2
                            st.success("Sauvegardé avec succès.")
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="section-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">📄 Rapport PDF</div>', unsafe_allow_html=True)
                    try:
                        pdf_bytes = generer_pdf(patient["nom"], r_carieux, r_paro, diversite, patient["historique"], plan)
                        st.download_button(
                            label="📥 Télécharger le rapport complet (PDF)",
                            data=pdf_bytes,
                            file_name=f"OralBiome_{patient['id']}_{patient['nom'].replace(' ','_')}.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur PDF : {e}")
                        st.info("Ajoutez 'reportlab' dans requirements.txt")
                    st.markdown('</div>', unsafe_allow_html=True)