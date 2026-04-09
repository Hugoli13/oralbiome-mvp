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
# LOGO — chargement unique en base64
# ============================================================
import os as _os

def _load_logo_b64(path: str = "image_19.png") -> str:
    """Charge le logo en base64 pour l'embarquer dans le HTML."""
    if _os.path.exists(path):
        with open(path, "rb") as f:
            import base64 as _b64
            return _b64.b64encode(f.read()).decode("utf-8")
    return ""

LOGO_B64 = _load_logo_b64()

def logo_img(width: int = 160, style: str = "") -> str:
    """Retourne une balise <img> avec le logo embarqué, ou le nom texte si absent."""
    if LOGO_B64:
        return f'<img src="data:image/png;base64,{LOGO_B64}" width="{width}" style="display:block;{style}" />'
    return '<span style="font-family:Syne,sans-serif;font-size:1.4rem;color:#00c8b4;font-weight:800;">🦷 OralBiome</span>'

# ============================================================
# MOTEUR BENCHMARK NHANES — Diversité Microbienne
# Source : NHANES 2009-2012 Oral Microbiome (CDC)
#          Vogtmann E et al. Lancet Microbe 2022
#          Chaturvedi AK et al. JAMA Network Open 2025
#          n = 8 237 adultes américains représentatifs
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

NHANES_THRESHOLDS = {
    "excellent": 69.5,  # P85
    "bon":       61.3,  # P75
    "modere":    38.2,  # P25
    "faible":    0,
}

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
        niveau, niveau_label, niveau_color = "excellent", "Excellent 🌟", "#1de986"
    elif score >= NHANES_THRESHOLDS["bon"]:
        niveau, niveau_label, niveau_color = "bon", "Bon 👍", "#3d9eff"
    elif score >= NHANES_THRESHOLDS["modere"]:
        niveau, niveau_label, niveau_color = "modere", "Modéré ⚠️", "#ffb547"
    else:
        niveau, niveau_label, niveau_color = "faible", "Faible 🔴", "#ff3d6a"

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
        benchmark_age = (
            f"Meilleur que **{pct_age}%** des {age_group} ans "
            f"({delta_str} pts vs médiane de votre âge)"
        )

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
    <div style="background:var(--bg-card);
         border:1.5px solid {color}50; border-top:2px solid {color};
         border-radius:18px; padding:22px 26px; margin:12px 0;
         box-shadow:0 0 28px {color}18, 0 4px 20px rgba(0,0,0,0.5);">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
            <div>
                <div style="font-family:'Space Mono',monospace;font-size:0.63rem;color:#7a8fa8;
                     font-weight:400;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:6px;">
                    Score Diversité Microbienne
                </div>
                <div style="font-family:'Syne',sans-serif;font-size:3rem;color:{color};line-height:1;font-weight:800;">
                    {diversite}<span style="font-size:1.1rem;color:#3d5068;">/100</span>
                </div>
                <span style="background:{color}20;color:{color};font-weight:600;padding:4px 14px;
                     border-radius:20px;font-size:0.78rem;font-family:'Space Mono',monospace;
                     letter-spacing:0.04em;margin-top:8px;display:inline-block;">
                    {bm['niveau_label']}
                </span>
            </div>
            <div style="text-align:right;">
                <div style="font-family:'Space Mono',monospace;font-size:0.63rem;color:#7a8fa8;
                     margin-bottom:4px;text-transform:uppercase;letter-spacing:0.1em;">vs population générale</div>
                <div style="font-family:'Syne',sans-serif;font-size:2.4rem;color:{color};line-height:1;font-weight:800;">
                    Top {100 - pct}%
                </div>
                <div style="font-family:'Space Mono',monospace;font-size:0.68rem;color:#3d5068;margin-top:4px;">
                    sur {bm['nhanes_n']:,} patients NHANES
                </div>
            </div>
        </div>
        <div style="margin-top:16px;padding-top:14px;border-top:1px solid {color}20;">
            <div style="font-size:0.88rem;color:#e8f0fe;margin-bottom:4px;">🌍 {bm['benchmark_global']}</div>
            {"" if not bm['benchmark_age'] else f'<div style="font-size:0.88rem;color:#e8f0fe;">👤 {bm["benchmark_age"]}</div>'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Barre percentile visuelle
    bar_segs = [(25,"rgba(255,61,106,0.4)"),(25,"rgba(255,181,71,0.4)"),(25,"rgba(61,158,255,0.4)"),(15,"rgba(29,233,134,0.4)"),(10,"rgba(29,233,134,0.7)")]
    bar_html = '<div style="display:flex;border-radius:8px;overflow:hidden;height:8px;margin:10px 0 2px 0;border:1px solid rgba(255,255,255,0.06);">'
    for w, bg in bar_segs:
        bar_html += f'<div style="flex:{w};background:{bg};"></div>'
    bar_html += "</div>"
    bar_html += f'<div style="position:relative;height:22px;">'
    bar_html += f'<div style="position:absolute;left:{pct}%;transform:translateX(-50%);">'
    bar_html += f'<div style="width:2px;height:10px;background:{color};margin:0 auto;box-shadow:0 0 6px {color};"></div>'
    bar_html += f'<div style="font-family:\'Space Mono\',monospace;font-size:0.65rem;font-weight:700;color:{color};white-space:nowrap;transform:translateX(-40%);margin-top:2px;">P{pct} — vous</div>'
    bar_html += "</div></div>"
    st.markdown(bar_html, unsafe_allow_html=True)

    leg_cols = st.columns(5)
    for col, (lbl, c) in zip(leg_cols, [
        ("< P25\nFaible","#ff3d6a"),("P25–50\nModéré","#ffb547"),
        ("P50–75\nBon","#3d9eff"),("P75–85\nExcellent","#1de986"),
        ("> P90\nTop 10%","#00c8b4")
    ]):
        col.markdown(f"<div style='text-align:center;font-family:Space Mono,monospace;font-size:0.62rem;color:{c};font-weight:600;line-height:1.4;'>{lbl}</div>",
                     unsafe_allow_html=True)

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
            <div style="background:var(--bg-surface);border:1px solid var(--border-dim);border-radius:12px;padding:14px;text-align:center;">
                <div style="font-size:1.3rem;">{icon}</div>
                <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:0.88rem;margin:6px 0;color:#e8f0fe;">{label}</div>
                <div style="font-family:'Syne',sans-serif;font-size:1.5rem;color:#ff3d6a;font-weight:800;">−{d['difference']} pts</div>
                <div style="font-family:'Space Mono',monospace;font-size:0.68rem;color:#7a8fa8;">sains: {d['mean_sain']} vs malades: {d['mean_malade']}</div>
                <div style="font-family:'Space Mono',monospace;font-size:0.68rem;color:#1de986;margin-top:4px;font-weight:700;">p={d['p_value']}</div>
            </div>""", unsafe_allow_html=True)
        mort = NHANES_CLINICAL["mortalite"]
        st.markdown(f"""
        <div style="background:rgba(29,233,134,0.06);border:1px solid rgba(29,233,134,0.2);
             border-radius:12px;padding:14px 18px;margin-top:10px;">
            <b style="color:#1de986;">💚 Mortalité toutes causes</b> — HR={mort['hazard_ratio']} {mort['ci_95']}<br>
            <span style="font-size:0.85rem;color:#e8f0fe;">{mort['interpretation']}</span><br>
            <span style="font-family:'Space Mono',monospace;font-size:0.68rem;color:#3d5068;">Shen et al. J Clin Periodontol 2024 · 7 055 adultes · suivi 9 ans</span>
        </div>""", unsafe_allow_html=True)

# ============================================================
# CSS — HEALTH-TECH DARK PREMIUM
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300&display=swap');

/* ── VARIABLES ── */
:root {
  --bg-void:       #050a12;
  --bg-deep:       #080e1a;
  --bg-card:       #0c1525;
  --bg-surface:    #111d30;
  --bg-elevated:   #162238;
  --border-dim:    rgba(255,255,255,0.06);
  --border-glow:   rgba(0,200,180,0.25);
  --teal:          #00c8b4;
  --teal-dim:      rgba(0,200,180,0.12);
  --teal-glow:     rgba(0,200,180,0.35);
  --blue-neon:     #3d9eff;
  --red-vital:     #ff3d6a;
  --amber-warn:    #ffb547;
  --green-ok:      #1de986;
  --text-primary:  #e8f0fe;
  --text-secondary:#7a8fa8;
  --text-muted:    #3d5068;
  --font-display:  'Syne', sans-serif;
  --font-body:     'IBM Plex Sans', sans-serif;
  --font-mono:     'Space Mono', monospace;
  --radius-sm:     6px;
  --radius-md:     12px;
  --radius-lg:     18px;
  --radius-xl:     24px;
  --shadow-card:   0 4px 24px rgba(0,0,0,0.5), 0 1px 0 rgba(255,255,255,0.04) inset;
  --shadow-glow:   0 0 30px rgba(0,200,180,0.15), 0 4px 24px rgba(0,0,0,0.5);
}

/* ── BASE ── */
html, body, [class*="css"], .stApp {
  font-family: var(--font-body) !important;
  background: var(--bg-void) !important;
  color: var(--text-primary) !important;
}

/* Grille de points en fond */
.stApp::before {
  content: '';
  position: fixed; inset: 0;
  background-image:
    radial-gradient(circle at 20% 20%, rgba(0,200,180,0.04) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(61,158,255,0.04) 0%, transparent 50%),
    radial-gradient(rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 28px 28px;
  pointer-events: none; z-index: 0;
}

/* ── HEADER ── */
.ob-header {
  background: linear-gradient(145deg, #080e1a 0%, #0c1a2e 50%, #091520 100%);
  border: 1px solid var(--border-dim);
  border-top: 2px solid rgba(0,200,180,0.4);
  border-radius: var(--radius-xl);
  padding: 32px 36px; margin-bottom: 28px;
  box-shadow: var(--shadow-glow);
  position: relative; overflow: hidden;
}
.ob-header::before {
  content: ''; position: absolute; top: -60px; right: -60px;
  width: 220px; height: 220px;
  background: radial-gradient(circle, rgba(0,200,180,0.09) 0%, transparent 70%);
  pointer-events: none;
}
.ob-header::after {
  content: ''; position: absolute; bottom: -40px; left: 8%;
  width: 320px; height: 110px;
  background: radial-gradient(ellipse, rgba(61,158,255,0.07) 0%, transparent 70%);
  pointer-events: none;
}
.ob-header h1 {
  font-family: var(--font-display) !important;
  font-size: 2rem !important; font-weight: 800 !important;
  color: var(--text-primary) !important; letter-spacing: -0.03em !important; margin: 0 !important;
}
.ob-header p {
  font-family: var(--font-mono) !important;
  font-size: 0.72rem !important; color: var(--teal) !important;
  letter-spacing: 0.1em !important; margin: 8px 0 0 0 !important; text-transform: uppercase;
}

/* ── RISK CARDS ── */
.risk-card {
  border-radius: var(--radius-md); padding: 20px; margin: 8px 0;
  border: 1px solid var(--border-dim);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  position: relative; overflow: hidden;
}
.risk-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
.risk-low  { background: linear-gradient(135deg, rgba(29,233,134,0.07), rgba(29,233,134,0.02)); border-left: 4px solid #1de986; border-color: rgba(29,233,134,0.25); }
.risk-med  { background: linear-gradient(135deg, rgba(255,181,71,0.07), rgba(255,181,71,0.02));  border-left: 4px solid #ffb547; border-color: rgba(255,181,71,0.25); }
.risk-high { background: linear-gradient(135deg, rgba(255,61,106,0.07), rgba(255,61,106,0.02));  border-left: 4px solid #ff3d6a; border-color: rgba(255,61,106,0.25); }

/* ── SYSTEMIC CARD ── */
.systemic-card {
  background: var(--bg-surface);
  border-radius: var(--radius-md); padding: 20px 24px;
  border: 1px solid var(--border-dim); margin: 10px 0;
  box-shadow: var(--shadow-card); transition: border-color 0.2s ease;
}
.systemic-card:hover { border-color: var(--border-glow); }
.systemic-title { font-family: var(--font-display); font-size: 1.1rem; color: var(--text-primary); margin: 0 0 8px 0; font-weight: 700; }

/* ── SCORE RINGS ── */
.score-ring {
  display: flex; align-items: center; justify-content: center;
  width: 72px; height: 72px; border-radius: 50%;
  font-family: var(--font-display); font-weight: 700; font-size: 1.1rem;
  color: #050a12; flex-shrink: 0;
}
.score-low  { background: #1de986; box-shadow: 0 0 22px rgba(29,233,134,0.45); }
.score-med  { background: #ffb547; box-shadow: 0 0 22px rgba(255,181,71,0.45); }
.score-high { background: #ff3d6a; box-shadow: 0 0 22px rgba(255,61,106,0.45); }

/* ── PHOTO UPLOAD ── */
.photo-upload-zone {
  border: 2px dashed rgba(0,200,180,0.25); border-radius: var(--radius-lg);
  padding: 48px; text-align: center;
  background: linear-gradient(135deg, rgba(0,200,180,0.03), rgba(61,158,255,0.03));
  cursor: pointer; transition: all 0.3s ease;
}
.photo-upload-zone:hover { border-color: var(--teal); background: rgba(0,200,180,0.06); box-shadow: 0 0 30px rgba(0,200,180,0.1); }

/* ── FINDING BADGES ── */
.finding-badge {
  display: inline-block; padding: 4px 12px; border-radius: 20px;
  font-family: var(--font-mono); font-size: 0.72rem; font-weight: 400; margin: 3px;
}
.finding-alert { background: rgba(255,61,106,0.15);  color: #ff8fa8; border: 1px solid rgba(255,61,106,0.3); }
.finding-warn  { background: rgba(255,181,71,0.15);  color: #ffd080; border: 1px solid rgba(255,181,71,0.3); }
.finding-ok    { background: rgba(29,233,134,0.15);  color: #7af7c0; border: 1px solid rgba(29,233,134,0.3); }

/* ── PILLS NUTRITION ── */
.pill-green { display:inline-block; background:rgba(29,233,134,0.1); border:1px solid rgba(29,233,134,0.25); border-radius:20px; padding:5px 14px; margin:3px; font-size:13px; color:#7af7c0; font-weight:500; }
.pill-red   { display:inline-block; background:rgba(255,61,106,0.1); border:1px solid rgba(255,61,106,0.25); border-radius:20px; padding:5px 14px; margin:3px; font-size:13px; color:#ff8fa8; font-weight:500; }

/* ── RECO CARDS ── */
.reco-card { padding:14px 18px; border-radius:var(--radius-sm); margin:8px 0; }
.reco-red    { background:rgba(255,61,106,0.07); border-left:4px solid #ff3d6a; }
.reco-orange { background:rgba(255,181,71,0.07); border-left:4px solid #ffb547; }
.reco-green  { background:rgba(29,233,134,0.07); border-left:4px solid #1de986; }

/* ── PATIENT HEADER ── */
.patient-header {
  background: linear-gradient(145deg, var(--bg-deep), var(--bg-surface));
  border: 1px solid var(--border-dim); border-top: 2px solid rgba(0,200,180,0.4);
  color: var(--text-primary); padding: 24px; border-radius: var(--radius-lg);
  margin-bottom: 20px; box-shadow: var(--shadow-glow);
}

/* ── METRIC BOX ── */
.metric-box {
  background: var(--bg-card); border: 1px solid var(--border-dim);
  border-radius: var(--radius-md); padding: 16px; text-align: center;
  box-shadow: var(--shadow-card);
}
.metric-val { font-family: var(--font-display); font-size: 1.8rem; color: var(--teal); font-weight: 800; }
.metric-lbl { font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-secondary); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.08em; }

/* ── KPI CARDS DASHBOARD ── */
.kpi-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg); padding: 22px 24px;
  border: 1px solid var(--border-dim); box-shadow: var(--shadow-card);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  position: relative; overflow: hidden;
  animation: slideUp 0.35s ease both;
}
.kpi-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--teal), transparent); opacity: 0.5;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-glow); border-color: var(--border-glow); }
.kpi-num   { font-family: var(--font-display); font-size: 2.4rem; line-height: 1; font-weight: 800; letter-spacing: -0.03em; }
.kpi-lbl   { font-family: var(--font-mono); font-size: 0.72rem; color: var(--text-secondary); margin-top: 4px; font-weight: 400; text-transform: uppercase; letter-spacing: 0.08em; }
.kpi-delta { font-size: 0.8rem; margin-top: 6px; font-weight: 600; font-family: var(--font-body); }
.kpi-red   { color: #ff3d6a; }
.kpi-green { color: #1de986; }
.kpi-blue  { color: #3d9eff; }
.kpi-amber { color: #ffb547; }
.kpi-teal  { color: #00c8b4; }

/* ── ALERTES ── */
.alert-card {
  background: var(--bg-card); border-radius: var(--radius-md); padding: 16px 20px; margin: 8px 0;
  border: 1px solid rgba(255,61,106,0.2); border-left: 5px solid #ff3d6a;
  box-shadow: 0 2px 8px rgba(255,61,106,0.08);
  display: flex; align-items: flex-start; gap: 14px;
  transition: box-shadow 0.2s ease;
}
.alert-card:hover { box-shadow: 0 4px 20px rgba(255,61,106,0.18); }
.alert-card.warn { border-color: rgba(255,181,71,0.2); border-left-color: #ffb547; box-shadow: 0 2px 8px rgba(255,181,71,0.08); }
.alert-card.warn:hover { box-shadow: 0 4px 20px rgba(255,181,71,0.18); }
.alert-card.info { border-color: rgba(61,158,255,0.2); border-left-color: #3d9eff; box-shadow: 0 2px 8px rgba(61,158,255,0.08); }
.alert-icon  { font-size: 1.5rem; flex-shrink: 0; margin-top: 2px; }
.alert-body  { flex: 1; }
.alert-title { font-family: var(--font-body); font-weight: 600; font-size: 0.95rem; color: var(--text-primary); margin: 0 0 3px 0; }
.alert-desc  { font-size: 0.85rem; color: var(--text-secondary); margin: 0; }
.alert-meta  { font-family: var(--font-mono); font-size: 0.72rem; color: var(--teal); margin-top: 5px; }

/* ── PROGRESS BARS ── */
.progress-bar-wrap { background: var(--bg-surface); border-radius: 8px; height: 8px; overflow: hidden; margin: 8px 0; border: 1px solid var(--border-dim); }
.progress-bar-fill { height: 100%; border-radius: 8px; transition: width 0.4s ease; }

/* ── STREAMLIT OVERRIDES ── */
.stApp, .main, .block-container { background: var(--bg-void) !important; }
section[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
  background: var(--bg-deep) !important; border-right: 1px solid var(--border-dim) !important;
}

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stPasswordInput > div > div > input,
.stDateInput > div > div > input {
  background: var(--bg-surface) !important; border: 1px solid var(--border-dim) !important;
  color: var(--text-primary) !important; border-radius: var(--radius-sm) !important;
  font-family: var(--font-body) !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
  border-color: var(--teal) !important; box-shadow: 0 0 0 2px rgba(0,200,180,0.15) !important;
}

.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #00c8b4, #00a896) !important;
  color: #050a12 !important; border: none !important;
  font-family: var(--font-display) !important; font-weight: 700 !important;
  letter-spacing: 0.02em !important; border-radius: var(--radius-sm) !important;
  box-shadow: 0 0 20px rgba(0,200,180,0.3) !important; transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover { transform: translateY(-1px) !important; box-shadow: 0 0 32px rgba(0,200,180,0.55) !important; }

.stButton > button[kind="secondary"],
.stButton > button:not([kind]) {
  background: var(--bg-surface) !important; border: 1px solid var(--border-dim) !important;
  color: var(--text-secondary) !important; font-family: var(--font-body) !important;
  border-radius: var(--radius-sm) !important; transition: all 0.2s ease !important;
}
.stButton > button:hover { border-color: var(--teal) !important; color: var(--teal) !important; }

.stDownloadButton > button {
  background: linear-gradient(135deg, rgba(0,200,180,0.15), rgba(0,200,180,0.08)) !important;
  border: 1px solid rgba(0,200,180,0.35) !important; color: var(--teal) !important;
  font-family: var(--font-display) !important; font-weight: 700 !important;
  border-radius: var(--radius-sm) !important;
}

[data-testid="stMetric"] {
  background: var(--bg-card) !important; border: 1px solid var(--border-dim) !important;
  border-radius: var(--radius-md) !important; padding: 16px !important;
  box-shadow: var(--shadow-card) !important;
}
[data-testid="stMetricLabel"] {
  font-family: var(--font-mono) !important; font-size: 0.65rem !important;
  letter-spacing: 0.1em !important; text-transform: uppercase !important;
  color: var(--text-secondary) !important;
}
[data-testid="stMetricValue"] { font-family: var(--font-display) !important; font-weight: 800 !important; color: var(--text-primary) !important; }

.stDataFrame, [data-testid="stDataFrameResizable"] { border: 1px solid var(--border-dim) !important; border-radius: var(--radius-md) !important; overflow: hidden !important; }

.stTabs [data-baseweb="tab-list"] {
  background: var(--bg-surface) !important; border-radius: var(--radius-md) !important;
  border: 1px solid var(--border-dim) !important; gap: 4px !important; padding: 6px !important;
}
.stTabs [data-baseweb="tab"] {
  font-family: var(--font-body) !important; font-size: 0.82rem !important;
  color: var(--text-secondary) !important; border-radius: var(--radius-sm) !important;
  background: transparent !important; transition: all 0.15s ease !important;
}
.stTabs [aria-selected="true"] { background: var(--bg-elevated) !important; color: var(--teal) !important; box-shadow: 0 0 14px rgba(0,200,180,0.2) !important; }

.streamlit-expanderHeader {
  background: var(--bg-surface) !important; border: 1px solid var(--border-dim) !important;
  border-radius: var(--radius-sm) !important; color: var(--text-primary) !important;
  font-family: var(--font-body) !important;
}

.stSlider > div > div > div > div { background: var(--teal) !important; }
.stCheckbox > label { color: var(--text-primary) !important; font-family: var(--font-body) !important; }
.stSelectbox [data-baseweb="select"] > div { background: var(--bg-surface) !important; border-color: var(--border-dim) !important; color: var(--text-primary) !important; }

h1, h2, h3, h4 { font-family: var(--font-display) !important; color: var(--text-primary) !important; letter-spacing: -0.02em !important; }
p, li, label, .stMarkdown { font-family: var(--font-body) !important; color: var(--text-primary) !important; }
.stCaption, caption { font-family: var(--font-mono) !important; font-size: 0.7rem !important; color: var(--text-muted) !important; }

code { background: rgba(0,200,180,0.1) !important; color: var(--teal) !important; border: 1px solid rgba(0,200,180,0.2) !important; border-radius: 4px !important; font-family: var(--font-mono) !important; padding: 2px 7px !important; font-size: 0.82em !important; }
hr { border-color: var(--border-dim) !important; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--bg-elevated); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--teal); }

.stSuccess { background: rgba(29,233,134,0.08) !important; border: 1px solid rgba(29,233,134,0.25) !important; color: #7af7c0 !important; border-radius: var(--radius-md) !important; }
.stWarning { background: rgba(255,181,71,0.08) !important; border: 1px solid rgba(255,181,71,0.25) !important; color: #ffd080 !important; border-radius: var(--radius-md) !important; }
.stError   { background: rgba(255,61,106,0.08) !important; border: 1px solid rgba(255,61,106,0.25) !important; color: #ff8fa8 !important; border-radius: var(--radius-md) !important; }
.stInfo    { background: rgba(61,158,255,0.08) !important; border: 1px solid rgba(61,158,255,0.25) !important; color: #90c8ff !important; border-radius: var(--radius-md) !important; }

.stForm { background: var(--bg-card) !important; border: 1px solid var(--border-dim) !important; border-radius: var(--radius-lg) !important; padding: 20px !important; }

@keyframes slideUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulseGlow { 0%,100% { box-shadow: 0 0 10px rgba(0,200,180,0.2); } 50% { box-shadow: 0 0 28px rgba(0,200,180,0.55); } }
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
        color = "#1de986" if score >= 70 else "#ffb547" if score >= 45 else "#ff3d6a"
        st.markdown(f"""
        <div style="text-align:center; background:var(--bg-surface);
             border: 2px solid {color}60; border-top: 2px solid {color};
             border-radius: 16px; padding: 24px;
             box-shadow: 0 0 24px {color}20;">
            <div style="font-family:'Syne',sans-serif; font-size: 3rem; color: {color}; line-height:1; font-weight:800;">
                {score}
            </div>
            <div style="font-family:'Space Mono',monospace; font-size: 0.65rem; color: #7a8fa8; margin-top: 4px; text-transform:uppercase; letter-spacing:0.1em;">Score santé visuelle</div>
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
                    <div style="font-family:'Syne',sans-serif; font-weight:700; font-size:0.9rem; color:#e8f0fe;">{icon} {f.get('zone', 'N/A')}</div>
                    <div style="font-size:0.85rem; margin-top:4px; color:#7a8fa8;">{f.get('observation', '')}</div>
                    <div style="font-size:0.78rem; margin-top:6px; color:#3d5068; font-style:italic;">{f.get('detail', '')}</div>
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
        DARK    = colors.HexColor('#050a12')
        TEAL    = colors.HexColor('#00c8b4')
        SURFACE = colors.HexColor('#111d30')
        CARD    = colors.HexColor('#0c1525')
        GREEN   = colors.HexColor('#1de986')
        RED     = colors.HexColor('#ff3d6a')
        AMBER   = colors.HexColor('#ffb547')
        LIGHT_TEAL = colors.HexColor('#0c2a28')

        title_style = ParagraphStyle('Title', fontSize=18, textColor=TEAL,
                                     alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=4)
        sub_style = ParagraphStyle('Sub', fontSize=10, textColor=colors.HexColor('#7a8fa8'),
                                   alignment=TA_CENTER, fontName='Helvetica', spaceAfter=6)
        h1_style = ParagraphStyle('H1', fontSize=13, textColor=TEAL,
                                  fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=4)
        h2_style = ParagraphStyle('H2', fontSize=11, textColor=colors.HexColor('#e8f0fe'),
                                  fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=3)
        body_style = ParagraphStyle('Body', fontSize=10, fontName='Helvetica', spaceAfter=3, leading=14,
                                    textColor=colors.HexColor('#e8f0fe'))
        italic_style = ParagraphStyle('Italic', fontSize=9, fontName='Helvetica-Oblique',
                                      textColor=colors.HexColor('#7a8fa8'), spaceAfter=4)
        small_style = ParagraphStyle('Small', fontSize=8, fontName='Helvetica',
                                     textColor=colors.HexColor('#3d5068'), alignment=TA_CENTER)

        elems = []

        # EN-TÊTE
        header_data = [[Paragraph("OralBiome - Rapport Patient Complet", title_style)],
                       [Paragraph("Microbiome Oral Predictif + Risques Systemiques | Rapport Personnalise", sub_style)]]
        header_table = Table(header_data, colWidths=[180*mm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), DARK),
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
            ('BACKGROUND', (0,0), (-1,-1), SURFACE),
            ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elems.append(info_table)
        elems.append(Spacer(1, 6*mm))

        # RÉSULTATS MICROBIOME
        elems.append(Paragraph("Resultats de l'Analyse Microbiome", h1_style))
        elems.append(HRFlowable(width="100%", thickness=1, color=TEAL))
        res_data = [
            [Paragraph("<b>Risque Carieux</b>", body_style),
             Paragraph(f"<font color='{'#ff3d6a' if r_carieux=='Eleve' else '#1de986'}'><b>{r_carieux}</b></font>", body_style)],
            [Paragraph("<b>Risque Parodontal</b>", body_style),
             Paragraph(f"<font color='{'#ff3d6a' if r_paro=='Eleve' else '#1de986'}'><b>{r_paro}</b></font>", body_style)],
            [Paragraph("<b>Score de Diversite</b>", body_style),
             Paragraph(f"<b>{diversite}/100</b> (optimal > 65)", body_style)],
        ]
        res_table = Table(res_data, colWidths=[90*mm, 90*mm])
        res_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), CARD),
            ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('LINEBELOW', (0,0), (-1,-2), 0.5, SURFACE),
        ]))
        elems.append(res_table)
        elems.append(Spacer(1, 6*mm))

        # SCORES SYSTÉMIQUES
        if scores_systemiques:
            elems.append(Paragraph("Scores de Risque Systemique", h1_style))
            elems.append(HRFlowable(width="100%", thickness=1, color=TEAL))
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
                ('BACKGROUND', (0,0), (-1,0), DARK),
                ('TEXTCOLOR', (0,0), (-1,0), TEAL),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [CARD, SURFACE]),
                ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#162238')),
            ]))
            elems.append(sys_table)
            elems.append(Spacer(1, 6*mm))

        # PLAN D'ACTION
        if plan["priorites"]:
            elems.append(Paragraph("Plan d'Action - Priorites", h1_style))
            elems.append(HRFlowable(width="100%", thickness=1, color=TEAL))
            for i, p in enumerate(plan["priorites"]):
                urgence = p["urgence"]
                badge = "URGENCE ELEVEE" if urgence=="Elevee" else "MODEREE" if urgence=="Moderee" else "ROUTINE"
                elems.append(Paragraph(f"Priorite {i+1} — {p['titre']} [{badge}]", h2_style))
                for action in p["actions"]:
                    elems.append(Paragraph(f"• {action}", body_style))
                elems.append(Spacer(1, 3*mm))

        # NUTRITION
        elems.append(Paragraph("Plan Nutritionnel", h1_style))
        elems.append(HRFlowable(width="100%", thickness=1, color=TEAL))
        if plan["aliments_favoriser"] or plan["aliments_eviter"]:
            max_items = max(len(plan["aliments_favoriser"]), len(plan["aliments_eviter"]))
            nutr_rows = []
            for i in range(max_items):
                fav = plan["aliments_favoriser"][i] if i < len(plan["aliments_favoriser"]) else ""
                evi = plan["aliments_eviter"][i] if i < len(plan["aliments_eviter"]) else ""
                nutr_rows.append([Paragraph(f"+ {fav}", body_style), Paragraph(f"- {evi}", body_style)])
            nutr_table = Table(nutr_rows, colWidths=[90*mm, 90*mm])
            nutr_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#0a1a10')),
                ('BACKGROUND', (1,0), (1,-1), colors.HexColor('#1a0a10')),
                ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('LINEBELOW', (0,0), (-1,-2), 0.3, SURFACE),
            ]))
            elems.append(nutr_table)

        # PIED DE PAGE
        elems.append(Spacer(1, 8*mm))
        footer_data = [
            [Paragraph("Ce rapport est fourni a titre preventif et informatif. Ne constitue pas un diagnostic medical.", small_style)],
            [Paragraph("OralBiome - Health Intelligence Platform | contact@oralbiome.com", small_style)]
        ]
        footer_table = Table(footer_data, colWidths=[180*mm])
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), SURFACE),
            ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elems.append(footer_table)

        doc.build(elems)
        return buffer.getvalue()

    except ImportError:
        return b"Installez reportlab : pip install reportlab"


# ============================================================
# MOTEUR DASHBOARD & ALERTES
# ============================================================
from datetime import datetime, timedelta

def calculer_alertes(patients: dict) -> list:
    """
    Génère la liste des alertes actives pour tous les patients.
    Types : urgence clinique, rappel de contrôle, dégradation, première visite manquante.
    """
    alertes = []
    today = date.today()

    for nom, p in patients.items():
        s_mutans = p["s_mutans"]
        p_gingivalis = p["p_gingivalis"]
        diversite = p["diversite"]
        hist = p["historique"]

        # --- Alertes cliniques critiques ---
        if p_gingivalis > 1.5:
            alertes.append({
                "type": "urgence", "patient": nom, "id": p["id"],
                "titre": f"P. gingivalis critique ({p_gingivalis}%)",
                "desc": "Taux de P. gingivalis très élevé — risque parodontal sévère et risque systémique élevé (CV, Alzheimer).",
                "priorite": 1, "icone": "🚨",
                "action": "Consultation parodontale urgente"
            })
        elif s_mutans > 6.0:
            alertes.append({
                "type": "urgence", "patient": nom, "id": p["id"],
                "titre": f"S. mutans critique ({s_mutans}%)",
                "desc": "Taux de S. mutans très élevé — caries actives probables, intervention immédiate recommandée.",
                "priorite": 1, "icone": "🚨",
                "action": "Bilan carie et soin urgents"
            })

        # --- Rappels de contrôle ---
        if not hist.empty:
            try:
                derniere_date_str = hist.iloc[-1]["Date"]
                derniere_date = datetime.strptime(derniere_date_str, "%d/%m/%Y").date()
                en_alerte = s_mutans > 3.0 or p_gingivalis > 0.5 or diversite < 50
                delai_semaines = 8 if en_alerte and (p_gingivalis > 1.5 or s_mutans > 6.0) else 12 if en_alerte else 24
                delai_jours = delai_semaines * 7
                date_prochain = derniere_date + timedelta(days=delai_jours)
                jours_restants = (date_prochain - today).days

                if jours_restants < 0:
                    alertes.append({
                        "type": "urgence", "patient": nom, "id": p["id"],
                        "titre": f"Contrôle en retard de {abs(jours_restants)} jours",
                        "desc": f"Dernier examen le {derniere_date_str}. Contrôle prévu tous les {delai_semaines} semaines.",
                        "priorite": 2, "icone": "⏰",
                        "action": "Planifier rendez-vous"
                    })
                elif jours_restants <= 14:
                    alertes.append({
                        "type": "warn", "patient": nom, "id": p["id"],
                        "titre": f"Contrôle dans {jours_restants} jours",
                        "desc": f"Rappel : prochain examen recommandé le {date_prochain.strftime('%d/%m/%Y')}.",
                        "priorite": 3, "icone": "📅",
                        "action": "Envoyer rappel au patient"
                    })
            except Exception:
                pass

        # --- Dégradation détectée (comparaison 2 dernières visites) ---
        if len(hist) >= 2:
            try:
                avant = hist.iloc[-2]
                apres = hist.iloc[-1]
                dg_mutans = float(apres["S. mutans (%)"]) - float(avant["S. mutans (%)"])
                dg_paro   = float(apres["P. gingiv. (%)"]) - float(avant["P. gingiv. (%)"])
                dg_div    = float(avant.get("Diversite (%)", avant.get("Diversité (%)", 70))) - \
                            float(apres.get("Diversite (%)", apres.get("Diversité (%)", 70)))
                if dg_paro > 0.3:
                    alertes.append({
                        "type": "warn", "patient": nom, "id": p["id"],
                        "titre": f"Dégradation parodontale (+{dg_paro:.1f}% P. gingivalis)",
                        "desc": "Augmentation significative de P. gingivalis entre deux visites.",
                        "priorite": 2, "icone": "📈",
                        "action": "Adapter le protocole de traitement"
                    })
                if dg_mutans > 1.0:
                    alertes.append({
                        "type": "warn", "patient": nom, "id": p["id"],
                        "titre": f"Dégradation cariogène (+{dg_mutans:.1f}% S. mutans)",
                        "desc": "Augmentation de S. mutans entre deux visites — revoir l'hygiène et l'alimentation.",
                        "priorite": 3, "icone": "📈",
                        "action": "Revoir le plan nutritionnel"
                    })
            except Exception:
                pass

        # --- Patients sans analyse depuis longtemps ---
        if hist.empty:
            alertes.append({
                "type": "info", "patient": nom, "id": p["id"],
                "titre": "Aucune analyse enregistrée",
                "desc": "Ce patient n'a pas encore d'analyse microbiome dans le dossier.",
                "priorite": 4, "icone": "📋",
                "action": "Planifier un examen initial"
            })

    return sorted(alertes, key=lambda x: x["priorite"])


def calculer_stats_cabinet(patients: dict) -> dict:
    """Calcule les KPIs globaux du cabinet."""
    total = len(patients)
    if total == 0:
        return {}

    alertes_count = sum(1 for p in patients.values()
                        if p["s_mutans"] > 3.0 or p["p_gingivalis"] > 0.5 or p["diversite"] < 50)
    stables_count = total - alertes_count

    avg_mutans    = sum(p["s_mutans"] for p in patients.values()) / total
    avg_paro      = sum(p["p_gingivalis"] for p in patients.values()) / total
    avg_diversite = sum(p["diversite"] for p in patients.values()) / total

    risque_cardio_eleve = sum(
        1 for p in patients.values()
        if calculer_score_systemique(p["s_mutans"], p["p_gingivalis"], p["diversite"])["cardiovasculaire"]["level"] == "high"
    )
    risque_alz_eleve = sum(
        1 for p in patients.values()
        if calculer_score_systemique(p["s_mutans"], p["p_gingivalis"], p["diversite"])["alzheimer"]["level"] == "high"
    )

    total_visites = sum(len(p["historique"]) for p in patients.values())

    return {
        "total": total,
        "alertes": alertes_count,
        "stables": stables_count,
        "pct_alerte": round(alertes_count / total * 100),
        "avg_mutans": round(avg_mutans, 2),
        "avg_paro": round(avg_paro, 2),
        "avg_diversite": round(avg_diversite, 1),
        "risque_cardio_eleve": risque_cardio_eleve,
        "risque_alz_eleve": risque_alz_eleve,
        "total_visites": total_visites,
    }


def render_dashboard(patients: dict):
    """Affiche le dashboard analytics complet du cabinet."""
    stats = calculer_stats_cabinet(patients)
    alertes = calculer_alertes(patients)

    logo_h = logo_img(width=140, style="margin-bottom:8px;filter:brightness(0) invert(1);opacity:0.85;")
    st.markdown(f"""
    <div class="ob-header">
        {logo_h}
        <h1>📊 Dashboard Cabinet</h1>
        <p>● Vue analytique en temps réel · Alertes · KPIs · Tendances</p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs ligne 1
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-num kpi-blue">{stats['total']}</div>
            <div class="kpi-lbl">Patients Total</div>
            <div class="kpi-delta kpi-teal">📂 {stats['total_visites']} visites</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-num kpi-red">{stats['alertes']}</div>
            <div class="kpi-lbl">En Alerte</div>
            <div class="kpi-delta kpi-red">⚠️ {stats['pct_alerte']}% du cabinet</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-num kpi-green">{stats['stables']}</div>
            <div class="kpi-lbl">Stables</div>
            <div class="kpi-delta kpi-green">✅ {100 - stats['pct_alerte']}% du cabinet</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-num kpi-amber">{stats['risque_cardio_eleve']}</div>
            <div class="kpi-lbl">Risque Cardio Élevé</div>
            <div class="kpi-delta kpi-amber">❤️ Suivi systémique requis</div>
        </div>""", unsafe_allow_html=True)
    with k5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-num kpi-amber">{stats['risque_alz_eleve']}</div>
            <div class="kpi-lbl">Risque Neuro Élevé</div>
            <div class="kpi-delta kpi-amber">🧠 P. gingivalis critique</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Ligne 2 : moyennes cabinet
    st.markdown("#### 🧬 Moyennes Microbiome du Cabinet")
    col_m1, col_m2, col_m3 = st.columns(3)

    def bar(val, max_val, color):
        pct = min(100, val / max_val * 100)
        return f"""<div class="progress-bar-wrap">
            <div class="progress-bar-fill" style="width:{pct:.0f}%; background:{color}; box-shadow:0 0 8px {color}80;"></div>
        </div>"""

    with col_m1:
        color = "#ff3d6a" if stats["avg_mutans"] > 3 else "#1de986"
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#7a8fa8;text-transform:uppercase;letter-spacing:0.1em;">S. MUTANS MOYEN</div>
            <div class="kpi-num" style="color:{color};">{stats['avg_mutans']}%</div>
            <div style="font-family:'Space Mono',monospace;font-size:0.68rem;color:#3d5068;">Normal &lt; 3%</div>
            {bar(stats["avg_mutans"], 8, color)}
        </div>""", unsafe_allow_html=True)
    with col_m2:
        color = "#ff3d6a" if stats["avg_paro"] > 0.5 else "#1de986"
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#7a8fa8;text-transform:uppercase;letter-spacing:0.1em;">P. GINGIVALIS MOYEN</div>
            <div class="kpi-num" style="color:{color};">{stats['avg_paro']}%</div>
            <div style="font-family:'Space Mono',monospace;font-size:0.68rem;color:#3d5068;">Normal &lt; 0.5%</div>
            {bar(stats["avg_paro"], 2, color)}
        </div>""", unsafe_allow_html=True)
    with col_m3:
        color = "#1de986" if stats["avg_diversite"] >= 65 else "#ffb547" if stats["avg_diversite"] >= 50 else "#ff3d6a"
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#7a8fa8;text-transform:uppercase;letter-spacing:0.1em;">DIVERSITÉ MOYENNE</div>
            <div class="kpi-num" style="color:{color};">{stats['avg_diversite']}/100</div>
            <div style="font-family:'Space Mono',monospace;font-size:0.68rem;color:#3d5068;">Optimal &gt; 65</div>
            {bar(stats["avg_diversite"], 100, color)}
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Ligne 3 : alertes + tableau patients
    col_alerts, col_patients = st.columns([1, 2])

    with col_alerts:
        nb_alertes_actives = len(alertes)
        st.markdown(f"#### 🔔 Alertes Actives `{nb_alertes_actives}`")
        if not alertes:
            st.success("✅ Aucune alerte active — tous les patients sont dans les paramètres.")
        else:
            for a in alertes[:8]:  # max 8 dans la vue dashboard
                css = "alert-card" if a["type"] == "urgence" else "alert-card warn" if a["type"] == "warn" else "alert-card info"
                st.markdown(f"""
                <div class="{css}">
                    <div class="alert-icon">{a['icone']}</div>
                    <div class="alert-body">
                        <div class="alert-title">{a['patient']} — {a['titre']}</div>
                        <div class="alert-desc">{a['desc']}</div>
                        <div class="alert-meta">👉 {a['action']}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

    with col_patients:
        st.markdown("#### 👥 État du Cabinet")
        rows = []
        for nom, p in patients.items():
            ea = p["s_mutans"] > 3.0 or p["p_gingivalis"] > 0.5 or p["diversite"] < 50
            sys_scores = calculer_score_systemique(p["s_mutans"], p["p_gingivalis"], p["diversite"])
            top_sys = max(sys_scores.items(), key=lambda x: x[1]["score"])
            nb_alertes_p = sum(1 for a in alertes if a["patient"] == nom)
            rows.append({
                "Nom": nom,
                "Statut": "🔴 Alerte" if ea else "🟢 Stable",
                "S. mutans": f"{p['s_mutans']}%",
                "P. gingivalis": f"{p['p_gingivalis']}%",
                "Diversité": f"{p['diversite']}/100",
                "Top Risque": f"{top_sys[1]['icon']} {top_sys[1]['score']}/100",
                "Alertes": nb_alertes_p if nb_alertes_p else "—"
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Graphique évolution diversité tous patients
        st.markdown("#### 📈 Tendance Diversité Microbienne")
        chart_data = {}
        for nom, p in patients.items():
            hist = p["historique"]
            if len(hist) >= 2:
                div_col = next((c for c in ["Diversite (%)", "Diversité (%)"] if c in hist.columns), None)
                if div_col:
                    chart_data[nom] = hist[div_col].astype(float).tolist()
        if chart_data:
            max_len = max(len(v) for v in chart_data.values())
            df_chart = pd.DataFrame(
                {k: v + [None] * (max_len - len(v)) for k, v in chart_data.items()}
            )
            st.line_chart(df_chart)
        else:
            st.caption("Pas assez d'historique pour afficher les tendances.")

    st.markdown("---")

    # ── Tableau complet des alertes
    st.markdown(f"#### 🗂️ Toutes les Alertes ({len(alertes)})")
    if alertes:
        filtre_type = st.selectbox("Filtrer par type", ["Toutes", "🚨 Urgences", "⚠️ Avertissements", "ℹ️ Infos"],
                                   label_visibility="collapsed")
        filtre_map = {"Toutes": None, "🚨 Urgences": "urgence", "⚠️ Avertissements": "warn", "ℹ️ Infos": "info"}
        alertes_filtrees = [a for a in alertes if filtre_map[filtre_type] is None or a["type"] == filtre_map[filtre_type]]

        for a in alertes_filtrees:
            css = "alert-card" if a["type"] == "urgence" else "alert-card warn" if a["type"] == "warn" else "alert-card info"
            col_a, col_btn = st.columns([5, 1])
            with col_a:
                st.markdown(f"""
                <div class="{css}">
                    <div class="alert-icon">{a['icone']}</div>
                    <div class="alert-body">
                        <div class="alert-title">{a['id']} · {a['patient']} — {a['titre']}</div>
                        <div class="alert-desc">{a['desc']}</div>
                        <div class="alert-meta">👉 {a['action']}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with col_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Ouvrir →", key=f"alerte_btn_{a['patient']}_{a['titre'][:10]}"):
                    st.session_state.patient_sel = a["patient"]
                    st.session_state.vue = "dossier"
                    st.rerun()
    else:
        st.success("✅ Aucune alerte active.")


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
    ("vue", "dashboard"), ("patient_connecte", None)
]:
    if key not in st.session_state:
        st.session_state[key] = val

if "patients" not in st.session_state:
    st.session_state.patients = donnees_initiales()


# ============================================================
# ÉCRAN DE CHOIX
# ============================================================
if st.session_state.mode == "choix":
    logo_html = logo_img(width=180, style="margin-bottom:10px;filter:brightness(0) invert(1);opacity:0.9;")
    st.markdown(f"""
    <div class="ob-header">
        {logo_html}
        <h1 style="margin-top:6px;">Oral<span style="color:#00c8b4;">Biome</span></h1>
        <p>● Microbiome Oral Prédictif — Prévention dentaire et systémique personnalisée par l'IA</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown("""
        <div class="kpi-card" style="padding:28px 24px;margin-bottom:12px;">
            <div style="font-size:2rem;margin-bottom:10px;">🩺</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;color:#e8f0fe;margin-bottom:8px;">Praticien</div>
            <div style="font-family:'IBM Plex Sans',sans-serif;font-size:0.85rem;color:#7a8fa8;line-height:1.6;">
                Tableau de bord complet, gestion des dossiers, analyses systémiques et rapports PDF.
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button("Connexion Praticien", use_container_width=True, type="primary"):
            st.session_state.mode = "praticien"; st.rerun()
    with col2:
        st.markdown("""
        <div class="kpi-card" style="padding:28px 24px;margin-bottom:12px;">
            <div style="font-size:2rem;margin-bottom:10px;">🧑</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;color:#e8f0fe;margin-bottom:8px;">Patient</div>
            <div style="font-family:'IBM Plex Sans',sans-serif;font-size:0.85rem;color:#7a8fa8;line-height:1.6;">
                Votre rapport personnalisé, plan nutritionnel, risques systémiques et historique.
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button("Accès Patient", use_container_width=True):
            st.session_state.mode = "patient"; st.rerun()
    with col3:
        st.markdown("""
        <div class="kpi-card" style="padding:28px 24px;margin-bottom:12px;">
            <div style="font-size:2rem;margin-bottom:10px;">ℹ️</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;color:#e8f0fe;margin-bottom:8px;">À propos</div>
            <div style="font-family:'IBM Plex Sans',sans-serif;font-size:0.85rem;color:#7a8fa8;line-height:1.6;">
                OralBiome corrèle votre microbiote oral avec vos risques cardiovasculaires, diabète, Alzheimer et plus.
            </div>
            <div style="font-family:'Space Mono',monospace;font-size:0.72rem;color:#00c8b4;margin-top:12px;font-weight:700;">contact@oralbiome.com</div>
        </div>""", unsafe_allow_html=True)


# ============================================================
# PORTAIL PATIENT
# ============================================================
elif st.session_state.mode == "patient":

    if st.session_state.patient_connecte is None:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if LOGO_B64:
                st.markdown(f"<div style='text-align:center;'>{logo_img(width=160)}</div>", unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align:center;margin-top:10px;">
                <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:#e8f0fe;">Espace Patient</div>
                <div style="font-family:'Space Mono',monospace;font-size:0.68rem;color:#7a8fa8;margin-top:4px;text-transform:uppercase;letter-spacing:0.1em;">Consultez votre rapport personnalisé</div>
            </div>""", unsafe_allow_html=True)
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

        if LOGO_B64:
            st.sidebar.markdown(
                f"<div style='text-align:center;padding:6px 0;'>{logo_img(width=120)}</div>",
                unsafe_allow_html=True
            )
        st.sidebar.markdown(f"### 👋 {patient['nom'].split()[0]}")
        st.sidebar.markdown(f"Code : `{patient['code_patient']}`")
        status_color = "#ff3d6a" if en_alerte else "#1de986"
        st.sidebar.markdown(f"<span style='color:{status_color};font-weight:700;'>{'🔴 En alerte' if en_alerte else '🟢 Équilibré'}</span>", unsafe_allow_html=True)
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
            <h2 style="margin-top:4px;font-family:'Syne',sans-serif;font-weight:800;">Bonjour {patient['nom']} !</h2>
            <p style="font-family:'Space Mono',monospace;font-size:0.72rem;color:#00c8b4;text-transform:uppercase;letter-spacing:0.08em;">● Rapport microbiome oral personnalisé · {date.today().strftime('%d/%m/%Y')}</p>
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
            st.markdown("---")
            st.markdown("#### 🌍 Votre Diversité Microbienne vs la Population")
            render_diversity_benchmark(diversite, age=patient.get("age"), context="patient")
            if not patient["historique"].empty:
                st.markdown("---")
                st.markdown("#### 📅 Historique de vos analyses")
                st.dataframe(patient["historique"], use_container_width=True, hide_index=True)

        with tp2:
            st.header("🧬 Risques Systémiques")
            st.markdown("*Corrélations établies entre votre microbiote oral et vos risques de santé généraux, basées sur la littérature scientifique peer-reviewed.*")
            st.markdown("---")
            for key, data in scores_sys.items():
                score = data["score"]
                level = data["level"]
                score_css = "score-high" if level == "high" else "score-med" if level == "med" else "score-low"
                col_ring, col_content = st.columns([1, 6])
                with col_ring:
                    st.markdown(f"<div class='score-ring {score_css}'>{score}</div>", unsafe_allow_html=True)
                with col_content:
                    st.markdown(f"""
                    <div class='systemic-card'>
                        <div class='systemic-title'>{data['icon']} {data['label']}</div>
                        <div style="font-size:0.85rem; color:#7a8fa8; margin-bottom:8px;">{data['description']}</div>
                        <div style="font-family:'Space Mono',monospace;font-size:0.72rem; color:#3d5068; margin-bottom:8px;"><em>Réf : {data['references']}</em></div>
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
            if LOGO_B64:
                st.markdown(f"<div style='text-align:center;'>{logo_img(width=160)}</div>", unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align:center;margin-top:10px;">
                <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;color:#e8f0fe;">Oral<span style="color:#00c8b4;">Biome</span></div>
                <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#7a8fa8;margin-top:4px;text-transform:uppercase;letter-spacing:0.12em;">Portail Praticien</div>
            </div>""", unsafe_allow_html=True)
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
        if LOGO_B64:
            st.sidebar.markdown(
                f"<div style='text-align:center;padding:8px 0 4px 0;'>{logo_img(width=140)}</div>",
                unsafe_allow_html=True
            )
        st.sidebar.markdown("""
        <div style="padding:4px 8px 8px 8px;">
            <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;color:#e8f0fe;">Oral<span style="color:#00c8b4;">Biome</span></div>
            <div style="font-family:'Space Mono',monospace;font-size:0.58rem;color:#7a8fa8;letter-spacing:0.1em;text-transform:uppercase;">Health Intelligence</div>
        </div>""", unsafe_allow_html=True)
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
                         if p["s_mutans"] > 3.0 or p["p_gingivalis"] > 0.5 or p["diversite"] < 50)
        nb_alertes_actives = len(calculer_alertes(st.session_state.patients))
        ms1, ms2, ms3 = st.sidebar.columns(3)
        ms1.metric("Patients", nb_patients)
        ms2.metric("Alertes", nb_alertes)
        ms3.metric("🔔", nb_alertes_actives)
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

        # VUE DASHBOARD
        if st.session_state.vue == "dashboard":
            render_dashboard(st.session_state.patients)

        # VUE LISTE
        elif st.session_state.vue == "liste":
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
                badge_color = "#ff3d6a" if en_alerte else "#1de986"
                st.markdown(f"""
                <div class="ob-header">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
                        <div>
                            <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#00c8b4;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:6px;">● Dossier Patient · {patient['id']}</div>
                            <h1 style="font-size:1.7rem;margin:0;">🦷 {patient['nom']}</h1>
                            <p style="font-family:'IBM Plex Sans',sans-serif;color:#7a8fa8;font-size:0.85rem;margin:4px 0 0 0;">Âge : {patient['age']} ans · {patient['email']} · Code : <code>{patient.get('code_patient','')}</code></p>
                        </div>
                        <div style="padding-top:8px;">
                            <span style="background:{badge_color}20;color:{badge_color};font-family:'Syne',sans-serif;font-weight:700;padding:8px 18px;border-radius:24px;font-size:0.9rem;border:1px solid {badge_color}50;">{badge}</span>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

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

                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "🧬 Risques Systémiques", "🚨 Plan d'Action", "🔬 Simulateur", "📸 Analyse Photo", "📂 Historique & PDF"
                ])

                with tab1:
                    st.header("🧬 Corrélations Microbiome → Risques Systémiques")
                    st.caption("Scores calculés selon les pondérations de la littérature scientifique peer-reviewed.")

                    # Benchmark NHANES diversité
                    st.markdown("#### 🌍 Benchmark Diversité — Population NHANES (n=8 237)")
                    render_diversity_benchmark(diversite, age=patient.get("age"), context="praticien")
                    st.markdown("---")

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
                    # ══════════════════════════════════════════
                    # SIMULATEUR "ET SI ?" — VERSION MAXIMALE
                    # ══════════════════════════════════════════
                    st.markdown("""
                    <div class="ob-header">
                        <h1 style="font-size:1.5rem;">🔬 Simulateur d'Impact Thérapeutique</h1>
                        <p>● Ajustez les biomarqueurs et visualisez l'impact en temps réel sur tous les risques systémiques</p>
                    </div>
                    """, unsafe_allow_html=True)

                    col_sliders, col_results = st.columns([1, 2])

                    with col_sliders:
                        st.markdown("#### ⚙️ Ajuster les biomarqueurs")
                        st.caption("Faites glisser pour simuler l'effet d'un traitement")

                        sim_mutans = st.slider(
                            "S. mutans (%)", 0.0, 10.0, float(s_mutans), step=0.1,
                            help="Normal < 3% | Bactérie cariogène principale"
                        )
                        sim_paro = st.slider(
                            "P. gingivalis (%)", 0.0, 3.0, float(p_gingivalis), step=0.1,
                            help="Normal < 0.5% | Pathogène parodontal majeur"
                        )
                        sim_div = st.slider(
                            "Diversité microbienne", 0, 100, int(diversite), step=1,
                            help="Optimal > 65 | Richesse de la flore orale"
                        )

                        st.markdown("---")

                        # Projection temporelle
                        st.markdown("#### 📅 Projection dans le temps")
                        mois_projection = st.select_slider(
                            "Horizon de projection",
                            options=[1, 2, 3, 6, 12],
                            value=3,
                            format_func=lambda x: f"{x} mois"
                        )

                        # Calcul trajectoire : amélioration progressive vers la cible simulée
                        st.markdown("---")
                        st.markdown("#### 💊 Protocole simulé")
                        with_probio  = st.checkbox("Probiotiques oraux", value=True)
                        with_detartr = st.checkbox("Détartrage / surfaçage", value=False)
                        with_nutri   = st.checkbox("Plan nutritionnel suivi", value=False)

                        # Modificateurs de trajectoire
                        traj_boost = 1.0
                        traj_boost += 0.25 if with_probio else 0
                        traj_boost += 0.40 if with_detartr else 0
                        traj_boost += 0.20 if with_nutri else 0

                    with col_results:
                        scores_actuels  = calculer_score_systemique(s_mutans, p_gingivalis, diversite)
                        scores_simules  = calculer_score_systemique(sim_mutans, sim_paro, sim_div)

                        # ── Avant / Après côte à côte
                        st.markdown("#### 📊 Comparaison Avant → Après Traitement")

                        header_c1, header_c2, header_c3 = st.columns([2, 1, 1])
                        header_c1.markdown("**Pathologie**")
                        header_c2.markdown("**Actuel**")
                        header_c3.markdown("**Simulé**")
                        st.markdown("<hr style='margin:4px 0 10px 0;border-color:rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

                        total_gain = 0
                        for key, act in scores_actuels.items():
                            sim = scores_simules[key]
                            gain = act["score"] - sim["score"]
                            total_gain += gain

                            col_name, col_act, col_sim = st.columns([2, 1, 1])

                            act_color = "#ff3d6a" if act["level"]=="high" else "#ffb547" if act["level"]=="med" else "#1de986"
                            sim_color = "#ff3d6a" if sim["level"]=="high" else "#ffb547" if sim["level"]=="med" else "#1de986"
                            arrow = "↓" if gain > 0 else "↑" if gain < 0 else "→"
                            arrow_color = "#1de986" if gain > 0 else "#ff3d6a" if gain < 0 else "#7a8fa8"

                            col_name.markdown(f"{act['icon']} **{act['label']}**")
                            col_act.markdown(
                                f"<span style='color:{act_color};font-family:Syne,sans-serif;font-weight:700;font-size:1.1rem;'>{act['score']}</span>/100",
                                unsafe_allow_html=True
                            )
                            col_sim.markdown(
                                f"<span style='color:{sim_color};font-family:Syne,sans-serif;font-weight:700;font-size:1.1rem;'>{sim['score']}</span>"
                                f"<span style='color:{arrow_color};font-weight:600;font-size:0.9rem;margin-left:6px;'>"
                                f"{arrow} {abs(gain):+.0f}</span>",
                                unsafe_allow_html=True
                            )

                        st.markdown("<hr style='margin:10px 0;border-color:rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

                        # Score global
                        avg_act = sum(s["score"] for s in scores_actuels.values()) / len(scores_actuels)
                        avg_sim = sum(s["score"] for s in scores_simules.values()) / len(scores_simules)
                        gain_global = avg_act - avg_sim
                        gain_pct    = round(gain_global / avg_act * 100) if avg_act > 0 else 0

                        g_color = "#1de986" if gain_global > 0 else "#ff3d6a" if gain_global < 0 else "#7a8fa8"
                        st.markdown(f"""
                        <div style="background:var(--bg-card);
                             border:1.5px solid {g_color}40; border-top:2px solid {g_color};
                             border-radius:14px;padding:16px 20px;
                             display:flex;justify-content:space-between;align-items:center;
                             box-shadow:0 0 20px {g_color}15;">
                            <div>
                                <div style="font-family:'Space Mono',monospace;font-size:0.63rem;color:#7a8fa8;text-transform:uppercase;letter-spacing:0.1em;">
                                    Réduction Risque Global Estimée
                                </div>
                                <div style="font-family:'Syne',sans-serif;font-size:2.2rem;color:{g_color};font-weight:800;">
                                    {"↓" if gain_global>0 else "↑"} {abs(gain_pct)}%
                                </div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:0.85rem;color:#e8f0fe;">
                                    Score moyen : <b>{avg_act:.0f}</b> → <b>{avg_sim:.0f}</b>
                                </div>
                                <div style="font-family:'Space Mono',monospace;font-size:0.72rem;color:#3d5068;margin-top:4px;">
                                    Sur {mois_projection} mois avec le protocole sélectionné
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)

                        # ── Projection temporelle mois par mois
                        st.markdown(f"#### 📈 Projection sur {mois_projection} mois")
                        st.caption(f"Trajectoire d'amélioration estimée avec boost protocole ×{traj_boost:.1f}")

                        import math
                        projection_data = {}
                        mois_labels = list(range(0, mois_projection + 1))

                        for key, act in scores_actuels.items():
                            cible = scores_simules[key]["score"]
                            depart = act["score"]
                            serie = []
                            for m in mois_labels:
                                if depart == cible:
                                    serie.append(depart)
                                else:
                                    # Courbe logarithmique d'amélioration avec boost protocole
                                    progression = min(1.0, (m / mois_projection) ** (1 / traj_boost))
                                    val = depart + (cible - depart) * progression
                                    serie.append(round(val, 1))
                            projection_data[act["label"][:18]] = serie

                        df_proj = pd.DataFrame(projection_data, index=[f"M{m}" for m in mois_labels])
                        st.line_chart(df_proj, height=220)

                        # ── Message clinique final
                        st.markdown("<br>", unsafe_allow_html=True)
                        if gain_pct >= 20:
                            st.success(f"✅ **Impact thérapeutique significatif** — Ce protocole pourrait réduire le risque systémique global de **{gain_pct}%** en {mois_projection} mois.")
                        elif gain_pct >= 5:
                            st.info(f"📉 **Impact modéré** — Amélioration estimée de **{gain_pct}%** sur les risques systémiques en {mois_projection} mois.")
                        elif gain_pct < 0:
                            st.warning("⚠️ Les valeurs simulées sont supérieures aux valeurs actuelles — ce scénario représente une dégradation.")
                        else:
                            st.info("Les valeurs simulées sont proches des valeurs actuelles. Ajustez les sliders pour visualiser l'impact d'un traitement.")

                        if sim_mutans != s_mutans or sim_paro != p_gingivalis or sim_div != diversite:
                            st.markdown("---")
                            st.markdown("**Paramètres simulés vs actuels :**")
                            delta_c1, delta_c2, delta_c3 = st.columns(3)
                            delta_c1.metric("S. mutans", f"{sim_mutans}%", f"{sim_mutans - s_mutans:+.1f}%", delta_color="inverse")
                            delta_c2.metric("P. gingivalis", f"{sim_paro}%", f"{sim_paro - p_gingivalis:+.1f}%", delta_color="inverse")
                            delta_c3.metric("Diversité", f"{sim_div}/100", f"{sim_div - diversite:+.0f}", delta_color="normal")

                with tab4:
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

                with tab5:
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