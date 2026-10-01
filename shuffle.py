# streamlit_app.py
# Phased TTX Random-Q Card Deck — Mittare Cyber Drill 2026
#
# WHAT THIS APP DOES: a clean, fully manual flip-reveal board. Every card in every
# phase can be flipped at any time, in any order — no draws, no locks, no picker.
# The facilitator (speaker) runs the actual game logic out loud; the app's only job
# is to reveal a card's art on click. Team selection and scoring stay outside the app.
#
# Content stock (edit PHASE_CARD_NUMBERS below if the grouping ever changes):
#   Ph.1 StdQ3 + RanQ2   Ph.2 StdQ3 + RanQ2   Ph.3 StdQ3 + RanQ2   Ph.4 StdQ3 + RanQ3
#   (Standard Qs are not in this app at all — this deck only renders the RanQ pool.)
#
# Art: drop human-made cards straight into assets/card01.png ... card09.png (plain
# numbered files). Falls back to a generated placeholder if a number's file is missing.

import os
import base64, io, random, textwrap
from typing import Dict, List, Optional
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps

st.set_page_config(page_title="TTX Phased Deck", page_icon="🃏", layout="wide")

# ---------- Assets ----------
ASSET_DIR = "assets"  # holds back.png + per-card front art (card01.png ... card09.png)

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

# ================= CONFIG — edit this block as content changes =================
# Human-designed art goes straight in assets/card01.png ... card09.png — plain numbered
# files, no renaming needed. Each phase owns a fixed group of numbers; on-screen slot
# order is reshuffled every time the deck is (re)dealt, so layout isn't always identical.
#   Phase 1: card01, card02            Phase 3: card05, card06
#   Phase 2: card03, card04            Phase 4: card07, card08, card09
PHASE_CARD_NUMBERS: Dict[str, List[int]] = {
    "Phase 1 – Detection & Analysis":          [1, 2],
    "Phase 2 – Containment & Eradication":      [3, 4],
    "Phase 3 – Core Disruption & Data Breach":  [5, 6],
    "Phase 4 – Post-Incident & Resilience":     [7, 8, 9],
}
PHASES: Dict[str, List[str]] = {
    ph: [f"card{n:02d}" for n in nums] for ph, nums in PHASE_CARD_NUMBERS.items()
}

# Optional short caption under a flipped card. Leave blank if the card art already
# contains the full question — these are just an extra on-screen reminder if you want one.
STORY: Dict[str, str] = {
    # "card01": "Wait for more information before acting?",
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
st.markdown(
    '<div class="subtitle-bg">Facilitator-controlled card reveal. Ask the team, then flip the chosen card manually.</div>',
    unsafe_allow_html=True,
)

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
    for ph, numbers in PHASE_CARD_NUMBERS.items():
        shuffled_numbers = numbers[:]
        random.shuffle(shuffled_numbers)  # fresh on-screen order every deal/reset
        phase_cards = []
        for n in shuffled_numbers:
            qid = f"card{n:02d}"
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
                "id": qid, "front": front_b64, "back": back_b64, "flipped": False,
            })
        cards[ph] = phase_cards

    st.session_state.cards = cards
    st.session_state.zoom: Optional[tuple] = None

init()

# ---------- Admin / helpers ----------
def reset_all():
    st.session_state.pop("cards", None)
    init()

def reveal_all_cards():
    for ph in st.session_state.cards:
        for c in st.session_state.cards[ph]:
            c["flipped"] = True

def shuffle_unflipped_in_phase(phase_name: str):
    pcs = st.session_state.cards[phase_name]
    flipped = [c for c in pcs if c["flipped"]]
    unflipped = [c for c in pcs if not c["flipped"]]
    random.shuffle(unflipped)
    st.session_state.cards[phase_name] = flipped + unflipped

def flip_card(phase_name: str, idx: int):
    """Free flip — any card, any time. No draws, no locks, no eligibility checks."""
    card = st.session_state.cards[phase_name][idx]
    if not card["flipped"]:
        card["flipped"] = True

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

    st.button("\U0001F440 Reveal ALL Cards Now", on_click=reveal_all_cards, use_container_width=True)
    st.button("\U0001F504 Reset All Cards", on_click=reset_all, use_container_width=True)
    st.markdown("---")
    st.subheader("Shuffle unflipped cards")
    for ph in PHASES:
        st.button(f"\U0001F500 {ph}", on_click=shuffle_unflipped_in_phase,
                  args=(ph,), use_container_width=True, key=f"shuf_{ph}")

# ---------- Main ----------
st.caption("Click **Flip** on any card, any phase, any time — nothing is locked. Click **Zoom** once it's flipped.")

def render_phase(phase_name: str):
    pcs = st.session_state.cards[phase_name]
    picked = sum(c["flipped"] for c in pcs)

    st.markdown(
        f'<div class="phase-title">{phase_name} <span class="badge">{picked}/{len(pcs)}</span></div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(len(pcs), gap="small")
    for i, col in enumerate(cols):
        with col:
            card = pcs[i]
            front = f"data:image/png;base64,{card['front']}"
            back = f"data:image/png;base64,{card['back']}"
            flipped_class = "flipped" if card["flipped"] else ""

            st.markdown(f"""
            <div class="card-container">
              <div class="card {flipped_class}">
                <div class="card-inner">
                  <div class="card-face card-front"><img class="img-fit" src="{back}"/></div>
                  <div class="card-face card-back"><img class="img-fit" src="{front}"/></div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            b1, b2 = st.columns(2, gap="small")
            with b1:
                st.button("Flip", key=f"flip_{phase_name}_{i}", on_click=flip_card,
                          args=(phase_name, i), disabled=card["flipped"], use_container_width=True)
            with b2:
                st.button("Zoom", key=f"zoom_{phase_name}_{i}", on_click=toggle_zoom,
                          args=(phase_name, i), disabled=not card["flipped"], use_container_width=True)

            if card["flipped"] and STORY.get(card["id"]):
                st.caption(STORY[card["id"]])

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
