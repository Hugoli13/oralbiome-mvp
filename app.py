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
# LOGO
# ============================================================
import os as _os

def _load_logo_b64(path: str = "image_19.png") -> str:
    if _os.path.exists(path):
        with open(path, "rb") as f:
            import base64 as _b64
            return _b64.b64encode(f.read()).decode("utf-8")
    return ""

LOGO_B64 = _load_logo_b64()

def logo_img(width: int = 400, style: str = "") -> str:
    if LOGO_B64:
        return f'<img src="data:image/png;base64,{LOGO_B64}" width="{width}" style="display:block;{style}" />'
    return '<span style="font-family:DM Serif Display,serif;font-size:1.4rem;color:#1a3a5c;">🦷 OralBiome</span>'

# ============================================================
# NHANES
# ============================================================
NHANES_PERCENTILES = {
     1:14.2,  2:17.8,  3:20.1,  4:22.0,  5:23.5,
     6:24.8,  7:25.9,  8:27.0,  9:28.0, 10:28.9,
    11:29.7, 12:30.5, 13:31.2, 14:31.9, 15:32.6,
    16:33.2, 17:33.8, 18:34.4, 19:35.0, 20:35.6,
    21:36.1, 22:36.7, 23:37.2, 24:37.7, 25:38.2,
    26:38.7, 27:39.2, 28:39.7, 29:40.1, 30:40.6,
    31:41.0, 32:41.5, 33:41.9, 34:42.3, 35:42.8,
    36:43.2, 37:43.6, 38:44.0, 39:44.4, 40:44.8,
    41:45.2, 42:45.6, 43:46.0, 44:46.4, 45:46.8,
    46:47.2, 47:47.6, 48:48.0, 49:48.4, 50:48.8,
    51:49.2, 52:49.6, 53:50.1, 54:50.5, 55:50.9,
    56:51.3, 57:51.8, 58:52.2, 59:52.7, 60:53.1,
    61:53.6, 62:54.1, 63:54.5, 64:55.0, 65:55.5,
    66:56.0, 67:56.5, 68:57.1, 69:57.6, 70:58.2,
    71:58.8, 72:59.4, 73:60.0, 74:60.6, 75:61.3,
    76:62.0, 77:62.7, 78:63.4, 79:64.2, 80:65.0,
    81:65.8, 82:66.7, 83:67.6, 84:68.5, 85:69.5,
    86:70.5, 87:71.6, 88:72.7, 89:73.9, 90:75.2,
    91:76.5, 92:77.9, 93:79.4, 94:81.0, 95:82.7,
    96:84.6, 97:86.7, 98:89.2, 99:93.1
}

NHANES_BY_AGE = {
    "18-29": {"p25":41.5,"p50":52.1,"p75":63.8,"p85":71.2,"mean":51.8},
    "30-39": {"p25":40.2,"p50":51.0,"p75":62.5,"p85":70.1,"mean":50.6},
    "40-49": {"p25":38.8,"p50":49.4,"p75":61.0,"p85":68.7,"mean":49.1},
    "50-59": {"p25":37.1,"p50":47.6,"p75":59.2,"p85":67.0,"mean":47.4},
    "60-69": {"p25":35.5,"p50":45.8,"p75":57.4,"p85":65.2,"mean":45.6},
    "70+":   {"p25":33.2,"p50":43.5,"p75":55.1,"p85":63.0,"mean":43.3},
}

NHANES_THRESHOLDS = {"excellent":69.5,"bon":61.3,"modere":38.2,"faible":0}

NHANES_CLINICAL = {
    "diabete":      {"mean_sain":51.3,"mean_malade":44.7,"difference":6.6,"p_value":0.0001},
    "hypertension": {"mean_sain":50.8,"mean_malade":46.2,"difference":4.6,"p_value":0.0008},
    "inflammation": {"mean_sain":51.1,"mean_malade":45.9,"difference":5.2,"p_value":0.0003},
    "mortalite":    {"hazard_ratio":0.63,"ci_95":"(0.49–0.82)",
                     "interpretation":"Chaque hausse de diversité réduit le risque de mortalité de 37% (HR=0.63)"},
}

def nhanes_percentile_rank(score: float, age: int = None) -> dict:
    pct_global = 1
    for p in range(99, 0, -1):
        if score >= NHANES_PERCENTILES[p]:
            pct_global = p
            break
    if score >= NHANES_THRESHOLDS["excellent"]:
        niveau, niveau_label, niveau_color = "excellent", "Excellent 🌟", "#16a34a"
    elif score >= NHANES_THRESHOLDS["bon"]:
        niveau, niveau_label, niveau_color = "bon", "Bon 👍", "#2563eb"
    elif score >= NHANES_THRESHOLDS["modere"]:
        niveau, niveau_label, niveau_color = "modere", "Modéré ⚠️", "#d97706"
    else:
        niveau, niveau_label, niveau_color = "faible", "Faible 🔴", "#e11d48"
    benchmark_global = f"Meilleur que **{pct_global}%** de la population générale"
    age_group = pct_age = nhanes_median_age = delta_median = benchmark_age = None
    if age is not None:
        if age < 30:    age_group = "18-29"
        elif age < 40:  age_group = "30-39"
        elif age < 50:  age_group = "40-49"
        elif age < 60:  age_group = "50-59"
        elif age < 70:  age_group = "60-69"
        else:           age_group = "70+"
        ag = NHANES_BY_AGE[age_group]
        nhanes_median_age = ag["p50"]
        delta_median = round(score - nhanes_median_age, 1)
        if score >= ag["p85"]:    pct_age = 85
        elif score >= ag["p75"]:  pct_age = 75
        elif score >= ag["p50"]:  pct_age = 50
        elif score >= ag["p25"]:  pct_age = 25
        else:                     pct_age = 10
        delta_str = f"+{delta_median}" if delta_median >= 0 else str(delta_median)
        benchmark_age = (f"Meilleur que **{pct_age}%** des {age_group} ans "
                         f"({delta_str} pts vs médiane de votre âge)")
    return {
        "percentile_global": pct_global, "percentile_age": pct_age,
        "benchmark_global": benchmark_global, "benchmark_age": benchmark_age,
        "niveau": niveau, "niveau_label": niveau_label, "niveau_color": niveau_color,
        "age_group": age_group, "nhanes_median_age": nhanes_median_age,
        "delta_median": delta_median, "nhanes_n": 8237,
        "source": "NHANES 2009-2012 · Vogtmann et al. Lancet Microbe 2022"
    }

def render_diversity_benchmark(diversite: float, age: int = None, context: str = "patient"):
    bm = nhanes_percentile_rank(diversite, age)
    color = bm["niveau_color"]
    pct = bm["percentile_global"]
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{color}12,{color}06);
         border:1.5px solid {color}40;border-radius:16px;padding:20px 24px;margin:12px 0;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
            <div>
                <div style="font-size:0.75rem;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Score Diversité Microbienne</div>
                <div style="font-family:'DM Serif Display',serif;font-size:2.8rem;color:{color};line-height:1;">
                    {diversite}<span style="font-size:1.2rem;color:#9ca3af;">/100</span>
                </div>
                <span style="background:{color}20;color:{color};font-weight:600;padding:3px 12px;border-radius:20px;font-size:0.85rem;">{bm['niveau_label']}</span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.8rem;color:#6b7280;margin-bottom:2px;">vs population générale</div>
                <div style="font-family:'DM Serif Display',serif;font-size:2rem;color:{color};line-height:1;">Top {100-pct}%</div>
                <div style="font-size:0.78rem;color:#9ca3af;margin-top:4px;">sur {bm['nhanes_n']:,} patients NHANES</div>
            </div>
        </div>
        <div style="margin-top:14px;padding-top:12px;border-top:1px solid {color}20;">
            <div style="font-size:0.9rem;color:#374151;margin-bottom:4px;">🌍 {bm['benchmark_global']}</div>
            {"" if not bm['benchmark_age'] else f'<div style="font-size:0.9rem;color:#374151;">👤 {bm["benchmark_age"]}</div>'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    bar_segs = [(25,"#fee2e2"),(25,"#fef3c7"),(25,"#dbeafe"),(15,"#dcfce7"),(10,"#bbf7d0")]
    bar_html = '<div style="display:flex;border-radius:8px;overflow:hidden;height:12px;margin:8px 0 2px 0;">'
    for w, bg in bar_segs:
        bar_html += f'<div style="flex:{w};background:{bg};border-right:1px solid white;"></div>'
    bar_html += f'</div><div style="position:relative;height:20px;">'
    bar_html += f'<div style="position:absolute;left:{pct}%;transform:translateX(-50%);">'
    bar_html += f'<div style="width:3px;height:12px;background:{color};margin:0 auto;"></div>'
    bar_html += f'<div style="font-size:0.7rem;font-weight:700;color:{color};white-space:nowrap;transform:translateX(-40%);">P{pct} — vous</div>'
    bar_html += "</div></div>"
    st.markdown(bar_html, unsafe_allow_html=True)
    leg_cols = st.columns(5)
    for col, (lbl, c) in zip(leg_cols, [
        ("< P25\nFaible","#e11d48"),("P25–50\nModéré","#d97706"),
        ("P50–75\nBon","#2563eb"),("P75–85\nExcellent","#16a34a"),("> P90\nTop 10%","#15803d")
    ]):
        col.markdown(f"<div style='text-align:center;font-size:0.68rem;color:{c};font-weight:600;line-height:1.3;'>{lbl}</div>", unsafe_allow_html=True)
    if context == "praticien":
        st.markdown("---")
        st.markdown("##### 📊 Corrélations cliniques — NHANES 2009-2012 (n=8 237)")
        st.caption(f"Source : {bm['source']}")
        c1, c2, c3 = st.columns(3)
        for col, (key, label, icon) in zip([c1,c2,c3],[
            ("diabete","Diabète","🩸"),("hypertension","Hypertension","❤️"),("inflammation","Inflammation","🔥")
        ]):
            d = NHANES_CLINICAL[key]
            col.markdown(f"""
            <div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:1.2rem;">{icon}</div>
                <div style="font-weight:600;font-size:0.85rem;margin:4px 0;">{label}</div>
                <div style="font-family:'DM Serif Display',serif;font-size:1.4rem;color:#e11d48;">−{d['difference']} pts</div>
                <div style="font-size:0.72rem;color:#6b7280;">sains: {d['mean_sain']} vs malades: {d['mean_malade']}</div>
                <div style="font-size:0.7rem;color:#16a34a;margin-top:4px;font-weight:600;">p={d['p_value']}</div>
            </div>""", unsafe_allow_html=True)
        mort = NHANES_CLINICAL["mortalite"]
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:1px solid #16a34a40;
             border-radius:10px;padding:12px 16px;margin-top:8px;">
            <b>💚 Mortalité toutes causes</b> — HR={mort['hazard_ratio']} {mort['ci_95']}<br>
            <span style="font-size:0.85rem;color:#374151;">{mort['interpretation']}</span><br>
            <span style="font-size:0.72rem;color:#9ca3af;">Shen et al. J Clin Periodontol 2024 · 7 055 adultes · suivi 9 ans</span>
        </div>""", unsafe_allow_html=True)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display:ital@0;1&display=swap');
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
  .ob-header { background:linear-gradient(135deg,#0a1628 0%,#1a3a5c 60%,#0d2640 100%);border-radius:16px;padding:28px 32px;margin-bottom:24px;border:1px solid rgba(255,255,255,0.08);box-shadow:0 8px 32px rgba(0,0,0,0.3); }
  .ob-header h1 { font-family:'DM Serif Display',serif;color:#fff;margin:0;font-size:2rem; }
  .ob-header p { color:rgba(255,255,255,0.6);margin:4px 0 0 0;font-size:0.9rem; }
  .risk-card { border-radius:12px;padding:20px;margin:8px 0;border:1px solid rgba(0,0,0,0.06);transition:transform 0.2s ease,box-shadow 0.2s ease; }
  .risk-card:hover { transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,0.12); }
  .risk-low  { background:linear-gradient(135deg,#f0fdf4,#dcfce7);border-left:4px solid #16a34a; }
  .risk-med  { background:linear-gradient(135deg,#fffbeb,#fef3c7);border-left:4px solid #d97706; }
  .risk-high { background:linear-gradient(135deg,#fff1f2,#ffe4e6);border-left:4px solid #e11d48; }
  .systemic-card { background:#fff;border-radius:14px;padding:20px 24px;border:1px solid #e5e7eb;margin:10px 0;box-shadow:0 2px 8px rgba(0,0,0,0.05); }
  .systemic-title { font-family:'DM Serif Display',serif;font-size:1.1rem;color:#1a3a5c;margin:0 0 8px 0; }
  .score-ring { display:flex;align-items:center;justify-content:center;width:72px;height:72px;border-radius:50%;font-weight:600;font-size:1.1rem;color:#fff;flex-shrink:0; }
  .score-low  { background:linear-gradient(135deg,#16a34a,#22c55e); }
  .score-med  { background:linear-gradient(135deg,#d97706,#f59e0b); }
  .score-high { background:linear-gradient(135deg,#e11d48,#f43f5e); }
  .finding-badge { display:inline-block;padding:4px 12px;border-radius:20px;font-size:0.78rem;font-weight:500;margin:3px; }
  .finding-alert { background:#fee2e2;color:#991b1b; }
  .finding-warn  { background:#fef3c7;color:#92400e; }
  .finding-ok    { background:#dcfce7;color:#166534; }
  .pill-green { display:inline-block;background:#d1fae5;border-radius:20px;padding:5px 14px;margin:3px;font-size:13px;color:#065f46;font-weight:500; }
  .pill-red   { display:inline-block;background:#fee2e2;border-radius:20px;padding:5px 14px;margin:3px;font-size:13px;color:#991b1b;font-weight:500; }
  .reco-card { padding:14px 18px;border-radius:8px;margin:8px 0; }
  .reco-red    { background:#fff5f5;border-left:4px solid #dc3545; }
  .reco-orange { background:#fff8f0;border-left:4px solid #fd7e14; }
  .reco-green  { background:#f0fff4;border-left:4px solid #28a745; }
  .patient-header { background:linear-gradient(135deg,#1a3a5c,#2563eb);color:white;padding:24px;border-radius:12px;margin-bottom:20px; }
  .kpi-card { background:#fff;border-radius:16px;padding:22px 24px;border:1px solid #e5e7eb;box-shadow:0 2px 12px rgba(0,0,0,0.06);transition:transform 0.2s ease; }
  .kpi-card:hover { transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,0.1); }
  .kpi-num { font-family:'DM Serif Display',serif;font-size:2.4rem;line-height:1; }
  .kpi-lbl { font-size:0.82rem;color:#6b7280;margin-top:4px;font-weight:500;text-transform:uppercase;letter-spacing:0.04em; }
  .kpi-delta { font-size:0.8rem;margin-top:6px;font-weight:600; }
  .kpi-red{color:#e11d48;} .kpi-green{color:#16a34a;} .kpi-blue{color:#2563eb;} .kpi-amber{color:#d97706;}
  .alert-card { background:#fff;border-radius:12px;padding:16px 20px;margin:8px 0;border:1px solid #fee2e2;border-left:5px solid #e11d48;box-shadow:0 2px 8px rgba(225,29,72,0.08);display:flex;align-items:flex-start;gap:14px; }
  .alert-card.warn { border-color:#fef3c7;border-left-color:#d97706;box-shadow:0 2px 8px rgba(217,119,6,0.08); }
  .alert-card.info { border-color:#dbeafe;border-left-color:#2563eb;box-shadow:0 2px 8px rgba(37,99,235,0.08); }
  .alert-icon { font-size:1.5rem;flex-shrink:0;margin-top:2px; }
  .alert-body { flex:1; }
  .alert-title { font-weight:600;font-size:0.95rem;color:#111827;margin:0 0 3px 0; }
  .alert-desc  { font-size:0.85rem;color:#6b7280;margin:0; }
  .alert-meta  { font-size:0.75rem;color:#9ca3af;margin-top:5px; }
  .progress-bar-wrap { background:#f1f5f9;border-radius:8px;height:10px;overflow:hidden;margin:6px 0; }
  .progress-bar-fill { height:100%;border-radius:8px;transition:width 0.4s ease; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SCORES SYSTÉMIQUES
# ============================================================
SYSTEMIC_CORRELATIONS = {
    "cardiovasculaire": {
        "icon":"❤️","label":"Risque Cardiovasculaire",
        "description":"P. gingivalis et T. forsythia libèrent des endotoxines qui favorisent l'athérosclérose et les plaques artérielles.",
        "references":"Herzberg & Meyer, 1996 · Mehta et al., 2013 · AHA Scientific Statement 2012",
        "weight_gingivalis":0.45,"weight_mutans":0.10,"weight_diversity":0.30,"weight_inflammation":0.15,
        "thresholds":{"low":25,"high":55},
        "actions_high":["Consultation cardiologique recommandée","Bilan CRP ultrasensible","Traitement parodontal en priorité — réduit le risque CV de 20%","Alimentation anti-inflammatoire (omega-3, polyphénols)"],
        "actions_low":["Maintenir une hygiène parodontale rigoureuse","Contrôle microbiome oral tous les 6 mois"]
    },
    "diabete": {
        "icon":"🩸","label":"Risque Diabète / Résistance Insuline",
        "description":"La dysbiose orale entretient une inflammation chronique de bas grade qui dégrade la sensibilité à l'insuline.",
        "references":"Taylor et al., 2013 · Preshaw et al., 2012 · Systemic Reviews Lancet 2020",
        "weight_gingivalis":0.35,"weight_mutans":0.20,"weight_diversity":0.35,"weight_inflammation":0.10,
        "thresholds":{"low":25,"high":55},
        "actions_high":["Bilan glycémie à jeun et HbA1c recommandé","Réduction drastique des sucres rapides","Traitement parodontal prouvé : réduit HbA1c de 0.4%","Exercice physique 150 min/semaine"],
        "actions_low":["Limiter les sucres raffinés","Contrôle glycémie si antécédents familiaux"]
    },
    "alzheimer": {
        "icon":"🧠","label":"Risque Neurodégénératif (Alzheimer)",
        "description":"P. gingivalis a été retrouvée dans le cerveau de patients Alzheimer. Ses gingipaines favorisent les plaques amyloïdes.",
        "references":"Dominy et al., Science Advances 2019 · Ilievski et al., 2018 · Olsen & Singhrao, 2015",
        "weight_gingivalis":0.60,"weight_mutans":0.05,"weight_diversity":0.25,"weight_inflammation":0.10,
        "thresholds":{"low":20,"high":50},
        "actions_high":["Élimination de P. gingivalis — priorité absolue","Supplémentation en omega-3 DHA (1g/jour minimum)","Activité physique aérobie","Suivi neurologique si > 60 ans"],
        "actions_low":["Maintenir un microbiome diversifié","Alimentation méditerranéenne riche en polyphénols"]
    },
    "colon": {
        "icon":"🦠","label":"Risque Colorectal",
        "description":"Fusobacterium nucleatum est retrouvé en forte concentration dans les tumeurs colorectales.",
        "references":"Castellarin et al., Genome Research 2012 · Rubinstein et al., Cell Host 2013",
        "weight_gingivalis":0.25,"weight_mutans":0.10,"weight_diversity":0.50,"weight_inflammation":0.15,
        "thresholds":{"low":20,"high":45},
        "actions_high":["Coloscopie de dépistage si > 45 ans","Augmenter les fibres prébiotiques (30g/jour minimum)","Réduire la viande rouge transformée","Probiotiques intestinaux"],
        "actions_low":["Alimentation riche en fibres et légumes fermentés","Dépistage de routine selon l'âge"]
    },
    "respiratoire": {
        "icon":"🫁","label":"Risque Respiratoire / Pneumonie",
        "description":"Les bactéries orales aspirées colonisent les voies respiratoires basses. Risque ×4 en dysbiose sévère.",
        "references":"Scannapieco et al., 2003 · ADA Journal 2021 · Azarpazhooh & Leake, 2006",
        "weight_gingivalis":0.30,"weight_mutans":0.15,"weight_diversity":0.40,"weight_inflammation":0.15,
        "thresholds":{"low":25,"high":50},
        "actions_high":["Hygiène orale renforcée","Brossage de la langue matin et soir (réduit charge bactérienne de 70%)","Consultation pneumologique si toux chronique"],
        "actions_low":["Hygiène bucco-dentaire régulière","Brossage de la langue quotidien"]
    }
}

def calculer_score_systemique(s_mutans, p_gingivalis, diversite):
    score_gingivalis = min(100, (p_gingivalis / 2.0) * 100)
    score_mutans = min(100, (s_mutans / 8.0) * 100)
    score_diversity_risk = max(0, 100 - diversite)
    score_inflammation = min(100, (score_gingivalis * 0.6 + score_diversity_risk * 0.4))
    results = {}
    for key, corr in SYSTEMIC_CORRELATIONS.items():
        raw_score = (
            corr["weight_gingivalis"] * score_gingivalis +
            corr["weight_mutans"] * score_mutans +
            corr["weight_diversity"] * score_diversity_risk +
            corr["weight_inflammation"] * score_inflammation
        )
        score = round(min(100, max(0, raw_score)))
        level = "low" if score < corr["thresholds"]["low"] else \
                "high" if score > corr["thresholds"]["high"] else "med"
        results[key] = {**corr,"score":score,"level":level,
                        "actions":corr["actions_high"] if level=="high" else corr["actions_low"]}
    return dict(sorted(results.items(), key=lambda x: -x[1]["score"]))

# ============================================================
# ANALYSE PHOTO
# ============================================================
def analyser_photo_bouche(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
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
  "findings": [{"zone":"","observation":"","severite":"normal|attention|alerte","detail":""}],
  "score_global": 0-100,
  "profil_visuel": "Bouche saine|Inflammation légère|Inflammation modérée|Dysbiose visible|Urgence clinique",
  "recommandations_immediates": ["action 1", "action 2"],
  "disclaimer": "Cette analyse est une aide à la décision pour professionnels. Ne constitue pas un diagnostic.",
  "confiance": "élevée|modérée|faible"
}"""
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1500,
        "system": system_prompt,
        "messages": [{"role":"user","content":[
            {"type":"image","source":{"type":"base64","media_type":mime_type,"data":b64_image}},
            {"type":"text","text":"Analyse cette photo de cavité buccale. Identifie tous les signes visuels observables."}
        ]}]
    }
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"},
            json=payload, timeout=30
        )
        response.raise_for_status()
        raw = response.json()["content"][0]["text"].strip()
        raw = raw.replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except requests.exceptions.Timeout:
        return {"error":"Délai d'attente dépassé."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Erreur réseau : {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"Réponse invalide : {str(e)}"}

def render_photo_analysis(result: dict):
    if "error" in result:
        st.error(f"⚠️ {result['error']}")
        return
    score = result.get("score_global", 50)
    profil = result.get("profil_visuel", "N/A")
    confiance = result.get("confiance", "modérée")
    qualite = result.get("qualite_image", "N/A")
    col_score, col_info = st.columns([1, 3])
    with col_score:
        color = "#16a34a" if score >= 70 else "#d97706" if score >= 45 else "#e11d48"
        st.markdown(f"""
        <div style="text-align:center;background:linear-gradient(135deg,{color}22,{color}11);
             border:2px solid {color};border-radius:16px;padding:24px;">
            <div style="font-family:'DM Serif Display',serif;font-size:3rem;color:{color};line-height:1;">{score}</div>
            <div style="font-size:0.75rem;color:#6b7280;margin-top:4px;">Score santé visuelle</div>
            <div style="font-size:0.8rem;font-weight:600;color:{color};margin-top:8px;">{profil}</div>
        </div>""", unsafe_allow_html=True)
    with col_info:
        st.markdown(f"**Qualité image :** `{qualite}` · **Confiance analyse :** `{confiance}`")
        zones = result.get("zones_analysees", [])
        if zones:
            st.markdown(f"**Zones analysées :** {' · '.join(zones)}")
        st.markdown("**Findings détectés :**")
        for f in result.get("findings", []):
            sev = f.get("severite","normal")
            css = "finding-alert" if sev=="alerte" else "finding-warn" if sev=="attention" else "finding-ok"
            icon = "🔴" if sev=="alerte" else "🟡" if sev=="attention" else "🟢"
            st.markdown(f"<span class='finding-badge {css}'>{icon} {f.get('zone','')} — {f.get('observation','')}</span>", unsafe_allow_html=True)
    st.markdown("---")
    findings = result.get("findings", [])
    if findings:
        st.markdown("#### 🔬 Analyse détaillée par zone")
        cols = st.columns(min(len(findings), 3))
        for i, f in enumerate(findings):
            sev = f.get("severite","normal")
            with cols[i % 3]:
                css = "risk-high" if sev=="alerte" else "risk-med" if sev=="attention" else "risk-low"
                icon = "🔴" if sev=="alerte" else "🟡" if sev=="attention" else "🟢"
                st.markdown(f"""
                <div class='risk-card {css}'>
                    <div style="font-weight:600;font-size:0.9rem;">{icon} {f.get('zone','N/A')}</div>
                    <div style="font-size:0.85rem;margin-top:4px;color:#374151;">{f.get('observation','')}</div>
                    <div style="font-size:0.78rem;margin-top:6px;color:#6b7280;font-style:italic;">{f.get('detail','')}</div>
                </div>""", unsafe_allow_html=True)
    st.markdown("---")
    recos = result.get("recommandations_immediates", [])
    if recos:
        st.markdown("#### ✅ Actions immédiates recommandées")
        for r in recos:
            st.markdown(f"- {r}")
    disclaimer = result.get("disclaimer","")
    if disclaimer:
        st.caption(f"⚕️ *{disclaimer}*")

# ============================================================
# ANAMNÈSE — CRUD session_state
# ============================================================
def get_anamnes(patient_nom):
    return st.session_state.anamnes.get(patient_nom, {})

def save_anamnes(patient_nom, data):
    from datetime import datetime
    data["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.anamnes[patient_nom] = data

# ============================================================
# RECOMMANDATIONS
# ============================================================
def generer_recommandations(s_mutans, p_gingivalis, diversite):
    plan = {"priorites":[],"aliments_favoriser":[],"aliments_eviter":[],"probiotiques":[],"hygiene":[],"suivi_semaines":24,"profil_label":"","profil_description":""}
    nb = sum([s_mutans>3.0, p_gingivalis>0.5, diversite<50])
    if nb==0:
        plan["profil_label"]="🟢 Microbiome Équilibré"; plan["profil_description"]="Votre flore buccale est protectrice. Continuez vos bonnes habitudes."; plan["suivi_semaines"]=24
    elif nb==1:
        plan["profil_label"]="🟡 Déséquilibre Modéré"; plan["profil_description"]="Un déséquilibre est détecté. Des ajustements ciblés corrigeront la situation en 2-3 mois."; plan["suivi_semaines"]=12
    else:
        plan["profil_label"]="🔴 Dysbiose Active"; plan["profil_description"]="Plusieurs marqueurs sont en alerte. Un plan d'action renforcé est nécessaire."; plan["suivi_semaines"]=8
    if s_mutans>3.0:
        plan["priorites"].append({"icone":"🦠","titre":"Réduire les bactéries acidogènes (S. mutans)","urgence":"Elevee" if s_mutans>6.0 else "Moderee","explication":f"Taux de S. mutans : {s_mutans}% (normal < 3%).","actions":["Brossage 2 min minimum après chaque repas sucré","Fil dentaire quotidien le soir","Bain de bouche fluoré 1x/jour sans alcool","Éviter de grignoter entre les repas"]})
        plan["aliments_eviter"] += ["Bonbons et sucreries","Sodas et boissons sucrées","Pain blanc et viennoiseries","Jus de fruits (fructose élevé)"]
        plan["aliments_favoriser"] += ["Fromage à pâte dure (Gruyère, Comté)","Yaourt nature sans sucre","Légumes crus et croquants","Thé vert sans sucre","Noix et amandes"]
        plan["probiotiques"].append({"nom":"Lactobacillus reuteri (souche DSM 17938)","forme":"Comprimés à sucer 1x/jour après brossage du soir","duree":"3 mois minimum","benefice":"Inhibe S. mutans et réduit la plaque acide","marques":"BioGaia Prodentis, Sunstar GUM PerioBalance"})
    if p_gingivalis>0.5:
        plan["priorites"].append({"icone":"🩸","titre":"Éliminer les pathogènes parodontaux (complexe rouge)","urgence":"Elevee" if p_gingivalis>1.5 else "Moderee","explication":f"Taux de P. gingivalis : {p_gingivalis}% (normal < 0.5%).","actions":["Nettoyage interdentaire quotidien — PRIORITÉ N°1","Brossage de la langue matin et soir","Consultation parodontale si gencives qui saignent","Arrêt du tabac si applicable (multiplie ×3 le risque)"]})
        plan["aliments_eviter"] += ["Tabac sous toutes formes","Alcool en excès","Sucres raffinés","Aliments ultra-transformés"]
        plan["aliments_favoriser"] += ["Poissons gras 2-3×/semaine (oméga-3)","Myrtilles et framboises (polyphénols)","Légumes verts feuillus (nitrates)","Huile d'olive extra vierge","Ail et oignon crus (allicine)"]
        plan["probiotiques"].append({"nom":"Lactobacillus reuteri + Lactobacillus salivarius","forme":"Pastilles à dissoudre en bouche 2×/jour","duree":"3 à 6 mois","benefice":"Réduit P. gingivalis et le saignement gingival","marques":"Sunstar GUM PerioBalance, Blis K12"})
    if diversite<50:
        plan["priorites"].append({"icone":"🌱","titre":"Restaurer la diversité microbienne orale","urgence":"Moderee" if diversite>30 else "Elevee","explication":f"Score de diversité : {diversite}/100 (optimal > 65).","actions":["Diversifier : objectif 30 plantes différentes par semaine","Réduire les bains de bouche antiseptiques quotidiens","Augmenter les fibres prébiotiques (poireau, ail, oignon)","Boire 1.5L d'eau par jour minimum"]})
        plan["aliments_favoriser"] += ["Légumes racines variés (fibres prébiotiques)","Pomme avec la peau (pectine)","Légumineuses (lentilles, pois chiches)","Légumes fermentés (choucroute, kimchi)","Kombucha sans sucre ajouté"]
        plan["aliments_eviter"] += ["Bains de bouche antiseptiques quotidiens","Antibiotiques inutiles","Fast-food régulier"]
        plan["probiotiques"].append({"nom":"Streptococcus salivarius K12 + M18","forme":"Pastilles à sucer le soir après brossage","duree":"2 à 3 mois puis entretien trimestriel","benefice":"Recolonise la flore avec des espèces protectrices","marques":"BLIS K12, Nasal Guard Throat Guard"})
    if nb==0:
        plan["priorites"].append({"icone":"✅","titre":"Maintenir l'équilibre de votre microbiome","urgence":"Routine","explication":"Votre microbiome oral est en bonne santé.","actions":["Brossage 2×/jour avec brosse souple","Fil dentaire 1×/jour","Alimentation variée riche en fibres","Contrôle dans 6 mois"]})
        plan["aliments_favoriser"] += ["Alimentation méditerranéenne variée","Eau comme boisson principale","Produits laitiers fermentés (yaourt, kéfir)"]
    plan["aliments_favoriser"] = list(dict.fromkeys(plan["aliments_favoriser"]))
    plan["aliments_eviter"] = list(dict.fromkeys(plan["aliments_eviter"]))
    return plan

# ============================================================
# PDF
# ============================================================
def generer_pdf(patient_nom, r_carieux, r_paro, diversite, historique_df, plan, scores_systemiques=None):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
        BLUE = colors.HexColor('#1a3a5c'); LIGHT_BLUE = colors.HexColor('#dbeafe'); GRAY_BG = colors.HexColor('#f9fafb')
        title_style = ParagraphStyle('Title', fontSize=18, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=4)
        sub_style = ParagraphStyle('Sub', fontSize=10, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica', spaceAfter=6)
        h1_style = ParagraphStyle('H1', fontSize=13, textColor=BLUE, fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=4)
        h2_style = ParagraphStyle('H2', fontSize=11, textColor=BLUE, fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=3)
        body_style = ParagraphStyle('Body', fontSize=10, fontName='Helvetica', spaceAfter=3, leading=14)
        italic_style = ParagraphStyle('Italic', fontSize=9, fontName='Helvetica-Oblique', textColor=colors.HexColor('#555555'), spaceAfter=4)
        small_style = ParagraphStyle('Small', fontSize=8, fontName='Helvetica', textColor=colors.grey, alignment=TA_CENTER)
        elems = []
        header_table = Table([[Paragraph("OralBiome - Rapport Patient Complet", title_style)],[Paragraph("Microbiome Oral Predictif + Risques Systemiques | Rapport Personnalise", sub_style)]], colWidths=[180*mm])
        header_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),BLUE),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        elems.append(header_table); elems.append(Spacer(1,5*mm))
        info_table = Table([[Paragraph(f"<b>Patient :</b> {patient_nom}", body_style),Paragraph(f"<b>Date :</b> {date.today().strftime('%d/%m/%Y')}", body_style)]], colWidths=[90*mm,90*mm])
        info_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT_BLUE),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),8)]))
        elems.append(info_table); elems.append(Spacer(1,6*mm))
        elems.append(Paragraph("Resultats de l'Analyse Microbiome", h1_style))
        elems.append(HRFlowable(width="100%",thickness=1,color=LIGHT_BLUE))
        res_table = Table([
            [Paragraph("<b>Risque Carieux</b>",body_style),Paragraph(f"<b>{r_carieux}</b>",body_style)],
            [Paragraph("<b>Risque Parodontal</b>",body_style),Paragraph(f"<b>{r_paro}</b>",body_style)],
            [Paragraph("<b>Score de Diversite</b>",body_style),Paragraph(f"<b>{diversite}/100</b> (optimal > 65)",body_style)],
        ], colWidths=[90*mm,90*mm])
        res_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),GRAY_BG),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),8)]))
        elems.append(res_table); elems.append(Spacer(1,6*mm))
        if scores_systemiques:
            elems.append(Paragraph("Scores de Risque Systemique", h1_style))
            elems.append(HRFlowable(width="100%",thickness=1,color=LIGHT_BLUE))
            elems.append(Paragraph("Ces scores sont calcules sur la base de correlations publiees dans la litterature scientifique.", italic_style))
            elems.append(Spacer(1,3*mm))
            sys_rows = [["Pathologie","Score /100","Niveau","Action principale"]]
            for key, data in scores_systemiques.items():
                level_label = "Eleve" if data["level"]=="high" else "Modere" if data["level"]=="med" else "Faible"
                action = data["actions"][0] if data["actions"] else "-"
                sys_rows.append([Paragraph(f"{data['icon']} {data['label']}",body_style),Paragraph(f"<b>{data['score']}</b>",body_style),Paragraph(level_label,body_style),Paragraph(action[:80]+"..." if len(action)>80 else action,body_style)])
            sys_table = Table(sys_rows, colWidths=[55*mm,22*mm,22*mm,81*mm])
            sys_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('ROWBACKGROUNDS',(0,1),(-1,-1),[GRAY_BG,colors.white]),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),6),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#e5e7eb'))]))
            elems.append(sys_table); elems.append(Spacer(1,6*mm))
        if plan["priorites"]:
            elems.append(Paragraph("Plan d'Action - Priorites", h1_style))
            elems.append(HRFlowable(width="100%",thickness=1,color=LIGHT_BLUE))
            for i, p in enumerate(plan["priorites"]):
                badge = "URGENCE ELEVEE" if p["urgence"]=="Elevee" else "MODEREE" if p["urgence"]=="Moderee" else "ROUTINE"
                elems.append(Paragraph(f"Priorite {i+1} — {p['titre']} [{badge}]", h2_style))
                for action in p["actions"]: elems.append(Paragraph(f"• {action}", body_style))
                elems.append(Spacer(1,3*mm))
        elems.append(Paragraph("Plan Nutritionnel", h1_style))
        elems.append(HRFlowable(width="100%",thickness=1,color=LIGHT_BLUE))
        if plan["aliments_favoriser"] or plan["aliments_eviter"]:
            max_items = max(len(plan["aliments_favoriser"]),len(plan["aliments_eviter"]))
            nutr_rows = []
            for i in range(max_items):
                fav = plan["aliments_favoriser"][i] if i<len(plan["aliments_favoriser"]) else ""
                evi = plan["aliments_eviter"][i] if i<len(plan["aliments_eviter"]) else ""
                nutr_rows.append([Paragraph(f"+ {fav}",body_style),Paragraph(f"- {evi}",body_style)])
            nutr_table = Table(nutr_rows, colWidths=[90*mm,90*mm])
            nutr_table.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),colors.HexColor('#f0fdf4')),('BACKGROUND',(1,0),(1,-1),colors.HexColor('#fff1f2')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),8)]))
            elems.append(nutr_table)
        elems.append(Spacer(1,8*mm))
        footer_table = Table([[Paragraph("Ce rapport est fourni a titre preventif et informatif. Ne constitue pas un diagnostic medical.", small_style)],[Paragraph("OralBiome - Microbiome Oral Predictif | contact@oralbiome.com", small_style)]], colWidths=[180*mm])
        footer_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT_BLUE),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        elems.append(footer_table)
        doc.build(elems)
        return buffer.getvalue()
    except ImportError:
        return b"Installez reportlab : pip install reportlab"

# ============================================================
# ALERTES & DASHBOARD
# ============================================================
from datetime import datetime, timedelta

def calculer_alertes(patients: dict) -> list:
    alertes = []
    today = date.today()
    for nom, p in patients.items():
        s_mutans = p["s_mutans"]; p_gingivalis = p["p_gingivalis"]; diversite = p["diversite"]; hist = p["historique"]
        if p_gingivalis > 1.5:
            alertes.append({"type":"urgence","patient":nom,"id":p["id"],"titre":f"P. gingivalis critique ({p_gingivalis}%)","desc":"Risque parodontal sévère et systémique élevé.","priorite":1,"icone":"🚨","action":"Consultation parodontale urgente"})
        elif s_mutans > 6.0:
            alertes.append({"type":"urgence","patient":nom,"id":p["id"],"titre":f"S. mutans critique ({s_mutans}%)","desc":"Caries actives probables — intervention immédiate.","priorite":1,"icone":"🚨","action":"Bilan carie et soin urgents"})
        if not hist.empty:
            try:
                derniere_date_str = hist.iloc[-1]["Date"]
                derniere_date = datetime.strptime(derniere_date_str, "%d/%m/%Y").date()
                en_alerte = s_mutans>3.0 or p_gingivalis>0.5 or diversite<50
                delai_semaines = 8 if en_alerte and (p_gingivalis>1.5 or s_mutans>6.0) else 12 if en_alerte else 24
                date_prochain = derniere_date + timedelta(days=delai_semaines*7)
                jours_restants = (date_prochain - today).days
                if jours_restants < 0:
                    alertes.append({"type":"urgence","patient":nom,"id":p["id"],"titre":f"Contrôle en retard de {abs(jours_restants)} jours","desc":f"Dernier examen le {derniere_date_str}.","priorite":2,"icone":"⏰","action":"Planifier rendez-vous"})
                elif jours_restants <= 14:
                    alertes.append({"type":"warn","patient":nom,"id":p["id"],"titre":f"Contrôle dans {jours_restants} jours","desc":f"Prochain examen recommandé le {date_prochain.strftime('%d/%m/%Y')}.","priorite":3,"icone":"📅","action":"Envoyer rappel au patient"})
            except Exception:
                pass
        if len(hist) >= 2:
            try:
                avant = hist.iloc[-2]; apres = hist.iloc[-1]
                dg_paro = float(apres["P. gingiv. (%)"]) - float(avant["P. gingiv. (%)"])
                dg_mutans = float(apres["S. mutans (%)"]) - float(avant["S. mutans (%)"])
                if dg_paro > 0.3:
                    alertes.append({"type":"warn","patient":nom,"id":p["id"],"titre":f"Dégradation parodontale (+{dg_paro:.1f}%)","desc":"Augmentation significative de P. gingivalis.","priorite":2,"icone":"📈","action":"Adapter le protocole de traitement"})
                if dg_mutans > 1.0:
                    alertes.append({"type":"warn","patient":nom,"id":p["id"],"titre":f"Dégradation cariogène (+{dg_mutans:.1f}%)","desc":"Augmentation de S. mutans — revoir hygiène et alimentation.","priorite":3,"icone":"📈","action":"Revoir le plan nutritionnel"})
            except Exception:
                pass
        if hist.empty:
            alertes.append({"type":"info","patient":nom,"id":p["id"],"titre":"Aucune analyse enregistrée","desc":"Ce patient n'a pas encore d'analyse microbiome.","priorite":4,"icone":"📋","action":"Planifier un examen initial"})
    return sorted(alertes, key=lambda x: x["priorite"])

def calculer_stats_cabinet(patients: dict) -> dict:
    total = len(patients)
    if total == 0: return {}
    alertes_count = sum(1 for p in patients.values() if p["s_mutans"]>3.0 or p["p_gingivalis"]>0.5 or p["diversite"]<50)
    avg_mutans    = sum(p["s_mutans"] for p in patients.values()) / total
    avg_paro      = sum(p["p_gingivalis"] for p in patients.values()) / total
    avg_diversite = sum(p["diversite"] for p in patients.values()) / total
    risque_cardio_eleve = sum(1 for p in patients.values() if calculer_score_systemique(p["s_mutans"],p["p_gingivalis"],p["diversite"])["cardiovasculaire"]["level"]=="high")
    risque_alz_eleve    = sum(1 for p in patients.values() if calculer_score_systemique(p["s_mutans"],p["p_gingivalis"],p["diversite"])["alzheimer"]["level"]=="high")
    total_visites = sum(len(p["historique"]) for p in patients.values())
    return {"total":total,"alertes":alertes_count,"stables":total-alertes_count,"pct_alerte":round(alertes_count/total*100),
            "avg_mutans":round(avg_mutans,2),"avg_paro":round(avg_paro,2),"avg_diversite":round(avg_diversite,1),
            "risque_cardio_eleve":risque_cardio_eleve,"risque_alz_eleve":risque_alz_eleve,"total_visites":total_visites}

def render_dashboard(patients: dict):
    stats = calculer_stats_cabinet(patients)
    alertes = calculer_alertes(patients)
    logo_h = logo_img(width=140, style="margin-bottom:8px;filter:brightness(0) invert(1);opacity:0.85;")
    st.markdown(f"""<div class="ob-header">{logo_h}<h1>📊 Dashboard Cabinet</h1><p>Vue analytique en temps réel · Alertes · KPIs · Tendances</p></div>""", unsafe_allow_html=True)
    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: st.markdown(f'<div class="kpi-card"><div class="kpi-num kpi-blue">{stats["total"]}</div><div class="kpi-lbl">Patients Total</div><div class="kpi-delta kpi-blue">📂 {stats["total_visites"]} visites</div></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="kpi-card"><div class="kpi-num kpi-red">{stats["alertes"]}</div><div class="kpi-lbl">En Alerte</div><div class="kpi-delta kpi-red">⚠️ {stats["pct_alerte"]}% du cabinet</div></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="kpi-card"><div class="kpi-num kpi-green">{stats["stables"]}</div><div class="kpi-lbl">Stables</div><div class="kpi-delta kpi-green">✅ {100-stats["pct_alerte"]}% du cabinet</div></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="kpi-card"><div class="kpi-num kpi-amber">{stats["risque_cardio_eleve"]}</div><div class="kpi-lbl">Risque Cardio Élevé</div><div class="kpi-delta kpi-amber">❤️ Suivi systémique requis</div></div>', unsafe_allow_html=True)
    with k5: st.markdown(f'<div class="kpi-card"><div class="kpi-num kpi-amber">{stats["risque_alz_eleve"]}</div><div class="kpi-lbl">Risque Neuro Élevé</div><div class="kpi-delta kpi-amber">🧠 P. gingivalis critique</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🧬 Moyennes Microbiome du Cabinet")
    col_m1, col_m2, col_m3 = st.columns(3)
    def bar(val, max_val, color):
        pct = min(100, val/max_val*100)
        return f'<div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:{pct:.0f}%;background:{color};"></div></div>'
    with col_m1:
        color = "#e11d48" if stats["avg_mutans"]>3 else "#16a34a"
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.8rem;color:#6b7280;font-weight:600;">S. MUTANS MOYEN</div><div class="kpi-num" style="color:{color};">{stats["avg_mutans"]}%</div><div style="font-size:0.75rem;color:#9ca3af;">Normal &lt; 3%</div>{bar(stats["avg_mutans"],8,color)}</div>', unsafe_allow_html=True)
    with col_m2:
        color = "#e11d48" if stats["avg_paro"]>0.5 else "#16a34a"
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.8rem;color:#6b7280;font-weight:600;">P. GINGIVALIS MOYEN</div><div class="kpi-num" style="color:{color};">{stats["avg_paro"]}%</div><div style="font-size:0.75rem;color:#9ca3af;">Normal &lt; 0.5%</div>{bar(stats["avg_paro"],2,color)}</div>', unsafe_allow_html=True)
    with col_m3:
        color = "#16a34a" if stats["avg_diversite"]>=65 else "#d97706" if stats["avg_diversite"]>=50 else "#e11d48"
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.8rem;color:#6b7280;font-weight:600;">DIVERSITÉ MOYENNE</div><div class="kpi-num" style="color:{color};">{stats["avg_diversite"]}/100</div><div style="font-size:0.75rem;color:#9ca3af;">Optimal &gt; 65</div>{bar(stats["avg_diversite"],100,color)}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col_alerts, col_patients = st.columns([1, 2])
    with col_alerts:
        st.markdown(f"#### 🔔 Alertes Actives `{len(alertes)}`")
        if not alertes:
            st.success("✅ Aucune alerte active — tous les patients sont dans les paramètres.")
        else:
            for a in alertes[:8]:
                css = "alert-card" if a["type"]=="urgence" else "alert-card warn" if a["type"]=="warn" else "alert-card info"
                st.markdown(f'<div class="{css}"><div class="alert-icon">{a["icone"]}</div><div class="alert-body"><div class="alert-title">{a["patient"]} — {a["titre"]}</div><div class="alert-desc">{a["desc"]}</div><div class="alert-meta">👉 {a["action"]}</div></div></div>', unsafe_allow_html=True)
    with col_patients:
        st.markdown("#### 👥 État du Cabinet")
        rows = []
        for nom, p in patients.items():
            ea = p["s_mutans"]>3.0 or p["p_gingivalis"]>0.5 or p["diversite"]<50
            sys_scores = calculer_score_systemique(p["s_mutans"],p["p_gingivalis"],p["diversite"])
            top_sys = max(sys_scores.items(), key=lambda x: x[1]["score"])
            nb_alertes_p = sum(1 for a in alertes if a["patient"]==nom)
            rows.append({"Nom":nom,"Statut":"🔴 Alerte" if ea else "🟢 Stable","S. mutans":f"{p['s_mutans']}%","P. gingivalis":f"{p['p_gingivalis']}%","Diversité":f"{p['diversite']}/100","Top Risque":f"{top_sys[1]['icon']} {top_sys[1]['score']}/100","Alertes":nb_alertes_p if nb_alertes_p else "—"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.markdown("#### 📈 Tendance Diversité Microbienne")
        chart_data = {}
        for nom, p in patients.items():
            hist = p["historique"]
            if len(hist) >= 2:
                div_col = next((c for c in ["Diversite (%)","Diversité (%)"] if c in hist.columns), None)
                if div_col: chart_data[nom] = hist[div_col].astype(float).tolist()
        if chart_data:
            max_len = max(len(v) for v in chart_data.values())
            st.line_chart(pd.DataFrame({k: v+[None]*(max_len-len(v)) for k,v in chart_data.items()}))
        else:
            st.caption("Pas assez d'historique pour afficher les tendances.")
    st.markdown("---")
    st.markdown(f"#### 🗂️ Toutes les Alertes ({len(alertes)})")
    if alertes:
        filtre_type = st.selectbox("Filtrer par type", ["Toutes","🚨 Urgences","⚠️ Avertissements","ℹ️ Infos"], label_visibility="collapsed")
        filtre_map = {"Toutes":None,"🚨 Urgences":"urgence","⚠️ Avertissements":"warn","ℹ️ Infos":"info"}
        alertes_filtrees = [a for a in alertes if filtre_map[filtre_type] is None or a["type"]==filtre_map[filtre_type]]
        for a in alertes_filtrees:
            css = "alert-card" if a["type"]=="urgence" else "alert-card warn" if a["type"]=="warn" else "alert-card info"
            col_a, col_btn = st.columns([5,1])
            with col_a:
                st.markdown(f'<div class="{css}"><div class="alert-icon">{a["icone"]}</div><div class="alert-body"><div class="alert-title">{a["id"]} · {a["patient"]} — {a["titre"]}</div><div class="alert-desc">{a["desc"]}</div><div class="alert-meta">👉 {a["action"]}</div></div></div>', unsafe_allow_html=True)
            with col_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Ouvrir →", key=f"alerte_btn_{a['patient']}_{a['titre'][:10]}"):
                    st.session_state.patient_sel = a["patient"]; st.session_state.vue = "dossier"; st.rerun()
    else:
        st.success("✅ Aucune alerte active.")

# ============================================================
# DONNÉES INITIALES
# ============================================================
def donnees_initiales():
    patients = {}
    df1 = pd.DataFrame({"Date":["12/10/2023","08/04/2026"],"Acte / Test":["Examen Initial","Controle"],"S. mutans (%)":[4.2,4.2],"P. gingiv. (%)":[0.8,0.3],"Diversite (%)":[45,75],"Status":["Alerte","Alerte"]})
    patients["Jean Dupont"] = {"id":"P001","nom":"Jean Dupont","age":42,"email":"jean.dupont@email.com","telephone":"+32 472 123 456","date_naissance":"15/03/1982","historique":df1,"s_mutans":4.2,"p_gingivalis":0.3,"diversite":75,"code_patient":"OB-P001"}
    df2 = pd.DataFrame({"Date":["05/01/2024"],"Acte / Test":["Examen Initial"],"S. mutans (%)":[1.2],"P. gingiv. (%)":[0.1],"Diversite (%)":[82],"Status":["Stable"]})
    patients["Marie Martin"] = {"id":"P002","nom":"Marie Martin","age":35,"email":"marie.martin@email.com","telephone":"+32 478 654 321","date_naissance":"22/07/1989","historique":df2,"s_mutans":1.2,"p_gingivalis":0.1,"diversite":82,"code_patient":"OB-P002"}
    df3 = pd.DataFrame({"Date":["18/02/2025"],"Acte / Test":["Examen Initial"],"S. mutans (%)":[6.5],"P. gingiv. (%)":[1.8],"Diversite (%)":[38],"Status":["Alerte"]})
    patients["Pierre Bernard"] = {"id":"P003","nom":"Pierre Bernard","age":58,"email":"pierre.bernard@email.com","telephone":"+32 495 789 012","date_naissance":"03/11/1966","historique":df3,"s_mutans":6.5,"p_gingivalis":1.8,"diversite":38,"code_patient":"OB-P003"}
    return patients

# ============================================================
# INIT SESSION
# ============================================================
for key, val in [
    ("mode","choix"),("connecte",False),("patient_sel","Jean Dupont"),
    ("vue","dashboard"),("patient_connecte",None)
]:
    if key not in st.session_state:
        st.session_state[key] = val

if "patients" not in st.session_state:
    st.session_state.patients = donnees_initiales()

if "anamnes" not in st.session_state:
    st.session_state.anamnes = {}

if "onboarding_done" not in st.session_state:
    st.session_state.onboarding_done = False

if "onboarding_step" not in st.session_state:
    st.session_state.onboarding_step = 1

if "rgpd_accepted" not in st.session_state:
    st.session_state.rgpd_accepted = False
# ============================================================
# ÉCRAN DE CHOIX
# ============================================================
def render_onboarding():
 def render_rgpd_banner():
    _, col_m, _ = st.columns([1, 3, 1])
    with col_m:
        st.markdown("""
        <div style="background:white;border:2px solid #1a3a5c;border-radius:16px;
                    padding:28px 32px;margin:40px auto;box-shadow:0 8px 32px rgba(0,0,0,0.12);">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                <span style="font-size:2rem;">🔒</span>
                <div>
                    <div style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:#1a3a5c;font-weight:600;">
                        Protection de vos données — RGPD
                    </div>
                    <div style="font-size:0.8rem;color:#6b7280;margin-top:2px;">
                        Conformité Règlement Général sur la Protection des Données (UE 2016/679)
                    </div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        with st.expander("📄 Lire la politique complète de confidentialité", expanded=False):
            st.markdown("""
**1. Responsable du traitement**
OralBiome SAS — contact@oralbiome.com — DPO disponible sur demande.

**2. Données collectées**
Données d'identification (nom, âge, email, téléphone), données de santé bucco-dentaire (biomarqueurs microbiome), données de santé systémique (scores de risque), questionnaire d'anamnèse.

**3. Base légale**
Consentement explicite (Art. 9 RGPD) et intérêt légitime du professionnel de santé.

**4. Finalités**
Suivi de la santé bucco-dentaire et systémique, génération de rapports cliniques, communication praticien-patient.

**5. Conservation**
Durée de la relation de soin puis archivage légal (10 ans — dossiers médicaux).

**6. Destinataires**
Données jamais vendues ni transmises à des tiers à des fins commerciales.

**7. Hébergement**
Serveurs certifiés HDS (Hébergeur de Données de Santé) — Art. L.1111-8 CSP.

**8. Vos droits**
Accès, rectification, effacement, portabilité, opposition → contact@oralbiome.com

**9. Réclamations**
CNIL — www.cnil.fr
            """)

        st.markdown("""
        <div style="background:#fefce8;border:1px solid #fde047;border-radius:10px;padding:14px 18px;margin:12px 0;">
            <div style="font-size:0.85rem;color:#713f12;">
                ⚠️ <b>Données de santé :</b> Les informations saisies constituent des données de santé au sens du RGPD.
                Leur traitement est strictement encadré et réservé aux professionnels de santé habilités.
            </div>
        </div>""", unsafe_allow_html=True)

        agree1 = st.checkbox("✅ J'accepte que mes données de santé soient traitées par OralBiome conformément à la politique de confidentialité ci-dessus.", key="rgpd_check1")
        agree2 = st.checkbox("✅ Je confirme être un professionnel de santé habilité ou le patient concerné.", key="rgpd_check2")
        st.checkbox("📧 J'accepte de recevoir des communications relatives à mon suivi OralBiome. *(optionnel)*", key="rgpd_check3")

        st.markdown("<br>", unsafe_allow_html=True)
        col_ref, col_acc = st.columns(2)
        with col_ref:
            if st.button("Refuser et quitter", use_container_width=True):
                st.session_state.mode = "choix"; st.rerun()
        with col_acc:
            if st.button("Accepter et continuer →", use_container_width=True,
                         type="primary", disabled=not (agree1 and agree2)):
                st.session_state.rgpd_accepted = True; st.rerun()
        if not (agree1 and agree2):
            st.caption("⚠️ Les deux premières cases sont obligatoires.")
    st.markdown("""
    <style>
    .wizard-card {
        background:white;border-radius:20px;padding:40px 44px;
        border:1px solid #e5e7eb;box-shadow:0 4px 24px rgba(0,0,0,0.06);
        max-width:680px;margin:0 auto;
    }
    .feature-chip {
        display:inline-flex;align-items:center;gap:6px;
        background:#f0f9ff;border:1px solid #bae6fd;border-radius:20px;
        padding:6px 14px;margin:4px;font-size:0.82rem;color:#0369a1;font-weight:500;
    }
    .step-circle-active   { background:#2563eb;border:2px solid #2563eb;color:white; }
    .step-circle-done     { background:#16a34a;border:2px solid #16a34a;color:white; }
    .step-circle-inactive { background:white;border:2px solid #d1d5db;color:#9ca3af; }
    </style>
    """, unsafe_allow_html=True)

    step = st.session_state.onboarding_step

    # Header
    logo_h = logo_img(width=160, style="margin:0 auto 16px auto;")
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:20px;
         padding:32px 40px;margin-bottom:32px;text-align:center;color:white;">
        {logo_h}
        <h2 style="font-family:'DM Serif Display',serif;font-size:2rem;margin:0;">Bienvenue sur OralBiome</h2>
        <p style="opacity:0.7;margin:8px 0 0 0;font-size:0.95rem;">Configuration de votre espace · 3 étapes · moins de 2 minutes</p>
    </div>""", unsafe_allow_html=True)

    # Barre de progression
    def s_circle(n):
        if n < step:   css = "background:#16a34a;border:2px solid #16a34a;color:white;"
        elif n == step: css = "background:#2563eb;border:2px solid #2563eb;color:white;"
        else:           css = "background:white;border:2px solid #d1d5db;color:#9ca3af;"
        txt = "✓" if n < step else str(n)
        return f'<div style="width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.9rem;{css}">{txt}</div>'
    def s_label(txt, n):
        c = "#16a34a" if n < step else "#2563eb" if n == step else "#9ca3af"
        return f'<div style="font-size:0.78rem;font-weight:600;color:{c};margin-top:6px;">{txt}</div>'
    def s_line(n):
        c = "#16a34a" if n < step else "#e5e7eb"
        return f'<div style="width:80px;height:2px;background:{c};margin:18px 4px 0 4px;"></div>'

    st.markdown(f"""
    <div style="display:flex;justify-content:center;align-items:flex-start;margin:0 0 36px 0;">
        <div style="text-align:center;">{s_circle(1)}{s_label("Bienvenue",1)}</div>
        {s_line(1)}
        <div style="text-align:center;">{s_circle(2)}{s_label("Votre cabinet",2)}</div>
        {s_line(2)}
        <div style="text-align:center;">{s_circle(3)}{s_label("Premier patient",3)}</div>
    </div>""", unsafe_allow_html=True)

    _, col_center, _ = st.columns([1, 2, 1])

    # ── ÉTAPE 1 ──────────────────────────────────────────────
    if step == 1:
        with col_center:
            st.markdown("""
            <div class="wizard-card">
                <div style="font-size:2.4rem;text-align:center;margin-bottom:12px;">🦷</div>
                <h3 style="font-family:'DM Serif Display',serif;color:#1a3a5c;text-align:center;margin:0 0 8px 0;">
                    La plateforme d'intelligence orale prédictive
                </h3>
                <p style="color:#6b7280;text-align:center;font-size:0.9rem;margin-bottom:24px;">
                    Corrèlez le microbiote oral de vos patients avec leurs risques systémiques.<br>
                    Générez des rapports cliniques en 1 clic. Suivez l'évolution en temps réel.
                </p>
                <div style="text-align:center;margin-bottom:24px;">
                    <span class="feature-chip">🧬 Microbiome oral prédictif</span>
                    <span class="feature-chip">❤️ Risques cardiovasculaires</span>
                    <span class="feature-chip">🧠 Alzheimer & neuro</span>
                    <span class="feature-chip">📊 Benchmark NHANES n=8 237</span>
                    <span class="feature-chip">🤖 IA Claude intégrée</span>
                    <span class="feature-chip">📄 PDF automatiques</span>
                </div>
                <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:16px;text-align:center;">
                    <div style="font-weight:600;color:#15803d;margin-bottom:4px;">✅ Votre compte est activé</div>
                    <div style="font-size:0.85rem;color:#166534;">Accès complet à toutes les fonctionnalités · Données sécurisées</div>
                </div>
            </div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Commencer la configuration →", use_container_width=True, type="primary"):
                st.session_state.onboarding_step = 2
                st.rerun()

    # ── ÉTAPE 2 ──────────────────────────────────────────────
    elif step == 2:
        with col_center:
            st.markdown("### 🏥 Configurez votre cabinet")
            st.caption("Ces informations apparaîtront sur vos rapports PDF.")
            with st.form("form_cabinet"):
                c1, c2 = st.columns(2)
                with c1:
                    cabinet_nom = st.text_input("Nom du cabinet *",
                        value=st.session_state.get("cabinet_nom",""),
                        placeholder="Ex: Cabinet Dentaire Dupont")
                    cabinet_praticien = st.text_input("Praticien *",
                        value=st.session_state.get("cabinet_praticien",""),
                        placeholder="Ex: Dr. Marie Dupont")
                    cabinet_specialite = st.selectbox("Spécialité",
                        ["Omnipraticien","Parodontiste","Orthodontiste","Implantologiste","Pédodontiste","Autre"])
                with c2:
                    cabinet_adresse = st.text_input("Adresse",
                        value=st.session_state.get("cabinet_adresse",""),
                        placeholder="Ex: 12 rue de la Santé, Paris")
                    cabinet_tel = st.text_input("Téléphone",
                        value=st.session_state.get("cabinet_tel",""),
                        placeholder="+33 1 23 45 67 89")
                    cabinet_email = st.text_input("Email cabinet",
                        value=st.session_state.get("cabinet_email",""),
                        placeholder="contact@cabinet.fr")
                st.markdown("---")
                st.markdown("**🔔 Préférences de suivi**")
                p1, p2 = st.columns(2)
                with p1:
                    rappel_semaines = st.selectbox("Intervalle rappel par défaut",
                        [8,12,16,24], format_func=lambda x: f"Tous les {x} semaines", index=1)
                with p2:
                    seuil_alerte = st.selectbox("Seuil alerte P. gingivalis",
                        [0.3,0.5,0.8,1.0], format_func=lambda x: f"> {x}%", index=1)
                sub2 = st.form_submit_button("Enregistrer et continuer →",
                    use_container_width=True, type="primary")
                if sub2:
                    if not cabinet_nom.strip() or not cabinet_praticien.strip():
                        st.error("Le nom du cabinet et le nom du praticien sont obligatoires.")
                    else:
                        st.session_state.cabinet_nom        = cabinet_nom
                        st.session_state.cabinet_praticien  = cabinet_praticien
                        st.session_state.cabinet_adresse    = cabinet_adresse
                        st.session_state.cabinet_tel        = cabinet_tel
                        st.session_state.cabinet_email      = cabinet_email
                        st.session_state.cabinet_specialite = cabinet_specialite
                        st.session_state.rappel_semaines    = rappel_semaines
                        st.session_state.seuil_alerte       = seuil_alerte
                        st.session_state.onboarding_step    = 3
                        st.rerun()
            if st.button("← Retour", key="back2"):
                st.session_state.onboarding_step = 1; st.rerun()

    # ── ÉTAPE 3 ──────────────────────────────────────────────
    elif step == 3:
        with col_center:
            st.markdown("### 👤 Ajoutez votre premier patient")
            st.caption("Vous pourrez en ajouter d'autres depuis le tableau de bord. Cette étape est optionnelle.")
            with st.form("form_premier_patient"):
                fc1, fc2 = st.columns(2)
                with fc1:
                    p_nom   = st.text_input("Nom complet", placeholder="Ex: Jean Dupont")
                    p_age   = st.number_input("Âge", 1, 120, 40)
                    p_email = st.text_input("Email patient", placeholder="jean@email.com")
                with fc2:
                    p_tel = st.text_input("Téléphone", placeholder="+32 472 000 000")
                    p_sm  = st.number_input("S. mutans (%)", 0.0, 10.0, 2.0, step=0.1)
                    p_pg  = st.number_input("P. gingivalis (%)", 0.0, 5.0, 0.2, step=0.1)
                p_div = st.slider("Score Diversité Microbienne", 0, 100, 70)
                col_skip, col_save = st.columns(2)
                with col_skip:
                    passer = st.form_submit_button("Passer cette étape →", use_container_width=True)
                with col_save:
                    sauver = st.form_submit_button("Créer le dossier et terminer ✓",
                        use_container_width=True, type="primary")
                if passer:
                    st.session_state.onboarding_done = True
                    st.session_state.connecte = True
                    st.session_state.mode = "praticien"
                    st.rerun()
                if sauver:
                    if p_nom.strip():
                        nid  = f"P{str(len(st.session_state.patients)+1).zfill(3)}"
                        stat = "Alerte" if p_sm>3.0 or p_pg>0.5 or p_div<50 else "Stable"
                        df_n = pd.DataFrame({"Date":[date.today().strftime("%d/%m/%Y")],"Acte / Test":["Examen Initial"],"S. mutans (%)":[p_sm],"P. gingiv. (%)":[p_pg],"Diversite (%)":[p_div],"Status":[stat]})
                        st.session_state.patients[p_nom] = {"id":nid,"nom":p_nom,"age":p_age,"email":p_email,"telephone":p_tel,"date_naissance":"","historique":df_n,"s_mutans":p_sm,"p_gingivalis":p_pg,"diversite":p_div,"code_patient":f"OB-{nid}"}
                        st.session_state.patient_sel = p_nom
                    st.session_state.onboarding_done = True
                    st.session_state.connecte = True
                    st.session_state.mode = "praticien"
                    st.success("✅ Cabinet configuré ! Bienvenue sur OralBiome.")
                    st.rerun()
            if st.button("← Retour", key="back3"):
                st.session_state.onboarding_step = 2; st.rerun()
if st.session_state.mode == "choix":
    st.markdown("""
    <style>
    .main { background:#f6f8fb; }
    .ob-header { background:linear-gradient(135deg,rgba(15,42,68,0.95),rgba(31,78,121,0.95));padding:32px 36px;border-radius:20px;color:white;display:flex;align-items:center;gap:20px;backdrop-filter:blur(10px); }
    .logo-box { background:white;padding:10px;border-radius:12px; }
    .subtitle { opacity:0.8;font-size:15px;margin-top:4px; }
    .card { background:white;padding:26px;border-radius:18px;border:1px solid #e6eaf0;height:100%;display:flex;flex-direction:column;justify-content:space-between;transition:all 0.2s ease; }
    .card:hover { border-color:#c9d3df;transform:translateY(-3px); }
    .card-title { font-size:18px;font-weight:600;margin-bottom:10px; }
    .card-text { font-size:14px;color:#5f6b7a;line-height:1.5; }
    .card-footer { margin-top:20px; }
    .stButton > button { border-radius:10px;height:42px;font-weight:500;font-size:14px; }
    .footer { text-align:center;font-size:12px;color:#8892a0;margin-top:50px; }
    </style>""", unsafe_allow_html=True)
    logo_html = logo_img(width=400)
    st.markdown(f"""
    <div class="ob-header">
        <div class="logo-box">{logo_html}</div>
        <div>
            <div style="font-size:28px;font-weight:600;">OralBiome</div>
            <div class="subtitle">Analyse prédictive du microbiome oral pour la prévention systémique</div>
        </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.markdown('<div class="card"><div><div class="card-title">Espace Praticien</div><div class="card-text">Accédez à un tableau de bord complet pour analyser, suivre et générer des rapports cliniques avancés.</div></div></div>', unsafe_allow_html=True)
        if st.button("Se connecter", use_container_width=True, type="primary"):
            st.session_state.mode = "praticien"; st.rerun()
    with col2:
        st.markdown('<div class="card"><div><div class="card-title">Espace Patient</div><div class="card-text">Consultez votre analyse personnalisée, vos recommandations et votre suivi santé.</div></div></div>', unsafe_allow_html=True)
        if st.button("Accéder à mon espace", use_container_width=True):
            st.session_state.mode = "patient"; st.rerun()
    with col3:
        st.markdown('<div class="card"><div><div class="card-title">ℹ️ À propos</div><div class="card-text">OralBiome utilise l\'IA pour corréler le microbiote oral avec les risques systémiques (cardio, diabète, neuro…).</div></div><div class="card-footer"><span style="font-size:13px;color:#1f4e79;">contact@oralbiome.com</span></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="footer">© 2026 OralBiome — Clinical Intelligence Platform</div>', unsafe_allow_html=True)

# ============================================================
# PORTAIL PATIENT
# ============================================================
elif st.session_state.mode == "patient":
# RGPD avant accès patient
    if not st.session_state.rgpd_accepted:
        render_rgpd_banner()
        st.stop()
    if st.session_state.patient_connecte is None:
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if LOGO_B64:
                st.markdown(f"<div style='text-align:center;'>{logo_img(width=400)}</div>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center;color:#1a3a5c;margin-top:10px;'>Espace Patient</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center;color:#888;'>Consultez votre rapport personnalisé</p>", unsafe_allow_html=True)
            st.markdown("---")
            code = st.text_input("Votre code patient", placeholder="Ex: OB-P001")
            if st.button("Accéder à mon dossier", use_container_width=True, type="primary"):
                found = next((n for n,d in st.session_state.patients.items() if d.get("code_patient")==code.strip()), None)
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

        if LOGO_B64:
            st.sidebar.markdown(f"<div style='text-align:center;padding:6px 0;'>{logo_img(width=120)}</div>", unsafe_allow_html=True)
        st.sidebar.markdown(f"### 👋 {patient['nom'].split()[0]}")
        st.sidebar.markdown(f"Code : `{patient['code_patient']}`")
        st.sidebar.markdown(f"**{'🔴 En alerte' if en_alerte else '🟢 Équilibré'}**")
        st.sidebar.markdown(f"Prochain contrôle : **{plan['suivi_semaines']} semaines**")
        st.sidebar.markdown("---")
        if st.sidebar.button("Se déconnecter"):
            st.session_state.patient_connecte = None; st.rerun()
        if st.sidebar.button("Retour accueil"):
            st.session_state.patient_connecte = None; st.session_state.mode = "choix"; st.rerun()

        logo_h = logo_img(width=120, style="margin-bottom:8px;filter:brightness(0) invert(1);opacity:0.9;")
        st.markdown(f"""
        <div class='patient-header'>
            {logo_h}
            <h2 style="margin-top:4px;">Bonjour {patient['nom']} !</h2>
            <p>Rapport microbiome oral personnalisé · {date.today().strftime('%d/%m/%Y')}</p>
        </div>""", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Risque Carieux", r_carieux, delta_color="inverse")
        c2.metric("Risque Parodontal", r_paro, delta_color="inverse")
        c3.metric("Diversité Microbienne", f"{diversite}/100")
        st.markdown("---")

        # ── TABS PATIENT (7 onglets avec anamnèse) ──────────
        tp1, tp2, tp3, tp4, tp5, tp6, tp7 = st.tabs([
            "📊 Mon Profil", "🧬 Risques Systémiques", "📸 Analyse Photo",
            "🚨 Mes Actions", "🥗 Nutrition & Probiotiques", "📋 Mon Anamnèse", "📥 Rapport PDF"
        ])

        with tp1:
            st.header("📊 Mon Profil Bactérien")
            if en_alerte:
                st.warning(f"**{plan['profil_label']}** — {plan['profil_description']}")
            else:
                st.success(f"**{plan['profil_label']}** — {plan['profil_description']}")
            st.markdown("---")
            st.markdown("#### 🌍 Votre Diversité Microbienne vs la Population")
            render_diversity_benchmark(diversite, age=patient.get("age"), context="patient")
            if not patient["historique"].empty:
                st.markdown("---")
                st.markdown("#### 📅 Historique de vos analyses")
                st.dataframe(patient["historique"], use_container_width=True, hide_index=True)

        with tp2:
            st.header("🧬 Risques Systémiques")
            st.markdown("*Corrélations établies entre votre microbiote oral et vos risques de santé généraux.*")
            st.markdown("---")
            for key, data in scores_sys.items():
                score = data["score"]
                level = data["level"]
                score_css = "score-high" if level=="high" else "score-med" if level=="med" else "score-low"
                col_ring, col_content = st.columns([1, 6])
                with col_ring:
                    st.markdown(f"<div class='score-ring {score_css}'>{score}</div>", unsafe_allow_html=True)
                with col_content:
                    st.markdown(f"""
                    <div class='systemic-card'>
                        <div class='systemic-title'>{data['icon']} {data['label']}</div>
                        <div style="font-size:0.85rem;color:#4b5563;margin-bottom:8px;">{data['description']}</div>
                        <div style="font-size:0.75rem;color:#9ca3af;margin-bottom:8px;"><em>Réf : {data['references']}</em></div>
                    </div>""", unsafe_allow_html=True)
                    with st.expander("Voir les recommandations →"):
                        for action in data["actions"]:
                            st.markdown(f"- {action}")
                st.markdown("")
            st.info("⚕️ Ces scores sont des estimations basées sur des corrélations épidémiologiques publiées. Ne constituent pas un diagnostic médical.")

        with tp3:
            st.header("📸 Analyse Photo de la Cavité Buccale")
            st.markdown("Uploadez une photo de votre bouche. L'IA détecte les signes visuels d'inflammation, tartre, lésions et anomalies.")
            st.caption("📌 Conseils : bonne lumière, bouche ouverte, photo nette. JPEG ou PNG.")
            st.markdown("---")
            if not ANTHROPIC_API_KEY:
                st.warning("⚠️ Fonctionnalité disponible après configuration de la clé API Anthropic dans `st.secrets`.")
            else:
                uploaded = st.file_uploader("Choisir une photo", type=["jpg","jpeg","png"], label_visibility="collapsed")
                if uploaded:
                    img_bytes = uploaded.read()
                    mime = "image/png" if uploaded.name.endswith(".png") else "image/jpeg"
                    col_img, col_res = st.columns([1,2])
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

        # ── ONGLET ANAMNÈSE ──────────────────────────────────
        with tp6:
            st.header("📋 Mon Questionnaire de Santé")
            st.markdown("Ces informations permettent à votre praticien d'affiner votre analyse.")

            anamnes = get_anamnes(st.session_state.patient_connecte)

            if anamnes.get("completed_at"):
                st.success(f"✅ Questionnaire complété le {anamnes['completed_at'][:10]}")
            else:
                st.warning("⚠️ Questionnaire non encore rempli — vos recommandations seront plus précises une fois complété.")

            with st.form("form_anamnes_patient"):
                st.markdown("### 🏥 Antécédents Médicaux")
                a1, a2, a3 = st.columns(3)
                with a1:
                    diabete      = st.checkbox("Diabète",       value=bool(anamnes.get("diabete", 0)))
                    hypertension = st.checkbox("Hypertension",  value=bool(anamnes.get("hypertension", 0)))
                with a2:
                    maladie_cardio = st.checkbox("Maladie cardiovasculaire", value=bool(anamnes.get("maladie_cardio", 0)))
                    osteoporose    = st.checkbox("Ostéoporose",              value=bool(anamnes.get("osteoporose", 0)))
                with a3:
                    cancer = st.checkbox("Cancer (actuel ou passé)", value=bool(anamnes.get("cancer", 0)))
                autre_antecedent = st.text_input("Autre condition médicale",
                    value=anamnes.get("autre_antecedent",""),
                    placeholder="Ex: hypothyroïdie, asthme...")

                st.markdown("---")
                st.markdown("### 💊 Médicaments")
                prend_medicaments = st.checkbox("Je prends actuellement des médicaments",
                    value=bool(anamnes.get("prend_medicaments", 0)))
                liste_medicaments = ""
                antibiotiques_recents = False
                if prend_medicaments:
                    liste_medicaments = st.text_area("Liste des médicaments",
                        value=anamnes.get("liste_medicaments",""),
                        placeholder="Ex: Metformine 500mg, Amlodipine 5mg...", height=80)
                    antibiotiques_recents = st.checkbox("J'ai pris des antibiotiques dans les 3 derniers mois",
                        value=bool(anamnes.get("antibiotiques_recents", 0)))

                st.markdown("---")
                st.markdown("### 🌿 Habitudes de Vie")
                h1, h2 = st.columns(2)
                with h1:
                    fumeur = st.selectbox("Tabac",
                        ["non","occasionnel","regulier"],
                        index=["non","occasionnel","regulier"].index(anamnes.get("fumeur","non")),
                        format_func=lambda x: {"non":"🚭 Non-fumeur","occasionnel":"🚬 Occasionnel","regulier":"🚬 Fumeur régulier"}[x])
                    alcool = st.selectbox("Consommation d'alcool",
                        ["non","modere","eleve"],
                        index=["non","modere","eleve"].index(anamnes.get("alcool","non")),
                        format_func=lambda x: {"non":"✅ Pas ou rarement","modere":"🍷 Modérée","eleve":"⚠️ Élevée"}[x])
                with h2:
                    alimentation_type = st.selectbox("Type d'alimentation",
                        ["omnivore","vegetarien","vegan","paleo","mediterraneen","autre"],
                        index=["omnivore","vegetarien","vegan","paleo","mediterraneen","autre"].index(
                            anamnes.get("alimentation_type","omnivore")),
                        format_func=lambda x: {"omnivore":"🍖 Omnivore","vegetarien":"🥗 Végétarien","vegan":"🌱 Vegan","paleo":"🥩 Paléo","mediterraneen":"🫒 Méditerranéen","autre":"🍽️ Autre"}[x])
                    sucres_eleves = st.checkbox("Consommation élevée de sucres",
                        value=bool(anamnes.get("sucres_eleves", 0)))

                st.markdown("---")
                st.markdown("### 🦷 Hygiène Buccale")
                hb1, hb2, hb3 = st.columns(3)
                with hb1:
                    brosse_dents_freq = st.selectbox("Fréquence de brossage",
                        ["1x/jour","2x/jour","3x/jour","moins d'1x/jour"],
                        index=["1x/jour","2x/jour","3x/jour","moins d'1x/jour"].index(
                            anamnes.get("brosse_dents_freq","2x/jour")))
                with hb2:
                    fil_dentaire = st.checkbox("Fil dentaire quotidien", value=bool(anamnes.get("fil_dentaire", 0)))
                with hb3:
                    bain_bouche = st.checkbox("Bain de bouche régulier", value=bool(anamnes.get("bain_bouche", 0)))

                st.markdown("---")
                st.markdown("### 🔍 Symptômes Actuels")
                s1, s2, s3, s4 = st.columns(4)
                with s1: saignement   = st.checkbox("🩸 Saignement gencives",    value=bool(anamnes.get("saignement_gencives", 0)))
                with s2: douleur      = st.checkbox("😣 Douleur dentaire",        value=bool(anamnes.get("douleur_dentaire", 0)))
                with s3: sensibilite  = st.checkbox("❄️ Sensibilité chaud/froid", value=bool(anamnes.get("sensibilite", 0)))
                with s4: mauvaise_hal = st.checkbox("💨 Mauvaise haleine",        value=bool(anamnes.get("mauvaise_haleine", 0)))

                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("💾 Sauvegarder mon questionnaire",
                    use_container_width=True, type="primary")

                if submitted:
                    save_anamnes(st.session_state.patient_connecte, {
                        "diabete":int(diabete),"hypertension":int(hypertension),
                        "maladie_cardio":int(maladie_cardio),"osteoporose":int(osteoporose),
                        "cancer":int(cancer),"autre_antecedent":autre_antecedent,
                        "prend_medicaments":int(prend_medicaments),
                        "liste_medicaments":liste_medicaments,
                        "antibiotiques_recents":int(antibiotiques_recents),
                        "fumeur":fumeur,"alcool":alcool,
                        "brosse_dents_freq":brosse_dents_freq,
                        "fil_dentaire":int(fil_dentaire),"bain_bouche":int(bain_bouche),
                        "sucres_eleves":int(sucres_eleves),"alimentation_type":alimentation_type,
                        "saignement_gencives":int(saignement),"douleur_dentaire":int(douleur),
                        "sensibilite":int(sensibilite),"mauvaise_haleine":int(mauvaise_hal)
                    })
                    st.success("✅ Questionnaire sauvegardé ! Votre praticien y a maintenant accès.")
                    st.rerun()

        with tp7:
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

        # RGPD avant login
        if not st.session_state.rgpd_accepted:
            render_rgpd_banner()
            st.stop()

        # LOGIN
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if LOGO_B64:
                st.markdown(f"<div style='text-align:center;'>{logo_img(width=400)}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<h2 style='text-align:center;color:#1a3a5c;'>🦷 OralBiome</h2>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align:center;color:#64748b;'>Portail Praticien</h4>", unsafe_allow_html=True)
            st.markdown("---")
            email = st.text_input("Email Professionnel")
            mdp   = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter", use_container_width=True, type="primary"):
                if email == "contact@oralbiome.com" and mdp == "mvp2024":
                    st.session_state.connecte = True
                    if not st.session_state.onboarding_done:
                        st.session_state.onboarding_step = 1
                    st.rerun()
                else:
                    st.error("Identifiants incorrects. Demo : contact@oralbiome.com / mvp2024")
            if st.button("Retour à l'accueil", use_container_width=True):
                st.session_state.mode = "choix"; st.rerun()

    else:
        # Wizard onboarding première connexion
        if not st.session_state.onboarding_done:
            render_onboarding()
            st.stop()

        # ── SIDEBAR ───────────────────────────────────────────
        if LOGO_B64:
            st.sidebar.markdown(f"<div style='text-align:center;padding:8px 0 4px 0;'>{logo_img(width=400)}</div>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown("## 🦷 OralBiome")
        st.sidebar.markdown("---")
        sc1, sc2, sc3 = st.sidebar.columns(3)
        with sc1:
            if st.button("📊", use_container_width=True, help="Dashboard"):
                st.session_state.vue = "dashboard"; st.rerun()
        with sc2:
            if st.button("👥", use_container_width=True, help="Patients"):
                st.session_state.vue = "liste"; st.rerun()
        with sc3:
            if st.button("➕", use_container_width=True, help="Nouveau patient"):
                st.session_state.vue = "nouveau"; st.rerun()
        st.sidebar.markdown("---")

        nb_patients = len(st.session_state.patients)
        nb_alertes = sum(1 for p in st.session_state.patients.values()
                         if p["s_mutans"]>3.0 or p["p_gingivalis"]>0.5 or p["diversite"]<50)
        nb_alertes_actives = len(calculer_alertes(st.session_state.patients))
        ms1, ms2, ms3 = st.sidebar.columns(3)
        ms1.metric("Patients", nb_patients)
        ms2.metric("Alertes", nb_alertes)
        ms3.metric("🔔", nb_alertes_actives)
        st.sidebar.markdown("---")

        rech = st.sidebar.text_input("Rechercher...", placeholder="Nom ou ID")
        pf = {n:d for n,d in st.session_state.patients.items()
              if rech.lower() in n.lower() or rech.lower() in d["id"].lower()} if rech else st.session_state.patients
        for nom, data in pf.items():
            icon = "🔴" if (data["s_mutans"]>3.0 or data["p_gingivalis"]>0.5 or data["diversite"]<50) else "🟢"
            is_sel = nom == st.session_state.patient_sel
            if st.sidebar.button(f"{icon} {data['id']} — {nom}", use_container_width=True,
                                  type="primary" if is_sel else "secondary"):
                st.session_state.patient_sel = nom; st.session_state.vue = "dossier"; st.rerun()
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Déconnecter", use_container_width=True):
            st.session_state.connecte = False; st.rerun()
        if st.sidebar.button("Retour accueil", use_container_width=True):
            st.session_state.connecte = False; st.session_state.mode = "choix"; st.rerun()

        # ── VUE DASHBOARD ─────────────────────────────────────
        if st.session_state.vue == "dashboard":
            render_dashboard(st.session_state.patients)

        # ── VUE LISTE ─────────────────────────────────────────
        elif st.session_state.vue == "liste":
            st.title("👥 Gestion des Patients")
            lf1, lf2, lf3 = st.columns(3)
            with lf1:
                filtre = st.selectbox("Filtrer", ["Tous","Alerte uniquement","Stable uniquement"])
            with lf3:
                if st.button("➕ Nouveau Patient", type="primary"):
                    st.session_state.vue = "nouveau"; st.rerun()
            donnees = []
            for nom, data in st.session_state.patients.items():
                ea = data["s_mutans"]>3.0 or data["p_gingivalis"]>0.5 or data["diversite"]<50
                if filtre=="Alerte uniquement" and not ea: continue
                if filtre=="Stable uniquement" and ea: continue
                sys_scores = calculer_score_systemique(data["s_mutans"],data["p_gingivalis"],data["diversite"])
                top_sys = max(sys_scores.items(), key=lambda x: x[1]["score"])
                donnees.append({"ID":data["id"],"Nom":nom,"Âge":data["age"],
                                "Risque Carieux":"⚠️ Élevé" if data["s_mutans"]>3.0 else "✅ Faible",
                                "Risque Parodontal":"⚠️ Élevé" if data["p_gingivalis"]>0.5 else "✅ Faible",
                                "Diversité":f"{data['diversite']}/100",
                                "Risque Systémique Principal":f"{top_sys[1]['icon']} {top_sys[1]['label']} ({top_sys[1]['score']}/100)",
                                "Statut":"🔴 Alerte" if ea else "🟢 Stable"})
            if donnees:
                st.dataframe(pd.DataFrame(donnees), use_container_width=True, hide_index=True)

        # ── VUE NOUVEAU ───────────────────────────────────────
        elif st.session_state.vue == "nouveau":
            st.title("➕ Nouveau Patient")
            with st.form("form_nouveau"):
                nc1, nc2 = st.columns(2)
                with nc1:
                    nn = st.text_input("Nom complet *")
                    ne = st.text_input("Email")
                    nd_nais = st.date_input("Date de naissance", value=date(1985,1,1))
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
                        df_n = pd.DataFrame(columns=["Date","Acte / Test","S. mutans (%)","P. gingiv. (%)","Diversite (%)","Status"])
                        if aj:
                            s = "Alerte" if is_>3.0 or ip_>0.5 or id_<50 else "Stable"
                            df_n.loc[0] = [date.today().strftime("%d/%m/%Y"),"Examen Initial",is_,ip_,id_,s]
                        st.session_state.patients[nn] = {
                            "id":nid,"nom":nn,"age":na,"email":ne,"telephone":nt,
                            "date_naissance":nd_nais.strftime("%d/%m/%Y"),
                            "historique":df_n,"s_mutans":is_ if aj else 0.0,
                            "p_gingivalis":ip_ if aj else 0.0,"diversite":id_ if aj else 70,
                            "code_patient":f"OB-{nid}"
                        }
                        st.session_state.patient_sel = nn
                        st.session_state.vue = "dossier"
                        st.success(f"Dossier créé ! Code patient : **OB-{nid}**")
                        st.rerun()

        # ── VUE DOSSIER ───────────────────────────────────────
        else:
            patient = st.session_state.patients.get(st.session_state.patient_sel)
            if not patient:
                st.error("Patient introuvable.")
            else:
                s_mutans = patient["s_mutans"]
                p_gingivalis = patient["p_gingivalis"]
                diversite = patient["diversite"]
                r_carieux = "Eleve" if s_mutans>3.0 else "Faible"
                r_paro    = "Eleve" if p_gingivalis>0.5 else "Faible"
                en_alerte = r_carieux=="Eleve" or r_paro=="Eleve" or diversite<50
                plan = generer_recommandations(s_mutans, p_gingivalis, diversite)
                scores_sys = calculer_score_systemique(s_mutans, p_gingivalis, diversite)

                badge = "🔴 En Alerte" if en_alerte else "🟢 Stable"
                st.markdown(f"## 🦷 {patient['nom']}  `{patient['id']}`  —  {badge}")
                st.caption(f"Âge : {patient['age']} ans  ·  {patient['email']}  ·  Code : **{patient.get('code_patient','')}**")
                st.markdown("---")

                m1,m2,m3,m4,m5 = st.columns(5)
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

                st.info(f"Code patient : **{patient.get('code_patient','')}** — À communiquer au patient pour son accès portail.")
                st.markdown("---")

                # ── Anamnèse visible pour le praticien ────────
                anamnes_p = get_anamnes(st.session_state.patient_sel)
                if anamnes_p.get("completed_at"):
                    with st.expander(f"📋 Anamnèse patient — complétée le {anamnes_p['completed_at'][:10]}"):
                        ac1, ac2, ac3 = st.columns(3)
                        with ac1:
                            st.markdown("**🏥 Antécédents**")
                            if anamnes_p.get("diabete"):          st.markdown("- 🩸 Diabète")
                            if anamnes_p.get("hypertension"):     st.markdown("- ❤️ Hypertension")
                            if anamnes_p.get("maladie_cardio"):   st.markdown("- 🫀 Maladie cardiovasculaire")
                            if anamnes_p.get("osteoporose"):      st.markdown("- 🦴 Ostéoporose")
                            if anamnes_p.get("cancer"):           st.markdown("- ⚠️ Cancer")
                            if anamnes_p.get("autre_antecedent"): st.markdown(f"- 📌 {anamnes_p['autre_antecedent']}")
                        with ac2:
                            st.markdown("**🌿 Habitudes**")
                            st.markdown(f"- Tabac : `{anamnes_p.get('fumeur','?')}`")
                            st.markdown(f"- Alcool : `{anamnes_p.get('alcool','?')}`")
                            st.markdown(f"- Alimentation : `{anamnes_p.get('alimentation_type','?')}`")
                            st.markdown(f"- Brossage : `{anamnes_p.get('brosse_dents_freq','?')}`")
                            if anamnes_p.get("sucres_eleves"): st.markdown("- ⚠️ Sucres élevés")
                        with ac3:
                            st.markdown("**🔍 Symptômes**")
                            if anamnes_p.get("saignement_gencives"):   st.markdown("- 🩸 Saignement gencives")
                            if anamnes_p.get("douleur_dentaire"):      st.markdown("- 😣 Douleur dentaire")
                            if anamnes_p.get("sensibilite"):           st.markdown("- ❄️ Sensibilité")
                            if anamnes_p.get("mauvaise_haleine"):      st.markdown("- 💨 Mauvaise haleine")
                            if anamnes_p.get("antibiotiques_recents"): st.markdown("- 💊 Antibiotiques récents")
                else:
                    st.caption("📋 Anamnèse non encore remplie par le patient.")

                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "🧬 Risques Systémiques","🚨 Plan d'Action","🔬 Simulateur","📸 Analyse Photo","📂 Historique & PDF"
                ])

                with tab1:
                    st.header("🧬 Corrélations Microbiome → Risques Systémiques")
                    st.caption("Scores calculés selon les pondérations de la littérature scientifique peer-reviewed.")
                    st.markdown("#### 🌍 Benchmark Diversité — Population NHANES (n=8 237)")
                    render_diversity_benchmark(diversite, age=patient.get("age"), context="praticien")
                    st.markdown("---")
                    rows = []
                    for key, data in scores_sys.items():
                        level_label = "🔴 Élevé" if data["level"]=="high" else "🟡 Modéré" if data["level"]=="med" else "🟢 Faible"
                        rows.append({"Pathologie":f"{data['icon']} {data['label']}","Score":data["score"],"Niveau":level_label,"Action prioritaire":data["actions"][0] if data["actions"] else "-"})
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    st.markdown("---")
                    for key, data in scores_sys.items():
                        if data["level"] == "high":
                            col1, col2 = st.columns([1,6])
                            with col1:
                                st.markdown(f"<div class='score-ring score-high'>{data['score']}</div>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"**{data['icon']} {data['label']}**")
                                st.markdown(f"*{data['description']}*")
                                with st.expander("Protocole clinique recommandé"):
                                    for action in data["actions"]: st.markdown(f"- {action}")
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
                        for action in p["actions"]: st.markdown(f"- {action}")
                        st.markdown("---")

                with tab3:
                    st.markdown("""
                    <div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:14px;padding:20px 28px;margin-bottom:20px;">
                        <h3 style="color:#fff;margin:0;font-family:'DM Serif Display',serif;">🔬 Simulateur d'Impact Thérapeutique</h3>
                        <p style="color:rgba(255,255,255,0.65);margin:6px 0 0 0;font-size:0.9rem;">Ajustez les biomarqueurs et visualisez l'impact en temps réel.</p>
                    </div>""", unsafe_allow_html=True)

                    col_sliders, col_results = st.columns([1,2])
                    with col_sliders:
                        st.markdown("#### ⚙️ Ajuster les biomarqueurs")
                        sim_mutans = st.slider("S. mutans (%)", 0.0, 10.0, float(s_mutans), step=0.1)
                        sim_paro   = st.slider("P. gingivalis (%)", 0.0, 3.0, float(p_gingivalis), step=0.1)
                        sim_div    = st.slider("Diversité microbienne", 0, 100, int(diversite), step=1)
                        st.markdown("---")
                        st.markdown("#### 📅 Projection dans le temps")
                        mois_projection = st.select_slider("Horizon", options=[1,2,3,6,12], value=3, format_func=lambda x: f"{x} mois")
                        st.markdown("---")
                        st.markdown("#### 💊 Protocole simulé")
                        with_probio  = st.checkbox("Probiotiques oraux", value=True)
                        with_detartr = st.checkbox("Détartrage / surfaçage", value=False)
                        with_nutri   = st.checkbox("Plan nutritionnel suivi", value=False)
                        traj_boost = 1.0 + (0.25 if with_probio else 0) + (0.40 if with_detartr else 0) + (0.20 if with_nutri else 0)

                    with col_results:
                        scores_actuels = calculer_score_systemique(s_mutans, p_gingivalis, diversite)
                        scores_simules = calculer_score_systemique(sim_mutans, sim_paro, sim_div)
                        st.markdown("#### 📊 Comparaison Avant → Après Traitement")
                        h1, h2, h3 = st.columns([2,1,1])
                        h1.markdown("**Pathologie**"); h2.markdown("**Actuel**"); h3.markdown("**Simulé**")
                        st.markdown("<hr style='margin:4px 0 10px 0;border-color:#e5e7eb;'>", unsafe_allow_html=True)
                        for key, act in scores_actuels.items():
                            sim = scores_simules[key]; gain = act["score"]-sim["score"]
                            cn, ca, cs = st.columns([2,1,1])
                            act_c = "#e11d48" if act["level"]=="high" else "#d97706" if act["level"]=="med" else "#16a34a"
                            sim_c = "#e11d48" if sim["level"]=="high" else "#d97706" if sim["level"]=="med" else "#16a34a"
                            arrow = "↓" if gain>0 else "↑" if gain<0 else "→"
                            arrow_c = "#16a34a" if gain>0 else "#e11d48" if gain<0 else "#6b7280"
                            cn.markdown(f"{act['icon']} **{act['label']}**")
                            ca.markdown(f"<span style='color:{act_c};font-weight:700;font-size:1.1rem;'>{act['score']}</span>/100", unsafe_allow_html=True)
                            cs.markdown(f"<span style='color:{sim_c};font-weight:700;font-size:1.1rem;'>{sim['score']}</span><span style='color:{arrow_c};margin-left:6px;'>{arrow} {abs(gain):+.0f}</span>", unsafe_allow_html=True)
                        st.markdown("<hr style='margin:10px 0;border-color:#e5e7eb;'>", unsafe_allow_html=True)
                        avg_act = sum(s["score"] for s in scores_actuels.values())/len(scores_actuels)
                        avg_sim = sum(s["score"] for s in scores_simules.values())/len(scores_simules)
                        gain_global = avg_act - avg_sim
                        gain_pct = round(gain_global/avg_act*100) if avg_act>0 else 0
                        g_c = "#16a34a" if gain_global>0 else "#e11d48" if gain_global<0 else "#6b7280"
                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg,{g_c}15,{g_c}08);border:1.5px solid {g_c}40;border-radius:12px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;">
                            <div><div style="font-size:0.8rem;color:#6b7280;font-weight:600;text-transform:uppercase;">Réduction Risque Global Estimée</div>
                            <div style="font-family:'DM Serif Display',serif;font-size:2rem;color:{g_c};">{"↓" if gain_global>0 else "↑"} {abs(gain_pct)}%</div></div>
                            <div style="text-align:right;"><div style="font-size:0.85rem;color:#374151;">Score moyen : <b>{avg_act:.0f}</b> → <b>{avg_sim:.0f}</b></div>
                            <div style="font-size:0.8rem;color:#9ca3af;margin-top:4px;">Sur {mois_projection} mois avec le protocole sélectionné</div></div>
                        </div>""", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(f"#### 📈 Projection sur {mois_projection} mois")
                        projection_data = {}
                        for key, act in scores_actuels.items():
                            cible=scores_simules[key]["score"]; depart=act["score"]; serie=[]
                            for m in range(mois_projection+1):
                                prog = min(1.0,(m/mois_projection)**(1/traj_boost)) if mois_projection>0 else 1.0
                                serie.append(round(depart+(cible-depart)*prog,1))
                            projection_data[act["label"][:18]] = serie
                        st.line_chart(pd.DataFrame(projection_data, index=[f"M{m}" for m in range(mois_projection+1)]), height=220)
                        st.markdown("<br>", unsafe_allow_html=True)
                        if gain_pct >= 20: st.success(f"✅ Impact thérapeutique significatif — réduction risque de **{gain_pct}%** en {mois_projection} mois.")
                        elif gain_pct >= 5: st.info(f"📉 Impact modéré — amélioration estimée de **{gain_pct}%** en {mois_projection} mois.")
                        elif gain_pct < 0: st.warning("⚠️ Ce scénario représente une dégradation.")
                        else: st.info("Ajustez les sliders pour visualiser l'impact d'un traitement.")
                        if sim_mutans!=s_mutans or sim_paro!=p_gingivalis or sim_div!=diversite:
                            st.markdown("---")
                            st.markdown("**Paramètres simulés vs actuels :**")
                            dc1,dc2,dc3 = st.columns(3)
                            dc1.metric("S. mutans", f"{sim_mutans}%", f"{sim_mutans-s_mutans:+.1f}%", delta_color="inverse")
                            dc2.metric("P. gingivalis", f"{sim_paro}%", f"{sim_paro-p_gingivalis:+.1f}%", delta_color="inverse")
                            dc3.metric("Diversité", f"{sim_div}/100", f"{sim_div-diversite:+.0f}", delta_color="normal")

                with tab4:
                    st.header("📸 Analyse Visuelle de la Cavité Buccale")
                    st.markdown("Uploadez une photo de la bouche du patient pour une analyse IA complémentaire.")
                    if not ANTHROPIC_API_KEY:
                        st.warning("Configurez `ANTHROPIC_API_KEY` dans `st.secrets` pour activer.")
                    else:
                        uploaded = st.file_uploader("Photo bouche patient", type=["jpg","jpeg","png"])
                        if uploaded:
                            img_bytes = uploaded.read()
                            mime = "image/png" if uploaded.name.endswith(".png") else "image/jpeg"
                            col_img, col_res = st.columns([1,2])
                            with col_img: st.image(img_bytes, caption="Photo patient", use_container_width=True)
                            with col_res:
                                with st.spinner("Analyse IA en cours..."): result = analyser_photo_bouche(img_bytes, mime)
                                render_photo_analysis(result)

                with tab5:
                    if not patient["historique"].empty:
                        st.dataframe(patient["historique"], use_container_width=True, hide_index=True)
                        if len(patient["historique"]) > 1:
                            df_g = patient["historique"].copy()
                            df_g.index = range(len(df_g))
                            gc1, gc2 = st.columns(2)
                            with gc1: st.line_chart(df_g[["S. mutans (%)","P. gingiv. (%)"]].astype(float))
                            with gc2:
                                div_col = next((c for c in ["Diversite (%)","Diversité (%)"] if c in df_g.columns), None)
                                if div_col: st.line_chart(df_g[[div_col]].astype(float))
                    st.markdown("---")
                    st.header("Ajouter une Intervention")
                    with st.form("form_ajout"):
                        fa1, fa2, fa3 = st.columns(3)
                        with fa1:
                            nd = st.date_input("Date", date.today())
                            nact = st.selectbox("Intervention", ["Examen Initial","Contrôle Microbiome","Détartrage","Soin Carie","Surfaçage","Probiotiques Prescrits","Autre"])
                        with fa2:
                            ns  = st.number_input("S. mutans (%)", 0.0, 10.0, float(s_mutans), step=0.1)
                            np_ = st.number_input("P. gingivalis (%)", 0.0, 5.0, float(p_gingivalis), step=0.1)
                        with fa3:
                            nd2 = st.number_input("Diversité (%)", 0, 100, int(diversite))
                            st.markdown("<br>", unsafe_allow_html=True)
                            sauver = st.form_submit_button("Sauvegarder", use_container_width=True, type="primary")
                        if sauver:
                            st_val = "Alerte" if ns>3.0 or np_>0.5 or nd2<50 else "Stable"
                            nl = pd.DataFrame({"Date":[nd.strftime("%d/%m/%Y")],"Acte / Test":[nact],"S. mutans (%)":[ns],"P. gingiv. (%)":[np_],"Diversite (%)":[nd2],"Status":[st_val]})
                            st.session_state.patients[st.session_state.patient_sel]["historique"] = pd.concat([patient["historique"],nl], ignore_index=True)
                            st.session_state.patients[st.session_state.patient_sel]["s_mutans"] = ns
                            st.session_state.patients[st.session_state.patient_sel]["p_gingivalis"] = np_
                            st.session_state.patients[st.session_state.patient_sel]["diversite"] = nd2
                            st.success("Sauvegardé.")
                            st.rerun()
                    st.markdown("---")
                    st.header("Rapport PDF Complet")
                    st.markdown("Le rapport inclut les **scores de risque systémique** avec les références scientifiques.")
                    if st.button("Générer le rapport PDF", type="primary"):
                        with st.spinner("Génération..."):
                            pdf = generer_pdf(patient["nom"],r_carieux,r_paro,diversite,patient["historique"],plan,scores_sys)
                        st.download_button(
                            "📥 Télécharger le Rapport Patient Complet (PDF)",
                            data=pdf,
                            file_name=f"OralBiome_{patient['id']}_{patient['nom'].replace(' ','_')}.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )