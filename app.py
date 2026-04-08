import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
import io
import base64
import json
import requests

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="OralBiome", page_icon="🦷", layout="wide")

ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display:ital@0;1&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

  .ob-header {
    background: linear-gradient(135deg, #0a1628 0%, #1a3a5c 60%, #0d2640 100%);
    border-radius: 16px; padding: 28px 32px; margin-bottom: 24px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  }
  .ob-header h1 { font-family: 'DM Serif Display', serif; color: #fff; margin: 0; font-size: 2rem; }
  .ob-header p { color: rgba(255,255,255,0.6); margin: 4px 0 0 0; font-size: 0.9rem; }

  .risk-card {
    border-radius: 12px; padding: 20px; margin: 8px 0;
    border: 1px solid rgba(0,0,0,0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .risk-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
  .risk-low  { background: linear-gradient(135deg, #f0fdf4, #dcfce7); border-left: 4px solid #16a34a; }
  .risk-med  { background: linear-gradient(135deg, #fffbeb, #fef3c7); border-left: 4px solid #d97706; }
  .risk-high { background: linear-gradient(135deg, #fff1f2, #ffe4e6); border-left: 4px solid #e11d48; }

  .systemic-card {
    background: #fff; border-radius: 14px; padding: 20px 24px;
    border: 1px solid #e5e7eb; margin: 10px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  }
  .systemic-title { font-family: 'DM Serif Display', serif; font-size: 1.1rem; color: #1a3a5c; margin: 0 0 8px 0; }

  .score-ring {
    display: flex; align-items: center; justify-content: center;
    width: 72px; height: 72px; border-radius: 50%;
    font-weight: 600; font-size: 1.1rem; color: #fff;
    flex-shrink: 0;
  }
  .score-low  { background: linear-gradient(135deg, #16a34a, #22c55e); }
  .score-med  { background: linear-gradient(135deg, #d97706, #f59e0b); }
  .score-high { background: linear-gradient(135deg, #e11d48, #f43f5e); }

  .photo-upload-zone {
    border: 2px dashed #cbd5e1; border-radius: 16px;
    padding: 48px; text-align: center;
    background: linear-gradient(135deg, #f8fafc, #f1f5f9);
    cursor: pointer; transition: all 0.3s ease;
  }
  .photo-upload-zone:hover { border-color: #1a3a5c; background: #f0f4ff; }

  .finding-badge {
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-size: 0.78rem; font-weight: 500; margin: 3px;
  }
  .finding-alert { background: #fee2e2; color: #991b1b; }
  .finding-warn  { background: #fef3c7; color: #92400e; }
  .finding-ok    { background: #dcfce7; color: #166534; }

  .pill-green { display:inline-block; background:#d1fae5; border-radius:20px; padding:5px 14px; margin:3px; font-size:13px; color:#065f46; font-weight:500; }
  .pill-red   { display:inline-block; background:#fee2e2; border-radius:20px; padding:5px 14px; margin:3px; font-size:13px; color:#991b1b; font-weight:500; }

  .reco-card { padding:14px 18px; border-radius:8px; margin:8px 0; }
  .reco-red    { background:#fff5f5; border-left:4px solid #dc3545; }
  .reco-orange { background:#fff8f0; border-left:4px solid #fd7e14; }
  .reco-green  { background:#f0fff4; border-left:4px solid #28a745; }

  .patient-header {
    background: linear-gradient(135deg, #1a3a5c, #2563eb);
    color: white; padding: 24px; border-radius: 12px; margin-bottom: 20px;
  }

  .metric-box {
    background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
    padding: 16px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  }
  .metric-val { font-family: 'DM Serif Display', serif; font-size: 1.8rem; color: #1a3a5c; }
  .metric-lbl { font-size: 0.8rem; color: #6b7280; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# MOTEUR SCORE SYSTÉMIQUE — basé sur la littérature scientifique
# ============================================================
SYSTEMIC_CORRELATIONS = {
    "cardiovasculaire": {
        "icon": "❤️",
        "label": "Risque Cardiovasculaire",
        "description": "P. gingivalis et T. forsythia libèrent des endotoxines qui favorisent l'athérosclérose et les plaques artérielles.",
        "references": "Herzberg & Meyer, 1996 · Mehta et al., 2013 · AHA Scientific Statement 2012",
        "weight_gingivalis": 0.45,
        "weight_mutans": 0.10,
        "weight_diversity": 0.30,
        "weight_inflammation": 0.15,
        "thresholds": {"low": 25, "high": 55},
        "actions_high": [
            "Consultation cardiologique recommandée",
            "Bilan CRP ultrasensible (marqueur inflammation systémique)",
            "Traitement parodontal en priorité — réduit le risque CV de 20%",
            "Alimentation anti-inflammatoire (omega-3, polyphénols)"
        ],
        "actions_low": [
            "Maintenir une hygiène parodontale rigoureuse",
            "Contrôle microbiome oral tous les 6 mois"
        ]
    },
    "diabete": {
        "icon": "🩸",
        "label": "Risque Diabète / Résistance Insuline",
        "description": "La dysbiose orale entretient une inflammation chronique de bas grade qui dégrade la sensibilité à l'insuline. La relation est bidirectionnelle.",
        "references": "Taylor et al., 2013 · Preshaw et al., 2012 · Systemic Reviews Lancet 2020",
        "weight_gingivalis": 0.35,
        "weight_mutans": 0.20,
        "weight_diversity": 0.35,
        "weight_inflammation": 0.10,
        "thresholds": {"low": 25, "high": 55},
        "actions_high": [
            "Bilan glycémie à jeun et HbA1c recommandé",
            "Réduction drastique des sucres rapides — impact direct sur S. mutans ET glycémie",
            "Traitement parodontal prouvé : réduit HbA1c de 0.4% en moyenne",
            "Exercice physique 150 min/semaine (améliore microbiome ET insulinorésistance)"
        ],
        "actions_low": [
            "Limiter les sucres raffinés pour protéger à la fois les dents et le métabolisme",
            "Contrôle glycémie si antécédents familiaux"
        ]
    },
    "alzheimer": {
        "icon": "🧠",
        "label": "Risque Neurodégénératif (Alzheimer)",
        "description": "P. gingivalis a été retrouvée dans le cerveau de patients Alzheimer. Ses gingipaines détruisent les protéines neuroprotectrices et favorisent les plaques amyloïdes.",
        "references": "Dominy et al., Science Advances 2019 · Ilievski et al., 2018 · Olsen & Singhrao, 2015",
        "weight_gingivalis": 0.60,
        "weight_mutans": 0.05,
        "weight_diversity": 0.25,
        "weight_inflammation": 0.10,
        "thresholds": {"low": 20, "high": 50},
        "actions_high": [
            "Élimination de P. gingivalis — priorité absolue (traitement parodontal intensif)",
            "Supplémentation en omega-3 DHA (neuroprotecteur, 1g/jour minimum)",
            "Activité physique aérobie — seul facteur prouvé de neuroplasticité",
            "Suivi neurologique si > 60 ans avec P. gingivalis chronique"
        ],
        "actions_low": [
            "Maintenir un microbiome diversifié — effet neuroprotecteur indirect",
            "Alimentation méditerranéenne riche en polyphénols"
        ]
    },
    "colon": {
        "icon": "🦠",
        "label": "Risque Colorectal",
        "description": "Fusobacterium nucleatum, présent dans les dysbioses orales, est retrouvé en forte concentration dans les tumeurs colorectales. Migration oro-digestive documentée.",
        "references": "Castellarin et al., Genome Research 2012 · Rubinstein et al., Cell Host 2013",
        "weight_gingivalis": 0.25,
        "weight_mutans": 0.10,
        "weight_diversity": 0.50,
        "weight_inflammation": 0.15,
        "thresholds": {"low": 20, "high": 45},
        "actions_high": [
            "Coloscopie de dépistage si > 45 ans",
            "Augmenter drastiquement les fibres prébiotiques (30g/jour minimum)",
            "Réduire la viande rouge transformée",
            "Probiotiques intestinaux en complément des probiotiques oraux"
        ],
        "actions_low": [
            "Alimentation riche en fibres et légumes fermentés",
            "Dépistage de routine selon les recommandations d'âge"
        ]
    },
    "respiratoire": {
        "icon": "🫁",
        "label": "Risque Respiratoire / Pneumonie",
        "description": "Les bactéries orales aspirées colonisent les voies respiratoires basses. Risque de pneumonie d'aspiration multiplié par 4 en cas de dysbiose sévère.",
        "references": "Scannapieco et al., 2003 · ADA Journal 2021 · Azarpazhooh & Leake, 2006",
        "weight_gingivalis": 0.30,
        "weight_mutans": 0.15,
        "weight_diversity": 0.40,
        "weight_inflammation": 0.15,
        "thresholds": {"low": 25, "high": 50},
        "actions_high": [
            "Hygiène orale renforcée — particulièrement chez personnes âgées ou hospitalisées",
            "Brossage de la langue matin et soir (réduit charge bactérienne de 70%)",
            "Consultation pneumologique si toux chronique inexpliquée"
        ],
        "actions_low": [
            "Hygiène bucco-dentaire régulière",
            "Brossage de la langue quotidien"
        ]
    }
}


def calculer_score_systemique(s_mutans, p_gingivalis, diversite):
    """
    Calcule un score de risque systémique (0-100) pour chaque pathologie,
    basé sur les corrélations publiées dans la littérature.
    """
    # Normaliser les inputs en scores 0-100
    score_gingivalis = min(100, (p_gingivalis / 2.0) * 100)   # seuil critique = 2%
    score_mutans = min(100, (s_mutans / 8.0) * 100)            # seuil critique = 8%
    score_diversity_risk = max(0, 100 - diversite)             # inverse : faible diversité = risque élevé
    # Score inflammation estimé (proxy combiné)
    score_inflammation = min(100, (score_gingivalis * 0.6 + score_diversity_risk * 0.4))

    results = {}
    for key, corr in SYSTEMIC_CORRELATIONS.items():
        raw_score = (
            corr["weight_gingivalis"]    * score_gingivalis +
            corr["weight_mutans"]        * score_mutans +
            corr["weight_diversity"]     * score_diversity_risk +
            corr["weight_inflammation"]  * score_inflammation
        )
        score = round(min(100, max(0, raw_score)))
        level = "low" if score < corr["thresholds"]["low"] else \
                "high" if score > corr["thresholds"]["high"] else "med"
        results[key] = {
            **corr,
            "score": score,
            "level": level,
            "actions": corr["actions_high"] if level == "high" else corr["actions_low"]
        }

    return dict(sorted(results.items(), key=lambda x: -x[1]["score"]))


# ============================================================
# ANALYSE PHOTO VIA CLAUDE VISION
# ============================================================
def analyser_photo_bouche(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Envoie l'image à Claude claude-sonnet-4-20250514 pour analyse visuelle de la cavité buccale.
    Retourne un dict structuré avec findings, score global et recommandations.
    """
    if not ANTHROPIC_API_KEY:
        return {"error": "Clé API Anthropic manquante. Ajoutez ANTHROPIC_API_KEY dans st.secrets."}

    b64_image = base64.standard_b64encode(image_bytes).decode("utf-8")

    system_prompt = """Tu es un assistant d'aide à la décision dentaire pour des professionnels de santé.
Tu analyses des photos de cavité buccale et détectes des signes visuels d'anomalies.
IMPORTANT : tu fournis une aide à la décision, PAS un diagnostic médical.
Réponds UNIQUEMENT en JSON valide, sans markdown, sans backticks, sans texte avant ou après.
Structure exacte requise :
{
  "qualite_image": "bonne|moyenne|insuffisante",
  "zones_analysees": ["liste des zones visibles"],
  "findings": [
    {
      "zone": "nom de la zone",
      "observation": "description précise",
      "severite": "normal|attention|alerte",
      "detail": "explication clinique courte"
    }
  ],
  "score_global": 0-100,
  "profil_visuel": "Bouche saine|Inflammation légère|Inflammation modérée|Dysbiose visible|Urgence clinique",
  "recommandations_immediates": ["action 1", "action 2"],
  "disclaimer": "Cette analyse est une aide à la décision pour professionnels. Ne constitue pas un diagnostic.",
  "confiance": "élevée|modérée|faible"
}
Le score_global représente la santé apparente (100 = parfaite, 0 = urgence).
Sois précis, factuel, et professionnel."""

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1500,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": b64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": "Analyse cette photo de cavité buccale. Identifie tous les signes visuels observables : inflammation gingivale, tartre, plaque visible, lésions suspectes, récessions, coloration anormale, état de l'émail. Fournis ton analyse complète en JSON."
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01"
            },
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        raw = data["content"][0]["text"].strip()
        # Nettoyer les éventuels backticks
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except requests.exceptions.Timeout:
        return {"error": "Délai d'attente dépassé. Réessayez."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Erreur réseau : {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"Réponse invalide de l'API : {str(e)}"}


def render_photo_analysis(result: dict):
    """Affiche les résultats de l'analyse photo de façon visuelle."""
    if "error" in result:
        st.error(f"⚠️ {result['error']}")
        if "Clé API" in result["error"]:
            st.info("👉 Ajoutez `ANTHROPIC_API_KEY = 'sk-ant-...'` dans votre fichier `.streamlit/secrets.toml`")
        return

    # Score global
    score = result.get("score_global", 50)
    profil = result.get("profil_visuel", "N/A")
    confiance = result.get("confiance", "modérée")
    qualite = result.get("qualite_image", "N/A")

    col_score, col_info = st.columns([1, 3])
    with col_score:
        color = "#16a34a" if score >= 70 else "#d97706" if score >= 45 else "#e11d48"
        st.markdown(f"""
        <div style="text-align:center; background: linear-gradient(135deg, {color}22, {color}11);
             border: 2px solid {color}; border-radius: 16px; padding: 24px;">
            <div style="font-family: 'DM Serif Display', serif; font-size: 3rem; color: {color}; line-height:1;">
                {score}
            </div>
            <div style="font-size: 0.75rem; color: #6b7280; margin-top: 4px;">Score santé visuelle</div>
            <div style="font-size: 0.8rem; font-weight: 600; color: {color}; margin-top: 8px;">{profil}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        st.markdown(f"**Qualité image :** `{qualite}` · **Confiance analyse :** `{confiance}`")
        zones = result.get("zones_analysees", [])
        if zones:
            st.markdown(f"**Zones analysées :** {' · '.join(zones)}")

        st.markdown("**Findings détectés :**")
        findings = result.get("findings", [])
        for f in findings:
            sev = f.get("severite", "normal")
            css = "finding-alert" if sev == "alerte" else "finding-warn" if sev == "attention" else "finding-ok"
            icon = "🔴" if sev == "alerte" else "🟡" if sev == "attention" else "🟢"
            st.markdown(
                f"<span class='finding-badge {css}'>{icon} {f.get('zone', '')} — {f.get('observation', '')}</span>",
                unsafe_allow_html=True
            )

    st.markdown("---")

    # Détails findings
    findings = result.get("findings", [])
    if findings:
        st.markdown("#### 🔬 Analyse détaillée par zone")
        cols = st.columns(min(len(findings), 3))
        for i, f in enumerate(findings):
            sev = f.get("severite", "normal")
            with cols[i % 3]:
                css = "risk-high" if sev == "alerte" else "risk-med" if sev == "attention" else "risk-low"
                icon = "🔴" if sev == "alerte" else "🟡" if sev == "attention" else "🟢"
                st.markdown(f"""
                <div class='risk-card {css}'>
                    <div style="font-weight:600; font-size:0.9rem;">{icon} {f.get('zone', 'N/A')}</div>
                    <div style="font-size:0.85rem; margin-top:4px; color:#374151;">{f.get('observation', '')}</div>
                    <div style="font-size:0.78rem; margin-top:6px; color:#6b7280; font-style:italic;">{f.get('detail', '')}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # Recommandations immédiates
    recos = result.get("recommandations_immediates", [])
    if recos:
        st.markdown("#### ✅ Actions immédiates recommandées")
        for r in recos:
            st.markdown(f"- {r}")

    # Disclaimer
    disclaimer = result.get("disclaimer", "")
    if disclaimer:
        st.caption(f"⚕️ *{disclaimer}*")


# ============================================================
# MOTEUR DE RECOMMANDATIONS (inchangé + amélioré)
# ============================================================
def generer_recommandations(s_mutans, p_gingivalis, diversite):
    plan = {
        "priorites": [], "aliments_favoriser": [], "aliments_eviter": [],
        "probiotiques": [], "hygiene": [],
        "suivi_semaines": 24, "profil_label": "", "profil_description": ""
    }
    nb = sum([s_mutans > 3.0, p_gingivalis > 0.5, diversite < 50])
    if nb == 0:
        plan["profil_label"] = "🟢 Microbiome Équilibré"
        plan["profil_description"] = "Votre flore buccale est protectrice. Continuez vos bonnes habitudes."
        plan["suivi_semaines"] = 24
    elif nb == 1:
        plan["profil_label"] = "🟡 Déséquilibre Modéré"
        plan["profil_description"] = "Un déséquilibre est détecté. Des ajustements ciblés corrigeront la situation en 2-3 mois."
        plan["suivi_semaines"] = 12
    else:
        plan["profil_label"] = "🔴 Dysbiose Active"
        plan["profil_description"] = "Plusieurs marqueurs sont en alerte. Un plan d'action renforcé est nécessaire."
        plan["suivi_semaines"] = 8

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
        plan["aliments_eviter"] += ["Bonbons et sucreries", "Sodas et boissons sucrées", "Pain blanc et viennoiseries", "Jus de fruits (fructose élevé)"]
        plan["aliments_favoriser"] += ["Fromage à pâte dure (Gruyère, Comté)", "Yaourt nature sans sucre", "Légumes crus et croquants", "Thé vert sans sucre", "Noix et amandes"]
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
        plan["aliments_eviter"] += ["Tabac sous toutes formes", "Alcool en excès", "Sucres raffinés", "Aliments ultra-transformés"]
        plan["aliments_favoriser"] += ["Poissons gras 2-3×/semaine (oméga-3)", "Myrtilles et framboises (polyphénols)", "Légumes verts feuillus (nitrates)", "Huile d'olive extra vierge", "Ail et oignon crus (allicine)"]
        plan["probiotiques"].append({"nom": "Lactobacillus reuteri + Lactobacillus salivarius", "forme": "Pastilles à dissoudre en bouche 2×/jour", "duree": "3 à 6 mois", "benefice": "Réduit P. gingivalis et le saignement gingival", "marques": "Sunstar GUM PerioBalance, Blis K12"})

    if diversite < 50:
        plan["priorites"].append({
            "icone": "🌱", "titre": "Restaurer la diversité microbienne orale",
            "urgence": "Moderee" if diversite > 30 else "Elevee",
            "explication": f"Score de diversité : {diversite}/100 (optimal > 65). Une flore appauvrie ne se défend pas contre les pathogènes.",
            "actions": [
                "Diversifier : objectif 30 plantes différentes par semaine",
                "Réduire les bains de bouche antiseptiques quotidiens",
                "Augmenter les fibres prébiotiques (poireau, ail, oignon)",
                "Boire 1.5L d'eau par jour minimum"
            ]
        })
        plan["aliments_favoriser"] += ["Légumes racines variés (fibres prébiotiques)", "Pomme avec la peau (pectine)", "Légumineuses (lentilles, pois chiches)", "Légumes fermentés (choucroute, kimchi)", "Kombucha sans sucre ajouté"]
        plan["aliments_eviter"] += ["Bains de bouche antiseptiques quotidiens", "Antibiotiques inutiles", "Fast-food régulier"]
        plan["probiotiques"].append({"nom": "Streptococcus salivarius K12 + M18", "forme": "Pastilles à sucer le soir après brossage", "duree": "2 à 3 mois puis entretien trimestriel", "benefice": "Recolonise la flore avec des espèces protectrices", "marques": "BLIS K12, Nasal Guard Throat Guard"})

    if nb == 0:
        plan["priorites"].append({
            "icone": "✅", "titre": "Maintenir l'équilibre de votre microbiome",
            "urgence": "Routine",
            "explication": "Votre microbiome oral est en bonne santé. Préservez cet équilibre sur le long terme.",
            "actions": ["Brossage 2×/jour avec brosse souple", "Fil dentaire 1×/jour", "Alimentation variée riche en fibres", "Contrôle dans 6 mois"]
        })
        plan["aliments_favoriser"] += ["Alimentation méditerranéenne variée", "Eau comme boisson principale", "Produits laitiers fermentés (yaourt, kéfir)"]

    plan["hygiene"] = [
        {"moment": "🌅 Matin", "actions": ["Brossage 2 min brosse souple (électrique recommandée)", "Brossage de la langue arrière vers avant", "Bain de bouche non-alcoolisé si recommandé"]},
        {"moment": "🌙 Soir (le plus important)", "actions": ["Fil dentaire ou brossettes AVANT le brossage", "Brossage 2 min minimum", "Probiotique oral à dissoudre si prescrit", "Ne plus rien manger ni boire après (sauf eau)"]},
        {"moment": "🍽️ Après les repas", "actions": ["Attendre 30 min avant de brosser (émail fragilisé)", "Boire un verre d'eau pour rincer", "Chewing-gum xylitol 5 min si pas de brossage possible"]}
    ]

    plan["aliments_favoriser"] = list(dict.fromkeys(plan["aliments_favoriser"]))
    plan["aliments_eviter"] = list(dict.fromkeys(plan["aliments_eviter"]))
    return plan


# ============================================================
# GÉNÉRATION PDF
# ============================================================
def generer_pdf(patient_nom, r_carieux, r_paro, diversite, historique_df, plan, scores_systemiques=None):
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
        BLUE = colors.HexColor('#1a3a5c')
        LIGHT_BLUE = colors.HexColor('#dbeafe')
        GREEN = colors.HexColor('#16a34a')
        RED = colors.HexColor('#e11d48')
        ORANGE = colors.HexColor('#d97706')
        GRAY_BG = colors.HexColor('#f9fafb')

        title_style = ParagraphStyle('Title', fontSize=18, textColor=colors.white,
                                     alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=4)
        sub_style = ParagraphStyle('Sub', fontSize=10, textColor=colors.white,
                                   alignment=TA_CENTER, fontName='Helvetica', spaceAfter=6)
        h1_style = ParagraphStyle('H1', fontSize=13, textColor=BLUE,
                                  fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=4)
        h2_style = ParagraphStyle('H2', fontSize=11, textColor=BLUE,
                                  fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=3)
        body_style = ParagraphStyle('Body', fontSize=10, fontName='Helvetica', spaceAfter=3, leading=14)
        italic_style = ParagraphStyle('Italic', fontSize=9, fontName='Helvetica-Oblique',
                                      textColor=colors.HexColor('#555555'), spaceAfter=4)
        small_style = ParagraphStyle('Small', fontSize=8, fontName='Helvetica',
                                     textColor=colors.grey, alignment=TA_CENTER)

        elems = []

        # EN-TÊTE
        header_data = [[Paragraph("OralBiome - Rapport Patient Complet", title_style)],
                       [Paragraph("Microbiome Oral Predictif + Risques Systemiques | Rapport Personnalise", sub_style)]]
        header_table = Table(header_data, colWidths=[180*mm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BLUE),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        elems.append(header_table)
        elems.append(Spacer(1, 5*mm))

        info_data = [[
            Paragraph(f"<b>Patient :</b> {patient_nom}", body_style),
            Paragraph(f"<b>Date :</b> {date.today().strftime('%d/%m/%Y')}", body_style)
        ]]
        info_table = Table(info_data, colWidths=[90*mm, 90*mm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BLUE),
            ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elems.append(info_table)
        elems.append(Spacer(1, 6*mm))

        # RÉSULTATS MICROBIOME
        elems.append(Paragraph("Resultats de l'Analyse Microbiome", h1_style))
        elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE))
        res_data = [
            [Paragraph("<b>Risque Carieux</b>", body_style),
             Paragraph(f"<font color='{'#e11d48' if r_carieux=='Eleve' else '#16a34a'}'><b>{r_carieux}</b></font>", body_style)],
            [Paragraph("<b>Risque Parodontal</b>", body_style),
             Paragraph(f"<font color='{'#e11d48' if r_paro=='Eleve' else '#16a34a'}'><b>{r_paro}</b></font>", body_style)],
            [Paragraph("<b>Score de Diversite</b>", body_style),
             Paragraph(f"<b>{diversite}/100</b> (optimal > 65)", body_style)],
        ]
        res_table = Table(res_data, colWidths=[90*mm, 90*mm])
        res_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), GRAY_BG),
            ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.white),
        ]))
        elems.append(res_table)
        elems.append(Spacer(1, 6*mm))

        # SCORES SYSTÉMIQUES
        if scores_systemiques:
            elems.append(Paragraph("Scores de Risque Systemique", h1_style))
            elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE))
            elems.append(Paragraph(
                "Ces scores sont calcules sur la base de correlations publiees dans la litterature scientifique. "
                "Ils constituent une aide a la decision et ne remplacent pas un avis medical.",
                italic_style
            ))
            elems.append(Spacer(1, 3*mm))

            sys_rows = [["Pathologie", "Score /100", "Niveau", "Action principale"]]
            for key, data in scores_systemiques.items():
                level_label = "Eleve" if data["level"] == "high" else "Modere" if data["level"] == "med" else "Faible"
                action = data["actions"][0] if data["actions"] else "-"
                sys_rows.append([
                    Paragraph(f"{data['icon']} {data['label']}", body_style),
                    Paragraph(f"<b>{data['score']}</b>", body_style),
                    Paragraph(level_label, body_style),
                    Paragraph(action[:80] + "..." if len(action) > 80 else action, body_style)
                ])
            sys_table = Table(sys_rows, colWidths=[55*mm, 22*mm, 22*mm, 81*mm])
            sys_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), BLUE),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [GRAY_BG, colors.white]),
                ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#e5e7eb')),
            ]))
            elems.append(sys_table)
            elems.append(Spacer(1, 6*mm))

        # PLAN D'ACTION
        if plan["priorites"]:
            elems.append(Paragraph("Plan d'Action - Priorites", h1_style))
            elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE))
            for i, p in enumerate(plan["priorites"]):
                urgence = p["urgence"]
                badge = "URGENCE ELEVEE" if urgence=="Elevee" else "MODEREE" if urgence=="Moderee" else "ROUTINE"
                elems.append(Paragraph(f"Priorite {i+1} — {p['titre']} [{badge}]", h2_style))
                for action in p["actions"]:
                    elems.append(Paragraph(f"• {action}", body_style))
                elems.append(Spacer(1, 3*mm))

        # NUTRITION
        elems.append(Paragraph("Plan Nutritionnel", h1_style))
        elems.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE))
        if plan["aliments_favoriser"] or plan["aliments_eviter"]:
            max_items = max(len(plan["aliments_favoriser"]), len(plan["aliments_eviter"]))
            nutr_rows = []
            for i in range(max_items):
                fav = plan["aliments_favoriser"][i] if i < len(plan["aliments_favoriser"]) else ""
                evi = plan["aliments_eviter"][i] if i < len(plan["aliments_eviter"]) else ""
                nutr_rows.append([Paragraph(f"+ {fav}", body_style), Paragraph(f"- {evi}", body_style)])
            nutr_table = Table(nutr_rows, colWidths=[90*mm, 90*mm])
            nutr_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f0fdf4')),
                ('BACKGROUND', (1,0), (1,-1), colors.HexColor('#fff1f2')),
                ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('LINEBELOW', (0,0), (-1,-2), 0.3, colors.white),
            ]))
            elems.append(nutr_table)

        # PIED DE PAGE
        elems.append(Spacer(1, 8*mm))
        footer_data = [
            [Paragraph("Ce rapport est fourni a titre preventif et informatif. Ne constitue pas un diagnostic medical.", small_style)],
            [Paragraph("OralBiome - Microbiome Oral Predictif | contact@oralbiome.com", small_style)]
        ]
        footer_table = Table(footer_data, colWidths=[180*mm])
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BLUE),
            ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elems.append(footer_table)

        doc.build(elems)
        return buffer.getvalue()

    except ImportError:
        return b"Installez reportlab : pip install reportlab"


# ============================================================
# DONNÉES INITIALES
# ============================================================
def donnees_initiales():
    patients = {}
    df1 = pd.DataFrame({
        "Date": ["12/10/2023", "08/04/2026"],
        "Acte / Test": ["Examen Initial", "Controle"],
        "S. mutans (%)": [4.2, 4.2],
        "P. gingiv. (%)": [0.8, 0.3],
        "Diversite (%)": [45, 75],
        "Status": ["Alerte", "Alerte"]
    })
    patients["Jean Dupont"] = {
        "id": "P001", "nom": "Jean Dupont", "age": 42, "email": "jean.dupont@email.com",
        "telephone": "+32 472 123 456", "date_naissance": "15/03/1982",
        "historique": df1, "s_mutans": 4.2, "p_gingivalis": 0.3, "diversite": 75,
        "code_patient": "OB-P001"
    }
    df2 = pd.DataFrame({
        "Date": ["05/01/2024"],
        "Acte / Test": ["Examen Initial"],
        "S. mutans (%)": [1.2],
        "P. gingiv. (%)": [0.1],
        "Diversite (%)": [82],
        "Status": ["Stable"]
    })
    patients["Marie Martin"] = {
        "id": "P002", "nom": "Marie Martin", "age": 35, "email": "marie.martin@email.com",
        "telephone": "+32 478 654 321", "date_naissance": "22/07/1989",
        "historique": df2, "s_mutans": 1.2, "p_gingivalis": 0.1, "diversite": 82,
        "code_patient": "OB-P002"
    }
    df3 = pd.DataFrame({
        "Date": ["18/02/2025"],
        "Acte / Test": ["Examen Initial"],
        "S. mutans (%)": [6.5],
        "P. gingiv. (%)": [1.8],
        "Diversite (%)": [38],
        "Status": ["Alerte"]
    })
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
for key, val in [
    ("mode", "choix"), ("connecte", False), ("patient_sel", "Jean Dupont"),
    ("vue", "dossier"), ("patient_connecte", None)
]:
    if key not in st.session_state:
        st.session_state[key] = val

if "patients" not in st.session_state:
    st.session_state.patients = donnees_initiales()


# ============================================================
# ÉCRAN DE CHOIX
# ============================================================
if st.session_state.mode == "choix":
    st.markdown("""
    <div class="ob-header">
        <h1>🦷 OralBiome</h1>
        <p>Microbiome Oral Prédictif — Prévention dentaire et systémique personnalisée par l'IA</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown("#### 🩺 Praticien")
        st.markdown("Tableau de bord complet, gestion des dossiers, analyses systémiques et rapports PDF.")
        if st.button("Connexion Praticien", use_container_width=True, type="primary"):
            st.session_state.mode = "praticien"; st.rerun()
    with col2:
        st.markdown("#### 🧑 Patient")
        st.markdown("Votre rapport personnalisé, plan nutritionnel, risques systémiques et historique.")
        if st.button("Accès Patient", use_container_width=True):
            st.session_state.mode = "patient"; st.rerun()
    with col3:
        st.markdown("#### ℹ️ À propos")
        st.markdown("OralBiome corrèle votre microbiote oral avec vos risques cardiovasculaires, diabète, Alzheimer et plus.")
        st.markdown("**contact@oralbiome.com**")


# ============================================================
# PORTAIL PATIENT
# ============================================================
elif st.session_state.mode == "patient":

    if st.session_state.patient_connecte is None:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center; color:#1a3a5c;'>🦷 Espace Patient</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#888;'>Consultez votre rapport personnalisé</p>", unsafe_allow_html=True)
            st.markdown("---")
            code = st.text_input("Votre code patient", placeholder="Ex: OB-P001")
            if st.button("Accéder à mon dossier", use_container_width=True, type="primary"):
                found = next((n for n, d in st.session_state.patients.items() if d.get("code_patient") == code.strip()), None)
                if found:
                    st.session_state.patient_connecte = found; st.rerun()
                else:
                    st.error("Code patient invalide.")
            if st.button("Retour à l'accueil", use_container_width=True):
                st.session_state.mode = "choix"; st.rerun()
            st.caption("Codes démo : OB-P001 · OB-P002 · OB-P003")
    else:
        patient = st.session_state.patients[st.session_state.patient_connecte]
        s_mutans = patient["s_mutans"]
        p_gingivalis = patient["p_gingivalis"]
        diversite = patient["diversite"]
        r_carieux = "Eleve" if s_mutans > 3.0 else "Faible"
        r_paro = "Eleve" if p_gingivalis > 0.5 else "Faible"
        en_alerte = r_carieux == "Eleve" or r_paro == "Eleve" or diversite < 50
        plan = generer_recommandations(s_mutans, p_gingivalis, diversite)
        scores_sys = calculer_score_systemique(s_mutans, p_gingivalis, diversite)

        st.sidebar.markdown(f"### 👋 {patient['nom'].split()[0]}")
        st.sidebar.markdown(f"Code : `{patient['code_patient']}`")
        st.sidebar.markdown(f"**{'🔴 En alerte' if en_alerte else '🟢 Équilibré'}**")
        st.sidebar.markdown(f"Prochain contrôle : **{plan['suivi_semaines']} semaines**")
        st.sidebar.markdown("---")
        if st.sidebar.button("Se déconnecter"):
            st.session_state.patient_connecte = None; st.rerun()
        if st.sidebar.button("Retour accueil"):
            st.session_state.patient_connecte = None; st.session_state.mode = "choix"; st.rerun()

        st.markdown(f"""
        <div class='patient-header'>
            <h2>🦷 Bonjour {patient['nom']} !</h2>
            <p>Rapport microbiome oral personnalisé · {date.today().strftime('%d/%m/%Y')}</p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Risque Carieux", r_carieux, delta_color="inverse")
        c2.metric("Risque Parodontal", r_paro, delta_color="inverse")
        c3.metric("Diversité Microbienne", f"{diversite}/100")
        st.markdown("---")

        tp1, tp2, tp3, tp4, tp5, tp6 = st.tabs([
            "📊 Mon Profil", "🧬 Risques Systémiques", "📸 Analyse Photo",
            "🚨 Mes Actions", "🥗 Nutrition & Probiotiques", "📥 Rapport PDF"
        ])

        with tp1:
            st.header("📊 Mon Profil Bactérien")
            if en_alerte:
                st.warning(f"**{plan['profil_label']}** — {plan['profil_description']}")
            else:
                st.success(f"**{plan['profil_label']}** — {plan['profil_description']}")
            if not patient["historique"].empty:
                st.dataframe(patient["historique"], use_container_width=True, hide_index=True)

        with tp2:
            st.header("🧬 Risques Systémiques")
            st.markdown("*Corrélations établies entre votre microbiote oral et vos risques de santé généraux, basées sur la littérature scientifique peer-reviewed.*")
            st.markdown("---")
            for key, data in scores_sys.items():
                score = data["score"]
                level = data["level"]
                score_css = "score-high" if level == "high" else "score-med" if level == "med" else "score-low"
                card_css = "risk-high" if level == "high" else "risk-med" if level == "med" else "risk-low"
                col_ring, col_content = st.columns([1, 6])
                with col_ring:
                    st.markdown(f"<div class='score-ring {score_css}'>{score}</div>", unsafe_allow_html=True)
                with col_content:
                    st.markdown(f"""
                    <div class='systemic-card'>
                        <div class='systemic-title'>{data['icon']} {data['label']}</div>
                        <div style="font-size:0.85rem; color:#4b5563; margin-bottom:8px;">{data['description']}</div>
                        <div style="font-size:0.75rem; color:#9ca3af; margin-bottom:8px;"><em>Réf : {data['references']}</em></div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("Voir les recommandations →"):
                        for action in data["actions"]:
                            st.markdown(f"- {action}")
                st.markdown("")

            st.info("⚕️ Ces scores sont des estimations basées sur des corrélations épidémiologiques publiées. Ils ne constituent pas un diagnostic médical. Consultez votre médecin pour tout suivi.")

        with tp3:
            st.header("📸 Analyse Photo de la Cavité Buccale")
            st.markdown("Uploadez une photo de votre bouche (gencives, dents, langue). L'IA détecte les signes visuels d'inflammation, tartre, lésions et anomalies.")
            st.caption("📌 Conseils : bonne lumière, bouche ouverte, photo nette. JPEG ou PNG.")
            st.markdown("---")

            if not ANTHROPIC_API_KEY:
                st.warning("⚠️ Fonctionnalité disponible après configuration de la clé API Anthropic dans `st.secrets`.")
            else:
                uploaded = st.file_uploader("Choisir une photo", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
                if uploaded:
                    img_bytes = uploaded.read()
                    mime = "image/png" if uploaded.name.endswith(".png") else "image/jpeg"
                    col_img, col_res = st.columns([1, 2])
                    with col_img:
                        st.image(img_bytes, caption="Photo uploadée", use_container_width=True)
                    with col_res:
                        with st.spinner("🔍 Analyse en cours par l'IA..."):
                            result = analyser_photo_bouche(img_bytes, mime)
                        render_photo_analysis(result)

        with tp4:
            st.header("🚨 Mes Actions Prioritaires")
            for i, p in enumerate(plan["priorites"]):
                urg = p["urgence"]
                badge = "URGENT" if urg=="Elevee" else "MODÉRÉ" if urg=="Moderee" else "ROUTINE"
                css = "reco-red" if urg=="Elevee" else "reco-orange" if urg=="Moderee" else "reco-green"
                st.markdown(f"### {p['icone']} Action {i+1} — {p['titre']} `{badge}`")
                st.markdown(f"<div class='reco-card {css}'><em>{p['explication']}</em></div>", unsafe_allow_html=True)
                for action in p["actions"]:
                    st.markdown(f"- {action}")
                st.markdown("---")

        with tp5:
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
            st.header("💊 Probiotiques Recommandés")
            for prob in plan["probiotiques"]:
                with st.expander(f"🧫 {prob['nom']}", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Forme :** {prob['forme']}")
                        st.markdown(f"**Durée :** {prob['duree']}")
                    with c2:
                        st.markdown(f"**Bénéfice :** {prob['benefice']}")
                        st.markdown(f"**Produits :** `{prob['marques']}`")

        with tp6:
            st.header("📥 Rapport PDF Complet")
            st.markdown("Votre rapport inclut votre profil bactérien, les **risques systémiques corrélés**, votre plan nutritionnel et votre protocole d'hygiène.")
            if st.button("Générer mon rapport PDF", type="primary", use_container_width=True):
                with st.spinner("Génération en cours..."):
                    pdf = generer_pdf(patient["nom"], r_carieux, r_paro, diversite, patient["historique"], plan, scores_sys)
                st.download_button(
                    "📥 Télécharger mon Rapport OralBiome (PDF)",
                    data=pdf,
                    file_name=f"OralBiome_MonRapport_{patient['id']}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )


# ============================================================
# PORTAIL PRATICIEN
# ============================================================
elif st.session_state.mode == "praticien":

    if not st.session_state.connecte:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h2 style='text-align:center; color:#1a3a5c;'>🦷 OralBiome</h2>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align:center; color:#64748b;'>Portail Praticien</h4>", unsafe_allow_html=True)
            st.markdown("---")
            email = st.text_input("Email Professionnel")
            mdp = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter", use_container_width=True, type="primary"):
                if email == "contact@oralbiome.com" and mdp == "mvp2024":
                    st.session_state.connecte = True; st.rerun()
                else:
                    st.error("Identifiants incorrects. Demo : contact@oralbiome.com / mvp2024")
            if st.button("Retour à l'accueil", use_container_width=True):
                st.session_state.mode = "choix"; st.rerun()
    else:
        # SIDEBAR
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
        ms1, ms2 = st.sidebar.columns(2)
        ms1.metric("Patients", nb_patients)
        ms2.metric("Alertes", nb_alertes)
        st.sidebar.markdown("---")

        rech = st.sidebar.text_input("Rechercher...", placeholder="Nom ou ID")
        pf = {n: d for n, d in st.session_state.patients.items()
              if rech.lower() in n.lower() or rech.lower() in d["id"].lower()} if rech else st.session_state.patients
        for nom, data in pf.items():
            icon = "🔴" if (data["s_mutans"] > 3.0 or data["p_gingivalis"] > 0.5 or data["diversite"] < 50) else "🟢"
            is_sel = nom == st.session_state.patient_sel
            if st.sidebar.button(f"{icon} {data['id']} — {nom}", use_container_width=True,
                                  type="primary" if is_sel else "secondary"):
                st.session_state.patient_sel = nom; st.session_state.vue = "dossier"; st.rerun()
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Déconnecter", use_container_width=True):
            st.session_state.connecte = False; st.rerun()
        if st.sidebar.button("Retour accueil", use_container_width=True):
            st.session_state.connecte = False; st.session_state.mode = "choix"; st.rerun()

        # VUE LISTE
        if st.session_state.vue == "liste":
            st.title("👥 Gestion des Patients")
            lf1, lf2, lf3 = st.columns(3)
            with lf1:
                filtre = st.selectbox("Filtrer", ["Tous", "Alerte uniquement", "Stable uniquement"])
            with lf3:
                if st.button("➕ Nouveau Patient", type="primary"):
                    st.session_state.vue = "nouveau"; st.rerun()
            donnees = []
            for nom, data in st.session_state.patients.items():
                ea = data["s_mutans"] > 3.0 or data["p_gingivalis"] > 0.5 or data["diversite"] < 50
                if filtre == "Alerte uniquement" and not ea: continue
                if filtre == "Stable uniquement" and ea: continue
                sys_scores = calculer_score_systemique(data["s_mutans"], data["p_gingivalis"], data["diversite"])
                top_sys = max(sys_scores.items(), key=lambda x: x[1]["score"])
                donnees.append({
                    "ID": data["id"], "Nom": nom, "Âge": data["age"],
                    "Risque Carieux": "⚠️ Élevé" if data["s_mutans"] > 3.0 else "✅ Faible",
                    "Risque Parodontal": "⚠️ Élevé" if data["p_gingivalis"] > 0.5 else "✅ Faible",
                    "Diversité": f"{data['diversite']}/100",
                    "Risque Systémique Principal": f"{top_sys[1]['icon']} {top_sys[1]['label']} ({top_sys[1]['score']}/100)",
                    "Statut": "🔴 Alerte" if ea else "🟢 Stable"
                })
            if donnees:
                st.dataframe(pd.DataFrame(donnees), use_container_width=True, hide_index=True)

        # VUE NOUVEAU
        elif st.session_state.vue == "nouveau":
            st.title("➕ Nouveau Patient")
            with st.form("form_nouveau"):
                nc1, nc2 = st.columns(2)
                with nc1:
                    nn = st.text_input("Nom complet *")
                    ne = st.text_input("Email")
                    nd_nais = st.date_input("Date de naissance", value=date(1985, 1, 1))
                with nc2:
                    na = st.number_input("Âge", 1, 120, 35)
                    nt = st.text_input("Téléphone")
                st.markdown("### Première Analyse")
                nc3, nc4, nc5 = st.columns(3)
                with nc3: is_ = st.number_input("S. mutans (%)", 0.0, 10.0, 2.0, step=0.1)
                with nc4: ip_ = st.number_input("P. gingivalis (%)", 0.0, 5.0, 0.2, step=0.1)
                with nc5: id_ = st.number_input("Diversité (%)", 0, 100, 70)
                aj = st.checkbox("Enregistrer comme examen initial", value=True)
                sub = st.form_submit_button("Créer le dossier", use_container_width=True, type="primary")
                if sub:
                    if not nn.strip():
                        st.error("Le nom est obligatoire.")
                    elif nn in st.session_state.patients:
                        st.error("Ce patient existe déjà.")
                    else:
                        nid = f"P{str(len(st.session_state.patients)+1).zfill(3)}"
                        df_n = pd.DataFrame(columns=["Date", "Acte / Test", "S. mutans (%)", "P. gingiv. (%)", "Diversite (%)", "Status"])
                        if aj:
                            s = "Alerte" if is_ > 3.0 or ip_ > 0.5 or id_ < 50 else "Stable"
                            df_n.loc[0] = [date.today().strftime("%d/%m/%Y"), "Examen Initial", is_, ip_, id_, s]
                        st.session_state.patients[nn] = {
                            "id": nid, "nom": nn, "age": na, "email": ne, "telephone": nt,
                            "date_naissance": nd_nais.strftime("%d/%m/%Y"),
                            "historique": df_n, "s_mutans": is_ if aj else 0.0,
                            "p_gingivalis": ip_ if aj else 0.0, "diversite": id_ if aj else 70,
                            "code_patient": f"OB-{nid}"
                        }
                        st.session_state.patient_sel = nn
                        st.session_state.vue = "dossier"
                        st.success(f"Dossier créé ! Code patient : **OB-{nid}**")
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
                en_alerte = r_carieux == "Eleve" or r_paro == "Eleve" or diversite < 50
                plan = generer_recommandations(s_mutans, p_gingivalis, diversite)
                scores_sys = calculer_score_systemique(s_mutans, p_gingivalis, diversite)

                badge = "🔴 En Alerte" if en_alerte else "🟢 Stable"
                st.markdown(f"## 🦷 {patient['nom']}  `{patient['id']}`  —  {badge}")
                st.caption(f"Âge : {patient['age']} ans  ·  {patient['email']}  ·  Code : **{patient.get('code_patient','')}**")
                st.markdown("---")

                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Risque Carieux", r_carieux, delta_color="inverse")
                m2.metric("Risque Parodontal", r_paro, delta_color="inverse")
                m3.metric("Diversité", f"{diversite}/100")
                m4.metric("Visites", len(patient["historique"]))
                top_sys = max(scores_sys.items(), key=lambda x: x[1]["score"])
                m5.metric("Risque Sys. Principal", f"{top_sys[1]['score']}/100", top_sys[1]["icon"])
                st.markdown("---")

                if en_alerte:
                    st.warning(f"**{plan['profil_label']}** — {plan['profil_description']}")
                else:
                    st.success(f"**{plan['profil_label']}** — {plan['profil_description']}")

                st.info(f"Code patient : **{patient.get('code_patient', '')}** — À communiquer au patient pour son accès portail.")
                st.markdown("---")

                tab1, tab2, tab3, tab4 = st.tabs([
                    "🧬 Risques Systémiques", "🚨 Plan d'Action", "📸 Analyse Photo", "📂 Historique & PDF"
                ])

                with tab1:
                    st.header("🧬 Corrélations Microbiome → Risques Systémiques")
                    st.caption("Scores calculés selon les pondérations de la littérature scientifique peer-reviewed.")

                    # Vue synthétique tableau
                    rows = []
                    for key, data in scores_sys.items():
                        level_label = "🔴 Élevé" if data["level"] == "high" else "🟡 Modéré" if data["level"] == "med" else "🟢 Faible"
                        rows.append({
                            "Pathologie": f"{data['icon']} {data['label']}",
                            "Score": data["score"],
                            "Niveau": level_label,
                            "Action prioritaire": data["actions"][0] if data["actions"] else "-"
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    st.markdown("---")

                    # Vue détaillée
                    for key, data in scores_sys.items():
                        score = data["score"]
                        level = data["level"]
                        if level == "high":
                            col1, col2 = st.columns([1, 6])
                            with col1:
                                st.markdown(f"<div class='score-ring score-high'>{score}</div>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"**{data['icon']} {data['label']}**")
                                st.markdown(f"*{data['description']}*")
                                with st.expander("Protocole clinique recommandé"):
                                    for action in data["actions"]:
                                        st.markdown(f"- {action}")
                                    st.caption(f"Références : {data['references']}")
                            st.markdown("")

                with tab2:
                    st.header("Plan d'Action & Recommandations")
                    for i, p in enumerate(plan["priorites"]):
                        urg = p["urgence"]
                        badge_u = "URGENT" if urg=="Elevee" else "MODÉRÉ" if urg=="Moderee" else "ROUTINE"
                        css = "reco-red" if urg=="Elevee" else "reco-orange" if urg=="Moderee" else "reco-green"
                        st.markdown(f"#### {p['icone']} Priorité {i+1} — {p['titre']} `{badge_u}`")
                        st.markdown(f"<div class='reco-card {css}'><em>{p['explication']}</em></div>", unsafe_allow_html=True)
                        for action in p["actions"]:
                            st.markdown(f"- {action}")
                        st.markdown("---")

                with tab3:
                    st.header("📸 Analyse Visuelle de la Cavité Buccale")
                    st.markdown("Uploadez une photo de la bouche du patient pour une analyse IA complémentaire.")
                    if not ANTHROPIC_API_KEY:
                        st.warning("Configurez `ANTHROPIC_API_KEY` dans `st.secrets` pour activer cette fonctionnalité.")
                    else:
                        uploaded = st.file_uploader("Photo bouche patient", type=["jpg", "jpeg", "png"])
                        if uploaded:
                            img_bytes = uploaded.read()
                            mime = "image/png" if uploaded.name.endswith(".png") else "image/jpeg"
                            col_img, col_res = st.columns([1, 2])
                            with col_img:
                                st.image(img_bytes, caption="Photo patient", use_container_width=True)
                            with col_res:
                                with st.spinner("Analyse IA en cours..."):
                                    result = analyser_photo_bouche(img_bytes, mime)
                                render_photo_analysis(result)

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
                                div_col = next((c for c in ["Diversite (%)", "Diversité (%)"] if c in df_g.columns), None)
                                if div_col:
                                    st.line_chart(df_g[[div_col]].astype(float))

                    st.markdown("---")
                    st.header("Ajouter une Intervention")
                    with st.form("form_ajout"):
                        fa1, fa2, fa3 = st.columns(3)
                        with fa1:
                            nd = st.date_input("Date", date.today())
                            nact = st.selectbox("Intervention", ["Examen Initial", "Contrôle Microbiome", "Détartrage", "Soin Carie", "Surfaçage", "Probiotiques Prescrits", "Autre"])
                        with fa2:
                            ns = st.number_input("S. mutans (%)", 0.0, 10.0, float(s_mutans), step=0.1)
                            np_ = st.number_input("P. gingivalis (%)", 0.0, 5.0, float(p_gingivalis), step=0.1)
                        with fa3:
                            nd2 = st.number_input("Diversité (%)", 0, 100, int(diversite))
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
                            st.success("Sauvegardé.")
                            st.rerun()

                    st.markdown("---")
                    st.header("Rapport PDF Complet")
                    st.markdown("Le rapport inclut désormais les **scores de risque systémique** avec les références scientifiques.")
                    if st.button("Générer le rapport PDF", type="primary"):
                        with st.spinner("Génération..."):
                            pdf = generer_pdf(patient["nom"], r_carieux, r_paro, diversite, patient["historique"], plan, scores_sys)
                        st.download_button(
                            "📥 Télécharger le Rapport Patient Complet (PDF)",
                            data=pdf,
                            file_name=f"OralBiome_{patient['id']}_{patient['nom'].replace(' ','_')}.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )