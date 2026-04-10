import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from PIL import Image
import io
import base64
import json
import requests
import os as _os

# ============================================================
# CONFIGURATION ET CLÉS
# ============================================================
st.set_page_config(page_title="OralBiome", page_icon="🦷", layout="wide")

ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")

# ============================================================
# LOGO LOGIC
# ============================================================
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
    return f'<span style="font-family:DM Serif Display,serif;font-size:1.4rem;color:#1a3a5c;{style}">🦷 OralBiome</span>'

# ============================================================
# DONNÉES CLINIQUES (NHANES)
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
    "mortalite":    {"hazard_ratio":0.63,"ci_95":"(0.49–0.82)", "interpretation":"Chaque hausse de diversité réduit le risque de mortalité de 37%"},
}

# ============================================================
# CSS PERSONNALISÉ
# ============================================================
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display:ital@0;1&display=swap');
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
  .ob-header { background:linear-gradient(135deg,#0a1628 0%,#1a3a5c 60%,#0d2640 100%);border-radius:16px;padding:28px 32px;margin-bottom:24px;border:1px solid rgba(255,255,255,0.08);box-shadow:0 8px 32px rgba(0,0,0,0.3); }
  .ob-header h1 { font-family:'DM Serif Display',serif;color:#fff;margin:0;font-size:2rem; }
  .risk-card { border-radius:12px;padding:20px;margin:8px 0;border:1px solid rgba(0,0,0,0.06);transition:transform 0.2s ease; }
  .risk-high { background:linear-gradient(135deg,#fff1f2,#ffe4e6);border-left:4px solid #e11d48; }
  .risk-med  { background:linear-gradient(135deg,#fffbeb,#fef3c7);border-left:4px solid #d97706; }
  .risk-low  { background:linear-gradient(135deg,#f0fdf4,#dcfce7);border-left:4px solid #16a34a; }
  .systemic-card { background:#fff;border-radius:14px;padding:20px 24px;border:1px solid #e5e7eb;margin:10px 0;box-shadow:0 2px 8px rgba(0,0,0,0.05); }
  .score-ring { display:flex;align-items:center;justify-content:center;width:72px;height:72px;border-radius:50%;font-weight:600;font-size:1.1rem;color:#fff; }
  .score-low  { background:linear-gradient(135deg,#16a34a,#22c55e); }
  .score-med  { background:linear-gradient(135deg,#d97706,#f59e0b); }
  .score-high { background:linear-gradient(135deg,#e11d48,#f43f5e); }
  .patient-header { background:linear-gradient(135deg,#1a3a5c,#2563eb);color:white;padding:24px;border-radius:12px;margin-bottom:20px; }
  .pill-green { display:inline-block;background:#d1fae5;border-radius:20px;padding:5px 14px;margin:3px;font-size:13px;color:#065f46;font-weight:500; }
  .pill-red   { display:inline-block;background:#fee2e2;border-radius:20px;padding:5px 14px;margin:3px;font-size:13px;color:#991b1b;font-weight:500; }
  .reco-card { padding:14px 18px;border-radius:8px;margin:8px 0; }
  .reco-red    { background:#fff5f5;border-left:4px solid #dc3545; }
  .reco-orange { background:#fff8f0;border-left:4px solid #fd7e14; }
  .reco-green  { background:#f0fff4;border-left:4px solid #28a745; }
  .kpi-card { background:#fff;border-radius:16px;padding:22px 24px;border:1px solid #e5e7eb;box-shadow:0 2px 12px rgba(0,0,0,0.06); }
  .kpi-num { font-family:'DM Serif Display',serif;font-size:2.4rem;line-height:1; }
  .alert-card { background:#fff;border-radius:12px;padding:16px 20px;margin:8px 0;border-left:5px solid #e11d48;display:flex;align-items:flex-start;gap:14px; }
  .progress-bar-wrap { background:#f1f5f9;border-radius:8px;height:10px;overflow:hidden;margin:6px 0; }
  .progress-bar-fill { height:100%;border-radius:8px;transition:width 0.4s ease; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOGIQUE MÉTIER ET CALCULS
# ============================================================
SYSTEMIC_CORRELATIONS = {
    "cardiovasculaire": {
        "icon":"❤️","label":"Risque Cardiovasculaire",
        "description":"P. gingivalis favorise l'athérosclérose.",
        "references":"AHA Statement 2012",
        "weight_gingivalis":0.45,"weight_mutans":0.10,"weight_diversity":0.30,"weight_inflammation":0.15,
        "thresholds":{"low":25,"high":55},
        "actions_high":["Bilan CRP ultrasensible","Traitement parodontal prioritaire"],
        "actions_low":["Contrôle microbiome 6 mois"]
    },
    "diabete": {
        "icon":"🩸","label":"Risque Diabète",
        "description":"Dysbiose dégradant la sensibilité insuline.",
        "references":"Lancet 2020",
        "weight_gingivalis":0.35,"weight_mutans":0.20,"weight_diversity":0.35,"weight_inflammation":0.10,
        "thresholds":{"low":25,"high":55},
        "actions_high":["Bilan HbA1c recommandé"],
        "actions_low":["Limiter sucres raffinés"]
    },
    "alzheimer": {
        "icon":"🧠","label":"Risque Neurodégénératif",
        "description":"Gingipaines favorisant les plaques amyloïdes.",
        "references":"Science Advances 2019",
        "weight_gingivalis":0.60,"weight_mutans":0.05,"weight_diversity":0.25,"weight_inflammation":0.10,
        "thresholds":{"low":20,"high":50},
        "actions_high":["Élimination P. gingivalis - Priorité absolue"],
        "actions_low":["Alimentation riche en polyphénols"]
    }
}

def calculer_score_systemique(s_mutans, p_gingivalis, diversite):
    score_gingivalis = min(100, (p_gingivalis / 2.0) * 100)
    score_mutans = min(100, (s_mutans / 8.0) * 100)
    score_diversity_risk = max(0, 100 - diversite)
    score_inflammation = min(100, (score_gingivalis * 0.6 + score_diversity_risk * 0.4))
    results = {}
    for key, corr in SYSTEMIC_CORRELATIONS.items():
        raw_score = (corr["weight_gingivalis"] * score_gingivalis + corr["weight_mutans"] * score_mutans + 
                     corr["weight_diversity"] * score_diversity_risk + corr["weight_inflammation"] * score_inflammation)
        score = round(min(100, max(0, raw_score)))
        level = "low" if score < corr["thresholds"]["low"] else "high" if score > corr["thresholds"]["high"] else "med"
        results[key] = {**corr,"score":score,"level":level, "actions":corr["actions_high"] if level=="high" else corr["actions_low"]}
    return dict(sorted(results.items(), key=lambda x: -x[1]["score"]))

def render_digital_twin(p_gingivalis, s_mutans, diversite):
    redness = min(255, int(p_gingivalis * 100 + 150)) if p_gingivalis > 0.5 else 180
    gum_color = f"rgb({redness}, 100, 120)"
    plaque_opacity = min(0.8, s_mutans / 10)
    recession = min(15, int(p_gingivalis * 5)) 
    svg_html = f"""
    <div style="display: flex; justify-content: center; background: #f8fafc; padding: 40px; border-radius: 20px; border: 1px solid #e2e8f0;">
        <svg width="200" height="250" viewBox="0 0 200 250">
            <path d="M50,50 Q50,20 100,20 Q150,20 150,50 L150,150 Q150,180 100,180 Q50,180 50,150 Z" fill="#ffffff" stroke="#e2e8f0" stroke-width="2"/>
            <path d="M55,60 Q55,40 100,40 Q145,40 145,60 L145,140 Q145,160 100,160 Q55,160 55,140 Z" fill="#fbbf24" fill-opacity="{plaque_opacity}"></path>
            <path d="M20,{150+recession} Q20,{120+recession} 100,{120+recession} Q180,{120+recession} 180,{150+recession} L180,230 Q180,250 100,250 Q20,250 20,230 Z" fill="{gum_color}"></path>
        </svg>
    </div>"""
    st.markdown(svg_html, unsafe_allow_html=True)

# ============================================================
# RÉFÉRENTIELS ET BENCHMARKS
# ============================================================
def nhanes_percentile_rank(score: float, age: int = None) -> dict:
    pct_global = 50
    for p in range(99, 0, -1):
        if p in NHANES_PERCENTILES and score >= NHANES_PERCENTILES[p]:
            pct_global = p; break
    niveau, niveau_label, niveau_color = ("excellent", "Excellent 🌟", "#16a34a") if score >= 69 else ("faible", "Faible 🔴", "#e11d48")
    return {"percentile_global": pct_global, "niveau_label": niveau_label, "niveau_color": niveau_color, "nhanes_n": 8237}

def render_diversity_benchmark(diversite: float, age: int = None, context: str = "patient"):
    bm = nhanes_percentile_rank(diversite, age)
    color = bm["niveau_color"]
    st.markdown(f"""<div style="border:1.5px solid {color}40;border-radius:16px;padding:20px;margin:12px 0;">
    <h3>Score Diversité : {diversite}/100 <span style="color:{color}">{bm['niveau_label']}</span></h3></div>""", unsafe_allow_html=True)

# ============================================================
# PROTECTION DES DONNÉES (RGPD)
# ============================================================
def render_rgpd_banner():
    st.markdown("### 🔒 Protection de vos données — RGPD")
    st.info("Conformité Règlement Général sur la Protection des Données (UE 2016/679)")
    agree1 = st.checkbox("J'accepte que mes données de santé soient traitées par OralBiome.")
    agree2 = st.checkbox("Je confirme être un professionnel de santé habilité ou le patient concerné.")
    col_ref, col_acc = st.columns(2)
    with col_ref:
        if st.button("Refuser"): st.session_state.mode = "choix"; st.rerun()
    with col_acc:
        if st.button("Accepter et continuer", type="primary", disabled=not (agree1 and agree2)):
            st.session_state.rgpd_accepted = True; st.rerun()

# ============================================================
# INITIALISATION DE LA SESSION
# ============================================================
for key, val in [("mode","choix"),("connecte",False),("patient_sel","Jean Dupont"),("vue","dashboard"),("rgpd_accepted",False),("onboarding_done",False),("onboarding_step",1)]:
    if key not in st.session_state: st.session_state[key] = val

if "patients" not in st.session_state:
    df1 = pd.DataFrame({"Date":["12/10/2023"],"Acte":["Initial"],"S. mutans (%)":[4.2],"P. gingiv. (%)":[0.8],"Diversite (%)":[45],"Status":["Alerte"]})
    st.session_state.patients = {"Jean Dupont": {"id":"P001","nom":"Jean Dupont","age":42,"email":"jean@email.com","historique":df1,"s_mutans":4.2,"p_gingivalis":0.3,"diversite":75,"code_patient":"OB-P001"}}
if "anamnes" not in st.session_state: st.session_state.anamnes = {}

# ============================================================
# ROUTAGE PRINCIPAL
# ============================================================
if st.session_state.mode == "choix":
    logo_h = logo_img(width=400)
    st.markdown(f"<div style='text-align:center;'>{logo_h}<h1>OralBiome</h1></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Espace Praticien", use_container_width=True, type="primary"): st.session_state.mode = "praticien"; st.rerun()
    with c2:
        if st.button("Espace Patient", use_container_width=True): st.session_state.mode = "patient"; st.rerun()

elif st.session_state.mode == "patient":
    if not st.session_state.rgpd_accepted: render_rgpd_banner()
    else:
        st.title("Espace Patient")
        if st.button("Retour"): st.session_state.mode = "choix"; st.rerun()

elif st.session_state.mode == "praticien":
    if not st.session_state.connecte:
        if not st.session_state.rgpd_accepted: render_rgpd_banner()
        else:
            st.text_input("Email", key="login_email")
            st.text_input("Mot de passe", type="password", key="login_mdp")
            if st.button("Se connecter", type="primary"): 
                if st.session_state.login_email == "contact@oralbiome.com":
                    st.session_state.connecte = True; st.rerun()
    else:
        # Sidebar Praticien
        st.sidebar.markdown(logo_img(width=150), unsafe_allow_html=True)
        if st.sidebar.button("📊 Dashboard"): st.session_state.vue = "dashboard"; st.rerun()
        if st.sidebar.button("👥 Patients"): st.session_state.vue = "liste"; st.rerun()
        
        # Vue Dossier Patient
        patient = st.session_state.patients[st.session_state.patient_sel]
        s_mutans, p_gingivalis, diversite = patient["s_mutans"], patient["p_gingivalis"], patient["diversite"]
        scores_sys = calculer_score_systemique(s_mutans, p_gingivalis, diversite)

        st.title(f"🦷 Dossier : {patient['nom']}")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Risques Systémiques", "Plan d'Action", "🔬 Simulateur", "📸 Photo IA", "📂 Historique"])

        with tab1:
            st.header("🧬 Risques Systémiques")
            for k, v in scores_sys.items():
                st.write(f"{v['icon']} **{v['label']}** : {v['score']}/100 ({v['level']})")

        with tab3:
            st.markdown("### 🧬 Jumeau Numérique & Simulation")
            cs1, cs2 = st.columns(2)
            with cs1:
                sm = st.slider("Taux S. mutans (%)", 0.0, 10.0, float(s_mutans), key="s_m")
                pg = st.slider("Taux P. gingivalis (%)", 0.0, 5.0, float(p_gingivalis), key="s_p")
            with cs2:
                render_digital_twin(pg, sm, diversite)

        with tab5:
            st.dataframe(patient["historique"], use_container_width=True)