import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import io, base64, json, requests, os, hashlib, random, math

st.set_page_config(page_title="OralBiome", page_icon="🦷", layout="wide")
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")

# ── Logo ──────────────────────────────────────────────────────────────────────
def _load_logo_b64(path="image_19.png"):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = _load_logo_b64()

def logo_img(width=400, style=""):
    if LOGO_B64:
        return f'<img src="data:image/png;base64,{LOGO_B64}" width="{width}" style="display:block;{style}" />'
    return '<span style="font-family:DM Serif Display,serif;font-size:1.4rem;color:#1a3a5c;">🦷 OralBiome</span>'

# ── I18N ──────────────────────────────────────────────────────────────────────
I18N = {
    "fr": {
        "flag": "🇫🇷", "lang_name": "Français",
        "home_login": "Se connecter", "home_access": "Accéder à mon espace",
        "metric_caries": "Risque Carieux", "metric_paro": "Risque Parodontal",
        "metric_diversity": "Diversité Microbienne",
        "metric_high": "Élevé", "metric_low": "Faible",
        "pat_hello": "Bonjour", "pat_logout": "Se déconnecter", "pat_back": "Retour accueil",
        "pat_next_ctrl": "Prochain contrôle", "pat_weeks": "semaines",
        "pat_profile": "📊 Mon Profil", "pat_systemic": "🧬 Risques Systémiques",
        "pat_photo": "📸 Analyse Photo", "pat_actions": "🚨 Mes Actions",
        "pat_nutrition": "🥗 Nutrition & Probiotiques", "pat_anamnes": "📋 Mon Anamnèse",
        "pat_share": "📤 Partager", "pat_twin": "🦷 Mon Twin Dentaire",
        "pat_pdf": "📥 Rapport PDF", "pat_observance": "📈 Mon Observance",
        "pat_iot": "📱 Brosse Connectée", "pat_privisite": "🏥 Pré-Visite",
        "prat_connect": "Se connecter", "prat_back": "Retour à l'accueil",
        "prat_disconnect": "Déconnecter", "prat_email": "Email Professionnel",
        "prat_password": "Mot de passe", "prat_login_title": "Portail Praticien",
        "dash_title": "Dashboard Cabinet", "dash_total": "Patients Total",
        "dash_alerts": "En Alerte", "dash_stable": "Stables",
        "dash_cardio": "Risque Cardio Élevé", "dash_neuro": "Risque Neuro Élevé",
        "notif_empty": "Aucune notification", "notif_mark_read": "Tout marquer comme lu",
        "dm_on": "🌙 Mode sombre", "dm_off": "☀️ Mode clair",
    },
    "en": {
        "flag": "🇬🇧", "lang_name": "English",
        "home_login": "Log in", "home_access": "Access my space",
        "metric_caries": "Caries Risk", "metric_paro": "Periodontal Risk",
        "metric_diversity": "Microbial Diversity",
        "metric_high": "High", "metric_low": "Low",
        "pat_hello": "Hello", "pat_logout": "Log out", "pat_back": "Back to home",
        "pat_next_ctrl": "Next check-up", "pat_weeks": "weeks",
        "pat_profile": "📊 My Profile", "pat_systemic": "🧬 Systemic Risks",
        "pat_photo": "📸 Photo Analysis", "pat_actions": "🚨 My Actions",
        "pat_nutrition": "🥗 Nutrition & Probiotics", "pat_anamnes": "📋 My Anamnesis",
        "pat_share": "📤 Share", "pat_twin": "🦷 My Dental Twin",
        "pat_pdf": "📥 PDF Report", "pat_observance": "📈 My Compliance",
        "pat_iot": "📱 Smart Brush", "pat_privisite": "🏥 Pre-Visit",
        "prat_connect": "Log in", "prat_back": "Back to home",
        "prat_disconnect": "Log out", "prat_email": "Professional Email",
        "prat_password": "Password", "prat_login_title": "Practitioner Portal",
        "dash_title": "Cabinet Dashboard", "dash_total": "Total Patients",
        "dash_alerts": "Alerts", "dash_stable": "Stable",
        "dash_cardio": "High Cardio Risk", "dash_neuro": "High Neuro Risk",
        "notif_empty": "No notifications", "notif_mark_read": "Mark all as read",
        "dm_on": "🌙 Dark mode", "dm_off": "☀️ Light mode",
    },
    "nl": {
        "flag": "🇧🇪", "lang_name": "Nederlands",
        "home_login": "Inloggen", "home_access": "Toegang tot mijn ruimte",
        "metric_caries": "Cariësrisico", "metric_paro": "Parodontaal Risico",
        "metric_diversity": "Microbiële Diversiteit",
        "metric_high": "Hoog", "metric_low": "Laag",
        "pat_hello": "Hallo", "pat_logout": "Uitloggen", "pat_back": "Terug naar home",
        "pat_next_ctrl": "Volgende controle", "pat_weeks": "weken",
        "pat_profile": "📊 Mijn Profiel", "pat_systemic": "🧬 Systemische Risico's",
        "pat_photo": "📸 Foto Analyse", "pat_actions": "🚨 Mijn Acties",
        "pat_nutrition": "🥗 Voeding & Probiotica", "pat_anamnes": "📋 Mijn Anamnese",
        "pat_share": "📤 Delen", "pat_twin": "🦷 Mijn Tand Twin",
        "pat_pdf": "📥 PDF Rapport", "pat_observance": "📈 Mijn Naleving",
        "pat_iot": "📱 Slimme Borstel", "pat_privisite": "🏥 Pre-Bezoek",
        "prat_connect": "Inloggen", "prat_back": "Terug naar home",
        "prat_disconnect": "Uitloggen", "prat_email": "Professioneel E-mail",
        "prat_password": "Wachtwoord", "prat_login_title": "Practitioner Portaal",
        "dash_title": "Kabinet Dashboard", "dash_total": "Totaal Patiënten",
        "dash_alerts": "Meldingen", "dash_stable": "Stabiel",
        "dash_cardio": "Hoog Cardio Risico", "dash_neuro": "Hoog Neuro Risico",
        "notif_empty": "Geen meldingen", "notif_mark_read": "Alles als gelezen markeren",
        "dm_on": "🌙 Donkere modus", "dm_off": "☀️ Lichte modus",
    },
}

def t(key):
    return I18N.get(st.session_state.get("lang", "fr"), I18N["fr"]).get(key, key)

def render_lang_selector():
    langs = {f"{I18N[k]['flag']} {I18N[k]['lang_name']}": k for k in I18N}
    current = st.session_state.get("lang", "fr")
    cur_label = next(lbl for lbl, k in langs.items() if k == current)
    chosen = st.sidebar.selectbox("🌐", list(langs.keys()),
                                   index=list(langs.keys()).index(cur_label),
                                   label_visibility="collapsed")
    if langs[chosen] != current:
        st.session_state.lang = langs[chosen]
        st.rerun()

def render_dark_mode_toggle():
    is_dark = st.session_state.get("dark_mode", False)
    if st.sidebar.button(t("dm_off") if is_dark else t("dm_on"),
                         use_container_width=True, key="dm_toggle"):
        st.session_state.dark_mode = not is_dark
        st.rerun()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display:ital@0;1&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
.ob-header{background:linear-gradient(135deg,#0a1628 0%,#1a3a5c 60%,#0d2640 100%);border-radius:16px;padding:28px 32px;margin-bottom:24px;border:1px solid rgba(255,255,255,0.08);box-shadow:0 8px 32px rgba(0,0,0,0.3);}
.ob-header h1{font-family:'DM Serif Display',serif;color:#fff;margin:0;font-size:2rem;}
.ob-header p{color:rgba(255,255,255,0.6);margin:4px 0 0 0;font-size:0.9rem;}
.risk-card{border-radius:12px;padding:20px;margin:8px 0;border:1px solid rgba(0,0,0,0.06);}
.risk-low{background:linear-gradient(135deg,#f0fdf4,#dcfce7);border-left:4px solid #16a34a;}
.risk-med{background:linear-gradient(135deg,#fffbeb,#fef3c7);border-left:4px solid #d97706;}
.risk-high{background:linear-gradient(135deg,#fff1f2,#ffe4e6);border-left:4px solid #e11d48;}
.systemic-card{background:#fff;border-radius:14px;padding:20px 24px;border:1px solid #e5e7eb;margin:10px 0;box-shadow:0 2px 8px rgba(0,0,0,0.05);}
.systemic-title{font-family:'DM Serif Display',serif;font-size:1.1rem;color:#1a3a5c;margin:0 0 8px 0;}
.score-ring{display:flex;align-items:center;justify-content:center;width:72px;height:72px;border-radius:50%;font-weight:600;font-size:1.1rem;color:#fff;flex-shrink:0;}
.score-low{background:linear-gradient(135deg,#16a34a,#22c55e);}
.score-med{background:linear-gradient(135deg,#d97706,#f59e0b);}
.score-high{background:linear-gradient(135deg,#e11d48,#f43f5e);}
.finding-badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:0.78rem;font-weight:500;margin:3px;}
.finding-alert{background:#fee2e2;color:#991b1b;}
.finding-warn{background:#fef3c7;color:#92400e;}
.finding-ok{background:#dcfce7;color:#166534;}
.pill-green{display:inline-block;background:#d1fae5;border-radius:20px;padding:5px 14px;margin:3px;font-size:13px;color:#065f46;font-weight:500;}
.pill-red{display:inline-block;background:#fee2e2;border-radius:20px;padding:5px 14px;margin:3px;font-size:13px;color:#991b1b;font-weight:500;}
.reco-card{padding:14px 18px;border-radius:8px;margin:8px 0;}
.reco-red{background:#fff5f5;border-left:4px solid #dc3545;}
.reco-orange{background:#fff8f0;border-left:4px solid #fd7e14;}
.reco-green{background:#f0fff4;border-left:4px solid #28a745;}
.patient-header{background:linear-gradient(135deg,#1a3a5c,#2563eb);color:white;padding:24px;border-radius:12px;margin-bottom:20px;}
.kpi-card{background:#fff;border-radius:16px;padding:22px 24px;border:1px solid #e5e7eb;box-shadow:0 2px 12px rgba(0,0,0,0.06);}
.kpi-num{font-family:'DM Serif Display',serif;font-size:2.4rem;line-height:1;}
.kpi-lbl{font-size:0.82rem;color:#6b7280;margin-top:4px;font-weight:500;text-transform:uppercase;letter-spacing:0.04em;}
.kpi-delta{font-size:0.8rem;margin-top:6px;font-weight:600;}
.kpi-red{color:#e11d48;} .kpi-green{color:#16a34a;} .kpi-blue{color:#2563eb;} .kpi-amber{color:#d97706;}
.alert-card{background:#fff;border-radius:12px;padding:16px 20px;margin:8px 0;border:1px solid #fee2e2;border-left:5px solid #e11d48;display:flex;align-items:flex-start;gap:14px;}
.alert-card.warn{border-color:#fef3c7;border-left-color:#d97706;}
.alert-card.info{border-color:#dbeafe;border-left-color:#2563eb;}
.alert-icon{font-size:1.5rem;flex-shrink:0;margin-top:2px;}
.alert-body{flex:1;}
.alert-title{font-weight:600;font-size:0.95rem;color:#111827;margin:0 0 3px 0;}
.alert-desc{font-size:0.85rem;color:#6b7280;margin:0;}
.alert-meta{font-size:0.75rem;color:#9ca3af;margin-top:5px;}
.progress-bar-wrap{background:#f1f5f9;border-radius:8px;height:10px;overflow:hidden;margin:6px 0;}
.progress-bar-fill{height:100%;border-radius:8px;}
.iot-card{background:#fff;border-radius:14px;padding:18px 20px;border:1px solid #e5e7eb;box-shadow:0 2px 8px rgba(0,0,0,0.05);text-align:center;}
.obs-badge{display:inline-block;padding:4px 14px;border-radius:20px;font-weight:700;font-size:0.82rem;margin-top:6px;}
.interact-card{border-radius:10px;padding:12px 16px;margin:8px 0;}
.interact-alert{background:#fef2f2;border-left:4px solid #dc2626;}
.interact-warn{background:#fffbeb;border-left:4px solid #d97706;}
.interact-ok{background:#f0fdf4;border-left:4px solid #16a34a;}
.prediag-step{border-radius:10px;padding:10px;text-align:center;transition:all 0.2s;}
</style>""", unsafe_allow_html=True)

# ── NHANES ────────────────────────────────────────────────────────────────────
NHANES_PERCENTILES = {
    1:14.2,2:17.8,3:20.1,4:22.0,5:23.5,6:24.8,7:25.9,8:27.0,9:28.0,10:28.9,
    11:29.7,12:30.5,13:31.2,14:31.9,15:32.6,16:33.2,17:33.8,18:34.4,19:35.0,20:35.6,
    21:36.1,22:36.7,23:37.2,24:37.7,25:38.2,26:38.7,27:39.2,28:39.7,29:40.1,30:40.6,
    31:41.0,32:41.5,33:41.9,34:42.3,35:42.8,36:43.2,37:43.6,38:44.0,39:44.4,40:44.8,
    41:45.2,42:45.6,43:46.0,44:46.4,45:46.8,46:47.2,47:47.6,48:48.0,49:48.4,50:48.8,
    51:49.2,52:49.6,53:50.1,54:50.5,55:50.9,56:51.3,57:51.8,58:52.2,59:52.7,60:53.1,
    61:53.6,62:54.1,63:54.5,64:55.0,65:55.5,66:56.0,67:56.5,68:57.1,69:57.6,70:58.2,
    71:58.8,72:59.4,73:60.0,74:60.6,75:61.3,76:62.0,77:62.7,78:63.4,79:64.2,80:65.0,
    81:65.8,82:66.7,83:67.6,84:68.5,85:69.5,86:70.5,87:71.6,88:72.7,89:73.9,90:75.2,
    91:76.5,92:77.9,93:79.4,94:81.0,95:82.7,96:84.6,97:86.7,98:89.2,99:93.1
}
NHANES_BY_AGE = {
    "18-29":{"p25":41.5,"p50":52.1,"p75":63.8,"p85":71.2},
    "30-39":{"p25":40.2,"p50":51.0,"p75":62.5,"p85":70.1},
    "40-49":{"p25":38.8,"p50":49.4,"p75":61.0,"p85":68.7},
    "50-59":{"p25":37.1,"p50":47.6,"p75":59.2,"p85":67.0},
    "60-69":{"p25":35.5,"p50":45.8,"p75":57.4,"p85":65.2},
    "70+":  {"p25":33.2,"p50":43.5,"p75":55.1,"p85":63.0},
}
NHANES_CLINICAL = {
    "diabete":      {"mean_sain":51.3,"mean_malade":44.7,"difference":6.6,"p_value":0.0001},
    "hypertension": {"mean_sain":50.8,"mean_malade":46.2,"difference":4.6,"p_value":0.0008},
    "inflammation": {"mean_sain":51.1,"mean_malade":45.9,"difference":5.2,"p_value":0.0003},
    "mortalite":    {"hazard_ratio":0.63,"ci_95":"(0.49–0.82)",
                     "interpretation":"Chaque hausse de diversité réduit le risque de mortalité de 37% (HR=0.63)"},
}

def nhanes_percentile_rank(score, age=None):
    pct = 1
    for p in range(99, 0, -1):
        if score >= NHANES_PERCENTILES[p]:
            pct = p
            break
    if score >= 69.5:   niveau, nlabel, ncolor = "excellent", "Excellent 🌟", "#16a34a"
    elif score >= 61.3: niveau, nlabel, ncolor = "bon",       "Bon 👍",        "#2563eb"
    elif score >= 38.2: niveau, nlabel, ncolor = "modere",    "Modéré ⚠️",     "#d97706"
    else:               niveau, nlabel, ncolor = "faible",    "Faible 🔴",     "#e11d48"
    bg = f"Meilleur que **{pct}%** de la population générale"
    ag = pa = nm = dm = ba = None
    if age is not None:
        if age < 30:   ag = "18-29"
        elif age < 40: ag = "30-39"
        elif age < 50: ag = "40-49"
        elif age < 60: ag = "50-59"
        elif age < 70: ag = "60-69"
        else:          ag = "70+"
        a = NHANES_BY_AGE[ag]
        nm = a["p50"]
        dm = round(score - nm, 1)
        if score >= a["p85"]:   pa = 85
        elif score >= a["p75"]: pa = 75
        elif score >= a["p50"]: pa = 50
        elif score >= a["p25"]: pa = 25
        else:                   pa = 10
        ds = f"+{dm}" if dm >= 0 else str(dm)
        ba = f"Meilleur que **{pa}%** des {ag} ans ({ds} pts vs médiane)"
    return {
        "percentile_global": pct, "percentile_age": pa,
        "benchmark_global": bg, "benchmark_age": ba,
        "niveau": niveau, "niveau_label": nlabel, "niveau_color": ncolor,
        "age_group": ag, "nhanes_n": 8237,
        "source": "NHANES 2009-2012 · Vogtmann et al. Lancet Microbe 2022",
    }

def render_diversity_benchmark(diversite, age=None, context="patient"):
    bm = nhanes_percentile_rank(diversite, age)
    c = bm["niveau_color"]
    pct = bm["percentile_global"]
    st.markdown(f"""<div style="background:linear-gradient(135deg,{c}12,{c}06);border:1.5px solid {c}40;border-radius:16px;padding:20px 24px;margin:12px 0;">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
    <div><div style="font-size:0.75rem;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Score Diversité Microbienne</div>
    <div style="font-family:'DM Serif Display',serif;font-size:2.8rem;color:{c};line-height:1;">{diversite}<span style="font-size:1.2rem;color:#9ca3af;">/100</span></div>
    <span style="background:{c}20;color:{c};font-weight:600;padding:3px 12px;border-radius:20px;font-size:0.85rem;">{bm['niveau_label']}</span></div>
    <div style="text-align:right;"><div style="font-size:0.8rem;color:#6b7280;margin-bottom:2px;">vs population générale</div>
    <div style="font-family:'DM Serif Display',serif;font-size:2rem;color:{c};line-height:1;">Top {100-pct}%</div>
    <div style="font-size:0.78rem;color:#9ca3af;margin-top:4px;">sur {bm['nhanes_n']:,} patients NHANES</div></div></div>
    <div style="margin-top:14px;padding-top:12px;border-top:1px solid {c}20;">
    <div style="font-size:0.9rem;color:#374151;margin-bottom:4px;">🌍 {bm['benchmark_global']}</div>
    {"" if not bm['benchmark_age'] else f'<div style="font-size:0.9rem;color:#374151;">👤 {bm["benchmark_age"]}</div>'}
    </div></div>""", unsafe_allow_html=True)
    bh = '<div style="display:flex;border-radius:8px;overflow:hidden;height:12px;margin:8px 0 2px 0;">'
    for w, bg in [(25,"#fee2e2"),(25,"#fef3c7"),(25,"#dbeafe"),(15,"#dcfce7"),(10,"#bbf7d0")]:
        bh += f'<div style="flex:{w};background:{bg};border-right:1px solid white;"></div>'
    bh += f'</div><div style="position:relative;height:20px;"><div style="position:absolute;left:{pct}%;transform:translateX(-50%);">'
    bh += f'<div style="width:3px;height:12px;background:{c};margin:0 auto;"></div>'
    bh += f'<div style="font-size:0.7rem;font-weight:700;color:{c};white-space:nowrap;transform:translateX(-40%);">P{pct} — vous</div></div></div>'
    st.markdown(bh, unsafe_allow_html=True)
    lc = st.columns(5)
    for col, (lbl, cc) in zip(lc, [
        ("< P25\nFaible","#e11d48"),("P25–50\nModéré","#d97706"),
        ("P50–75\nBon","#2563eb"),("P75–85\nExcellent","#16a34a"),("> P90\nTop 10%","#15803d")
    ]):
        col.markdown(f"<div style='text-align:center;font-size:0.68rem;color:{cc};font-weight:600;line-height:1.3;'>{lbl}</div>", unsafe_allow_html=True)
    if context == "praticien":
        st.markdown("---")
        st.markdown("##### 📊 Corrélations cliniques — NHANES 2009-2012 (n=8 237)")
        c1, c2, c3 = st.columns(3)
        for col, (key, label, icon) in zip([c1, c2, c3], [
            ("diabete","Diabète","🩸"),("hypertension","Hypertension","❤️"),("inflammation","Inflammation","🔥")
        ]):
            d = NHANES_CLINICAL[key]
            col.markdown(f"""<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:12px;text-align:center;">
            <div style="font-size:1.2rem;">{icon}</div><div style="font-weight:600;font-size:0.85rem;margin:4px 0;">{label}</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.4rem;color:#e11d48;">−{d['difference']} pts</div>
            <div style="font-size:0.72rem;color:#6b7280;">sains: {d['mean_sain']} vs malades: {d['mean_malade']}</div>
            <div style="font-size:0.7rem;color:#16a34a;margin-top:4px;font-weight:600;">p={d['p_value']}</div></div>""", unsafe_allow_html=True)
        mort = NHANES_CLINICAL["mortalite"]
        st.markdown(f"""<div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:1px solid #16a34a40;border-radius:10px;padding:12px 16px;margin-top:8px;">
        <b>💚 Mortalité toutes causes</b> — HR={mort['hazard_ratio']} {mort['ci_95']}<br>
        <span style="font-size:0.85rem;color:#374151;">{mort['interpretation']}</span></div>""", unsafe_allow_html=True)

# ── SCORES SYSTÉMIQUES ────────────────────────────────────────────────────────
SYSTEMIC_CORRELATIONS = {
    "cardiovasculaire": {
        "icon":"❤️","label":"Risque Cardiovasculaire",
        "description":"P. gingivalis et T. forsythia libèrent des endotoxines favorisant l'athérosclérose.",
        "references":"Herzberg & Meyer 1996 · AHA 2012",
        "weight_gingivalis":0.45,"weight_mutans":0.10,"weight_diversity":0.30,"weight_inflammation":0.15,
        "thresholds":{"low":25,"high":55},
        "actions_high":["Consultation cardiologique recommandée","Bilan CRP ultrasensible","Traitement parodontal — réduit risque CV 20%","Alimentation anti-inflammatoire"],
        "actions_low":["Maintenir hygiène parodontale","Contrôle microbiome 6 mois"],
    },
    "diabete": {
        "icon":"🩸","label":"Risque Diabète / Résistance Insuline",
        "description":"Dysbiose orale entretenant inflammation chronique dégradant la sensibilité à l'insuline.",
        "references":"Taylor et al. 2013 · Lancet 2020",
        "weight_gingivalis":0.35,"weight_mutans":0.20,"weight_diversity":0.35,"weight_inflammation":0.10,
        "thresholds":{"low":25,"high":55},
        "actions_high":["Bilan glycémie à jeun et HbA1c","Réduction sucres rapides","Traitement paro : réduit HbA1c 0.4%","Exercice 150 min/semaine"],
        "actions_low":["Limiter sucres raffinés","Contrôle glycémie si antécédents"],
    },
    "alzheimer": {
        "icon":"🧠","label":"Risque Neurodégénératif (Alzheimer)",
        "description":"P. gingivalis retrouvée dans le cerveau Alzheimer. Gingipaines favorisant les plaques amyloïdes.",
        "references":"Dominy et al. Science Advances 2019",
        "weight_gingivalis":0.60,"weight_mutans":0.05,"weight_diversity":0.25,"weight_inflammation":0.10,
        "thresholds":{"low":20,"high":50},
        "actions_high":["Élimination P. gingivalis — priorité absolue","Oméga-3 DHA 1g/jour","Activité physique aérobie","Suivi neurologique si > 60 ans"],
        "actions_low":["Maintenir microbiome diversifié","Alimentation méditerranéenne"],
    },
    "colon": {
        "icon":"🦠","label":"Risque Colorectal",
        "description":"Fusobacterium nucleatum retrouvé dans les tumeurs colorectales.",
        "references":"Castellarin et al. 2012 · Rubinstein et al. 2013",
        "weight_gingivalis":0.25,"weight_mutans":0.10,"weight_diversity":0.50,"weight_inflammation":0.15,
        "thresholds":{"low":20,"high":45},
        "actions_high":["Coloscopie si > 45 ans","Fibres prébiotiques 30g/jour","Réduire viande rouge transformée","Probiotiques intestinaux"],
        "actions_low":["Alimentation riche en fibres","Dépistage selon l'âge"],
    },
    "respiratoire": {
        "icon":"🫁","label":"Risque Respiratoire / Pneumonie",
        "description":"Bactéries orales aspirées colonisant les voies respiratoires. Risque ×4 en dysbiose.",
        "references":"Scannapieco et al. 2003 · ADA 2021",
        "weight_gingivalis":0.30,"weight_mutans":0.15,"weight_diversity":0.40,"weight_inflammation":0.15,
        "thresholds":{"low":25,"high":50},
        "actions_high":["Hygiène orale renforcée","Brossage langue matin et soir (−70% bactéries)","Consultation pneumologique si toux chronique"],
        "actions_low":["Hygiène bucco-dentaire régulière","Brossage de la langue quotidien"],
    },
}

def calculer_score_systemique(sm, pg, div):
    sg  = min(100, (pg / 2.0) * 100)
    smu = min(100, (sm / 8.0) * 100)
    sd  = max(0, 100 - div)
    si  = min(100, sg * 0.6 + sd * 0.4)
    results = {}
    for key, corr in SYSTEMIC_CORRELATIONS.items():
        raw = (corr["weight_gingivalis"] * sg + corr["weight_mutans"] * smu +
               corr["weight_diversity"] * sd + corr["weight_inflammation"] * si)
        score = round(min(100, max(0, raw)))
        level = "low" if score < corr["thresholds"]["low"] else "high" if score > corr["thresholds"]["high"] else "med"
        results[key] = {**corr, "score": score, "level": level,
                        "actions": corr["actions_high"] if level == "high" else corr["actions_low"]}
    return dict(sorted(results.items(), key=lambda x: -x[1]["score"]))

# ── ANAMNÈSE ──────────────────────────────────────────────────────────────────
def get_anamnes(nom):
    return st.session_state.anamnes.get(nom, {})

def save_anamnes(nom, data):
    data["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.anamnes[nom] = data

# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────
def generer_notifications(patients):
    notifs = []
    today = date.today()
    for nom, p in patients.items():
        hist = p["historique"]
        if not hist.empty:
            try:
                ld = datetime.strptime(hist.iloc[-1]["Date"], "%d/%m/%Y").date()
                ea = p["s_mutans"] > 3 or p["p_gingivalis"] > 0.5 or p["diversite"] < 50
                dl = 8 if p["p_gingivalis"] > 1.5 or p["s_mutans"] > 6 else 12 if ea else 24
                retard = (today - (ld + timedelta(weeks=dl))).days
                if retard > 0:
                    notifs.append({"id": f"ctrl_{nom}", "type": "urgent", "icon": "⏰",
                                   "titre": nom, "message": f"Contrôle en retard de {retard} jours",
                                   "action": nom, "read": False})
            except:
                pass
        if p["p_gingivalis"] > 1.5:
            notifs.append({"id": f"pg_{nom}", "type": "urgent", "icon": "🚨",
                           "titre": nom, "message": f"P. gingivalis critique : {p['p_gingivalis']}%",
                           "action": nom, "read": False})
        elif p["s_mutans"] > 6.0:
            notifs.append({"id": f"sm_{nom}", "type": "warn", "icon": "⚠️",
                           "titre": nom, "message": f"S. mutans très élevé : {p['s_mutans']}%",
                           "action": nom, "read": False})
        # Observance décrochage
        jsr = jours_sans_reponse(p["id"])
        if jsr >= 3:
            notifs.append({"id": f"obs_{nom}", "type": "warn", "icon": "📉",
                           "titre": nom, "message": f"Décrochage protocole — {jsr} jours sans questionnaire",
                           "action": nom, "read": False})
    read_ids = st.session_state.get("notifs_read", set())
    for n in notifs:
        if n["id"] in read_ids:
            n["read"] = True
    return sorted(notifs, key=lambda x: (x["read"], x["type"] != "urgent"))

def render_notifications(patients):
    notifs  = generer_notifications(patients)
    unread  = sum(1 for n in notifs if not n["read"])
    badge   = (f'<span style="background:#e11d48;color:white;border-radius:10px;padding:1px 7px;'
               f'font-size:0.72rem;font-weight:700;margin-left:6px;">{unread}</span>'
               if unread > 0 else "")
    st.sidebar.markdown(f"**🔔 Notifications**{badge}", unsafe_allow_html=True)
    with st.sidebar.expander(f"Voir ({len(notifs)})", expanded=unread > 0):
        if not notifs:
            st.markdown(f"*✅ {t('notif_empty')}*")
        else:
            if st.button(t("notif_mark_read"), key="mark_all_read", use_container_width=True):
                st.session_state.notifs_read = {n["id"] for n in notifs}
                st.rerun()
            for n in notifs[:6]:
                bg   = "#fff1f2" if n["type"] == "urgent" and not n["read"] else "#fffbeb" if n["type"] == "warn" and not n["read"] else "#f8fafc"
                left = "#e11d48" if n["type"] == "urgent" else "#d97706"
                op   = "0.55" if n["read"] else "1"
                st.markdown(f'<div style="background:{bg};border-left:3px solid {left};border-radius:8px;padding:10px 12px;margin:6px 0;opacity:{op};"><div style="font-size:0.85rem;font-weight:600;">{n["icon"]} {n["titre"]}</div><div style="font-size:0.78rem;color:#6b7280;">{n["message"]}</div></div>', unsafe_allow_html=True)
                ca, cb = st.columns([3, 1])
                with ca:
                    if st.button("Ouvrir →", key=f"no_{n['id']}", use_container_width=True):
                        st.session_state.patient_sel = n["action"]
                        st.session_state.vue = "dossier"
                        st.rerun()
                with cb:
                    if not n["read"]:
                        if st.button("✓", key=f"nr_{n['id']}", use_container_width=True):
                            if "notifs_read" not in st.session_state:
                                st.session_state.notifs_read = set()
                            st.session_state.notifs_read.add(n["id"])
                            st.rerun()

# ── TWIN NUMÉRIQUE DENTAIRE ───────────────────────────────────────────────────
DENTS_FDI = {
    11:{"nom":"Incisive centrale","quadrant":1,"type":"incisive"},
    12:{"nom":"Incisive latérale","quadrant":1,"type":"incisive"},
    13:{"nom":"Canine","quadrant":1,"type":"canine"},
    14:{"nom":"Prémolaire 1","quadrant":1,"type":"premolaire"},
    15:{"nom":"Prémolaire 2","quadrant":1,"type":"premolaire"},
    16:{"nom":"Molaire 1","quadrant":1,"type":"molaire"},
    17:{"nom":"Molaire 2","quadrant":1,"type":"molaire"},
    18:{"nom":"Sagesse","quadrant":1,"type":"sagesse"},
    21:{"nom":"Incisive centrale","quadrant":2,"type":"incisive"},
    22:{"nom":"Incisive latérale","quadrant":2,"type":"incisive"},
    23:{"nom":"Canine","quadrant":2,"type":"canine"},
    24:{"nom":"Prémolaire 1","quadrant":2,"type":"premolaire"},
    25:{"nom":"Prémolaire 2","quadrant":2,"type":"premolaire"},
    26:{"nom":"Molaire 1","quadrant":2,"type":"molaire"},
    27:{"nom":"Molaire 2","quadrant":2,"type":"molaire"},
    28:{"nom":"Sagesse","quadrant":2,"type":"sagesse"},
    31:{"nom":"Incisive centrale","quadrant":3,"type":"incisive"},
    32:{"nom":"Incisive latérale","quadrant":3,"type":"incisive"},
    33:{"nom":"Canine","quadrant":3,"type":"canine"},
    34:{"nom":"Prémolaire 1","quadrant":3,"type":"premolaire"},
    35:{"nom":"Prémolaire 2","quadrant":3,"type":"premolaire"},
    36:{"nom":"Molaire 1","quadrant":3,"type":"molaire"},
    37:{"nom":"Molaire 2","quadrant":3,"type":"molaire"},
    38:{"nom":"Sagesse","quadrant":3,"type":"sagesse"},
    41:{"nom":"Incisive centrale","quadrant":4,"type":"incisive"},
    42:{"nom":"Incisive latérale","quadrant":4,"type":"incisive"},
    43:{"nom":"Canine","quadrant":4,"type":"canine"},
    44:{"nom":"Prémolaire 1","quadrant":4,"type":"premolaire"},
    45:{"nom":"Prémolaire 2","quadrant":4,"type":"premolaire"},
    46:{"nom":"Molaire 1","quadrant":4,"type":"molaire"},
    47:{"nom":"Molaire 2","quadrant":4,"type":"molaire"},
    48:{"nom":"Sagesse","quadrant":4,"type":"sagesse"},
}
ETATS_DENT = {
    "saine":       {"label":"Saine",           "color":"#16a34a","icon":"✅","bg":"#f0fdf4"},
    "surveillance":{"label":"À surveiller",    "color":"#d97706","icon":"👁️","bg":"#fffbeb"},
    "carie":       {"label":"Carie",           "color":"#ef4444","icon":"🔴","bg":"#fef2f2"},
    "paro":        {"label":"Atteinte paro.",  "color":"#dc2626","icon":"🩸","bg":"#fff1f2"},
    "absente":     {"label":"Absente",         "color":"#94a3b8","icon":"⬜","bg":"#f8fafc"},
    "couronne":    {"label":"Couronne/Implant","color":"#7c3aed","icon":"👑","bg":"#f5f3ff"},
    "traitement":  {"label":"En traitement",   "color":"#2563eb","icon":"🔧","bg":"#eff6ff"},
}
SOINS_TYPES = ["Détartrage","Soin carie","Extraction","Couronne","Implant",
               "Traitement paro.","Surfaçage","Probiotiques locaux","Observation"]

def get_twin(pid):
    if "twins" not in st.session_state: st.session_state.twins = {}
    if pid not in st.session_state.twins:
        td = {"notes_generales":"","indice_plaque":0,"indice_saignement":0,"derniere_maj":"","dents":{}}
        for num in DENTS_FDI:
            td["dents"][str(num)] = {"etat":"saine","risque_carie":0,"inflammation":0,"profondeur_poche":2,"soins":[],"notes":""}
        st.session_state.twins[pid] = td
    return st.session_state.twins[pid]

def save_twin(pid, twin):
    twin["derniere_maj"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.session_state.twins[pid] = twin

def score_quadrant(twin, q):
    ds = [twin["dents"].get(str(n), {}) for n, info in DENTS_FDI.items() if info["quadrant"] == q]
    pb = sum(1 for d in ds if d.get("etat") in ["carie","paro","traitement"])
    return max(0, 100 - pb * 20)

def dent_color(etat, risque, infl):
    if etat == "absente":    return "#94a3b8"
    if etat in ["carie","paro"]: return ETATS_DENT[etat]["color"]
    if etat == "couronne":   return "#7c3aed"
    if etat == "traitement": return "#2563eb"
    if etat == "surveillance": return "#d97706"
    r = max(risque, infl)
    if r > 70: return "#ef4444"
    if r > 40: return "#f59e0b"
    return "#16a34a"

def render_dent_svg(num, dent_data, selected=False):
    info  = DENTS_FDI.get(num, {})
    dtype = info.get("type","incisive")
    etat  = dent_data.get("etat","saine")
    rc    = dent_data.get("risque_carie",0)
    infl  = dent_data.get("inflammation",0)
    soins = dent_data.get("soins",[])
    color = dent_color(etat, rc, infl)
    absent = etat == "absente"
    W, H = {"molaire":(28,24),"premolaire":(22,22),"canine":(18,28),"incisive":(16,26),"sagesse":(22,20)}.get(dtype,(20,22))
    sel_glow  = f'filter:drop-shadow(0 0 6px {color}aa);' if selected else ""
    sel_scale = "transform:scale(1.15) translateY(-2px);" if selected else ""
    svg = f'<svg width="{W+4}" height="{H+12}" viewBox="-2 -2 {W+4} {H+16}" style="{sel_glow}{sel_scale}transition:all 0.2s;">'
    if absent:
        svg += f'<ellipse cx="{W/2}" cy="{H/2}" rx="{W/2-1}" ry="{H/2-1}" fill="#e2e8f0" stroke="#94a3b8" stroke-width="1" stroke-dasharray="2,2"/>'
        svg += f'<text x="{W/2}" y="{H/2+3}" text-anchor="middle" font-size="7" fill="#94a3b8" font-family="monospace">{num}</text>'
    else:
        if dtype in ["molaire","premolaire"]:
            svg += f'<ellipse cx="{W*0.3}" cy="{H+7}" rx="4" ry="7" fill="{color}" opacity="0.3"/>'
            svg += f'<ellipse cx="{W*0.7}" cy="{H+7}" rx="4" ry="7" fill="{color}" opacity="0.3"/>'
            if dtype == "molaire":
                svg += f'<ellipse cx="{W/2}" cy="{H+8}" rx="3" ry="5" fill="{color}" opacity="0.2"/>'
        else:
            svg += f'<ellipse cx="{W/2}" cy="{H+8}" rx="4" ry="8" fill="{color}" opacity="0.3"/>'
        gum_c = "#fda4af" if infl > 60 else "#fecdd3" if infl > 30 else "#fde8ec"
        svg += f'<ellipse cx="{W/2}" cy="{H-1}" rx="{W/2+1}" ry="5" fill="{gum_c}" opacity="0.5"/>'
        svg += f'<ellipse cx="{W/2+1}" cy="{H/2+1}" rx="{W/2-0.5}" ry="{H/2-0.5}" fill="rgba(0,0,0,0.25)"/>'
        if dtype in ["molaire","premolaire"]:
            r = 4 if dtype == "molaire" else 3
            svg += f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="{r}" fill="{color}"/>'
            if dtype == "molaire":
                svg += f'<line x1="{W/2}" y1="3" x2="{W/2}" y2="{H-3}" stroke="rgba(0,0,0,0.15)" stroke-width="1.5"/>'
                svg += f'<line x1="3" y1="{H/2}" x2="{W-3}" y2="{H/2}" stroke="rgba(0,0,0,0.15)" stroke-width="1.5"/>'
        elif dtype == "canine":
            svg += f'<path d="M{W/2},{1} L{W-1},{H*0.4} Q{W-1},{H-1} {W/2},{H-1} Q{1},{H-1} {1},{H*0.4} Z" fill="{color}"/>'
        else:
            svg += f'<ellipse cx="{W/2}" cy="{H/2}" rx="{W/2-1}" ry="{H/2-1}" fill="{color}"/>'
        svg += f'<ellipse cx="{W*0.32}" cy="{H*0.28}" rx="{W*0.18}" ry="{H*0.2}" fill="white" opacity="0.3"/>'
        svg += f'<ellipse cx="{W/2}" cy="{H*0.12}" rx="{W*0.25}" ry="{H*0.08}" fill="white" opacity="0.4"/>'
        svg += f'<ellipse cx="{W*0.78}" cy="{H/2}" rx="{W*0.15}" ry="{H*0.4}" fill="rgba(0,0,0,0.15)"/>'
        svg += f'<text x="{W/2}" y="{H/2+3}" text-anchor="middle" font-size="6.5" fill="white" font-family="monospace" font-weight="bold" opacity="0.95">{num}</text>'
        if rc > 40:
            rc_c = "#dc2626" if rc > 70 else "#f59e0b"
            svg += f'<circle cx="{W-2}" cy="2" r="4" fill="{rc_c}" stroke="white" stroke-width="0.8"/>'
        if infl > 40:
            in_c = "#dc2626" if infl > 70 else "#f97316"
            svg += f'<circle cx="2" cy="2" r="4" fill="{in_c}" stroke="white" stroke-width="0.8"/>'
        if soins:
            svg += f'<circle cx="{W-2}" cy="{H-2}" r="3.5" fill="#6366f1" stroke="white" stroke-width="0.7"/>'
    svg += '</svg>'
    return svg

def render_arch_svg(twin, quadrant_top, quadrant_bot, is_praticien=True, selected_num=None):
    top_nums = [18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28]
    W, H = 700, 200
    svg_parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:700px;">']
    svg_parts.append(f'''<defs><radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#f0f4ff" stop-opacity="0.8"/>
        <stop offset="100%" stop-color="#e8edf8" stop-opacity="0.4"/>
    </radialGradient></defs>
    <ellipse cx="{W/2}" cy="{H/2}" rx="{W/2-10}" ry="{H/2-10}" fill="url(#bgGrad)" stroke="#dbeafe" stroke-width="0.5"/>''')
    svg_parts.append(f'<line x1="{W/2}" y1="5" x2="{W/2}" y2="{H-5}" stroke="#cbd5e1" stroke-width="0.8" stroke-dasharray="3,3" opacity="0.6"/>')

    def arch_positions(nums, row="top"):
        positions = {}
        n = len(nums)
        for i, num in enumerate(nums):
            t = i / (n - 1)
            rx = W / 2 - 55
            cx = W / 2 + rx * (-1 + 2 * t) * 0.95
            if row == "top":
                cy = max(20, min(H - 20, H / 2 - 60 + 120 * abs(0.5 - t) * 1.6))
            else:
                cy = max(20, min(H - 20, H / 2 + 60 - 120 * abs(0.5 - t) * 1.6))
            positions[num] = (cx, cy)
        return positions

    positions_top = arch_positions(top_nums)
    for i, num in enumerate(top_nums):
        cx, cy = positions_top[num]
        d = twin["dents"].get(str(num), {"etat":"saine"})
        color = dent_color(d.get("etat","saine"), d.get("risque_carie",0), d.get("inflammation",0))
        info  = DENTS_FDI.get(num, {})
        dtype = info.get("type","incisive")
        W2, H2 = {"molaire":(26,20),"premolaire":(20,18),"canine":(16,22),"incisive":(14,20),"sagesse":(20,17)}.get(dtype,(18,18))
        absent = d.get("etat") == "absente"
        if absent:
            svg_parts.append(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{W2/2:.0f}" ry="{H2/2:.0f}" fill="#e2e8f0" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="2,2" opacity="0.5"/>')
        else:
            svg_parts.append(f'<ellipse cx="{cx+1:.0f}" cy="{cy+1:.0f}" rx="{W2/2:.0f}" ry="{H2/2:.0f}" fill="rgba(0,0,0,0.2)"/>')
            if dtype in ["molaire","premolaire"]:
                rx2, ry2 = W2/2-1, H2/2-1
                svg_parts.append(f'<rect x="{cx-rx2:.0f}" y="{cy-ry2:.0f}" width="{W2-2}" height="{H2-2}" rx="4" fill="{color}"/>')
                if dtype == "molaire":
                    svg_parts.append(f'<line x1="{cx:.0f}" y1="{cy-ry2+2:.0f}" x2="{cx:.0f}" y2="{cy+ry2-2:.0f}" stroke="rgba(0,0,0,0.12)" stroke-width="1.2"/>')
                    svg_parts.append(f'<line x1="{cx-rx2+2:.0f}" y1="{cy:.0f}" x2="{cx+rx2-2:.0f}" y2="{cy:.0f}" stroke="rgba(0,0,0,0.12)" stroke-width="1.2"/>')
            elif dtype == "canine":
                svg_parts.append(f'<ellipse cx="{cx:.0f}" cy="{cy+2:.0f}" rx="{W2/2-1:.0f}" ry="{H2/2-1:.0f}" fill="{color}"/>')
                svg_parts.append(f'<ellipse cx="{cx:.0f}" cy="{cy-H2/2+1:.0f}" rx="3" ry="4" fill="{color}"/>')
            else:
                svg_parts.append(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{W2/2-1:.0f}" ry="{H2/2-1:.0f}" fill="{color}"/>')
            svg_parts.append(f'<ellipse cx="{cx-W2*0.18:.0f}" cy="{cy-H2*0.22:.0f}" rx="{W2*0.2:.0f}" ry="{H2*0.18:.0f}" fill="white" opacity="0.28"/>')
        if is_praticien:
            svg_parts.append(f'<text x="{cx:.0f}" y="{cy+3:.0f}" text-anchor="middle" font-size="6" fill="white" font-family="monospace" font-weight="bold" opacity="0.9">{num}</text>')
        rc  = d.get("risque_carie",0)
        inf = d.get("inflammation",0)
        if rc > 40 and not absent:
            rc_c = "#dc2626" if rc > 70 else "#f59e0b"
            svg_parts.append(f'<circle cx="{cx+W2/2-1:.0f}" cy="{cy-H2/2+1:.0f}" r="4" fill="{rc_c}" stroke="white" stroke-width="0.7"/>')
        if inf > 40 and not absent:
            in_c = "#dc2626" if inf > 70 else "#f97316"
            svg_parts.append(f'<circle cx="{cx-W2/2+1:.0f}" cy="{cy-H2/2+1:.0f}" r="4" fill="{in_c}" stroke="white" stroke-width="0.7"/>')
        if d.get("soins") and not absent:
            svg_parts.append(f'<circle cx="{cx+W2/2-1:.0f}" cy="{cy+H2/2-1:.0f}" r="3.5" fill="#6366f1" stroke="white" stroke-width="0.6"/>')
    svg_parts.append(f'<text x="120" y="12" font-size="7" fill="#94a3b8" text-anchor="middle" font-weight="600">Q1 — HAUT DROITE</text>')
    svg_parts.append(f'<text x="580" y="12" font-size="7" fill="#94a3b8" text-anchor="middle" font-weight="600">Q2 — HAUT GAUCHE</text>')
    svg_parts.append('</svg>')
    return "".join(svg_parts)

def render_twin_complet(twin, sm, pg, mode="praticien", pid=""):
    q_scores     = {q: score_quadrant(twin, q) for q in [1,2,3,4]}
    score_global = round(sum(q_scores.values()) / 4)
    sc           = "#16a34a" if score_global >= 80 else "#d97706" if score_global >= 60 else "#e11d48"
    q_labels     = {1:"Haut Droite",2:"Haut Gauche",3:"Bas Gauche",4:"Bas Droite"}
    q_icons      = {1:"↗️",2:"↖️",3:"↙️",4:"↘️"}
    cols_q = st.columns(4)
    for q, col in zip([1,2,3,4], cols_q):
        qs = q_scores[q]
        qc = "#16a34a" if qs >= 80 else "#d97706" if qs >= 50 else "#e11d48"
        col.markdown(f"""<div style="background:#fff;border:1.5px solid {qc}30;border-radius:12px;padding:12px 8px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
            <div style="font-size:0.7rem;color:#6b7280;font-weight:700;margin-bottom:3px;">{q_icons[q]} {q_labels[q]}</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:{qc};line-height:1;">{qs}</div>
            <div style="font-size:0.68rem;color:#9ca3af;">/100</div></div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🦷 Arcade Maxillaire — Q1 · Q2 (Haut)")
    svg_top = render_arch_svg(twin, 1, 2, mode == "praticien", None)
    st.markdown(f'<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:16px;padding:12px;text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.06);">{svg_top}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🦷 Arcade Mandibulaire — Q3 · Q4 (Bas)")
    svg_bot = render_arch_svg(twin, 3, 4, mode == "praticien", None)
    st.markdown(f'<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:16px;padding:12px;text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.06);">{svg_bot}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    leg_cols = st.columns(7)
    for col, (key, info) in zip(leg_cols, list(ETATS_DENT.items())[:7]):
        col.markdown(f'<div style="display:flex;align-items:center;gap:4px;font-size:0.7rem;"><div style="width:10px;height:10px;border-radius:2px;background:{info["color"]};flex-shrink:0;"></div><span style="color:#374151;">{info["label"]}</span></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### 🧬 Corrélation Microbiome → Twin")
    mi1, mi2, mi3 = st.columns(3)
    sm_c = "#e11d48" if sm > 3 else "#d97706" if sm > 1.5 else "#16a34a"
    pg_c = "#e11d48" if pg > 0.5 else "#d97706" if pg > 0.2 else "#16a34a"
    nb_rc  = sum(1 for d in twin["dents"].values() if d.get("risque_carie",0) > 50)
    nb_inf = sum(1 for d in twin["dents"].values() if d.get("inflammation",0) > 50)
    nb_pb  = sum(1 for d in twin["dents"].values() if d.get("etat") in ["carie","paro"])
    with mi1:
        st.markdown(f"""<div style="background:#fff;border:1px solid {sm_c}30;border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:0.72rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin-bottom:4px;">S. mutans → Caries</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:{sm_c};">{sm}%</div>
            <div style="font-size:0.8rem;color:#374151;margin-top:6px;">Dents à risque élevé : <b style="color:{sm_c};">{nb_rc}</b></div>
            <div style="background:{sm_c}15;border-radius:6px;padding:3px 8px;margin-top:8px;font-size:0.72rem;color:{sm_c};">
            {"🔴 Risque élevé" if sm > 3 else "🟡 Modéré" if sm > 1.5 else "🟢 Faible"}</div></div>""", unsafe_allow_html=True)
    with mi2:
        st.markdown(f"""<div style="background:#fff;border:1px solid {pg_c}30;border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:0.72rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin-bottom:4px;">P. gingivalis → Paro</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:{pg_c};">{pg}%</div>
            <div style="font-size:0.8rem;color:#374151;margin-top:6px;">Zones enflammées : <b style="color:{pg_c};">{nb_inf}</b></div>
            <div style="background:{pg_c}15;border-radius:6px;padding:3px 8px;margin-top:8px;font-size:0.72rem;color:{pg_c};">
            {"🔴 Atteinte probable" if pg > 0.5 else "🟡 Surveillance" if pg > 0.2 else "🟢 Protectrice"}</div></div>""", unsafe_allow_html=True)
    with mi3:
        st.markdown(f"""<div style="background:#fff;border:1px solid {sc}30;border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:0.72rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin-bottom:4px;">Score Twin Global</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:{sc};">{score_global}/100</div>
            <div style="font-size:0.8rem;color:#374151;margin-top:6px;">Interventions requises : <b style="color:{sc};">{nb_pb}</b></div>
            <div style="background:{sc}15;border-radius:6px;padding:3px 8px;margin-top:8px;font-size:0.72rem;color:{sc};">
            {"✅ Bonne santé" if score_global >= 80 else "⚠️ Surveillance" if score_global >= 60 else "🔴 Soins recommandés"}</div></div>""", unsafe_allow_html=True)

def render_twin_edition(twin, pid):
    st.markdown("---")
    st.markdown("#### ✏️ Éditer une Dent")
    options = {f"Dent {n} — {info['nom']} (Q{info['quadrant']})": n for n, info in DENTS_FDI.items()}
    sel_label = st.selectbox("Sélectionner une dent", list(options.keys()), key=f"sel_dent_{pid}")
    sel_num   = options[sel_label]
    sel_str   = str(sel_num)
    dent_data = twin["dents"].get(sel_str, {"etat":"saine","risque_carie":0,"inflammation":0,"profondeur_poche":2,"soins":[],"notes":""})
    etat_act  = dent_data.get("etat","saine")
    etat_info = ETATS_DENT.get(etat_act, ETATS_DENT["saine"])
    col_form, col_preview = st.columns([3, 1])
    with col_form:
        st.markdown(f"""<div style="background:{etat_info['bg']};border:2px solid {etat_info['color']}40;border-radius:12px;padding:14px 18px;margin-bottom:14px;display:flex;align-items:center;gap:12px;">
            <div style="background:{etat_info['color']};color:white;width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:800;font-family:monospace;font-size:1rem;">{sel_num}</div>
            <div><div style="font-weight:700;font-size:0.95rem;">{DENTS_FDI[sel_num]['nom']} — {DENTS_FDI[sel_num]['type'].capitalize()}</div>
            <div style="font-size:0.78rem;color:#6b7280;">Q{DENTS_FDI[sel_num]['quadrant']} — {['','Haut Droite','Haut Gauche','Bas Gauche','Bas Droite'][DENTS_FDI[sel_num]['quadrant']]}</div></div>
            <span style="margin-left:auto;background:{etat_info['color']}20;color:{etat_info['color']};padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;">{etat_info['icon']} {etat_info['label']}</span></div>""", unsafe_allow_html=True)
        with st.form(f"form_dent_{pid}_{sel_num}"):
            fa, fb = st.columns(2)
            with fa:
                nouveau_etat = st.selectbox("État clinique", list(ETATS_DENT.keys()),
                    index=list(ETATS_DENT.keys()).index(etat_act),
                    format_func=lambda x: f"{ETATS_DENT[x]['icon']} {ETATS_DENT[x]['label']}")
                rc_val = st.slider("🦠 Risque Carieux (S. mutans)", 0, 100, int(dent_data.get("risque_carie",0)))
            with fb:
                infl_val  = st.slider("🩸 Inflammation Gingivale (P. gingivalis)", 0, 100, int(dent_data.get("inflammation",0)))
                poche_val = st.slider("📏 Profondeur de poche (mm)", 1, 12, int(dent_data.get("profondeur_poche",2)))
            soins_val = st.multiselect("🔧 Historique des soins", SOINS_TYPES, default=dent_data.get("soins",[]))
            notes_val = st.text_area("📝 Notes cliniques", value=dent_data.get("notes",""),
                                      placeholder="Ex: Carie distale profonde, sondage 5mm...", height=60)
            if st.form_submit_button("💾 Sauvegarder cette dent", use_container_width=True, type="primary"):
                twin["dents"][sel_str] = {"etat":nouveau_etat,"risque_carie":rc_val,"inflammation":infl_val,
                                           "profondeur_poche":poche_val,"soins":soins_val,"notes":notes_val}
                save_twin(pid, twin)
                st.success(f"✅ Dent {sel_num} mise à jour !")
                st.rerun()
    with col_preview:
        svg = render_dent_svg(sel_num, dent_data, selected=True)
        st.markdown(f"""<div style="text-align:center;background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:16px;">
            <div style="font-size:0.72rem;color:#6b7280;margin-bottom:8px;font-weight:600;">PRÉVISUALISATION 3D</div>
            {svg}<div style="margin-top:8px;display:flex;flex-direction:column;gap:4px;">
                <div style="font-size:0.7rem;color:#6b7280;">● Coin haut-droit : risque carieux</div>
                <div style="font-size:0.7rem;color:#6b7280;">● Coin haut-gauche : inflammation</div>
                <div style="font-size:0.7rem;color:#6b7280;">● Coin bas-droit : soins enregistrés</div>
            </div></div>""", unsafe_allow_html=True)
        poche_v  = dent_data.get("profondeur_poche", 2)
        poche_c  = "#16a34a" if poche_v <= 3 else "#d97706" if poche_v <= 5 else "#e11d48"
        poche_lb = "✅ Normal" if poche_v <= 3 else "⚠️ Pathologique" if poche_v <= 5 else "🔴 Sévère"
        st.markdown(f"""<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:12px;margin-top:10px;text-align:center;">
            <div style="font-size:0.68rem;color:#6b7280;font-weight:700;margin-bottom:6px;">POCHE PARO</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:{poche_c};">{poche_v}mm</div>
            <div style="font-size:0.68rem;color:#9ca3af;">{poche_lb}</div></div>""", unsafe_allow_html=True)
    st.markdown("---")
    col_proj, col_notes_g = st.columns([1, 1])
    with col_proj:
        st.markdown("#### ⚡ Actions Rapides")
        sm_pat = st.session_state.patients.get(st.session_state.patient_sel, {}).get("s_mutans", 0)
        pg_pat = st.session_state.patients.get(st.session_state.patient_sel, {}).get("p_gingivalis", 0)
        if st.button("🧬 Projeter microbiome sur toutes les dents", use_container_width=True,
                     help="Calcule le risque carieux et l'inflammation à partir des biomarqueurs globaux"):
            for num_str in twin["dents"]:
                if twin["dents"][num_str].get("etat") == "absente": continue
                dtype2 = DENTS_FDI.get(int(num_str), {}).get("type","incisive")
                fact = 1.2 if dtype2 in ["molaire","premolaire"] else 0.85
                twin["dents"][num_str]["risque_carie"] = min(100, int((sm_pat / 8.0) * 100 * fact))
                twin["dents"][num_str]["inflammation"]  = min(100, int((pg_pat / 2.0) * 100))
            save_twin(pid, twin)
            st.success("✅ Microbiome projeté !")
            st.rerun()
        if twin.get("derniere_maj"): st.caption(f"Dernière mise à jour : {twin['derniere_maj']}")
        nb_s  = sum(1 for d in twin["dents"].values() if d.get("etat") == "saine")
        nb_pb = sum(1 for d in twin["dents"].values() if d.get("etat") in ["carie","paro"])
        nb_tx = sum(1 for d in twin["dents"].values() if d.get("etat") == "traitement")
        nb_ab = sum(1 for d in twin["dents"].values() if d.get("etat") == "absente")
        st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:12px 14px;margin-top:10px;">
            <div style="font-size:0.75rem;font-weight:700;color:#374151;margin-bottom:8px;">📊 Bilan du twin</div>
            <div style="font-size:0.82rem;display:flex;flex-direction:column;gap:4px;">
                <div style="display:flex;justify-content:space-between;"><span>✅ Saines</span><b style="color:#16a34a;">{nb_s}</b></div>
                <div style="display:flex;justify-content:space-between;"><span>🔴 Problèmes</span><b style="color:#ef4444;">{nb_pb}</b></div>
                <div style="display:flex;justify-content:space-between;"><span>🔧 En traitement</span><b style="color:#2563eb;">{nb_tx}</b></div>
                <div style="display:flex;justify-content:space-between;"><span>⬜ Absentes</span><b style="color:#94a3b8;">{nb_ab}</b></div>
                <div style="display:flex;justify-content:space-between;border-top:1px solid #e5e7eb;padding-top:4px;margin-top:2px;"><span>📊 Présentes</span><b>{32-nb_ab}/32</b></div>
            </div></div>""", unsafe_allow_html=True)
    with col_notes_g:
        st.markdown("#### 📝 Notes Générales")
        with st.form(f"form_notes_{pid}"):
            notes_g = st.text_area("Notes du cabinet", value=twin.get("notes_generales",""),
                                    placeholder="Bruxisme, prothèse, antécédents...", height=80)
            ip_v = st.slider("Indice de plaque global", 0, 100, int(twin.get("indice_plaque",0)))
            is_v = st.slider("Indice de saignement global", 0, 100, int(twin.get("indice_saignement",0)))
            if st.form_submit_button("💾 Sauvegarder", use_container_width=True):
                twin["notes_generales"] = notes_g
                twin["indice_plaque"]   = ip_v
                twin["indice_saignement"] = is_v
                save_twin(pid, twin)
                st.success("✅ Sauvegardé")
                st.rerun()

def render_twin_tableau(twin):
    st.markdown("---")
    st.markdown("#### 📋 Tableau Complet des Dents")
    tab_q1, tab_q2, tab_q3, tab_q4, tab_all = st.tabs(["Q1 — Haut Droite","Q2 — Haut Gauche","Q3 — Bas Gauche","Q4 — Bas Droite","Vue complète"])
    def rows_for_q(q):
        rows = []
        for num, info in DENTS_FDI.items():
            if info["quadrant"] != q: continue
            d  = twin["dents"].get(str(num), {"etat":"saine"})
            ei = ETATS_DENT.get(d.get("etat","saine"), ETATS_DENT["saine"])
            rows.append({"N° FDI":num,"Dent":info["nom"],"État":f"{ei['icon']} {ei['label']}",
                         "Risque carieux":f"{d.get('risque_carie',0)}/100","Inflammation":f"{d.get('inflammation',0)}/100",
                         "Poche (mm)":d.get("profondeur_poche",2),"Soins":", ".join(d.get("soins",[])) or "—","Notes":d.get("notes","")[:40] or "—"})
        return rows
    with tab_q1: st.dataframe(pd.DataFrame(rows_for_q(1)), use_container_width=True, hide_index=True)
    with tab_q2: st.dataframe(pd.DataFrame(rows_for_q(2)), use_container_width=True, hide_index=True)
    with tab_q3: st.dataframe(pd.DataFrame(rows_for_q(3)), use_container_width=True, hide_index=True)
    with tab_q4: st.dataframe(pd.DataFrame(rows_for_q(4)), use_container_width=True, hide_index=True)
    with tab_all:
        all_rows = []
        for num, info in DENTS_FDI.items():
            d  = twin["dents"].get(str(num), {"etat":"saine"})
            ei = ETATS_DENT.get(d.get("etat","saine"), ETATS_DENT["saine"])
            all_rows.append({"N°":num,"Dent":info["nom"],"Q":f"Q{info['quadrant']}","État":f"{ei['icon']} {ei['label']}",
                             "Carie":f"{d.get('risque_carie',0)}/100","Inflam.":f"{d.get('inflammation',0)}/100","Poche":f"{d.get('profondeur_poche',2)}mm"})
        st.dataframe(pd.DataFrame(all_rows), use_container_width=True, hide_index=True)

def render_twin_praticien(patient):
    twin = get_twin(patient["id"])
    sm = patient["s_mutans"]; pg = patient["p_gingivalis"]
    st.markdown(f"""<div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:14px;padding:20px 28px;margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:14px;">
            <span style="background:linear-gradient(135deg,#38bdf8,#0284c7);border-radius:10px;padding:8px 12px;font-size:1.8rem;">🦷</span>
            <div><div style="font-family:'DM Serif Display',serif;font-size:1.4rem;color:white;">Twin Numérique Dentaire — {patient['nom']}</div>
            <div style="font-size:0.82rem;color:rgba(255,255,255,0.65);">Vue 3D · Numérotation FDI · Corrélation microbiome · Suivi par dent</div></div></div></div>""", unsafe_allow_html=True)
    view_mode = st.radio("Vue", ["🗺️ Schéma 3D","✏️ Édition dent","📋 Tableau"], horizontal=True, key=f"twin_view_{patient['id']}")
    if view_mode == "🗺️ Schéma 3D":
        render_twin_complet(twin, sm, pg, mode="praticien", pid=patient["id"])
    elif view_mode == "✏️ Édition dent":
        render_twin_complet(twin, sm, pg, mode="praticien", pid=patient["id"])
        render_twin_edition(twin, patient["id"])
    else:
        render_twin_complet(twin, sm, pg, mode="praticien", pid=patient["id"])
        render_twin_tableau(twin)

def render_twin_patient(patient):
    twin     = get_twin(patient["id"])
    sm = patient["s_mutans"]; pg = patient["p_gingivalis"]
    scores_q = {q: score_quadrant(twin, q) for q in [1,2,3,4]}
    score_global = round(sum(scores_q.values()) / 4)
    sc = "#16a34a" if score_global >= 80 else "#d97706" if score_global >= 60 else "#e11d48"
    st.markdown(f"""<div style="background:linear-gradient(135deg,#1a3a5c,#2563eb);border-radius:14px;padding:20px 28px;margin-bottom:20px;">
        <div style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:white;">🦷 Mon Twin Numérique Dentaire</div>
        <div style="font-size:0.82rem;color:rgba(255,255,255,0.7);">Visualisation de l'état de vos dents · Mis à jour par votre praticien</div></div>""", unsafe_allow_html=True)
    col_score, col_q = st.columns([1, 2])
    with col_score:
        st.markdown(f"""<div style="background:linear-gradient(135deg,{sc}18,{sc}08);border:2px solid {sc};border-radius:16px;padding:28px 20px;text-align:center;height:100%;">
            <div style="font-size:0.72rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin-bottom:6px;">Score Santé Bucco-Dentaire</div>
            <div style="font-family:'DM Serif Display',serif;font-size:3.5rem;color:{sc};line-height:1;">{score_global}</div>
            <div style="font-size:0.75rem;color:#9ca3af;">/100</div>
            <div style="margin-top:12px;font-size:0.9rem;font-weight:600;color:{sc};">
                {"✅ Très bonne santé" if score_global >= 80 else "⚠️ Points à surveiller" if score_global >= 60 else "🔴 Soins recommandés"}
            </div></div>""", unsafe_allow_html=True)
    with col_q:
        q_labels = {1:"Haut Droite",2:"Haut Gauche",3:"Bas Gauche",4:"Bas Droite"}
        for q in [1, 2, 3, 4]:
            qs = scores_q[q]; qc = "#16a34a" if qs >= 80 else "#d97706" if qs >= 50 else "#e11d48"
            emoji = "✅" if qs >= 80 else "⚠️" if qs >= 50 else "🔴"
            st.markdown(f'<div style="background:#f8fafc;border:1px solid {qc}30;border-radius:8px;padding:8px 12px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><span style="font-size:0.85rem;color:#374151;">{emoji} {q_labels[q]}</span><span style="font-family:\'DM Serif Display\',serif;font-size:1.2rem;color:{qc};font-weight:700;">{qs}/100</span></div>', unsafe_allow_html=True)
    st.markdown("---")
    svg_top = render_arch_svg(twin, 1, 2, is_praticien=False)
    svg_bot = render_arch_svg(twin, 3, 4, is_praticien=False)
    st.markdown("##### Votre arcade dentaire")
    st.markdown(f'<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:14px;padding:10px;text-align:center;">{svg_top}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:14px;padding:10px;text-align:center;">{svg_bot}</div>', unsafe_allow_html=True)
    st.markdown("---")
    dents_att = [(int(n), d) for n, d in twin["dents"].items() if d.get("etat") in ["carie","paro","surveillance","traitement"]]
    if dents_att:
        st.markdown("#### 🔍 Points d'attention")
        for num, d in dents_att:
            info = DENTS_FDI.get(num, {}); etat = d.get("etat","saine"); ei = ETATS_DENT.get(etat, ETATS_DENT["saine"])
            q_label = {1:"Haut Droite",2:"Haut Gauche",3:"Bas Gauche",4:"Bas Droite"}.get(info.get("quadrant",1),"")
            soins = d.get("soins",[]); notes = d.get("notes","")
            st.markdown(f"""<div style="background:{ei['bg']};border:1px solid {ei['color']}40;border-radius:10px;padding:14px 18px;margin:8px 0;display:flex;align-items:center;gap:14px;">
                <div style="background:{ei['color']};color:white;width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:800;font-family:monospace;flex-shrink:0;">{num}</div>
                <div style="flex:1;"><div style="font-weight:600;font-size:0.9rem;">{info.get('nom','Dent')} {ei['icon']} — {ei['label']}</div>
                <div style="font-size:0.8rem;color:#6b7280;margin-top:2px;">{q_label}{" · Soins : " + ", ".join(soins) if soins else ""}</div>
                {f'<div style="font-size:0.78rem;color:#374151;margin-top:4px;font-style:italic;">{notes}</div>' if notes else ""}</div></div>""", unsafe_allow_html=True)
    else:
        st.success("✅ Toutes vos dents suivies sont en bonne santé !")
    st.info("⚕️ Ce schéma est mis à jour par votre praticien lors de chaque visite.")

# ══════════════════════════════════════════════════════════════
# FONCTIONNALITÉ 1 — SCORE D'OBSERVANCE
# ══════════════════════════════════════════════════════════════

OBSERVANCE_BADGES = {
    (90, 100): {"label":"Champion 🏆",       "color":"#15803d","bg":"#dcfce7","desc":"Observance exemplaire"},
    (75,  90): {"label":"Engagé ✅",          "color":"#16a34a","bg":"#f0fdf4","desc":"Très bonne observance"},
    (55,  75): {"label":"Régulier 👍",        "color":"#2563eb","bg":"#eff6ff","desc":"Observance correcte"},
    (35,  55): {"label":"Irrégulier ⚠️",     "color":"#d97706","bg":"#fffbeb","desc":"Des progrès à faire"},
    (0,   35): {"label":"En décrochage 🔴",  "color":"#dc2626","bg":"#fef2f2","desc":"Alerte praticien requise"},
}

def get_observance_badge(score):
    for (lo, hi), badge in OBSERVANCE_BADGES.items():
        if lo <= score <= hi:
            return badge
    return list(OBSERVANCE_BADGES.values())[-1]

def get_observance_data(pid):
    if "observance" not in st.session_state: st.session_state.observance = {}
    if pid not in st.session_state.observance:
        history = []
        base_score = random.randint(55, 85)
        for i in range(28, 0, -1):
            day   = date.today() - timedelta(days=i)
            noise = random.randint(-12, 12)
            score = max(10, min(100, base_score + noise))
            history.append({"date": day.strftime("%d/%m/%Y"), "score": score, "submitted": True})
        for i in range(3, 0, -1):
            day = date.today() - timedelta(days=i)
            history.append({"date": day.strftime("%d/%m/%Y"), "score": None, "submitted": False})
        st.session_state.observance[pid] = {"history": history, "last_questionnaire": {}}
    return st.session_state.observance[pid]

def calculer_score_observance(pid):
    data   = get_observance_data(pid)
    recent = [d for d in data["history"] if d["submitted"]][-7:]
    if not recent: return 0
    return round(sum(d["score"] for d in recent) / len(recent))

def jours_sans_reponse(pid):
    data  = get_observance_data(pid)
    count = 0
    for entry in reversed(data["history"]):
        if not entry["submitted"]: count += 1
        else: break
    return count

def predire_prochain_score_microbiome(sm, pg, div, observance_score):
    f = observance_score / 100
    sm_prevu  = round(max(0.1, sm  * (1 - f * 0.30)), 2)
    pg_prevu  = round(max(0.02, pg * (1 - f * 0.35)), 2)
    div_prevu = round(min(100, div + f * 15), 1)
    horizon   = "4–6 semaines" if observance_score >= 75 else "8–12 semaines"
    return {"sm_actuel":sm,"sm_prevu":sm_prevu,"pg_actuel":pg,"pg_prevu":pg_prevu,
            "div_actuel":div,"div_prevu":div_prevu,"horizon":horizon,
            "confiance":"élevée" if observance_score >= 70 else "modérée"}

def render_observance_patient(pid, sm, pg, div):
    obs_data = get_observance_data(pid)
    score    = calculer_score_observance(pid)
    badge    = get_observance_badge(score)
    jsr      = jours_sans_reponse(pid)
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0a1628,#1e3a5f);border-radius:18px;padding:28px 32px;margin-bottom:24px;">
        <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <div style="flex:1;">
                <div style="font-size:0.72rem;color:rgba(255,255,255,0.5);font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Score d'Observance — 7 derniers jours</div>
                <div style="display:flex;align-items:baseline;gap:8px;">
                    <span style="font-family:'DM Serif Display',serif;font-size:3.5rem;color:{badge['color']};line-height:1;">{score}</span>
                    <span style="font-size:1.2rem;color:rgba(255,255,255,0.4);">/100</span>
                </div>
                <span style="background:{badge['bg']};color:{badge['color']};font-weight:700;padding:4px 14px;border-radius:20px;font-size:0.82rem;">{badge['label']}</span>
            </div>
            <div style="background:rgba(255,255,255,0.06);border-radius:12px;padding:16px 20px;min-width:200px;">
                <div style="font-size:0.72rem;color:rgba(255,255,255,0.5);font-weight:700;margin-bottom:8px;">TENDANCE 28 JOURS</div>
                {"<div style='color:#f87171;font-weight:600;font-size:0.9rem;'>⚠️ " + str(jsr) + " jours sans réponse</div>" if jsr >= 2 else "<div style='color:#4ade80;font-weight:600;font-size:0.9rem;'>✅ Questionnaires à jour</div>"}
                <div style="font-size:0.78rem;color:rgba(255,255,255,0.4);margin-top:4px;">{badge['desc']}</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    hist_scores = [d["score"] if d["submitted"] else None for d in obs_data["history"]]
    df_obs = pd.DataFrame({"Score d'observance": pd.to_numeric(hist_scores, errors="coerce")})
    st.caption("📈 Historique d'observance — 28 derniers jours")
    st.area_chart(df_obs, height=130, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📝 Questionnaire du Jour")
    st.caption("Remplissez chaque soir — 2 minutes suffisent pour maintenir votre protocole")
    with st.form(f"form_questionnaire_{pid}"):
        col1, col2 = st.columns(2)
        with col1:
            brossage = st.select_slider("🦷 Brossage aujourd'hui", options=[0,1,2,3], value=2,
                                         format_func=lambda x: f"{x}× par jour")
            fil      = st.checkbox("🧵 Fil dentaire utilisé")
            probio   = st.checkbox("💊 Probiotiques pris")
        with col2:
            sucres = st.select_slider("🍬 Sucres rapides", options=["Aucun","1-2 fois","3+ fois"], value="1-2 fois")
            tabac  = st.checkbox("🚭 Tabac aujourd'hui (cochez si oui)")
            eau    = st.select_slider("💧 Eau (litres)", options=[0.0,0.5,1.0,1.5,2.0,2.5,3.0], value=1.5)
        ressenti = st.select_slider("😊 Ressenti global", options=["Très difficile","Difficile","Neutre","Bien","Excellent"], value="Bien")
        if st.form_submit_button("✅ Soumettre mon questionnaire du jour", use_container_width=True, type="primary"):
            s_brossage = min(100, (brossage / 2) * 100)
            s_fil      = 100 if fil    else 30
            s_probio   = 100 if probio else 40
            s_sucres   = {"Aucun":100,"1-2 fois":60,"3+ fois":20}[sucres]
            s_tabac    = 20  if tabac  else 100
            s_eau      = min(100, (eau / 1.5) * 100)
            score_today = round(0.25*s_brossage + 0.20*s_fil + 0.20*s_probio + 0.15*s_sucres + 0.10*s_tabac + 0.10*s_eau)
            st.session_state.observance[pid]["history"].append(
                {"date": date.today().strftime("%d/%m/%Y"), "score": score_today, "submitted": True})
            st.success(f"✅ Score du jour : **{score_today}/100** — Merci pour votre régularité !")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 🔮 Prédiction Microbiome si vous maintenez ce rythme")
    pred = predire_prochain_score_microbiome(sm, pg, div, score)
    p_cols = st.columns(3)
    for col, (label, actuel, prevu, good_lower) in zip(p_cols, [
        ("S. mutans", pred["sm_actuel"], pred["sm_prevu"], True),
        ("P. gingivalis", pred["pg_actuel"], pred["pg_prevu"], True),
        ("Diversité", pred["div_actuel"], pred["div_prevu"], False),
    ]):
        amelio = (prevu < actuel) if good_lower else (prevu > actuel)
        color  = "#16a34a" if amelio else "#dc2626"
        arrow  = "↓" if (good_lower and amelio) or (not good_lower and not amelio) else "↑"
        unit   = "%" if "mutans" in label or "gingivalis" in label else "/100"
        col.markdown(f"""<div style="background:#f8fafc;border:1.5px solid {color}30;border-radius:12px;padding:14px;text-align:center;">
            <div style="font-size:0.7rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin-bottom:6px;">{label}</div>
            <div style="font-size:1.1rem;color:#374151;">{actuel}{unit} → <b style="color:{color};">{prevu}{unit}</b></div>
            <div style="font-size:1.6rem;color:{color};">{arrow}</div>
            <div style="font-size:0.7rem;color:#9ca3af;">horizon : {pred['horizon']}</div></div>""", unsafe_allow_html=True)
    st.caption(f"🔮 Prédiction basée sur votre observance actuelle ({score}/100) · Confiance : **{pred['confiance']}**")

def render_observance_praticien(patient):
    pid   = patient["id"]
    sm    = patient["s_mutans"]; pg = patient["p_gingivalis"]; div = patient["diversite"]
    score = calculer_score_observance(pid)
    jsr   = jours_sans_reponse(pid)
    badge = get_observance_badge(score)
    obs_data = get_observance_data(pid)

    if jsr >= 3:
        st.markdown(f"""<div style="background:linear-gradient(135deg,#fef2f2,#fee2e2);border:2px solid #dc2626;border-radius:14px;padding:18px 22px;margin-bottom:20px;display:flex;align-items:center;gap:16px;">
            <span style="font-size:2rem;">🚨</span>
            <div><div style="font-weight:700;color:#991b1b;font-size:1rem;">Décrochage détecté — {patient['nom']}</div>
            <div style="color:#b91c1c;font-size:0.88rem;margin-top:3px;">{jsr} jours sans questionnaire. Risque de régression du protocole.</div>
            <div style="color:#dc2626;font-size:0.82rem;margin-top:4px;">👉 Action recommandée : Envoyer un message de rappel au patient</div></div></div>""", unsafe_allow_html=True)

    col_score, col_pred, col_chart = st.columns([1, 1, 2])
    with col_score:
        st.markdown(f"""<div style="background:{badge['bg']};border:2px solid {badge['color']}40;border-radius:14px;padding:20px;text-align:center;height:100%;">
            <div style="font-size:0.7rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin-bottom:8px;">Observance — 7j</div>
            <div style="font-family:'DM Serif Display',serif;font-size:3rem;color:{badge['color']};line-height:1;">{score}</div>
            <div style="font-size:0.7rem;color:#9ca3af;">/100</div>
            <div style="margin-top:8px;"><span style="background:{badge['color']}20;color:{badge['color']};font-weight:700;padding:3px 10px;border-radius:20px;font-size:0.78rem;">{badge['label']}</span></div>
            <div style="margin-top:10px;font-size:0.78rem;color:#6b7280;">Dernier questionnaire :<br><b>{"Aujourd'hui" if jsr == 0 else f"Il y a {jsr} jour{'s' if jsr > 1 else ''}"}</b></div></div>""", unsafe_allow_html=True)
    with col_pred:
        pred = predire_prochain_score_microbiome(sm, pg, div, score)
        st.markdown(f"""<div style="background:#f0f9ff;border:1.5px solid #bae6fd;border-radius:14px;padding:18px;height:100%;">
            <div style="font-size:0.72rem;color:#0369a1;font-weight:700;text-transform:uppercase;margin-bottom:10px;">🔮 Prédiction Microbiome</div>
            <div style="font-size:0.85rem;color:#0c4a6e;margin-bottom:8px;">
                S. mutans : {pred['sm_actuel']}% → <b>{pred['sm_prevu']}%</b><br>
                P. gingivalis : {pred['pg_actuel']}% → <b>{pred['pg_prevu']}%</b><br>
                Diversité : {pred['div_actuel']} → <b>{pred['div_prevu']}/100</b></div>
            <div style="background:#e0f2fe;border-radius:8px;padding:8px 10px;font-size:0.78rem;color:#0369a1;">
                Horizon : <b>{pred['horizon']}</b> · Confiance : <b>{pred['confiance']}</b></div></div>""", unsafe_allow_html=True)
    with col_chart:
        hist_scores = [d["score"] if d["submitted"] else None for d in obs_data["history"][-28:]]
        df_obs = pd.DataFrame({"Observance (%)": pd.to_numeric(hist_scores, errors="coerce")})
        st.caption("📈 Courbe d'observance — 28 jours")
        st.line_chart(df_obs, height=160, use_container_width=True)

    if st.button("📱 Envoyer rappel SMS au patient", use_container_width=True, type="primary"):
        st.success(f"📱 Rappel envoyé à {patient.get('telephone','le patient')}")


# ══════════════════════════════════════════════════════════════
# FONCTIONNALITÉ 2 — INTERACTIONS MÉDICAMENTEUSES
# ══════════════════════════════════════════════════════════════

INTERACTIONS_MEDICAMENTS = {
    "metformine": {
        "nom_generique":"Metformine (Biguanide)","classe":"Antidiabétique","icone":"🩸",
        "effets_oraux":[
            {"effet":"Xérostomie légère","mecanisme":"Réduction modérée du flux salivaire","impact_microbiome":"S. mutans +15% — risque carieux modérément augmenté","severite":"modere"},
            {"effet":"Goût métallique","mecanisme":"Excrétion salivaire du médicament","impact_microbiome":"Modification pH salivaire","severite":"faible"},
        ],
        "recommandations":["Fluoration préventive renforcée","Surveillance S. mutans à 6 mois","Hydratation optimale (≥ 1.5L/j)"],
        "probiotique_cible":"Lactobacillus reuteri DSM 17938 — Limite la prolifération de S. mutans en contexte hyperglycémique",
    },
    "lisinopril": {
        "nom_generique":"Lisinopril (IEC)","classe":"Antihypertenseur — Inhibiteur de l'enzyme de conversion","icone":"❤️",
        "effets_oraux":[
            {"effet":"Toux sèche chronique","mecanisme":"Accumulation de bradykinine","impact_microbiome":"Modifications pH oropharyngé","severite":"modere"},
            {"effet":"Œdème angioneurotique (rare)","mecanisme":"Bradykinine élevée","impact_microbiome":"Inflammation muqueuse","severite":"alerte"},
            {"effet":"Xérostomie modérée","mecanisme":"Réduction flux salivaire","impact_microbiome":"S. mutans +25%, P. gingivalis +20%","severite":"modere"},
        ],
        "recommandations":["⚠️ Substitut salivaire (Biotène, Xerostom)","Probiotiques oraux prioritaires","Contrôle microbiome tous les 4 mois","Signaler l'œdème en urgence"],
        "probiotique_cible":"Streptococcus salivarius K12 — Restaure le flux salivaire et protège la muqueuse",
    },
    "amlodipine": {
        "nom_generique":"Amlodipine (Inhibiteur calcique)","classe":"Antihypertenseur — Inhibiteur calcique","icone":"❤️",
        "effets_oraux":[
            {"effet":"Hyperplasie gingivale","mecanisme":"Prolifération des fibroblastes gingivaux","impact_microbiome":"P. gingivalis +40% dans les poches profondes — risque parodontal sévère","severite":"alerte"},
            {"effet":"Xérostomie","mecanisme":"Action sur les glandes salivaires","impact_microbiome":"Diversité microbienne −20%","severite":"modere"},
        ],
        "recommandations":["🚨 Surveillance parodontale rapprochée (tous les 3 mois)","Détartrage préventif systématique","Envisager changement de molécule avec cardiologue si hyperplasie sévère","Brossage interdentaire quotidien obligatoire"],
        "probiotique_cible":"L. reuteri + L. salivarius — Réduit l'inflammation gingivale induite par les bloqueurs calciques",
    },
    "sertraline": {
        "nom_generique":"Sertraline (ISRS)","classe":"Antidépresseur — Inhibiteur sélectif de la recapture de sérotonine","icone":"🧠",
        "effets_oraux":[
            {"effet":"Xérostomie importante","mecanisme":"Inhibition parasympathique forte","impact_microbiome":"S. mutans +30%, diversité −25% — risque carieux élevé","severite":"alerte"},
            {"effet":"Bruxisme","mecanisme":"Hyperactivité sérotoninergique nocturne","impact_microbiome":"Usure dentaire accélérée","severite":"modere"},
            {"effet":"Dysgueusie","mecanisme":"Altération perception gustative","impact_microbiome":"Modifications comportement alimentaire","severite":"faible"},
        ],
        "recommandations":["🚨 Substitut salivaire obligatoire (spray nocturne)","Gouttière anti-bruxisme envisagée","Fluoration professionnelle tous les 3 mois","Probiotiques en priorité absolue"],
        "probiotique_cible":"Blis M18 (S. salivarius M18) — Action reminéralisante synergique avec les traitements ISRS",
    },
    "bisphosphonate": {
        "nom_generique":"Bisphosphonates (Alendronate, Zolédronate...)","classe":"Traitement ostéoporose / Oncologie osseuse","icone":"🦴",
        "effets_oraux":[
            {"effet":"Ostéonécrose de la mâchoire — risque grave","mecanisme":"Inhibition du remodelage osseux des maxillaires","impact_microbiome":"Dysbiose locale sévère en cas d'infection","severite":"alerte"},
            {"effet":"Ulcérations muqueuses","mecanisme":"Irritation locale","impact_microbiome":"Porte d'entrée pour P. gingivalis","severite":"modere"},
        ],
        "recommandations":["🚨 CONTRE-INDICATION aux extractions sans bilan préalable","Bilan dentaire complet AVANT traitement","Coordination OBLIGATOIRE avec prescripteur","Antibioprophylaxie avant actes invasifs"],
        "probiotique_cible":"Probiotiques doux uniquement après validation médicale — L. acidophilus",
    },
    "cortisone": {
        "nom_generique":"Corticoïdes systémiques (Prednisone, Dexaméthasone...)","classe":"Anti-inflammatoire / Immunosuppresseur","icone":"💊",
        "effets_oraux":[
            {"effet":"Candidose buccale (muguet)","mecanisme":"Immunodépression locale et systémique","impact_microbiome":"Candida albicans prolifération — dysbiose fongique","severite":"alerte"},
            {"effet":"Cicatrisation retardée","mecanisme":"Inhibition de la réponse inflammatoire","impact_microbiome":"Risque surinfection post-soins élevé","severite":"modere"},
            {"effet":"Ostéoporose maxillaire","mecanisme":"Carence calcique induite","impact_microbiome":"Résorption osseuse → P. gingivalis","severite":"modere"},
        ],
        "recommandations":["Rinçage bouche après chaque prise (si inhalé)","Bain de bouche antifongique préventif","Suivi densitométrique osseux","Calcium + Vitamine D3"],
        "probiotique_cible":"L. rhamnosus GG — Prévention de la candidose orale sous corticoïdes",
    },
    "antibioti": {
        "nom_generique":"Antibiotiques à large spectre (Amoxicilline, Augmentin...)","classe":"Antibiotique","icone":"💉",
        "effets_oraux":[
            {"effet":"Dysbiose orale sévère","mecanisme":"Élimination des bactéries commensales protectrices","impact_microbiome":"Diversité −40% sur 3 mois · Candidose fréquente","severite":"alerte"},
            {"effet":"Réémergence pathogènes","mecanisme":"Niche écologique libérée pour pathogènes résistants","impact_microbiome":"S. mutans et P. gingivalis rebounds fréquents","severite":"modere"},
        ],
        "recommandations":["Probiotiques PENDANT et 4 semaines APRÈS l'antibiothérapie","Contrôle microbiome à M3 post-traitement","Éviter les bains de bouche antiseptiques pendant cette période"],
        "probiotique_cible":"Lactobacillus reuteri + Bifidobacterium — Reconstruction du microbiome post-antibiotiques",
    },
}

def detecter_interactions(liste_medicaments_texte):
    if not liste_medicaments_texte: return []
    texte_lower = liste_medicaments_texte.lower()
    return [data for keyword, data in INTERACTIONS_MEDICAMENTS.items() if keyword in texte_lower]

def render_interactions_medicamenteuses(patient, anamnes):
    st.markdown("""<div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:16px;padding:22px 28px;margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:1.8rem;">💊</span>
            <div><div style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:white;">Interactions Médicament → Microbiome Oral</div>
            <div style="font-size:0.82rem;color:rgba(255,255,255,0.6);">Analyse automatique des risques oraux liés aux traitements en cours</div></div></div></div>""", unsafe_allow_html=True)
    pid = patient["id"]
    if not anamnes.get("prend_medicaments") or not anamnes.get("liste_medicaments"):
        st.info("📋 Aucun médicament renseigné dans l'anamnèse.")
        with st.expander("➕ Saisir les médicaments manuellement"):
            med_input = st.text_area("Médicaments", placeholder="Ex: Amlodipine 5mg, Metformine 1000mg, Sertraline 50mg...")
            if st.button("🔍 Analyser les interactions", type="primary"):
                st.session_state[f"med_manual_{pid}"] = med_input
                st.rerun()
        med_text = st.session_state.get(f"med_manual_{pid}", "")
    else:
        med_text = anamnes.get("liste_medicaments","")
        if anamnes.get("antibiotiques_recents"): med_text += " antibioti"
    interactions = detecter_interactions(med_text)
    if not interactions:
        st.success("✅ Aucune interaction médicament-microbiome détectée.")
        st.caption("Base de données : 7 classes médicamenteuses à risque oral connues.")
        return
    nb_alertes = sum(1 for ia in interactions for e in ia["effets_oraux"] if e["severite"] == "alerte")
    nb_moderes = sum(1 for ia in interactions for e in ia["effets_oraux"] if e["severite"] == "modere")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"""<div style="background:#fef2f2;border:1.5px solid #dc2626;border-radius:10px;padding:14px;text-align:center;">
        <div style="font-family:'DM Serif Display',serif;font-size:2.2rem;color:#dc2626;">{len(interactions)}</div>
        <div style="font-size:0.78rem;color:#991b1b;font-weight:600;">Médicaments à risque oral</div></div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div style="background:#fff1f2;border:1.5px solid #f43f5e30;border-radius:10px;padding:14px;text-align:center;">
        <div style="font-family:'DM Serif Display',serif;font-size:2.2rem;color:#e11d48;">{nb_alertes}</div>
        <div style="font-size:0.78rem;color:#be123c;font-weight:600;">Effets critiques détectés</div></div>""", unsafe_allow_html=True)
    c3.markdown(f"""<div style="background:#fffbeb;border:1.5px solid #d9770630;border-radius:10px;padding:14px;text-align:center;">
        <div style="font-family:'DM Serif Display',serif;font-size:2.2rem;color:#d97706;">{nb_moderes}</div>
        <div style="font-size:0.78rem;color:#92400e;font-weight:600;">Effets modérés</div></div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    sev_colors = {"alerte":"#dc2626","modere":"#d97706","faible":"#16a34a"}
    for inter in interactions:
        max_sev = "alerte" if any(e["severite"]=="alerte" for e in inter["effets_oraux"]) else "modere"
        with st.expander(f"{inter['icone']} {inter['nom_generique']} — {inter['classe']}", expanded=(max_sev=="alerte")):
            st.markdown("**Effets connus sur le microbiome oral :**")
            for effet in inter["effets_oraux"]:
                sev = effet["severite"]; bc = sev_colors[sev]
                bg  = "#fef2f2" if sev=="alerte" else "#fffbeb" if sev=="modere" else "#f0fdf4"
                icon = "🚨" if sev=="alerte" else "⚠️" if sev=="modere" else "ℹ️"
                st.markdown(f"""<div style="background:{bg};border-left:4px solid {bc};border-radius:8px;padding:12px 16px;margin:8px 0;">
                    <div style="font-weight:700;color:{bc};font-size:0.9rem;">{icon} {effet['effet']}</div>
                    <div style="font-size:0.82rem;color:#374151;margin-top:4px;"><b>Mécanisme :</b> {effet['mecanisme']}</div>
                    <div style="font-size:0.82rem;color:#6b7280;margin-top:2px;"><b>Impact microbiome :</b> {effet['impact_microbiome']}</div></div>""", unsafe_allow_html=True)
            st.markdown("**Recommandations cliniques :**")
            for reco in inter["recommandations"]: st.markdown(f"- {reco}")
            st.markdown(f"""<div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:1px solid #16a34a40;border-radius:10px;padding:12px 16px;margin-top:8px;">
                <div style="font-size:0.72rem;color:#166534;font-weight:700;text-transform:uppercase;margin-bottom:4px;">🧫 Probiotique Ciblé</div>
                <div style="font-size:0.85rem;color:#14532d;">{inter['probiotique_cible']}</div></div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# FONCTIONNALITÉ 3 — SALLE D'ATTENTE VIRTUELLE
# ══════════════════════════════════════════════════════════════

PREDIAG_PROMPT = """Tu es un assistant clinique dentaire expert. Analyse les données suivantes et génère un pré-diagnostic JSON structuré.
DONNÉES PATIENT : {data}
Réponds UNIQUEMENT en JSON valide, sans markdown ni backticks :
{{"statut_global":"Stable|Surveillance|Urgence","score_risque_global":0,"priorites_cliniques":[{{"zone":"...","observation":"...","urgence":"immediate|sous_48h|prochaine_visite","examens":["..."]}}],"points_attention":["..."],"questions_a_poser":["..."],"ordre_examen_suggere":["..."],"message_accueil":"Message chaleureux personnalisé (2-3 phrases, ton bienveillant)"}}"""

def generer_prediag_ia(patient_data, anamnes, photo_result=None):
    if not ANTHROPIC_API_KEY: return {"error":"Clé API manquante"}
    data_str = json.dumps({"nom":patient_data.get("nom"),"age":patient_data.get("age"),
        "s_mutans":patient_data.get("s_mutans"),"p_gingivalis":patient_data.get("p_gingivalis"),
        "diversite":patient_data.get("diversite"),"anamnes":anamnes,"photo_analyse":photo_result},
        ensure_ascii=False, indent=2)
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":1500,
                  "messages":[{"role":"user","content":PREDIAG_PROMPT.format(data=data_str)}]}, timeout=30)
        r.raise_for_status()
        raw = r.json()["content"][0]["text"].strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e: return {"error": str(e)}

def render_salle_attente_patient(patient):
    st.markdown("""<div style="background:linear-gradient(135deg,#0f4c75,#1b6ca8);border-radius:20px;padding:32px 36px;margin-bottom:28px;text-align:center;">
        <div style="font-size:2.5rem;margin-bottom:10px;">🏥</div>
        <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:white;margin-bottom:6px;">Salle d'Attente Virtuelle</div>
        <div style="color:rgba(255,255,255,0.7);font-size:0.9rem;">Préparez votre visite en 3 étapes · Votre dentiste vous attend prêt</div></div>""", unsafe_allow_html=True)
    key   = f"preatend_{patient['id']}"
    if key not in st.session_state:
        st.session_state[key] = {"step":1,"anamnes_done":False,"photo_done":False,"photo_result":None}
    pdata = st.session_state[key]
    steps = ["📋 Anamnèse","📸 Photo IA","✅ Confirmé"]
    step  = pdata["step"]
    cols_step = st.columns(3)
    for i, (col, s_label) in enumerate(zip(cols_step, steps), 1):
        done   = i < step; active = i == step
        bg = "#16a34a" if done else "#2563eb" if active else "#e5e7eb"
        tc = "white" if (done or active) else "#9ca3af"
        col.markdown(f'<div style="background:{bg};border-radius:10px;padding:10px;text-align:center;"><div style="color:{tc};font-weight:700;font-size:0.85rem;">{"✓ " if done else ""}{s_label}</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if step == 1:
        st.markdown("### 📋 Étape 1 — Vérifiez votre anamnèse")
        anamnes_exist = st.session_state.anamnes.get(patient["nom"],{}).get("completed_at")
        if anamnes_exist:
            st.success(f"✅ Questionnaire déjà rempli le {anamnes_exist[:10]}.")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Mettre à jour", use_container_width=True): pdata["anamnes_done"] = False
            with col_b:
                if st.button("Continuer →", use_container_width=True, type="primary"):
                    pdata["step"] = 2; pdata["anamnes_done"] = True; st.rerun()
        else:
            st.info("📝 Remplissez votre questionnaire de santé (onglet **Mon Anamnèse**), puis revenez ici.")
            if st.button("J'ai rempli mon questionnaire →", type="primary", use_container_width=True):
                pdata["step"] = 2; pdata["anamnes_done"] = True; st.rerun()
    elif step == 2:
        st.markdown("### 📸 Étape 2 — Photo de votre bouche")
        st.caption("Bonne lumière · Bouche grande ouverte · Photo nette (JPEG/PNG)")
        uploaded = st.file_uploader("Votre photo", type=["jpg","jpeg","png"], label_visibility="collapsed")
        if uploaded:
            img_bytes = uploaded.read(); mime = "image/png" if uploaded.name.endswith(".png") else "image/jpeg"
            col_img, col_res = st.columns([1, 2])
            with col_img: st.image(img_bytes, use_container_width=True)
            with col_res:
                if not pdata.get("photo_result"):
                    with st.spinner("Analyse IA en cours..."):
                        pdata["photo_result"] = analyser_photo_bouche(img_bytes, mime)
                    st.rerun()
                else:
                    result = pdata["photo_result"]
                    score  = result.get("score_global",50); profil = result.get("profil_visuel","N/A")
                    c_s    = "#16a34a" if score >= 70 else "#d97706" if score >= 45 else "#e11d48"
                    st.markdown(f'<div style="background:linear-gradient(135deg,{c_s}15,{c_s}08);border:2px solid {c_s}40;border-radius:12px;padding:16px;text-align:center;"><div style="font-family:\'DM Serif Display\',serif;font-size:2.5rem;color:{c_s};">{score}/100</div><div style="font-size:0.85rem;color:#374151;font-weight:600;">{profil}</div></div>', unsafe_allow_html=True)
                    for f in result.get("findings",[]):
                        sev = f.get("severite","normal")
                        icon = "🔴" if sev=="alerte" else "🟡" if sev=="attention" else "🟢"
                        st.markdown(f"<small>{icon} **{f.get('zone','')}** — {f.get('observation','')}</small>", unsafe_allow_html=True)
        col_back, col_next = st.columns(2)
        with col_back:
            if st.button("← Retour", use_container_width=True): pdata["step"] = 1; st.rerun()
        with col_next:
            label = "Passer et continuer →" if not pdata.get("photo_result") else "Continuer →"
            if st.button(label, use_container_width=True, type="primary"):
                pdata["step"] = 3; pdata["photo_done"] = True; st.rerun()
    elif step == 3:
        st.markdown("### ✅ Vous êtes prêt(e) !")
        st.success("🎉 Vos informations ont bien été transmises à votre praticien.")
        st.markdown(f"""<div style="background:#f0fdf4;border:1.5px solid #16a34a40;border-radius:14px;padding:24px;margin:16px 0;">
            <div style="font-family:'DM Serif Display',serif;font-size:1.1rem;color:#14532d;margin-bottom:10px;">📋 Récapitulatif transmis</div>
            <div style="font-size:0.85rem;color:#374151;">
                {"✅ Anamnèse envoyée" if pdata.get("anamnes_done") else "⚠️ Anamnèse non remplie"}<br>
                {"✅ Photo analysée par IA" if pdata.get("photo_result") else "⚠️ Photo non fournie"}<br>
                ✅ Dossier microbiome disponible</div></div>
        <div style="background:#eff6ff;border-radius:10px;padding:14px 18px;font-size:0.85rem;color:#1e40af;">
            💡 <b>Votre dentiste connaît déjà vos priorités</b> et peut commencer l'examen immédiatement.</div>""", unsafe_allow_html=True)

def render_salle_attente_praticien(patient):
    st.markdown("""<div style="background:linear-gradient(135deg,#0f4c75,#1b6ca8);border-radius:16px;padding:20px 28px;margin-bottom:20px;">
        <div style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:white;">🏥 Salle d'Attente Virtuelle — Pré-diagnostic IA</div>
        <div style="font-size:0.82rem;color:rgba(255,255,255,0.65);">Généré automatiquement à partir des données patient · Avant la visite</div></div>""", unsafe_allow_html=True)
    pid      = patient["id"]
    anamnes  = st.session_state.anamnes.get(patient["nom"],{})
    key_prea = f"preatend_{pid}"
    photo_result = st.session_state.get(key_prea,{}).get("photo_result")
    for col, (label, ready, icon) in zip(st.columns(3), [
        ("Anamnèse", bool(anamnes.get("completed_at")), "📋"),
        ("Photo IA",  bool(photo_result), "📸"),
        ("Microbiome", True, "🧬"),
    ]):
        bg = "#f0fdf4" if ready else "#fef2f2"
        bc = "#16a34a" if ready else "#dc2626"
        col.markdown(f'<div style="background:{bg};border:1.5px solid {bc}40;border-radius:10px;padding:14px;text-align:center;"><div style="font-size:1.4rem;">{icon}</div><div style="font-weight:600;font-size:0.85rem;margin-top:4px;">{label}</div><div style="font-size:0.78rem;color:{bc};font-weight:700;">{"✅ Reçu" if ready else "⏳ En attente"}</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    cache_key = f"prediag_{pid}"
    if cache_key not in st.session_state: st.session_state[cache_key] = None
    if st.session_state[cache_key] is None:
        if st.button("🤖 Générer le Pré-diagnostic IA", type="primary", use_container_width=True):
            with st.spinner("L'IA analyse le dossier complet..."):
                st.session_state[cache_key] = generer_prediag_ia(patient, anamnes, photo_result)
            st.rerun()
    else:
        prediag = st.session_state[cache_key]
        if "error" in prediag:
            st.error(f"Erreur IA : {prediag['error']}")
        else:
            statut  = prediag.get("statut_global","Surveillance")
            score_g = prediag.get("score_risque_global",50)
            sc      = {"Stable":"#16a34a","Surveillance":"#d97706","Urgence":"#dc2626"}.get(statut,"#d97706")
            st.markdown(f"""<div style="background:linear-gradient(135deg,{sc}15,{sc}08);border:2px solid {sc}40;border-radius:14px;padding:20px 24px;margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div><div style="font-size:0.72rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin-bottom:4px;">Statut Pré-visite</div>
                    <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:{sc};">{statut}</div></div>
                    <div style="text-align:right;"><div style="font-family:'DM Serif Display',serif;font-size:2.5rem;color:{sc};">{score_g}</div>
                    <div style="font-size:0.72rem;color:#9ca3af;">Score risque</div></div></div>
                <div style="margin-top:12px;padding:10px 14px;background:rgba(255,255,255,0.7);border-radius:8px;font-size:0.88rem;color:#374151;font-style:italic;">
                    💬 "{prediag.get('message_accueil','')}"</div></div>""", unsafe_allow_html=True)
            if prediag.get("priorites_cliniques"):
                st.markdown("#### 🎯 Priorités Cliniques — Ordre d'examen suggéré")
                urg_c = {"immediate":"#dc2626","sous_48h":"#d97706","prochaine_visite":"#2563eb"}
                urg_l = {"immediate":"🚨 IMMÉDIAT","sous_48h":"⚠️ SOUS 48H","prochaine_visite":"📅 CETTE VISITE"}
                for i, prio in enumerate(prediag["priorites_cliniques"], 1):
                    urg = prio.get("urgence","prochaine_visite")
                    uc  = urg_c.get(urg,"#2563eb"); ul = urg_l.get(urg,"📅")
                    badges = "".join(f'<span style="background:#dbeafe;color:#1e40af;font-size:0.72rem;padding:2px 8px;border-radius:10px;margin:2px;display:inline-block;">{ex}</span>' for ex in prio.get("examens",[]))
                    st.markdown(f"""<div style="background:#fff;border:1px solid {uc}30;border-left:4px solid {uc};border-radius:10px;padding:14px 18px;margin:8px 0;">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
                            <div style="font-weight:700;color:#111827;">#{i} — {prio.get('zone','')}</div>
                            <span style="background:{uc}15;color:{uc};font-size:0.72rem;font-weight:700;padding:2px 8px;border-radius:12px;">{ul}</span></div>
                        <div style="font-size:0.85rem;color:#374151;">{prio.get('observation','')}</div>
                        {badges}</div>""", unsafe_allow_html=True)
            if prediag.get("questions_a_poser"):
                with st.expander("❓ Questions suggérées pour l'entretien patient"):
                    for q in prediag["questions_a_poser"]: st.markdown(f"- {q}")
            if prediag.get("points_attention"):
                with st.expander("📌 Points d'attention cliniques"):
                    for p in prediag["points_attention"]: st.markdown(f"- {p}")
        if st.button("🔄 Régénérer l'analyse IA", use_container_width=True):
            st.session_state[cache_key] = None; st.rerun()
    st.markdown("---")
    st.markdown("#### 📨 Inviter le patient à pré-remplir son dossier")
    invite_url = f"https://app.oralbiome.com/salle-attente/{patient.get('code_patient','')}"
    st.markdown(f"""<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:14px 18px;">
        <div style="font-size:0.78rem;color:#0369a1;font-weight:600;margin-bottom:6px;">🔗 Lien salle d'attente virtuelle</div>
        <div style="font-family:monospace;font-size:0.82rem;background:white;padding:6px 10px;border-radius:6px;border:1px solid #dbeafe;">{invite_url}</div>
        <div style="font-size:0.75rem;color:#0369a1;margin-top:6px;">À envoyer par SMS/email 24h avant la visite</div></div>""", unsafe_allow_html=True)
    col_sms, col_email = st.columns(2)
    with col_sms:
        if st.button("📱 Envoyer par SMS", use_container_width=True): st.success(f"📱 SMS envoyé à {patient.get('telephone','')}")
    with col_email:
        if st.button("📧 Envoyer par Email", use_container_width=True): st.success(f"📧 Email envoyé à {patient.get('email','')}")


# ══════════════════════════════════════════════════════════════
# FONCTIONNALITÉ 4 — OBJETS CONNECTÉS (IoT)
# ══════════════════════════════════════════════════════════════

BROSSES_COMPATIBLES = {
    "oral_b_io":      {"nom":"Oral-B iO Series 9","marque":"Oral-B / Braun","icone":"🪥","couleur":"#005B8E","api_disponible":True},
    "philips_sonicare":{"nom":"Philips Sonicare 9900 Prestige","marque":"Philips","icone":"🦷","couleur":"#0066A1","api_disponible":True},
    "colgate_e1":     {"nom":"Colgate E1","marque":"Colgate","icone":"🪥","couleur":"#E31C25","api_disponible":False},
    "manuel":         {"nom":"Brosse manuelle / Saisie manuelle","marque":"Saisie manuelle","icone":"✏️","couleur":"#6b7280","api_disponible":False},
}

def get_iot_data(pid):
    if "iot_data" not in st.session_state: st.session_state.iot_data = {}
    if pid not in st.session_state.iot_data:
        data = {"brosse_type":"oral_b_io","connecte":False,"historique":[]}
        for i in range(30, 0, -1):
            day = date.today() - timedelta(days=i)
            nb  = random.choices([0,1,2,3], weights=[5,20,65,10])[0]
            data["historique"].append({
                "date": day.strftime("%d/%m/%Y"),
                "duree_brossage":   random.randint(60,150) if nb > 0 else 0,
                "pression":         random.randint(100,280),
                "zones_couvertes":  random.randint(55,95),
                "technique":        random.randint(50,95),
                "frequence_quotidienne": nb,
            })
        st.session_state.iot_data[pid] = data
    return st.session_state.iot_data[pid]

def calculer_score_hygiene_iot(iot_data):
    hist = iot_data["historique"][-14:]
    if not hist: return 0
    scores = []
    for day in hist:
        if day["frequence_quotidienne"] == 0: scores.append(0); continue
        s_d = min(100, (day.get("duree_brossage",0) / 120) * 100)
        s_p = 100 if day.get("pression",200) <= 200 else max(0, 100 - (day["pression"]-200)/2)
        s_z = day.get("zones_couvertes",70)
        s_f = min(100, (day["frequence_quotidienne"]/2)*100)
        scores.append(round(0.3*s_d + 0.2*s_p + 0.3*s_z + 0.2*s_f))
    return round(sum(scores)/len(scores)) if scores else 0

def render_iot_dashboard(patient):
    pid       = patient["id"]
    sm        = patient["s_mutans"]; pg = patient["p_gingivalis"]
    iot_data  = get_iot_data(pid)
    b_info    = BROSSES_COMPATIBLES.get(iot_data["brosse_type"], BROSSES_COMPATIBLES["manuel"])
    iot_score = calculer_score_hygiene_iot(iot_data)
    sc        = "#4ade80" if iot_score >= 75 else "#fbbf24" if iot_score >= 55 else "#f87171"
    sm_pot    = round(max(0.1, sm  * (1 - (iot_score/100) * 0.25)), 2)
    pg_pot    = round(max(0.02,pg  * (1 - (iot_score/100) * 0.30)), 2)

    st.markdown(f"""<div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:16px;padding:22px 28px;margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <div style="background:{b_info['couleur']};border-radius:12px;padding:10px 14px;font-size:1.8rem;">{b_info['icone']}</div>
            <div><div style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:white;">Objets Connectés · {b_info['nom']}</div>
            <div style="font-size:0.82rem;color:rgba(255,255,255,0.6);">{b_info['marque']} · {"🔗 Connecté" if iot_data["connecte"] else "⚫ Non connecté — Données démo"}</div></div>
            <div style="margin-left:auto;background:rgba(255,255,255,0.1);border-radius:10px;padding:8px 14px;text-align:center;">
                <div style="font-size:0.7rem;color:rgba(255,255,255,0.5);text-transform:uppercase;font-weight:700;">Score Hygiène</div>
                <div style="font-family:'DM Serif Display',serif;font-size:2rem;color:{sc};">{iot_score}/100</div>
            </div></div></div>""", unsafe_allow_html=True)

    # Connexion appareil
    with st.expander("🔗 Connecter un appareil", expanded=not iot_data["connecte"]):
        brosse_sel = st.selectbox("Type d'appareil", options=list(BROSSES_COMPATIBLES.keys()),
            format_func=lambda k: f"{BROSSES_COMPATIBLES[k]['icone']} {BROSSES_COMPATIBLES[k]['nom']}",
            index=list(BROSSES_COMPATIBLES.keys()).index(iot_data["brosse_type"]))
        bi = BROSSES_COMPATIBLES[brosse_sel]
        if bi["api_disponible"]:
            col_a, col_b = st.columns(2)
            with col_a: st.text_input(f"Email {bi['marque']} App", placeholder="votre@email.com")
            with col_b:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"Connecter {bi['nom']}", type="primary", use_container_width=True):
                    st.session_state.iot_data[pid]["brosse_type"] = brosse_sel
                    st.session_state.iot_data[pid]["connecte"]    = True
                    st.success(f"✅ {bi['nom']} connecté ! Synchronisation en cours..."); st.rerun()
        else:
            st.info(f"⚠️ {bi['nom']} ne dispose pas encore d'API publique. Saisie manuelle disponible.")
            with st.form(f"form_iot_{pid}"):
                mc1, mc2 = st.columns(2)
                with mc1:
                    duree = st.number_input("Durée brossage (sec)", 0, 300, 120)
                    freq  = st.number_input("Brossages aujourd'hui", 0, 5, 2)
                with mc2:
                    pression_txt = st.select_slider("Pression", options=["Légère","Normale","Forte"], value="Normale")
                    zones = st.slider("Zones couvertes (%)", 0, 100, 80)
                if st.form_submit_button("💾 Sauvegarder", use_container_width=True):
                    p_val = {"Légère":100,"Normale":150,"Forte":250}[pression_txt]
                    st.session_state.iot_data[pid]["historique"].append({
                        "date": date.today().strftime("%d/%m/%Y"), "duree_brossage": duree,
                        "pression": p_val, "zones_couvertes": zones, "technique": 70, "frequence_quotidienne": freq})
                    st.success("✅ Données sauvegardées !"); st.rerun()

    # KPIs
    st.markdown("#### 📊 Métriques — 30 derniers jours")
    hist    = iot_data["historique"]
    h_comp  = [d for d in hist if d["frequence_quotidienne"] > 0]
    if h_comp:
        avg_dur  = round(sum(d["duree_brossage"] for d in h_comp) / len(h_comp))
        avg_pres = round(sum(d["pression"] for d in h_comp) / len(h_comp))
        avg_zon  = round(sum(d["zones_couvertes"] for d in h_comp) / len(h_comp))
        avg_freq = round(sum(d["frequence_quotidienne"] for d in hist) / len(hist), 1)
        jours_b  = sum(1 for d in hist if d["frequence_quotidienne"] > 0)
        kpis = [
            ("⏱️ Durée moy.", f"{avg_dur}s",    "#16a34a" if avg_dur  >= 120 else "#d97706", "Optimal : 120s"),
            ("🤚 Pression",   f"{avg_pres}g",   "#16a34a" if avg_pres <= 200 else "#dc2626", "Max : 200g"),
            ("🗺️ Zones",      f"{avg_zon}%",    "#16a34a" if avg_zon  >= 80  else "#d97706", "Optimal : ≥80%"),
            ("📅 Fréquence",  f"{avg_freq}×/j", "#16a34a" if avg_freq >= 2   else "#dc2626", "Optimal : 2×/j"),
            ("📆 Jours",      f"{jours_b}/30",  "#16a34a" if jours_b  >= 25  else "#d97706", "Optimal : ≥25/30"),
        ]
        cols_kpi = st.columns(5)
        for col, (label, val, color, hint) in zip(cols_kpi, kpis):
            col.markdown(f"""<div style="background:#fff;border:1.5px solid {color}30;border-radius:12px;padding:14px;text-align:center;">
                <div style="font-size:0.7rem;color:#6b7280;font-weight:700;margin-bottom:4px;">{label}</div>
                <div style="font-family:'DM Serif Display',serif;font-size:1.6rem;color:{color};">{val}</div>
                <div style="font-size:0.68rem;color:#9ca3af;">{hint}</div></div>""", unsafe_allow_html=True)

    # Graphiques
    st.markdown("<br>", unsafe_allow_html=True)
    df_iot = pd.DataFrame(iot_data["historique"][-30:])
    if not df_iot.empty:
        gc1, gc2 = st.columns(2)
        with gc1:
            st.caption("⏱️ Durée de brossage (secondes)")
            st.area_chart(df_iot[["duree_brossage"]].rename(columns={"duree_brossage":"Durée (sec)"}), height=160)
        with gc2:
            st.caption("🗺️ Zones couvertes (%)")
            st.area_chart(df_iot[["zones_couvertes"]].rename(columns={"zones_couvertes":"Zones (%)"}), height=160)

    # Impact microbiome
    st.markdown("---")
    st.markdown("#### 🧬 Impact Hygiène → Microbiome")
    ic1, ic2, ic3 = st.columns(3)
    sm_c = "#16a34a" if sm_pot < sm else "#dc2626"
    pg_c = "#16a34a" if pg_pot < pg else "#dc2626"
    with ic1:
        st.markdown(f"""<div style="background:#fff;border:1.5px solid {sm_c}30;border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:0.7rem;color:#6b7280;font-weight:700;margin-bottom:6px;">S. MUTANS POTENTIEL</div>
            <div style="font-size:1rem;color:#374151;">{sm}% → <b style="color:{sm_c};">{sm_pot}%</b></div>
            <div style="font-size:0.7rem;color:#9ca3af;margin-top:4px;">avec hygiène optimale</div></div>""", unsafe_allow_html=True)
    with ic2:
        st.markdown(f"""<div style="background:#fff;border:1.5px solid {pg_c}30;border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:0.7rem;color:#6b7280;font-weight:700;margin-bottom:6px;">P. GINGIVALIS POTENTIEL</div>
            <div style="font-size:1rem;color:#374151;">{pg}% → <b style="color:{pg_c};">{pg_pot}%</b></div>
            <div style="font-size:0.7rem;color:#9ca3af;margin-top:4px;">avec hygiène optimale</div></div>""", unsafe_allow_html=True)
    with ic3:
        iot_sc = "#16a34a" if iot_score >= 75 else "#d97706" if iot_score >= 55 else "#dc2626"
        msg_iot = "Excellent niveau d'hygiène" if iot_score >= 80 else "Hygiène correcte — marge de progression" if iot_score >= 60 else "Hygiène insuffisante — risque élevé"
        st.markdown(f"""<div style="background:#fff;border:1.5px solid {iot_sc}30;border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:0.7rem;color:#6b7280;font-weight:700;margin-bottom:6px;">SCORE HYGIÈNE GLOBAL</div>
            <div style="font-family:'DM Serif Display',serif;font-size:2rem;color:{iot_sc};">{iot_score}/100</div>
            <div style="font-size:0.72rem;color:{iot_sc};font-weight:600;margin-top:4px;">{msg_iot}</div></div>""", unsafe_allow_html=True)

    # Conseils personnalisés
    if h_comp:
        conseils = []
        if avg_dur  < 90:  conseils.append({"icon":"⏱️","msg":f"Brossage trop court ({avg_dur}s). Objectif : 2 minutes.","prio":"urgent"})
        if avg_pres > 200: conseils.append({"icon":"🤚","msg":f"Pression excessive ({avg_pres}g) — risque récession gingivale.","prio":"urgent"})
        if avg_zon  < 75:  conseils.append({"icon":"🗺️","msg":f"Zones insuffisantes ({avg_zon}%). Pensez au secteur postérieur.","prio":"modere"})
        if avg_freq < 1.8: conseils.append({"icon":"📅","msg":f"Fréquence insuffisante ({avg_freq}×/j). Objectif : 2×/jour.","prio":"urgent"})
        if not conseils:   conseils.append({"icon":"✅","msg":"Excellente hygiène buccale ! Continuez ainsi.","prio":"ok"})
        st.markdown("---")
        st.markdown("#### 💡 Conseils Personnalisés basés sur vos données")
        for conseil in conseils:
            bg = "#fef2f2" if conseil["prio"]=="urgent" else "#fffbeb" if conseil["prio"]=="modere" else "#f0fdf4"
            bc = "#dc2626" if conseil["prio"]=="urgent" else "#d97706" if conseil["prio"]=="modere" else "#16a34a"
            st.markdown(f'<div style="background:{bg};border-left:4px solid {bc};border-radius:8px;padding:12px 16px;margin:6px 0;font-size:0.88rem;color:#374151;">{conseil["icon"]} {conseil["msg"]}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# MODULE — ANALYSE RADIOLOGIQUE IA
# OPG (Panoramique) + Rétro-alvéolaires
# ══════════════════════════════════════════════════════════════

RADIO_SYSTEM_PROMPT = """Tu es un assistant d'aide à la décision radiologique dentaire expert, formé pour analyser des clichés dentaires.
Tu analyses uniquement dans un cadre d'aide à la décision pour des praticiens qualifiés.

Pour une radio panoramique OPG, analyse :
- Toutes les dents visibles avec leur numérotation FDI (11-18, 21-28, 31-38, 41-48)
- Caries interproximales, occlusales, cervicales
- Perte osseuse alvéolaire (horizontale/verticale, légère <3mm / modérée 3-6mm / sévère >6mm)
- Lésions apicales, granulomes, kystes
- État des dents de sagesse (éruption, inclusions, angulation)
- Qualité des restaurations existantes, couronnes, implants
- Anomalies de structure osseuse, asymétries

Pour une rétro-alvéolaire, analyse avec précision :
- Dents spécifiques visibles
- Caries interproximales (stade 0-4 selon classification internationale)
- Niveau osseux précis (distance jonction amélo-cémentaire → crête alvéolaire)
- Espace desmodontal
- Apex et lésions péri-apicales
- Qualité des restaurations (étanchéité, débords, sous-contours)

Réponds UNIQUEMENT en JSON valide sans markdown ni backtick :
{
  "type_radio": "panoramique|retro_alveolaire",
  "qualite_image": "excellente|bonne|moyenne|insuffisante",
  "dents_visibles": [{"num_fdi": 11, "nom": "Incisive centrale sup droite", "etat_general": "saine|restaurée|cariée|absente|traitée", "present": true}],
  "caries_detectees": [{"dent_fdi": 0, "localisation": "interproximale|occlusale|cervicale|sous-gingivale", "stade": "initiale|modérée|profonde|pulpaire", "urgence": "surveillance|traitement_programme|urgent", "detail": "..."}],
  "perte_osseuse": {"present": true, "type": "horizontale|verticale|mixte|aucune", "severite": "legere|moderee|severe|aucune", "zones_atteintes": ["..."], "mesures_estimees": {"sextant_anterieur": "...", "sextant_posterieur_droit": "...", "sextant_posterieur_gauche": "..."}, "detail": "..."},
  "lesions_apicales": [{"dent_fdi": 0, "type": "granulome|kyste|abces|cicatrice", "taille_mm": 0, "urgence": "surveillance|traitement_endodontique|extraction", "detail": "..."}],
  "sagesses": [{"dent_fdi": 0, "statut": "eruption_normale|inclusion_partielle|inclusion_totale|angulation_mesiale|angulation_distale|absente", "recommandation": "surveillance|extraction_preventive|extraction_urgente|aucune", "detail": "..."}],
  "restaurations": [{"dent_fdi": 0, "type": "composite|amalgame|couronne|inlay|onlay|implant", "qualite": "adequate|a_remplacer|urgente", "detail": "..."}],
  "mesures_cles": {"hauteur_osseuse_ant_mm": null, "hauteur_osseuse_post_d_mm": null, "hauteur_osseuse_post_g_mm": null, "longueur_racine_exemple": null, "note_mesures": "Estimations visuelles uniquement — mesures précises sur logiciel dédié"},
  "anomalies_autres": ["..."],
  "score_global_radio": 0,
  "niveau_urgence_global": "aucune|faible|moderee|elevee|urgence_immediate",
  "rapport_narratif": "Texte clinique structuré de 3-5 paragraphes, professionnel, intégrant tous les findings clés dans l'ordre de priorité clinique.",
  "plan_traitement_suggere": [{"priorite": 1, "acte": "...", "dents": [0], "delai_suggere": "immédiat|sous_2semaines|1_mois|3_mois|6_mois|surveillance", "justification": "..."}],
  "correlation_microbiome": {"p_gingivalis_coherent": true, "s_mutans_coherent": true, "commentaire": "Cohérence entre profil radiologique et données microbiome"},
  "confiance_analyse": "elevee|moderee|faible",
  "disclaimer": "Aide à la décision radiologique. Interprétation définitive par le praticien qualifié sur cliché original."
}"""

def analyser_radio(image_bytes, mime_type, type_radio="panoramique", contexte_patient=None):
    """Analyse radiologique IA via Claude Vision API."""
    if not ANTHROPIC_API_KEY:
        return {"error": "Clé API Anthropic manquante — configurez ANTHROPIC_API_KEY dans les secrets Streamlit."}
    b64 = base64.standard_b64encode(image_bytes).decode()
    ctx = ""
    if contexte_patient:
        ctx = (f"\n\nCONTEXTE PATIENT pour corrélation :\n"
               f"- S. mutans : {contexte_patient.get('s_mutans','N/A')}% (normal < 3%)\n"
               f"- P. gingivalis : {contexte_patient.get('p_gingivalis','N/A')}% (normal < 0.5%)\n"
               f"- Diversité microbienne : {contexte_patient.get('diversite','N/A')}/100\n"
               f"- Âge : {contexte_patient.get('age','N/A')} ans\n"
               f"Utilise ces données pour remplir le champ correlation_microbiome.")
    prompt = f"Analyse cette radiographie dentaire de type {type_radio}.{ctx}\nRéponds en JSON uniquement."
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":3000,"system":RADIO_SYSTEM_PROMPT,
                  "messages":[{"role":"user","content":[
                      {"type":"image","source":{"type":"base64","media_type":mime_type,"data":b64}},
                      {"type":"text","text":prompt}
                  ]}]},
            timeout=45,
        )
        r.raise_for_status()
        raw = r.json()["content"][0]["text"].strip()
        raw = raw.replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"error": f"Réponse IA non parsable : {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


def _urgence_color(urgence):
    return {"urgence_immediate":"#dc2626","elevee":"#ef4444","moderee":"#d97706",
            "faible":"#f59e0b","aucune":"#16a34a","urgent":"#dc2626",
            "traitement_programme":"#d97706","surveillance":"#16a34a"}.get(urgence, "#6b7280")

def _urgence_label(urgence):
    return {"urgence_immediate":"🚨 URGENT","elevee":"🔴 Élevée","moderee":"⚠️ Modérée",
            "faible":"🟡 Faible","aucune":"🟢 Aucune","urgent":"🚨 Urgent",
            "traitement_programme":"📅 Programmé","surveillance":"👁️ Surveillance"}.get(urgence, urgence)

def _stade_color(stade):
    return {"initiale":"#f59e0b","modérée":"#d97706","profonde":"#ef4444","pulpaire":"#dc2626"}.get(stade,"#6b7280")


def render_radio_score_header(result, type_radio):
    score   = result.get("score_global_radio", 50)
    urgence = result.get("niveau_urgence_global", "moderee")
    qualite = result.get("qualite_image", "bonne")
    confiance = result.get("confiance_analyse","moderee")
    sc = "#16a34a" if score >= 75 else "#d97706" if score >= 50 else "#e11d48"
    uc = _urgence_color(urgence)
    ul = _urgence_label(urgence)
    type_label = "Panoramique OPG" if type_radio == "panoramique" else "Rétro-alvéolaire"
    type_icon  = "🌐" if type_radio == "panoramique" else "🦷"
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:18px;padding:24px 32px;margin-bottom:20px;">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;">
            <div>
                <div style="font-size:0.72rem;color:rgba(255,255,255,0.5);font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">{type_icon} Analyse IA · {type_label}</div>
                <div style="font-family:'DM Serif Display',serif;font-size:2rem;color:white;line-height:1;">Rapport Radiologique</div>
                <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;">
                    <span style="background:rgba(255,255,255,0.1);color:rgba(255,255,255,0.8);padding:3px 10px;border-radius:12px;font-size:0.75rem;">📷 Qualité : {qualite}</span>
                    <span style="background:rgba(255,255,255,0.1);color:rgba(255,255,255,0.8);padding:3px 10px;border-radius:12px;font-size:0.75rem;">🎯 Confiance : {confiance}</span>
                </div>
            </div>
            <div style="display:flex;gap:16px;align-items:center;">
                <div style="background:rgba(255,255,255,0.08);border-radius:14px;padding:16px 20px;text-align:center;">
                    <div style="font-size:0.68rem;color:rgba(255,255,255,0.5);text-transform:uppercase;font-weight:700;margin-bottom:4px;">Score Radio</div>
                    <div style="font-family:'DM Serif Display',serif;font-size:2.4rem;color:{sc};line-height:1;">{score}</div>
                    <div style="font-size:0.68rem;color:rgba(255,255,255,0.4);">/100</div>
                </div>
                <div style="background:{uc}22;border:2px solid {uc};border-radius:14px;padding:16px 20px;text-align:center;">
                    <div style="font-size:0.68rem;color:rgba(255,255,255,0.5);text-transform:uppercase;font-weight:700;margin-bottom:4px;">Urgence</div>
                    <div style="font-size:1.1rem;font-weight:800;color:{uc};">{ul}</div>
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)


def render_radio_dents_visibles(result):
    dents = result.get("dents_visibles", [])
    if not dents: return
    st.markdown("#### 🦷 Dents Identifiées")
    # Regrouper par quadrant
    quadrants = {1:[], 2:[], 3:[], 4:[]}
    for d in dents:
        num = d.get("num_fdi", 0)
        if 11 <= num <= 18: quadrants[1].append(d)
        elif 21 <= num <= 28: quadrants[2].append(d)
        elif 31 <= num <= 38: quadrants[3].append(d)
        elif 41 <= num <= 48: quadrants[4].append(d)
    q_labels = {1:"Q1 — Haut Droite",2:"Q2 — Haut Gauche",3:"Q3 — Bas Gauche",4:"Q4 — Bas Droite"}
    q_cols = st.columns(4)
    for q, col in zip([1,2,3,4], q_cols):
        with col:
            st.markdown(f"<div style='font-size:0.72rem;font-weight:700;color:#6b7280;text-transform:uppercase;margin-bottom:6px;'>{q_labels[q]}</div>", unsafe_allow_html=True)
            if not quadrants[q]:
                st.markdown("<div style='font-size:0.78rem;color:#d1d5db;font-style:italic;'>Non visible</div>", unsafe_allow_html=True)
            else:
                for d in sorted(quadrants[q], key=lambda x: x.get("num_fdi",0)):
                    etat = d.get("etat_general","saine")
                    ec = {"saine":"#16a34a","restaurée":"#2563eb","cariée":"#dc2626",
                          "absente":"#94a3b8","traitée":"#7c3aed"}.get(etat,"#6b7280")
                    present = d.get("present", True)
                    op = "1" if present else "0.4"
                    st.markdown(f"""<div style="display:flex;align-items:center;gap:6px;margin:3px 0;opacity:{op};">
                        <div style="background:{ec};color:white;border-radius:5px;padding:1px 6px;font-size:0.7rem;font-weight:800;font-family:monospace;min-width:26px;text-align:center;">{d.get('num_fdi','')}</div>
                        <div style="font-size:0.75rem;color:#374151;">{etat}</div>
                    </div>""", unsafe_allow_html=True)
    nb_presentes = sum(1 for d in dents if d.get("present", True))
    nb_absentes  = sum(1 for d in dents if not d.get("present", True))
    st.caption(f"👁️ {len(dents)} dents analysées · {nb_presentes} présentes · {nb_absentes} absentes/non visibles")


def render_radio_caries(result):
    caries = result.get("caries_detectees", [])
    if not caries:
        st.success("✅ Aucune carie détectée sur ce cliché.")
        return
    nb_urgent = sum(1 for c in caries if c.get("urgence") == "urgent")
    nb_prog   = sum(1 for c in caries if c.get("urgence") == "traitement_programme")
    st.markdown(f"""
    <div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;">
        <div style="background:#fef2f2;border:1.5px solid #dc2626;border-radius:10px;padding:12px 18px;text-align:center;min-width:100px;">
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:#dc2626;">{len(caries)}</div>
            <div style="font-size:0.72rem;color:#991b1b;font-weight:700;">Caries détectées</div>
        </div>
        <div style="background:#fff1f2;border:1.5px solid #f43f5e30;border-radius:10px;padding:12px 18px;text-align:center;min-width:100px;">
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:#e11d48;">{nb_urgent}</div>
            <div style="font-size:0.72rem;color:#be123c;font-weight:700;">Urgentes</div>
        </div>
        <div style="background:#fffbeb;border:1.5px solid #d9770630;border-radius:10px;padding:12px 18px;text-align:center;min-width:100px;">
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:#d97706;">{nb_prog}</div>
            <div style="font-size:0.72rem;color:#92400e;font-weight:700;">Programmées</div>
        </div>
    </div>""", unsafe_allow_html=True)
    for c in sorted(caries, key=lambda x: {"urgent":0,"traitement_programme":1,"surveillance":2}.get(x.get("urgence","surveillance"),3)):
        dent  = c.get("dent_fdi", "?")
        loc   = c.get("localisation", "")
        stade = c.get("stade", "")
        urg   = c.get("urgence", "surveillance")
        detail= c.get("detail", "")
        sc    = _stade_color(stade)
        uc    = _urgence_color(urg)
        st.markdown(f"""<div style="background:#fff;border:1px solid {uc}30;border-left:4px solid {uc};border-radius:10px;padding:14px 18px;margin:8px 0;display:flex;align-items:flex-start;gap:14px;">
            <div style="background:{sc};color:white;border-radius:8px;padding:4px 8px;font-size:0.9rem;font-weight:800;font-family:monospace;flex-shrink:0;min-width:32px;text-align:center;">{dent}</div>
            <div style="flex:1;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:6px;">
                    <div><span style="font-weight:700;color:#111827;">Carie {stade}</span> · <span style="color:#6b7280;font-size:0.85rem;">{loc}</span></div>
                    <span style="background:{uc}15;color:{uc};font-size:0.72rem;font-weight:700;padding:2px 8px;border-radius:10px;">{_urgence_label(urg)}</span>
                </div>
                {f'<div style="font-size:0.83rem;color:#374151;margin-top:4px;">{detail}</div>' if detail else ''}
            </div>
        </div>""", unsafe_allow_html=True)


def render_radio_perte_osseuse(result):
    po = result.get("perte_osseuse", {})
    if not po or not po.get("present", False):
        st.success("✅ Aucune perte osseuse significative détectée.")
        return
    sev   = po.get("severite", "aucune")
    typ   = po.get("type", "horizontale")
    zones = po.get("zones_atteintes", [])
    detail= po.get("detail", "")
    mesures = po.get("mesures_estimees", {})
    sev_c = {"severe":"#dc2626","moderee":"#d97706","legere":"#f59e0b","aucune":"#16a34a"}.get(sev,"#6b7280")
    sev_l = {"severe":"🔴 Sévère (> 6mm)","moderee":"🟠 Modérée (3-6mm)","legere":"🟡 Légère (< 3mm)","aucune":"🟢 Aucune"}.get(sev,"")
    typ_l = {"horizontale":"📐 Horizontale","verticale":"📏 Verticale","mixte":"📊 Mixte","aucune":"Aucune"}.get(typ, typ)
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{sev_c}12,{sev_c}06);border:2px solid {sev_c}40;border-radius:14px;padding:20px 24px;margin-bottom:16px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
            <div>
                <div style="font-size:0.72rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin-bottom:4px;">Perte Osseuse Alvéolaire</div>
                <div style="font-family:'DM Serif Display',serif;font-size:1.6rem;color:{sev_c};">{sev_l}</div>
                <div style="font-size:0.85rem;color:#374151;margin-top:4px;">{typ_l}</div>
            </div>
            <div style="background:rgba(255,255,255,0.8);border-radius:10px;padding:12px 16px;">
                <div style="font-size:0.7rem;color:#6b7280;font-weight:700;margin-bottom:6px;">ZONES ATTEINTES</div>
                {"".join(f'<div style="font-size:0.82rem;color:#374151;margin:2px 0;">• {z}</div>' for z in zones) if zones else '<div style="font-size:0.82rem;color:#9ca3af;">Non précisé</div>'}
            </div>
        </div>
        {f'<div style="margin-top:12px;font-size:0.85rem;color:#374151;border-top:1px solid {sev_c}20;padding-top:10px;">{detail}</div>' if detail else ''}
    </div>""", unsafe_allow_html=True)
    if any(mesures.get(k) for k in ["sextant_anterieur","sextant_posterieur_droit","sextant_posterieur_gauche"]):
        st.markdown("##### 📏 Estimations Hauteur Osseuse")
        mc = st.columns(3)
        for col, (key, label, icon) in zip(mc, [
            ("sextant_anterieur","Sextant Antérieur","⬆️"),
            ("sextant_posterieur_droit","Secteur Postérieur Droit","↗️"),
            ("sextant_posterieur_gauche","Secteur Postérieur Gauche","↖️"),
        ]):
            val = mesures.get(key, "N/A")
            col.markdown(f"""<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:0.7rem;color:#6b7280;font-weight:700;margin-bottom:4px;">{icon} {label}</div>
                <div style="font-size:1rem;font-weight:700;color:#1a3a5c;">{val}</div>
            </div>""", unsafe_allow_html=True)
        st.caption("⚠️ Estimations visuelles — mesures précises sur logiciel radio dédié (Trophy, Romexis, Carestream...)")


def render_radio_lesions_apicales(result):
    lesions = result.get("lesions_apicales", [])
    if not lesions:
        st.success("✅ Aucune lésion péri-apicale détectée.")
        return
    for l in lesions:
        dent   = l.get("dent_fdi", "?")
        typ    = l.get("type", "")
        taille = l.get("taille_mm", "?")
        urg    = l.get("urgence", "surveillance")
        detail = l.get("detail","")
        uc     = _urgence_color(urg)
        typ_icon = {"granulome":"🔵","kyste":"⭕","abces":"🔴","cicatrice":"⬜"}.get(typ,"●")
        st.markdown(f"""<div style="background:#fff;border:1px solid {uc}30;border-left:4px solid {uc};border-radius:10px;padding:14px 18px;margin:8px 0;">
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="background:{uc};color:white;border-radius:8px;padding:4px 8px;font-weight:800;font-family:monospace;font-size:0.9rem;">{dent}</div>
                <div><div style="font-weight:700;">{typ_icon} {typ.capitalize()} ({taille} mm)</div>
                <div style="font-size:0.83rem;color:#6b7280;">{detail}</div></div>
                <span style="margin-left:auto;background:{uc}15;color:{uc};font-size:0.72rem;font-weight:700;padding:2px 8px;border-radius:10px;">{_urgence_label(urg)}</span>
            </div>
        </div>""", unsafe_allow_html=True)


def render_radio_sagesses(result):
    sagesses = result.get("sagesses", [])
    if not sagesses: return
    need_action = [s for s in sagesses if s.get("recommandation") not in ["aucune","surveillance"]]
    if not need_action:
        st.info(f"ℹ️ {len(sagesses)} dent(s) de sagesse — aucune extraction urgente recommandée.")
        return
    for s in sagesses:
        dent   = s.get("dent_fdi","?")
        statut = s.get("statut","")
        reco   = s.get("recommandation","surveillance")
        detail = s.get("detail","")
        rc     = _urgence_color(reco)
        statut_label = statut.replace("_"," ").capitalize()
        reco_label   = reco.replace("_"," ").capitalize()
        st.markdown(f"""<div style="background:#faf5ff;border:1px solid #a855f730;border-left:4px solid #a855f7;border-radius:10px;padding:12px 16px;margin:6px 0;">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="background:#a855f7;color:white;border-radius:6px;padding:2px 7px;font-weight:800;font-family:monospace;">{dent}</div>
                <div><div style="font-weight:600;">{statut_label}</div>
                <div style="font-size:0.82rem;color:#6b7280;">{detail}</div></div>
                <span style="margin-left:auto;background:{rc}15;color:{rc};font-size:0.72rem;font-weight:700;padding:2px 8px;border-radius:10px;">{reco_label}</span>
            </div>
        </div>""", unsafe_allow_html=True)


def render_radio_plan_traitement(result):
    plan = result.get("plan_traitement_suggere", [])
    if not plan:
        st.info("Aucun plan de traitement généré.")
        return
    delai_c = {
        "immédiat":"#dc2626","sous_2semaines":"#ef4444","1_mois":"#d97706",
        "3_mois":"#f59e0b","6_mois":"#2563eb","surveillance":"#16a34a"
    }
    for acte in sorted(plan, key=lambda x: x.get("priorite", 99)):
        prio   = acte.get("priorite", "—")
        nom_a  = acte.get("acte","")
        dents  = acte.get("dents",[])
        delai  = acte.get("delai_suggere","surveillance")
        justif = acte.get("justification","")
        dc     = delai_c.get(delai,"#6b7280")
        dents_str = " · ".join(f"<span style='background:#1a3a5c;color:white;border-radius:4px;padding:1px 5px;font-size:0.7rem;font-family:monospace;'>{d}</span>" for d in dents) if dents else ""
        st.markdown(f"""<div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:16px 20px;margin:8px 0;display:flex;align-items:flex-start;gap:14px;box-shadow:0 1px 4px rgba(0,0,0,0.04);">
            <div style="background:linear-gradient(135deg,#1a3a5c,#2563eb);color:white;border-radius:10px;padding:8px 10px;font-family:'DM Serif Display',serif;font-size:1.3rem;line-height:1;flex-shrink:0;min-width:36px;text-align:center;">{prio}</div>
            <div style="flex:1;">
                <div style="font-weight:700;font-size:0.95rem;color:#111827;margin-bottom:4px;">{nom_a}</div>
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;">
                    {dents_str}
                    <span style="background:{dc}15;color:{dc};font-size:0.72rem;font-weight:700;padding:2px 8px;border-radius:10px;">⏱ {delai.replace('_',' ')}</span>
                </div>
                {f'<div style="font-size:0.83rem;color:#6b7280;font-style:italic;">{justif}</div>' if justif else ''}
            </div>
        </div>""", unsafe_allow_html=True)


def render_radio_correlation_microbiome(result, patient):
    correl = result.get("correlation_microbiome", {})
    if not correl: return
    sm = patient.get("s_mutans",0); pg = patient.get("p_gingivalis",0)
    pg_ok = correl.get("p_gingivalis_coherent", True)
    sm_ok = correl.get("s_mutans_coherent", True)
    commentaire = correl.get("commentaire","")
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#f0f9ff,#e0f2fe);border:1.5px solid #bae6fd;border-radius:14px;padding:18px 22px;">
        <div style="font-size:0.72rem;color:#0369a1;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:12px;">🧬 Corrélation Radiologie ↔ Microbiome</div>
        <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:12px;">
            <div style="background:{'#f0fdf4' if sm_ok else '#fef2f2'};border:1px solid {'#16a34a' if sm_ok else '#dc2626'}40;border-radius:10px;padding:10px 14px;flex:1;min-width:160px;">
                <div style="font-size:0.7rem;font-weight:700;color:{'#166534' if sm_ok else '#991b1b'};margin-bottom:4px;">S. MUTANS ({sm}%)</div>
                <div style="font-size:0.85rem;color:#374151;">{'✅ Cohérent avec la radio' if sm_ok else '⚠️ Divergence possible'}</div>
            </div>
            <div style="background:{'#f0fdf4' if pg_ok else '#fef2f2'};border:1px solid {'#16a34a' if pg_ok else '#dc2626'}40;border-radius:10px;padding:10px 14px;flex:1;min-width:160px;">
                <div style="font-size:0.7rem;font-weight:700;color:{'#166534' if pg_ok else '#991b1b'};margin-bottom:4px;">P. GINGIVALIS ({pg}%)</div>
                <div style="font-size:0.85rem;color:#374151;">{'✅ Cohérent avec la radio' if pg_ok else '⚠️ Divergence possible'}</div>
            </div>
        </div>
        {f'<div style="font-size:0.85rem;color:#0c4a6e;background:rgba(255,255,255,0.7);border-radius:8px;padding:10px 12px;">{commentaire}</div>' if commentaire else ''}
    </div>""", unsafe_allow_html=True)


def render_radio_rapport_narratif(result):
    rapport = result.get("rapport_narratif","")
    if not rapport: return
    st.markdown(f"""
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:24px 28px;line-height:1.75;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
        <div style="font-family:'DM Serif Display',serif;font-size:1.1rem;color:#1a3a5c;margin-bottom:14px;border-bottom:1px solid #e5e7eb;padding-bottom:10px;">📝 Rapport Clinique IA</div>
        <div style="font-size:0.9rem;color:#374151;">{rapport.replace(chr(10), '<br>')}</div>
    </div>""", unsafe_allow_html=True)
    disc = result.get("disclaimer","")
    if disc: st.caption(f"⚕️ *{disc}*")


def render_radio_full_analysis(result, type_radio, patient=None, context="praticien"):
    """Render complet du rapport radio — utilisé dans onglet praticien ET patient."""
    if "error" in result:
        st.error(f"⚠️ Erreur d'analyse : {result['error']}")
        return

    render_radio_score_header(result, type_radio)

    tab_labels = ["🦷 Dents","🦠 Caries","🩸 Os Alvéolaire","⚠️ Lésions Apicales",
                  "🧠 Sagesses","📋 Plan Traitement","📝 Rapport Narratif"]
    if context == "praticien" and patient:
        tab_labels.append("🧬 Corrélation Microbiome")

    tabs_radio = st.tabs(tab_labels)
    with tabs_radio[0]: render_radio_dents_visibles(result)
    with tabs_radio[1]: render_radio_caries(result)
    with tabs_radio[2]: render_radio_perte_osseuse(result)
    with tabs_radio[3]: render_radio_lesions_apicales(result)
    with tabs_radio[4]: render_radio_sagesses(result)
    with tabs_radio[5]: render_radio_plan_traitement(result)
    with tabs_radio[6]: render_radio_rapport_narratif(result)
    if context == "praticien" and patient and len(tabs_radio) > 7:
        with tabs_radio[7]: render_radio_correlation_microbiome(result, patient)

    # Anomalies autres
    autres = result.get("anomalies_autres", [])
    if autres and autres != [""]:
        st.markdown("---")
        st.markdown("#### 🔍 Autres Anomalies")
        for a in autres:
            if a: st.markdown(f"- {a}")


def render_radio_uploader(pid, patient=None, context="praticien"):
    """Interface d'upload et déclenchement d'analyse radio — réutilisable praticien et patient."""
    key_prefix = f"{context}_radio_{pid}"
    result_key = f"{key_prefix}_result"
    type_key   = f"{key_prefix}_type"

    st.markdown("""
    <div style="background:linear-gradient(135deg,#0a1628,#1e3a5f);border-radius:16px;padding:22px 28px;margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:2rem;">🩻</span>
            <div>
                <div style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:white;">Analyse Radiologique IA</div>
                <div style="font-size:0.82rem;color:rgba(255,255,255,0.6);">OPG Panoramique · Rétro-alvéolaires · Powered by Claude Vision</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Type de radio
    type_radio = st.radio(
        "Type de radiographie",
        options=["panoramique","retro_alveolaire"],
        format_func=lambda x: "🌐 Panoramique / OPG" if x == "panoramique" else "🦷 Rétro-alvéolaire",
        horizontal=True,
        key=f"{key_prefix}_type_sel"
    )

    # Upload
    col_up, col_info = st.columns([2, 1])
    with col_up:
        uploaded = st.file_uploader(
            "Importer la radiographie",
            type=["jpg","jpeg","png","webp","bmp"],
            key=f"{key_prefix}_upload",
            label_visibility="visible",
            help="Format JPEG, PNG ou WebP · Max 20 Mo"
        )
    with col_info:
        st.markdown(f"""
        <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:12px;padding:14px 16px;margin-top:4px;">
            <div style="font-size:0.72rem;color:#0369a1;font-weight:700;margin-bottom:8px;">CONSEILS IMPORT</div>
            <div style="font-size:0.78rem;color:#0c4a6e;line-height:1.5;">
                🔹 Export JPEG depuis votre logiciel radio<br>
                🔹 Résolution minimale : 800px<br>
                🔹 Contraste suffisant (pas de surexposition)<br>
                🔹 {"OPG : vue complète arcade recommandée" if type_radio=="panoramique" else "Rétro : 2-4 dents idéalement"}
            </div>
        </div>""", unsafe_allow_html=True)

    if uploaded:
        img_bytes = uploaded.read()
        mime = "image/png" if uploaded.name.lower().endswith(".png") else "image/jpeg"

        col_prev, col_act = st.columns([1, 1])
        with col_prev:
            st.image(img_bytes, caption=f"Radio importée — {uploaded.name}", use_container_width=True)
        with col_act:
            st.markdown(f"""
            <div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:16px;">
                <div style="font-size:0.72rem;color:#6b7280;font-weight:700;margin-bottom:8px;">FICHIER IMPORTÉ</div>
                <div style="font-size:0.85rem;color:#374151;">📄 {uploaded.name}</div>
                <div style="font-size:0.78rem;color:#9ca3af;margin-top:2px;">Taille : {len(img_bytes)/1024:.1f} Ko</div>
                <div style="font-size:0.78rem;color:#9ca3af;">Type : {mime}</div>
                <div style="font-size:0.78rem;color:#0369a1;margin-top:6px;">
                    {"🌐 Analyse OPG — Vue complète" if type_radio=='panoramique' else "🦷 Analyse Rétro-alvéolaire"}
                </div>
            </div>""", unsafe_allow_html=True)
            already = st.session_state.get(result_key)
            btn_label = "🔄 Relancer l'analyse" if already else "🤖 Lancer l'analyse IA"
            if st.button(btn_label, use_container_width=True, type="primary", key=f"{key_prefix}_run"):
                with st.spinner("🩻 Analyse radiologique en cours... (15-25 secondes)"):
                    st.session_state[result_key] = analyser_radio(img_bytes, mime, type_radio, patient)
                    st.session_state[type_key]   = type_radio
                st.rerun()

    # Démo
    elif st.button("🩻 Voir une démo d'analyse", key=f"{key_prefix}_demo", use_container_width=True):
        st.session_state[result_key] = _demo_radio_result(type_radio)
        st.session_state[type_key]   = type_radio
        st.rerun()

    st.markdown("---")

    # Résultats
    if st.session_state.get(result_key):
        result     = st.session_state[result_key]
        type_saved = st.session_state.get(type_key, type_radio)
        render_radio_full_analysis(result, type_saved, patient=patient, context=context)

        # Export PDF / données
        if context == "praticien":
            st.markdown("---")
            col_pdf, col_clear = st.columns(2)
            with col_pdf:
                if st.button("📥 Intégrer au rapport PDF patient", use_container_width=True, type="primary", key=f"{key_prefix}_pdf"):
                    if "radio_results" not in st.session_state: st.session_state.radio_results = {}
                    st.session_state.radio_results[pid] = {"result": result, "type": type_saved, "date": date.today().strftime("%d/%m/%Y")}
                    st.success("✅ Analyse radio enregistrée dans le dossier patient — disponible dans le PDF.")
            with col_clear:
                if st.button("🗑️ Effacer l'analyse", use_container_width=True, key=f"{key_prefix}_clear"):
                    del st.session_state[result_key]
                    st.rerun()


def _demo_radio_result(type_radio):
    """Résultat de démo réaliste selon le type de radio."""
    if type_radio == "panoramique":
        return {
            "type_radio":"panoramique","qualite_image":"bonne","confiance_analyse":"moderee",
            "dents_visibles":[
                {"num_fdi":11,"nom":"Incisive centrale sup droite","etat_general":"saine","present":True},
                {"num_fdi":12,"nom":"Incisive latérale sup droite","etat_general":"restaurée","present":True},
                {"num_fdi":16,"nom":"Première molaire sup droite","etat_general":"cariée","present":True},
                {"num_fdi":21,"nom":"Incisive centrale sup gauche","etat_general":"saine","present":True},
                {"num_fdi":26,"nom":"Première molaire sup gauche","etat_general":"restaurée","present":True},
                {"num_fdi":36,"nom":"Première molaire inf gauche","etat_general":"traitée","present":True},
                {"num_fdi":38,"nom":"Sagesse inf gauche","etat_general":"absente","present":False},
                {"num_fdi":46,"nom":"Première molaire inf droite","etat_general":"restaurée","present":True},
                {"num_fdi":48,"nom":"Sagesse inf droite","etat_general":"saine","present":True},
            ],
            "caries_detectees":[
                {"dent_fdi":16,"localisation":"interproximale","stade":"profonde","urgence":"urgent","detail":"Carie distale profonde approchant la pulpe — soin urgent recommandé"},
                {"dent_fdi":26,"localisation":"occlusale","stade":"modérée","urgence":"traitement_programme","detail":"Carie sous joint de couronne défaillant"},
                {"dent_fdi":45,"localisation":"cervicale","stade":"initiale","urgence":"surveillance","detail":"Lésion cervicale débutante — reminéralisation possible"},
            ],
            "perte_osseuse":{"present":True,"type":"horizontale","severite":"moderee","zones_atteintes":["Secteur postérieur droit","Secteur postérieur gauche"],"mesures_estimees":{"sextant_anterieur":"Niveau conservé","sextant_posterieur_droit":"Perte estimée 3-4mm","sextant_posterieur_gauche":"Perte estimée 3mm"},"detail":"Perte osseuse horizontale modérée diffuse dans les secteurs postérieurs, compatible avec une parodontite chronique de stade II."},
            "lesions_apicales":[
                {"dent_fdi":36,"type":"granulome","taille_mm":4,"urgence":"traitement_endodontique","detail":"Image péri-apicale arrondie — granulome probable, retraitement endodontique à envisager"},
            ],
            "sagesses":[
                {"dent_fdi":48,"statut":"angulation_mesiale","recommandation":"extraction_preventive","detail":"Dent de sagesse en angulation mésiale avec contact sur la 47 — extraction préventive recommandée à discuter"},
            ],
            "restaurations":[
                {"dent_fdi":26,"type":"couronne","qualite":"a_remplacer","detail":"Joint de couronne ouvert — infiltration cariogène visible"},
                {"dent_fdi":46,"type":"amalgame","qualite":"adequate","detail":"Amalgame occlusal stable"},
            ],
            "mesures_cles":{"hauteur_osseuse_ant_mm":"~14mm","hauteur_osseuse_post_d_mm":"~10mm","hauteur_osseuse_post_g_mm":"~11mm","longueur_racine_exemple":"16 FDI ≈ 16mm","note_mesures":"Estimations visuelles — mesures précises sur logiciel dédié"},
            "anomalies_autres":["Asymétrie légère du condyle droit — surveillance","Sinus maxillaire gauche légèrement opacifié — suivi ORL si symptômes"],
            "score_global_radio":52,"niveau_urgence_global":"elevee",
            "rapport_narratif":"L'examen panoramique révèle une denture de 28 dents avec une dent de sagesse inférieure gauche absente et la 38 incluse non visible. La situation carieuse présente trois lésions dont une urgente en 16 nécessitant une intervention immédiate.\n\nL'os alvéolaire montre une perte modérée dans les secteurs postérieurs, compatible avec une parodontite chronique de stade II. Cette atteinte parodontale est cohérente avec les données microbiomes montrant un taux élevé de P. gingivalis.\n\nUne image péri-apicale en 36 suggère un granulome nécessitant une réévaluation endodontique. La couronne en 26 présente un joint défaillant à reprendre à court terme.\n\nPlan de traitement suggéré : 1) Soin urgent 16, 2) Bilan parodontal approfondi + sondage, 3) Retraitement 36, 4) Remake couronne 26, 5) Discussion extraction 48.",
            "plan_traitement_suggere":[
                {"priorite":1,"acte":"Soin carie profonde","dents":[16],"delai_suggere":"immédiat","justification":"Carie profonde pulpaire imminente"},
                {"priorite":2,"acte":"Bilan parodontal + sondage complet","dents":[],"delai_suggere":"sous_2semaines","justification":"Perte osseuse modérée diffuse"},
                {"priorite":3,"acte":"Évaluation endodontique / retraitement","dents":[36],"delai_suggere":"1_mois","justification":"Lésion péri-apicale granulomateuse"},
                {"priorite":4,"acte":"Remake couronne","dents":[26],"delai_suggere":"3_mois","justification":"Joint défaillant avec infiltration"},
                {"priorite":5,"acte":"Extraction préventive sagesse","dents":[48],"delai_suggere":"6_mois","justification":"Angulation mésiale — contact 47"},
            ],
            "correlation_microbiome":{"p_gingivalis_coherent":True,"s_mutans_coherent":True,"commentaire":"La perte osseuse parodontale modérée est cohérente avec le taux élevé de P. gingivalis. Les 3 caries détectées corrèlent avec le S. mutans élevé du patient."},
            "disclaimer":"Résultat de démonstration — Analyse IA aide à la décision uniquement. Diagnostic définitif par le praticien sur cliché original.",
        }
    else:
        return {
            "type_radio":"retro_alveolaire","qualite_image":"bonne","confiance_analyse":"elevee",
            "dents_visibles":[
                {"num_fdi":14,"nom":"Première prémolaire sup droite","etat_general":"saine","present":True},
                {"num_fdi":15,"nom":"Deuxième prémolaire sup droite","etat_general":"restaurée","present":True},
                {"num_fdi":16,"nom":"Première molaire sup droite","etat_general":"cariée","present":True},
                {"num_fdi":17,"nom":"Deuxième molaire sup droite","etat_general":"restaurée","present":True},
            ],
            "caries_detectees":[
                {"dent_fdi":16,"localisation":"interproximale","stade":"profonde","urgence":"urgent","detail":"Carie mésiale profonde, distance pulpe < 1mm — traitement immédiat nécessaire"},
                {"dent_fdi":15,"localisation":"interproximale","stade":"initiale","urgence":"surveillance","detail":"Déminéralisation interproximale débutante disto-15"},
            ],
            "perte_osseuse":{"present":True,"type":"verticale","severite":"legere","zones_atteintes":["Distal 16","Mésial 17"],"mesures_estimees":{"sextant_anterieur":"N/A — hors champ","sextant_posterieur_droit":"Perte verticale estimée 2-3mm 16D","sextant_posterieur_gauche":"N/A — hors champ"},"detail":"Défect osseux vertical léger en distal 16, profondeur estimée 2-3mm — sondage clinique recommandé pour confirmer."},
            "lesions_apicales":[],"sagesses":[],
            "restaurations":[
                {"dent_fdi":17,"type":"composite","qualite":"adequate","detail":"Composite occlusal étanche"},
                {"dent_fdi":15,"type":"inlay","qualite":"a_remplacer","detail":"Inlay avec micro-infiltration visible en mésial"},
            ],
            "mesures_cles":{"hauteur_osseuse_ant_mm":None,"hauteur_osseuse_post_d_mm":"~12mm (16), ~13mm (17)","hauteur_osseuse_post_g_mm":None,"longueur_racine_exemple":"16 ≈ 15-16mm estimé","note_mesures":"Estimations visuelles — calibration nécessaire sur logiciel radio"},
            "anomalies_autres":[],"score_global_radio":60,"niveau_urgence_global":"elevee",
            "rapport_narratif":"Ce cliché rétro-alvéolaire du secteur postérieur droit supérieur (14-17) révèle une situation carieuse nécessitant une prise en charge rapide.\n\nLa lésion carieuse en 16 mésial est profonde, approchant dangereusement la pulpe — une endodontie peut être nécessaire si l'exposition pulpaire est confirmée à l'ouverture. Un soin en urgence est recommandé.\n\nUn début de déminéralisation interproximale est visible en 15 distal — une application de vernis fluoré et une surveillance à 6 mois sont suggérées.\n\nL'inlay en 15 mésial présente une micro-infiltration à repolir ou à remplacer à court terme pour éviter une évolution carieuse.",
            "plan_traitement_suggere":[
                {"priorite":1,"acte":"Soin carie profonde ± endodontie","dents":[16],"delai_suggere":"immédiat","justification":"Carie approchant la pulpe — risque d'exposition"},
                {"priorite":2,"acte":"Application vernis fluoré + surveillance","dents":[15],"delai_suggere":"1_mois","justification":"Lésion initiale — reminéralisation possible"},
                {"priorite":3,"acte":"Remplacement inlay","dents":[15],"delai_suggere":"3_mois","justification":"Micro-infiltration sous inlay existant"},
            ],
            "correlation_microbiome":{"p_gingivalis_coherent":True,"s_mutans_coherent":True,"commentaire":"La carie profonde en 16 est cohérente avec un taux de S. mutans élevé. Le défect osseux vertical léger corrèle avec la présence de P. gingivalis."},
            "disclaimer":"Résultat de démonstration — Analyse IA aide à la décision uniquement. Diagnostic définitif par le praticien sur cliché original.",
        }

# ── ANALYSE PHOTO ─────────────────────────────────────────────────────────────
def analyser_photo_bouche(image_bytes, mime_type="image/jpeg"):
    if not ANTHROPIC_API_KEY: return {"error":"Clé API Anthropic manquante."}
    b64 = base64.standard_b64encode(image_bytes).decode()
    sp = ('Tu es un assistant d\'aide à la décision dentaire. Réponds UNIQUEMENT en JSON valide sans markdown. '
          'Structure: {"qualite_image":"bonne|moyenne|insuffisante","zones_analysees":[],"findings":[{"zone":"","observation":"","severite":"normal|attention|alerte","detail":""}],'
          '"score_global":0,"profil_visuel":"Bouche saine|Inflammation légère|Inflammation modérée|Dysbiose visible|Urgence clinique",'
          '"recommandations_immediates":[],"disclaimer":"Aide à la décision.","confiance":"élevée|modérée|faible"}')
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":1500,"system":sp,
                  "messages":[{"role":"user","content":[{"type":"image","source":{"type":"base64","media_type":mime_type,"data":b64}},{"type":"text","text":"Analyse cette photo en JSON."}]}]},
            timeout=30)
        r.raise_for_status()
        raw = r.json()["content"][0]["text"].strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e: return {"error": str(e)}

def render_photo_analysis(result):
    if "error" in result: st.error(f"⚠️ {result['error']}"); return
    score = result.get("score_global",50); profil = result.get("profil_visuel","N/A")
    c = "#16a34a" if score >= 70 else "#d97706" if score >= 45 else "#e11d48"
    cs, ci = st.columns([1, 3])
    with cs:
        st.markdown(f'<div style="text-align:center;background:linear-gradient(135deg,{c}22,{c}11);border:2px solid {c};border-radius:16px;padding:24px;"><div style="font-family:\'DM Serif Display\',serif;font-size:3rem;color:{c};line-height:1;">{score}</div><div style="font-size:0.75rem;color:#6b7280;margin-top:4px;">Score santé visuelle</div><div style="font-size:0.8rem;font-weight:600;color:{c};margin-top:8px;">{profil}</div></div>', unsafe_allow_html=True)
    with ci:
        st.markdown(f"**Qualité :** `{result.get('qualite_image','N/A')}` · **Confiance :** `{result.get('confiance','N/A')}`")
        zones = result.get("zones_analysees",[])
        if zones: st.markdown(f"**Zones :** {' · '.join(zones)}")
        for f in result.get("findings",[]):
            sev = f.get("severite","normal")
            css = "finding-alert" if sev=="alerte" else "finding-warn" if sev=="attention" else "finding-ok"
            icon = "🔴" if sev=="alerte" else "🟡" if sev=="attention" else "🟢"
            st.markdown(f"<span class='finding-badge {css}'>{icon} {f.get('zone','')} — {f.get('observation','')}</span>", unsafe_allow_html=True)
    recos = result.get("recommandations_immediates",[])
    if recos: st.markdown("---"); st.markdown("#### ✅ Actions immédiates")
    for r in recos: st.markdown(f"- {r}")
    if result.get("disclaimer"): st.caption(f"⚕️ *{result['disclaimer']}*")

# ── RECOMMANDATIONS ───────────────────────────────────────────────────────────
def generer_recommandations(sm, pg, div):
    plan = {"priorites":[],"aliments_favoriser":[],"aliments_eviter":[],"probiotiques":[],
            "suivi_semaines":24,"profil_label":"","profil_description":""}
    nb = sum([sm > 3.0, pg > 0.5, div < 50])
    if nb == 0:   plan["profil_label"]="🟢 Microbiome Équilibré"; plan["profil_description"]="Votre flore buccale est protectrice."; plan["suivi_semaines"]=24
    elif nb == 1: plan["profil_label"]="🟡 Déséquilibre Modéré";  plan["profil_description"]="Un déséquilibre détecté. Corrections en 2-3 mois."; plan["suivi_semaines"]=12
    else:         plan["profil_label"]="🔴 Dysbiose Active";       plan["profil_description"]="Plusieurs marqueurs en alerte. Plan renforcé nécessaire."; plan["suivi_semaines"]=8
    if sm > 3.0:
        plan["priorites"].append({"icone":"🦠","titre":"Réduire S. mutans","urgence":"Elevee" if sm>6.0 else "Moderee","explication":f"S. mutans : {sm}% (normal < 3%)","actions":["Brossage 2 min après repas sucrés","Fil dentaire quotidien le soir","Bain de bouche fluoré 1x/jour","Éviter le grignotage"]})
        plan["aliments_eviter"]  += ["Bonbons","Sodas","Pain blanc","Jus de fruits"]
        plan["aliments_favoriser"] += ["Fromage à pâte dure","Yaourt nature","Légumes crus","Thé vert","Noix"]
        plan["probiotiques"].append({"nom":"Lactobacillus reuteri DSM 17938","forme":"Comprimés 1x/jour après brossage","duree":"3 mois","benefice":"Inhibe S. mutans","marques":"BioGaia Prodentis"})
    if pg > 0.5:
        plan["priorites"].append({"icone":"🩸","titre":"Éliminer P. gingivalis","urgence":"Elevee" if pg>1.5 else "Moderee","explication":f"P. gingivalis : {pg}% (normal < 0.5%)","actions":["Nettoyage interdentaire quotidien — PRIORITÉ N°1","Brossage langue matin et soir","Consultation parodontale","Arrêt du tabac"]})
        plan["aliments_eviter"]  += ["Tabac","Alcool en excès","Sucres raffinés","Ultra-transformés"]
        plan["aliments_favoriser"] += ["Poissons gras 2-3×/semaine","Myrtilles (polyphénols)","Légumes verts feuillus","Huile d'olive","Ail et oignon"]
        plan["probiotiques"].append({"nom":"L. reuteri + L. salivarius","forme":"Pastilles 2x/jour","duree":"3-6 mois","benefice":"Réduit P. gingivalis","marques":"GUM PerioBalance, Blis K12"})
    if div < 50:
        plan["priorites"].append({"icone":"🌱","titre":"Restaurer la diversité","urgence":"Moderee" if div>30 else "Elevee","explication":f"Diversité : {div}/100 (optimal > 65)","actions":["30 plantes différentes/semaine","Réduire antiseptiques quotidiens","Fibres prébiotiques","1.5L eau/jour"]})
        plan["aliments_favoriser"] += ["Légumes racines","Pomme avec la peau","Légumineuses","Choucroute","Kombucha"]
        plan["aliments_eviter"]   += ["Bains de bouche antiseptiques quotidiens","Antibiotiques inutiles"]
        plan["probiotiques"].append({"nom":"Streptococcus salivarius K12 + M18","forme":"Pastilles le soir","duree":"2-3 mois","benefice":"Recolonise la flore","marques":"BLIS K12"})
    if nb == 0:
        plan["priorites"].append({"icone":"✅","titre":"Maintenir l'équilibre","urgence":"Routine","explication":"Microbiome oral en bonne santé.","actions":["Brossage 2×/jour","Fil dentaire","Alimentation variée","Contrôle dans 6 mois"]})
        plan["aliments_favoriser"] += ["Alimentation méditerranéenne","Eau","Yaourt, kéfir"]
    plan["aliments_favoriser"] = list(dict.fromkeys(plan["aliments_favoriser"]))
    plan["aliments_eviter"]    = list(dict.fromkeys(plan["aliments_eviter"]))
    return plan

# ── PDF ───────────────────────────────────────────────────────────────────────
def generer_pdf(pnom, rc, rp, div, hist_df, plan, scores=None):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
        BLUE = colors.HexColor('#1a3a5c'); LB = colors.HexColor('#dbeafe'); GBG = colors.HexColor('#f9fafb')
        ts  = ParagraphStyle('T', fontSize=18, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=4)
        ss  = ParagraphStyle('S', fontSize=10, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica', spaceAfter=6)
        h1  = ParagraphStyle('H1', fontSize=13, textColor=BLUE, fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=4)
        h2  = ParagraphStyle('H2', fontSize=11, textColor=BLUE, fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=3)
        bs  = ParagraphStyle('B', fontSize=10, fontName='Helvetica', spaceAfter=3, leading=14)
        its = ParagraphStyle('I', fontSize=9, fontName='Helvetica-Oblique', textColor=colors.HexColor('#555'), spaceAfter=4)
        sml = ParagraphStyle('Sm', fontSize=8, fontName='Helvetica', textColor=colors.grey, alignment=TA_CENTER)
        elems = []
        ht = Table([[Paragraph("OralBiome - Rapport Patient Complet",ts)],[Paragraph("Microbiome Oral Predictif | Rapport Personnalise",ss)]], colWidths=[180*mm])
        ht.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),BLUE),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        elems += [ht, Spacer(1,5*mm)]
        it = Table([[Paragraph(f"<b>Patient :</b> {pnom}",bs),Paragraph(f"<b>Date :</b> {date.today().strftime('%d/%m/%Y')}",bs)]], colWidths=[90*mm,90*mm])
        it.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LB),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),8)]))
        elems += [it, Spacer(1,6*mm)]
        elems += [Paragraph("Resultats Microbiome",h1), HRFlowable(width="100%",thickness=1,color=LB)]
        rt = Table([[Paragraph("<b>Risque Carieux</b>",bs),Paragraph(f"<b>{rc}</b>",bs)],[Paragraph("<b>Risque Parodontal</b>",bs),Paragraph(f"<b>{rp}</b>",bs)],[Paragraph("<b>Score Diversite</b>",bs),Paragraph(f"<b>{div}/100</b> (optimal > 65)",bs)]], colWidths=[90*mm,90*mm])
        rt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),GBG),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),8)]))
        elems += [rt, Spacer(1,6*mm)]
        if scores:
            elems += [Paragraph("Scores Risque Systemique",h1), HRFlowable(width="100%",thickness=1,color=LB), Paragraph("Scores bases sur correlations litterature scientifique.",its), Spacer(1,3*mm)]
            sr = [["Pathologie","Score","Niveau","Action"]]
            for key, data in scores.items():
                ll = "Eleve" if data["level"]=="high" else "Modere" if data["level"]=="med" else "Faible"
                action = data["actions"][0] if data["actions"] else "-"
                sr.append([Paragraph(f"{data['icon']} {data['label']}",bs), Paragraph(f"<b>{data['score']}</b>",bs), Paragraph(ll,bs), Paragraph(action[:80]+"..." if len(action)>80 else action,bs)])
            syt = Table(sr, colWidths=[55*mm,22*mm,22*mm,81*mm])
            syt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('ROWBACKGROUNDS',(0,1),(-1,-1),[GBG,colors.white]),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),6),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#e5e7eb'))]))
            elems += [syt, Spacer(1,6*mm)]
        if plan["priorites"]:
            elems += [Paragraph("Plan d'Action",h1), HRFlowable(width="100%",thickness=1,color=LB)]
            for i, p in enumerate(plan["priorites"]):
                b = "URGENT" if p["urgence"]=="Elevee" else "MODERE" if p["urgence"]=="Moderee" else "ROUTINE"
                elems.append(Paragraph(f"Priorite {i+1} — {p['titre']} [{b}]",h2))
                for action in p["actions"]: elems.append(Paragraph(f"• {action}",bs))
                elems.append(Spacer(1,3*mm))
        elems += [Paragraph("Plan Nutritionnel",h1), HRFlowable(width="100%",thickness=1,color=LB)]
        if plan["aliments_favoriser"] or plan["aliments_eviter"]:
            mi = max(len(plan["aliments_favoriser"]), len(plan["aliments_eviter"]))
            nr = [[Paragraph(f"+ {plan['aliments_favoriser'][i] if i<len(plan['aliments_favoriser']) else ''}",bs),
                   Paragraph(f"- {plan['aliments_eviter'][i]   if i<len(plan['aliments_eviter'])    else ''}",bs)] for i in range(mi)]
            nut = Table(nr, colWidths=[90*mm,90*mm])
            nut.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),colors.HexColor('#f0fdf4')),('BACKGROUND',(1,0),(1,-1),colors.HexColor('#fff1f2')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),8)]))
            elems.append(nut)
        elems.append(Spacer(1,8*mm))
        ft = Table([[Paragraph("Ce rapport est fourni a titre preventif. Ne constitue pas un diagnostic medical.",sml)],[Paragraph("OralBiome | contact@oralbiome.com",sml)]], colWidths=[180*mm])
        ft.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LB),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        elems.append(ft)
        doc.build(elems)
        return buf.getvalue()
    except ImportError: return b"Installez reportlab : pip install reportlab"

# ── ALERTES & DASHBOARD ───────────────────────────────────────────────────────
def calculer_alertes(patients):
    alertes = []; today = date.today()
    for nom, p in patients.items():
        sm=p["s_mutans"]; pg=p["p_gingivalis"]; div=p["diversite"]; hist=p["historique"]
        if pg > 1.5:
            alertes.append({"type":"urgence","patient":nom,"id":p["id"],"titre":f"P. gingivalis critique ({pg}%)","desc":"Risque parodontal sévère.","priorite":1,"icone":"🚨","action":"Consultation parodontale urgente"})
        elif sm > 6.0:
            alertes.append({"type":"urgence","patient":nom,"id":p["id"],"titre":f"S. mutans critique ({sm}%)","desc":"Caries actives probables.","priorite":1,"icone":"🚨","action":"Bilan carie urgent"})
        if not hist.empty:
            try:
                ld  = datetime.strptime(hist.iloc[-1]["Date"],"%d/%m/%Y").date()
                ea  = sm>3.0 or pg>0.5 or div<50
                dl  = 8 if ea and (pg>1.5 or sm>6.0) else 12 if ea else 24
                dp  = ld + timedelta(days=dl*7); jr = (dp-today).days
                if jr < 0:
                    alertes.append({"type":"urgence","patient":nom,"id":p["id"],"titre":f"Contrôle en retard de {abs(jr)} jours","desc":f"Dernier examen : {hist.iloc[-1]['Date']}.","priorite":2,"icone":"⏰","action":"Planifier rendez-vous"})
                elif jr <= 14:
                    alertes.append({"type":"warn","patient":nom,"id":p["id"],"titre":f"Contrôle dans {jr} jours","desc":f"Prochain : {dp.strftime('%d/%m/%Y')}.","priorite":3,"icone":"📅","action":"Envoyer rappel"})
            except: pass
        if len(hist) >= 2:
            try:
                dp2 = float(hist.iloc[-1]["P. gingiv. (%)"]) - float(hist.iloc[-2]["P. gingiv. (%)"])
                dm2 = float(hist.iloc[-1]["S. mutans (%)"])  - float(hist.iloc[-2]["S. mutans (%)"])
                if dp2 > 0.3: alertes.append({"type":"warn","patient":nom,"id":p["id"],"titre":f"Dégradation paro (+{dp2:.1f}%)","desc":"Augmentation P. gingivalis.","priorite":2,"icone":"📈","action":"Adapter protocole"})
                if dm2 > 1.0: alertes.append({"type":"warn","patient":nom,"id":p["id"],"titre":f"Dégradation cariogène (+{dm2:.1f}%)","desc":"Augmentation S. mutans.","priorite":3,"icone":"📈","action":"Revoir plan nutritionnel"})
            except: pass
        jsr = jours_sans_reponse(p["id"])
        if jsr >= 3:
            alertes.append({"type":"warn","patient":nom,"id":p["id"],"titre":f"Décrochage protocole ({jsr}j sans questionnaire)","desc":"Le patient n'a pas rempli son suivi.","priorite":2,"icone":"📉","action":"Envoyer rappel SMS"})
        if hist.empty:
            alertes.append({"type":"info","patient":nom,"id":p["id"],"titre":"Aucune analyse","desc":"Pas encore d'analyse microbiome.","priorite":4,"icone":"📋","action":"Planifier examen initial"})
    return sorted(alertes, key=lambda x: x["priorite"])

def calculer_stats_cabinet(patients):
    total = len(patients)
    if total == 0: return {}
    ac  = sum(1 for p in patients.values() if p["s_mutans"]>3.0 or p["p_gingivalis"]>0.5 or p["diversite"]<50)
    am  = sum(p["s_mutans"]    for p in patients.values()) / total
    ap  = sum(p["p_gingivalis"] for p in patients.values()) / total
    ad  = sum(p["diversite"]   for p in patients.values()) / total
    rc2 = sum(1 for p in patients.values() if calculer_score_systemique(p["s_mutans"],p["p_gingivalis"],p["diversite"])["cardiovasculaire"]["level"]=="high")
    ra2 = sum(1 for p in patients.values() if calculer_score_systemique(p["s_mutans"],p["p_gingivalis"],p["diversite"])["alzheimer"]["level"]=="high")
    obs = sum(1 for p in patients.values() if jours_sans_reponse(p["id"]) >= 3)
    tv  = sum(len(p["historique"]) for p in patients.values())
    return {"total":total,"alertes":ac,"stables":total-ac,"pct_alerte":round(ac/total*100),
            "avg_mutans":round(am,2),"avg_paro":round(ap,2),"avg_diversite":round(ad,1),
            "risque_cardio_eleve":rc2,"risque_alz_eleve":ra2,"decrochages":obs,"total_visites":tv}

def render_dashboard(patients):
    stats   = calculer_stats_cabinet(patients)
    alertes = calculer_alertes(patients)
    lh = logo_img(140, "margin-bottom:8px;filter:brightness(0) invert(1);opacity:0.85;")
    st.markdown(f'<div class="ob-header">{lh}<h1>📊 {t("dash_title")}</h1><p>Vue analytique en temps réel · Alertes · KPIs · Observance · IoT</p></div>', unsafe_allow_html=True)
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    def kpi(n,v,l,d,c): n.markdown(f'<div class="kpi-card"><div class="kpi-num {c}">{v}</div><div class="kpi-lbl">{l}</div><div class="kpi-delta {c}">{d}</div></div>', unsafe_allow_html=True)
    kpi(k1,stats["total"],    t("dash_total"),            f"📂 {stats['total_visites']} visites",   "kpi-blue")
    kpi(k2,stats["alertes"],  t("dash_alerts"),           f"⚠️ {stats['pct_alerte']}%",             "kpi-red")
    kpi(k3,stats["stables"],  t("dash_stable"),           f"✅ {100-stats['pct_alerte']}%",          "kpi-green")
    kpi(k4,stats["risque_cardio_eleve"], t("dash_cardio"),  "❤️ Suivi requis",                    "kpi-amber")
    kpi(k5,stats["risque_alz_eleve"],  t("dash_neuro"),     "🧠 P. gingivalis crit.",             "kpi-amber")
    kpi(k6,stats["decrochages"],       "Décrochages",        "📉 Sans questionnaire 3j+",          "kpi-red")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🧬 Moyennes Microbiome du Cabinet")
    cm1, cm2, cm3 = st.columns(3)
    def bar(v,mx,c): pct2 = min(100,v/mx*100); return f'<div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:{pct2:.0f}%;background:{c};"></div></div>'
    with cm1:
        c = "#e11d48" if stats["avg_mutans"] > 3 else "#16a34a"
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.8rem;color:#6b7280;font-weight:600;">S. MUTANS MOYEN</div><div class="kpi-num" style="color:{c};">{stats["avg_mutans"]}%</div><div style="font-size:0.75rem;color:#9ca3af;">Normal &lt; 3%</div>{bar(stats["avg_mutans"],8,c)}</div>', unsafe_allow_html=True)
    with cm2:
        c = "#e11d48" if stats["avg_paro"] > 0.5 else "#16a34a"
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.8rem;color:#6b7280;font-weight:600;">P. GINGIVALIS MOYEN</div><div class="kpi-num" style="color:{c};">{stats["avg_paro"]}%</div><div style="font-size:0.75rem;color:#9ca3af;">Normal &lt; 0.5%</div>{bar(stats["avg_paro"],2,c)}</div>', unsafe_allow_html=True)
    with cm3:
        c = "#16a34a" if stats["avg_diversite"] >= 65 else "#d97706" if stats["avg_diversite"] >= 50 else "#e11d48"
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.8rem;color:#6b7280;font-weight:600;">DIVERSITÉ MOYENNE</div><div class="kpi-num" style="color:{c};">{stats["avg_diversite"]}/100</div><div style="font-size:0.75rem;color:#9ca3af;">Optimal &gt; 65</div>{bar(stats["avg_diversite"],100,c)}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    ca2, cp2 = st.columns([1, 2])
    with ca2:
        st.markdown(f"#### 🔔 Alertes Actives `{len(alertes)}`")
        if not alertes: st.success("✅ Aucune alerte active.")
        else:
            for a in alertes[:8]:
                css = "alert-card" if a["type"]=="urgence" else "alert-card warn" if a["type"]=="warn" else "alert-card info"
                st.markdown(f'<div class="{css}"><div class="alert-icon">{a["icone"]}</div><div class="alert-body"><div class="alert-title">{a["patient"]} — {a["titre"]}</div><div class="alert-desc">{a["desc"]}</div><div class="alert-meta">👉 {a["action"]}</div></div></div>', unsafe_allow_html=True)
    with cp2:
        st.markdown("#### 👥 État du Cabinet")
        rows = []
        for nom, p in patients.items():
            ea  = p["s_mutans"]>3.0 or p["p_gingivalis"]>0.5 or p["diversite"]<50
            sys_s = calculer_score_systemique(p["s_mutans"],p["p_gingivalis"],p["diversite"])
            top   = max(sys_s.items(), key=lambda x: x[1]["score"])
            obs_s = calculer_score_observance(p["id"])
            jsr   = jours_sans_reponse(p["id"])
            nba   = sum(1 for a in alertes if a["patient"]==nom)
            rows.append({"Nom":nom,"Statut":"🔴 Alerte" if ea else "🟢 Stable",
                         "S. mutans":f"{p['s_mutans']}%","P. gingivalis":f"{p['p_gingivalis']}%","Diversité":f"{p['diversite']}/100",
                         "Top Risque":f"{top[1]['icon']} {top[1]['score']}/100",
                         "Observance":f"{obs_s}/100","Alertes":nba if nba else "—"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.markdown("#### 📈 Tendance Diversité")
        chart_data = {}
        for nom, p in patients.items():
            hist = p["historique"]
            if len(hist) >= 2:
                dc = next((c for c in ["Diversite (%)","Diversité (%)"] if c in hist.columns), None)
                if dc: chart_data[nom] = hist[dc].astype(float).tolist()
        if chart_data:
            ml = max(len(v) for v in chart_data.values())
            st.line_chart(pd.DataFrame({k: v+[None]*(ml-len(v)) for k,v in chart_data.items()}))
        else: st.caption("Pas assez d'historique.")
    st.markdown("---")
    st.markdown(f"#### 🗂️ Toutes les Alertes ({len(alertes)})")
    if alertes:
        ft = st.selectbox("Filtrer",["Toutes","🚨 Urgences","⚠️ Avertissements","ℹ️ Infos"], label_visibility="collapsed")
        fm = {"Toutes":None,"🚨 Urgences":"urgence","⚠️ Avertissements":"warn","ℹ️ Infos":"info"}
        for a in [x for x in alertes if fm[ft] is None or x["type"]==fm[ft]]:
            css = "alert-card" if a["type"]=="urgence" else "alert-card warn" if a["type"]=="warn" else "alert-card info"
            ca3, cb3 = st.columns([5,1])
            with ca3: st.markdown(f'<div class="{css}"><div class="alert-icon">{a["icone"]}</div><div class="alert-body"><div class="alert-title">{a["id"]} · {a["patient"]} — {a["titre"]}</div><div class="alert-desc">{a["desc"]}</div><div class="alert-meta">👉 {a["action"]}</div></div></div>', unsafe_allow_html=True)
            with cb3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Ouvrir →", key=f"ab_{a['patient']}_{a['titre'][:8]}"):
                    st.session_state.patient_sel = a["patient"]; st.session_state.vue = "dossier"; st.rerun()
    else: st.success("✅ Aucune alerte active.")

# ── RGPD ──────────────────────────────────────────────────────────────────────
def render_rgpd_banner():
    _, col_m, _ = st.columns([1,3,1])
    with col_m:
        st.markdown("""<div style="background:white;border:2px solid #1a3a5c;border-radius:16px;padding:28px 32px;margin:40px auto;box-shadow:0 8px 32px rgba(0,0,0,0.12);">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;"><span style="font-size:2rem;">🔒</span>
        <div><div style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:#1a3a5c;font-weight:600;">Protection de vos données — RGPD</div>
        <div style="font-size:0.8rem;color:#6b7280;margin-top:2px;">Conformité UE 2016/679</div></div></div></div>""", unsafe_allow_html=True)
        with st.expander("📄 Politique de confidentialité", expanded=False):
            st.markdown("**1. Responsable** — OralBiome SAS · contact@oralbiome.com\n\n**2. Données** — Identification, santé bucco-dentaire, biomarqueurs, anamnèse.\n\n**3. Base légale** — Consentement explicite (Art. 9 RGPD).\n\n**4. Conservation** — Durée de la relation + archivage légal 10 ans.\n\n**5. Droits** — Accès, rectification, effacement → contact@oralbiome.com\n\n**6. CNIL** — www.cnil.fr")
        st.markdown("""<div style="background:#fefce8;border:1px solid #fde047;border-radius:10px;padding:14px 18px;margin:12px 0;">
        <div style="font-size:0.85rem;color:#713f12;">⚠️ <b>Données de santé :</b> Traitement réservé aux professionnels de santé habilités.</div></div>""", unsafe_allow_html=True)
        agree1 = st.checkbox("✅ J'accepte que mes données de santé soient traitées par OralBiome conformément à la politique ci-dessus.", key="rgpd_check1")
        agree2 = st.checkbox("✅ Je confirme être un professionnel de santé habilité ou le patient concerné.", key="rgpd_check2")
        st.checkbox("📧 J'accepte de recevoir des communications OralBiome. *(optionnel)*", key="rgpd_check3")
        st.markdown("<br>", unsafe_allow_html=True)
        cr, ca = st.columns(2)
        with cr:
            if st.button("Refuser et quitter", use_container_width=True):
                st.session_state.mode = "choix"; st.rerun()
        with ca:
            if st.button("Accepter et continuer →", use_container_width=True, type="primary", disabled=not(agree1 and agree2)):
                st.session_state.rgpd_accepted = True; st.rerun()
        if not(agree1 and agree2): st.caption("⚠️ Les deux premières cases sont obligatoires.")

# ── ONBOARDING ────────────────────────────────────────────────────────────────
def render_onboarding():
    step = st.session_state.onboarding_step
    lh   = logo_img(160, "margin:0 auto 16px auto;")
    st.markdown(f"""<div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:20px;padding:32px 40px;margin-bottom:32px;text-align:center;color:white;">
        {lh}<h2 style="font-family:'DM Serif Display',serif;font-size:2rem;margin:0;">Bienvenue sur OralBiome</h2>
        <p style="opacity:0.7;margin:8px 0 0 0;">Configuration · 3 étapes · moins de 2 minutes</p></div>""", unsafe_allow_html=True)
    def sc(n):
        if n < step:   css = "background:#16a34a;border:2px solid #16a34a;color:white;"; txt = "✓"
        elif n == step: css = "background:#2563eb;border:2px solid #2563eb;color:white;"; txt = str(n)
        else:           css = "background:white;border:2px solid #d1d5db;color:#9ca3af;"; txt = str(n)
        return f'<div style="width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.9rem;{css}">{txt}</div>'
    def sl(txt, n): c = "#16a34a" if n<step else "#2563eb" if n==step else "#9ca3af"; return f'<div style="font-size:0.78rem;font-weight:600;color:{c};margin-top:6px;">{txt}</div>'
    def sline(n): c = "#16a34a" if n<step else "#e5e7eb"; return f'<div style="width:80px;height:2px;background:{c};margin:18px 4px 0 4px;"></div>'
    st.markdown(f'<div style="display:flex;justify-content:center;align-items:flex-start;margin:0 0 36px 0;"><div style="text-align:center;">{sc(1)}{sl("Bienvenue",1)}</div>{sline(1)}<div style="text-align:center;">{sc(2)}{sl("Votre cabinet",2)}</div>{sline(2)}<div style="text-align:center;">{sc(3)}{sl("Premier patient",3)}</div></div>', unsafe_allow_html=True)
    _, col_c, _ = st.columns([1,2,1])
    if step == 1:
        with col_c:
            st.markdown("""<div style="background:white;border-radius:20px;padding:40px 44px;border:1px solid #e5e7eb;box-shadow:0 4px 24px rgba(0,0,0,0.06);text-align:center;">
                <div style="font-size:2.4rem;margin-bottom:12px;">🦷</div>
                <h3 style="font-family:'DM Serif Display',serif;color:#1a3a5c;margin:0 0 8px 0;">La plateforme d'intelligence orale prédictive</h3>
                <p style="color:#6b7280;font-size:0.9rem;margin-bottom:24px;">Corrèlez le microbiote oral avec les risques systémiques.<br>Rapports cliniques en 1 clic. Twin numérique dentaire.<br>Score d'observance. Interactions médicamenteuses. IoT.</p>
                <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:16px;"><div style="font-weight:600;color:#15803d;margin-bottom:4px;">✅ Votre compte est activé</div>
                <div style="font-size:0.85rem;color:#166534;">Accès complet · Données sécurisées · Conforme RGPD</div></div></div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Commencer →", use_container_width=True, type="primary"):
                st.session_state.onboarding_step = 2; st.rerun()
    elif step == 2:
        with col_c:
            st.markdown("### 🏥 Configurez votre cabinet")
            with st.form("form_cabinet"):
                c1, c2 = st.columns(2)
                with c1:
                    cabinet_nom       = st.text_input("Nom du cabinet *", value=st.session_state.get("cabinet_nom",""), placeholder="Cabinet Dentaire Dupont")
                    cabinet_praticien = st.text_input("Praticien *", value=st.session_state.get("cabinet_praticien",""), placeholder="Dr. Marie Dupont")
                    cabinet_specialite = st.selectbox("Spécialité", ["Omnipraticien","Parodontiste","Orthodontiste","Implantologiste","Pédodontiste","Autre"])
                with c2:
                    cabinet_adresse = st.text_input("Adresse", value=st.session_state.get("cabinet_adresse",""), placeholder="12 rue de la Santé")
                    cabinet_tel     = st.text_input("Téléphone", value=st.session_state.get("cabinet_tel",""), placeholder="+33 1 23 45 67 89")
                    cabinet_email   = st.text_input("Email cabinet", value=st.session_state.get("cabinet_email",""), placeholder="contact@cabinet.fr")
                sub2 = st.form_submit_button("Enregistrer et continuer →", use_container_width=True, type="primary")
                if sub2:
                    if not cabinet_nom.strip() or not cabinet_praticien.strip(): st.error("Nom du cabinet et praticien obligatoires.")
                    else:
                        for k,v in [("cabinet_nom",cabinet_nom),("cabinet_praticien",cabinet_praticien),("cabinet_adresse",cabinet_adresse),("cabinet_tel",cabinet_tel),("cabinet_email",cabinet_email),("cabinet_specialite",cabinet_specialite)]:
                            st.session_state[k] = v
                        st.session_state.onboarding_step = 3; st.rerun()
            if st.button("← Retour", key="back2"): st.session_state.onboarding_step = 1; st.rerun()
    elif step == 3:
        with col_c:
            st.markdown("### 👤 Ajoutez votre premier patient")
            st.caption("Optionnel — vous pourrez en ajouter d'autres depuis le tableau de bord.")
            with st.form("form_premier_patient"):
                fc1, fc2 = st.columns(2)
                with fc1: p_nom=st.text_input("Nom complet",placeholder="Jean Dupont"); p_age=st.number_input("Âge",1,120,40); p_email=st.text_input("Email",placeholder="jean@email.com")
                with fc2: p_tel=st.text_input("Téléphone",placeholder="+32 472 000 000"); p_sm=st.number_input("S. mutans (%)",0.0,10.0,2.0,step=0.1); p_pg=st.number_input("P. gingivalis (%)",0.0,5.0,0.2,step=0.1)
                p_div = st.slider("Score Diversité Microbienne", 0, 100, 70)
                csk, csv = st.columns(2)
                with csk: passer = st.form_submit_button("Passer cette étape →", use_container_width=True)
                with csv: sauver = st.form_submit_button("Créer le dossier et terminer ✓", use_container_width=True, type="primary")
                if passer: st.session_state.onboarding_done=True; st.session_state.connecte=True; st.session_state.mode="praticien"; st.rerun()
                if sauver:
                    if p_nom.strip():
                        nid  = f"P{str(len(st.session_state.patients)+1).zfill(3)}"
                        stat = "Alerte" if p_sm>3.0 or p_pg>0.5 or p_div<50 else "Stable"
                        df_n = pd.DataFrame({"Date":[date.today().strftime("%d/%m/%Y")],"Acte / Test":["Examen Initial"],"S. mutans (%)":[p_sm],"P. gingiv. (%)":[p_pg],"Diversite (%)":[p_div],"Status":[stat]})
                        st.session_state.patients[p_nom] = {"id":nid,"nom":p_nom,"age":p_age,"email":p_email,"telephone":p_tel,"date_naissance":"","historique":df_n,"s_mutans":p_sm,"p_gingivalis":p_pg,"diversite":p_div,"code_patient":f"OB-{nid}"}
                        st.session_state.patient_sel = p_nom
                    st.session_state.onboarding_done=True; st.session_state.connecte=True; st.session_state.mode="praticien"; st.success("✅ Bienvenue !"); st.rerun()
            if st.button("← Retour", key="back3"): st.session_state.onboarding_step = 2; st.rerun()

# ── DONNÉES INITIALES ─────────────────────────────────────────────────────────
def donnees_initiales():
    patients = {}
    df1 = pd.DataFrame({"Date":["12/10/2023","08/04/2026"],"Acte / Test":["Examen Initial","Controle"],"S. mutans (%)":[4.2,4.2],"P. gingiv. (%)":[0.8,0.3],"Diversite (%)":[45,75],"Status":["Alerte","Alerte"]})
    patients["Jean Dupont"] = {"id":"P001","nom":"Jean Dupont","age":42,"email":"jean.dupont@email.com","telephone":"+32 472 123 456","date_naissance":"15/03/1982","historique":df1,"s_mutans":4.2,"p_gingivalis":0.3,"diversite":75,"code_patient":"OB-P001"}
    df2 = pd.DataFrame({"Date":["05/01/2024"],"Acte / Test":["Examen Initial"],"S. mutans (%)":[1.2],"P. gingiv. (%)":[0.1],"Diversite (%)":[82],"Status":["Stable"]})
    patients["Marie Martin"] = {"id":"P002","nom":"Marie Martin","age":35,"email":"marie.martin@email.com","telephone":"+32 478 654 321","date_naissance":"22/07/1989","historique":df2,"s_mutans":1.2,"p_gingivalis":0.1,"diversite":82,"code_patient":"OB-P002"}
    df3 = pd.DataFrame({"Date":["18/02/2025"],"Acte / Test":["Examen Initial"],"S. mutans (%)":[6.5],"P. gingiv. (%)":[1.8],"Diversite (%)":[38],"Status":["Alerte"]})
    patients["Pierre Bernard"] = {"id":"P003","nom":"Pierre Bernard","age":58,"email":"pierre.bernard@email.com","telephone":"+32 495 789 012","date_naissance":"03/11/1966","historique":df3,"s_mutans":6.5,"p_gingivalis":1.8,"diversite":38,"code_patient":"OB-P003"}
    return patients

# ── INIT SESSION ──────────────────────────────────────────────────────────────
for key, val in [("mode","choix"),("connecte",False),("patient_sel","Jean Dupont"),("vue","dashboard"),("patient_connecte",None)]:
    if key not in st.session_state: st.session_state[key] = val
if "patients"        not in st.session_state: st.session_state.patients        = donnees_initiales()
if "anamnes"         not in st.session_state: st.session_state.anamnes         = {}
if "twins"           not in st.session_state: st.session_state.twins           = {}
if "observance"      not in st.session_state: st.session_state.observance      = {}
if "iot_data"        not in st.session_state: st.session_state.iot_data        = {}
if "onboarding_done" not in st.session_state: st.session_state.onboarding_done = False
if "onboarding_step" not in st.session_state: st.session_state.onboarding_step = 1
if "rgpd_accepted"   not in st.session_state: st.session_state.rgpd_accepted   = False
if "lang"            not in st.session_state: st.session_state.lang            = "fr"
if "dark_mode"       not in st.session_state: st.session_state.dark_mode       = False
if "notifs_read"     not in st.session_state: st.session_state.notifs_read     = set()

# ══════════════════════════════════════════════════════════════
# PORTAIL PATIENT
# ══════════════════════════════════════════════════════════════
CODES_PATIENTS = {"OB-P001":"Jean Dupont","OB-P002":"Marie Martin","OB-P003":"Pierre Bernard"}

def get_patient_by_code(code):
    nom = CODES_PATIENTS.get(code)
    return st.session_state.patients.get(nom) if nom else None

def render_portail_patient():
    if st.session_state.patient_connecte is None:
        lh = logo_img(200,"margin:0 auto 20px auto;")
        st.markdown(f"""<div style="max-width:440px;margin:60px auto 0 auto;">
            <div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:20px;padding:36px 40px;text-align:center;color:white;margin-bottom:24px;">
                {lh}<h2 style="font-family:'DM Serif Display',serif;font-size:1.8rem;margin:0 0 6px 0;">Mon Espace Santé</h2>
                <p style="opacity:0.65;font-size:0.9rem;">Accédez à votre bilan microbiome personnalisé</p></div>
            <div style="background:white;border-radius:16px;padding:28px 32px;border:1px solid #e5e7eb;box-shadow:0 4px 16px rgba(0,0,0,0.06);">""", unsafe_allow_html=True)
        code = st.text_input("🔑 Code Patient", placeholder="Ex : OB-P001", help="Fourni par votre dentiste")
        if st.button(t("home_access"), type="primary", use_container_width=True):
            p = get_patient_by_code(code.strip().upper())
            if p: st.session_state.patient_connecte = p; st.rerun()
            else: st.error("❌ Code invalide.")
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button(t("pat_back"), use_container_width=True, key="pat_back_login"):
            st.session_state.mode = "choix"; st.rerun()
        return
    p   = st.session_state.patient_connecte
    nom = p["nom"]; pid = p["id"]
    sm  = p["s_mutans"]; pg = p["p_gingivalis"]; div = p["diversite"]
    rc  = "Élevé" if sm > 3.0 else "Faible"; rp = "Élevé" if pg > 0.5 else "Faible"
    scores = calculer_score_systemique(sm, pg, div)
    plan   = generer_recommandations(sm, pg, div)
    anamnes = get_anamnes(nom)
    # Sidebar
    with st.sidebar:
        lh = logo_img(180,"margin:0 auto 16px auto;display:block;")
        st.markdown(lh, unsafe_allow_html=True)
        st.markdown("---")
        render_lang_selector()
        render_dark_mode_toggle()
        st.markdown("---")
        st.markdown(f"👤 **{t('pat_hello')}, {nom.split()[0]}**")
        hist = p["historique"]
        if len(hist) >= 1:
            dl = 8 if pg > 1.5 or sm > 6 else 12 if (sm > 3 or pg > 0.5 or div < 50) else 24
            try:
                ld   = datetime.strptime(hist.iloc[-1]["Date"],"%d/%m/%Y").date()
                nc   = ld + timedelta(weeks=dl)
                jours = (nc - date.today()).days
                jl   = f"Dans {jours}j" if jours > 0 else "En retard"
                dc   = "#16a34a" if jours > 7 else "#d97706" if jours > 0 else "#e11d48"
                st.markdown(f"<div style='background:{dc}15;border:1px solid {dc}30;border-radius:8px;padding:8px 12px;font-size:0.82rem;'><b>⏰ {t('pat_next_ctrl')}</b><br><span style='color:{dc};font-weight:700;'>{jl}</span></div>", unsafe_allow_html=True)
            except: pass
        st.markdown("---")
        if st.button(t("pat_logout"), use_container_width=True):
            st.session_state.patient_connecte = None; st.rerun()
        if st.button(t("pat_back"), use_container_width=True, key="pat_home"):
            st.session_state.patient_connecte = None; st.session_state.mode = "choix"; st.rerun()
    # En-tête
    c_hdr = "#16a34a" if not (sm>3 or pg>0.5 or div<50) else "#e11d48"
    msg   = "Votre microbiome est équilibré ✅" if not (sm>3 or pg>0.5 or div<50) else "Des déséquilibres ont été détectés ⚠️"
    st.markdown(f"""<div class="patient-header"><div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
        <div><h2 style="margin:0;font-family:'DM Serif Display',serif;">{t('pat_hello')}, {nom} 👋</h2>
        <p style="margin:4px 0 0 0;opacity:0.8;font-size:0.9rem;">{msg}</p></div>
        <span style="background:{c_hdr};padding:6px 18px;border-radius:20px;font-weight:700;font-size:0.88rem;">
        {"🟢 Stable" if not (sm>3 or pg>0.5 or div<50) else "🔴 Alerte"}</span></div></div>""", unsafe_allow_html=True)

    # Onglets patient (12)
    tab_labels = [t("pat_profile"),t("pat_systemic"),t("pat_photo"),"🩻 Mes Radios",t("pat_actions"),
                  t("pat_nutrition"),t("pat_anamnes"),t("pat_twin"),t("pat_share"),t("pat_pdf"),
                  t("pat_observance"),t("pat_iot"),t("pat_privisite")]
    tabs = st.tabs(tab_labels)

    # ── 1. Profil ──────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("### 📊 Mon Profil Microbiome")
        col_m1, col_m2, col_m3 = st.columns(3)
        def metric_card(col, label, value, level, color, icon):
            col.markdown(f"""<div style="background:linear-gradient(135deg,{color}15,{color}05);border:2px solid {color};border-radius:14px;padding:20px;text-align:center;">
                <div style="font-size:1.8rem;">{icon}</div>
                <div style="font-size:0.7rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin:6px 0 4px 0;">{label}</div>
                <div style="font-family:'DM Serif Display',serif;font-size:1.6rem;color:{color};">{value}</div>
                <div style="font-size:0.8rem;color:{color};font-weight:600;margin-top:4px;">{level}</div></div>""", unsafe_allow_html=True)
        rc_c = "#e11d48" if sm>3 else "#16a34a"; rp_c = "#e11d48" if pg>0.5 else "#16a34a"; div_c = "#16a34a" if div>=65 else "#d97706" if div>=50 else "#e11d48"
        metric_card(col_m1, t("metric_caries"),    f"{sm}%",     t("metric_high") if sm>3 else t("metric_low"),     rc_c,  "🦠")
        metric_card(col_m2, t("metric_paro"),      f"{pg}%",     t("metric_high") if pg>0.5 else t("metric_low"),  rp_c,  "🩸")
        metric_card(col_m3, t("metric_diversity"), f"{div}/100", "🟢 Excellent" if div>=65 else "⚠️ Modéré" if div>=50 else "🔴 Faible", div_c, "🌱")
        st.markdown("---")
        render_diversity_benchmark(div, p.get("age"), context="patient")
        st.markdown("---")
        st.markdown("### 📅 Historique des Analyses")
        hist = p["historique"]
        if hist.empty: st.info("Aucune analyse.")
        else:
            st.dataframe(hist, use_container_width=True, hide_index=True)
            dc = next((c for c in ["Diversite (%)","Diversité (%)"] if c in hist.columns), None)
            if dc and len(hist) >= 2:
                st.caption("Évolution de la diversité")
                st.line_chart(hist[[dc]].astype(float), height=150)

    # ── 2. Risques Systémiques ─────────────────────────────────────
    with tabs[1]:
        st.markdown("### 🧬 Risques Systémiques")
        st.caption("Basé sur les corrélations de la littérature scientifique publiée")
        for key, data in scores.items():
            sc2 = data["score"]; lv = data["level"]
            cc  = "#e11d48" if lv=="high" else "#d97706" if lv=="med" else "#16a34a"
            pct = min(100, sc2)
            with st.container():
                st.markdown(f"""<div class="systemic-card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                    <div><div class="systemic-title">{data['icon']} {data['label']}</div>
                    <div style="font-size:0.82rem;color:#6b7280;max-width:520px;">{data['description']}</div></div>
                    <div class="score-ring score-{'high' if lv=='high' else 'med' if lv=='med' else 'low'}">{sc2}</div></div>
                    <div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:{pct}%;background:{cc};"></div></div>
                    <div style="font-size:0.7rem;color:#9ca3af;margin-top:2px;text-align:right;">{data['references']}</div></div>""", unsafe_allow_html=True)
                if lv == "high":
                    with st.expander(f"📋 Plan d'action détaillé — {data['label']}"):
                        for action in data["actions"]: st.markdown(f"- {action}")

    # ── 3. Photo ───────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("### 📸 Analyse Photo Intelligente")
        st.info("📷 Prenez une photo de votre bouche en bonne lumière (dents visibles). L'IA analysera votre santé visuelle.")
        uploaded = st.file_uploader("Photo de votre bouche", type=["jpg","jpeg","png","webp"], label_visibility="visible")
        if uploaded:
            img_bytes = uploaded.read(); mime = "image/png" if uploaded.name.endswith(".png") else "image/jpeg"
            st.image(img_bytes, use_container_width=True)
            rkey = f"photo_result_{pid}"
            if rkey not in st.session_state or st.button("🔄 Relancer l'analyse"):
                with st.spinner("🤖 Analyse IA en cours..."):
                    st.session_state[rkey] = analyser_photo_bouche(img_bytes, mime)
                st.rerun()
            if rkey in st.session_state: render_photo_analysis(st.session_state[rkey])
        elif st.button("📸 Voir une démo", key="demo_photo_pat"):
            st.session_state[f"photo_result_{pid}"] = {"qualite_image":"bonne","zones_analysees":["Gencives","Dents antérieures","Zone postérieure"],"findings":[{"zone":"Gencives","observation":"Légère inflammation gingivale détectée","severite":"attention","detail":"Bord gingival rougeâtre"},{"zone":"Dents antérieures","observation":"Légères traces de tartre","severite":"attention","detail":"Dépôts minéraux superficiels"}],"score_global":62,"profil_visuel":"Inflammation légère","recommandations_immediates":["Détartrage préventif recommandé","Renforcer le brossage interdentaire","Consultation dans 3 mois"],"disclaimer":"Aide à la décision uniquement.","confiance":"modérée"}
            st.rerun()
        if f"photo_result_{pid}" in st.session_state and not uploaded: render_photo_analysis(st.session_state[f"photo_result_{pid}"])

    # ── 3b. Radios ─────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("### 🩻 Mes Radiographies")
        st.caption("Importez vos clichés fournis par votre cabinet. L'IA analyse caries, os alvéolaire, dents et génère un rapport clinique.")
        render_radio_uploader(pid, patient=p, context="patient")

    # ── 4. Plan d'Action ───────────────────────────────────────────
    with tabs[4]:
        st.markdown("### 🚨 Mes Actions Prioritaires")
        st.markdown(f"""<div class="{'reco-red' if (sm>3 or pg>0.5 or div<50) else 'reco-green'} reco-card">
            <b>{plan['profil_label']}</b><br><span style='font-size:0.9rem;'>{plan['profil_description']}</span>
            <br><span style='font-size:0.85rem;color:#6b7280;'>⏱️ Contrôle dans : {plan['suivi_semaines']} semaines</span></div>""", unsafe_allow_html=True)
        for i, prio in enumerate(plan["priorites"], 1):
            bc = "#e11d48" if prio["urgence"]=="Elevee" else "#d97706" if prio["urgence"]=="Moderee" else "#16a34a"
            with st.expander(f"Priorité {i} — {prio['icone']} {prio['titre']} [{prio['urgence']}]", expanded=(i==1)):
                st.info(prio["explication"])
                for action in prio["actions"]: st.markdown(f"- ✅ {action}")
        if plan["probiotiques"]:
            st.markdown("---"); st.markdown("### 🧫 Probiotiques Recommandés")
            for pr in plan["probiotiques"]:
                st.markdown(f"""<div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:1.5px solid #16a34a40;border-radius:12px;padding:16px 20px;margin:8px 0;">
                    <div style="font-weight:700;color:#15803d;font-size:0.95rem;">{pr['nom']}</div>
                    <div style="font-size:0.83rem;color:#374151;margin-top:6px;">💊 <b>Forme :</b> {pr['forme']} · ⏳ <b>Durée :</b> {pr['duree']}<br>
                    🎯 <b>Bénéfice :</b> {pr['benefice']} · 🏪 <b>Produits :</b> {pr['marques']}</div></div>""", unsafe_allow_html=True)

    # ── 5. Nutrition ───────────────────────────────────────────────
    with tabs[5]:
        st.markdown("### 🥗 Nutrition & Probiotiques")
        n1, n2 = st.columns(2)
        with n1:
            st.markdown("#### ✅ Aliments à favoriser")
            for a in plan["aliments_favoriser"]: st.markdown(f'<span class="pill-green">✅ {a}</span>', unsafe_allow_html=True)
        with n2:
            st.markdown("#### ❌ Aliments à éviter")
            for a in plan["aliments_eviter"]: st.markdown(f'<span class="pill-red">❌ {a}</span>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("#### 🔬 Pourquoi l'alimentation affecte votre microbiome oral ?")
        st.markdown("""Votre microbiome oral est composé de **500 à 700 espèces bactériennes**. Chaque repas modifie son équilibre :

- **Sucres rapides** → carburant pour *S. mutans* → acidification → caries
- **Polyphénols** (thé, myrtilles) → effet antibactérien naturel contre *P. gingivalis*
- **Fibres prébiotiques** → nourrissent les bactéries protectrices → ↑ diversité
- **Probiotiques alimentaires** (yaourt, kéfir) → réensemencent la flore après perturbation""")

    # ── 6. Anamnèse ────────────────────────────────────────────────
    with tabs[6]:
        st.markdown("### 📋 Mon Questionnaire de Santé")
        st.caption("Informations transmises de façon sécurisée à votre praticien")
        if anamnes.get("completed_at"): st.success(f"✅ Questionnaire rempli le {anamnes['completed_at'][:10]}.")
        with st.form(f"anamnes_form_pat_{pid}"):
            st.markdown("**Informations générales**")
            ac1, ac2, ac3 = st.columns(3)
            with ac1: a_taille=st.number_input("Taille (cm)",140,220,170)
            with ac2: a_poids=st.number_input("Poids (kg)",40,200,70)
            with ac3: a_fumeur=st.selectbox("Tabac",["Non-fumeur","Ex-fumeur","Fumeur"])
            st.markdown("**Antécédents médicaux**")
            bc1, bc2, bc3 = st.columns(3)
            with bc1: a_diab=st.checkbox("Diabète",value=anamnes.get("diabete",False)); a_hta=st.checkbox("Hypertension",value=anamnes.get("hypertension",False))
            with bc2: a_card=st.checkbox("Maladie cardiovasculaire",value=anamnes.get("cardiovasculaire",False)); a_neo=st.checkbox("Cancer en cours / traitement",value=anamnes.get("cancer",False))
            with bc3: a_ost=st.checkbox("Ostéoporose",value=anamnes.get("osteoporose",False)); a_alz=st.checkbox("Alzheimer / Démence",value=anamnes.get("alzheimer",False))
            st.markdown("**Hygiène buccale**")
            hc1, hc2 = st.columns(2)
            with hc1: a_brosse_freq=st.selectbox("Fréquence brossage",["1×/jour","2×/jour","3×/jour"])
            with hc2: a_fil=st.checkbox("Fil dentaire quotidien",value=anamnes.get("fil_dentaire",False))
            st.markdown("**Médicaments**")
            a_meds = st.checkbox("Prend des médicaments", value=anamnes.get("prend_medicaments",False))
            a_liste_meds = ""
            if a_meds: a_liste_meds=st.text_area("Liste des médicaments",value=anamnes.get("liste_medicaments",""),placeholder="Ex: Metformine 1000mg, Amlodipine 5mg",height=60)
            a_antibio = st.checkbox("Antibiotiques au cours des 3 derniers mois",value=anamnes.get("antibiotiques_recents",False))
            a_notes = st.text_area("Remarques libres",value=anamnes.get("notes_libres",""),placeholder="Douleurs, symptômes particuliers...",height=60)
            if st.form_submit_button("💾 Enregistrer mon questionnaire", use_container_width=True, type="primary"):
                save_anamnes(nom, {"taille":a_taille,"poids":a_poids,"fumeur":a_fumeur,"diabete":a_diab,"hypertension":a_hta,"cardiovasculaire":a_card,"cancer":a_neo,"osteoporose":a_ost,"alzheimer":a_alz,"brosse_freq":a_brosse_freq,"fil_dentaire":a_fil,"prend_medicaments":a_meds,"liste_medicaments":a_liste_meds,"antibiotiques_recents":a_antibio,"notes_libres":a_notes})
                st.success("✅ Questionnaire enregistré et transmis à votre praticien !"); st.rerun()

    # ── 7. Twin ────────────────────────────────────────────────────
    with tabs[7]:
        render_twin_patient(p)

    # ── 8. Partager ────────────────────────────────────────────────
    with tabs[8]:
        st.markdown("### 📤 Partager mon Bilan")
        url = f"https://app.oralbiome.com/patient/{pid}"
        st.text_input("Lien de partage sécurisé", value=url, disabled=True)
        sc1, sc2, sc3 = st.columns(3)
        with sc1: st.button("📧 Email à mon médecin", use_container_width=True)
        with sc2: st.button("📱 WhatsApp", use_container_width=True)
        with sc3: st.button("🖨️ Imprimer / PDF", use_container_width=True)
        st.markdown("---"); st.info("🔒 Vos données sont protégées. Seul le destinataire peut accéder au rapport sécurisé.")

    # ── 9. PDF ─────────────────────────────────────────────────────
    with tabs[9]:
        st.markdown(f"### 📥 {t('pat_pdf')}")
        st.markdown("Téléchargez votre rapport personnel complet incluant tous vos résultats.")
        if st.button("Générer mon rapport PDF", type="primary", use_container_width=True):
            with st.spinner("Génération du PDF..."):
                pdf_data = generer_pdf(nom, rc, rp, div, p["historique"], plan, scores)
            if pdf_data:
                st.download_button("📥 Télécharger le rapport", data=pdf_data, file_name=f"OralBiome_{nom.replace(' ','_')}_{date.today().strftime('%Y%m%d')}.pdf", mime="application/pdf", use_container_width=True, type="primary")

    # ── 10. Observance ─────────────────────────────────────────────
    with tabs[10]:
        render_observance_patient(pid, sm, pg, div)

    # ── 11. Brosse Connectée ───────────────────────────────────────
    with tabs[11]:
        render_iot_dashboard(p)

    # ── 12. Pré-Visite ─────────────────────────────────────────────
    with tabs[12]:
        render_salle_attente_patient(p)


# ══════════════════════════════════════════════════════════════
# PORTAIL PRATICIEN
# ══════════════════════════════════════════════════════════════
PRAT_EMAIL    = "contact@oralbiome.com"
PRAT_PASSWORD = hashlib.sha256("mvp2024".encode()).hexdigest()

def render_login_praticien():
    lh = logo_img(200,"margin:0 auto 24px auto;")
    st.markdown(f"""<div style="max-width:440px;margin:60px auto 0 auto;">
        <div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:20px;padding:36px 40px;text-align:center;color:white;margin-bottom:24px;">
            {lh}<h2 style="font-family:'DM Serif Display',serif;font-size:1.8rem;margin:0;">{t('prat_login_title')}</h2>
            <p style="opacity:0.65;font-size:0.9rem;">Plateforme professionnelle · Données sécurisées</p></div>
        <div style="background:white;border-radius:16px;padding:28px 32px;border:1px solid #e5e7eb;box-shadow:0 4px 16px rgba(0,0,0,0.06);">""", unsafe_allow_html=True)
    email = st.text_input(t("prat_email"), placeholder="contact@cabinet.com")
    password = st.text_input(t("prat_password"), type="password")
    c_login, c_back = st.columns(2)
    with c_login:
        if st.button(t("prat_connect"), use_container_width=True, type="primary"):
            if email.strip() == PRAT_EMAIL and hashlib.sha256(password.encode()).hexdigest() == PRAT_PASSWORD:
                st.session_state.connecte = True
                if not st.session_state.onboarding_done:
                    st.session_state.onboarding_step = 1
                st.rerun()
            else: st.error("❌ Identifiants invalides.")
    with c_back:
        if st.button(t("prat_back"), use_container_width=True, key="back_login"):
            st.session_state.mode = "choix"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("Démo — Email : contact@oralbiome.com · Mot de passe : mvp2024")

def render_dossier_patient(nom, patients):
    p   = patients[nom]
    pid = p["id"]; sm = p["s_mutans"]; pg = p["p_gingivalis"]; div = p["diversite"]
    hist = p["historique"]
    rc  = "Élevé" if sm > 3.0 else "Faible"; rp = "Élevé" if pg > 0.5 else "Faible"
    scores_sys = calculer_score_systemique(sm, pg, div)
    plan   = generer_recommandations(sm, pg, div)
    anamnes_p = get_anamnes(nom)

    # En-tête dossier
    ea = sm>3.0 or pg>0.5 or div<50; sc = "#e11d48" if ea else "#16a34a"
    nbj_retard = 0
    if not hist.empty:
        try:
            dl = 8 if pg>1.5 or sm>6 else 12 if ea else 24
            ld = datetime.strptime(hist.iloc[-1]["Date"],"%d/%m/%Y").date()
            nc = ld + timedelta(weeks=dl)
            nbj_retard = max(0, (date.today()-nc).days)
        except: pass
    top3 = list(scores_sys.items())[:3]
    obs_score = calculer_score_observance(pid)
    obs_badge = get_observance_badge(obs_score)
    st.markdown(f"""<div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:16px;padding:22px 28px;margin-bottom:20px;color:white;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
            <div><div style="font-family:'DM Serif Display',serif;font-size:1.6rem;">{nom}</div>
            <div style="opacity:0.65;font-size:0.85rem;">{pid} · {p.get('age','')} ans · {p.get('email','')} · {p.get('telephone','')}</div>
            <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;">
                <span style="background:{'#e11d48' if sm>3 else '#16a34a'};color:white;padding:3px 10px;border-radius:12px;font-size:0.76rem;font-weight:700;">S. mutans {sm}%</span>
                <span style="background:{'#e11d48' if pg>0.5 else '#16a34a'};color:white;padding:3px 10px;border-radius:12px;font-size:0.76rem;font-weight:700;">P. gingivalis {pg}%</span>
                <span style="background:{'#16a34a' if div>=65 else '#d97706' if div>=50 else '#e11d48'};color:white;padding:3px 10px;border-radius:12px;font-size:0.76rem;font-weight:700;">Diversité {div}/100</span>
                <span style="background:{obs_badge['color']};color:white;padding:3px 10px;border-radius:12px;font-size:0.76rem;font-weight:700;">{obs_badge['label']} {obs_score}/100</span>
            </div></div>
            <div style="text-align:right;">
                <div style="background:{'#e11d48' if ea else '#16a34a'};color:white;padding:6px 16px;border-radius:12px;font-weight:700;font-size:0.85rem;">{'🔴 Alerte' if ea else '🟢 Stable'}</div>
                {f'<div style="margin-top:6px;font-size:0.75rem;color:#fca5a5;">⏰ Contrôle en retard de {nbj_retard}j</div>' if nbj_retard > 0 else ''}</div></div>
        </div></div>""", unsafe_allow_html=True)
    top3_html = "".join(f'<span style="background:rgba(255,255,255,0.1);color:rgba(255,255,255,0.8);padding:3px 10px;border-radius:10px;font-size:0.75rem;">{data["icon"]} {data["label"]} {data["score"]}/100</span>' for _, data in top3)
    st.markdown(f'<div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap;">{top3_html}</div>', unsafe_allow_html=True)

    # Navigation rapide
    na1, na2, na3, na4 = st.columns(4)
    with na1:
        if st.button("📸 Analyse Photo", use_container_width=True, key=f"prat_quick_photo_{pid}"):
            st.session_state[f"dossier_tab_{pid}"] = "photo"
    with na2:
        if st.button("🦷 Twin Numérique", use_container_width=True, key=f"prat_quick_twin_{pid}"):
            st.session_state[f"dossier_tab_{pid}"] = "twin"
    with na3:
        if st.button("📥 Générer PDF", use_container_width=True, key=f"prat_quick_pdf_{pid}"):
            with st.spinner("PDF..."):
                pdf_data = generer_pdf(nom, rc, rp, div, hist, plan, scores_sys)
            st.download_button("📥 Télécharger", data=pdf_data, file_name=f"OralBiome_{nom.replace(' ','_')}_{date.today().strftime('%Y%m%d')}.pdf", mime="application/pdf", key=f"prat_pdf_{pid}")
    with na4:
        if st.button("🏥 Salle d'Attente", use_container_width=True, key=f"prat_quick_salle_{pid}"):
            st.session_state[f"dossier_tab_{pid}"] = "salle"

    # Onglets praticien (10)
    tab_labels = ["🧬 Risques Systémiques","🚨 Plan d'Action","🔬 Simulateur",
                  "📸 Analyse Photo","🩻 Radiographies IA","📂 Historique & PDF","🦷 Twin Numérique",
                  "📈 Observance","💊 Interactions","🏥 Salle d'Attente","📱 Objets Connectés"]
    tabs_prat = st.tabs(tab_labels)

    # ── 1. Risques Systémiques ─────────────────────────────────────
    with tabs_prat[0]:
        st.markdown("### 🧬 Risques Systémiques")
        render_diversity_benchmark(div, p.get("age"), context="praticien")
        st.markdown("---")
        for key, data in scores_sys.items():
            sc2 = data["score"]; lv = data["level"]
            cc  = "#e11d48" if lv=="high" else "#d97706" if lv=="med" else "#16a34a"
            pct = min(100, sc2)
            with st.expander(f"{data['icon']} {data['label']} — {sc2}/100 {'🔴' if lv=='high' else '🟡' if lv=='med' else '🟢'}", expanded=(lv=="high")):
                col_i, col_sc = st.columns([3, 1])
                with col_i:
                    st.markdown(f"**Description :** {data['description']}")
                    st.markdown(f"**Références :** *{data['references']}*")
                    st.markdown(f"<div class='progress-bar-wrap'><div class='progress-bar-fill' style='width:{pct}%;background:{cc};'></div></div>", unsafe_allow_html=True)
                with col_sc:
                    ring_cls = "score-high" if lv=="high" else "score-med" if lv=="med" else "score-low"
                    st.markdown(f'<div class="score-ring {ring_cls}" style="margin:0 auto;">{sc2}</div>', unsafe_allow_html=True)
                st.markdown("**Actions recommandées :**")
                for action in data["actions"]: st.markdown(f"- {action}")

    # ── 2. Plan d'Action ───────────────────────────────────────────
    with tabs_prat[1]:
        st.markdown(f"### 🚨 Plan d'Action — {nom}")
        pr_bg = "#fff1f2" if plan["profil_label"].startswith("🔴") else "#fffbeb" if plan["profil_label"].startswith("🟡") else "#f0fdf4"
        pr_bc = "#e11d48" if plan["profil_label"].startswith("🔴") else "#d97706" if plan["profil_label"].startswith("🟡") else "#16a34a"
        st.markdown(f"""<div style="background:{pr_bg};border:2px solid {pr_bc}40;border-radius:12px;padding:14px 18px;margin-bottom:18px;">
            <div style="font-weight:700;font-size:1rem;color:{pr_bc};">{plan['profil_label']}</div>
            <div style="font-size:0.87rem;color:#374151;margin-top:4px;">{plan['profil_description']}</div>
            <div style="font-size:0.82rem;color:#6b7280;margin-top:6px;">⏱️ Prochain contrôle recommandé : <b>{plan['suivi_semaines']} semaines</b></div></div>""", unsafe_allow_html=True)
        for i, prio in enumerate(plan["priorites"], 1):
            bc = "#e11d48" if prio["urgence"]=="Elevee" else "#d97706" if prio["urgence"]=="Moderee" else "#16a34a"
            st.markdown(f"""<div style="background:#fff;border:1px solid {bc}30;border-left:4px solid {bc};border-radius:10px;padding:14px 18px;margin:10px 0;">
                <div style="font-weight:700;color:{bc};font-size:0.95rem;">{i}. {prio['icone']} {prio['titre']} — {prio['urgence']}</div>
                <div style="font-size:0.82rem;color:#6b7280;margin:4px 0 8px 0;">{prio['explication']}</div>
                {"".join(f'<div style="font-size:0.85rem;color:#374151;margin:2px 0;">• {a}</div>' for a in prio["actions"])}</div>""", unsafe_allow_html=True)
        if plan["probiotiques"]:
            st.markdown("---"); st.markdown("#### 🧫 Probiotiques Recommandés")
            for pr in plan["probiotiques"]:
                st.markdown(f"""<div style="background:#f0fdf4;border:1px solid #16a34a30;border-radius:10px;padding:12px 16px;margin:8px 0;">
                    <div style="font-weight:700;color:#15803d;">{pr['nom']}</div>
                    <div style="font-size:0.83rem;color:#374151;margin-top:4px;">💊 {pr['forme']} · ⏳ {pr['duree']} · 🎯 {pr['benefice']}<br>🏪 {pr['marques']}</div></div>""", unsafe_allow_html=True)

    # ── 3. Simulateur ──────────────────────────────────────────────
    with tabs_prat[2]:
        st.markdown("### 🔬 Simulateur Microbiome")
        st.caption("Projeter l'impact d'interventions thérapeutiques sur les biomarqueurs et risques systémiques")
        ss1, ss2, ss3 = st.columns(3)
        with ss1: sim_sm  = st.slider("S. mutans simulé (%)",  0.0, 10.0, float(sm),  step=0.1, key=f"sim_sm_{pid}")
        with ss2: sim_pg  = st.slider("P. gingivalis simulé (%):", 0.0, 5.0,  float(pg),  step=0.05, key=f"sim_pg_{pid}")
        with ss3: sim_div = st.slider("Diversité simulée", 0, 100, int(div), step=1, key=f"sim_div_{pid}")
        if st.button("🔄 Calculer la projection", use_container_width=True, type="primary", key=f"sim_run_{pid}"):
            scores_sim = calculer_score_systemique(sim_sm, sim_pg, sim_div)
            st.markdown("#### Comparaison Actuel vs Simulé")
            comp_rows = []
            for key, data in scores_sys.items():
                sim_d = scores_sim[key]
                diff  = sim_d["score"] - data["score"]
                arrow = "↑" if diff > 0 else "↓" if diff < 0 else "="
                color = "#e11d48" if diff > 0 else "#16a34a" if diff < 0 else "#6b7280"
                comp_rows.append({"Pathologie":f"{data['icon']} {data['label']}","Actuel":data["score"],"Simulé":sim_d["score"],"Δ":f"<span style='color:{color};font-weight:700;'>{arrow} {diff:+d}</span>"})
            df_comp = pd.DataFrame(comp_rows)
            st.markdown(df_comp.drop(columns=["Δ"]).to_html(index=False, border=0), unsafe_allow_html=True)

    # ── 4. Photo ───────────────────────────────────────────────────
    with tabs_prat[3]:
        st.markdown(f"### 📸 Analyse Photo — {nom}")
        uploaded = st.file_uploader("Photo clinique", type=["jpg","jpeg","png","webp"], key=f"prat_photo_{pid}")
        if uploaded:
            img_bytes = uploaded.read(); mime = "image/png" if uploaded.name.endswith(".png") else "image/jpeg"
            col_img, col_res = st.columns([1, 2])
            with col_img: st.image(img_bytes, use_container_width=True)
            with col_res:
                rkey = f"prat_photo_result_{pid}"
                if rkey not in st.session_state or st.button("🔄 Relancer"):
                    with st.spinner("Analyse IA..."): st.session_state[rkey] = analyser_photo_bouche(img_bytes, mime)
                if rkey in st.session_state: render_photo_analysis(st.session_state[rkey])
        elif st.button("📸 Démo clinique", key=f"demo_prat_{pid}"):
            st.session_state[f"prat_photo_result_{pid}"] = {"qualite_image":"bonne","zones_analysees":["Gencives","Incisives","Zone molaires","Langue"],"findings":[{"zone":"Gencives inférieures","observation":"Hyperplasie gingivale légère","severite":"attention","detail":"Possible réaction médicamenteuse"},{"zone":"Dents postérieures","observation":"Dépôts de tartre sous-gingival","severite":"alerte","detail":"Indication détartrage urgent"}],"score_global":48,"profil_visuel":"Inflammation modérée","recommandations_immediates":["Détartrage urgent","Vérifier liste médicamenteuse","Réévaluation à 3 mois"],"disclaimer":"Aide à la décision clinique.","confiance":"élevée"}
            st.rerun()
        if f"prat_photo_result_{pid}" in st.session_state and not uploaded:
            render_photo_analysis(st.session_state[f"prat_photo_result_{pid}"])

    # ── 4b. Radiographies IA ──────────────────────────────────────
    with tabs_prat[4]:
        st.markdown(f"### 🩻 Radiographies IA — {nom}")
        st.caption("Analysez les clichés OPG ou rétro-alvéolaires du patient · Détection caries, perte osseuse, lésions, plan de traitement IA")
        render_radio_uploader(pid, patient=p, context="praticien")

    # ── 5. Historique & PDF ────────────────────────────────────────
    with tabs_prat[5]:
        st.markdown(f"### 📂 Historique — {nom}")
        if not hist.empty:
            st.dataframe(hist, use_container_width=True, hide_index=True)
            dc = next((c for c in ["Diversite (%)","Diversité (%)"] if c in hist.columns), None)
            if dc and len(hist) >= 2:
                chart_h = pd.DataFrame({c:hist[c].astype(float) for c in hist.columns if c not in ["Date","Acte / Test","Status"]})
                st.line_chart(chart_h, height=180)
        else: st.info("Aucune analyse enregistrée.")
        st.markdown("---"); st.markdown("#### ➕ Ajouter une visite")
        with st.form(f"add_hist_{pid}"):
            ah1, ah2, ah3, ah4 = st.columns(4)
            with ah1: ah_acte=st.text_input("Acte",value="Contrôle")
            with ah2: ah_sm=st.number_input("S. mutans (%)",0.0,10.0,float(sm),step=0.1)
            with ah3: ah_pg=st.number_input("P. gingivalis (%)",0.0,5.0,float(pg),step=0.05)
            with ah4: ah_div=st.number_input("Diversité",0,100,int(div))
            if st.form_submit_button("Enregistrer cette visite", use_container_width=True, type="primary"):
                stat2 = "Alerte" if ah_sm>3.0 or ah_pg>0.5 or ah_div<50 else "Stable"
                new_row = {"Date":date.today().strftime("%d/%m/%Y"),"Acte / Test":ah_acte,"S. mutans (%)":ah_sm,"P. gingiv. (%)":ah_pg,"Diversite (%)":ah_div,"Status":stat2}
                st.session_state.patients[nom]["historique"] = pd.concat([hist,pd.DataFrame([new_row])],ignore_index=True)
                for k,v in [("s_mutans",ah_sm),("p_gingivalis",ah_pg),("diversite",ah_div)]: st.session_state.patients[nom][k]=v
                st.success("✅ Visite enregistrée."); st.rerun()
        st.markdown("---"); st.markdown("#### 📥 Générer le Rapport PDF")
        if st.button("Générer le rapport complet", use_container_width=True, type="primary", key=f"gen_pdf_{pid}"):
            with st.spinner("Génération PDF..."): pdf_data = generer_pdf(nom, rc, rp, div, hist, plan, scores_sys)
            if pdf_data: st.download_button("📥 Télécharger", data=pdf_data, file_name=f"OralBiome_{nom.replace(' ','_')}_{date.today().strftime('%Y%m%d')}.pdf", mime="application/pdf", use_container_width=True, type="primary")

    # ── 6. Twin Numérique ──────────────────────────────────────────
    with tabs_prat[6]:
        render_twin_praticien(p)

    # ── 7. Observance ──────────────────────────────────────────────
    with tabs_prat[7]:
        render_observance_praticien(p)

    # ── 8. Interactions ────────────────────────────────────────────
    with tabs_prat[8]:
        render_interactions_medicamenteuses(p, anamnes_p)

    # ── 9. Salle d'Attente ─────────────────────────────────────────
    with tabs_prat[9]:
        render_salle_attente_praticien(p)

    # ── 10. Objets Connectés ───────────────────────────────────────
    with tabs_prat[10]:
        render_iot_dashboard(p)

def render_portail_praticien():
    patients = st.session_state.patients
    # Onboarding
    if not st.session_state.onboarding_done:
        render_onboarding(); return
    # Sidebar
    with st.sidebar:
        lh = logo_img(180,"margin:0 auto 16px auto;display:block;")
        st.markdown(lh, unsafe_allow_html=True)
        cab = st.session_state.get("cabinet_nom","Dr. OralBiome")
        pra = st.session_state.get("cabinet_praticien","Praticien")
        st.markdown(f"""<div style="background:linear-gradient(135deg,#1a3a5c,#2563eb);border-radius:10px;padding:12px 14px;margin-bottom:8px;">
            <div style="font-weight:700;color:white;font-size:0.9rem;">{pra}</div>
            <div style="font-size:0.75rem;color:rgba(255,255,255,0.7);">{cab}</div></div>""", unsafe_allow_html=True)
        st.markdown("---")
        render_lang_selector()
        render_dark_mode_toggle()
        st.markdown("---")
        render_notifications(patients)
        st.markdown("---")
        st.markdown("**Navigation**")
        if st.button("📊 Dashboard", use_container_width=True, key="nav_dash"):
            st.session_state.vue = "dashboard"; st.rerun()
        st.markdown("**Patients**")
        for nom in list(patients.keys()):
            p = patients[nom]
            ea = p["s_mutans"]>3.0 or p["p_gingivalis"]>0.5 or p["diversite"]<50
            obs = calculer_score_observance(p["id"])
            lbl = f"{'🔴' if ea else '🟢'} {nom}"
            if st.button(lbl, key=f"nav_{nom}", use_container_width=True):
                st.session_state.patient_sel = nom; st.session_state.vue = "dossier"; st.rerun()
        st.markdown("---")
        st.markdown("**Gestion**")
        if st.button("➕ Ajouter un patient", use_container_width=True, key="add_pat"):
            st.session_state.vue = "ajout_patient"; st.rerun()
        if st.button(t("prat_disconnect"), use_container_width=True, key="logout_prat"):
            for k in ["connecte","mode","vue"]: st.session_state[k] = False if k=="connecte" else ("choix" if k=="mode" else "dashboard")
            st.rerun()

    # Contenu principal
    vue = st.session_state.get("vue","dashboard")
    if vue == "dashboard":
        render_dashboard(patients)
    elif vue == "dossier":
        nom = st.session_state.get("patient_sel","")
        if nom and nom in patients:
            col_back, _ = st.columns([1,6])
            with col_back:
                if st.button("← Tableau de bord", key="back_to_dash"): st.session_state.vue="dashboard"; st.rerun()
            render_dossier_patient(nom, patients)
        else: st.error("Patient introuvable.")
    elif vue == "ajout_patient":
        col_back, _ = st.columns([1,6])
        with col_back:
            if st.button("← Retour", key="back_add"): st.session_state.vue="dashboard"; st.rerun()
        st.markdown("### ➕ Nouveau Patient")
        with st.form("form_add_patient"):
            fc1, fc2, fc3 = st.columns(3)
            with fc1: n_nom=st.text_input("Nom complet *"); n_age=st.number_input("Âge",1,120,35)
            with fc2: n_email=st.text_input("Email",placeholder="patient@email.com"); n_tel=st.text_input("Téléphone",placeholder="+32 4XX XXX XXX")
            with fc3: n_sm=st.number_input("S. mutans (%)",0.0,10.0,2.0,step=0.1); n_pg=st.number_input("P. gingivalis (%)",0.0,5.0,0.1,step=0.05)
            n_div = st.slider("Score Diversité", 0, 100, 70)
            n_notes = st.text_area("Notes initiales", height=60)
            if st.form_submit_button("Créer le dossier →", use_container_width=True, type="primary"):
                if n_nom.strip():
                    nid = f"P{str(len(patients)+1).zfill(3)}"
                    stat = "Alerte" if n_sm>3.0 or n_pg>0.5 or n_div<50 else "Stable"
                    df_n = pd.DataFrame({"Date":[date.today().strftime("%d/%m/%Y")],"Acte / Test":["Examen Initial"],"S. mutans (%)":[n_sm],"P. gingiv. (%)":[n_pg],"Diversite (%)":[n_div],"Status":[stat]})
                    st.session_state.patients[n_nom] = {"id":nid,"nom":n_nom,"age":n_age,"email":n_email,"telephone":n_tel,"date_naissance":"","historique":df_n,"s_mutans":n_sm,"p_gingivalis":n_pg,"diversite":n_div,"code_patient":f"OB-{nid}"}
                    if n_notes: save_anamnes(n_nom,{"notes_libres":n_notes})
                    st.session_state.patient_sel = n_nom; st.session_state.vue = "dossier"
                    st.success(f"✅ Dossier créé — Code patient : OB-{nid}"); st.rerun()
                else: st.error("Le nom est obligatoire.")


# ══════════════════════════════════════════════════════════════
# ÉCRAN D'ACCUEIL
# ══════════════════════════════════════════════════════════════
def render_home():
    st.markdown(f"""<div style="background:linear-gradient(135deg,#0a1628 0%,#1a3a5c 60%,#0d2640 100%);border-radius:24px;padding:60px 40px;text-align:center;margin-bottom:40px;position:relative;overflow:hidden;">
        <div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;background:rgba(56,189,248,0.08);border-radius:50%;"></div>
        <div style="position:absolute;bottom:-30px;left:-30px;width:160px;height:160px;background:rgba(37,99,235,0.08);border-radius:50%;"></div>
        {logo_img(260,"margin:0 auto 20px auto;")}
        <p style="color:rgba(255,255,255,0.6);font-size:1rem;margin:0 0 32px 0;">Intelligence Microbiome Orale · Médecine Prédictive · Numérotation FDI</p>
        <div style="display:flex;justify-content:center;gap:16px;flex-wrap:wrap;">
            <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:12px;padding:10px 18px;color:rgba(255,255,255,0.8);font-size:0.85rem;">🧬 Microbiome Prédictif</div>
            <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:12px;padding:10px 18px;color:rgba(255,255,255,0.8);font-size:0.85rem;">🦷 Twin Numérique</div>
            <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:12px;padding:10px 18px;color:rgba(255,255,255,0.8);font-size:0.85rem;">🧠 IA Clinique</div>
            <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:12px;padding:10px 18px;color:rgba(255,255,255,0.8);font-size:0.85rem;">📱 Objets Connectés</div>
            <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:12px;padding:10px 18px;color:rgba(255,255,255,0.8);font-size:0.85rem;">📊 NHANES n=8 237</div>
        </div></div>""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div style="background:linear-gradient(135deg,#1a3a5c,#0f2744);border-radius:20px;padding:32px 28px;text-align:center;color:white;height:100%;">
            <div style="font-size:3rem;margin-bottom:12px;">🦷</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.4rem;margin-bottom:8px;">Espace Praticien</div>
            <div style="color:rgba(255,255,255,0.65);font-size:0.85rem;margin-bottom:20px;">Dashboard · Dossiers · IA Clinique · Rapports PDF · Twin Numérique · IoT</div></div>""", unsafe_allow_html=True)
        if st.button("🔐 Accès Praticien", use_container_width=True, type="primary", key="go_prat"):
            st.session_state.mode = "praticien"; st.rerun()
    with c2:
        st.markdown("""<div style="background:linear-gradient(135deg,#0f766e,#0d5e56);border-radius:20px;padding:32px 28px;text-align:center;color:white;height:100%;">
            <div style="font-size:3rem;margin-bottom:12px;">👤</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.4rem;margin-bottom:8px;">Espace Patient</div>
            <div style="color:rgba(255,255,255,0.65);font-size:0.85rem;margin-bottom:20px;">Résultats · Observance · Pré-visite · Brosse connectée · Nutrition</div></div>""", unsafe_allow_html=True)
        if st.button("🔑 Accès Patient", use_container_width=True, key="go_pat"):
            if not st.session_state.rgpd_accepted:
                st.session_state.mode = "rgpd_patient"; st.rerun()
            else:
                st.session_state.mode = "patient"; st.rerun()
    with c3:
        st.markdown("""<div style="background:linear-gradient(135deg,#1e1b4b,#312e81);border-radius:20px;padding:32px 28px;text-align:center;color:white;height:100%;">
            <div style="font-size:3rem;margin-bottom:12px;">📖</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.4rem;margin-bottom:8px;">À propos</div>
            <div style="color:rgba(255,255,255,0.65);font-size:0.85rem;margin-bottom:20px;">OralBiome — Plateforme d'intelligence orale prédictive · RGPD compliant</div></div>""", unsafe_allow_html=True)
        if st.button("ℹ️ En savoir plus", use_container_width=True, key="go_about"):
            st.session_state.mode = "about"; st.rerun()
    st.markdown("---")
    feat = [
        ("📊","Benchmarking NHANES",f"Votre score comparé à n=8 237 patients · Percentiles par âge · Corrélations diabète, hypertension, mortalité"),
        ("🧬","Risques Systémiques","5 pathologies corrélées au microbiome oral : cardiovasculaire, diabète, Alzheimer, colorectal, respiratoire"),
        ("🦷","Twin Numérique FDI","Schéma 3D interactif · 32 dents éditables · Projection microbiome · Historique soins par dent"),
        ("📈","Score d'Observance","Questionnaire quotidien · Badge Champion/Décrochage · Prédiction microbiome · Alerte praticien automatique"),
        ("💊","Interactions Médicaments","7 classes médicamenteuses · Impacts microbiome · Probiotiques ciblés · Détection automatique"),
        ("🏥","Salle d'Attente Virtuelle","Pré-diagnostic IA avant visite · Anamnèse + photo pré-remplies · Gain de temps en consultation"),
        ("📱","Objets Connectés","Compatible Oral-B iO, Sonicare · Score hygiène · Impact sur microbiome · Conseils personnalisés"),
        ("🤖","IA Clinique (Claude)","Analyse photo dentaire · Pré-diagnostic complet · Recommandations personnalisées via Anthropic API"),
    ]
    fc = st.columns(4)
    for i, (icon, titre, desc) in enumerate(feat):
        fc[i%4].markdown(f"""<div style="background:white;border:1px solid #e5e7eb;border-radius:14px;padding:18px 16px;margin:6px 0;box-shadow:0 2px 8px rgba(0,0,0,0.04);height:100%;">
            <div style="font-size:1.6rem;margin-bottom:8px;">{icon}</div>
            <div style="font-weight:700;font-size:0.9rem;color:#1a3a5c;margin-bottom:6px;">{titre}</div>
            <div style="font-size:0.78rem;color:#6b7280;line-height:1.5;">{desc}</div></div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='text-align:center;padding:16px 0;'>", unsafe_allow_html=True)
    cl1, cl2, cl3 = st.columns([1,2,1])
    with cl2:
        render_lang_selector()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;font-size:0.78rem;color:#9ca3af;padding:8px;'>OralBiome · Conforme RGPD · Données chiffrées · Ne remplace pas l'avis médical</div>", unsafe_allow_html=True)


def render_about():
    st.markdown("""<div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:16px;padding:32px 40px;margin-bottom:28px;text-align:center;color:white;">
        <div style="font-size:2.5rem;margin-bottom:10px;">🦷</div>
        <h2 style="font-family:'DM Serif Display',serif;font-size:2rem;margin:0 0 8px 0;">OralBiome</h2>
        <p style="opacity:0.7;">Intelligence Microbiome Orale · Médecine Prédictive</p></div>""", unsafe_allow_html=True)
    c_about1, c_about2 = st.columns(2)
    with c_about1:
        st.markdown("""### 🎯 Mission
OralBiome transforme les données microbiomes orales en insights cliniques actionnables.

**Pour les praticiens** : Tableaux de bord intelligents, alertes précoces, twin numérique FDI, prédiction des risques systémiques.

**Pour les patients** : Accès à leur bilan en temps réel, observance gamifiée, brosse connectée, pré-visite facilitée.

### 🔬 Base Scientifique
- **NHANES 2009-2012** · n=8,237 patients · Vogtmann et al. Lancet Microbe 2022
- **Dominy et al. Science Advances 2019** — P. gingivalis et Alzheimer
- **AHA 2012** — Lien microbiome oral–cardiovasculaire
- **Castellarin et al. 2012** — Fusobacterium et colorectal
""")
    with c_about2:
        st.markdown("""### ⚙️ Technologies
- **Anthropic Claude** (claude-sonnet-4-20250514) — IA clinique
- **Streamlit** — Interface clinique professionnelle
- **ReportLab** — Génération PDF cliniques
- **Pandas** — Analyse données microbiome
- **SVG custom** — Twin numérique 3D

### 🔒 Sécurité & RGPD
- Données chiffrées en transit (HTTPS)
- Conformité UE 2016/679 (RGPD)
- Consentement explicite requis
- Droit d'accès, rectification, effacement

### 📬 Contact
contact@oralbiome.com · www.oralbiome.com
""")
    if st.button("← Retour à l'accueil", use_container_width=True, type="primary"):
        st.session_state.mode = "choix"; st.rerun()


# ══════════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════════
mode = st.session_state.get("mode","choix")

if mode == "choix":
    render_home()
elif mode == "about":
    render_about()
elif mode == "rgpd_patient":
    render_rgpd_banner()
    if st.session_state.get("rgpd_accepted"):
        st.session_state.mode = "patient"; st.rerun()
elif mode == "patient":
    render_portail_patient()
elif mode == "praticien":
    if not st.session_state.get("connecte"):
        if not st.session_state.get("rgpd_accepted"):
            render_rgpd_banner()
            if st.session_state.get("rgpd_accepted"): st.rerun()
        else:
            render_login_praticien()
    else:
        render_portail_praticien()