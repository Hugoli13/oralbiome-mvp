import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import io, base64, json, requests, os, hashlib

st.set_page_config(page_title="OralBiome", page_icon="🦷", layout="wide")
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")

# ── Logo ──────────────────────────────────────────────────
def _load_logo_b64(path="image_19.png"):
    if os.path.exists(path):
        with open(path,"rb") as f: return base64.b64encode(f.read()).decode()
    return ""
LOGO_B64 = _load_logo_b64()
def logo_img(width=400, style=""):
    if LOGO_B64: return f'<img src="data:image/png;base64,{LOGO_B64}" width="{width}" style="display:block;{style}" />'
    return '<span style="font-family:DM Serif Display,serif;font-size:1.4rem;color:#1a3a5c;">🦷 OralBiome</span>'

# ── I18N ──────────────────────────────────────────────────
I18N = {
    "fr":{"flag":"🇫🇷","lang_name":"Français","home_login":"Se connecter","home_access":"Accéder à mon espace","metric_caries":"Risque Carieux","metric_paro":"Risque Parodontal","metric_diversity":"Diversité Microbienne","metric_high":"Élevé","metric_low":"Faible","pat_hello":"Bonjour","pat_logout":"Se déconnecter","pat_back":"Retour accueil","pat_next_ctrl":"Prochain contrôle","pat_weeks":"semaines","pat_profile":"📊 Mon Profil","pat_systemic":"🧬 Risques Systémiques","pat_photo":"📸 Analyse Photo","pat_actions":"🚨 Mes Actions","pat_nutrition":"🥗 Nutrition & Probiotiques","pat_anamnes":"📋 Mon Anamnèse","pat_share":"📤 Partager","pat_twin":"🦷 Mon Twin Dentaire","pat_pdf":"📥 Rapport PDF","prat_connect":"Se connecter","prat_back":"Retour à l'accueil","prat_disconnect":"Déconnecter","prat_email":"Email Professionnel","prat_password":"Mot de passe","prat_login_title":"Portail Praticien","dash_title":"Dashboard Cabinet","dash_total":"Patients Total","dash_alerts":"En Alerte","dash_stable":"Stables","dash_cardio":"Risque Cardio Élevé","dash_neuro":"Risque Neuro Élevé","notif_empty":"Aucune notification","notif_mark_read":"Tout marquer comme lu","dm_on":"🌙 Mode sombre","dm_off":"☀️ Mode clair"},
    "en":{"flag":"🇬🇧","lang_name":"English","home_login":"Log in","home_access":"Access my space","metric_caries":"Caries Risk","metric_paro":"Periodontal Risk","metric_diversity":"Microbial Diversity","metric_high":"High","metric_low":"Low","pat_hello":"Hello","pat_logout":"Log out","pat_back":"Back to home","pat_next_ctrl":"Next check-up","pat_weeks":"weeks","pat_profile":"📊 My Profile","pat_systemic":"🧬 Systemic Risks","pat_photo":"📸 Photo Analysis","pat_actions":"🚨 My Actions","pat_nutrition":"🥗 Nutrition & Probiotics","pat_anamnes":"📋 My Anamnesis","pat_share":"📤 Share","pat_twin":"🦷 My Dental Twin","pat_pdf":"📥 PDF Report","prat_connect":"Log in","prat_back":"Back to home","prat_disconnect":"Log out","prat_email":"Professional Email","prat_password":"Password","prat_login_title":"Practitioner Portal","dash_title":"Cabinet Dashboard","dash_total":"Total Patients","dash_alerts":"Alerts","dash_stable":"Stable","dash_cardio":"High Cardio Risk","dash_neuro":"High Neuro Risk","notif_empty":"No notifications","notif_mark_read":"Mark all as read","dm_on":"🌙 Dark mode","dm_off":"☀️ Light mode"},
    "nl":{"flag":"🇧🇪","lang_name":"Nederlands","home_login":"Inloggen","home_access":"Toegang tot mijn ruimte","metric_caries":"Cariësrisico","metric_paro":"Parodontaal Risico","metric_diversity":"Microbiële Diversiteit","metric_high":"Hoog","metric_low":"Laag","pat_hello":"Hallo","pat_logout":"Uitloggen","pat_back":"Terug naar home","pat_next_ctrl":"Volgende controle","pat_weeks":"weken","pat_profile":"📊 Mijn Profiel","pat_systemic":"🧬 Systemische Risico's","pat_photo":"📸 Foto Analyse","pat_actions":"🚨 Mijn Acties","pat_nutrition":"🥗 Voeding & Probiotica","pat_anamnes":"📋 Mijn Anamnese","pat_share":"📤 Delen","pat_twin":"🦷 Mijn Tand Twin","pat_pdf":"📥 PDF Rapport","prat_connect":"Inloggen","prat_back":"Terug naar home","prat_disconnect":"Uitloggen","prat_email":"Professioneel E-mail","prat_password":"Wachtwoord","prat_login_title":"Practitioner Portaal","dash_title":"Kabinet Dashboard","dash_total":"Totaal Patiënten","dash_alerts":"Meldingen","dash_stable":"Stabiel","dash_cardio":"Hoog Cardio Risico","dash_neuro":"Hoog Neuro Risico","notif_empty":"Geen meldingen","notif_mark_read":"Alles als gelezen markeren","dm_on":"🌙 Donkere modus","dm_off":"☀️ Lichte modus"},
}
def t(key):
    return I18N.get(st.session_state.get("lang","fr"), I18N["fr"]).get(key, key)
def render_lang_selector():
    langs = {f"{I18N[k]['flag']} {I18N[k]['lang_name']}": k for k in I18N}
    current = st.session_state.get("lang","fr")
    cur_label = next(lbl for lbl,k in langs.items() if k==current)
    chosen = st.sidebar.selectbox("🌐", list(langs.keys()), index=list(langs.keys()).index(cur_label), label_visibility="collapsed")
    if langs[chosen] != current:
        st.session_state.lang = langs[chosen]; st.rerun()
def render_dark_mode_toggle():
    is_dark = st.session_state.get("dark_mode", False)
    if st.sidebar.button(t("dm_off") if is_dark else t("dm_on"), use_container_width=True, key="dm_toggle"):
        st.session_state.dark_mode = not is_dark; st.rerun()

# ── NHANES ────────────────────────────────────────────────
NHANES_PERCENTILES = {1:14.2,2:17.8,3:20.1,4:22.0,5:23.5,6:24.8,7:25.9,8:27.0,9:28.0,10:28.9,11:29.7,12:30.5,13:31.2,14:31.9,15:32.6,16:33.2,17:33.8,18:34.4,19:35.0,20:35.6,21:36.1,22:36.7,23:37.2,24:37.7,25:38.2,26:38.7,27:39.2,28:39.7,29:40.1,30:40.6,31:41.0,32:41.5,33:41.9,34:42.3,35:42.8,36:43.2,37:43.6,38:44.0,39:44.4,40:44.8,41:45.2,42:45.6,43:46.0,44:46.4,45:46.8,46:47.2,47:47.6,48:48.0,49:48.4,50:48.8,51:49.2,52:49.6,53:50.1,54:50.5,55:50.9,56:51.3,57:51.8,58:52.2,59:52.7,60:53.1,61:53.6,62:54.1,63:54.5,64:55.0,65:55.5,66:56.0,67:56.5,68:57.1,69:57.6,70:58.2,71:58.8,72:59.4,73:60.0,74:60.6,75:61.3,76:62.0,77:62.7,78:63.4,79:64.2,80:65.0,81:65.8,82:66.7,83:67.6,84:68.5,85:69.5,86:70.5,87:71.6,88:72.7,89:73.9,90:75.2,91:76.5,92:77.9,93:79.4,94:81.0,95:82.7,96:84.6,97:86.7,98:89.2,99:93.1}
NHANES_BY_AGE = {"18-29":{"p25":41.5,"p50":52.1,"p75":63.8,"p85":71.2},"30-39":{"p25":40.2,"p50":51.0,"p75":62.5,"p85":70.1},"40-49":{"p25":38.8,"p50":49.4,"p75":61.0,"p85":68.7},"50-59":{"p25":37.1,"p50":47.6,"p75":59.2,"p85":67.0},"60-69":{"p25":35.5,"p50":45.8,"p75":57.4,"p85":65.2},"70+":{"p25":33.2,"p50":43.5,"p75":55.1,"p85":63.0}}
NHANES_CLINICAL = {"diabete":{"mean_sain":51.3,"mean_malade":44.7,"difference":6.6,"p_value":0.0001},"hypertension":{"mean_sain":50.8,"mean_malade":46.2,"difference":4.6,"p_value":0.0008},"inflammation":{"mean_sain":51.1,"mean_malade":45.9,"difference":5.2,"p_value":0.0003},"mortalite":{"hazard_ratio":0.63,"ci_95":"(0.49–0.82)","interpretation":"Chaque hausse de diversité réduit le risque de mortalité de 37% (HR=0.63)"}}

def nhanes_percentile_rank(score, age=None):
    pct=1
    for p in range(99,0,-1):
        if score>=NHANES_PERCENTILES[p]: pct=p; break
    if score>=69.5: niveau,nlabel,ncolor="excellent","Excellent 🌟","#16a34a"
    elif score>=61.3: niveau,nlabel,ncolor="bon","Bon 👍","#2563eb"
    elif score>=38.2: niveau,nlabel,ncolor="modere","Modéré ⚠️","#d97706"
    else: niveau,nlabel,ncolor="faible","Faible 🔴","#e11d48"
    bg=f"Meilleur que **{pct}%** de la population générale"
    ag=pa=nm=dm=ba=None
    if age is not None:
        if age<30: ag="18-29"
        elif age<40: ag="30-39"
        elif age<50: ag="40-49"
        elif age<60: ag="50-59"
        elif age<70: ag="60-69"
        else: ag="70+"
        a=NHANES_BY_AGE[ag]; nm=a["p50"]; dm=round(score-nm,1)
        if score>=a["p85"]: pa=85
        elif score>=a["p75"]: pa=75
        elif score>=a["p50"]: pa=50
        elif score>=a["p25"]: pa=25
        else: pa=10
        ds=f"+{dm}" if dm>=0 else str(dm)
        ba=f"Meilleur que **{pa}%** des {ag} ans ({ds} pts vs médiane)"
    return {"percentile_global":pct,"percentile_age":pa,"benchmark_global":bg,"benchmark_age":ba,"niveau":niveau,"niveau_label":nlabel,"niveau_color":ncolor,"age_group":ag,"nhanes_n":8237,"source":"NHANES 2009-2012 · Vogtmann et al. Lancet Microbe 2022"}

def render_diversity_benchmark(diversite, age=None, context="patient"):
    bm=nhanes_percentile_rank(diversite,age); c=bm["niveau_color"]; pct=bm["percentile_global"]
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
    bh='<div style="display:flex;border-radius:8px;overflow:hidden;height:12px;margin:8px 0 2px 0;">'
    for w,bg in [(25,"#fee2e2"),(25,"#fef3c7"),(25,"#dbeafe"),(15,"#dcfce7"),(10,"#bbf7d0")]:
        bh+=f'<div style="flex:{w};background:{bg};border-right:1px solid white;"></div>'
    bh+=f'</div><div style="position:relative;height:20px;"><div style="position:absolute;left:{pct}%;transform:translateX(-50%);">'
    bh+=f'<div style="width:3px;height:12px;background:{c};margin:0 auto;"></div>'
    bh+=f'<div style="font-size:0.7rem;font-weight:700;color:{c};white-space:nowrap;transform:translateX(-40%);">P{pct} — vous</div></div></div>'
    st.markdown(bh,unsafe_allow_html=True)
    lc=st.columns(5)
    for col,(lbl,cc) in zip(lc,[("< P25\nFaible","#e11d48"),("P25–50\nModéré","#d97706"),("P50–75\nBon","#2563eb"),("P75–85\nExcellent","#16a34a"),("> P90\nTop 10%","#15803d")]):
        col.markdown(f"<div style='text-align:center;font-size:0.68rem;color:{cc};font-weight:600;line-height:1.3;'>{lbl}</div>",unsafe_allow_html=True)
    if context=="praticien":
        st.markdown("---"); st.markdown("##### 📊 Corrélations cliniques — NHANES 2009-2012 (n=8 237)")
        c1,c2,c3=st.columns(3)
        for col,(key,label,icon) in zip([c1,c2,c3],[("diabete","Diabète","🩸"),("hypertension","Hypertension","❤️"),("inflammation","Inflammation","🔥")]):
            d=NHANES_CLINICAL[key]
            col.markdown(f"""<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:12px;text-align:center;">
            <div style="font-size:1.2rem;">{icon}</div><div style="font-weight:600;font-size:0.85rem;margin:4px 0;">{label}</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.4rem;color:#e11d48;">−{d['difference']} pts</div>
            <div style="font-size:0.72rem;color:#6b7280;">sains: {d['mean_sain']} vs malades: {d['mean_malade']}</div>
            <div style="font-size:0.7rem;color:#16a34a;margin-top:4px;font-weight:600;">p={d['p_value']}</div></div>""",unsafe_allow_html=True)
        mort=NHANES_CLINICAL["mortalite"]
        st.markdown(f"""<div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:1px solid #16a34a40;border-radius:10px;padding:12px 16px;margin-top:8px;">
        <b>💚 Mortalité toutes causes</b> — HR={mort['hazard_ratio']} {mort['ci_95']}<br>
        <span style="font-size:0.85rem;color:#374151;">{mort['interpretation']}</span></div>""",unsafe_allow_html=True)

# ── CSS ───────────────────────────────────────────────────
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
.finding-alert{background:#fee2e2;color:#991b1b;} .finding-warn{background:#fef3c7;color:#92400e;} .finding-ok{background:#dcfce7;color:#166534;}
.pill-green{display:inline-block;background:#d1fae5;border-radius:20px;padding:5px 14px;margin:3px;font-size:13px;color:#065f46;font-weight:500;}
.pill-red{display:inline-block;background:#fee2e2;border-radius:20px;padding:5px 14px;margin:3px;font-size:13px;color:#991b1b;font-weight:500;}
.reco-card{padding:14px 18px;border-radius:8px;margin:8px 0;}
.reco-red{background:#fff5f5;border-left:4px solid #dc3545;} .reco-orange{background:#fff8f0;border-left:4px solid #fd7e14;} .reco-green{background:#f0fff4;border-left:4px solid #28a745;}
.patient-header{background:linear-gradient(135deg,#1a3a5c,#2563eb);color:white;padding:24px;border-radius:12px;margin-bottom:20px;}
.kpi-card{background:#fff;border-radius:16px;padding:22px 24px;border:1px solid #e5e7eb;box-shadow:0 2px 12px rgba(0,0,0,0.06);}
.kpi-num{font-family:'DM Serif Display',serif;font-size:2.4rem;line-height:1;}
.kpi-lbl{font-size:0.82rem;color:#6b7280;margin-top:4px;font-weight:500;text-transform:uppercase;letter-spacing:0.04em;}
.kpi-delta{font-size:0.8rem;margin-top:6px;font-weight:600;}
.kpi-red{color:#e11d48;} .kpi-green{color:#16a34a;} .kpi-blue{color:#2563eb;} .kpi-amber{color:#d97706;}
.alert-card{background:#fff;border-radius:12px;padding:16px 20px;margin:8px 0;border:1px solid #fee2e2;border-left:5px solid #e11d48;display:flex;align-items:flex-start;gap:14px;}
.alert-card.warn{border-color:#fef3c7;border-left-color:#d97706;} .alert-card.info{border-color:#dbeafe;border-left-color:#2563eb;}
.alert-icon{font-size:1.5rem;flex-shrink:0;margin-top:2px;} .alert-body{flex:1;}
.alert-title{font-weight:600;font-size:0.95rem;color:#111827;margin:0 0 3px 0;}
.alert-desc{font-size:0.85rem;color:#6b7280;margin:0;} .alert-meta{font-size:0.75rem;color:#9ca3af;margin-top:5px;}
.progress-bar-wrap{background:#f1f5f9;border-radius:8px;height:10px;overflow:hidden;margin:6px 0;}
.progress-bar-fill{height:100%;border-radius:8px;}
</style>""", unsafe_allow_html=True)

# ── SCORES SYSTÉMIQUES ────────────────────────────────────
SYSTEMIC_CORRELATIONS = {
    "cardiovasculaire":{"icon":"❤️","label":"Risque Cardiovasculaire","description":"P. gingivalis et T. forsythia libèrent des endotoxines favorisant l'athérosclérose.","references":"Herzberg & Meyer 1996 · AHA 2012","weight_gingivalis":0.45,"weight_mutans":0.10,"weight_diversity":0.30,"weight_inflammation":0.15,"thresholds":{"low":25,"high":55},"actions_high":["Consultation cardiologique recommandée","Bilan CRP ultrasensible","Traitement parodontal — réduit risque CV 20%","Alimentation anti-inflammatoire"],"actions_low":["Maintenir hygiène parodontale","Contrôle microbiome 6 mois"]},
    "diabete":{"icon":"🩸","label":"Risque Diabète / Résistance Insuline","description":"Dysbiose orale entretenant inflammation chronique dégradant la sensibilité à l'insuline.","references":"Taylor et al. 2013 · Lancet 2020","weight_gingivalis":0.35,"weight_mutans":0.20,"weight_diversity":0.35,"weight_inflammation":0.10,"thresholds":{"low":25,"high":55},"actions_high":["Bilan glycémie à jeun et HbA1c","Réduction sucres rapides","Traitement paro : réduit HbA1c 0.4%","Exercice 150 min/semaine"],"actions_low":["Limiter sucres raffinés","Contrôle glycémie si antécédents"]},
    "alzheimer":{"icon":"🧠","label":"Risque Neurodégénératif (Alzheimer)","description":"P. gingivalis retrouvée dans le cerveau Alzheimer. Gingipaines favorisant les plaques amyloïdes.","references":"Dominy et al. Science Advances 2019","weight_gingivalis":0.60,"weight_mutans":0.05,"weight_diversity":0.25,"weight_inflammation":0.10,"thresholds":{"low":20,"high":50},"actions_high":["Élimination P. gingivalis — priorité absolue","Oméga-3 DHA 1g/jour","Activité physique aérobie","Suivi neurologique si > 60 ans"],"actions_low":["Maintenir microbiome diversifié","Alimentation méditerranéenne"]},
    "colon":{"icon":"🦠","label":"Risque Colorectal","description":"Fusobacterium nucleatum retrouvé dans les tumeurs colorectales.","references":"Castellarin et al. 2012 · Rubinstein et al. 2013","weight_gingivalis":0.25,"weight_mutans":0.10,"weight_diversity":0.50,"weight_inflammation":0.15,"thresholds":{"low":20,"high":45},"actions_high":["Coloscopie si > 45 ans","Fibres prébiotiques 30g/jour","Réduire viande rouge transformée","Probiotiques intestinaux"],"actions_low":["Alimentation riche en fibres","Dépistage selon l'âge"]},
    "respiratoire":{"icon":"🫁","label":"Risque Respiratoire / Pneumonie","description":"Bactéries orales aspirées colonisant les voies respiratoires. Risque ×4 en dysbiose.","references":"Scannapieco et al. 2003 · ADA 2021","weight_gingivalis":0.30,"weight_mutans":0.15,"weight_diversity":0.40,"weight_inflammation":0.15,"thresholds":{"low":25,"high":50},"actions_high":["Hygiène orale renforcée","Brossage langue matin et soir (−70% bactéries)","Consultation pneumologique si toux chronique"],"actions_low":["Hygiène bucco-dentaire régulière","Brossage de la langue quotidien"]}
}
def calculer_score_systemique(sm,pg,div):
    sg=min(100,(pg/2.0)*100); smu=min(100,(sm/8.0)*100); sd=max(0,100-div); si=min(100,sg*0.6+sd*0.4)
    results={}
    for key,corr in SYSTEMIC_CORRELATIONS.items():
        raw=corr["weight_gingivalis"]*sg+corr["weight_mutans"]*smu+corr["weight_diversity"]*sd+corr["weight_inflammation"]*si
        score=round(min(100,max(0,raw))); level="low" if score<corr["thresholds"]["low"] else "high" if score>corr["thresholds"]["high"] else "med"
        results[key]={**corr,"score":score,"level":level,"actions":corr["actions_high"] if level=="high" else corr["actions_low"]}
    return dict(sorted(results.items(),key=lambda x:-x[1]["score"]))

# ── ANAMNÈSE ──────────────────────────────────────────────
def get_anamnes(nom): return st.session_state.anamnes.get(nom,{})
def save_anamnes(nom,data): data["completed_at"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S"); st.session_state.anamnes[nom]=data

# ── NOTIFICATIONS ─────────────────────────────────────────
def generer_notifications(patients):
    notifs=[]; today=date.today()
    for nom,p in patients.items():
        hist=p["historique"]
        if not hist.empty:
            try:
                ld=datetime.strptime(hist.iloc[-1]["Date"],"%d/%m/%Y").date()
                ea=p["s_mutans"]>3 or p["p_gingivalis"]>0.5 or p["diversite"]<50
                dl=8 if p["p_gingivalis"]>1.5 or p["s_mutans"]>6 else 12 if ea else 24
                retard=(today-(ld+timedelta(weeks=dl))).days
                if retard>0: notifs.append({"id":f"ctrl_{nom}","type":"urgent","icon":"⏰","titre":nom,"message":f"Contrôle en retard de {retard} jours","action":nom,"read":False})
            except: pass
        if p["p_gingivalis"]>1.5: notifs.append({"id":f"pg_{nom}","type":"urgent","icon":"🚨","titre":nom,"message":f"P. gingivalis critique : {p['p_gingivalis']}%","action":nom,"read":False})
        elif p["s_mutans"]>6.0: notifs.append({"id":f"sm_{nom}","type":"warn","icon":"⚠️","titre":nom,"message":f"S. mutans très élevé : {p['s_mutans']}%","action":nom,"read":False})
    read_ids=st.session_state.get("notifs_read",set())
    for n in notifs:
        if n["id"] in read_ids: n["read"]=True
    return sorted(notifs,key=lambda x:(x["read"],x["type"]!="urgent"))
def render_notifications(patients):
    notifs=generer_notifications(patients); unread=sum(1 for n in notifs if not n["read"])
    badge=f'<span style="background:#e11d48;color:white;border-radius:10px;padding:1px 7px;font-size:0.72rem;font-weight:700;margin-left:6px;">{unread}</span>' if unread>0 else ""
    st.sidebar.markdown(f"**🔔 Notifications**{badge}",unsafe_allow_html=True)
    with st.sidebar.expander(f"Voir ({len(notifs)})",expanded=unread>0):
        if not notifs: st.markdown(f"*✅ {t('notif_empty')}*")
        else:
            if st.button(t("notif_mark_read"),key="mark_all_read",use_container_width=True):
                st.session_state.notifs_read={n["id"] for n in notifs}; st.rerun()
            for n in notifs[:6]:
                bg="#fff1f2" if n["type"]=="urgent" and not n["read"] else "#fffbeb" if n["type"]=="warn" and not n["read"] else "#f8fafc"
                left="#e11d48" if n["type"]=="urgent" else "#d97706"; op="0.55" if n["read"] else "1"
                st.markdown(f'<div style="background:{bg};border-left:3px solid {left};border-radius:8px;padding:10px 12px;margin:6px 0;opacity:{op};"><div style="font-size:0.85rem;font-weight:600;">{n["icon"]} {n["titre"]}</div><div style="font-size:0.78rem;color:#6b7280;">{n["message"]}</div></div>',unsafe_allow_html=True)
                ca,cb=st.columns([3,1])
                with ca:
                    if st.button("Ouvrir →",key=f"no_{n['id']}",use_container_width=True): st.session_state.patient_sel=n["action"]; st.session_state.vue="dossier"; st.rerun()
                with cb:
                    if not n["read"]:
                        if st.button("✓",key=f"nr_{n['id']}",use_container_width=True):
                            if "notifs_read" not in st.session_state: st.session_state.notifs_read=set()
                            st.session_state.notifs_read.add(n["id"]); st.rerun()

# ── TWIN NUMÉRIQUE DENTAIRE ───────────────────────────────
DENTS_FDI = {
    11:{"nom":"Incisive centrale","quadrant":1,"type":"incisive"},12:{"nom":"Incisive latérale","quadrant":1,"type":"incisive"},13:{"nom":"Canine","quadrant":1,"type":"canine"},14:{"nom":"Prémolaire 1","quadrant":1,"type":"premolaire"},15:{"nom":"Prémolaire 2","quadrant":1,"type":"premolaire"},16:{"nom":"Molaire 1","quadrant":1,"type":"molaire"},17:{"nom":"Molaire 2","quadrant":1,"type":"molaire"},18:{"nom":"Sagesse","quadrant":1,"type":"sagesse"},
    21:{"nom":"Incisive centrale","quadrant":2,"type":"incisive"},22:{"nom":"Incisive latérale","quadrant":2,"type":"incisive"},23:{"nom":"Canine","quadrant":2,"type":"canine"},24:{"nom":"Prémolaire 1","quadrant":2,"type":"premolaire"},25:{"nom":"Prémolaire 2","quadrant":2,"type":"premolaire"},26:{"nom":"Molaire 1","quadrant":2,"type":"molaire"},27:{"nom":"Molaire 2","quadrant":2,"type":"molaire"},28:{"nom":"Sagesse","quadrant":2,"type":"sagesse"},
    31:{"nom":"Incisive centrale","quadrant":3,"type":"incisive"},32:{"nom":"Incisive latérale","quadrant":3,"type":"incisive"},33:{"nom":"Canine","quadrant":3,"type":"canine"},34:{"nom":"Prémolaire 1","quadrant":3,"type":"premolaire"},35:{"nom":"Prémolaire 2","quadrant":3,"type":"premolaire"},36:{"nom":"Molaire 1","quadrant":3,"type":"molaire"},37:{"nom":"Molaire 2","quadrant":3,"type":"molaire"},38:{"nom":"Sagesse","quadrant":3,"type":"sagesse"},
    41:{"nom":"Incisive centrale","quadrant":4,"type":"incisive"},42:{"nom":"Incisive latérale","quadrant":4,"type":"incisive"},43:{"nom":"Canine","quadrant":4,"type":"canine"},44:{"nom":"Prémolaire 1","quadrant":4,"type":"premolaire"},45:{"nom":"Prémolaire 2","quadrant":4,"type":"premolaire"},46:{"nom":"Molaire 1","quadrant":4,"type":"molaire"},47:{"nom":"Molaire 2","quadrant":4,"type":"molaire"},48:{"nom":"Sagesse","quadrant":4,"type":"sagesse"},
}
ETATS_DENT = {
    "saine":      {"label":"Saine",             "color":"#16a34a","icon":"✅","bg":"#f0fdf4"},
    "surveillance":{"label":"À surveiller",      "color":"#d97706","icon":"👁️","bg":"#fffbeb"},
    "carie":      {"label":"Carie",             "color":"#ef4444","icon":"🔴","bg":"#fef2f2"},
    "paro":       {"label":"Atteinte paro.",    "color":"#dc2626","icon":"🩸","bg":"#fff1f2"},
    "absente":    {"label":"Absente",           "color":"#94a3b8","icon":"⬜","bg":"#f8fafc"},
    "couronne":   {"label":"Couronne/Implant",  "color":"#7c3aed","icon":"👑","bg":"#f5f3ff"},
    "traitement": {"label":"En traitement",     "color":"#2563eb","icon":"🔧","bg":"#eff6ff"},
}
SOINS_TYPES = ["Détartrage","Soin carie","Extraction","Couronne","Implant","Traitement paro.","Surfaçage","Probiotiques locaux","Observation"]

def get_twin(pid):
    if "twins" not in st.session_state: st.session_state.twins={}
    if pid not in st.session_state.twins:
        td={"notes_generales":"","indice_plaque":0,"indice_saignement":0,"derniere_maj":"","dents":{}}
        for num in DENTS_FDI:
            td["dents"][str(num)]={"etat":"saine","risque_carie":0,"inflammation":0,"profondeur_poche":2,"soins":[],"notes":""}
        st.session_state.twins[pid]=td
    return st.session_state.twins[pid]
def save_twin(pid,twin):
    twin["derniere_maj"]=datetime.now().strftime("%d/%m/%Y %H:%M")
    st.session_state.twins[pid]=twin

def score_quadrant(twin,q):
    ds=[twin["dents"].get(str(n),{}) for n,info in DENTS_FDI.items() if info["quadrant"]==q]
    pb=sum(1 for d in ds if d.get("etat") in ["carie","paro","traitement"])
    return max(0,100-pb*20)

def dent_color(etat,risque,infl):
    if etat=="absente": return "#94a3b8"
    if etat in ["carie","paro"]: return ETATS_DENT[etat]["color"]
    if etat=="couronne": return "#7c3aed"
    if etat=="traitement": return "#2563eb"
    if etat=="surveillance": return "#d97706"
    r=max(risque,infl)
    if r>70: return "#ef4444"
    if r>40: return "#f59e0b"
    return "#16a34a"

def render_dent_svg(num, dent_data, selected=False):
    """Rendu 3D SVG d'une dent individuelle avec effets de profondeur."""
    info = DENTS_FDI.get(num,{})
    dtype = info.get("type","incisive")
    etat = dent_data.get("etat","saine")
    rc = dent_data.get("risque_carie",0)
    infl = dent_data.get("inflammation",0)
    soins = dent_data.get("soins",[])
    color = dent_color(etat,rc,infl)
    absent = etat=="absente"

    # Dimensions selon type
    W,H = {"molaire":(28,24),"premolaire":(22,22),"canine":(18,28),"incisive":(16,26),"sagesse":(22,20)}.get(dtype,(20,22))

    sel_glow = f'filter:drop-shadow(0 0 6px {color}aa);' if selected else ""
    sel_scale = "transform:scale(1.15) translateY(-2px);" if selected else ""

    svg = f'<svg width="{W+4}" height="{H+12}" viewBox="-2 -2 {W+4} {H+16}" style="{sel_glow}{sel_scale}transition:all 0.2s;">'

    if absent:
        svg += f'<ellipse cx="{W/2}" cy="{H/2}" rx="{W/2-1}" ry="{H/2-1}" fill="#e2e8f0" stroke="#94a3b8" stroke-width="1" stroke-dasharray="2,2"/>'
        svg += f'<text x="{W/2}" y="{H/2+3}" text-anchor="middle" font-size="7" fill="#94a3b8" font-family="monospace">{num}</text>'
    else:
        # Racines
        if dtype in ["molaire","premolaire"]:
            svg += f'<ellipse cx="{W*0.3}" cy="{H+7}" rx="4" ry="7" fill="{color}" opacity="0.3"/>'
            svg += f'<ellipse cx="{W*0.7}" cy="{H+7}" rx="4" ry="7" fill="{color}" opacity="0.3"/>'
            if dtype=="molaire":
                svg += f'<ellipse cx="{W/2}" cy="{H+8}" rx="3" ry="5" fill="{color}" opacity="0.2"/>'
        else:
            svg += f'<ellipse cx="{W/2}" cy="{H+8}" rx="4" ry="8" fill="{color}" opacity="0.3"/>'

        # Gencive (rose enflammée si inflammation élevée)
        gum_c = "#fda4af" if infl>60 else "#fecdd3" if infl>30 else "#fde8ec"
        svg += f'<ellipse cx="{W/2}" cy="{H-1}" rx="{W/2+1}" ry="5" fill="{gum_c}" opacity="0.5"/>'

        # Corps principal — ombre
        svg += f'<ellipse cx="{W/2+1}" cy="{H/2+1}" rx="{W/2-0.5}" ry="{H/2-0.5}" fill="rgba(0,0,0,0.25)"/>'

        # Corps principal
        if dtype in ["molaire","premolaire"]:
            r = 4 if dtype=="molaire" else 3
            svg += f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="{r}" fill="{color}"/>'
            # Sillons molaires
            if dtype=="molaire":
                svg += f'<line x1="{W/2}" y1="3" x2="{W/2}" y2="{H-3}" stroke="rgba(0,0,0,0.15)" stroke-width="1.5"/>'
                svg += f'<line x1="3" y1="{H/2}" x2="{W-3}" y2="{H/2}" stroke="rgba(0,0,0,0.15)" stroke-width="1.5"/>'
        elif dtype=="canine":
            svg += f'<path d="M{W/2},{1} L{W-1},{H*0.4} Q{W-1},{H-1} {W/2},{H-1} Q{1},{H-1} {1},{H*0.4} Z" fill="{color}"/>'
        else:
            svg += f'<ellipse cx="{W/2}" cy="{H/2}" rx="{W/2-1}" ry="{H/2-1}" fill="{color}"/>'

        # Reflet 3D (brillance haut-gauche)
        svg += f'<ellipse cx="{W*0.32}" cy="{H*0.28}" rx="{W*0.18}" ry="{H*0.2}" fill="white" opacity="0.3"/>'
        # Highlight supérieur
        svg += f'<ellipse cx="{W/2}" cy="{H*0.12}" rx="{W*0.25}" ry="{H*0.08}" fill="white" opacity="0.4"/>'
        # Ombre côté droit
        svg += f'<ellipse cx="{W*0.78}" cy="{H/2}" rx="{W*0.15}" ry="{H*0.4}" fill="rgba(0,0,0,0.15)"/>'

        # Numéro
        svg += f'<text x="{W/2}" y="{H/2+3}" text-anchor="middle" font-size="6.5" fill="white" font-family="monospace" font-weight="bold" opacity="0.95">{num}</text>'

        # Badge risque carieux (coin haut-droit)
        if rc>40:
            rc_c="#dc2626" if rc>70 else "#f59e0b"
            svg += f'<circle cx="{W-2}" cy="2" r="4" fill="{rc_c}" stroke="white" stroke-width="0.8"/>'

        # Badge inflammation (coin haut-gauche)
        if infl>40:
            in_c="#dc2626" if infl>70 else "#f97316"
            svg += f'<circle cx="2" cy="2" r="4" fill="{in_c}" stroke="white" stroke-width="0.8"/>'

        # Badge soins (coin bas-droit)
        if soins:
            svg += f'<circle cx="{W-2}" cy="{H-2}" r="3.5" fill="#6366f1" stroke="white" stroke-width="0.7"/>'

    svg += '</svg>'
    return svg

def render_arch_svg(twin, quadrant_top, quadrant_bot, is_praticien=True, selected_num=None):
    """Rendu SVG de l'arc dentaire complet (vue occlusale 3D)."""
    # Arc maxillaire (quadrants 1+2) ou mandibulaire (3+4)
    top_nums = ([18,17,16,15,14,13,12,11] + [21,22,23,24,25,26,27,28])
    bot_nums = ([48,47,46,45,44,43,42,41] + [31,32,33,34,35,36,37,38])

    W,H = 700, 200
    svg_parts=[f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:700px;">']

    # Fond arc gencival
    svg_parts.append(f'''
    <defs>
        <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#f0f4ff" stop-opacity="0.8"/>
            <stop offset="100%" stop-color="#e8edf8" stop-opacity="0.4"/>
        </radialGradient>
    </defs>
    <ellipse cx="{W/2}" cy="{H/2}" rx="{W/2-10}" ry="{H/2-10}" fill="url(#bgGrad)" stroke="#dbeafe" stroke-width="0.5"/>
    ''')

    # Ligne médiane
    svg_parts.append(f'<line x1="{W/2}" y1="5" x2="{W/2}" y2="{H-5}" stroke="#cbd5e1" stroke-width="0.8" stroke-dasharray="3,3" opacity="0.6"/>')

    # ── Positionnement arc ── chaque dent placée sur une ellipse
    def arch_positions(nums, row="top"):
        positions = {}
        n = len(nums)
        for i, num in enumerate(nums):
            t = i / (n-1)
            rx = W/2 - 55
            ry = H/2 - 25
            cx = W/2 + rx * (-1 + 2*t) * 0.95
            if row == "top":
                cy = max(20, min(H-20, H/2 - 60 + 120*abs(0.5-t)*1.6))
            else:
                cy = max(20, min(H-20, H/2 + 60 - 120*abs(0.5-t)*1.6))
            positions[num] = (cx, cy)
        return positions

    positions_top = arch_positions(top_nums)
    positions_bot = arch_positions(bot_nums, "bot")

    # Dessiner les dents de l'arc supérieur
    for i, num in enumerate(top_nums):
        cx, cy = positions_top[num]
        d = twin["dents"].get(str(num), {"etat":"saine"})
        color = dent_color(d.get("etat","saine"), d.get("risque_carie",0), d.get("inflammation",0))
        info = DENTS_FDI.get(num,{}); dtype = info.get("type","incisive")
        W2,H2 = {"molaire":(26,20),"premolaire":(20,18),"canine":(16,22),"incisive":(14,20),"sagesse":(20,17)}.get(dtype,(18,18))
        absent = d.get("etat")=="absente"
        sel = (num==selected_num)
        glow = f'filter:drop-shadow(0 0 5px {color}99);' if sel else ""

        if absent:
            svg_parts.append(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{W2/2:.0f}" ry="{H2/2:.0f}" fill="#e2e8f0" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="2,2" opacity="0.5"/>')
        else:
            # Ombre
            svg_parts.append(f'<ellipse cx="{cx+1:.0f}" cy="{cy+1:.0f}" rx="{W2/2:.0f}" ry="{H2/2:.0f}" fill="rgba(0,0,0,0.2)"/>')
            # Corps
            if dtype in ["molaire","premolaire"]:
                rx2,ry2=W2/2-1,H2/2-1
                svg_parts.append(f'<rect x="{cx-rx2:.0f}" y="{cy-ry2:.0f}" width="{W2-2}" height="{H2-2}" rx="4" fill="{color}"/>')
                if dtype=="molaire":
                    svg_parts.append(f'<line x1="{cx:.0f}" y1="{cy-ry2+2:.0f}" x2="{cx:.0f}" y2="{cy+ry2-2:.0f}" stroke="rgba(0,0,0,0.12)" stroke-width="1.2"/>')
                    svg_parts.append(f'<line x1="{cx-rx2+2:.0f}" y1="{cy:.0f}" x2="{cx+rx2-2:.0f}" y2="{cy:.0f}" stroke="rgba(0,0,0,0.12)" stroke-width="1.2"/>')
            elif dtype=="canine":
                svg_parts.append(f'<ellipse cx="{cx:.0f}" cy="{cy+2:.0f}" rx="{W2/2-1:.0f}" ry="{H2/2-1:.0f}" fill="{color}"/>')
                svg_parts.append(f'<ellipse cx="{cx:.0f}" cy="{cy-H2/2+1:.0f}" rx="3" ry="4" fill="{color}"/>')
            else:
                svg_parts.append(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{W2/2-1:.0f}" ry="{H2/2-1:.0f}" fill="{color}"/>')
            # Reflet
            svg_parts.append(f'<ellipse cx="{cx-W2*0.18:.0f}" cy="{cy-H2*0.22:.0f}" rx="{W2*0.2:.0f}" ry="{H2*0.18:.0f}" fill="white" opacity="0.28"/>')
        # Numéro
        if is_praticien:
            svg_parts.append(f'<text x="{cx:.0f}" y="{cy+3:.0f}" text-anchor="middle" font-size="6" fill="white" font-family="monospace" font-weight="bold" opacity="0.9">{num}</text>')
        # Badges
        rc=d.get("risque_carie",0); infl=d.get("inflammation",0)
        if rc>40 and not absent:
            rc_c="#dc2626" if rc>70 else "#f59e0b"
            svg_parts.append(f'<circle cx="{cx+W2/2-1:.0f}" cy="{cy-H2/2+1:.0f}" r="4" fill="{rc_c}" stroke="white" stroke-width="0.7"/>')
        if infl>40 and not absent:
            in_c="#dc2626" if infl>70 else "#f97316"
            svg_parts.append(f'<circle cx="{cx-W2/2+1:.0f}" cy="{cy-H2/2+1:.0f}" r="4" fill="{in_c}" stroke="white" stroke-width="0.7"/>')
        if d.get("soins") and not absent:
            svg_parts.append(f'<circle cx="{cx+W2/2-1:.0f}" cy="{cy+H2/2-1:.0f}" r="3.5" fill="#6366f1" stroke="white" stroke-width="0.6"/>')

    # Labels quadrants
    svg_parts.append(f'<text x="120" y="12" font-size="7" fill="#94a3b8" text-anchor="middle" font-weight="600">Q1 — HAUT DROITE</text>')
    svg_parts.append(f'<text x="580" y="12" font-size="7" fill="#94a3b8" text-anchor="middle" font-weight="600">Q2 — HAUT GAUCHE</text>')
    svg_parts.append(f'</svg>')
    return "".join(svg_parts)

def render_twin_complet(twin, sm, pg, mode="praticien", pid=""):
    """Rendu HTML complet du twin numérique avec les deux arcs."""

    # ── Scores quadrants ──
    q_scores = {q: score_quadrant(twin,q) for q in [1,2,3,4]}
    score_global = round(sum(q_scores.values())/4)
    sc = "#16a34a" if score_global>=80 else "#d97706" if score_global>=60 else "#e11d48"
    q_labels = {1:"Haut Droite",2:"Haut Gauche",3:"Bas Gauche",4:"Bas Droite"}
    q_icons  = {1:"↗️",2:"↖️",3:"↙️",4:"↘️"}

    # Scores bar
    cols_q = st.columns(4)
    for i,(q,col) in enumerate(zip([1,2,3,4], cols_q)):
        qs=q_scores[q]; qc="#16a34a" if qs>=80 else "#d97706" if qs>=50 else "#e11d48"
        col.markdown(f"""<div style="background:#fff;border:1.5px solid {qc}30;border-radius:12px;padding:12px 8px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
            <div style="font-size:0.7rem;color:#6b7280;font-weight:700;margin-bottom:3px;">{q_icons[q]} {q_labels[q]}</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:{qc};line-height:1;">{qs}</div>
            <div style="font-size:0.68rem;color:#9ca3af;">/100</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Arc maxillaire ──
    st.markdown("##### 🦷 Arcade Maxillaire — Q1 · Q2 (Haut)")
    svg_top = render_arch_svg(twin, 1, 2, mode=="praticien", None)
    st.markdown(f'<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:16px;padding:12px;text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.06);">{svg_top}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Arc mandibulaire ──
    st.markdown("##### 🦷 Arcade Mandibulaire — Q3 · Q4 (Bas)")
    svg_bot = render_arch_svg(twin, 3, 4, mode=="praticien", None)
    st.markdown(f'<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:16px;padding:12px;text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.06);">{svg_bot}</div>', unsafe_allow_html=True)

    # ── Légende ──
    st.markdown("<br>", unsafe_allow_html=True)
    leg_cols = st.columns(7)
    for col,(key,info) in zip(leg_cols, list(ETATS_DENT.items())[:7]):
        col.markdown(f'<div style="display:flex;align-items:center;gap:4px;font-size:0.7rem;"><div style="width:10px;height:10px;border-radius:2px;background:{info["color"]};flex-shrink:0;"></div><span style="color:#374151;">{info["label"]}</span></div>', unsafe_allow_html=True)

    # ── Indicateurs microbiome ──
    st.markdown("---")
    st.markdown("#### 🧬 Corrélation Microbiome → Twin")
    mi1,mi2,mi3 = st.columns(3)
    sm_c="#e11d48" if sm>3 else "#d97706" if sm>1.5 else "#16a34a"
    pg_c="#e11d48" if pg>0.5 else "#d97706" if pg>0.2 else "#16a34a"
    nb_rc  = sum(1 for d in twin["dents"].values() if d.get("risque_carie",0)>50)
    nb_inf = sum(1 for d in twin["dents"].values() if d.get("inflammation",0)>50)
    nb_pb  = sum(1 for d in twin["dents"].values() if d.get("etat") in ["carie","paro"])
    with mi1:
        st.markdown(f"""<div style="background:#fff;border:1px solid {sm_c}30;border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:0.72rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin-bottom:4px;">S. mutans → Caries</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:{sm_c};">{sm}%</div>
            <div style="font-size:0.8rem;color:#374151;margin-top:6px;">Dents à risque élevé : <b style="color:{sm_c};">{nb_rc}</b></div>
            <div style="background:{sm_c}15;border-radius:6px;padding:3px 8px;margin-top:8px;font-size:0.72rem;color:{sm_c};">
            {"🔴 Risque élevé" if sm>3 else "🟡 Modéré" if sm>1.5 else "🟢 Faible"}</div>
        </div>""", unsafe_allow_html=True)
    with mi2:
        st.markdown(f"""<div style="background:#fff;border:1px solid {pg_c}30;border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:0.72rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin-bottom:4px;">P. gingivalis → Paro</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:{pg_c};">{pg}%</div>
            <div style="font-size:0.8rem;color:#374151;margin-top:6px;">Zones enflammées : <b style="color:{pg_c};">{nb_inf}</b></div>
            <div style="background:{pg_c}15;border-radius:6px;padding:3px 8px;margin-top:8px;font-size:0.72rem;color:{pg_c};">
            {"🔴 Atteinte probable" if pg>0.5 else "🟡 Surveillance" if pg>0.2 else "🟢 Protectrice"}</div>
        </div>""", unsafe_allow_html=True)
    with mi3:
        st.markdown(f"""<div style="background:#fff;border:1px solid {sc}30;border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:0.72rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin-bottom:4px;">Score Twin Global</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:{sc};">{score_global}/100</div>
            <div style="font-size:0.8rem;color:#374151;margin-top:6px;">Interventions requises : <b style="color:{sc};">{nb_pb}</b></div>
            <div style="background:{sc}15;border-radius:6px;padding:3px 8px;margin-top:8px;font-size:0.72rem;color:{sc};">
            {"✅ Bonne santé" if score_global>=80 else "⚠️ Surveillance" if score_global>=60 else "🔴 Soins recommandés"}</div>
        </div>""", unsafe_allow_html=True)


def render_twin_edition(twin, pid):
    """Panneau d'édition dent par dent pour le praticien."""
    st.markdown("---")
    st.markdown("#### ✏️ Éditer une Dent")

    # Sélection dent
    options = {f"Dent {n} — {info['nom']} (Q{info['quadrant']})": n for n,info in DENTS_FDI.items()}
    sel_label = st.selectbox("Sélectionner une dent", list(options.keys()), key=f"sel_dent_{pid}")
    sel_num = options[sel_label]
    sel_str = str(sel_num)
    dent_data = twin["dents"].get(sel_str, {"etat":"saine","risque_carie":0,"inflammation":0,"profondeur_poche":2,"soins":[],"notes":""})
    etat_act = dent_data.get("etat","saine")
    etat_info = ETATS_DENT.get(etat_act, ETATS_DENT["saine"])

    col_form, col_preview = st.columns([3,1])
    with col_form:
        # Header dent
        st.markdown(f"""<div style="background:{etat_info['bg']};border:2px solid {etat_info['color']}40;border-radius:12px;padding:14px 18px;margin-bottom:14px;display:flex;align-items:center;gap:12px;">
            <div style="background:{etat_info['color']};color:white;width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:800;font-family:monospace;font-size:1rem;">{sel_num}</div>
            <div><div style="font-weight:700;font-size:0.95rem;">{DENTS_FDI[sel_num]['nom']} — {DENTS_FDI[sel_num]['type'].capitalize()}</div>
            <div style="font-size:0.78rem;color:#6b7280;">Q{DENTS_FDI[sel_num]['quadrant']} — {['','Haut Droite','Haut Gauche','Bas Gauche','Bas Droite'][DENTS_FDI[sel_num]['quadrant']]}</div></div>
            <span style="margin-left:auto;background:{etat_info['color']}20;color:{etat_info['color']};padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;">{etat_info['icon']} {etat_info['label']}</span>
        </div>""", unsafe_allow_html=True)

        with st.form(f"form_dent_{pid}_{sel_num}"):
            fa,fb = st.columns(2)
            with fa:
                nouveau_etat = st.selectbox("État clinique", list(ETATS_DENT.keys()),
                    index=list(ETATS_DENT.keys()).index(etat_act),
                    format_func=lambda x: f"{ETATS_DENT[x]['icon']} {ETATS_DENT[x]['label']}")
                rc_val = st.slider("🦠 Risque Carieux (S. mutans)", 0, 100, int(dent_data.get("risque_carie",0)))
            with fb:
                infl_val = st.slider("🩸 Inflammation Gingivale (P. gingivalis)", 0, 100, int(dent_data.get("inflammation",0)))
                poche_val = st.slider("📏 Profondeur de poche (mm)", 1, 12, int(dent_data.get("profondeur_poche",2)))

            soins_val = st.multiselect("🔧 Historique des soins", SOINS_TYPES, default=dent_data.get("soins",[]))
            notes_val = st.text_area("📝 Notes cliniques", value=dent_data.get("notes",""), placeholder="Ex: Carie distale profonde, sondage 5mm...", height=60)

            if st.form_submit_button("💾 Sauvegarder cette dent", use_container_width=True, type="primary"):
                twin["dents"][sel_str] = {"etat":nouveau_etat,"risque_carie":rc_val,"inflammation":infl_val,"profondeur_poche":poche_val,"soins":soins_val,"notes":notes_val}
                save_twin(pid, twin)
                st.success(f"✅ Dent {sel_num} mise à jour !"); st.rerun()

    with col_preview:
        # Prévisualisation 3D dent
        svg = render_dent_svg(sel_num, dent_data, selected=True)
        st.markdown(f"""<div style="text-align:center;background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:16px;">
            <div style="font-size:0.72rem;color:#6b7280;margin-bottom:8px;font-weight:600;">PRÉVISUALISATION 3D</div>
            {svg}
            <div style="margin-top:8px;display:flex;flex-direction:column;gap:4px;">
                <div style="font-size:0.7rem;color:#6b7280;">● Coin haut-droit : risque carieux</div>
                <div style="font-size:0.7rem;color:#6b7280;">● Coin haut-gauche : inflammation</div>
                <div style="font-size:0.7rem;color:#6b7280;">● Coin bas-droit : soins enregistrés</div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Indicateurs rapides
        poche_v = dent_data.get("profondeur_poche", 2)
        poche_c = "#16a34a" if poche_v <= 3 else "#d97706" if poche_v <= 5 else "#e11d48"
        poche_lbl = "✅ Normal" if poche_v <= 3 else "⚠️ Pathologique" if poche_v <= 5 else "🔴 Sévère"
        st.markdown(f"""<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:12px;margin-top:10px;text-align:center;">
            <div style="font-size:0.68rem;color:#6b7280;font-weight:700;margin-bottom:6px;">POCHE PARO</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:{poche_c};">{poche_v}mm</div>
            <div style="font-size:0.68rem;color:#9ca3af;">{poche_lbl}</div>
        </div>""", unsafe_allow_html=True)

    # ── Action rapide : projeter microbiome ──
    st.markdown("---")
    col_proj, col_notes_g = st.columns([1,1])
    with col_proj:
        st.markdown("#### ⚡ Actions Rapides")
        sm_pat = st.session_state.patients.get(st.session_state.patient_sel,{}).get("s_mutans",0)
        pg_pat = st.session_state.patients.get(st.session_state.patient_sel,{}).get("p_gingivalis",0)
        if st.button("🧬 Projeter microbiome sur toutes les dents", use_container_width=True,
                     help="Calcule le risque carieux et l'inflammation à partir des biomarqueurs globaux"):
            for num_str in twin["dents"]:
                if twin["dents"][num_str].get("etat")=="absente": continue
                dtype2 = DENTS_FDI.get(int(num_str),{}).get("type","incisive")
                fact = 1.2 if dtype2 in ["molaire","premolaire"] else 0.85
                rc2 = min(100, int((sm_pat/8.0)*100*fact))
                in2 = min(100, int((pg_pat/2.0)*100))
                twin["dents"][num_str]["risque_carie"] = rc2
                twin["dents"][num_str]["inflammation"]  = in2
            save_twin(pid, twin)
            st.success("✅ Microbiome projeté !"); st.rerun()

        if twin.get("derniere_maj"):
            st.caption(f"Dernière mise à jour : {twin['derniere_maj']}")

        # Stats bilan
        nb_s  = sum(1 for d in twin["dents"].values() if d.get("etat")=="saine")
        nb_pb2= sum(1 for d in twin["dents"].values() if d.get("etat") in ["carie","paro"])
        nb_tx2= sum(1 for d in twin["dents"].values() if d.get("etat")=="traitement")
        nb_ab2= sum(1 for d in twin["dents"].values() if d.get("etat")=="absente")
        st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:12px 14px;margin-top:10px;">
            <div style="font-size:0.75rem;font-weight:700;color:#374151;margin-bottom:8px;">📊 Bilan du twin</div>
            <div style="font-size:0.82rem;display:flex;flex-direction:column;gap:4px;">
                <div style="display:flex;justify-content:space-between;"><span>✅ Saines</span><b style="color:#16a34a;">{nb_s}</b></div>
                <div style="display:flex;justify-content:space-between;"><span>🔴 Problèmes</span><b style="color:#ef4444;">{nb_pb2}</b></div>
                <div style="display:flex;justify-content:space-between;"><span>🔧 En traitement</span><b style="color:#2563eb;">{nb_tx2}</b></div>
                <div style="display:flex;justify-content:space-between;"><span>⬜ Absentes</span><b style="color:#94a3b8;">{nb_ab2}</b></div>
                <div style="display:flex;justify-content:space-between;border-top:1px solid #e5e7eb;padding-top:4px;margin-top:2px;"><span>📊 Présentes</span><b>{32-nb_ab2}/32</b></div>
            </div>
        </div>""", unsafe_allow_html=True)

    with col_notes_g:
        st.markdown("#### 📝 Notes Générales")
        with st.form(f"form_notes_{pid}"):
            notes_g = st.text_area("Notes du cabinet", value=twin.get("notes_generales",""), placeholder="Bruxisme, prothèse, antécédents...", height=80)
            ip_v = st.slider("Indice de plaque global", 0, 100, int(twin.get("indice_plaque",0)))
            is_v = st.slider("Indice de saignement global", 0, 100, int(twin.get("indice_saignement",0)))
            if st.form_submit_button("💾 Sauvegarder", use_container_width=True):
                twin["notes_generales"]=notes_g; twin["indice_plaque"]=ip_v; twin["indice_saignement"]=is_v
                save_twin(pid, twin); st.success("✅ Sauvegardé"); st.rerun()


def render_twin_tableau(twin):
    """Vue tableau récapitulatif de toutes les dents."""
    st.markdown("---")
    st.markdown("#### 📋 Tableau Complet des Dents")
    tab_q1,tab_q2,tab_q3,tab_q4,tab_all = st.tabs(["Q1 — Haut Droite","Q2 — Haut Gauche","Q3 — Bas Gauche","Q4 — Bas Droite","Vue complète"])
    def rows_for_q(q):
        rows=[]
        for num,info in DENTS_FDI.items():
            if info["quadrant"]!=q: continue
            d=twin["dents"].get(str(num),{"etat":"saine"})
            ei=ETATS_DENT.get(d.get("etat","saine"),ETATS_DENT["saine"])
            rows.append({"N° FDI":num,"Dent":info["nom"],"État":f"{ei['icon']} {ei['label']}","Risque carieux":f"{d.get('risque_carie',0)}/100","Inflammation":f"{d.get('inflammation',0)}/100","Poche (mm)":d.get("profondeur_poche",2),"Soins":", ".join(d.get("soins",[])) or "—","Notes":d.get("notes","")[:40] or "—"})
        return rows
    with tab_q1: st.dataframe(pd.DataFrame(rows_for_q(1)),use_container_width=True,hide_index=True)
    with tab_q2: st.dataframe(pd.DataFrame(rows_for_q(2)),use_container_width=True,hide_index=True)
    with tab_q3: st.dataframe(pd.DataFrame(rows_for_q(3)),use_container_width=True,hide_index=True)
    with tab_q4: st.dataframe(pd.DataFrame(rows_for_q(4)),use_container_width=True,hide_index=True)
    with tab_all:
        all_rows=[]
        for num,info in DENTS_FDI.items():
            d=twin["dents"].get(str(num),{"etat":"saine"}); ei=ETATS_DENT.get(d.get("etat","saine"),ETATS_DENT["saine"])
            all_rows.append({"N°":num,"Dent":info["nom"],"Q":f"Q{info['quadrant']}","État":f"{ei['icon']} {ei['label']}","Carie":f"{d.get('risque_carie',0)}/100","Inflam.":f"{d.get('inflammation',0)}/100","Poche":f"{d.get('profondeur_poche',2)}mm"})
        st.dataframe(pd.DataFrame(all_rows),use_container_width=True,hide_index=True)


def render_twin_praticien(patient):
    twin = get_twin(patient["id"])
    sm=patient["s_mutans"]; pg=patient["p_gingivalis"]
    st.markdown(f"""<div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:14px;padding:20px 28px;margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:14px;">
            <span style="background:linear-gradient(135deg,#38bdf8,#0284c7);border-radius:10px;padding:8px 12px;font-size:1.8rem;">🦷</span>
            <div><div style="font-family:'DM Serif Display',serif;font-size:1.4rem;color:white;">Twin Numérique Dentaire — {patient['nom']}</div>
            <div style="font-size:0.82rem;color:rgba(255,255,255,0.65);">Vue 3D · Numérotation FDI · Corrélation microbiome · Suivi par dent</div></div>
        </div></div>""", unsafe_allow_html=True)

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
    twin = get_twin(patient["id"])
    sm=patient["s_mutans"]; pg=patient["p_gingivalis"]
    scores_q = {q: score_quadrant(twin,q) for q in [1,2,3,4]}
    score_global = round(sum(scores_q.values())/4)
    sc = "#16a34a" if score_global>=80 else "#d97706" if score_global>=60 else "#e11d48"

    st.markdown(f"""<div style="background:linear-gradient(135deg,#1a3a5c,#2563eb);border-radius:14px;padding:20px 28px;margin-bottom:20px;">
        <div style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:white;">🦷 Mon Twin Numérique Dentaire</div>
        <div style="font-size:0.82rem;color:rgba(255,255,255,0.7);">Visualisation de l'état de vos dents · Mis à jour par votre praticien</div>
    </div>""", unsafe_allow_html=True)

    # Score global patient
    col_score, col_q = st.columns([1,2])
    with col_score:
        st.markdown(f"""<div style="background:linear-gradient(135deg,{sc}18,{sc}08);border:2px solid {sc};border-radius:16px;padding:28px 20px;text-align:center;height:100%;">
            <div style="font-size:0.72rem;color:#6b7280;font-weight:700;text-transform:uppercase;margin-bottom:6px;">Score Santé Bucco-Dentaire</div>
            <div style="font-family:'DM Serif Display',serif;font-size:3.5rem;color:{sc};line-height:1;">{score_global}</div>
            <div style="font-size:0.75rem;color:#9ca3af;">/100</div>
            <div style="margin-top:12px;font-size:0.9rem;font-weight:600;color:{sc};">
                {"✅ Très bonne santé" if score_global>=80 else "⚠️ Points à surveiller" if score_global>=60 else "🔴 Soins recommandés"}
            </div>
        </div>""", unsafe_allow_html=True)
    with col_q:
        q_labels = {1:"Haut Droite",2:"Haut Gauche",3:"Bas Gauche",4:"Bas Droite"}
        for q in [1,2]:
            qs=scores_q[q]; qc="#16a34a" if qs>=80 else "#d97706" if qs>=50 else "#e11d48"
            emoji = "✅" if qs>=80 else "⚠️" if qs>=50 else "🔴"
            st.markdown(f'<div style="background:#f8fafc;border:1px solid {qc}30;border-radius:8px;padding:8px 12px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><span style="font-size:0.85rem;color:#374151;">{emoji} {q_labels[q]}</span><span style="font-family:\'DM Serif Display\',serif;font-size:1.2rem;color:{qc};font-weight:700;">{qs}/100</span></div>', unsafe_allow_html=True)
        for q in [3,4]:
            qs=scores_q[q]; qc="#16a34a" if qs>=80 else "#d97706" if qs>=50 else "#e11d48"
            emoji = "✅" if qs>=80 else "⚠️" if qs>=50 else "🔴"
            st.markdown(f'<div style="background:#f8fafc;border:1px solid {qc}30;border-radius:8px;padding:8px 12px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><span style="font-size:0.85rem;color:#374151;">{emoji} {q_labels[q]}</span><span style="font-family:\'DM Serif Display\',serif;font-size:1.2rem;color:{qc};font-weight:700;">{qs}/100</span></div>', unsafe_allow_html=True)

    st.markdown("---")
    # Schéma 3D simplifié
    svg_top = render_arch_svg(twin, 1, 2, is_praticien=False)
    svg_bot = render_arch_svg(twin, 3, 4, is_praticien=False)
    st.markdown("##### Votre arcade dentaire")
    st.markdown(f'<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:14px;padding:10px;text-align:center;">{svg_top}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:14px;padding:10px;text-align:center;">{svg_bot}</div>', unsafe_allow_html=True)

    # Dents nécessitant attention
    st.markdown("---")
    dents_att = [(int(n),d) for n,d in twin["dents"].items() if d.get("etat") in ["carie","paro","surveillance","traitement"]]
    if dents_att:
        st.markdown("#### 🔍 Points d'attention")
        for num,d in dents_att:
            info=DENTS_FDI.get(num,{}); etat=d.get("etat","saine"); ei=ETATS_DENT.get(etat,ETATS_DENT["saine"])
            q_label={1:"Haut Droite",2:"Haut Gauche",3:"Bas Gauche",4:"Bas Droite"}.get(info.get("quadrant",1),"")
            soins=d.get("soins",[]); notes=d.get("notes","")
            st.markdown(f"""<div style="background:{ei['bg']};border:1px solid {ei['color']}40;border-radius:10px;padding:14px 18px;margin:8px 0;display:flex;align-items:center;gap:14px;">
                <div style="background:{ei['color']};color:white;width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:800;font-family:monospace;flex-shrink:0;">{num}</div>
                <div style="flex:1;">
                    <div style="font-weight:600;font-size:0.9rem;">{info.get('nom','Dent')} {ei['icon']} — {ei['label']}</div>
                    <div style="font-size:0.8rem;color:#6b7280;margin-top:2px;">{q_label}{" · Soins : " + ", ".join(soins) if soins else ""}</div>
                    {f'<div style="font-size:0.78rem;color:#374151;margin-top:4px;font-style:italic;">{notes}</div>' if notes else ""}
                </div></div>""", unsafe_allow_html=True)
    else:
        st.success("✅ Toutes vos dents suivies sont en bonne santé !")
    st.info("⚕️ Ce schéma est mis à jour par votre praticien lors de chaque visite.")

# ── ANALYSE PHOTO ─────────────────────────────────────────
def analyser_photo_bouche(image_bytes, mime_type="image/jpeg"):
    if not ANTHROPIC_API_KEY: return {"error":"Clé API Anthropic manquante."}
    b64=base64.standard_b64encode(image_bytes).decode()
    sp='Tu es un assistant d\'aide à la décision dentaire. Réponds UNIQUEMENT en JSON valide sans markdown. Structure: {"qualite_image":"bonne|moyenne|insuffisante","zones_analysees":[],"findings":[{"zone":"","observation":"","severite":"normal|attention|alerte","detail":""}],"score_global":0,"profil_visuel":"Bouche saine|Inflammation légère|Inflammation modérée|Dysbiose visible|Urgence clinique","recommandations_immediates":[],"disclaimer":"Aide à la décision.","confiance":"élevée|modérée|faible"}'
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"},json={"model":"claude-sonnet-4-20250514","max_tokens":1500,"system":sp,"messages":[{"role":"user","content":[{"type":"image","source":{"type":"base64","media_type":mime_type,"data":b64}},{"type":"text","text":"Analyse cette photo en JSON."}]}]},timeout=30)
        r.raise_for_status(); raw=r.json()["content"][0]["text"].strip().replace("```json","").replace("```","").strip(); return json.loads(raw)
    except Exception as e: return {"error":str(e)}

def render_photo_analysis(result):
    if "error" in result: st.error(f"⚠️ {result['error']}"); return
    score=result.get("score_global",50); profil=result.get("profil_visuel","N/A")
    c="#16a34a" if score>=70 else "#d97706" if score>=45 else "#e11d48"
    cs,ci=st.columns([1,3])
    with cs: st.markdown(f'<div style="text-align:center;background:linear-gradient(135deg,{c}22,{c}11);border:2px solid {c};border-radius:16px;padding:24px;"><div style="font-family:\'DM Serif Display\',serif;font-size:3rem;color:{c};line-height:1;">{score}</div><div style="font-size:0.75rem;color:#6b7280;margin-top:4px;">Score santé visuelle</div><div style="font-size:0.8rem;font-weight:600;color:{c};margin-top:8px;">{profil}</div></div>',unsafe_allow_html=True)
    with ci:
        st.markdown(f"**Qualité :** `{result.get('qualite_image','N/A')}` · **Confiance :** `{result.get('confiance','N/A')}`")
        zones=result.get("zones_analysees",[])
        if zones: st.markdown(f"**Zones :** {' · '.join(zones)}")
        for f in result.get("findings",[]):
            sev=f.get("severite","normal"); css="finding-alert" if sev=="alerte" else "finding-warn" if sev=="attention" else "finding-ok"; icon="🔴" if sev=="alerte" else "🟡" if sev=="attention" else "🟢"
            st.markdown(f"<span class='finding-badge {css}'>{icon} {f.get('zone','')} — {f.get('observation','')}</span>",unsafe_allow_html=True)
    recos=result.get("recommandations_immediates",[])
    if recos:
        st.markdown("---"); st.markdown("#### ✅ Actions immédiates")
        for r in recos: st.markdown(f"- {r}")
    if result.get("disclaimer"): st.caption(f"⚕️ *{result['disclaimer']}*")

# ── RECOMMANDATIONS ───────────────────────────────────────
def generer_recommandations(sm,pg,div):
    plan={"priorites":[],"aliments_favoriser":[],"aliments_eviter":[],"probiotiques":[],"suivi_semaines":24,"profil_label":"","profil_description":""}
    nb=sum([sm>3.0,pg>0.5,div<50])
    if nb==0: plan["profil_label"]="🟢 Microbiome Équilibré"; plan["profil_description"]="Votre flore buccale est protectrice."; plan["suivi_semaines"]=24
    elif nb==1: plan["profil_label"]="🟡 Déséquilibre Modéré"; plan["profil_description"]="Un déséquilibre détecté. Corrections en 2-3 mois."; plan["suivi_semaines"]=12
    else: plan["profil_label"]="🔴 Dysbiose Active"; plan["profil_description"]="Plusieurs marqueurs en alerte. Plan renforcé nécessaire."; plan["suivi_semaines"]=8
    if sm>3.0:
        plan["priorites"].append({"icone":"🦠","titre":"Réduire S. mutans","urgence":"Elevee" if sm>6.0 else "Moderee","explication":f"S. mutans : {sm}% (normal < 3%)","actions":["Brossage 2 min après repas sucrés","Fil dentaire quotidien le soir","Bain de bouche fluoré 1x/jour","Éviter le grignotage"]})
        plan["aliments_eviter"]+=["Bonbons","Sodas","Pain blanc","Jus de fruits"]
        plan["aliments_favoriser"]+=["Fromage à pâte dure","Yaourt nature","Légumes crus","Thé vert","Noix"]
        plan["probiotiques"].append({"nom":"Lactobacillus reuteri DSM 17938","forme":"Comprimés 1x/jour après brossage","duree":"3 mois","benefice":"Inhibe S. mutans","marques":"BioGaia Prodentis"})
    if pg>0.5:
        plan["priorites"].append({"icone":"🩸","titre":"Éliminer P. gingivalis","urgence":"Elevee" if pg>1.5 else "Moderee","explication":f"P. gingivalis : {pg}% (normal < 0.5%)","actions":["Nettoyage interdentaire quotidien — PRIORITÉ N°1","Brossage langue matin et soir","Consultation parodontale","Arrêt du tabac"]})
        plan["aliments_eviter"]+=["Tabac","Alcool en excès","Sucres raffinés","Ultra-transformés"]
        plan["aliments_favoriser"]+=["Poissons gras 2-3×/semaine","Myrtilles (polyphénols)","Légumes verts feuillus","Huile d'olive","Ail et oignon"]
        plan["probiotiques"].append({"nom":"L. reuteri + L. salivarius","forme":"Pastilles 2x/jour","duree":"3-6 mois","benefice":"Réduit P. gingivalis","marques":"GUM PerioBalance, Blis K12"})
    if div<50:
        plan["priorites"].append({"icone":"🌱","titre":"Restaurer la diversité","urgence":"Moderee" if div>30 else "Elevee","explication":f"Diversité : {div}/100 (optimal > 65)","actions":["30 plantes différentes/semaine","Réduire antiseptiques quotidiens","Fibres prébiotiques","1.5L eau/jour"]})
        plan["aliments_favoriser"]+=["Légumes racines","Pomme avec la peau","Légumineuses","Choucroute","Kombucha"]
        plan["aliments_eviter"]+=["Bains de bouche antiseptiques quotidiens","Antibiotiques inutiles"]
        plan["probiotiques"].append({"nom":"Streptococcus salivarius K12 + M18","forme":"Pastilles le soir","duree":"2-3 mois","benefice":"Recolonise la flore","marques":"BLIS K12"})
    if nb==0:
        plan["priorites"].append({"icone":"✅","titre":"Maintenir l'équilibre","urgence":"Routine","explication":"Microbiome oral en bonne santé.","actions":["Brossage 2×/jour","Fil dentaire","Alimentation variée","Contrôle dans 6 mois"]})
        plan["aliments_favoriser"]+=["Alimentation méditerranéenne","Eau","Yaourt, kéfir"]
    plan["aliments_favoriser"]=list(dict.fromkeys(plan["aliments_favoriser"])); plan["aliments_eviter"]=list(dict.fromkeys(plan["aliments_eviter"]))
    return plan

# ── PDF ───────────────────────────────────────────────────
def generer_pdf(pnom,rc,rp,div,hist_df,plan,scores=None):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,HRFlowable
        from reportlab.lib.enums import TA_CENTER
        buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=15*mm,rightMargin=15*mm,topMargin=15*mm,bottomMargin=15*mm)
        BLUE=colors.HexColor('#1a3a5c'); LB=colors.HexColor('#dbeafe'); GBG=colors.HexColor('#f9fafb')
        ts=ParagraphStyle('T',fontSize=18,textColor=colors.white,alignment=TA_CENTER,fontName='Helvetica-Bold',spaceAfter=4)
        ss=ParagraphStyle('S',fontSize=10,textColor=colors.white,alignment=TA_CENTER,fontName='Helvetica',spaceAfter=6)
        h1=ParagraphStyle('H1',fontSize=13,textColor=BLUE,fontName='Helvetica-Bold',spaceBefore=10,spaceAfter=4)
        h2=ParagraphStyle('H2',fontSize=11,textColor=BLUE,fontName='Helvetica-Bold',spaceBefore=6,spaceAfter=3)
        bs=ParagraphStyle('B',fontSize=10,fontName='Helvetica',spaceAfter=3,leading=14)
        its=ParagraphStyle('I',fontSize=9,fontName='Helvetica-Oblique',textColor=colors.HexColor('#555'),spaceAfter=4)
        sml=ParagraphStyle('Sm',fontSize=8,fontName='Helvetica',textColor=colors.grey,alignment=TA_CENTER)
        elems=[]
        ht=Table([[Paragraph("OralBiome - Rapport Patient Complet",ts)],[Paragraph("Microbiome Oral Predictif | Rapport Personnalise",ss)]],colWidths=[180*mm])
        ht.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),BLUE),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)])); elems+=[ht,Spacer(1,5*mm)]
        it=Table([[Paragraph(f"<b>Patient :</b> {pnom}",bs),Paragraph(f"<b>Date :</b> {date.today().strftime('%d/%m/%Y')}",bs)]],colWidths=[90*mm,90*mm])
        it.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LB),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),8)])); elems+=[it,Spacer(1,6*mm)]
        elems+=[Paragraph("Resultats Microbiome",h1),HRFlowable(width="100%",thickness=1,color=LB)]
        rt=Table([[Paragraph("<b>Risque Carieux</b>",bs),Paragraph(f"<b>{rc}</b>",bs)],[Paragraph("<b>Risque Parodontal</b>",bs),Paragraph(f"<b>{rp}</b>",bs)],[Paragraph("<b>Score Diversite</b>",bs),Paragraph(f"<b>{div}/100</b> (optimal > 65)",bs)]],colWidths=[90*mm,90*mm])
        rt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),GBG),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),8)])); elems+=[rt,Spacer(1,6*mm)]
        if scores:
            elems+=[Paragraph("Scores Risque Systemique",h1),HRFlowable(width="100%",thickness=1,color=LB),Paragraph("Scores bases sur correlations litterature scientifique.",its),Spacer(1,3*mm)]
            sr=[["Pathologie","Score","Niveau","Action"]]; 
            for key,data in scores.items():
                ll="Eleve" if data["level"]=="high" else "Modere" if data["level"]=="med" else "Faible"; action=data["actions"][0] if data["actions"] else "-"
                sr.append([Paragraph(f"{data['icon']} {data['label']}",bs),Paragraph(f"<b>{data['score']}</b>",bs),Paragraph(ll,bs),Paragraph(action[:80]+"..." if len(action)>80 else action,bs)])
            syt=Table(sr,colWidths=[55*mm,22*mm,22*mm,81*mm]); syt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('ROWBACKGROUNDS',(0,1),(-1,-1),[GBG,colors.white]),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),6),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#e5e7eb'))])); elems+=[syt,Spacer(1,6*mm)]
        if plan["priorites"]:
            elems+=[Paragraph("Plan d'Action",h1),HRFlowable(width="100%",thickness=1,color=LB)]
            for i,p in enumerate(plan["priorites"]):
                b="URGENT" if p["urgence"]=="Elevee" else "MODERE" if p["urgence"]=="Moderee" else "ROUTINE"
                elems.append(Paragraph(f"Priorite {i+1} — {p['titre']} [{b}]",h2))
                for action in p["actions"]: elems.append(Paragraph(f"• {action}",bs))
                elems.append(Spacer(1,3*mm))
        elems+=[Paragraph("Plan Nutritionnel",h1),HRFlowable(width="100%",thickness=1,color=LB)]
        if plan["aliments_favoriser"] or plan["aliments_eviter"]:
            mi=max(len(plan["aliments_favoriser"]),len(plan["aliments_eviter"]))
            nr=[[Paragraph(f"+ {plan['aliments_favoriser'][i] if i<len(plan['aliments_favoriser']) else ''}",bs),Paragraph(f"- {plan['aliments_eviter'][i] if i<len(plan['aliments_eviter']) else ''}",bs)] for i in range(mi)]
            nut=Table(nr,colWidths=[90*mm,90*mm]); nut.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),colors.HexColor('#f0fdf4')),('BACKGROUND',(1,0),(1,-1),colors.HexColor('#fff1f2')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),8)])); elems.append(nut)
        elems.append(Spacer(1,8*mm))
        ft=Table([[Paragraph("Ce rapport est fourni a titre preventif. Ne constitue pas un diagnostic medical.",sml)],[Paragraph("OralBiome | contact@oralbiome.com",sml)]],colWidths=[180*mm]); ft.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LB),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)])); elems.append(ft)
        doc.build(elems); return buf.getvalue()
    except ImportError: return b"Installez reportlab : pip install reportlab"

# ── ALERTES & DASHBOARD ───────────────────────────────────
def calculer_alertes(patients):
    alertes=[]; today=date.today()
    for nom,p in patients.items():
        sm=p["s_mutans"]; pg=p["p_gingivalis"]; div=p["diversite"]; hist=p["historique"]
        if pg>1.5: alertes.append({"type":"urgence","patient":nom,"id":p["id"],"titre":f"P. gingivalis critique ({pg}%)","desc":"Risque parodontal sévère.","priorite":1,"icone":"🚨","action":"Consultation parodontale urgente"})
        elif sm>6.0: alertes.append({"type":"urgence","patient":nom,"id":p["id"],"titre":f"S. mutans critique ({sm}%)","desc":"Caries actives probables.","priorite":1,"icone":"🚨","action":"Bilan carie urgent"})
        if not hist.empty:
            try:
                ld=datetime.strptime(hist.iloc[-1]["Date"],"%d/%m/%Y").date(); ea=sm>3.0 or pg>0.5 or div<50
                dl=8 if ea and (pg>1.5 or sm>6.0) else 12 if ea else 24; dp=ld+timedelta(days=dl*7); jr=(dp-today).days
                if jr<0: alertes.append({"type":"urgence","patient":nom,"id":p["id"],"titre":f"Contrôle en retard de {abs(jr)} jours","desc":f"Dernier examen : {hist.iloc[-1]['Date']}.","priorite":2,"icone":"⏰","action":"Planifier rendez-vous"})
                elif jr<=14: alertes.append({"type":"warn","patient":nom,"id":p["id"],"titre":f"Contrôle dans {jr} jours","desc":f"Prochain : {dp.strftime('%d/%m/%Y')}.","priorite":3,"icone":"📅","action":"Envoyer rappel"})
            except: pass
        if len(hist)>=2:
            try:
                dp2=float(hist.iloc[-1]["P. gingiv. (%)"])-float(hist.iloc[-2]["P. gingiv. (%)"]); dm2=float(hist.iloc[-1]["S. mutans (%)"])-float(hist.iloc[-2]["S. mutans (%)"])
                if dp2>0.3: alertes.append({"type":"warn","patient":nom,"id":p["id"],"titre":f"Dégradation paro (+{dp2:.1f}%)","desc":"Augmentation P. gingivalis.","priorite":2,"icone":"📈","action":"Adapter protocole"})
                if dm2>1.0: alertes.append({"type":"warn","patient":nom,"id":p["id"],"titre":f"Dégradation cariogène (+{dm2:.1f}%)","desc":"Augmentation S. mutans.","priorite":3,"icone":"📈","action":"Revoir plan nutritionnel"})
            except: pass
        if hist.empty: alertes.append({"type":"info","patient":nom,"id":p["id"],"titre":"Aucune analyse","desc":"Pas encore d'analyse microbiome.","priorite":4,"icone":"📋","action":"Planifier examen initial"})
    return sorted(alertes,key=lambda x:x["priorite"])

def calculer_stats_cabinet(patients):
    total=len(patients)
    if total==0: return {}
    ac=sum(1 for p in patients.values() if p["s_mutans"]>3.0 or p["p_gingivalis"]>0.5 or p["diversite"]<50)
    am=sum(p["s_mutans"] for p in patients.values())/total; ap=sum(p["p_gingivalis"] for p in patients.values())/total; ad=sum(p["diversite"] for p in patients.values())/total
    rc2=sum(1 for p in patients.values() if calculer_score_systemique(p["s_mutans"],p["p_gingivalis"],p["diversite"])["cardiovasculaire"]["level"]=="high")
    ra2=sum(1 for p in patients.values() if calculer_score_systemique(p["s_mutans"],p["p_gingivalis"],p["diversite"])["alzheimer"]["level"]=="high")
    tv=sum(len(p["historique"]) for p in patients.values())
    return {"total":total,"alertes":ac,"stables":total-ac,"pct_alerte":round(ac/total*100),"avg_mutans":round(am,2),"avg_paro":round(ap,2),"avg_diversite":round(ad,1),"risque_cardio_eleve":rc2,"risque_alz_eleve":ra2,"total_visites":tv}

def render_dashboard(patients):
    stats=calculer_stats_cabinet(patients); alertes=calculer_alertes(patients)
    lh=logo_img(140,"margin-bottom:8px;filter:brightness(0) invert(1);opacity:0.85;")
    st.markdown(f'<div class="ob-header">{lh}<h1>📊 {t("dash_title")}</h1><p>Vue analytique en temps réel · Alertes · KPIs</p></div>',unsafe_allow_html=True)
    k1,k2,k3,k4,k5=st.columns(5)
    def kpi(n,v,l,d,c): n.markdown(f'<div class="kpi-card"><div class="kpi-num {c}">{v}</div><div class="kpi-lbl">{l}</div><div class="kpi-delta {c}">{d}</div></div>',unsafe_allow_html=True)
    kpi(k1,stats["total"],t("dash_total"),f"📂 {stats['total_visites']} visites","kpi-blue"); kpi(k2,stats["alertes"],t("dash_alerts"),f"⚠️ {stats['pct_alerte']}%","kpi-red")
    kpi(k3,stats["stables"],t("dash_stable"),f"✅ {100-stats['pct_alerte']}%","kpi-green"); kpi(k4,stats["risque_cardio_eleve"],t("dash_cardio"),"❤️ Suivi requis","kpi-amber"); kpi(k5,stats["risque_alz_eleve"],t("dash_neuro"),"🧠 P. gingivalis crit.","kpi-amber")
    st.markdown("<br>",unsafe_allow_html=True); st.markdown("#### 🧬 Moyennes Microbiome du Cabinet")
    cm1,cm2,cm3=st.columns(3)
    def bar(v,mx,c): pct2=min(100,v/mx*100); return f'<div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:{pct2:.0f}%;background:{c};"></div></div>'
    with cm1:
        c="#e11d48" if stats["avg_mutans"]>3 else "#16a34a"
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.8rem;color:#6b7280;font-weight:600;">S. MUTANS MOYEN</div><div class="kpi-num" style="color:{c};">{stats["avg_mutans"]}%</div><div style="font-size:0.75rem;color:#9ca3af;">Normal &lt; 3%</div>{bar(stats["avg_mutans"],8,c)}</div>',unsafe_allow_html=True)
    with cm2:
        c="#e11d48" if stats["avg_paro"]>0.5 else "#16a34a"
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.8rem;color:#6b7280;font-weight:600;">P. GINGIVALIS MOYEN</div><div class="kpi-num" style="color:{c};">{stats["avg_paro"]}%</div><div style="font-size:0.75rem;color:#9ca3af;">Normal &lt; 0.5%</div>{bar(stats["avg_paro"],2,c)}</div>',unsafe_allow_html=True)
    with cm3:
        c="#16a34a" if stats["avg_diversite"]>=65 else "#d97706" if stats["avg_diversite"]>=50 else "#e11d48"
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.8rem;color:#6b7280;font-weight:600;">DIVERSITÉ MOYENNE</div><div class="kpi-num" style="color:{c};">{stats["avg_diversite"]}/100</div><div style="font-size:0.75rem;color:#9ca3af;">Optimal &gt; 65</div>{bar(stats["avg_diversite"],100,c)}</div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True); ca2,cp2=st.columns([1,2])
    with ca2:
        st.markdown(f"#### 🔔 Alertes Actives `{len(alertes)}`")
        if not alertes: st.success("✅ Aucune alerte active.")
        else:
            for a in alertes[:8]:
                css="alert-card" if a["type"]=="urgence" else "alert-card warn" if a["type"]=="warn" else "alert-card info"
                st.markdown(f'<div class="{css}"><div class="alert-icon">{a["icone"]}</div><div class="alert-body"><div class="alert-title">{a["patient"]} — {a["titre"]}</div><div class="alert-desc">{a["desc"]}</div><div class="alert-meta">👉 {a["action"]}</div></div></div>',unsafe_allow_html=True)
    with cp2:
        st.markdown("#### 👥 État du Cabinet"); rows=[]
        for nom,p in patients.items():
            ea=p["s_mutans"]>3.0 or p["p_gingivalis"]>0.5 or p["diversite"]<50
            sys_s=calculer_score_systemique(p["s_mutans"],p["p_gingivalis"],p["diversite"]); top=max(sys_s.items(),key=lambda x:x[1]["score"])
            nba=sum(1 for a in alertes if a["patient"]==nom)
            rows.append({"Nom":nom,"Statut":"🔴 Alerte" if ea else "🟢 Stable","S. mutans":f"{p['s_mutans']}%","P. gingivalis":f"{p['p_gingivalis']}%","Diversité":f"{p['diversite']}/100","Top Risque":f"{top[1]['icon']} {top[1]['score']}/100","Alertes":nba if nba else "—"})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        st.markdown("#### 📈 Tendance Diversité"); chart_data={}
        for nom,p in patients.items():
            hist=p["historique"]
            if len(hist)>=2:
                dc=next((c for c in ["Diversite (%)","Diversité (%)"] if c in hist.columns),None)
                if dc: chart_data[nom]=hist[dc].astype(float).tolist()
        if chart_data:
            ml=max(len(v) for v in chart_data.values()); st.line_chart(pd.DataFrame({k:v+[None]*(ml-len(v)) for k,v in chart_data.items()}))
        else: st.caption("Pas assez d'historique.")
    st.markdown("---"); st.markdown(f"#### 🗂️ Toutes les Alertes ({len(alertes)})")
    if alertes:
        ft=st.selectbox("Filtrer",["Toutes","🚨 Urgences","⚠️ Avertissements","ℹ️ Infos"],label_visibility="collapsed")
        fm={"Toutes":None,"🚨 Urgences":"urgence","⚠️ Avertissements":"warn","ℹ️ Infos":"info"}
        for a in [x for x in alertes if fm[ft] is None or x["type"]==fm[ft]]:
            css="alert-card" if a["type"]=="urgence" else "alert-card warn" if a["type"]=="warn" else "alert-card info"
            ca3,cb3=st.columns([5,1])
            with ca3: st.markdown(f'<div class="{css}"><div class="alert-icon">{a["icone"]}</div><div class="alert-body"><div class="alert-title">{a["id"]} · {a["patient"]} — {a["titre"]}</div><div class="alert-desc">{a["desc"]}</div><div class="alert-meta">👉 {a["action"]}</div></div></div>',unsafe_allow_html=True)
            with cb3:
                st.markdown("<br>",unsafe_allow_html=True)
                if st.button("Ouvrir →",key=f"ab_{a['patient']}_{a['titre'][:8]}"): st.session_state.patient_sel=a["patient"]; st.session_state.vue="dossier"; st.rerun()
    else: st.success("✅ Aucune alerte active.")

# ── RGPD ──────────────────────────────────────────────────
def render_rgpd_banner():
    _,col_m,_=st.columns([1,3,1])
    with col_m:
        st.markdown("""<div style="background:white;border:2px solid #1a3a5c;border-radius:16px;padding:28px 32px;margin:40px auto;box-shadow:0 8px 32px rgba(0,0,0,0.12);">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;"><span style="font-size:2rem;">🔒</span>
        <div><div style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:#1a3a5c;font-weight:600;">Protection de vos données — RGPD</div>
        <div style="font-size:0.8rem;color:#6b7280;margin-top:2px;">Conformité UE 2016/679</div></div></div></div>""",unsafe_allow_html=True)
        with st.expander("📄 Politique de confidentialité",expanded=False):
            st.markdown("**1. Responsable** — OralBiome SAS · contact@oralbiome.com\n\n**2. Données** — Identification, santé bucco-dentaire, biomarqueurs, anamnèse.\n\n**3. Base légale** — Consentement explicite (Art. 9 RGPD).\n\n**4. Conservation** — Durée de la relation + archivage légal 10 ans.\n\n**5. Droits** — Accès, rectification, effacement → contact@oralbiome.com\n\n**6. CNIL** — www.cnil.fr")
        st.markdown("""<div style="background:#fefce8;border:1px solid #fde047;border-radius:10px;padding:14px 18px;margin:12px 0;">
        <div style="font-size:0.85rem;color:#713f12;">⚠️ <b>Données de santé :</b> Traitement réservé aux professionnels de santé habilités.</div></div>""",unsafe_allow_html=True)
        agree1=st.checkbox("✅ J'accepte que mes données de santé soient traitées par OralBiome conformément à la politique ci-dessus.",key="rgpd_check1")
        agree2=st.checkbox("✅ Je confirme être un professionnel de santé habilité ou le patient concerné.",key="rgpd_check2")
        st.checkbox("📧 J'accepte de recevoir des communications OralBiome. *(optionnel)*",key="rgpd_check3")
        st.markdown("<br>",unsafe_allow_html=True)
        cr,ca=st.columns(2)
        with cr:
            if st.button("Refuser et quitter",use_container_width=True): st.session_state.mode="choix"; st.rerun()
        with ca:
            if st.button("Accepter et continuer →",use_container_width=True,type="primary",disabled=not(agree1 and agree2)):
                st.session_state.rgpd_accepted=True; st.rerun()
        if not(agree1 and agree2): st.caption("⚠️ Les deux premières cases sont obligatoires.")

# ── ONBOARDING ────────────────────────────────────────────
def render_onboarding():
    step=st.session_state.onboarding_step
    lh=logo_img(160,"margin:0 auto 16px auto;")
    st.markdown(f"""<div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:20px;padding:32px 40px;margin-bottom:32px;text-align:center;color:white;">
        {lh}<h2 style="font-family:'DM Serif Display',serif;font-size:2rem;margin:0;">Bienvenue sur OralBiome</h2>
        <p style="opacity:0.7;margin:8px 0 0 0;">Configuration · 3 étapes · moins de 2 minutes</p></div>""",unsafe_allow_html=True)
    def sc(n):
        if n<step: css="background:#16a34a;border:2px solid #16a34a;color:white;"; txt="✓"
        elif n==step: css="background:#2563eb;border:2px solid #2563eb;color:white;"; txt=str(n)
        else: css="background:white;border:2px solid #d1d5db;color:#9ca3af;"; txt=str(n)
        return f'<div style="width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.9rem;{css}">{txt}</div>'
    def sl(txt,n): c="#16a34a" if n<step else "#2563eb" if n==step else "#9ca3af"; return f'<div style="font-size:0.78rem;font-weight:600;color:{c};margin-top:6px;">{txt}</div>'
    def sline(n): c="#16a34a" if n<step else "#e5e7eb"; return f'<div style="width:80px;height:2px;background:{c};margin:18px 4px 0 4px;"></div>'
    st.markdown(f'<div style="display:flex;justify-content:center;align-items:flex-start;margin:0 0 36px 0;"><div style="text-align:center;">{sc(1)}{sl("Bienvenue",1)}</div>{sline(1)}<div style="text-align:center;">{sc(2)}{sl("Votre cabinet",2)}</div>{sline(2)}<div style="text-align:center;">{sc(3)}{sl("Premier patient",3)}</div></div>',unsafe_allow_html=True)
    _,col_c,_=st.columns([1,2,1])
    if step==1:
        with col_c:
            st.markdown("""<div style="background:white;border-radius:20px;padding:40px 44px;border:1px solid #e5e7eb;box-shadow:0 4px 24px rgba(0,0,0,0.06);text-align:center;">
                <div style="font-size:2.4rem;margin-bottom:12px;">🦷</div>
                <h3 style="font-family:'DM Serif Display',serif;color:#1a3a5c;margin:0 0 8px 0;">La plateforme d'intelligence orale prédictive</h3>
                <p style="color:#6b7280;font-size:0.9rem;margin-bottom:24px;">Corrèlez le microbiote oral avec les risques systémiques.<br>Rapports cliniques en 1 clic. Twin numérique dentaire.</p>
                <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:16px;"><div style="font-weight:600;color:#15803d;margin-bottom:4px;">✅ Votre compte est activé</div>
                <div style="font-size:0.85rem;color:#166534;">Accès complet · Données sécurisées · Conforme RGPD</div></div></div>""",unsafe_allow_html=True)
            st.markdown("<br>",unsafe_allow_html=True)
            if st.button("Commencer →",use_container_width=True,type="primary"): st.session_state.onboarding_step=2; st.rerun()
    elif step==2:
        with col_c:
            st.markdown("### 🏥 Configurez votre cabinet")
            with st.form("form_cabinet"):
                c1,c2=st.columns(2)
                with c1:
                    cabinet_nom=st.text_input("Nom du cabinet *",value=st.session_state.get("cabinet_nom",""),placeholder="Cabinet Dentaire Dupont")
                    cabinet_praticien=st.text_input("Praticien *",value=st.session_state.get("cabinet_praticien",""),placeholder="Dr. Marie Dupont")
                    cabinet_specialite=st.selectbox("Spécialité",["Omnipraticien","Parodontiste","Orthodontiste","Implantologiste","Pédodontiste","Autre"])
                with c2:
                    cabinet_adresse=st.text_input("Adresse",value=st.session_state.get("cabinet_adresse",""),placeholder="12 rue de la Santé")
                    cabinet_tel=st.text_input("Téléphone",value=st.session_state.get("cabinet_tel",""),placeholder="+33 1 23 45 67 89")
                    cabinet_email=st.text_input("Email cabinet",value=st.session_state.get("cabinet_email",""),placeholder="contact@cabinet.fr")
                sub2=st.form_submit_button("Enregistrer et continuer →",use_container_width=True,type="primary")
                if sub2:
                    if not cabinet_nom.strip() or not cabinet_praticien.strip(): st.error("Nom du cabinet et praticien obligatoires.")
                    else:
                        st.session_state.cabinet_nom=cabinet_nom; st.session_state.cabinet_praticien=cabinet_praticien; st.session_state.cabinet_adresse=cabinet_adresse; st.session_state.cabinet_tel=cabinet_tel; st.session_state.cabinet_email=cabinet_email; st.session_state.cabinet_specialite=cabinet_specialite; st.session_state.onboarding_step=3; st.rerun()
            if st.button("← Retour",key="back2"): st.session_state.onboarding_step=1; st.rerun()
    elif step==3:
        with col_c:
            st.markdown("### 👤 Ajoutez votre premier patient")
            st.caption("Optionnel — vous pourrez en ajouter d'autres depuis le tableau de bord.")
            with st.form("form_premier_patient"):
                fc1,fc2=st.columns(2)
                with fc1: p_nom=st.text_input("Nom complet",placeholder="Jean Dupont"); p_age=st.number_input("Âge",1,120,40); p_email=st.text_input("Email",placeholder="jean@email.com")
                with fc2: p_tel=st.text_input("Téléphone",placeholder="+32 472 000 000"); p_sm=st.number_input("S. mutans (%)",0.0,10.0,2.0,step=0.1); p_pg=st.number_input("P. gingivalis (%)",0.0,5.0,0.2,step=0.1)
                p_div=st.slider("Score Diversité Microbienne",0,100,70)
                csk,csv=st.columns(2)
                with csk: passer=st.form_submit_button("Passer cette étape →",use_container_width=True)
                with csv: sauver=st.form_submit_button("Créer le dossier et terminer ✓",use_container_width=True,type="primary")
                if passer: st.session_state.onboarding_done=True; st.session_state.connecte=True; st.session_state.mode="praticien"; st.rerun()
                if sauver:
                    if p_nom.strip():
                        nid=f"P{str(len(st.session_state.patients)+1).zfill(3)}"; stat="Alerte" if p_sm>3.0 or p_pg>0.5 or p_div<50 else "Stable"
                        df_n=pd.DataFrame({"Date":[date.today().strftime("%d/%m/%Y")],"Acte / Test":["Examen Initial"],"S. mutans (%)":[p_sm],"P. gingiv. (%)":[p_pg],"Diversite (%)":[p_div],"Status":[stat]})
                        st.session_state.patients[p_nom]={"id":nid,"nom":p_nom,"age":p_age,"email":p_email,"telephone":p_tel,"date_naissance":"","historique":df_n,"s_mutans":p_sm,"p_gingivalis":p_pg,"diversite":p_div,"code_patient":f"OB-{nid}"}
                        st.session_state.patient_sel=p_nom
                    st.session_state.onboarding_done=True; st.session_state.connecte=True; st.session_state.mode="praticien"; st.success("✅ Bienvenue !"); st.rerun()
            if st.button("← Retour",key="back3"): st.session_state.onboarding_step=2; st.rerun()

# ── DONNÉES INITIALES ─────────────────────────────────────
def donnees_initiales():
    patients={}
    df1=pd.DataFrame({"Date":["12/10/2023","08/04/2026"],"Acte / Test":["Examen Initial","Controle"],"S. mutans (%)":[4.2,4.2],"P. gingiv. (%)":[0.8,0.3],"Diversite (%)":[45,75],"Status":["Alerte","Alerte"]})
    patients["Jean Dupont"]={"id":"P001","nom":"Jean Dupont","age":42,"email":"jean.dupont@email.com","telephone":"+32 472 123 456","date_naissance":"15/03/1982","historique":df1,"s_mutans":4.2,"p_gingivalis":0.3,"diversite":75,"code_patient":"OB-P001"}
    df2=pd.DataFrame({"Date":["05/01/2024"],"Acte / Test":["Examen Initial"],"S. mutans (%)":[1.2],"P. gingiv. (%)":[0.1],"Diversite (%)":[82],"Status":["Stable"]})
    patients["Marie Martin"]={"id":"P002","nom":"Marie Martin","age":35,"email":"marie.martin@email.com","telephone":"+32 478 654 321","date_naissance":"22/07/1989","historique":df2,"s_mutans":1.2,"p_gingivalis":0.1,"diversite":82,"code_patient":"OB-P002"}
    df3=pd.DataFrame({"Date":["18/02/2025"],"Acte / Test":["Examen Initial"],"S. mutans (%)":[6.5],"P. gingiv. (%)":[1.8],"Diversite (%)":[38],"Status":["Alerte"]})
    patients["Pierre Bernard"]={"id":"P003","nom":"Pierre Bernard","age":58,"email":"pierre.bernard@email.com","telephone":"+32 495 789 012","date_naissance":"03/11/1966","historique":df3,"s_mutans":6.5,"p_gingivalis":1.8,"diversite":38,"code_patient":"OB-P003"}
    return patients

# ── INIT SESSION ──────────────────────────────────────────
for key,val in [("mode","choix"),("connecte",False),("patient_sel","Jean Dupont"),("vue","dashboard"),("patient_connecte",None)]:
    if key not in st.session_state: st.session_state[key]=val
if "patients"        not in st.session_state: st.session_state.patients=donnees_initiales()
if "anamnes"         not in st.session_state: st.session_state.anamnes={}
if "twins"           not in st.session_state: st.session_state.twins={}
if "onboarding_done" not in st.session_state: st.session_state.onboarding_done=False
if "onboarding_step" not in st.session_state: st.session_state.onboarding_step=1
if "rgpd_accepted"   not in st.session_state: st.session_state.rgpd_accepted=False
if "lang"            not in st.session_state: st.session_state.lang="fr"
if "dark_mode"       not in st.session_state: st.session_state.dark_mode=False
if "notifs_read"     not in st.session_state: st.session_state.notifs_read=set()

# ============================================================
# ÉCRAN D'ACCUEIL
# ============================================================
if st.session_state.mode=="choix":
    st.markdown("""<style>.main{background:#f6f8fb;}.card{background:white;padding:26px;border-radius:18px;border:1px solid #e6eaf0;transition:all 0.2s;}.card:hover{border-color:#c9d3df;transform:translateY(-3px);}.footer{text-align:center;font-size:12px;color:#8892a0;margin-top:50px;}</style>""",unsafe_allow_html=True)
    lh=logo_img(400)
    st.markdown(f"""<div style="background:linear-gradient(135deg,rgba(15,42,68,0.97),rgba(31,78,121,0.97));padding:40px 44px;border-radius:24px;color:white;margin-bottom:32px;box-shadow:0 12px 40px rgba(10,22,40,0.18);">
        <div style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;">
            <div style="background:white;padding:12px;border-radius:14px;">{lh}</div>
            <div><div style="font-family:'DM Serif Display',serif;font-size:2.2rem;">OralBiome</div>
            <div style="opacity:0.75;font-size:1rem;margin-top:6px;">Intelligence artificielle · Microbiome oral · Twin numérique dentaire · Prévention systémique</div>
            <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap;">
                <span style="background:rgba(255,255,255,0.15);padding:4px 12px;border-radius:20px;font-size:0.8rem;">🤖 IA Claude</span>
                <span style="background:rgba(255,255,255,0.15);padding:4px 12px;border-radius:20px;font-size:0.8rem;">🦷 Twin 3D</span>
                <span style="background:rgba(255,255,255,0.15);padding:4px 12px;border-radius:20px;font-size:0.8rem;">🌐 FR · EN · NL</span>
                <span style="background:rgba(255,255,255,0.15);padding:4px 12px;border-radius:20px;font-size:0.8rem;">📊 NHANES n=8 237</span>
                <span style="background:rgba(255,255,255,0.15);padding:4px 12px;border-radius:20px;font-size:0.8rem;">🔒 RGPD</span>
            </div></div></div></div>""",unsafe_allow_html=True)
    col1,col2,col3=st.columns(3,gap="large")
    with col1:
        st.markdown('<div class="card"><div style="font-size:18px;font-weight:600;margin-bottom:10px;">🩺 Espace Praticien</div><div style="font-size:14px;color:#5f6b7a;line-height:1.5;">Dashboard analytique · Gestion patients · IA clinique · Twin numérique 3D · Simulateur thérapeutique</div></div>',unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button(t("home_login"),use_container_width=True,type="primary"): st.session_state.mode="praticien"; st.rerun()
    with col2:
        st.markdown('<div class="card"><div style="font-size:18px;font-weight:600;margin-bottom:10px;">👤 Espace Patient</div><div style="font-size:14px;color:#5f6b7a;line-height:1.5;">Mon rapport personnalisé · Risques systémiques · Mon twin dentaire · Plan d\'action · Partager</div></div>',unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button(t("home_access"),use_container_width=True): st.session_state.mode="patient"; st.rerun()
    with col3:
        st.markdown('<div class="card"><div style="font-size:18px;font-weight:600;margin-bottom:10px;">ℹ️ À propos</div><div style="font-size:14px;color:#5f6b7a;line-height:1.5;">OralBiome corrèle le microbiote oral avec les risques systémiques. Benchmarking NHANES n=8 237.</div><div style="margin-top:16px;font-size:0.82rem;color:#1f4e79;font-weight:500;">contact@oralbiome.com</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="footer">© 2026 OralBiome — Clinical Intelligence Platform · FR · EN · NL · 🔒 RGPD · 🦷 Twin Numérique</div>',unsafe_allow_html=True)

# ============================================================
# PORTAIL PATIENT
# ============================================================
elif st.session_state.mode=="patient":
    if not st.session_state.rgpd_accepted:
        render_rgpd_banner(); st.stop()
    if st.session_state.patient_connecte is None:
        col1,col2,col3=st.columns([1,1,1])
        with col2:
            st.markdown("<br>",unsafe_allow_html=True)
            if LOGO_B64: st.markdown(f"<div style='text-align:center;'>{logo_img(width=340)}</div>",unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center;color:#1a3a5c;'>Espace Patient</h3>",unsafe_allow_html=True)
            st.markdown("---")
            code=st.text_input("Votre code patient",placeholder="Ex: OB-P001")
            if st.button("Accéder à mon dossier",use_container_width=True,type="primary"):
                found=next((n for n,d in st.session_state.patients.items() if d.get("code_patient")==code.strip()),None)
                if found: st.session_state.patient_connecte=found; st.rerun()
                else: st.error("Code patient invalide.")
            if st.button(t("pat_back"),use_container_width=True): st.session_state.mode="choix"; st.rerun()
            st.caption("Codes démo : OB-P001 · OB-P002 · OB-P003")
    else:
        patient=st.session_state.patients[st.session_state.patient_connecte]
        sm=patient["s_mutans"]; pg=patient["p_gingivalis"]; div=patient["diversite"]
        r_carieux=t("metric_high") if sm>3.0 else t("metric_low")
        r_paro=t("metric_high") if pg>0.5 else t("metric_low")
        en_alerte=sm>3.0 or pg>0.5 or div<50
        plan=generer_recommandations(sm,pg,div); scores_sys=calculer_score_systemique(sm,pg,div)
        if LOGO_B64: st.sidebar.markdown(f"<div style='text-align:center;padding:6px 0;'>{logo_img(width=120)}</div>",unsafe_allow_html=True)
        st.sidebar.markdown(f"### {t('pat_hello')} {patient['nom'].split()[0]}")
        st.sidebar.markdown(f"Code : `{patient['code_patient']}`")
        st.sidebar.markdown(f"**{'🔴 En alerte' if en_alerte else '🟢 Équilibré'}**")
        st.sidebar.markdown(f"{t('pat_next_ctrl')} : **{plan['suivi_semaines']} {t('pat_weeks')}**")
        st.sidebar.markdown("---")
        render_lang_selector(); render_dark_mode_toggle()
        st.sidebar.markdown("---")
        if st.sidebar.button(t("pat_logout")): st.session_state.patient_connecte=None; st.rerun()
        if st.sidebar.button(t("pat_back")): st.session_state.patient_connecte=None; st.session_state.mode="choix"; st.rerun()
        lh=logo_img(120,"margin-bottom:8px;filter:brightness(0) invert(1);opacity:0.9;")
        st.markdown(f'<div class="patient-header">{lh}<h2 style="margin-top:4px;">{t("pat_hello")} {patient["nom"]} !</h2><p>Rapport microbiome oral personnalisé · {date.today().strftime("%d/%m/%Y")}</p></div>',unsafe_allow_html=True)
        c1,c2,c3=st.columns(3)
        c1.metric(t("metric_caries"),r_carieux); c2.metric(t("metric_paro"),r_paro); c3.metric(t("metric_diversity"),f"{div}/100")
        st.markdown("---")
        tp1,tp2,tp3,tp4,tp5,tp6,tp7,tp8,tp9=st.tabs([
            t("pat_profile"),t("pat_systemic"),t("pat_photo"),t("pat_actions"),
            t("pat_nutrition"),t("pat_anamnes"),t("pat_twin"),t("pat_share"),t("pat_pdf")
        ])
        with tp1:
            st.header("📊 Mon Profil Bactérien")
            if en_alerte: st.warning(f"**{plan['profil_label']}** — {plan['profil_description']}")
            else: st.success(f"**{plan['profil_label']}** — {plan['profil_description']}")
            st.markdown("---"); st.markdown("#### 🌍 Votre Diversité Microbienne vs la Population")
            render_diversity_benchmark(div,age=patient.get("age"),context="patient")
            if not patient["historique"].empty:
                st.markdown("---"); st.markdown("#### 📅 Historique"); st.dataframe(patient["historique"],use_container_width=True,hide_index=True)
        with tp2:
            st.header("🧬 Risques Systémiques"); st.markdown("*Corrélations entre votre microbiote oral et vos risques de santé généraux.*"); st.markdown("---")
            for key,data in scores_sys.items():
                score=data["score"]; level=data["level"]; score_css="score-high" if level=="high" else "score-med" if level=="med" else "score-low"
                cr2,cc2=st.columns([1,6])
                with cr2: st.markdown(f"<div class='score-ring {score_css}'>{score}</div>",unsafe_allow_html=True)
                with cc2:
                    st.markdown(f'<div class="systemic-card"><div class="systemic-title">{data["icon"]} {data["label"]}</div><div style="font-size:0.85rem;color:#4b5563;">{data["description"]}</div><div style="font-size:0.75rem;color:#9ca3af;margin-top:6px;"><em>Réf : {data["references"]}</em></div></div>',unsafe_allow_html=True)
                    with st.expander("Voir les recommandations →"):
                        for action in data["actions"]: st.markdown(f"- {action}")
                st.markdown("")
            st.info("⚕️ Ces scores sont des estimations épidémiologiques. Ne constituent pas un diagnostic médical.")
        with tp3:
            st.header("📸 Analyse Photo"); st.caption("📌 Bonne lumière, bouche ouverte, photo nette. JPEG ou PNG."); st.markdown("---")
            if not ANTHROPIC_API_KEY: st.warning("⚠️ Configurez `ANTHROPIC_API_KEY` dans `st.secrets`.")
            else:
                uploaded=st.file_uploader("Photo bouche",type=["jpg","jpeg","png"],label_visibility="collapsed")
                if uploaded:
                    img_bytes=uploaded.read(); mime="image/png" if uploaded.name.endswith(".png") else "image/jpeg"
                    ci2,cr3=st.columns([1,2])
                    with ci2: st.image(img_bytes,use_container_width=True)
                    with cr3:
                        with st.spinner("🔍 Analyse IA en cours..."): result=analyser_photo_bouche(img_bytes,mime)
                        render_photo_analysis(result)
        with tp4:
            st.header("🚨 Mes Actions Prioritaires")
            for i,p in enumerate(plan["priorites"]):
                urg=p["urgence"]; badge="URGENT" if urg=="Elevee" else "MODÉRÉ" if urg=="Moderee" else "ROUTINE"
                css="reco-red" if urg=="Elevee" else "reco-orange" if urg=="Moderee" else "reco-green"
                st.markdown(f"### {p['icone']} Action {i+1} — {p['titre']} `{badge}`")
                st.markdown(f"<div class='reco-card {css}'><em>{p['explication']}</em></div>",unsafe_allow_html=True)
                for action in p["actions"]: st.markdown(f"- {action}")
                st.markdown("---")
        with tp5:
            cf,ce=st.columns(2)
            with cf:
                st.markdown("### ✅ Favoriser")
                for a in plan["aliments_favoriser"]: st.markdown(f"<span class='pill-green'>{a}</span>",unsafe_allow_html=True)
            with ce:
                st.markdown("### ❌ Limiter")
                for a in plan["aliments_eviter"]: st.markdown(f"<span class='pill-red'>{a}</span>",unsafe_allow_html=True)
            st.markdown("---"); st.header("💊 Probiotiques Recommandés")
            for prob in plan["probiotiques"]:
                with st.expander(f"🧫 {prob['nom']}",expanded=True):
                    cp1,cp2=st.columns(2)
                    with cp1: st.markdown(f"**Forme :** {prob['forme']}\n\n**Durée :** {prob['duree']}")
                    with cp2: st.markdown(f"**Bénéfice :** {prob['benefice']}\n\n**Produits :** `{prob['marques']}`")
        with tp6:
            st.header("📋 Mon Questionnaire de Santé")
            anamnes=get_anamnes(st.session_state.patient_connecte)
            if anamnes.get("completed_at"): st.success(f"✅ Questionnaire complété le {anamnes['completed_at'][:10]}")
            else: st.warning("⚠️ Questionnaire non encore rempli.")
            with st.form("form_anamnes_patient"):
                st.markdown("### 🏥 Antécédents Médicaux")
                a1,a2,a3=st.columns(3)
                with a1: diabete=st.checkbox("Diabète",value=bool(anamnes.get("diabete",0))); hypertension=st.checkbox("Hypertension",value=bool(anamnes.get("hypertension",0)))
                with a2: maladie_cardio=st.checkbox("Maladie cardiovasculaire",value=bool(anamnes.get("maladie_cardio",0))); osteoporose=st.checkbox("Ostéoporose",value=bool(anamnes.get("osteoporose",0)))
                with a3: cancer=st.checkbox("Cancer",value=bool(anamnes.get("cancer",0)))
                autre_antecedent=st.text_input("Autre condition",value=anamnes.get("autre_antecedent",""),placeholder="Ex: hypothyroïdie, asthme...")
                st.markdown("---"); st.markdown("### 💊 Médicaments")
                prend_medicaments=st.checkbox("Je prends actuellement des médicaments",value=bool(anamnes.get("prend_medicaments",0)))
                liste_medicaments=""; antibiotiques_recents=False
                if prend_medicaments:
                    liste_medicaments=st.text_area("Liste",value=anamnes.get("liste_medicaments",""),placeholder="Ex: Metformine 500mg...",height=80)
                    antibiotiques_recents=st.checkbox("Antibiotiques dans les 3 derniers mois",value=bool(anamnes.get("antibiotiques_recents",0)))
                st.markdown("---"); st.markdown("### 🌿 Habitudes de Vie")
                h1,h2=st.columns(2)
                with h1:
                    fumeur=st.selectbox("Tabac",["non","occasionnel","regulier"],index=["non","occasionnel","regulier"].index(anamnes.get("fumeur","non")),format_func=lambda x:{"non":"🚭 Non-fumeur","occasionnel":"🚬 Occasionnel","regulier":"🚬 Régulier"}[x])
                    alcool=st.selectbox("Alcool",["non","modere","eleve"],index=["non","modere","eleve"].index(anamnes.get("alcool","non")),format_func=lambda x:{"non":"✅ Pas ou rarement","modere":"🍷 Modérée","eleve":"⚠️ Élevée"}[x])
                with h2:
                    alimentation_type=st.selectbox("Alimentation",["omnivore","vegetarien","vegan","paleo","mediterraneen","autre"],index=["omnivore","vegetarien","vegan","paleo","mediterraneen","autre"].index(anamnes.get("alimentation_type","omnivore")),format_func=lambda x:{"omnivore":"🍖 Omnivore","vegetarien":"🥗 Végétarien","vegan":"🌱 Vegan","paleo":"🥩 Paléo","mediterraneen":"🫒 Méditerranéen","autre":"🍽️ Autre"}[x])
                    sucres_eleves=st.checkbox("Consommation élevée de sucres",value=bool(anamnes.get("sucres_eleves",0)))
                st.markdown("---"); st.markdown("### 🦷 Hygiène Buccale")
                hb1,hb2,hb3=st.columns(3)
                with hb1: brosse_dents_freq=st.selectbox("Brossage",["1x/jour","2x/jour","3x/jour","moins d'1x/jour"],index=["1x/jour","2x/jour","3x/jour","moins d'1x/jour"].index(anamnes.get("brosse_dents_freq","2x/jour")))
                with hb2: fil_dentaire=st.checkbox("Fil dentaire quotidien",value=bool(anamnes.get("fil_dentaire",0)))
                with hb3: bain_bouche=st.checkbox("Bain de bouche régulier",value=bool(anamnes.get("bain_bouche",0)))
                st.markdown("---"); st.markdown("### 🔍 Symptômes Actuels")
                s1,s2,s3,s4=st.columns(4)
                with s1: saignement=st.checkbox("🩸 Saignement gencives",value=bool(anamnes.get("saignement_gencives",0)))
                with s2: douleur=st.checkbox("😣 Douleur dentaire",value=bool(anamnes.get("douleur_dentaire",0)))
                with s3: sensibilite=st.checkbox("❄️ Sensibilité",value=bool(anamnes.get("sensibilite",0)))
                with s4: mauvaise_hal=st.checkbox("💨 Mauvaise haleine",value=bool(anamnes.get("mauvaise_haleine",0)))
                st.markdown("<br>",unsafe_allow_html=True)
                if st.form_submit_button("💾 Sauvegarder",use_container_width=True,type="primary"):
                    save_anamnes(st.session_state.patient_connecte,{"diabete":int(diabete),"hypertension":int(hypertension),"maladie_cardio":int(maladie_cardio),"osteoporose":int(osteoporose),"cancer":int(cancer),"autre_antecedent":autre_antecedent,"prend_medicaments":int(prend_medicaments),"liste_medicaments":liste_medicaments,"antibiotiques_recents":int(antibiotiques_recents),"fumeur":fumeur,"alcool":alcool,"brosse_dents_freq":brosse_dents_freq,"fil_dentaire":int(fil_dentaire),"bain_bouche":int(bain_bouche),"sucres_eleves":int(sucres_eleves),"alimentation_type":alimentation_type,"saignement_gencives":int(saignement),"douleur_dentaire":int(douleur),"sensibilite":int(sensibilite),"mauvaise_haleine":int(mauvaise_hal)})
                    st.success("✅ Questionnaire sauvegardé !"); st.rerun()
        with tp7:
            render_twin_patient(patient)
        with tp8:
            st.header("📤 Partager mon rapport")
            st.markdown("Partagez votre rapport avec votre médecin traitant.")
            token=hashlib.md5(f"{patient['id']}{date.today()}".encode()).hexdigest()[:12].upper()
            share_url=f"https://app.oralbiome.com/share/{patient['id']}-{token}"
            tab_email,tab_lien=st.tabs(["📧 Par email","🔗 Lien sécurisé"])
            with tab_email:
                with st.form("form_share"):
                    dest_email=st.text_input("Email du destinataire",placeholder="medecin@cabinet.fr")
                    dest_nom=st.text_input("Nom du destinataire",placeholder="Dr. Martin")
                    if st.form_submit_button("📨 Envoyer",use_container_width=True,type="primary"):
                        if not dest_email or "@" not in dest_email: st.error("Email invalide.")
                        else: st.session_state[f"share_{patient['id']}"]={"email":dest_email,"nom":dest_nom or "Votre médecin","date":date.today().strftime("%d/%m/%Y")}; st.rerun()
                si=st.session_state.get(f"share_{patient['id']}")
                if si: st.success(f"✅ Rapport envoyé à **{si['nom']}** ({si['email']}) le {si['date']}")
            with tab_lien:
                st.markdown(f"""<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:16px 20px;margin:12px 0;">
                    <div style="font-size:0.78rem;color:#0369a1;font-weight:600;margin-bottom:6px;">🔗 Lien sécurisé (valable 7 jours)</div>
                    <div style="font-family:monospace;font-size:0.85rem;background:white;padding:8px 12px;border-radius:6px;border:1px solid #dbeafe;word-break:break-all;">{share_url}</div>
                    <div style="font-size:0.78rem;color:#0369a1;margin-top:8px;">🔒 Lien en lecture seule · Expire dans 7 jours</div>
                </div>""",unsafe_allow_html=True)
                if st.button("📋 Copier le lien",use_container_width=True): st.success("✅ Lien copié !")
        with tp9:
            st.header("📥 Rapport PDF Complet")
            if st.button("Générer mon rapport PDF",type="primary",use_container_width=True):
                with st.spinner("Génération en cours..."):
                    pdf=generer_pdf(patient["nom"],r_carieux,r_paro,div,patient["historique"],plan,scores_sys)
                st.download_button("📥 Télécharger mon Rapport OralBiome (PDF)",data=pdf,file_name=f"OralBiome_MonRapport_{patient['id']}.pdf",mime="application/pdf",type="primary",use_container_width=True)

# ============================================================
# PORTAIL PRATICIEN
# ============================================================
elif st.session_state.mode=="praticien":
    if not st.session_state.connecte:
        if not st.session_state.rgpd_accepted: render_rgpd_banner(); st.stop()
        col1,col2,col3=st.columns([1,1,1])
        with col2:
            st.markdown("<br>",unsafe_allow_html=True)
            if LOGO_B64: st.markdown(f"<div style='text-align:center;'>{logo_img(width=340)}</div>",unsafe_allow_html=True)
            st.markdown(f"<h4 style='text-align:center;color:#64748b;'>{t('prat_login_title')}</h4>",unsafe_allow_html=True)
            st.markdown("---")
            email=st.text_input(t("prat_email")); mdp=st.text_input(t("prat_password"),type="password")
            if st.button(t("prat_connect"),use_container_width=True,type="primary"):
                if email=="contact@oralbiome.com" and mdp=="mvp2024":
                    st.session_state.connecte=True
                    if not st.session_state.onboarding_done: st.session_state.onboarding_step=1
                    st.rerun()
                else: st.error("Identifiants incorrects. Demo : contact@oralbiome.com / mvp2024")
            if st.button(t("prat_back"),use_container_width=True): st.session_state.mode="choix"; st.rerun()
    else:
        if not st.session_state.onboarding_done: render_onboarding(); st.stop()
        # ── SIDEBAR ──
        if LOGO_B64: st.sidebar.markdown(f"<div style='text-align:center;padding:8px 0 4px 0;'>{logo_img(width=140)}</div>",unsafe_allow_html=True)
        st.sidebar.markdown("---")
        sc1,sc2,sc3=st.sidebar.columns(3)
        with sc1:
            if st.button("📊",use_container_width=True,help="Dashboard"): st.session_state.vue="dashboard"; st.rerun()
        with sc2:
            if st.button("👥",use_container_width=True,help="Patients"): st.session_state.vue="liste"; st.rerun()
        with sc3:
            if st.button("➕",use_container_width=True,help="Nouveau"): st.session_state.vue="nouveau"; st.rerun()
        st.sidebar.markdown("---")
        nb_patients=len(st.session_state.patients); nb_alertes=sum(1 for p in st.session_state.patients.values() if p["s_mutans"]>3.0 or p["p_gingivalis"]>0.5 or p["diversite"]<50); nb_alertes_actives=len(calculer_alertes(st.session_state.patients))
        ms1,ms2,ms3=st.sidebar.columns(3); ms1.metric("Patients",nb_patients); ms2.metric("Alertes",nb_alertes); ms3.metric("🔔",nb_alertes_actives)
        st.sidebar.markdown("---")
        render_lang_selector(); render_dark_mode_toggle(); render_notifications(st.session_state.patients)
        st.sidebar.markdown("---")
        rech=st.sidebar.text_input("🔍 Rechercher...",placeholder="Nom ou ID")
        pf={n:d for n,d in st.session_state.patients.items() if rech.lower() in n.lower() or rech.lower() in d["id"].lower()} if rech else st.session_state.patients
        for nom,data in pf.items():
            icon="🔴" if (data["s_mutans"]>3.0 or data["p_gingivalis"]>0.5 or data["diversite"]<50) else "🟢"
            is_sel=nom==st.session_state.patient_sel
            if st.sidebar.button(f"{icon} {data['id']} — {nom}",use_container_width=True,type="primary" if is_sel else "secondary"):
                st.session_state.patient_sel=nom; st.session_state.vue="dossier"; st.rerun()
        st.sidebar.markdown("---")
        if st.sidebar.button(f"🚪 {t('prat_disconnect')}",use_container_width=True): st.session_state.connecte=False; st.rerun()
        if st.sidebar.button(t("prat_back"),use_container_width=True): st.session_state.connecte=False; st.session_state.mode="choix"; st.rerun()

        # ── VUES ──
        if st.session_state.vue=="dashboard":
            render_dashboard(st.session_state.patients)
        elif st.session_state.vue=="liste":
            st.title("👥 Gestion des Patients")
            lf1,_,lf3=st.columns(3)
            with lf1: filtre=st.selectbox("Filtrer",["Tous","Alerte uniquement","Stable uniquement"])
            with lf3:
                if st.button("➕ Nouveau Patient",type="primary"): st.session_state.vue="nouveau"; st.rerun()
            donnees=[]
            for nom,data in st.session_state.patients.items():
                ea=data["s_mutans"]>3.0 or data["p_gingivalis"]>0.5 or data["diversite"]<50
                if filtre=="Alerte uniquement" and not ea: continue
                if filtre=="Stable uniquement" and ea: continue
                sys_s=calculer_score_systemique(data["s_mutans"],data["p_gingivalis"],data["diversite"]); top=max(sys_s.items(),key=lambda x:x[1]["score"])
                donnees.append({"ID":data["id"],"Nom":nom,"Âge":data["age"],"Risque Carieux":"⚠️ Élevé" if data["s_mutans"]>3.0 else "✅ Faible","Risque Parodontal":"⚠️ Élevé" if data["p_gingivalis"]>0.5 else "✅ Faible","Diversité":f"{data['diversite']}/100","Risque Principal":f"{top[1]['icon']} {top[1]['label']} ({top[1]['score']}/100)","Statut":"🔴 Alerte" if ea else "🟢 Stable"})
            if donnees: st.dataframe(pd.DataFrame(donnees),use_container_width=True,hide_index=True)
        elif st.session_state.vue=="nouveau":
            st.title("➕ Nouveau Patient")
            with st.form("form_nouveau"):
                nc1,nc2=st.columns(2)
                with nc1: nn=st.text_input("Nom complet *"); ne=st.text_input("Email"); nd_nais=st.date_input("Date de naissance",value=date(1985,1,1))
                with nc2: na=st.number_input("Âge",1,120,35); nt=st.text_input("Téléphone")
                st.markdown("### Première Analyse")
                nc3,nc4,nc5=st.columns(3)
                with nc3: is_=st.number_input("S. mutans (%)",0.0,10.0,2.0,step=0.1)
                with nc4: ip_=st.number_input("P. gingivalis (%)",0.0,5.0,0.2,step=0.1)
                with nc5: id_=st.number_input("Diversité (%)",0,100,70)
                aj=st.checkbox("Enregistrer comme examen initial",value=True)
                if st.form_submit_button("Créer le dossier",use_container_width=True,type="primary"):
                    if not nn.strip(): st.error("Le nom est obligatoire.")
                    elif nn in st.session_state.patients: st.error("Ce patient existe déjà.")
                    else:
                        nid=f"P{str(len(st.session_state.patients)+1).zfill(3)}"
                        df_n=pd.DataFrame(columns=["Date","Acte / Test","S. mutans (%)","P. gingiv. (%)","Diversite (%)","Status"])
                        if aj:
                            s="Alerte" if is_>3.0 or ip_>0.5 or id_<50 else "Stable"; df_n.loc[0]=[date.today().strftime("%d/%m/%Y"),"Examen Initial",is_,ip_,id_,s]
                        st.session_state.patients[nn]={"id":nid,"nom":nn,"age":na,"email":ne,"telephone":nt,"date_naissance":nd_nais.strftime("%d/%m/%Y"),"historique":df_n,"s_mutans":is_ if aj else 0.0,"p_gingivalis":ip_ if aj else 0.0,"diversite":id_ if aj else 70,"code_patient":f"OB-{nid}"}
                        st.session_state.patient_sel=nn; st.session_state.vue="dossier"; st.success(f"Dossier créé ! Code patient : **OB-{nid}**"); st.rerun()
        else:
            patient=st.session_state.patients.get(st.session_state.patient_sel)
            if not patient: st.error("Patient introuvable.")
            else:
                sm=patient["s_mutans"]; pg=patient["p_gingivalis"]; div=patient["diversite"]
                r_carieux="Eleve" if sm>3.0 else "Faible"; r_paro="Eleve" if pg>0.5 else "Faible"
                en_alerte=r_carieux=="Eleve" or r_paro=="Eleve" or div<50
                plan=generer_recommandations(sm,pg,div); scores_sys=calculer_score_systemique(sm,pg,div)
                badge="🔴 En Alerte" if en_alerte else "🟢 Stable"
                st.markdown(f"## 🦷 {patient['nom']}  `{patient['id']}`  —  {badge}")
                st.caption(f"Âge : {patient['age']} ans  ·  {patient['email']}  ·  Code : **{patient.get('code_patient','')}**")
                st.markdown("---")
                m1,m2,m3,m4,m5=st.columns(5)
                m1.metric("Risque Carieux",r_carieux); m2.metric("Risque Parodontal",r_paro); m3.metric("Diversité",f"{div}/100"); m4.metric("Visites",len(patient["historique"]))
                top_sys=max(scores_sys.items(),key=lambda x:x[1]["score"]); m5.metric("Risque Sys.",f"{top_sys[1]['score']}/100",top_sys[1]["icon"])
                st.markdown("---")
                if en_alerte: st.warning(f"**{plan['profil_label']}** — {plan['profil_description']}")
                else: st.success(f"**{plan['profil_label']}** — {plan['profil_description']}")
                st.info(f"Code patient : **{patient.get('code_patient','')}** — À communiquer au patient.")
                st.markdown("---")
                anamnes_p=get_anamnes(st.session_state.patient_sel)
                if anamnes_p.get("completed_at"):
                    with st.expander(f"📋 Anamnèse — complétée le {anamnes_p['completed_at'][:10]}"):
                        ac1,ac2,ac3=st.columns(3)
                        with ac1:
                            st.markdown("**🏥 Antécédents**")
                            for k,l in [("diabete","🩸 Diabète"),("hypertension","❤️ Hypertension"),("maladie_cardio","🫀 Cardiovasculaire"),("osteoporose","🦴 Ostéoporose"),("cancer","⚠️ Cancer")]:
                                if anamnes_p.get(k): st.markdown(f"- {l}")
                            if anamnes_p.get("autre_antecedent"): st.markdown(f"- 📌 {anamnes_p['autre_antecedent']}")
                        with ac2:
                            st.markdown("**🌿 Habitudes**")
                            st.markdown(f"- Tabac : `{anamnes_p.get('fumeur','?')}`"); st.markdown(f"- Alcool : `{anamnes_p.get('alcool','?')}`"); st.markdown(f"- Alimentation : `{anamnes_p.get('alimentation_type','?')}`"); st.markdown(f"- Brossage : `{anamnes_p.get('brosse_dents_freq','?')}`")
                            if anamnes_p.get("sucres_eleves"): st.markdown("- ⚠️ Sucres élevés")
                        with ac3:
                            st.markdown("**🔍 Symptômes**")
                            for k,l in [("saignement_gencives","🩸 Saignement"),("douleur_dentaire","😣 Douleur"),("sensibilite","❄️ Sensibilité"),("mauvaise_haleine","💨 Haleine"),("antibiotiques_recents","💊 Antibiotiques récents")]:
                                if anamnes_p.get(k): st.markdown(f"- {l}")
                else: st.caption("📋 Anamnèse non encore remplie par le patient.")

                tab1,tab2,tab3,tab4,tab5,tab6=st.tabs([
                    "🧬 Risques Systémiques","🚨 Plan d'Action","🔬 Simulateur",
                    "📸 Analyse Photo","📂 Historique & PDF","🦷 Twin Numérique"
                ])
                with tab1:
                    st.header("🧬 Corrélations Microbiome → Risques Systémiques")
                    st.markdown("#### 🌍 Benchmark Diversité — NHANES (n=8 237)")
                    render_diversity_benchmark(div,age=patient.get("age"),context="praticien"); st.markdown("---")
                    rows2=[]
                    for key,data in scores_sys.items():
                        ll="🔴 Élevé" if data["level"]=="high" else "🟡 Modéré" if data["level"]=="med" else "🟢 Faible"
                        rows2.append({"Pathologie":f"{data['icon']} {data['label']}","Score":data["score"],"Niveau":ll,"Action":data["actions"][0] if data["actions"] else "-"})
                    st.dataframe(pd.DataFrame(rows2),use_container_width=True,hide_index=True); st.markdown("---")
                    for key,data in scores_sys.items():
                        if data["level"]=="high":
                            c1d,c2d=st.columns([1,6])
                            with c1d: st.markdown(f"<div class='score-ring score-high'>{data['score']}</div>",unsafe_allow_html=True)
                            with c2d:
                                st.markdown(f"**{data['icon']} {data['label']}**"); st.markdown(f"*{data['description']}*")
                                with st.expander("Protocole clinique"):
                                    for action in data["actions"]: st.markdown(f"- {action}")
                                    st.caption(f"Réf : {data['references']}")
                            st.markdown("")
                with tab2:
                    st.header("Plan d'Action & Recommandations")
                    for i,p in enumerate(plan["priorites"]):
                        urg=p["urgence"]; bu="URGENT" if urg=="Elevee" else "MODÉRÉ" if urg=="Moderee" else "ROUTINE"
                        css="reco-red" if urg=="Elevee" else "reco-orange" if urg=="Moderee" else "reco-green"
                        st.markdown(f"#### {p['icone']} Priorité {i+1} — {p['titre']} `{bu}`")
                        st.markdown(f"<div class='reco-card {css}'><em>{p['explication']}</em></div>",unsafe_allow_html=True)
                        for action in p["actions"]: st.markdown(f"- {action}")
                        st.markdown("---")
                with tab3:
                    st.markdown("""<div style="background:linear-gradient(135deg,#0a1628,#1a3a5c);border-radius:14px;padding:20px 28px;margin-bottom:20px;">
                        <h3 style="color:#fff;margin:0;font-family:'DM Serif Display',serif;">🔬 Simulateur d'Impact Thérapeutique</h3>
                        <p style="color:rgba(255,255,255,0.65);margin:6px 0 0 0;font-size:0.9rem;">Ajustez les biomarqueurs et visualisez l'impact en temps réel.</p></div>""",unsafe_allow_html=True)
                    cs,cr=st.columns([1,2])
                    with cs:
                        st.markdown("#### ⚙️ Biomarqueurs")
                        sim_mutans=st.slider("S. mutans (%)",0.0,10.0,float(sm),step=0.1); sim_paro=st.slider("P. gingivalis (%)",0.0,3.0,float(pg),step=0.1); sim_div=st.slider("Diversité",0,100,int(div),step=1)
                        st.markdown("---"); mois_proj=st.select_slider("Horizon",options=[1,2,3,6,12],value=3,format_func=lambda x:f"{x} mois")
                        st.markdown("---")
                        wp=st.checkbox("Probiotiques oraux",value=True); wd=st.checkbox("Détartrage/surfaçage",value=False); wn=st.checkbox("Plan nutritionnel",value=False)
                        boost=1.0+(0.25 if wp else 0)+(0.40 if wd else 0)+(0.20 if wn else 0)
                    with cr:
                        sa=calculer_score_systemique(sm,pg,div); ss=calculer_score_systemique(sim_mutans,sim_paro,sim_div)
                        st.markdown("#### 📊 Avant → Après")
                        h1s,h2s,h3s=st.columns([2,1,1]); h1s.markdown("**Pathologie**"); h2s.markdown("**Actuel**"); h3s.markdown("**Simulé**")
                        st.markdown("<hr style='margin:4px 0 10px 0;'>",unsafe_allow_html=True)
                        for key,act in sa.items():
                            sim2=ss[key]; gain=act["score"]-sim2["score"]; cn2,ca2,cs2=st.columns([2,1,1])
                            ac_colors={"high":"#e11d48","med":"#d97706","low":"#16a34a"}; arrow="↓" if gain>0 else "↑" if gain<0 else "→"; acol="#16a34a" if gain>0 else "#e11d48" if gain<0 else "#6b7280"
                            cn2.markdown(f"{act['icon']} **{act['label']}**"); ca2.markdown(f"<span style='color:{ac_colors[act['level']]};font-weight:700;font-size:1.1rem;'>{act['score']}</span>/100",unsafe_allow_html=True); cs2.markdown(f"<span style='color:{ac_colors[sim2['level']]};font-weight:700;font-size:1.1rem;'>{sim2['score']}</span><span style='color:{acol};margin-left:6px;'>{arrow} {abs(gain):+.0f}</span>",unsafe_allow_html=True)
                        st.markdown("<hr style='margin:10px 0;'>",unsafe_allow_html=True)
                        avg_a=sum(s["score"] for s in sa.values())/len(sa); avg_s=sum(s["score"] for s in ss.values())/len(ss); gg=avg_a-avg_s; gp=round(gg/avg_a*100) if avg_a>0 else 0; gc="#16a34a" if gg>0 else "#e11d48" if gg<0 else "#6b7280"
                        st.markdown(f'<div style="background:linear-gradient(135deg,{gc}15,{gc}08);border:1.5px solid {gc}40;border-radius:12px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;"><div><div style="font-size:0.8rem;color:#6b7280;font-weight:600;text-transform:uppercase;">Réduction Risque Global</div><div style="font-family:\'DM Serif Display\',serif;font-size:2rem;color:{gc};">{"↓" if gg>0 else "↑"} {abs(gp)}%</div></div><div style="text-align:right;"><div style="font-size:0.85rem;color:#374151;">Score : <b>{avg_a:.0f}</b> → <b>{avg_s:.0f}</b></div><div style="font-size:0.75rem;color:#9ca3af;">Sur {mois_proj} mois</div></div></div>',unsafe_allow_html=True)
                        st.markdown(f"<br>#### 📈 Projection {mois_proj} mois")
                        proj={}
                        for key,act in sa.items():
                            cible=ss[key]["score"]; depart=act["score"]; serie=[]
                            for m in range(mois_proj+1):
                                prog=min(1.0,(m/mois_proj)**(1/boost)) if mois_proj>0 else 1.0; serie.append(round(depart+(cible-depart)*prog,1))
                            proj[act["label"][:18]]=serie
                        st.line_chart(pd.DataFrame(proj,index=[f"M{m}" for m in range(mois_proj+1)]),height=200)
                        if gp>=20: st.success(f"✅ Impact significatif — {gp}% de réduction en {mois_proj} mois.")
                        elif gp>=5: st.info(f"📉 Impact modéré — {gp}% estimé en {mois_proj} mois.")
                        elif gp<0: st.warning("⚠️ Ce scénario représente une dégradation.")
                with tab4:
                    st.header("📸 Analyse Visuelle IA")
                    if not ANTHROPIC_API_KEY: st.warning("Configurez `ANTHROPIC_API_KEY` dans `st.secrets`.")
                    else:
                        uploaded=st.file_uploader("Photo bouche patient",type=["jpg","jpeg","png"])
                        if uploaded:
                            img_bytes=uploaded.read(); mime="image/png" if uploaded.name.endswith(".png") else "image/jpeg"
                            ci2,cr3=st.columns([1,2])
                            with ci2: st.image(img_bytes,use_container_width=True)
                            with cr3:
                                with st.spinner("Analyse IA..."): result=analyser_photo_bouche(img_bytes,mime)
                                render_photo_analysis(result)
                with tab5:
                    if not patient["historique"].empty:
                        st.dataframe(patient["historique"],use_container_width=True,hide_index=True)
                        if len(patient["historique"])>1:
                            df_g=patient["historique"].copy(); df_g.index=range(len(df_g))
                            gc1,gc2=st.columns(2)
                            with gc1: st.line_chart(df_g[["S. mutans (%)","P. gingiv. (%)"]].astype(float))
                            with gc2:
                                dc=next((c for c in ["Diversite (%)","Diversité (%)"] if c in df_g.columns),None)
                                if dc: st.line_chart(df_g[[dc]].astype(float))
                    st.markdown("---"); st.header("Ajouter une Intervention")
                    with st.form("form_ajout"):
                        fa1,fa2,fa3=st.columns(3)
                        with fa1: nd=st.date_input("Date",date.today()); nact=st.selectbox("Intervention",["Examen Initial","Contrôle Microbiome","Détartrage","Soin Carie","Surfaçage","Probiotiques Prescrits","Autre"])
                        with fa2: ns=st.number_input("S. mutans (%)",0.0,10.0,float(sm),step=0.1); np_=st.number_input("P. gingivalis (%)",0.0,5.0,float(pg),step=0.1)
                        with fa3: nd2=st.number_input("Diversité (%)",0,100,int(div)); st.markdown("<br>"); sauver=st.form_submit_button("Sauvegarder",use_container_width=True,type="primary")
                        if sauver:
                            sv="Alerte" if ns>3.0 or np_>0.5 or nd2<50 else "Stable"
                            nl=pd.DataFrame({"Date":[nd.strftime("%d/%m/%Y")],"Acte / Test":[nact],"S. mutans (%)":[ns],"P. gingiv. (%)":[np_],"Diversite (%)":[nd2],"Status":[sv]})
                            st.session_state.patients[st.session_state.patient_sel]["historique"]=pd.concat([patient["historique"],nl],ignore_index=True)
                            st.session_state.patients[st.session_state.patient_sel]["s_mutans"]=ns; st.session_state.patients[st.session_state.patient_sel]["p_gingivalis"]=np_; st.session_state.patients[st.session_state.patient_sel]["diversite"]=nd2; st.success("Sauvegardé."); st.rerun()
                    st.markdown("---"); st.header("Rapport PDF Complet")
                    if st.button("Générer le rapport PDF",type="primary"):
                        with st.spinner("Génération..."):
                            pdf=generer_pdf(patient["nom"],r_carieux,r_paro,div,patient["historique"],plan,scores_sys)
                        st.download_button("📥 Télécharger le Rapport (PDF)",data=pdf,file_name=f"OralBiome_{patient['id']}_{patient['nom'].replace(' ','_')}.pdf",mime="application/pdf",type="primary",use_container_width=True)
                with tab6:
                    render_twin_praticien(patient)