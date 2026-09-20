"""University of Dayton-inspired course styling without use of university marks."""

UD_NAVY = "#141B4D"
UD_RED = "#E4022B"
UD_TURQUOISE = "#59CBE8"
LINK_BLUE = "#0060F0"
INK = "#1E1E11"
PALE_TURQUOISE = "#E8F9FD"
LIGHT_GRAY = "#E5E5E5"

APP_CSS = f"""
<style>
  :root {{ --navy:{UD_NAVY}; --red:{UD_RED}; --aqua:{UD_TURQUOISE}; --ink:{INK}; --pale:{PALE_TURQUOISE}; --gray:{LIGHT_GRAY}; }}
  .stApp {{ background:#F7F8FB; }}
  section[data-testid="stMain"] {{ overflow-anchor:none; }}
  [data-testid="stDecoration"] {{ background:var(--red); }}
  [data-testid="stToolbar"], [data-testid="stHeaderActionElements"] {{ display:none; }}
  [data-testid="stIFrame"], iframe[title="st.iframe"] {{ height:0 !important; min-height:0 !important; border:0 !important; }}
  div[data-testid="stElementContainer"]:has(iframe[title="st.iframe"]) {{ height:0 !important; min-height:0 !important; margin:0 !important; }}
  .block-container {{ max-width:1120px; padding-top:1.25rem; padding-bottom:4rem; }}
  h1, h2, h3 {{ color:var(--navy); letter-spacing:-0.018em; }}
  p, li, label {{ color:var(--ink); }}
  a {{ color:{LINK_BLUE}; }}
  .hero {{ background:linear-gradient(128deg,var(--navy) 0%,#202B73 78%,#273587 100%); border-top:7px solid var(--red); border-radius:18px; box-shadow:0 15px 38px rgba(20,27,77,.16); padding:1.8rem 2rem; margin-bottom:1rem; position:relative; overflow:hidden; }}
  .hero:after {{ content:""; position:absolute; width:210px; height:210px; right:-75px; top:-100px; border:28px solid rgba(89,203,232,.32); border-radius:50%; }}
  .hero .kicker {{ color:var(--aqua); font-size:.78rem; font-weight:850; letter-spacing:.13em; text-transform:uppercase; }}
  .hero h1 {{ color:white; margin:.22rem 0 .35rem; font-size:clamp(2rem,4.8vw,3.45rem); }}
  .hero p {{ color:#F5F7FF; font-size:1.08rem; max-width:810px; margin:0; }}
  .stage-row {{ display:grid; grid-template-columns:repeat(7,1fr); gap:.4rem; margin:0 0 1.25rem; }}
  .stage-pill {{ background:#EAECF2; border:1px solid #D5D8E2; border-radius:999px; color:#555D75; font-size:.72rem; font-weight:760; padding:.46rem .42rem; text-align:center; }}
  .stage-pill.complete {{ background:var(--pale); border-color:#A9DEEA; color:var(--navy); }}
  .stage-pill.active {{ background:var(--red); border-color:var(--red); color:white; }}
  .eyebrow {{ color:var(--red); font-size:.78rem; font-weight:850; letter-spacing:.1em; text-transform:uppercase; }}
  .lead {{ color:#4F5668; font-size:1.05rem; max-width:880px; }}
  .case-card {{ background:white; border:1px solid #D9DCE6; border-left:6px solid var(--aqua); border-radius:13px; box-shadow:0 8px 22px rgba(20,27,77,.06); margin:.8rem 0 1rem; padding:1.05rem 1.2rem; }}
  .case-card strong {{ color:var(--navy); }}
  .principle {{ background:var(--pale); border-left:5px solid var(--navy); border-radius:9px; margin:.75rem 0 1rem; padding:.82rem .95rem; }}
  .principle strong {{ color:var(--navy); }}
  .schema-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:.7rem; margin:.8rem 0 1.1rem; }}
  .schema-table {{ background:white; border:1px solid #D8DCE7; border-radius:12px; overflow:hidden; }}
  .schema-table h4 {{ background:var(--navy); color:white; margin:0; padding:.62rem .75rem; }}
  .schema-table div {{ border-top:1px solid #E5E7EE; color:#33384A; font-size:.87rem; padding:.42rem .75rem; }}
  .source-table-wrap {{ background:white; border:1px solid #D8DCE7; border-radius:12px; margin:.8rem 0; overflow:hidden; width:100%; }}
  .source-table {{ border-collapse:collapse; table-layout:fixed; width:100%; }}
  .source-table th {{ background:var(--navy); color:white; font-size:14px !important; font-weight:800; line-height:1.15; overflow-wrap:normal; padding:.45rem .15rem; text-align:left; vertical-align:bottom; word-break:normal; }}
  .source-table td {{ border-top:1px solid #E5E7EE; color:#33384A; font-size:16px !important; line-height:1.24; padding:.45rem .15rem; vertical-align:top; }}
  .source-table th:nth-child(1) {{ width:8% !important; }}
  .source-table th:nth-child(2) {{ width:6.5% !important; }}
  .source-table th:nth-child(3) {{ width:10.5% !important; }}
  .source-table th:nth-child(4) {{ width:8.5% !important; }}
  .source-table th:nth-child(5) {{ width:13% !important; }}
  .source-table th:nth-child(6) {{ width:9% !important; }}
  .source-table th:nth-child(7) {{ width:7% !important; }}
  .source-table th:nth-child(8) {{ width:12% !important; }}
  .source-table th:nth-child(9) {{ width:8% !important; }}
  .source-table th:nth-child(10) {{ width:7.5% !important; }}
  .source-table th:nth-child(11) {{ width:10% !important; }}
  .source-table tbody tr:nth-child(even) {{ background:#F5F7FB; }}
  .comparison-grid {{ display:grid; gap:.8rem; grid-template-columns:1fr 1fr; margin:1rem 0; }}
  .comparison-card {{ background:white; border:1px solid #D8DCE7; border-radius:14px; box-shadow:0 8px 22px rgba(20,27,77,.06); padding:1rem 1.1rem; }}
  .comparison-card.problem {{ border-top:5px solid #A56700; }}
  .comparison-card.better {{ border-top:5px solid #147A4B; }}
  .comparison-card h4 {{ color:var(--navy); font-size:1.08rem; margin:.2rem 0 .5rem; }}
  .comparison-card p {{ color:#4F5668; margin:0; }}
  .comparison-label {{ color:var(--red); font-size:.7rem; font-weight:850; letter-spacing:.09em; }}
  .diagram {{ align-items:center; display:grid; gap:.45rem; grid-template-columns:1fr auto 1fr auto 1fr; margin:1rem 0; }}
  .entity {{ background:white; border:2px solid var(--navy); border-radius:12px; color:var(--navy); font-weight:820; padding:.85rem .55rem; text-align:center; }}
  .connector {{ color:var(--red); font-size:.82rem; font-weight:850; text-align:center; }}
  .rea-example {{ align-items:stretch; display:grid; gap:.8rem; grid-template-columns:1fr .66fr 1fr; margin:1rem 0; }}
  .rea-event-card {{ background:white; border:2px solid var(--navy); border-radius:14px; box-shadow:0 8px 22px rgba(20,27,77,.06); overflow:hidden; padding:1rem; }}
  .rea-event-card h4 {{ color:var(--navy); font-size:1.25rem; margin:.15rem 0 .8rem; }}
  .rea-event-label {{ color:var(--red); font-size:.72rem; font-weight:850; letter-spacing:.1em; }}
  .rea-event-card div:not(.rea-event-label) {{ border-top:1px solid #E5E7EE; display:flex; flex-direction:column; gap:.12rem; padding:.55rem 0 .15rem; }}
  .rea-event-card span {{ color:#4F5668; }}
  .rea-duality {{ align-items:center; background:var(--pale); border:1px solid #A9DEEA; border-radius:14px; color:var(--navy); display:flex; flex-direction:column; justify-content:center; padding:1rem .55rem; text-align:center; }}
  .rea-duality span {{ color:var(--red); font-size:.72rem; font-weight:850; letter-spacing:.09em; text-transform:uppercase; }}
  .feedback {{ background:white; border:1px solid #D9DCE6; border-left:5px solid #8A5A00; border-radius:9px; margin:.45rem 0; padding:.72rem .82rem; }}
  .feedback.correct {{ border-left-color:#147A4B; }}
  .feedback strong {{ color:var(--navy); }}
  .stButton > button, .stFormSubmitButton > button {{ border-radius:9px; font-weight:780; min-height:2.7rem; }}
  button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {{ background:var(--red); border-color:var(--red); color:white; }}
  button[data-testid="stBaseButton-primary"] p, button[data-testid="stBaseButton-primaryFormSubmit"] p {{ color:white !important; }}
  @media (max-width:800px) {{ .block-container{{padding-left:1rem;padding-right:1rem}} .hero{{padding:1.35rem 1.15rem}} .stage-row{{grid-template-columns:1fr}} .stage-pill{{display:none}} .stage-pill.active{{display:block}} .schema-grid{{grid-template-columns:1fr 1fr}} .diagram,.rea-example,.comparison-grid{{grid-template-columns:1fr}} .connector{{padding:.15rem}} .source-table th{{font-size:.62rem}} .source-table td{{font-size:.66rem}} }}
  @media (max-width:520px) {{ .schema-grid{{grid-template-columns:1fr}} }}
</style>
"""
