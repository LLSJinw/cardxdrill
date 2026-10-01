# streamlit_app.py
# Phased TTX Random-Q Card Deck — Mittare Cyber Drill 2026, Plan B
#
# WHAT THIS APP DOES (Random Questions only — Standard Qs run separately via Slido):
#   Phase 1-3: a dice draw (no repeat) picks ONE team to play that phase's Random Q.
#              The drawn team sees 2 cards (left/right) and flips ONLY ONE to answer;
#              the other stays a locked decoy — adds suspense without adding scored items.
#   Phase 4:   no draw needed — all 3 teams play, 1 card each, 3 cards total.
#
# Content stock needed (edit PHASES / STORY below once questions are finalized):
#   Ph.1 StdQ3 + RanQ2   Ph.2 StdQ3 + RanQ2   Ph.3 StdQ3 + RanQ2   Ph.4 StdQ3 + RanQ3
#   (Standard Qs are not in this app at all — this deck only renders the RanQ pool.)
#
# Supports real images under /assets; falls back to generated placeholders.

import os
import base64, io, random, textwrap
from typing import Dict, List, Optional
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps

st.set_page_config(page_title="TTX Phased Deck", page_icon="🃏", layout="wide")

# ---------- Assets ----------
ASSET_DIR = "assets"  # holds back.png, and per-card front art named "<card id>.png" e.g. "RQ1-A.png"

def load_image_b64(filename: str) -> str:
    """Read an image from assets and return base64 string."""
    path = os.path.join(ASSET_DIR, filename)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

# ---------- Background (1920x1080 recommended) ----------
BG_PATH = "BG.png"
try:
    with open(BG_PATH, "rb") as f:
        bg_base64 = base64.b64encode(f.read()).decode()
    bg_css = f'url("data:image/png;base64,{bg_base64}") no-repeat center center fixed;\n  background-size: cover;'
except Exception:
    bg_css = "none;"

# ================= CONFIG — edit this block as content/teams change =================
TEAMS: List[str] = ["Team A", "Team B", "Team C"]
TEAM_COLORS: Dict[str, str] = {"Team A": "#D9822B", "Team B": "#028090", "Team C": "#6B4E8E"}

# Phase 1-3: exactly 2 ids each = the left/right decoy pair for the drawn team.
# Phase 4: exactly 3 ids = one per team, all teams play, no draw / no decoy.
# Swap any id below for a different pick from the full authored pool (shown in the comments).
PHASES: Dict[str, List[str]] = {
    "Phase 1 – Detection & Analysis":          ["RQ1-A", "RQ1-B"],   # full pool: RQ1-A / RQ1-B / RQ1-C
    "Phase 2 – Containment & Eradication":      ["RQ2-B", "RQ2-C"],   # full pool: RQ2-A / RQ2-B / RQ2-C
    "Phase 3 – Core Disruption & Data Breach":  ["RQ3-B", "RQ3-C"],   # full pool: RQ3-A / RQ3-B / RQ3-C
    "Phase 4 – Post-Incident & Resilience":     ["RQ4-A", "RQ4-B", "RQ4-C"],  # always all 3
}
DRAW_PHASES = list(PHASES.keys())[:3]     # Phase 1-3: dice-draw + decoy-card mechanic
ALL_PLAY_PHASE = list(PHASES.keys())[3]   # Phase 4: all 3 teams, no draw

# Short facilitator-facing labels — replace with final wording once the Word doc is locked.
STORY: Dict[str, str] = {
    "RQ1-A": "Wait for more information before acting?",
    "RQ1-B": "Business still running — pause IR or continue?",
    "RQ1-C": "3rd party denies sending the email — now what?",
    "RQ2-A": "Multiple systems affected — widen isolation?",
    "RQ2-B": "Power off now, or disconnect first?",
    "RQ2-C": "3rd-party remote access — restrict or leave alone?",
    "RQ3-A": "Regulator asks for an update mid-investigation.",
    "RQ3-B": "Customer / media pressure — how do we respond?",
    "RQ3-C": "Attacker offers to delete data if ransom is paid.",
    "RQ4-A": "Media reports Mittare hid the breach.",
    "RQ4-B": "RCA finds vendor access was broader than needed.",
    "RQ4-C": "New indicator found after recovery — close or dig in?",
}
# =======================================================================================

CARD_W, CARD_H = 288, 432  # fixed 2:3 card size

# CSS + Title
st.markdown(f"""
<style>
.stApp {{
  background: {bg_css}
  background-color: #0e1525 !important;
  color: #fff !important;
}}

.title-bg {{
  font-size: 1.8rem; font-weight: 800; margin: .25rem 0 .35rem 0;
  display: inline-block; background: rgba(0,0,0,.50);
  padding: .35rem .65rem; border-radius: 10px;
}}
.subtitle-bg {{
  font-size: .95rem; margin: 0 0 .75rem 0; display: inline-block;
  background: rgba(0,0,0,.40); padding: .25rem .6rem; border-radius: 8px; color: #cfe3e6;
}}
.block-container, header, .st-emotion-cache-18ni7ap, .st-emotion-cache-1v0mbdj {{
  background: transparent !important; box-shadow: none !important; backdrop-filter: none !important;
}}
[data-testid="stSidebar"] {{ background: rgba(10,15,25,0.96) !important; color: #fff !important; box-shadow: none !important; }}
[data-testid="stSidebar"] > div:first-child {{ background: transparent !important; }}

/* Phase container styling */
.phase-box {{
  padding: .6rem .7rem .8rem .7rem; border-radius: 14px;
  background: rgba(8,14,26,.55); border: 1px solid rgba(255,255,255,.08);
  box-shadow: 0 6px 18px rgba(0,0,0,.25);
}}
.phase-title {{
  margin: 0 0 .5rem 0; font-weight: 700; font-size: 1.08rem;
  background: rgba(0,0,0,.45); display: inline-block; padding: .3rem .6rem;
  border-radius: 8px; line-height: 1.2;
}}
.hr-compact {{ margin: 0.8rem 0 1.1rem 0; border: 0; height: 1px; background: rgba(255,255,255,.15); }}
.badge {{ display:inline-block; padding:.15rem .5rem; margin-left:.4rem; border-radius: 999px; font-size:.75rem; background:rgba(255,255,255,.14); }}

/* Team legend */
.legend-chip {{
  display:inline-flex; align-items:center; gap:.4rem; margin-right: .9rem;
  font-size:.85rem; font-weight:600; background: rgba(0,0,0,.35); padding:.2rem .55rem; border-radius: 999px;
}}
.legend-dot {{ width:.65rem; height:.65rem; border-radius:50%; display:inline-block; }}

/* Draw banner */
.draw-banner {{
  display:inline-block; font-size:.85rem; font-weight:700; padding:.3rem .6rem;
  border-radius: 8px; margin-bottom:.5rem; color:#0e1525;
}}
.draw-pending {{
  display:inline-block; font-size:.8rem; font-style:italic; padding:.3rem .6rem;
  border-radius: 8px; margin-bottom:.5rem; background: rgba(255,255,255,.1); color:#cfd6da;
}}

/* Card team strip (Phase 4) */
.team-strip {{
  font-size:.78rem; font-weight:700; text-align:center; padding:.18rem 0;
  border-radius: 6px 6px 0 0; color:#0e1525; margin: 0 auto; width: 288px;
}}

/* Card + Flip */
.card-container {{ perspective: 1000px; }}
.card {{ width: 288px; height: 432px; margin: .3rem auto 0 auto; position: relative; transition: transform .2s ease; }}
.card:hover {{ transform: translateY(-3px); }}
.card-inner {{ position: absolute; width: 100%; height: 100%; transform-style: preserve-3d; transition: transform 0.6s ease;
  filter: drop-shadow(0 8px 14px rgba(0,0,0,.45)); }}
.flipped .card-inner {{ transform: rotateY(180deg); }}
.card-face {{ position: absolute; width: 100%; height: 100%; -webkit-backface-visibility: hidden; backface-visibility: hidden;
  border-radius: 12px; overflow: hidden; }}
.card-front {{ transform: rotateY(0deg); }}
.card-back  {{ transform: rotateY(180deg); }}
.img-fit {{ width: 100%; height: 100%; object-fit: cover; }}
.card.locked-decoy {{ opacity: .45; filter: grayscale(.6); }}

/* Zoom overlay */
.overlay {{ position: fixed; inset: 0; background: rgba(0,0,0,0.72); display: flex; align-items: center; justify-content: center;
  z-index: 2147483646; pointer-events: none; }}
.overlay .cardwrap {{ max-width: min(90vw, 900px); border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.55); pointer-events: auto; }}
.overlay img {{ width: 100%; height: auto; display:block; }}
.closebar {{ position: fixed; bottom: 18px; left: 18px; z-index: 2147483647; }}
.closebar .stButton > button {{ position: relative; font-weight: 700; box-shadow: 0 6px 16px rgba(0,0,0,0.35); }}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title-bg">Phased TTX Card Deck — Random Questions</div>', unsafe_allow_html=True)
legend_html = "".join(
    f'<span class="legend-chip"><span class="legend-dot" style="background:{TEAM_COLORS[t]}"></span>{t}</span>'
    for t in TEAMS
)
st.markdown(f'<div class="subtitle-bg">{legend_html}</div>', unsafe_allow_html=True)

# ---------- Fallback card drawing (used if an image is missing) ----------
def get_font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()

def draw_card_back() -> Image.Image:
    NAVY = (16, 34, 64); WHITE = (248, 251, 255)
    img = Image.new("RGB", (CARD_W, CARD_H), NAVY)
    d = ImageDraw.Draw(img)
    for x in range(-CARD_H, CARD_W + CARD_H, 36):
        d.line([(x, 0), (x + CARD_H, CARD_H)], fill=(255, 255, 255, 32), width=2)
    d.text((CARD_W // 2, CARD_H // 2 - 40), "UIH", anchor="mm", fill=WHITE, font=get_font(40))
    img = ImageOps.expand(img, border=8, fill=(240, 244, 252))
    img = ImageOps.expand(img, border=3, fill=(220, 226, 236))
    return img

def draw_front(label: str, subtitle: str) -> Image.Image:
    NAVY = (16, 34, 64); STRIPE = (208, 213, 221); LIGHT = (236, 240, 248)
    img = Image.new("RGB", (CARD_W, CARD_H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, int(CARD_H * 0.16), CARD_W, int(CARD_H * 0.19)], fill=STRIPE)
    d.rectangle([0, int(CARD_H * 0.72), CARD_W, int(CARD_H * 0.75)], fill=STRIPE)
    d.text((CARD_W // 2, int(CARD_H * 0.30)), label, anchor="mm", fill=LIGHT, font=get_font(44))
    wrapped = textwrap.fill(subtitle, width=22)
    d.multiline_text((CARD_W // 2, int(CARD_H * 0.55)), wrapped, anchor="mm", fill=LIGHT, font=get_font(24), align="center")
    img = ImageOps.expand(img, border=8, fill=(240, 244, 252))
    img = ImageOps.expand(img, border=3, fill=(220, 226, 236))
    return img

def pil_to_b64(img) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")

# ---------- State ----------
def init():
    if "cards" in st.session_state:
        return

    try:
        back_b64 = load_image_b64("back.png")
    except Exception:
        back_b64 = pil_to_b64(draw_card_back())

    cards: Dict[str, List[Dict]] = {}
    for ph, ids in PHASES.items():
        phase_cards = []
        for qid in ids:
            img_filename = f"{qid}.png"
            img_path = os.path.join(ASSET_DIR, img_filename)
            if os.path.exists(img_path):
                try:
                    front_b64 = load_image_b64(img_filename)
                except Exception:
                    front_b64 = pil_to_b64(draw_front(qid, STORY.get(qid, "")))
            else:
                front_b64 = pil_to_b64(draw_front(qid, STORY.get(qid, "")))
            phase_cards.append({
                "id": qid, "front": front_b64, "back": back_b64,
                "flipped": False, "owner": None,
            })
        cards[ph] = phase_cards

    st.session_state.cards = cards
    st.session_state.draw: Dict[str, str] = {}          # Phase 1-3 only: phase -> assigned team
    st.session_state.draw_pool: List[str] = TEAMS[:]     # remaining undrawn teams (no-repeat draw)
    st.session_state.score = {t: 0 for t in TEAMS}
    st.session_state.zoom: Optional[tuple] = None

init()

# ---------- Admin / helpers ----------
def reset_all():
    st.session_state.pop("cards", None)
    st.session_state.pop("draw", None)
    st.session_state.pop("draw_pool", None)
    st.session_state.pop("score", None)
    init()

def reset_draws():
    """Re-roll who plays Phase 1-3 without touching flipped cards/scores already made."""
    st.session_state.draw = {}
    st.session_state.draw_pool = TEAMS[:]
    for ph in DRAW_PHASES:
        for c in st.session_state.cards[ph]:
            c["flipped"] = False
            c["owner"] = None

def shuffle_unflipped_in_phase(phase_name: str):
    pcs = st.session_state.cards[phase_name]
    flipped = [c for c in pcs if c["flipped"]]
    unflipped = [c for c in pcs if not c["flipped"]]
    random.shuffle(unflipped)
    st.session_state.cards[phase_name] = flipped + unflipped

def draw_team_for_phase(phase_name: str):
    """No-repeat dice draw: picks from teams not yet drawn in Phase 1-3."""
    if phase_name in st.session_state.draw:
        return
    pool = st.session_state.draw_pool
    if not pool:
        return
    team = random.choice(pool)
    pool.remove(team)
    st.session_state.draw[phase_name] = team

def flip_card(phase_name: str, idx: int):
    pcs = st.session_state.cards[phase_name]
    card = pcs[idx]
    if card["flipped"]:
        return

    if phase_name in DRAW_PHASES:
        team = st.session_state.draw.get(phase_name)
        if team is None:
            return  # must draw first
        if any(c["flipped"] for c in pcs):
            return  # only 1 of the 2 cards may be answered per phase
    else:
        team = TEAMS[idx]  # Phase 4: fixed 1 card per team, by position

    card["flipped"] = True
    card["owner"] = team
    st.session_state.score[team] += 1

def toggle_zoom(phase_name: str, idx: int):
    st.session_state.zoom = None if st.session_state.zoom == (phase_name, idx) else (phase_name, idx)

def close_zoom():
    st.session_state.zoom = None

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Admin / Demo Controls")
    if st.session_state.get("zoom") is not None:
        st.button("✕ Close Zoom (Admin)", on_click=close_zoom, type="primary", use_container_width=True)
        st.caption("Visible only while a card is zoomed.")
        st.markdown("---")

    reveal_all_global = st.checkbox("Reveal all cards (demo / override)", value=False)

    st.markdown("---")
    st.subheader("\U0001F3B2 Team Draw — Phase 1–3")
    st.caption("Each phase draws from teams not yet picked, so every team plays exactly once across Phase 1–3.")
    for ph in DRAW_PHASES:
        drawn = st.session_state.draw.get(ph)
        label = f"Draw team — {ph.split('–')[0].strip()}"
        if drawn:
            st.markdown(
                f'<div class="draw-banner" style="background:{TEAM_COLORS[drawn]}">{ph.split("–")[0].strip()} → {drawn}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.button(label, on_click=draw_team_for_phase, args=(ph,), use_container_width=True,
                      disabled=not st.session_state.draw_pool, key=f"draw_{ph}")
    if not st.session_state.draw_pool and len(st.session_state.draw) == len(DRAW_PHASES):
        st.caption("All 3 teams drawn — each plays exactly once in Phase 1–3.")
    st.button("↻ Reset Draws (keep scores elsewhere)", on_click=reset_draws, use_container_width=True)

    st.markdown("---")
    st.subheader("Reset")
    st.button("\U0001F504 Reset All (cards + draws + scores)", on_click=reset_all, use_container_width=True)
    for ph in PHASES:
        st.button(f"\U0001F500 Shuffle Unflipped — {ph}", on_click=shuffle_unflipped_in_phase,
                  args=(ph,), use_container_width=True, key=f"shuf_{ph}")

    st.markdown("---")
    st.header("Teams & Score")
    for t in TEAMS:
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.3rem;">'
            f'<span class="legend-chip"><span class="legend-dot" style="background:{TEAM_COLORS[t]}"></span>{t}</span>'
            f'<b>{st.session_state.score[t]}</b></div>',
            unsafe_allow_html=True,
        )

# ---------- Main ----------
st.caption(
    "Phase 1–3: draw a team in the sidebar, then that team flips ONE of 2 cards (the other stays a locked decoy). "
    "Phase 4: all 3 teams play — 1 card each, no draw needed. Click **Zoom** on a flipped card."
)

def render_phase(phase_name: str):
    pcs = st.session_state.cards[phase_name]
    picked = sum(c["flipped"] for c in pcs)
    is_draw_phase = phase_name in DRAW_PHASES
    limit = 1 if is_draw_phase else len(pcs)

    st.markdown(
        f'<div class="phase-title">{phase_name} <span class="badge">{picked}/{limit}</span></div>',
        unsafe_allow_html=True,
    )

    drawn_team = st.session_state.draw.get(phase_name) if is_draw_phase else None
    if is_draw_phase:
        if drawn_team:
            st.markdown(
                f'<div class="draw-banner" style="background:{TEAM_COLORS[drawn_team]}">\U0001F3B2 {drawn_team} plays this phase’s Random Q</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="draw-pending">\U0001F3B2 Waiting on team draw (sidebar) before cards can be flipped…</div>', unsafe_allow_html=True)

    cols = st.columns(len(pcs), gap="small")
    for i, col in enumerate(cols):
        with col:
            card = pcs[i]
            front = f"data:image/png;base64,{card['front']}"
            back = f"data:image/png;base64,{card['back']}"
            flipped_class = "flipped" if card["flipped"] else ""

            # eligibility
            if is_draw_phase:
                already_answered = any(c["flipped"] for c in pcs)
                eligible = (drawn_team is not None) and not already_answered
                is_locked_decoy = already_answered and not card["flipped"]
            else:
                eligible = True
                is_locked_decoy = False

            # team strip (Phase 4 shows fixed owner; draw-phases show drawn team once known)
            strip_team = TEAMS[i] if not is_draw_phase else drawn_team
            if strip_team and not is_locked_decoy:
                st.markdown(
                    f'<div class="team-strip" style="background:{TEAM_COLORS[strip_team]}">{strip_team}</div>',
                    unsafe_allow_html=True,
                )

            locked_cls = " locked-decoy" if is_locked_decoy else ""
            st.markdown(f"""
            <div class="card-container">
              <div class="card {flipped_class}{locked_cls}">
                <div class="card-inner">
                  <div class="card-face card-front"><img class="img-fit" src="{back}"/></div>
                  <div class="card-face card-back"><img class="img-fit" src="{front}"/></div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            b1, b2 = st.columns(2, gap="small")
            with b1:
                flip_disabled = card["flipped"] or (not reveal_all_global and not eligible)
                st.button("Flip", key=f"flip_{phase_name}_{i}", on_click=flip_card,
                          args=(phase_name, i), disabled=flip_disabled, use_container_width=True)
            with b2:
                st.button("Zoom", key=f"zoom_{phase_name}_{i}", on_click=toggle_zoom,
                          args=(phase_name, i), disabled=not card["flipped"], use_container_width=True)

            if card["flipped"]:
                st.caption(f"**{card['id']}** → {card['owner']}")
                st.caption(STORY.get(card["id"], ""))
            elif is_locked_decoy:
                st.caption("_Not selected this round_")

# 2x2 matrix layout
row1 = st.columns(2, gap="large")
with row1[0]:
    st.markdown('<div class="phase-box">', unsafe_allow_html=True)
    render_phase("Phase 1 – Detection & Analysis")
    st.markdown('</div>', unsafe_allow_html=True)
with row1[1]:
    st.markdown('<div class="phase-box">', unsafe_allow_html=True)
    render_phase("Phase 2 – Containment & Eradication")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<hr class="hr-compact">', unsafe_allow_html=True)

row2 = st.columns(2, gap="large")
with row2[0]:
    st.markdown('<div class="phase-box">', unsafe_allow_html=True)
    render_phase("Phase 3 – Core Disruption & Data Breach")
    st.markdown('</div>', unsafe_allow_html=True)
with row2[1]:
    st.markdown('<div class="phase-box">', unsafe_allow_html=True)
    render_phase("Phase 4 – Post-Incident & Resilience")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Zoom overlay ----------
if st.session_state.zoom is not None:
    ph, idx = st.session_state.zoom
    card = st.session_state.cards[ph][idx]
    img_b64 = card["front"] if card["flipped"] else card["back"]
    st.markdown(f"""
    <div class="overlay">
      <div class="cardwrap"><img src="data:image/png;base64,{img_b64}" /></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="closebar">', unsafe_allow_html=True)
    st.button("✕ Close Zoom", on_click=close_zoom, type="primary")
    st.markdown('</div>', unsafe_allow_html=True)
