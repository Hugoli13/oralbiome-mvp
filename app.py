import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
import io

# ============================================================
# PDF — utilise reportlab (disponible sur Streamlit Cloud)
# Si reportlab absent, fallback vers fpdf avec ASCII strict
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
        BLUE = colors.HexColor('#1B4F8A')
        LIGHT_BLUE = colors.HexColor('#D6E4F7')
        GREEN = colors.HexColor('#28a745')
        RED = colors.HexColor('#dc3545')
        ORANGE = colors.HexColor('#fd7e14')
        YELLOW_BG = colors.HexColor('#fff3cd')
        GREEN_BG = colors.HexColor('#d4edda')
        RED_BG = colors.HexColor('#f8d7da')
        GRAY_BG = colors.HexColor('#f5f5f5')

        title_style = ParagraphStyle('Title', fontSize=18, textColor=colors.white,
                                     alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=4)
        sub_style = ParagraphStyle('Sub', fontSize=10, textColor=colors.white,
                                   alignment=TA_CENTER, fontName='Helvetica', spaceAfter=6)
        h1_style = ParagraphStyle('H1', fontSize=13, textColor=BLUE,
                                  fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=4)
        h2_style = ParagraphStyle('H2', fontSize=11, textColor=BLUE,
                                  fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=3)
        body_style = ParagraphStyle('Body', fontSize=10, fontName='Helvetica',
                                    spaceAfter=3, leading=14)
        italic_style = ParagraphStyle('Italic', fontSize=9, fontName='Helvetica-Oblique',
                                      textColor=colors.HexColor('#555555'), spaceAfter=4)
        small_style = ParagraphStyle('Small', fontSize=8, fontName='Helvetica',
                                     textColor=colors.grey, alignment=TA_CENTER)

        elems = []

        # EN-TETE
        header_data = [[Paragraph("OralBiome - Rapport Patient", title_style)],
                       [Paragraph("Microbiome Oral Predictif | Rapport Personnalise", sub_style)]]
        header_table = Table(header_data, colWidths=[180*mm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BLUE),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        elems.append(header_table)
        elems.append(Spacer(1, 5*mm))

        # INFOS PATIENT
        info_data = [[
            Paragraph(f"<b>Patient :</b> {patient_nom}", body_style),
            Paragraph(f"<b>Date :</b> {date.today().strftime('%d/%m/%Y')}", body_style)
        ]]
        info_table = Table(info_data, colWidths=[90*mm, 90*mm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BLUE),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elems.append(info_table)
        elems.append(Spacer(1, 4*mm))

        # PROFIL
        profil = plan["profil_label"].replace("🟢","").replace("🟡","").replace("🔴","").strip()
        nb_al = sum([r_carieux=="Eleve", r_paro=="Eleve", diversite<50])
        profil_color = GREEN if nb_al==0 else ORANGE if nb_al==1 else RED
        profil_data = [[Paragraph(f"<b>Profil : {profil}</b>", ParagraphStyle('PF', fontSize=12,
                        textColor=colors.white, fontName='Helvetica-Bold'))]]
        profil_table = Table(profil_data, colWidths=[180*mm])
        profil_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), profil_color),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elems.append(profil_table)
        elems.append(Paragraph(plan["profil_description"], italic_style))
        elems.append(Spacer(1, 3*mm))

        # RESULTATS
        elems.append(Paragraph("Resultats de l'Analyse", h1_style))
        elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE))
        
        rc_color = RED if r_carieux=="Eleve" else GREEN
        rp_color = RED if r_paro=="Eleve" else GREEN
        res_data = [
            [Paragraph("<b>Risque Carieux</b>", body_style),
             Paragraph(f"<font color='{'#dc3545' if r_carieux=='Eleve' else '#28a745'}'><b>{r_carieux}</b></font>", body_style)],
            [Paragraph("<b>Risque Parodontal</b>", body_style),
             Paragraph(f"<font color='{'#dc3545' if r_paro=='Eleve' else '#28a745'}'><b>{r_paro}</b></font>", body_style)],
            [Paragraph("<b>Score de Diversite</b>", body_style),
             Paragraph(f"<b>{diversite}/100</b> (optimal > 65)", body_style)],
            [Paragraph("<b>Prochain controle</b>", body_style),
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

        # PLAN D'ACTION
        if plan["priorites"]:
            elems.append(Paragraph("Plan d'Action - Priorites", h1_style))
            elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE))
            for i, p in enumerate(plan["priorites"]):
                urgence = p["urgence"]
                bg = colors.HexColor('#fff5f5') if urgence=="Elevee" else colors.HexColor('#fff8f0') if urgence=="Moderee" else colors.HexColor('#f0fff4')
                badge = "URGENCE ELEVEE" if urgence=="Elevee" else "MODEREE" if urgence=="Moderee" else "ROUTINE"
                elems.append(Paragraph(f"Priorite {i+1} — {p['titre']} [{badge}]", h2_style))
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

        # NUTRITION
        elems.append(Paragraph("Plan Nutritionnel Personnalise", h1_style))
        elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE))

        if plan["aliments_favoriser"] or plan["aliments_eviter"]:
            header_nutr = [[
                Paragraph("<b>Aliments a Favoriser</b>", ParagraphStyle('NH', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white)),
                Paragraph("<b>Aliments a Limiter / Eviter</b>", ParagraphStyle('NH2', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white))
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
                evi = plan["aliments_eviter"][i] if i < len(plan["aliments_eviter"]) else ""
                nutr_rows.append([
                    Paragraph(fav, body_style),
                    Paragraph(evi, body_style)
                ])
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

        # PROBIOTIQUES
        if plan["probiotiques"]:
            elems.append(Paragraph("Probiotiques Oraux Recommandes", h1_style))
            elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE))
            for prob in plan["probiotiques"]:
                elems.append(Paragraph(f"<b>{prob['nom']}</b>", h2_style))
                prob_data = [
                    [Paragraph("<b>Forme :</b>", body_style), Paragraph(prob['forme'], body_style)],
                    [Paragraph("<b>Duree :</b>", body_style), Paragraph(prob['duree'], body_style)],
                    [Paragraph("<b>Benefice :</b>", body_style), Paragraph(prob['benefice'], body_style)],
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

        # HYGIENE
        elems.append(Paragraph("Protocole d'Hygiene Personnalise", h1_style))
        elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE))
        for moment_data in plan["hygiene"]:
            elems.append(Paragraph(f"<b>{moment_data['moment']}</b>", h2_style))
            for action in moment_data["actions"]:
                elems.append(Paragraph(f"• {action}", body_style))
            elems.append(Spacer(1, 2*mm))

        # HISTORIQUE
        if not historique_df.empty:
            elems.append(Spacer(1, 5*mm))
            elems.append(Paragraph("Historique des Analyses", h1_style))
            elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE))
            hist_header = [["Date", "Acte / Test", "S. mutans", "P. gingiv.", "Diversite", "Statut"]]
            hist_rows = []
            for _, row in historique_df.iterrows():
                statut = str(row.get("Status","")).replace("🔴 ","").replace("🟢 ","")
                hist_rows.append([
                    str(row.get("Date","")),
                    str(row.get("Acte / Test","")),
                    str(row.get("S. mutans (%)","")) + "%",
                    str(row.get("P. gingiv. (%)","")) + "%",
                    str(row.get("Diversité (%)","")) + "%",
                    statut
                ])
            hist_data = hist_header + hist_rows
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

        # SUIVI
        elems.append(Spacer(1, 5*mm))
        suivi_data = [[Paragraph(f"Prochain controle recommande : dans {plan['suivi_semaines']} semaines", 
                                  ParagraphStyle('SV', fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#856404')))]]
        suivi_table = Table(suivi_data, colWidths=[180*mm])
        suivi_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fff3cd')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        elems.append(suivi_table)
        elems.append(Spacer(1, 5*mm))

        # PIED DE PAGE
        footer_data = [[Paragraph("Ce rapport est fourni a titre preventif et informatif. Il ne constitue pas un diagnostic medical.", small_style)],
                       [Paragraph("OralBiome - Microbiome Oral Predictif | contact@oralbiome.com", small_style)]]
        footer_table = Table(footer_data, colWidths=[180*mm])
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BLUE),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elems.append(footer_table)

        doc.build(elems)
        return buffer.getvalue()

    except ImportError:
        # Fallback: PDF minimaliste ASCII pur si reportlab absent
        lines = [
            b"%PDF-1.4",
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj",
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj",
        ]
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
            f"pip install reportlab",
        ]
        stream = "\n".join(content_lines).encode('ascii', errors='replace')
        return stream


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
        plan["profil_label"] = "Microbiome Equilibre"
        plan["profil_description"] = "Votre flore buccale est protectrice. Continuez vos bonnes habitudes et revenez dans 6 mois."
        plan["suivi_semaines"] = 24
    elif nb == 1:
        plan["profil_label"] = "Desequilibre Modere"
        plan["profil_description"] = "Un desequilibre est detecte. Des ajustements alimentaires et d'hygiene cibles peuvent corriger la situation en 2 a 3 mois."
        plan["suivi_semaines"] = 12
    else:
        plan["profil_label"] = "Dysbiose Active"
        plan["profil_description"] = "Plusieurs marqueurs sont en alerte. Un plan d'action renforce est necessaire. Suivi dans 6 a 8 semaines recommande."
        plan["suivi_semaines"] = 8

    if s_mutans > 3.0:
        plan["priorites"].append({
            "icone": "🦠", "titre": "Reduire les bacteries acidogenes (S. mutans)",
            "urgence": "Elevee" if s_mutans > 6.0 else "Moderee",
            "explication": f"Taux de S. mutans : {s_mutans}% (normal < 3%). Ces bacteries produisent des acides qui dissolvent l'email.",
            "actions": [
                "Brossage 2 min minimum apres chaque repas sucre",
                "Fil dentaire quotidien le soir avant le coucher",
                "Bain de bouche fluore 1x/jour sans alcool",
                "Eviter de grignoter entre les repas"
            ]
        })
        plan["aliments_eviter"] += ["Bonbons et sucreries", "Sodas et boissons sucrees", "Pain blanc et viennoiseries", "Chocolat au lait entre les repas", "Jus de fruits (fructose eleve)"]
        plan["aliments_favoriser"] += ["Fromage a pate dure (Gruyere, Comte)", "Yaourt nature sans sucre", "Legumes crus et croquants", "The vert sans sucre", "Eau plate entre les repas", "Noix et amandes"]
        plan["probiotiques"].append({"nom": "Lactobacillus reuteri (souche DSM 17938)", "forme": "Comprimes a sucer 1x/jour apres brossage du soir", "duree": "3 mois minimum", "benefice": "Inhibe S. mutans et reduit la plaque acide", "marques": "BioGaia Prodentis, Sunstar GUM PerioBalance"})

    if p_gingivalis > 0.5:
        plan["priorites"].append({
            "icone": "🩸", "titre": "Eliminer les pathogenes parodontaux (complexe rouge)",
            "urgence": "Elevee" if p_gingivalis > 1.5 else "Moderee",
            "explication": f"Taux de P. gingivalis : {p_gingivalis}% (normal < 0.5%). Ces bacteries attaquent l'os qui maintient vos dents.",
            "actions": [
                "Nettoyage interdentaire quotidien PRIORITE N1",
                "Brossage de la langue matin et soir",
                "Consultation parodontale si gencives qui saignent",
                "Arret du tabac si applicable (multiplie x3 le risque)"
            ]
        })
        plan["aliments_eviter"] += ["Tabac sous toutes formes", "Alcool en exces", "Viandes rouges en exces", "Sucres raffines", "Aliments ultra-transformes"]
        plan["aliments_favoriser"] += ["Poissons gras 2-3x/semaine (omega-3)", "Myrtilles et framboises (polyphenols)", "Legumes verts feuillus (nitrates)", "Huile d'olive extra vierge", "Ail et oignon crus (allicine)", "Agrumes moderes (vitamine C)"]
        plan["probiotiques"].append({"nom": "Lactobacillus reuteri + Lactobacillus salivarius", "forme": "Pastilles a dissoudre en bouche 2x/jour", "duree": "3 a 6 mois", "benefice": "Reduit P. gingivalis et le saignement gingival", "marques": "Sunstar GUM PerioBalance, Blis K12"})

    if diversite < 50:
        plan["priorites"].append({
            "icone": "🌱", "titre": "Restaurer la diversite microbienne orale",
            "urgence": "Moderee" if diversite > 30 else "Elevee",
            "explication": f"Score de diversite : {diversite}/100 (optimal > 65). Une flore appauvrie ne se defend pas contre les pathogenes.",
            "actions": [
                "Diversifier : objectif 30 plantes differentes par semaine",
                "Reduire les bains de bouche antiseptiques quotidiens",
                "Augmenter les fibres prebiotiques (poireau, ail, oignon)",
                "Boire 1.5L d'eau par jour minimum"
            ]
        })
        plan["aliments_favoriser"] += ["Legumes racines varies (fibres prebiotiques)", "Pomme avec la peau (pectine)", "Legumineuses (lentilles, pois chiches)", "Cereales completes", "Legumes fermentes (choucroute, kimchi)", "Kombucha sans sucre ajoute"]
        plan["aliments_eviter"] += ["Bains de bouche antiseptiques quotidiens", "Antibiotiques inutiles", "Fast-food regulier"]
        plan["probiotiques"].append({"nom": "Streptococcus salivarius K12 + M18", "forme": "Pastilles a sucer le soir apres brossage", "duree": "2 a 3 mois puis entretien trimestriel", "benefice": "Recolonise la flore avec des especes protectrices", "marques": "BLIS K12, Nasal Guard Throat Guard"})

    if nb == 0:
        plan["priorites"].append({
            "icone": "✅", "titre": "Maintenir l'equilibre de votre microbiome",
            "urgence": "Routine",
            "explication": "Votre microbiome oral est en bonne sante. Preservez cet equilibre sur le long terme.",
            "actions": ["Brossage 2x/jour avec brosse souple", "Fil dentaire 1x/jour", "Alimentation variee riche en fibres", "Controle dans 6 mois"]
        })
        plan["aliments_favoriser"] += ["Alimentation mediterraneenne variee", "Eau comme boisson principale", "Produits laitiers fermentes (yaourt, kefir)", "Legumes cruciferes (brocoli, chou)"]

    plan["hygiene"] = [
        {"moment": "Matin", "actions": ["Brossage 2 min brosse souple (electrique recommandee)", "Brossage de la langue arriere vers avant", "Bain de bouche non-alcoolise si recommande"]},
        {"moment": "Soir (le plus important)", "actions": ["Fil dentaire ou brossettes AVANT le brossage", "Brossage 2 min minimum", "Probiotique oral a dissoudre si prescrit", "Ne plus rien manger ni boire apres (sauf eau)"]},
        {"moment": "Apres les repas", "actions": ["Attendre 30 min avant de brosser (email fragilise)", "Boire un verre d'eau pour rincer", "Chewing-gum xylitol 5 min si pas de brossage possible"]}
    ]

    plan["aliments_favoriser"] = list(dict.fromkeys(plan["aliments_favoriser"]))
    plan["aliments_eviter"] = list(dict.fromkeys(plan["aliments_eviter"]))
    return plan


# ============================================================
# CONFIGURATION
# ============================================================
st.set_page_config(page_title="OralBiome", page_icon="🦷", layout="wide")

st.markdown("""
<style>
    .pill-green { display:inline-block; background:#d4edda; border-radius:20px; padding:4px 12px; margin:3px; font-size:13px; }
    .pill-red { display:inline-block; background:#f8d7da; border-radius:20px; padding:4px 12px; margin:3px; font-size:13px; }
    .reco-card { padding:12px 16px; border-radius:6px; margin:6px 0; }
    .reco-red { background:#fff5f5; border-left:4px solid #dc3545; }
    .reco-orange { background:#fff8f0; border-left:4px solid #fd7e14; }
    .reco-green { background:#f0fff4; border-left:4px solid #28a745; }
    .patient-header { background:linear-gradient(135deg, #1B4F8A 0%, #2E86C1 100%); color:white; padding:20px; border-radius:10px; margin-bottom:20px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# DONNÉES INITIALES
# ============================================================
def donnees_initiales():
    patients = {}
    df1 = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversite (%)", "Status"])
    df1.loc[0] = ["12/10/2023", "Examen Initial", 4.2, 0.8, 45, "Alerte"]
    df1.loc[1] = ["08/04/2026", "Controle", 4.2, 0.3, 75, "Alerte"]
    patients["Jean Dupont"] = {
        "id": "P001", "nom": "Jean Dupont", "age": 42, "email": "jean.dupont@email.com",
        "telephone": "+32 472 123 456", "date_naissance": "15/03/1982",
        "historique": df1, "s_mutans": 4.2, "p_gingivalis": 0.3, "diversite": 75,
        "code_patient": "OB-P001"
    }
    df2 = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversite (%)", "Status"])
    df2.loc[0] = ["05/01/2024", "Examen Initial", 1.2, 0.1, 82, "Stable"]
    patients["Marie Martin"] = {
        "id": "P002", "nom": "Marie Martin", "age": 35, "email": "marie.martin@email.com",
        "telephone": "+32 478 654 321", "date_naissance": "22/07/1989",
        "historique": df2, "s_mutans": 1.2, "p_gingivalis": 0.1, "diversite": 82,
        "code_patient": "OB-P002"
    }
    df3 = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversite (%)", "Status"])
    df3.loc[0] = ["18/02/2025", "Examen Initial", 6.5, 1.8, 38, "Alerte"]
    patients["Pierre Bernard"] = {
        "id": "P003", "nom": "Pierre Bernard", "age": 58, "email": "pierre.bernard@email.com",
        "telephone": "+32 495 789 012", "date_naissance": "03/11/1966",
        "historique": df3, "s_mutans": 6.5, "p_gingivalis": 1.8, "diversite": 38,
        "code_patient": "OB-P003"
    }
    return patients


# ============================================================
# INIT SESSION
# ============================================================
if 'mode' not in st.session_state:
    st.session_state.mode = "choix"  # choix | praticien | patient
if 'connecte' not in st.session_state:
    st.session_state.connecte = False
if 'patients' not in st.session_state:
    st.session_state.patients = donnees_initiales()
if 'patient_sel' not in st.session_state:
    st.session_state.patient_sel = "Jean Dupont"
if 'vue' not in st.session_state:
    st.session_state.vue = "dossier"
if 'patient_connecte' not in st.session_state:
    st.session_state.patient_connecte = None


# ============================================================
# ECRAN DE CHOIX
# ============================================================
if st.session_state.mode == "choix":
    st.markdown("<br>", unsafe_allow_html=True)
    try:
        st.image(Image.open("image_19.png"), width=250)
    except:
        st.markdown("## 🦷 OralBiome")
    st.markdown("## Bienvenue sur OralBiome")
    st.markdown("*Microbiome Oral Predictif*")
    st.markdown("---")
    st.markdown("### Qui etes-vous ?")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown("#### 🩺 Praticien")
        st.markdown("Acces au tableau de bord complet, gestion des dossiers patients, analyses et rapports.")
        if st.button("Connexion Praticien", use_container_width=True, type="primary"):
            st.session_state.mode = "praticien"
            st.rerun()
    with col2:
        st.markdown("#### 🧑 Patient")
        st.markdown("Consultez votre rapport personnalise, votre plan nutritionnel et votre historique.")
        if st.button("Acces Patient", use_container_width=True):
            st.session_state.mode = "patient"
            st.rerun()
    with col3:
        st.markdown("#### ℹ️ A propos")
        st.markdown("OralBiome analyse votre microbiome oral pour une prevention dentaire et systemique personnalisee.")
        st.markdown("**contact@oralbiome.com**")


# ============================================================
# PORTAIL PATIENT
# ============================================================
elif st.session_state.mode == "patient":

    if st.session_state.patient_connecte is None:
        # Connexion patient
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            try:
                st.image(Image.open("image_19.png"), use_container_width=True)
            except:
                st.markdown("## 🦷 OralBiome")
            st.markdown("<h3 style='text-align:center; color:#1B4F8A;'>Espace Patient</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#888;'>Consultez votre rapport personnalise</p>", unsafe_allow_html=True)
            st.markdown("---")
            code = st.text_input("Votre code patient", placeholder="Ex: OB-P001")
            st.caption("Votre code patient vous a ete communique par votre praticien.")
            if st.button("Acceder a mon dossier", use_container_width=True, type="primary"):
                found = None
                for nom, data in st.session_state.patients.items():
                    if data.get("code_patient") == code.strip():
                        found = nom
                        break
                if found:
                    st.session_state.patient_connecte = found
                    st.rerun()
                else:
                    st.error("Code patient invalide. Verifiez avec votre praticien.")
            st.markdown("---")
            if st.button("Retour a l'accueil", use_container_width=True):
                st.session_state.mode = "choix"; st.rerun()
            st.caption("Codes de demo : OB-P001 (Jean Dupont) · OB-P002 (Marie Martin) · OB-P003 (Pierre Bernard)")

    else:
        # Dossier patient connecte
        patient = st.session_state.patients[st.session_state.patient_connecte]
        s_mutans = patient["s_mutans"]
        p_gingivalis = patient["p_gingivalis"]
        diversite = patient["diversite"]
        r_carieux = "Eleve" if s_mutans > 3.0 else "Faible"
        r_paro = "Eleve" if p_gingivalis > 0.5 else "Faible"
        en_alerte = r_carieux == "Eleve" or r_paro == "Eleve" or diversite < 50
        plan = generer_recommandations(s_mutans, p_gingivalis, diversite)

        # Sidebar patient
        try:
            st.sidebar.image(Image.open("image_19.png"), use_container_width=True)
        except:
            st.sidebar.markdown("## 🦷 OralBiome")
        st.sidebar.markdown(f"### Bonjour, {patient['nom'].split()[0]} !")
        st.sidebar.markdown(f"Code : `{patient['code_patient']}`")
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**Statut :** {'🔴 En alerte' if en_alerte else '🟢 Equilibre'}")
        st.sidebar.markdown(f"**Prochain controle :** dans {plan['suivi_semaines']} semaines")
        st.sidebar.markdown("---")
        if st.sidebar.button("Se deconnecter", use_container_width=True):
            st.session_state.patient_connecte = None; st.rerun()
        if st.sidebar.button("Retour accueil", use_container_width=True):
            st.session_state.patient_connecte = None
            st.session_state.mode = "choix"; st.rerun()

        # Contenu principal patient
        st.markdown(f"""
        <div class='patient-header'>
            <h2>🦷 Bonjour {patient['nom']} !</h2>
            <p>Votre rapport de microbiome oral personnalise | {date.today().strftime('%d/%m/%Y')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Metriques
        c1, c2, c3 = st.columns(3)
        c1.metric("Risque Carieux", r_carieux, "Attention" if r_carieux=="Eleve" else "Bon", delta_color="inverse")
        c2.metric("Risque Parodontal", r_paro, "Attention" if r_paro=="Eleve" else "Bon", delta_color="inverse")
        c3.metric("Diversite Microbienne", f"{diversite}/100")
        st.markdown("---")

        # Profil
        if en_alerte:
            st.warning(f"**{plan['profil_label']}** — {plan['profil_description']}")
        else:
            st.success(f"**{plan['profil_label']}** — {plan['profil_description']}")

        st.markdown("---")

        # Onglets patient
        tp1, tp2, tp3, tp4, tp5 = st.tabs([
            "📊 Mon Profil", "🚨 Mes Actions", "🥗 Ma Nutrition", "🪥 Mon Hygiene", "📥 Mon Rapport PDF"
        ])

        with tp1:
            st.header("📊 Mon Profil Bacterien")
            st.markdown(f"Voici l'etat de votre microbiome oral au {date.today().strftime('%d/%m/%Y')}.")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown("#### S. mutans")
                color_sm = "🔴" if s_mutans > 3.0 else "🟢"
                st.markdown(f"## {color_sm} {s_mutans}%")
                st.caption("Normal : < 3% | Cause principale des caries")
                if s_mutans > 3.0:
                    st.error("Taux trop eleve — des caries peuvent se former")
                else:
                    st.success("Taux normal — votre email est bien protege")

            with col_b:
                st.markdown("#### P. gingivalis")
                color_pg = "🔴" if p_gingivalis > 0.5 else "🟢"
                st.markdown(f"## {color_pg} {p_gingivalis}%")
                st.caption("Normal : < 0.5% | Bacterie du complexe rouge")
                if p_gingivalis > 0.5:
                    st.error("Taux trop eleve — risque pour vos gencives")
                else:
                    st.success("Taux normal — vos gencives sont protegees")

            with col_c:
                st.markdown("#### Diversite Microbienne")
                color_div = "🔴" if diversite < 50 else "🟡" if diversite < 65 else "🟢"
                st.markdown(f"## {color_div} {diversite}/100")
                st.caption("Optimal : > 65 | Richesse de votre flore")
                if diversite < 50:
                    st.error("Flore appauvrie — vulnerabilite accrue")
                elif diversite < 65:
                    st.warning("Flore moderee — peut etre amelioree")
                else:
                    st.success("Flore riche et protective")

            st.markdown("---")
            st.markdown("#### Historique de vos analyses")
            if not patient["historique"].empty:
                st.dataframe(patient["historique"], use_container_width=True, hide_index=True)
                if len(patient["historique"]) > 1:
                    st.markdown("#### Evolution dans le temps")
                    df_g = patient["historique"].copy()
                    df_g.index = range(len(df_g))
                    gc1, gc2 = st.columns(2)
                    with gc1:
                        st.caption("Bacteries (S. mutans et P. gingivalis)")
                        st.line_chart(df_g[["S. mutans (%)", "P. gingiv. (%)"]].astype(float))
                    with gc2:
                        st.caption("Diversite microbienne")
                        st.line_chart(df_g[["Diversite (%)"]].astype(float))
            else:
                st.info("Aucune analyse enregistree pour le moment.")

        with tp2:
            st.header("🚨 Mes Actions Prioritaires")
            st.caption("Actions classees par ordre d'importance pour votre profil.")
            st.markdown("---")
            for i, p in enumerate(plan["priorites"]):
                urg = p["urgence"]
                badge = "URGENT" if urg=="Elevee" else "MODERE" if urg=="Moderee" else "ROUTINE"
                css = "reco-red" if urg=="Elevee" else "reco-orange" if urg=="Moderee" else "reco-green"
                st.markdown(f"### {p['icone']} Action {i+1} — {p['titre']} `{badge}`")
                st.markdown(f"<div class='reco-card {css}'><em>{p['explication']}</em></div>", unsafe_allow_html=True)
                for action in p["actions"]:
                    st.markdown(f"- {action}")
                st.markdown("---")

        with tp3:
            st.header("🥗 Mon Plan Nutritionnel")
            st.caption("Ce plan est personnalise pour votre profil bacterien specifique.")
            st.markdown("---")
            col_fav, col_evi = st.columns(2)
            with col_fav:
                st.markdown("### ✅ Favoriser")
                for a in plan["aliments_favoriser"]:
                    st.markdown(f"<span class='pill-green'>{a}</span>", unsafe_allow_html=True)
            with col_evi:
                st.markdown("### ❌ Limiter")
                for a in plan["aliments_eviter"]:
                    st.markdown(f"<span class='pill-red'>{a}</span>", unsafe_allow_html=True)

            st.markdown("---")
            st.header("💊 Mes Probiotiques")
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
                st.success("Pas de probiotiques specifiques necessaires. Maintenez une alimentation variee.")

        with tp4:
            st.header("🪥 Mon Protocole d'Hygiene")
            st.caption("Routine adaptee a votre profil bacterien.")
            st.markdown("---")
            for m in plan["hygiene"]:
                st.markdown(f"### {m['moment']}")
                for action in m["actions"]:
                    st.markdown(f"- {action}")
                st.markdown("")
            st.markdown("---")
            if r_paro == "Eleve":
                st.info("Le nettoyage interdentaire est PLUS important que le brossage. 5 minutes de fil dentaire le soir valent mieux que 10 minutes de brossage.")
            elif r_carieux == "Eleve":
                st.warning("Le timing des repas est aussi important que l'hygiene. Chaque prise alimentaire relance la production d'acides pendant 20 minutes.")
            else:
                st.success("Votre routine est efficace. Continuez et revenez dans 6 mois.")

        with tp5:
            st.header("📥 Mon Rapport PDF Complet")
            st.markdown("Votre rapport personalise inclut votre profil bacterien, votre plan d'action, votre nutrition, vos probiotiques et votre protocole d'hygiene.")
            st.markdown("---")
            try:
                pdf_bytes = generer_pdf(patient["nom"], r_carieux, r_paro, diversite, patient["historique"], plan)
                st.download_button(
                    label="📥 Telecharger mon Rapport OralBiome (PDF)",
                    data=pdf_bytes,
                    file_name=f"OralBiome_MonRapport_{patient['id']}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
                st.success("Votre rapport est pret ! Cliquez pour le telecharger et le partager avec votre medecin.")
            except Exception as e:
                st.error(f"Erreur generation PDF : {e}")
                st.info("Conseil : ajoutez 'reportlab' dans votre fichier requirements.txt")


# ============================================================
# PORTAIL PRATICIEN
# ============================================================
elif st.session_state.mode == "praticien":

    if not st.session_state.connecte:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.write(""); st.write("")
            try:
                st.image(Image.open("image_19.png"), use_container_width=True)
            except:
                st.markdown("<h1 style='text-align:center;'>🦷 OralBiome</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center; color:#1B4F8A;'>Portail Praticien</h3>", unsafe_allow_html=True)
            st.markdown("---")
            email = st.text_input("Email Professionnel")
            mdp = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter", use_container_width=True, type="primary"):
                if email == "contact@oralbiome.com" and mdp == "mvp2024":
                    st.session_state.connecte = True; st.rerun()
                else:
                    st.error("Identifiants incorrects. Utilisez contact@oralbiome.com / mvp2024")
            st.markdown("---")
            if st.button("Retour a l'accueil", use_container_width=True):
                st.session_state.mode = "choix"; st.rerun()

    else:
        # SIDEBAR PRATICIEN
        try:
            st.sidebar.image(Image.open("image_19.png"), use_container_width=True)
        except:
            st.sidebar.markdown("## 🦷 OralBiome")

        st.sidebar.markdown("---")
        sc1, sc2 = st.sidebar.columns(2)
        with sc1:
            if st.button("👥 Patients", use_container_width=True):
                st.session_state.vue = "liste"; st.rerun()
        with sc2:
            if st.button("➕ Nouveau", use_container_width=True):
                st.session_state.vue = "nouveau"; st.rerun()

        st.sidebar.markdown("---")
        nb_patients = len(st.session_state.patients)
        nb_alertes = sum(1 for p in st.session_state.patients.values()
                         if p["s_mutans"] > 3.0 or p["p_gingivalis"] > 0.5 or p["diversite"] < 50)
        st.sidebar.markdown("### Mon Cabinet")
        ms1, ms2 = st.sidebar.columns(2)
        ms1.metric("Patients", nb_patients)
        ms2.metric("Alertes", nb_alertes)

        st.sidebar.markdown("---")
        st.sidebar.markdown("### Acces Rapide")
        rech = st.sidebar.text_input("Rechercher...", placeholder="Nom ou ID")
        pf = {n: d for n, d in st.session_state.patients.items()
              if rech.lower() in n.lower() or rech.lower() in d["id"].lower()} if rech else st.session_state.patients

        for nom, data in pf.items():
            icon = "🔴" if (data["s_mutans"] > 3.0 or data["p_gingivalis"] > 0.5 or data["diversite"] < 50) else "🟢"
            is_sel = nom == st.session_state.patient_sel
            if st.sidebar.button(f"{icon} {data['id']} — {nom}", use_container_width=True,
                                  type="primary" if is_sel else "secondary"):
                st.session_state.patient_sel = nom
                st.session_state.vue = "dossier"; st.rerun()

        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Deconnecter", use_container_width=True):
            st.session_state.connecte = False; st.rerun()
        if st.sidebar.button("Retour accueil", use_container_width=True):
            st.session_state.connecte = False
            st.session_state.mode = "choix"; st.rerun()

        # VUE LISTE
        if st.session_state.vue == "liste":
            st.title("👥 Gestion des Patients")
            st.markdown(f"**{nb_patients} patients** · **{nb_alertes} alertes actives**")
            st.markdown("---")
            lf1, lf2, lf3 = st.columns(3)
            with lf1:
                filtre = st.selectbox("Filtrer", ["Tous", "Alerte uniquement", "Stable uniquement"])
            with lf3:
                if st.button("➕ Nouveau Patient", type="primary"):
                    st.session_state.vue = "nouveau"; st.rerun()
            st.markdown("---")
            donnees = []
            for nom, data in st.session_state.patients.items():
                ea = data["s_mutans"] > 3.0 or data["p_gingivalis"] > 0.5 or data["diversite"] < 50
                if filtre == "Alerte uniquement" and not ea: continue
                if filtre == "Stable uniquement" and ea: continue
                donnees.append({
                    "ID": data["id"], "Nom": nom, "Age": data["age"],
                    "Code Patient": data.get("code_patient", ""),
                    "Risque Carieux": "Eleve" if data["s_mutans"] > 3.0 else "Faible",
                    "Risque Parodontal": "Eleve" if data["p_gingivalis"] > 0.5 else "Faible",
                    "Diversite": f"{data['diversite']}/100",
                    "Statut": "Alerte" if ea else "Stable",
                    "Visites": len(data["historique"])
                })
            if donnees:
                st.dataframe(pd.DataFrame(donnees), use_container_width=True, hide_index=True)
                st.markdown("---")
                st.markdown("**Ouvrir un dossier :**")
                cols = st.columns(min(len(st.session_state.patients), 4))
                for i, (nom, data) in enumerate(st.session_state.patients.items()):
                    ea = data["s_mutans"] > 3.0 or data["p_gingivalis"] > 0.5 or data["diversite"] < 50
                    with cols[i % 4]:
                        if st.button(f"{'🔴' if ea else '🟢'} {nom}", use_container_width=True):
                            st.session_state.patient_sel = nom
                            st.session_state.vue = "dossier"; st.rerun()

        # VUE NOUVEAU
        elif st.session_state.vue == "nouveau":
            st.title("➕ Nouveau Patient")
            st.markdown("---")
            with st.form("form_nouveau"):
                nc1, nc2 = st.columns(2)
                with nc1:
                    nn = st.text_input("Nom complet *")
                    ne = st.text_input("Email")
                    nd_nais = st.date_input("Date de naissance", value=date(1985, 1, 1))
                with nc2:
                    na = st.number_input("Age", 1, 120, 35)
                    nt = st.text_input("Telephone")
                st.markdown("---")
                st.markdown("### Premiere Analyse")
                nc3, nc4, nc5 = st.columns(3)
                with nc3: is_ = st.number_input("S. mutans (%)", 0.0, 10.0, 2.0, step=0.1)
                with nc4: ip_ = st.number_input("P. gingivalis (%)", 0.0, 5.0, 0.2, step=0.1)
                with nc5: id_ = st.number_input("Diversite (%)", 0, 100, 70)
                aj = st.checkbox("Enregistrer comme examen initial", value=True)
                sub = st.form_submit_button("Creer le dossier", use_container_width=True, type="primary")
                if sub:
                    if not nn.strip():
                        st.error("Le nom est obligatoire.")
                    elif nn in st.session_state.patients:
                        st.error("Ce patient existe deja.")
                    else:
                        nid = f"P{str(len(st.session_state.patients)+1).zfill(3)}"
                        code_p = f"OB-{nid}"
                        df_n = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversite (%)", "Status"])
                        if aj:
                            s = "Alerte" if is_ > 3.0 or ip_ > 0.5 or id_ < 50 else "Stable"
                            df_n.loc[0] = [date.today().strftime("%d/%m/%Y"), "Examen Initial", is_, ip_, id_, s]
                        st.session_state.patients[nn] = {
                            "id": nid, "nom": nn, "age": na, "email": ne, "telephone": nt,
                            "date_naissance": nd_nais.strftime("%d/%m/%Y"),
                            "historique": df_n,
                            "s_mutans": is_ if aj else 0.0,
                            "p_gingivalis": ip_ if aj else 0.0,
                            "diversite": id_ if aj else 70,
                            "code_patient": code_p
                        }
                        st.session_state.patient_sel = nn
                        st.session_state.vue = "dossier"
                        st.success(f"Dossier cree ! Code patient : **{code_p}** — communiquez ce code au patient.")
                        st.rerun()

        # VUE DOSSIER
        else:
            patient = st.session_state.patients.get(st.session_state.patient_sel)
            if not patient:
                st.error("Patient introuvable.")
            else:
                s_mutans = patient["s_mutans"]
                p_gingivalis = patient["p_gingivalis"]
                diversite = patient["diversite"]
                r_carieux = "Eleve" if s_mutans > 3.0 else "Faible"
                r_paro = "Eleve" if p_gingivalis > 0.5 else "Faible"
                en_alerte = r_carieux=="Eleve" or r_paro=="Eleve" or diversite<50
                plan = generer_recommandations(s_mutans, p_gingivalis, diversite)

                badge = "🔴 En Alerte" if en_alerte else "🟢 Stable"
                st.markdown(f"## 🦷 {patient['nom']}  `{patient['id']}`  —  {badge}")
                st.caption(f"Age : {patient['age']} ans  ·  {patient['email']}  ·  Code patient : **{patient.get('code_patient','')}**")
                st.markdown("---")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Risque Carieux", r_carieux, "Alerte" if r_carieux=="Eleve" else "Normal", delta_color="inverse")
                m2.metric("Risque Parodontal", r_paro, "Alerte" if r_paro=="Eleve" else "Normal", delta_color="inverse")
                m3.metric("Diversite", f"{diversite}/100")
                m4.metric("Visites", len(patient["historique"]))
                st.markdown("---")

                if en_alerte:
                    st.warning(f"**{plan['profil_label']}** — {plan['profil_description']}")
                else:
                    st.success(f"**{plan['profil_label']}** — {plan['profil_description']}")
                st.markdown(f"**Prochain controle : dans {plan['suivi_semaines']} semaines**")
                st.markdown("---")

                # Info code patient
                code_p = patient.get("code_patient", "")
                st.info(f"Code d'acces patient : **{code_p}** — Communiquez ce code au patient pour qu'il accede a son portail.")
                st.markdown("---")

                tab1, tab2, tab3, tab4 = st.tabs(["🚨 Plan d'Action", "🥗 Nutrition & Probiotiques", "🪥 Hygiene", "📂 Historique & PDF"])

                with tab1:
                    st.header("Priorites & Actions")
                    for i, p in enumerate(plan["priorites"]):
                        urg = p["urgence"]
                        badge_u = "URGENT" if urg=="Elevee" else "MODERE" if urg=="Moderee" else "ROUTINE"
                        css = "reco-red" if urg=="Elevee" else "reco-orange" if urg=="Moderee" else "reco-green"
                        st.markdown(f"#### {p['icone']} Priorite {i+1} — {p['titre']} `{badge_u}`")
                        st.markdown(f"<div class='reco-card {css}'><em>{p['explication']}</em></div>", unsafe_allow_html=True)
                        for action in p["actions"]:
                            st.markdown(f"- {action}")
                        st.markdown("---")

                with tab2:
                    st.header("Plan Nutritionnel")
                    col_fav, col_evi = st.columns(2)
                    with col_fav:
                        st.markdown("### Favoriser")
                        for a in plan["aliments_favoriser"]:
                            st.markdown(f"<span class='pill-green'>{a}</span>", unsafe_allow_html=True)
                    with col_evi:
                        st.markdown("### Limiter")
                        for a in plan["aliments_eviter"]:
                            st.markdown(f"<span class='pill-red'>{a}</span>", unsafe_allow_html=True)
                    st.markdown("---")
                    st.header("Probiotiques")
                    for prob in plan["probiotiques"]:
                        with st.expander(f"🧫 {prob['nom']}", expanded=True):
                            pp1, pp2 = st.columns(2)
                            with pp1:
                                st.markdown(f"**Forme :** {prob['forme']}")
                                st.markdown(f"**Duree :** {prob['duree']}")
                            with pp2:
                                st.markdown(f"**Benefice :** {prob['benefice']}")
                                st.markdown(f"**Produits :** `{prob['marques']}`")

                with tab3:
                    st.header("Protocole d'Hygiene")
                    for m in plan["hygiene"]:
                        st.markdown(f"### {m['moment']}")
                        for action in m["actions"]:
                            st.markdown(f"- {action}")
                    st.markdown("---")
                    if r_paro == "Eleve":
                        st.info("Le nettoyage interdentaire est PLUS important que le brossage.")
                    elif r_carieux == "Eleve":
                        st.warning("Le timing des repas est aussi important que l'hygiene. Chaque prise alimentaire = 20 min d'acides.")
                    else:
                        st.success("Routine efficace. Controle dans 6 mois.")

                with tab4:
                    st.header("Historique")
                    if not patient["historique"].empty:
                        st.dataframe(patient["historique"], use_container_width=True, hide_index=True)
                        if len(patient["historique"]) > 1:
                            df_g = patient["historique"].copy()
                            df_g.index = range(len(df_g))
                            gc1, gc2 = st.columns(2)
                            with gc1:
                                st.line_chart(df_g[["S. mutans (%)", "P. gingiv. (%)"]].astype(float))
                            with gc2:
                                hist_cols = [c for c in ["Diversite (%)", "Diversité (%)"] if c in df_g.columns]
                                if hist_cols:
                                    st.line_chart(df_g[hist_cols].astype(float))
                    else:
                        st.info("Aucune analyse enregistree.")

                    st.markdown("---")
                    st.header("Ajouter une Intervention")
                    with st.form("form_ajout"):
                        fa1, fa2, fa3 = st.columns(3)
                        with fa1:
                            nd = st.date_input("Date", date.today())
                            nact = st.selectbox("Intervention", ["Examen Initial", "Controle Microbiome", "Detartrage", "Soin Carie", "Surfacage", "Probiotiques Prescrits", "Autre"])
                        with fa2:
                            ns = st.number_input("S. mutans (%)", 0.0, 10.0, float(s_mutans), step=0.1)
                            np_ = st.number_input("P. gingivalis (%)", 0.0, 5.0, float(p_gingivalis), step=0.1)
                        with fa3:
                            nd2 = st.number_input("Diversite (%)", 0, 100, int(diversite))
                            st.markdown("<br>", unsafe_allow_html=True)
                            sauver = st.form_submit_button("Sauvegarder", use_container_width=True, type="primary")
                        if sauver:
                            st_val = "Alerte" if ns > 3.0 or np_ > 0.5 or nd2 < 50 else "Stable"
                            nl = pd.DataFrame({
                                "Date": [nd.strftime("%d/%m/%Y")], "Acte / Test": [nact],
                                "S. mutans (%)": [ns], "P. gingiv. (%)": [np_],
                                "Diversite (%)": [nd2], "Status": [st_val]
                            })
                            st.session_state.patients[st.session_state.patient_sel]["historique"] = pd.concat(
                                [patient["historique"], nl], ignore_index=True)
                            st.session_state.patients[st.session_state.patient_sel]["s_mutans"] = ns
                            st.session_state.patients[st.session_state.patient_sel]["p_gingivalis"] = np_
                            st.session_state.patients[st.session_state.patient_sel]["diversite"] = nd2
                            st.success("Sauvegarde.")
                            st.rerun()

                    st.markdown("---")
                    st.header("Rapport PDF Complet")
                    try:
                        pdf_bytes = generer_pdf(patient["nom"], r_carieux, r_paro, diversite, patient["historique"], plan)
                        st.download_button(
                            label="Telecharger le Rapport Patient Complet (PDF)",
                            data=pdf_bytes,
                            file_name=f"OralBiome_{patient['id']}_{patient['nom'].replace(' ','_')}.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur PDF : {e}")
                        st.info("Ajoutez 'reportlab' dans requirements.txt")