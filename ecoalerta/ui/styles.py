import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

.stApp { font-family: 'Inter', sans-serif; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .eco-title, .eco-step-t, .eco-kpi-v,
.eco-meter-pct, .eco-hs-v { font-family: 'Plus Jakarta Sans', sans-serif; letter-spacing: -0.02em; }
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1320px; }
footer { visibility: hidden; }

.eco-hero { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1.2rem;
    padding: 1.5rem 1.9rem; border-radius: 22px; color: #fff; margin-bottom: 1.1rem;
    background: radial-gradient(900px 280px at 100% 0%, rgba(45,212,191,.38), transparent 60%),
                radial-gradient(500px 200px at 0% 100%, rgba(16,185,129,.25), transparent 60%),
                linear-gradient(120deg, #064e3b 0%, #0f766e 80%);
    box-shadow: 0 12px 32px rgba(6,78,59,.2); }
.eco-title { font-size: 1.85rem; font-weight: 800; line-height: 1.1; color: #fff; }
.eco-ver { font-size: .72rem; font-weight: 600; background: rgba(255,255,255,.2);
           padding: .15rem .55rem; border-radius: 999px; vertical-align: middle; margin-left: .4rem; }
.eco-hero p { margin: .35rem 0 0; font-size: .92rem; color: #d1fae5 !important; max-width: 560px; }
.eco-hstats { display: flex; gap: .7rem; flex-wrap: wrap; }
.eco-hs { background: rgba(255,255,255,.13); border: 1px solid rgba(255,255,255,.22); border-radius: 14px;
          padding: .6rem 1rem; min-width: 96px; text-align: center; backdrop-filter: blur(4px); }
.eco-hs-v { font-size: 1.5rem; font-weight: 800; line-height: 1; }
.eco-hs-l { font-size: .66rem; text-transform: uppercase; letter-spacing: .07em; opacity: .85; margin-top: .25rem; }

.eco-how { display: grid; grid-template-columns: repeat(3, 1fr); gap: .7rem; margin-bottom: .8rem; }
.eco-how div { border: 1px solid rgba(45,212,191,.22); background: rgba(20,184,166,.07); border-radius: 14px;
               padding: .65rem .9rem; font-size: .84rem; }
.eco-how b { color: #2dd4bf; }

.eco-step { display: flex; gap: .75rem; align-items: center; margin: .7rem 0 .55rem; }
.eco-step-n { width: 30px; height: 30px; flex: none; border-radius: 50%; color: #fff; font-weight: 700;
              display: flex; align-items: center; justify-content: center; font-size: .9rem;
              background: linear-gradient(135deg, #0f766e, #14b8a6); box-shadow: 0 3px 8px rgba(15,118,110,.35); }
.eco-step-t { font-weight: 700; font-size: 1.06rem; line-height: 1.1; }
.eco-step-s { font-size: .8rem; opacity: .72; margin-top: 2px; }

.eco-kpi { display: flex; gap: .8rem; align-items: center; padding: .9rem 1rem; border-radius: 16px;
           border: 1px solid rgba(45,212,191,.22); background: rgba(20,184,166,.07);
           transition: transform .2s ease, border-color .2s ease; }
.eco-kpi:hover { transform: translateY(-2px); border-color: #14b8a6; }
.eco-kpi-ico { width: 42px; height: 42px; flex: none; border-radius: 12px; font-size: 1.3rem;
               display: flex; align-items: center; justify-content: center; background: rgba(20,184,166,.16); }
.eco-kpi-v { font-size: 1.45rem; font-weight: 800; color: #2dd4bf; line-height: 1; }
.eco-kpi-l { font-size: .68rem; font-weight: 600; text-transform: uppercase; letter-spacing: .06em;
             opacity: .78; margin-top: .3rem; }

.eco-meter-box { border: 1px solid rgba(45,212,191,.22); border-radius: 16px; padding: 1rem 1.2rem;
                 background: rgba(20,184,166,.07); margin: .4rem 0 .8rem; }
.eco-meter-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: .8rem; }
.eco-meter-pct { font-size: 2.1rem; font-weight: 800; line-height: 1; }
.eco-meter-track { position: relative; height: 12px; border-radius: 999px;
    background: linear-gradient(90deg, #22c55e 0 40%, #f59e0b 40% 70%, #ef4444 70% 100%); }
.eco-meter-marker { position: absolute; top: 50%; width: 22px; height: 22px; border-radius: 50%;
    background: #f8fafc; border: 4px solid #0f172a; transform: translate(-50%, -50%);
    box-shadow: 0 2px 8px rgba(0,0,0,.45); transition: left .3s ease; }
.eco-meter-scale { display: flex; font-size: .68rem; font-weight: 600; opacity: .72; margin-top: .45rem; }
.eco-meter-scale span:nth-child(1) { width: 40%; }
.eco-meter-scale span:nth-child(2) { width: 30%; }
.eco-meter-hint { font-size: .82rem; margin-top: .6rem; opacity: .88; }

.eco-badge { display: inline-block; padding: .3rem .85rem; border-radius: 999px; font-size: .78rem;
             font-weight: 700; letter-spacing: .03em; }
.b-bajo { background: #dcfce7; color: #166534; }
.b-moderado { background: #fef3c7; color: #92400e; }
.b-critico { background: #fee2e2; color: #991b1b; }

.eco-result { border: 1px solid rgba(45,212,191,.22); border-left: 6px solid var(--nivel, #14b8a6);
              border-radius: 16px; padding: 1.2rem 1.4rem; background: rgba(20,184,166,.07); margin-bottom: .8rem; }
.eco-result-top { display: flex; flex-wrap: wrap; justify-content: space-between; gap: .5rem; align-items: center; }
.eco-ok { font-weight: 700; font-size: .85rem; color: #2dd4bf; }
.eco-meta { display: flex; flex-wrap: wrap; gap: .35rem 1.4rem; font-size: .86rem; margin-top: .7rem; }
.eco-meta b { opacity: .72; font-weight: 600; margin-right: .25rem; }
.eco-action { margin: .8rem 0 0; font-size: .92rem; }

.eco-check { list-style: none; padding: 0; margin: 0 0 .6rem; display: flex; flex-wrap: wrap; gap: .4rem; }
.eco-check li { font-size: .78rem; font-weight: 600; padding: .25rem .7rem; border-radius: 999px; }
.eco-check li.ok { background: #dcfce7; color: #166534; }
.eco-check li.no { background: rgba(148,163,184,.18); opacity: .9; }

.eco-tl { border-left: 2px solid rgba(45,212,191,.35); margin: .5rem 0 1rem .5rem; padding-left: 1rem; }
.eco-tl-i { position: relative; font-size: .86rem; padding: .25rem 0 .55rem; }
.eco-tl-d { position: absolute; left: -1.38rem; top: .45rem; width: 11px; height: 11px;
            border-radius: 50%; background: #14b8a6; border: 2px solid #0f172a; }

.eco-empty { text-align: center; padding: 2.5rem 1rem; border: 1.5px dashed rgba(45,212,191,.35);
             border-radius: 16px; background: rgba(20,184,166,.05); }
.eco-empty-ico { font-size: 2.4rem; }
.eco-empty-t { font-weight: 700; margin-top: .3rem; }
.eco-empty-s { font-size: .88rem; opacity: .75; }

.stButton > button[kind="primary"] { border-radius: 12px; font-weight: 700; padding: .65rem 1rem; }
.stTabs [data-baseweb="tab"] { font-weight: 600; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px;
    border-color: rgba(45, 212, 191, 0.22) !important;
}

@media (max-width: 760px) {
  .block-container { padding-left: .7rem; padding-right: .7rem; }
  .eco-hero { padding: 1.1rem 1.1rem; border-radius: 18px; }
  .eco-title { font-size: 1.45rem; }
  .eco-how { grid-template-columns: 1fr; }
  .eco-hs { min-width: 80px; padding: .5rem .7rem; }
  .eco-meter-pct { font-size: 1.7rem; }
}
</style>
"""


def inyectar() -> None:
    st.markdown(CSS, unsafe_allow_html=True)