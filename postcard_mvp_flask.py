from flask import Flask, request, jsonify, render_template_string, g, make_response
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from textwrap import wrap
import re
import unicodedata

app = Flask(__name__)
DATABASE = os.getenv("DATABASE_PATH", "postcards.db")
PUBLIC_POSTCARD_BASE_URL = os.getenv("PUBLIC_POSTCARD_BASE_URL", "https://postcard.sendamemory.store").rstrip("/")

POSTCARD_MESSAGE_STYLE = {
    "desktop_font_size": "23px",
    "tablet_font_size": "20px",
    "mobile_font_size": "18px",
    "font_family": '"Caveat", "Brush Script MT", cursive',
    "font_weight": "600",
    "color": "#6c4a30",
    "line_height": "1.24",
    "letter_spacing": "0.015em",
    "rotation": "0deg",
    "top": "49.6%",
    "left": "8.3%",
    "width": "38.6%",
    "height": "19.2%",
    "min_font_size": "8",
    "max_font_ratio": "0.27",
    "font_scale": "1",
    "horizontal_padding_ratio": "0.024",
    "vertical_padding_ratio": "0.11",
    "line_gap_ratio": "0.2",
    "vertical_align": "0.18",
}

POSTCARD_MESSAGE_POSITIONS = {
    "left": {
        "top": "49.6%",
        "left": "8.3%",
        "width": "38.6%",
        "height": "19.2%",
    },
    "right": {
        "top": "49.6%",
        "left": "53.3%",
        "width": "38.6%",
        "height": "19.2%",
    },
}

POSTCARD_MESSAGE_STYLE_RIGHT = {
    "top": "49.6%",
    "left": "53.3%",
    "width": "38.6%",
    "height": "19.2%",
}

SLOT_CLASS_NAMES = ["slot-a", "slot-b", "slot-c", "slot-d", "slot-e", "slot-f"]


def make_layout_preset(label, count, class_name):
    return {
        "label": label,
        "slot_classes": SLOT_CLASS_NAMES[:count],
        "class_name": class_name,
    }


POSTCARD_LAYOUT_PRESETS = {
    "single": make_layout_preset("Full Bleed", 1, "layout-single-full"),
    "single-full": make_layout_preset("Full Bleed", 1, "layout-single-full"),
    "single-classic": make_layout_preset("Classic Frame", 1, "layout-single-classic"),
    "single-portrait": make_layout_preset("Portrait Focus", 1, "layout-single-portrait"),
    "single-square": make_layout_preset("Square Crop", 1, "layout-single-square"),
    "multi-split": make_layout_preset("Split Duo", 2, "layout-multi-split"),
    "multi-sidebar": make_layout_preset("Sidebar Duo", 2, "layout-multi-sidebar"),
    "multi-top-band": make_layout_preset("Top + Bottom", 3, "layout-multi-top-band"),
    "multi-feature-stack": make_layout_preset("Feature Stack", 3, "layout-multi-feature-stack"),
    "multi-grid": make_layout_preset("Four Grid", 4, "layout-multi-grid"),
    "multi-window": make_layout_preset("Window Stack", 4, "layout-multi-window"),
    "multi-strips": make_layout_preset("Vertical Strips", 4, "layout-multi-strips"),
    "multi-mosaic": make_layout_preset("Mosaic Band", 5, "layout-multi-mosaic"),
    "multi-story": make_layout_preset("Story Spread", 5, "layout-multi-story"),
    "multi-cascade": make_layout_preset("Cascade", 5, "layout-multi-cascade"),
    "multi-six-grid": make_layout_preset("Six Grid", 6, "layout-multi-six-grid"),
    "multi-contact-sheet": make_layout_preset("Contact Sheet", 6, "layout-multi-contact-sheet"),
    "multi-gallery-ribbon": make_layout_preset("Gallery Ribbon", 6, "layout-multi-gallery-ribbon"),
    "signature-hero": make_layout_preset("Signature Hero", 1, "layout-signature-hero"),
    "signature-duo": make_layout_preset("Editorial Duo", 2, "layout-signature-duo"),
    "signature-triptych": make_layout_preset("Three Panel", 3, "layout-signature-triptych"),
    "signature-poster": make_layout_preset("Poster Mix", 4, "layout-signature-poster"),
    "signature-cinema": make_layout_preset("Cinema Frame", 2, "layout-signature-cinema"),
    "signature-atelier": make_layout_preset("Atelier Grid", 4, "layout-signature-atelier"),
    "signature-ribbon": make_layout_preset("Ribbon Story", 5, "layout-signature-ribbon"),
    "signature-salon": make_layout_preset("Salon Scatter", 4, "layout-signature-salon"),
    "signature-archive": make_layout_preset("Archive Notes", 4, "layout-signature-archive"),
    "signature-polaroid": make_layout_preset("Polaroid Table", 4, "layout-signature-polaroid"),
    "signature-compass": make_layout_preset("Compass Four", 4, "layout-signature-compass"),
    "signature-collage-five": make_layout_preset("Collage Five", 5, "layout-signature-collage-five"),
    "signature-orbit-five": make_layout_preset("Orbit Five", 5, "layout-signature-orbit-five"),
    "signature-postcard-wall": make_layout_preset("Postcard Wall", 5, "layout-signature-postcard-wall"),
    "signature-overlap-six": make_layout_preset("Overlap Six", 6, "layout-signature-overlap-six"),
    "signature-scattered-six": make_layout_preset("Scattered Six", 6, "layout-signature-scattered-six"),
    "signature-gallery-six": make_layout_preset("Gallery Six", 6, "layout-signature-gallery-six"),
    "playful-brush-five": make_layout_preset("Brush Scatter", 5, "layout-playful-brush-five"),
    "playful-polaroid-five": make_layout_preset("Polaroid Cascade", 5, "layout-playful-polaroid-five"),
    "playful-flight-six": make_layout_preset("Flight Path", 6, "layout-playful-flight-six"),
    "playful-drift-four": make_layout_preset("Soft Drift", 4, "layout-playful-drift-four"),
    "playful-orbit-six": make_layout_preset("Orbit Scatter", 6, "layout-playful-orbit-six"),
    "playful-diary-five": make_layout_preset("Diary Pieces", 5, "layout-playful-diary-five"),
    "playful-wave-five": make_layout_preset("Wave Story", 5, "layout-playful-wave-five"),
    "playful-tumble-six": make_layout_preset("Tumble Six", 6, "layout-playful-tumble-six"),
    "playful-travel-five": make_layout_preset("Travel Notes", 5, "layout-playful-travel-five"),
    "playful-cloud-six": make_layout_preset("Cloud Notes", 6, "layout-playful-cloud-six"),
    "playful-tilt-four": make_layout_preset("Tilted Four", 4, "layout-playful-tilt-four"),
    "playful-scrapbook-six": make_layout_preset("Scrapbook Six", 6, "layout-playful-scrapbook-six"),
}

POSTCARD_LAYOUT_ALIASES = {
    **{key: key for key in POSTCARD_LAYOUT_PRESETS},
    "single photo": "single",
    "single": "single",
    "split": "multi-split",
    "split duo": "multi-split",
    "memory trio": "multi-top-band",
    "trio": "multi-top-band",
    "four grid": "multi-grid",
    "grid": "multi-grid",
    "story strip": "multi-story",
    "story": "multi-story",
    "strip": "multi-story",
    "collection layout": "single",
    "freeform canvas": "single",
}

POSTCARD_FRAME_PRESETS = {
    "classic-ivory": {"label": "Classic Ivory"},
    "sunlit-paper": {"label": "Sunlit Paper"},
    "rose-keepsake": {"label": "Rose Keepsake"},
    "atlas-stamp": {"label": "Atlas Stamp"},
    "sea-voyage": {"label": "Sea Voyage"},
}

POSTCARD_FRAME_ALIASES = {
    "classic ivory": "classic-ivory",
    "classic-ivory": "classic-ivory",
    "sunlit paper": "sunlit-paper",
    "sunlit-paper": "sunlit-paper",
    "rose keepsake": "rose-keepsake",
    "rose-keepsake": "rose-keepsake",
    "atlas stamp": "atlas-stamp",
    "atlas-stamp": "atlas-stamp",
    "sea voyage": "sea-voyage",
    "sea-voyage": "sea-voyage",
}

POSTCARD_FONT_PRESETS = {
    "caveat": {
        "label": "Caveat",
        "font_family": '"Caveat", "Brush Script MT", cursive',
        "font_weight": "600",
        "color": "#6c4a30",
        "letter_spacing": "0.015em",
        "font_scale": "1",
        "max_font_ratio": "0.27",
        "min_font_size": "8",
        "line_gap_ratio": "0.2",
        "vertical_align": "0.18",
    },
    "dancing-script": {
        "label": "Dancing Script",
        "font_family": '"Dancing Script", "Brush Script MT", cursive',
        "font_weight": "600",
        "color": "#7b5641",
        "letter_spacing": "0.01em",
        "font_scale": "0.92",
        "max_font_ratio": "0.25",
        "min_font_size": "7.5",
        "line_gap_ratio": "0.18",
        "vertical_align": "0.16",
    },
    "allura": {
        "label": "Allura",
        "font_family": '"Allura", "Brush Script MT", cursive',
        "font_weight": "400",
        "color": "#8b6170",
        "letter_spacing": "0.01em",
        "font_scale": "0.8",
        "max_font_ratio": "0.225",
        "min_font_size": "7",
        "line_gap_ratio": "0.16",
        "vertical_align": "0.14",
    },
    "cormorant": {
        "label": "Cormorant Garamond",
        "font_family": '"Cormorant Garamond", Georgia, serif',
        "font_weight": "600",
        "color": "#775540",
        "letter_spacing": "0.008em",
        "font_scale": "0.9",
        "max_font_ratio": "0.245",
        "min_font_size": "7.5",
        "line_gap_ratio": "0.18",
        "vertical_align": "0.2",
    },
    "cinzel": {
        "label": "Cinzel",
        "font_family": '"Cinzel", Georgia, serif',
        "font_weight": "500",
        "color": "#70523d",
        "letter_spacing": "0.02em",
        "font_scale": "0.82",
        "max_font_ratio": "0.22",
        "min_font_size": "7",
        "line_gap_ratio": "0.17",
        "vertical_align": "0.18",
        "horizontal_padding_ratio": "0.03",
    },
    "romantic-script": {
        "label": "Romantic script",
        "font_family": '"Snell Roundhand", "Segoe Script", "Brush Script MT", cursive',
        "font_weight": "500",
        "color": "#6c4a30",
        "letter_spacing": "0.012em",
        "font_scale": "0.9",
        "max_font_ratio": "0.24",
        "min_font_size": "6",
        "line_gap_ratio": "0.18",
        "vertical_align": "0.16",
    },
    "handwritten-note": {
        "label": "Handwritten note",
        "font_family": '"Segoe Print", "Bradley Hand", "Marker Felt", cursive',
        "font_weight": "400",
        "color": "#6c4a30",
        "letter_spacing": "0.006em",
        "font_scale": "0.88",
        "max_font_ratio": "0.235",
        "min_font_size": "6",
        "line_gap_ratio": "0.18",
        "vertical_align": "0.16",
    },
    "elegant-signature": {
        "label": "Elegant signature",
        "font_family": '"Monotype Corsiva", "Apple Chancery", "URW Chancery L", cursive',
        "font_weight": "400",
        "color": "#6c4a30",
        "letter_spacing": "0.014em",
        "font_scale": "0.86",
        "max_font_ratio": "0.23",
        "min_font_size": "6",
        "line_gap_ratio": "0.17",
        "vertical_align": "0.15",
    },
    "classic-serif": {
        "label": "Classic serif",
        "font_family": '"Palatino Linotype", "Book Antiqua", Georgia, serif',
        "font_weight": "400",
        "color": "#5d4738",
        "letter_spacing": "0.006em",
        "font_scale": "1",
        "max_font_ratio": "0.255",
        "min_font_size": "6",
        "line_gap_ratio": "0.18",
        "vertical_align": "0.18",
    },
    "editorial-chic": {
        "label": "Editorial chic",
        "font_family": '"Didot", "Bodoni MT", "Times New Roman", serif',
        "font_weight": "500",
        "color": "#5d4738",
        "letter_spacing": "0.012em",
        "font_scale": "0.94",
        "max_font_ratio": "0.245",
        "min_font_size": "6",
        "line_gap_ratio": "0.18",
        "vertical_align": "0.18",
    },
}

POSTCARD_FONT_ALIASES = {
    "caveat": "caveat",
    "handwriting": "caveat",
    "dancing script": "dancing-script",
    "dancing-script": "dancing-script",
    "allura": "allura",
    "romantic script": "romantic-script",
    "romantic-script": "romantic-script",
    "handwritten note": "handwritten-note",
    "handwritten-note": "handwritten-note",
    "elegant signature": "elegant-signature",
    "elegant-signature": "elegant-signature",
    "cormorant": "cormorant",
    "cormorant garamond": "cormorant",
    "editorial serif": "cormorant",
    "cinzel": "cinzel",
    "classic serif": "classic-serif",
    "classic-serif": "classic-serif",
    "editorial chic": "editorial-chic",
    "editorial-chic": "editorial-chic",
}

TEMPLATES = {
    "Riva": {
        "front": "https://sendamemory.store/cdn/shop/files/Panorama_Splita.jpg?v=1775754558&width=1200",
        "back": "https://sendamemory.store/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },
    "Peristil": {
        "front": "https://sendamemory.store/cdn/shop/files/Peristil_65009f39-156f-4e41-a913-9e8d7896db8b.jpg?v=1775754568&width=1200",
        "back": "https://sendamemory.store/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },
    "Cathedral of Saint Domnius": {
        "front": "https://sendamemory.store/cdn/shop/files/Sv._Duje.jpg?v=1775754570&width=1200",
        "back": "https://sendamemory.store/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },"Adriatic View": {
        "front": "https://sendamemory.store/cdn/shop/files/AdriaticView.jpg?v=1776011389&width=1200",
        "back": "https://sendamemory.store/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },
    "Split From Above": {
        "front": "https://sendamemory.store/cdn/shop/files/SplitFromAbove.jpg?v=1776011510&width=1200",
        "back": "https://sendamemory.store/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },
    "Bell Tower of Split": {
        "front":"https://sendamemory.store/cdn/shop/files/BellTowerofSplit.jpg?v=1776011445&width=1200",
        "back": "https://sendamemory.store/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },
    "Old Town": {
        "front": "https://sendamemory.store/cdn/shop/files/Varos_790dd52a-bf89-41bf-a21e-a377b559083a.jpg?v=1775763079&width=1200",
        "back": "https://sendamemory.store/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },
    "Bird View": {
        "front": "https://sendamemory.store/cdn/shop/files/Splitizzraka.jpg?v=1775742362&width=1200",
        "back": "https://sendamemory.store/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },
}

VIEW_HTML = r"""
<!doctype html>
<html lang="hr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ postcard['product_title'] }} | Send a Memory</title>
  <meta name="description" content="A digital postcard from {{ postcard['from_name'] or 'someone special' }} to {{ postcard['to_name'] or 'someone special' }}.">
  <meta name="theme-color" content="#f4e7d3">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{{ postcard['product_title'] }} | Send a Memory">
  <meta property="og:description" content="A digital postcard from {{ postcard['from_name'] or 'someone special' }} to {{ postcard['to_name'] or 'someone special' }}.">
  <meta property="og:image" content="{{ postcard['front_image_url'] }}">
  <meta property="og:url" content="{{ request.url }}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{{ postcard['product_title'] }} | Send a Memory">
  <meta name="twitter:description" content="A digital postcard from {{ postcard['from_name'] or 'someone special' }} to {{ postcard['to_name'] or 'someone special' }}.">
  <meta name="twitter:image" content="{{ postcard['front_image_url'] }}">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Allura&family=Caveat:wght@500;600;700&family=Cinzel:wght@500;600&family=Cormorant+Garamond:wght@500;600;700&family=Dancing+Script:wght@500;600;700&family=Manrope:wght@400;500;600;700&display=swap');
    :root {
      --bg-top: #fbf7f2;
      --bg-mid: #efe6de;
      --bg-bottom: #e7ddd6;
      --ink: #2f2427;
      --muted: rgba(47, 36, 39, 0.58);
      --card-radius: 30px;
      --card-shadow: 0 38px 96px rgba(64, 94, 108, 0.16);
      --card-shadow-strong: 0 58px 140px rgba(44, 72, 89, 0.16);
      --glass: rgba(255, 255, 255, 0.7);
      --panel-bg: linear-gradient(180deg, rgba(255,255,255,0.82), rgba(255,248,238,0.68));
      --panel-border: rgba(255,255,255,0.84);
      --accent: #b78b4e;
      --message-font-size: {{ message_style.desktop_font_size }};
      --message-rotation: {{ message_style.rotation }};
      --ease: cubic-bezier(0.22, 1, 0.36, 1);
      --ease-soft: cubic-bezier(0.16, 1, 0.3, 1);
      --drift-x: 0px;
      --drift-y: 0px;
      --tilt-x: 0deg;
      --tilt-y: 0deg;
    }

    * {
      box-sizing: border-box;
    }

    html, body {
      margin: 0;
      min-height: 100%;
      font-family: "Manrope", Arial, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 50% 8%, rgba(234, 206, 163, 0.7), transparent 22%),
        radial-gradient(circle at 22% 28%, rgba(247, 233, 213, 0.84), transparent 26%),
        radial-gradient(circle at 82% 26%, rgba(222, 221, 233, 0.58), transparent 24%),
        linear-gradient(180deg, #f9f4ec 0%, #f3eadf 26%, #e8ddd3 58%, #d8d2d2 82%, #8f98ae 100%);
      overflow: hidden;
    }

    body::before,
    body::after {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
    }

    body::before {
      background:
        radial-gradient(circle at 50% 12%, rgba(222, 194, 149, 0.28), transparent 26%),
        linear-gradient(180deg, rgba(255,255,255,0.18), transparent 42%);
      opacity: 1;
    }

    body::after {
      background:
        radial-gradient(circle at center, transparent 0 54%, rgba(92, 145, 174, 0.1) 100%),
        linear-gradient(180deg, transparent 0%, transparent 74%, rgba(255,255,255,0.16) 100%);
    }

    .sun-glow,
    .sun-rays,
    .sea-haze,
    .sea-shimmer,
    .distant-city,
    .coastline,
    .coast-waves,
    .brand-bar,
    .stage-shadow {
      position: fixed;
      inset: 0;
      pointer-events: none;
    }

    .sun-glow::before {
      content: "";
      position: absolute;
      top: 4vh;
      left: 50%;
      transform: translateX(-50%);
      width: min(54vw, 620px);
      height: min(18vw, 190px);
      border-radius: 999px;
      background:
        radial-gradient(circle, rgba(248, 236, 216, 0.96), rgba(213, 182, 131, 0.46) 42%, rgba(245, 226, 203, 0.08) 72%, transparent 76%);
      filter: blur(34px);
      opacity: 0.98;
    }

    .sun-rays::before {
      content: "";
      position: absolute;
      top: 3vh;
      left: 50%;
      transform: translateX(-50%);
      width: min(72vw, 880px);
      height: 34vh;
      background:
        conic-gradient(from 180deg at 50% 0%, rgba(224, 193, 145, 0.16), rgba(255,255,255,0) 12%, rgba(226, 204, 170, 0.08) 22%, rgba(255,255,255,0) 34%, rgba(214, 205, 192, 0.06) 46%, rgba(255,255,255,0) 58%, rgba(223, 198, 165, 0.08) 70%, rgba(255,255,255,0) 82%, rgba(216, 190, 148, 0.14));
      clip-path: ellipse(54% 100% at 50% 0%);
      opacity: 0.55;
      filter: blur(1px);
    }

    .sea-haze::before {
      content: "";
      position: absolute;
      top: 18vh;
      left: 50%;
      transform: translateX(-50%);
      width: min(86vw, 1100px);
      height: min(32vw, 360px);
      border-radius: 999px;
      background:
        radial-gradient(circle, rgba(229, 220, 214, 0.34), rgba(229, 220, 214, 0.12) 58%, transparent 76%);
      filter: blur(56px);
      opacity: 0.8;
    }

    .sea-shimmer::before {
      content: "";
      position: absolute;
      left: 50%;
      bottom: 16vh;
      transform: translateX(-50%);
      width: min(36vw, 360px);
      height: 18vh;
      background:
        linear-gradient(180deg, rgba(255, 251, 233, 0.42), rgba(255,255,255,0) 78%);
      clip-path: polygon(47% 0%, 60% 26%, 72% 52%, 82% 100%, 18% 100%, 28% 52%, 40% 26%);
      filter: blur(10px);
      opacity: 0.72;
    }

    .brand-bar {
      top: 0;
      bottom: auto;
      height: 24vh;
      background:
        linear-gradient(180deg, rgba(255, 248, 228, 0.78), rgba(255,255,255,0));
      opacity: 0.96;
    }

    .coast-waves::before,
    .coast-waves::after {
      content: "";
      position: absolute;
      left: -8vw;
      right: -8vw;
      bottom: -2vh;
      border-radius: 50% 50% 0 0 / 18% 18% 0 0;
    }

    .coast-waves::before {
      height: 24vh;
      background:
        linear-gradient(180deg, rgba(229, 221, 216, 0.18), rgba(168, 154, 145, 0.72));
      clip-path: ellipse(74% 62% at 50% 100%);
      opacity: 0.95;
    }

    .coast-waves::after {
      height: 17vh;
      background:
        linear-gradient(180deg, rgba(140, 150, 176, 0.88), rgba(89, 95, 118, 0.98));
      clip-path: ellipse(82% 78% at 50% 100%);
    }

    .distant-city::before,
    .distant-city::after {
      content: "";
      position: absolute;
      left: 50%;
      transform: translateX(-50%);
      pointer-events: none;
    }

    .distant-city::before {
      bottom: 18.5vh;
      width: min(70vw, 760px);
      height: 11vh;
      background:
        linear-gradient(180deg, rgba(205, 192, 168, 0.06), rgba(146, 133, 114, 0.28));
      clip-path: polygon(0% 100%, 0% 78%, 8% 76%, 12% 54%, 15% 54%, 15% 74%, 22% 73%, 24% 60%, 27% 60%, 27% 78%, 34% 76%, 38% 66%, 40% 66%, 40% 82%, 48% 80%, 54% 68%, 57% 68%, 57% 78%, 66% 76%, 71% 58%, 73% 58%, 73% 84%, 83% 82%, 87% 70%, 90% 70%, 90% 86%, 100% 88%, 100% 100%);
      opacity: 0.42;
      filter: blur(0.4px);
    }

    .distant-city::after {
      bottom: 17.8vh;
      width: min(74vw, 820px);
      height: 3px;
      border-radius: 999px;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.48), transparent);
      opacity: 0.42;
    }

    .coastline::before,
    .coastline::after {
      content: "";
      position: absolute;
      left: 0;
      right: 0;
      bottom: 12.2vh;
      margin: 0 auto;
      pointer-events: none;
    }

    .coastline::before {
      width: min(92vw, 1100px);
      height: 10vh;
      background:
        linear-gradient(180deg, rgba(152, 189, 152, 0.08), rgba(89, 126, 95, 0.28));
      clip-path: polygon(0% 88%, 9% 76%, 16% 80%, 24% 64%, 33% 76%, 41% 58%, 50% 72%, 58% 62%, 67% 78%, 76% 60%, 85% 74%, 92% 66%, 100% 82%, 100% 100%, 0% 100%);
      filter: blur(0.6px);
      opacity: 0.44;
    }

    .coastline::after {
      width: min(78vw, 860px);
      height: 6vh;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.16), rgba(255,255,255,0));
      clip-path: polygon(0% 84%, 14% 70%, 28% 80%, 41% 60%, 55% 72%, 68% 58%, 82% 74%, 100% 82%, 100% 100%, 0% 100%);
      opacity: 0.38;
    }

    .stage-shadow::before {
      content: "";
      position: absolute;
      bottom: 12vh;
      left: 50%;
      transform: translateX(-50%) scaleX(0.84);
      width: min(52vw, 620px);
      height: 72px;
      border-radius: 999px;
      background: rgba(88, 124, 141, 0.18);
      filter: blur(30px);
      opacity: 0;
      transition: opacity 1s ease, transform 1.2s var(--ease);
    }

    body.is-ready .stage-shadow::before {
      opacity: 1;
      transform: translateX(-50%) scaleX(1);
    }

    .experience {
      position: relative;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px 20px 108px;
      z-index: 1;
    }

    .experience::before {
      content: "";
      position: absolute;
      inset: 5vh 8vw auto;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent);
      opacity: 0.55;
      pointer-events: none;
    }

    .brand-mark {
      position: fixed;
      top: 18px;
      left: 50%;
      transform: translateX(-50%) translateY(-10px) scale(0.96);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      min-width: min(36vw, 220px);
      min-height: 54px;
      padding: 12px 18px;
      border-radius: 999px;
      background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(255,250,239,0.8));
      border: 1px solid rgba(255,255,255,0.92);
      box-shadow: 0 18px 42px rgba(111, 141, 156, 0.14);
      backdrop-filter: blur(14px);
      opacity: 0;
      transition: opacity 0.9s ease, transform 1.1s var(--ease);
      z-index: 2;
    }

    .brand-mark img {
      width: min(34vw, 184px);
      max-height: 34px;
      height: auto;
      object-fit: contain;
      display: block;
      filter:
        drop-shadow(0 10px 28px rgba(173, 136, 74, 0.16))
        drop-shadow(0 2px 8px rgba(255, 255, 255, 0.28));
    }

    .brand-mark-fallback {
      display: none;
      align-items: center;
      gap: 10px;
      color: rgba(45, 36, 38, 0.94);
      font-weight: 700;
      letter-spacing: 0.04em;
      white-space: nowrap;
    }

    .brand-mark-fallback::before {
      content: "";
      width: 12px;
      height: 12px;
      border-radius: 999px;
      background: radial-gradient(circle at 35% 35%, #fbf1dc, #d3b173 58%, #a67c3d 100%);
      box-shadow: 0 0 0 6px rgba(183, 139, 78, 0.18);
    }

    .brand-mark.is-fallback img {
      display: none;
    }

    .brand-mark.is-fallback .brand-mark-fallback {
      display: inline-flex;
    }

    body.reveal-active .brand-mark,
    body.is-ready .brand-mark {
      opacity: 1;
      transform: translateX(-50%) translateY(0) scale(1);
    }

    .scene-layout {
      position: relative;
      width: min(100%, 1100px);
      display: grid;
      grid-template-columns: minmax(150px, 190px) minmax(0, 1fr) minmax(150px, 190px);
      gap: clamp(18px, 3vw, 32px);
      align-items: center;
      margin-top: 34px;
    }

    .story-stop {
      min-width: 0;
      display: grid;
      gap: 6px;
      padding: 0;
      background: none;
      border: 0;
      box-shadow: none;
      backdrop-filter: none;
      opacity: 0;
      transform: translateY(16px);
      transition: opacity 0.9s ease, transform 1s var(--ease);
      position: relative;
    }

    .story-stop-label {
      display: block;
      margin-bottom: 2px;
      font-size: 8px;
      font-weight: 700;
      letter-spacing: 0.24em;
      text-transform: uppercase;
      color: rgba(113, 101, 86, 0.72);
    }

    .story-stop-name {
      display: block;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-family: "Cormorant Garamond", Georgia, serif;
      font-size: clamp(21px, 2.2vw, 29px);
      line-height: 1.02;
      color: rgba(77, 55, 40, 0.94);
      letter-spacing: 0.01em;
    }

    .story-stop-meta {
      font-size: 10px;
      line-height: 1.4;
      color: rgba(119, 105, 88, 0.68);
    }

    .story-stop::before {
      content: "";
      position: absolute;
      top: 50%;
      width: 42px;
      height: 1px;
      background: linear-gradient(90deg, rgba(186, 162, 126, 0), rgba(186, 162, 126, 0.9));
      opacity: 0.85;
    }

    .story-stop-from {
      text-align: right;
      justify-self: end;
      padding-right: 58px;
    }

    .story-stop-to {
      text-align: left;
      justify-self: start;
      padding-left: 58px;
    }

    .story-stop-from::before {
      right: 0;
      transform: translateY(-50%);
    }

    .story-stop-to::before {
      left: 0;
      transform: translateY(-50%) scaleX(-1);
    }

    body.reveal-active .story-stop,
    body.is-ready .story-stop {
      opacity: 1;
      transform: translateY(0);
    }

    .scene {
      position: relative;
      width: min(80vw, 620px);
      aspect-ratio: 3 / 2;
      display: grid;
      place-items: center;
      perspective: 2200px;
      margin-top: 0;
      justify-self: center;
    }

    .scene::before {
      content: "";
      position: absolute;
      inset: -3% -4%;
      border-radius: 36px;
      background:
        radial-gradient(circle at 50% 18%, rgba(255, 244, 214, 0.58), rgba(255,255,255,0) 52%),
        linear-gradient(180deg, rgba(255,255,255,0.18), rgba(255,255,255,0));
      filter: blur(10px);
      opacity: 0.9;
      pointer-events: none;
    }

    .scene::after {
      content: "";
      position: absolute;
      inset: -4.5% -5.5%;
      border-radius: 42px;
      background: none;
      border: 1px solid rgba(255, 247, 233, 0.42);
      box-shadow:
        0 18px 46px rgba(92, 75, 51, 0.09),
        0 0 0 10px rgba(255, 250, 242, 0.12);
      filter: blur(14px);
      opacity: 0.42;
      transform: translateY(10px) scale(0.985);
      transition: opacity 1.1s ease, transform 1.1s var(--ease), box-shadow 1.1s ease;
      pointer-events: none;
    }

    body.reveal-active .scene::after,
    body.is-ready .scene::after {
      opacity: 0.62;
      transform: translateY(0) scale(1);
    }

    .reveal-halo,
    .reveal-flash,
    .reveal-sweep {
      position: absolute;
      pointer-events: none;
      opacity: 0;
      transition: opacity 1.2s ease, transform 1.4s var(--ease-soft), filter 1.2s ease;
    }

    .reveal-halo {
      width: min(68vw, 620px);
      aspect-ratio: 1;
      border-radius: 999px;
      border: 1px solid rgba(220, 188, 118, 0.24);
      mask-image: radial-gradient(circle at center, transparent 57%, black 58%, black 61%, transparent 62%);
      transform: scale(0.88);
      filter: drop-shadow(0 0 28px rgba(192, 154, 99, 0.2));
    }

    .reveal-flash {
      width: min(72vw, 580px);
      height: min(26vw, 170px);
      border-radius: 999px;
      background: radial-gradient(circle, rgba(255,248,233,0.92), rgba(255, 224, 163, 0.16) 50%, transparent 72%);
      filter: blur(20px);
      transform: scale(0.8);
    }

    .reveal-sweep {
      width: min(110vw, 1200px);
      height: 180px;
      background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.04) 26%, rgba(255,244,214,0.82) 50%, rgba(255,255,255,0.08) 74%, transparent 100%);
      filter: blur(18px);
      transform: translateX(-34%) translateY(-10px) rotate(-9deg) scaleX(0.88);
      mix-blend-mode: screen;
    }

    .ambient-orbs {
      position: absolute;
      inset: 4% 8% 10%;
      pointer-events: none;
    }

    .ambient-orbs span {
      position: absolute;
      display: block;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(248, 239, 224, 0.94), rgba(196, 167, 117, 0.2) 58%, transparent 72%);
      filter: blur(2px);
      opacity: 0;
      transition: opacity 1s ease;
      animation: orbFloat 6.2s ease-in-out infinite;
    }

    .ambient-orbs span:nth-child(1) {
      top: 8%;
      left: 10%;
      width: 18px;
      height: 18px;
      animation-delay: 0s;
    }

    .ambient-orbs span:nth-child(2) {
      right: 12%;
      top: 18%;
      width: 14px;
      height: 14px;
      animation-delay: 1.2s;
    }

    .ambient-orbs span:nth-child(3) {
      left: 20%;
      bottom: 20%;
      width: 10px;
      height: 10px;
      animation-delay: 2.1s;
    }

    body.reveal-active .reveal-halo,
    body.reveal-active .reveal-flash,
    body.reveal-active .reveal-sweep,
    body.is-ready .reveal-halo,
    body.is-ready .reveal-flash,
    body.is-ready .reveal-sweep,
    body.reveal-active .ambient-orbs span,
    body.is-ready .ambient-orbs span {
      opacity: 1;
    }

    body.reveal-active .reveal-halo,
    body.is-ready .reveal-halo {
      transform: scale(1);
      animation: haloPulse 5.8s ease-in-out infinite;
    }

    body.reveal-active .reveal-flash,
    body.is-ready .reveal-flash {
      transform: scale(1);
    }

    body.reveal-active .reveal-sweep {
      animation: revealSweep 1.35s var(--ease) forwards;
    }

    body.is-ready .reveal-sweep {
      opacity: 0;
      transform: translateX(44%) translateY(-20px) rotate(-7deg) scaleX(1.06);
    }

    .postcard-shell {
      position: relative;
      width: 100%;
      height: 100%;
      opacity: 0;
      filter: blur(16px);
      transform:
        translate3d(0, 72px, -90px)
        scale(0.9)
        rotateX(12deg);
      transform-style: preserve-3d;
      transition: opacity 1.2s ease, filter 1.25s ease, transform 1.75s var(--ease), box-shadow 1s ease;
      will-change: transform;
    }

    .postcard-shell::before {
      content: "";
      position: absolute;
      inset: -5% -3%;
      border-radius: 40px;
      background: radial-gradient(circle at 50% 40%, rgba(255, 244, 214, 0.3), transparent 62%);
      opacity: 0;
      filter: blur(16px);
      transition: opacity 1.2s ease;
      pointer-events: none;
    }

    body.reveal-start .postcard-shell {
      opacity: 0.54;
      filter: blur(8px);
      transform:
        translate3d(0, 24px, -26px)
        scale(0.96)
        rotateX(5deg);
    }

    body.reveal-active .postcard-shell {
      opacity: 1;
      filter: blur(0);
      transform:
        translate3d(0, -8px, 0)
        scale(1.018)
        rotateX(0deg);
    }

    body.reveal-active .postcard-shell::before,
    body.is-ready .postcard-shell::before {
      opacity: 1;
    }

    body.is-ready .postcard-shell {
      opacity: 1;
      filter: blur(0);
      transform:
        translate3d(var(--drift-x), calc(var(--drift-y) * 0.45), 0)
        scale(1.01)
        rotateX(var(--tilt-x))
        rotateY(var(--tilt-y));
      animation: postcardFloat 6.8s ease-in-out infinite;
    }

    .flip-target {
      appearance: none;
      border: 0;
      padding: 0;
      margin: 0;
      width: 100%;
      height: 100%;
      background: none;
      cursor: pointer;
      border-radius: calc(var(--card-radius) + 2px);
      position: relative;
      transform-style: preserve-3d;
    }

    .flip-target:focus-visible {
      outline: 2px solid rgba(74, 122, 145, 0.34);
      outline-offset: 10px;
    }

    .card-glow {
      position: absolute;
      inset: -18px;
      border-radius: calc(var(--card-radius) + 18px);
      background: none;
      box-shadow:
        0 0 0 1px rgba(255, 244, 221, 0.24),
        0 18px 42px rgba(96, 79, 54, 0.12),
        0 0 28px rgba(239, 220, 183, 0.14);
      filter: blur(10px);
      opacity: 0.74;
      transform: translateZ(-8px);
      transition: opacity 0.55s ease, filter 0.55s ease, transform 0.8s ease;
    }

    .card-glow::before {
      content: "";
      position: absolute;
      inset: 8px;
      border-radius: calc(var(--card-radius) + 6px);
      border: 1px solid rgba(255, 244, 221, 0.44);
      opacity: 0.62;
    }

    .card-glow::after {
      content: "";
      position: absolute;
      inset: -2px;
      border-radius: calc(var(--card-radius) + 14px);
      box-shadow:
        inset 0 0 0 1px rgba(255,255,255,0.14),
        0 22px 54px rgba(102, 86, 58, 0.06);
      opacity: 0.82;
    }

    .flip-target:hover .card-glow {
      opacity: 0.86;
      filter: blur(12px);
    }

    .postcard {
      position: relative;
      width: 100%;
      height: 100%;
      transform-style: preserve-3d;
      transition: transform 1.06s var(--ease);
      will-change: transform;
    }

    .postcard::after {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: var(--card-radius);
      background: linear-gradient(115deg, transparent 18%, rgba(255,255,255,0.36) 34%, rgba(255,255,255,0.08) 44%, transparent 58%);
      opacity: 0;
      transform: translateX(-26%) skewX(-10deg);
      pointer-events: none;
      z-index: 3;
    }

    body.reveal-active .postcard::after {
      animation: postcardGleam 1.45s var(--ease) 0.18s forwards;
    }

    .postcard.flipped {
      transform: rotateY(180deg);
    }

    .face {
      position: absolute;
      inset: 0;
      overflow: hidden;
      border-radius: var(--card-radius);
      backface-visibility: hidden;
      -webkit-backface-visibility: hidden;
      box-shadow: var(--card-shadow), var(--card-shadow-strong);
      border: 1px solid rgba(255,255,255,0.86);
      background: white;
    }

    .face::before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(135deg, rgba(255,255,255,0.14), transparent 18%),
        linear-gradient(180deg, rgba(255,255,255,0.05), transparent 22%);
      pointer-events: none;
      z-index: 2;
    }

    .face img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }

    .postcard-front-art {
      --front-gap: 2px;
      --front-pad: 2px;
      --front-slot-pad: 0px;
      --front-frame-gap: linear-gradient(180deg, #ece2d3 0%, #e2d4c0 100%);
      --front-frame-surface: linear-gradient(180deg, #fbf6ee 0%, #efe5d8 100%);
      --front-frame-border: rgba(150, 126, 92, 0.2);
      position: relative;
      width: 100%;
      height: 100%;
      display: grid;
      gap: var(--front-gap);
      padding: var(--front-pad);
      background: var(--front-frame-gap);
      isolation: isolate;
    }

    .postcard-front-art::before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        radial-gradient(circle at top, rgba(255,255,255,0.2), transparent 44%),
        linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.01));
      pointer-events: none;
      z-index: 0;
    }

    .postcard-front-background {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      pointer-events: none;
      z-index: 0;
    }

    .postcard-front-art.is-single {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr;
    }

    .postcard-front-art.is-split {
      grid-template-columns: 1fr 1fr;
      grid-template-rows: 1fr;
    }

    .postcard-front-art.is-trio {
      grid-template-columns: 1.16fr 0.84fr;
      grid-template-rows: 1fr 1fr;
    }

    .postcard-front-art.is-grid {
      grid-template-columns: 1fr 1fr;
      grid-template-rows: 1fr 1fr;
    }

    .postcard-front-art.is-story {
      grid-template-columns: repeat(6, 1fr);
      grid-template-rows: 1fr 1fr;
    }

    .postcard-front-art[class*="layout-"] {
      grid-template-columns: repeat(12, 1fr);
      grid-template-rows: repeat(8, 1fr);
      gap: 8px;
      padding: 10px;
      background: #fff;
    }

    .postcard-front-art.layout-single-full .slot-a,
    .postcard-front-art.layout-signature-hero .slot-a { grid-column: 1 / 13; grid-row: 1 / 9; }
    .postcard-front-art.layout-single-classic .slot-a { grid-column: 2 / 12; grid-row: 2 / 8; }
    .postcard-front-art.layout-single-portrait .slot-a { grid-column: 4 / 10; grid-row: 1 / 9; }
    .postcard-front-art.layout-single-square .slot-a { grid-column: 3 / 11; grid-row: 1 / 8; }
    .postcard-front-art.layout-multi-split .slot-a { grid-column: 1 / 7; grid-row: 1 / 9; }
    .postcard-front-art.layout-multi-split .slot-b { grid-column: 7 / 13; grid-row: 1 / 9; }
    .postcard-front-art.layout-multi-sidebar .slot-a { grid-column: 1 / 9; grid-row: 1 / 9; }
    .postcard-front-art.layout-multi-sidebar .slot-b { grid-column: 9 / 13; grid-row: 1 / 9; }
    .postcard-front-art.layout-multi-top-band .slot-a { grid-column: 1 / 7; grid-row: 1 / 5; }
    .postcard-front-art.layout-multi-top-band .slot-b { grid-column: 7 / 13; grid-row: 1 / 5; }
    .postcard-front-art.layout-multi-top-band .slot-c { grid-column: 1 / 13; grid-row: 5 / 9; }
    .postcard-front-art.layout-multi-feature-stack .slot-a { grid-column: 1 / 8; grid-row: 1 / 9; }
    .postcard-front-art.layout-multi-feature-stack .slot-b { grid-column: 8 / 13; grid-row: 1 / 5; }
    .postcard-front-art.layout-multi-feature-stack .slot-c { grid-column: 8 / 13; grid-row: 5 / 9; }
    .postcard-front-art.layout-multi-grid .slot-a { grid-column: 1 / 7; grid-row: 1 / 5; }
    .postcard-front-art.layout-multi-grid .slot-b { grid-column: 7 / 13; grid-row: 1 / 5; }
    .postcard-front-art.layout-multi-grid .slot-c { grid-column: 1 / 7; grid-row: 5 / 9; }
    .postcard-front-art.layout-multi-grid .slot-d { grid-column: 7 / 13; grid-row: 5 / 9; }
    .postcard-front-art.layout-multi-window .slot-a { grid-column: 1 / 9; grid-row: 1 / 9; }
    .postcard-front-art.layout-multi-window .slot-b { grid-column: 9 / 13; grid-row: 1 / 4; }
    .postcard-front-art.layout-multi-window .slot-c { grid-column: 9 / 13; grid-row: 4 / 6; }
    .postcard-front-art.layout-multi-window .slot-d { grid-column: 9 / 13; grid-row: 6 / 9; }
    .postcard-front-art.layout-multi-strips .slot-a { grid-column: 1 / 4; grid-row: 1 / 9; }
    .postcard-front-art.layout-multi-strips .slot-b { grid-column: 4 / 7; grid-row: 1 / 9; }
    .postcard-front-art.layout-multi-strips .slot-c { grid-column: 7 / 10; grid-row: 1 / 9; }
    .postcard-front-art.layout-multi-strips .slot-d { grid-column: 10 / 13; grid-row: 1 / 9; }
    .postcard-front-art.layout-multi-mosaic .slot-a { grid-column: 1 / 5; grid-row: 1 / 5; }
    .postcard-front-art.layout-multi-mosaic .slot-b { grid-column: 5 / 9; grid-row: 1 / 3; }
    .postcard-front-art.layout-multi-mosaic .slot-c { grid-column: 9 / 13; grid-row: 1 / 5; }
    .postcard-front-art.layout-multi-mosaic .slot-d { grid-column: 5 / 9; grid-row: 3 / 5; }
    .postcard-front-art.layout-multi-mosaic .slot-e { grid-column: 1 / 13; grid-row: 5 / 9; }
    .postcard-front-art.layout-multi-story .slot-a { grid-column: 1 / 5; grid-row: 1 / 4; }
    .postcard-front-art.layout-multi-story .slot-b { grid-column: 5 / 9; grid-row: 1 / 4; }
    .postcard-front-art.layout-multi-story .slot-c { grid-column: 9 / 13; grid-row: 1 / 4; }
    .postcard-front-art.layout-multi-story .slot-d { grid-column: 1 / 7; grid-row: 4 / 9; }
    .postcard-front-art.layout-multi-story .slot-e { grid-column: 7 / 13; grid-row: 4 / 9; }
    .postcard-front-art.layout-multi-cascade .slot-a { grid-column: 1 / 4; grid-row: 1 / 4; }
    .postcard-front-art.layout-multi-cascade .slot-b { grid-column: 4 / 8; grid-row: 1 / 5; }
    .postcard-front-art.layout-multi-cascade .slot-c { grid-column: 8 / 13; grid-row: 1 / 4; }
    .postcard-front-art.layout-multi-cascade .slot-d { grid-column: 1 / 6; grid-row: 4 / 9; }
    .postcard-front-art.layout-multi-cascade .slot-e { grid-column: 6 / 13; grid-row: 4 / 9; }
    .postcard-front-art.layout-multi-six-grid .slot-a { grid-column: 1 / 5; grid-row: 1 / 5; }
    .postcard-front-art.layout-multi-six-grid .slot-b { grid-column: 5 / 9; grid-row: 1 / 5; }
    .postcard-front-art.layout-multi-six-grid .slot-c { grid-column: 9 / 13; grid-row: 1 / 5; }
    .postcard-front-art.layout-multi-six-grid .slot-d { grid-column: 1 / 5; grid-row: 5 / 9; }
    .postcard-front-art.layout-multi-six-grid .slot-e { grid-column: 5 / 9; grid-row: 5 / 9; }
    .postcard-front-art.layout-multi-six-grid .slot-f { grid-column: 9 / 13; grid-row: 5 / 9; }
    .postcard-front-art.layout-multi-contact-sheet .slot-a { grid-column: 1 / 7; grid-row: 1 / 3; }
    .postcard-front-art.layout-multi-contact-sheet .slot-b { grid-column: 7 / 13; grid-row: 1 / 3; }
    .postcard-front-art.layout-multi-contact-sheet .slot-c { grid-column: 1 / 7; grid-row: 3 / 6; }
    .postcard-front-art.layout-multi-contact-sheet .slot-d { grid-column: 7 / 13; grid-row: 3 / 6; }
    .postcard-front-art.layout-multi-contact-sheet .slot-e { grid-column: 1 / 7; grid-row: 6 / 9; }
    .postcard-front-art.layout-multi-contact-sheet .slot-f { grid-column: 7 / 13; grid-row: 6 / 9; }
    .postcard-front-art.layout-multi-gallery-ribbon .slot-a { grid-column: 1 / 7; grid-row: 1 / 4; }
    .postcard-front-art.layout-multi-gallery-ribbon .slot-b { grid-column: 7 / 13; grid-row: 1 / 4; }
    .postcard-front-art.layout-multi-gallery-ribbon .slot-c { grid-column: 1 / 4; grid-row: 4 / 9; }
    .postcard-front-art.layout-multi-gallery-ribbon .slot-d { grid-column: 4 / 7; grid-row: 4 / 9; }
    .postcard-front-art.layout-multi-gallery-ribbon .slot-e { grid-column: 7 / 10; grid-row: 4 / 9; }
    .postcard-front-art.layout-multi-gallery-ribbon .slot-f { grid-column: 10 / 13; grid-row: 4 / 9; }

    .postcard-front-art.layout-signature-duo .slot-a { grid-column: 1 / 8; grid-row: 2 / 8; }
    .postcard-front-art.layout-signature-duo .slot-b { grid-column: 8 / 13; grid-row: 1 / 7; }
    .postcard-front-art.layout-signature-triptych .slot-a { grid-column: 1 / 5; grid-row: 2 / 8; }
    .postcard-front-art.layout-signature-triptych .slot-b { grid-column: 5 / 9; grid-row: 1 / 7; }
    .postcard-front-art.layout-signature-triptych .slot-c { grid-column: 9 / 13; grid-row: 2 / 8; }
    .postcard-front-art.layout-signature-poster .slot-a { grid-column: 2 / 6; grid-row: 2 / 6; }
    .postcard-front-art.layout-signature-poster .slot-b { grid-column: 6 / 10; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-poster .slot-c { grid-column: 10 / 13; grid-row: 2 / 6; }
    .postcard-front-art.layout-signature-poster .slot-d { grid-column: 3 / 11; grid-row: 6 / 9; }
    .postcard-front-art.layout-signature-cinema .slot-a { grid-column: 1 / 13; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-cinema .slot-b { grid-column: 3 / 11; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-atelier .slot-a { grid-column: 1 / 6; grid-row: 1 / 9; }
    .postcard-front-art.layout-signature-atelier .slot-b { grid-column: 6 / 10; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-atelier .slot-c { grid-column: 10 / 13; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-atelier .slot-d { grid-column: 6 / 13; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-ribbon .slot-a { grid-column: 1 / 8; grid-row: 1 / 6; }
    .postcard-front-art.layout-signature-ribbon .slot-b { grid-column: 8 / 13; grid-row: 1 / 4; }
    .postcard-front-art.layout-signature-ribbon .slot-c { grid-column: 8 / 13; grid-row: 4 / 6; }
    .postcard-front-art.layout-signature-ribbon .slot-d { grid-column: 1 / 5; grid-row: 6 / 9; }
    .postcard-front-art.layout-signature-ribbon .slot-e { grid-column: 5 / 13; grid-row: 6 / 9; }
    .postcard-front-art.layout-signature-salon .slot-a { grid-column: 1 / 7; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-salon .slot-b { grid-column: 7 / 13; grid-row: 2 / 6; }
    .postcard-front-art.layout-signature-salon .slot-c { grid-column: 2 / 6; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-salon .slot-d { grid-column: 6 / 12; grid-row: 6 / 9; }
    .postcard-front-art.layout-signature-archive .slot-a { grid-column: 1 / 5; grid-row: 1 / 4; }
    .postcard-front-art.layout-signature-archive .slot-b { grid-column: 5 / 13; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-archive .slot-c { grid-column: 1 / 8; grid-row: 4 / 9; }
    .postcard-front-art.layout-signature-archive .slot-d { grid-column: 8 / 13; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-polaroid .slot-a { grid-column: 2 / 6; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-polaroid .slot-b { grid-column: 7 / 12; grid-row: 1 / 4; }
    .postcard-front-art.layout-signature-polaroid .slot-c { grid-column: 1 / 7; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-polaroid .slot-d { grid-column: 7 / 13; grid-row: 4 / 9; }
    .postcard-front-art.layout-signature-compass .slot-a { grid-column: 1 / 6; grid-row: 2 / 6; }
    .postcard-front-art.layout-signature-compass .slot-b { grid-column: 7 / 13; grid-row: 1 / 4; }
    .postcard-front-art.layout-signature-compass .slot-c { grid-column: 2 / 7; grid-row: 6 / 9; }
    .postcard-front-art.layout-signature-compass .slot-d { grid-column: 8 / 12; grid-row: 4 / 8; }
    .postcard-front-art.layout-signature-collage-five .slot-a { grid-column: 1 / 7; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-collage-five .slot-b { grid-column: 7 / 13; grid-row: 1 / 4; }
    .postcard-front-art.layout-signature-collage-five .slot-c { grid-column: 1 / 5; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-collage-five .slot-d { grid-column: 5 / 9; grid-row: 4 / 8; }
    .postcard-front-art.layout-signature-collage-five .slot-e { grid-column: 9 / 13; grid-row: 4 / 9; }
    .postcard-front-art.layout-signature-orbit-five .slot-a { grid-column: 4 / 10; grid-row: 3 / 7; }
    .postcard-front-art.layout-signature-orbit-five .slot-b { grid-column: 1 / 5; grid-row: 1 / 4; }
    .postcard-front-art.layout-signature-orbit-five .slot-c { grid-column: 8 / 13; grid-row: 1 / 4; }
    .postcard-front-art.layout-signature-orbit-five .slot-d { grid-column: 1 / 6; grid-row: 6 / 9; }
    .postcard-front-art.layout-signature-orbit-five .slot-e { grid-column: 8 / 13; grid-row: 6 / 9; }
    .postcard-front-art.layout-signature-postcard-wall .slot-a { grid-column: 1 / 5; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-postcard-wall .slot-b { grid-column: 5 / 9; grid-row: 2 / 6; }
    .postcard-front-art.layout-signature-postcard-wall .slot-c { grid-column: 9 / 13; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-postcard-wall .slot-d { grid-column: 2 / 7; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-postcard-wall .slot-e { grid-column: 7 / 12; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-overlap-six .slot-a { grid-column: 1 / 6; grid-row: 1 / 4; }
    .postcard-front-art.layout-signature-overlap-six .slot-b { grid-column: 5 / 10; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-overlap-six .slot-c { grid-column: 9 / 13; grid-row: 2 / 6; }
    .postcard-front-art.layout-signature-overlap-six .slot-d { grid-column: 1 / 5; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-overlap-six .slot-e { grid-column: 5 / 9; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-overlap-six .slot-f { grid-column: 9 / 13; grid-row: 6 / 9; }
    .postcard-front-art.layout-signature-scattered-six .slot-a { grid-column: 1 / 4; grid-row: 2 / 5; }
    .postcard-front-art.layout-signature-scattered-six .slot-b { grid-column: 4 / 8; grid-row: 1 / 4; }
    .postcard-front-art.layout-signature-scattered-six .slot-c { grid-column: 8 / 13; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-scattered-six .slot-d { grid-column: 1 / 6; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-scattered-six .slot-e { grid-column: 6 / 10; grid-row: 4 / 8; }
    .postcard-front-art.layout-signature-scattered-six .slot-f { grid-column: 10 / 13; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-gallery-six .slot-a { grid-column: 1 / 7; grid-row: 1 / 5; }
    .postcard-front-art.layout-signature-gallery-six .slot-b { grid-column: 7 / 13; grid-row: 1 / 4; }
    .postcard-front-art.layout-signature-gallery-six .slot-c { grid-column: 1 / 4; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-gallery-six .slot-d { grid-column: 4 / 8; grid-row: 5 / 9; }
    .postcard-front-art.layout-signature-gallery-six .slot-e { grid-column: 8 / 10; grid-row: 4 / 9; }
    .postcard-front-art.layout-signature-gallery-six .slot-f { grid-column: 10 / 13; grid-row: 4 / 9; }

    .postcard-front-art[class*="layout-playful-"] { display: block; gap: 0; background: #fff; }
    .postcard-front-art[class*="layout-playful-"] .postcard-front-slot {
      position: absolute !important;
      transform: rotate(var(--front-rotate, 0deg));
      transform-origin: center;
      border: 0;
      background: #dfe7ff !important;
    }
    .postcard-front-art[class*="layout-playful-"] .postcard-front-slot-media { background: #dfe7ff !important; }
    .postcard-front-art.layout-playful-brush-five .slot-a { left: 8%; top: 7%; width: 23%; height: 42%; --front-rotate: -5deg; }
    .postcard-front-art.layout-playful-brush-five .slot-b { left: 39%; top: 23%; width: 23%; height: 39%; --front-rotate: 4deg; }
    .postcard-front-art.layout-playful-brush-five .slot-c { left: 71%; top: 10%; width: 20%; height: 38%; --front-rotate: 4deg; }
    .postcard-front-art.layout-playful-brush-five .slot-d { left: 9%; top: 61%; width: 25%; height: 27%; --front-rotate: 9deg; }
    .postcard-front-art.layout-playful-brush-five .slot-e { left: 70%; top: 60%; width: 23%; height: 25%; --front-rotate: -4deg; }
    .postcard-front-art.layout-playful-polaroid-five .slot-a { left: 4%; top: 13%; width: 29%; height: 56%; --front-rotate: -10deg; }
    .postcard-front-art.layout-playful-polaroid-five .slot-b { left: 35%; top: 4%; width: 27%; height: 56%; --front-rotate: 4deg; z-index: 4; }
    .postcard-front-art.layout-playful-polaroid-five .slot-c { left: 64%; top: 14%; width: 32%; height: 48%; --front-rotate: 8deg; }
    .postcard-front-art.layout-playful-polaroid-five .slot-d { left: 17%; top: 62%; width: 28%; height: 32%; --front-rotate: -7deg; }
    .postcard-front-art.layout-playful-polaroid-five .slot-e { left: 55%; top: 58%; width: 34%; height: 33%; --front-rotate: -9deg; }
    .postcard-front-art.layout-playful-flight-six .slot-a { left: 7%; top: 8%; width: 27%; height: 31%; --front-rotate: -8deg; }
    .postcard-front-art.layout-playful-flight-six .slot-b { left: 67%; top: 10%; width: 26%; height: 31%; --front-rotate: 6deg; }
    .postcard-front-art.layout-playful-flight-six .slot-c { left: 4%; top: 42%; width: 28%; height: 28%; --front-rotate: 8deg; }
    .postcard-front-art.layout-playful-flight-six .slot-d { left: 70%; top: 44%; width: 24%; height: 28%; --front-rotate: -5deg; }
    .postcard-front-art.layout-playful-flight-six .slot-e { left: 10%; top: 72%; width: 29%; height: 23%; --front-rotate: -6deg; }
    .postcard-front-art.layout-playful-flight-six .slot-f { left: 43%; top: 71%; width: 28%; height: 23%; --front-rotate: 9deg; }
    .postcard-front-art.layout-playful-drift-four .slot-a { left: 10%; top: 12%; width: 28%; height: 36%; --front-rotate: -8deg; }
    .postcard-front-art.layout-playful-drift-four .slot-b { left: 53%; top: 9%; width: 32%; height: 34%; --front-rotate: 7deg; }
    .postcard-front-art.layout-playful-drift-four .slot-c { left: 18%; top: 58%; width: 29%; height: 30%; --front-rotate: 8deg; }
    .postcard-front-art.layout-playful-drift-four .slot-d { left: 60%; top: 55%; width: 27%; height: 30%; --front-rotate: -6deg; }
    .postcard-front-art.layout-playful-orbit-six .slot-a { left: 39%; top: 27%; width: 24%; height: 36%; --front-rotate: 3deg; }
    .postcard-front-art.layout-playful-orbit-six .slot-b { left: 12%; top: 8%; width: 23%; height: 28%; --front-rotate: -7deg; }
    .postcard-front-art.layout-playful-orbit-six .slot-c { left: 65%; top: 9%; width: 23%; height: 28%; --front-rotate: 8deg; }
    .postcard-front-art.layout-playful-orbit-six .slot-d { left: 8%; top: 55%; width: 25%; height: 29%; --front-rotate: 6deg; }
    .postcard-front-art.layout-playful-orbit-six .slot-e { left: 67%; top: 56%; width: 24%; height: 28%; --front-rotate: -7deg; }
    .postcard-front-art.layout-playful-orbit-six .slot-f { left: 38%; top: 72%; width: 25%; height: 21%; --front-rotate: -3deg; }
    .postcard-front-art.layout-playful-diary-five .slot-a { left: 6%; top: 9%; width: 31%; height: 31%; --front-rotate: 5deg; }
    .postcard-front-art.layout-playful-diary-five .slot-b { left: 42%; top: 8%; width: 24%; height: 42%; --front-rotate: -5deg; }
    .postcard-front-art.layout-playful-diary-five .slot-c { left: 69%; top: 17%; width: 24%; height: 28%; --front-rotate: 8deg; }
    .postcard-front-art.layout-playful-diary-five .slot-d { left: 13%; top: 55%; width: 32%; height: 30%; --front-rotate: -8deg; }
    .postcard-front-art.layout-playful-diary-five .slot-e { left: 52%; top: 56%; width: 34%; height: 29%; --front-rotate: 5deg; }
    .postcard-front-art.layout-playful-wave-five .slot-a { left: 7%; top: 17%; width: 23%; height: 30%; --front-rotate: -7deg; }
    .postcard-front-art.layout-playful-wave-five .slot-b { left: 30%; top: 35%; width: 22%; height: 30%; --front-rotate: 7deg; }
    .postcard-front-art.layout-playful-wave-five .slot-c { left: 51%; top: 15%; width: 24%; height: 32%; --front-rotate: -5deg; }
    .postcard-front-art.layout-playful-wave-five .slot-d { left: 70%; top: 49%; width: 23%; height: 29%; --front-rotate: 8deg; }
    .postcard-front-art.layout-playful-wave-five .slot-e { left: 13%; top: 68%; width: 27%; height: 23%; --front-rotate: -4deg; }
    .postcard-front-art.layout-playful-tumble-six .slot-a { left: 5%; top: 8%; width: 24%; height: 32%; --front-rotate: -10deg; }
    .postcard-front-art.layout-playful-tumble-six .slot-b { left: 29%; top: 12%; width: 25%; height: 29%; --front-rotate: 6deg; }
    .postcard-front-art.layout-playful-tumble-six .slot-c { left: 58%; top: 8%; width: 30%; height: 34%; --front-rotate: 9deg; }
    .postcard-front-art.layout-playful-tumble-six .slot-d { left: 10%; top: 50%; width: 28%; height: 29%; --front-rotate: 7deg; }
    .postcard-front-art.layout-playful-tumble-six .slot-e { left: 43%; top: 48%; width: 23%; height: 34%; --front-rotate: -6deg; }
    .postcard-front-art.layout-playful-tumble-six .slot-f { left: 70%; top: 55%; width: 22%; height: 29%; --front-rotate: -8deg; }
    .postcard-front-art.layout-playful-travel-five .slot-a { left: 8%; top: 10%; width: 30%; height: 39%; --front-rotate: -6deg; }
    .postcard-front-art.layout-playful-travel-five .slot-b { left: 43%; top: 9%; width: 25%; height: 31%; --front-rotate: 8deg; }
    .postcard-front-art.layout-playful-travel-five .slot-c { left: 69%; top: 25%; width: 24%; height: 31%; --front-rotate: -7deg; }
    .postcard-front-art.layout-playful-travel-five .slot-d { left: 16%; top: 61%; width: 28%; height: 28%; --front-rotate: 7deg; }
    .postcard-front-art.layout-playful-travel-five .slot-e { left: 51%; top: 57%; width: 30%; height: 30%; --front-rotate: -4deg; }
    .postcard-front-art.layout-playful-cloud-six .slot-a { left: 8%; top: 7%; width: 22%; height: 27%; --front-rotate: 6deg; }
    .postcard-front-art.layout-playful-cloud-six .slot-b { left: 38%; top: 9%; width: 25%; height: 28%; --front-rotate: -7deg; }
    .postcard-front-art.layout-playful-cloud-six .slot-c { left: 68%; top: 8%; width: 22%; height: 28%; --front-rotate: 7deg; }
    .postcard-front-art.layout-playful-cloud-six .slot-d { left: 17%; top: 43%; width: 24%; height: 29%; --front-rotate: -4deg; }
    .postcard-front-art.layout-playful-cloud-six .slot-e { left: 50%; top: 42%; width: 26%; height: 30%; --front-rotate: 6deg; }
    .postcard-front-art.layout-playful-cloud-six .slot-f { left: 35%; top: 72%; width: 29%; height: 21%; --front-rotate: -5deg; }
    .postcard-front-art.layout-playful-tilt-four .slot-a { left: 9%; top: 9%; width: 34%; height: 36%; --front-rotate: -6deg; }
    .postcard-front-art.layout-playful-tilt-four .slot-b { left: 56%; top: 10%; width: 32%; height: 35%; --front-rotate: 6deg; }
    .postcard-front-art.layout-playful-tilt-four .slot-c { left: 12%; top: 57%; width: 32%; height: 31%; --front-rotate: 7deg; }
    .postcard-front-art.layout-playful-tilt-four .slot-d { left: 56%; top: 55%; width: 33%; height: 32%; --front-rotate: -6deg; }
    .postcard-front-art.layout-playful-scrapbook-six .slot-a { left: 6%; top: 14%; width: 28%; height: 28%; --front-rotate: -8deg; }
    .postcard-front-art.layout-playful-scrapbook-six .slot-b { left: 35%; top: 6%; width: 24%; height: 35%; --front-rotate: 5deg; }
    .postcard-front-art.layout-playful-scrapbook-six .slot-c { left: 62%; top: 15%; width: 31%; height: 29%; --front-rotate: 7deg; }
    .postcard-front-art.layout-playful-scrapbook-six .slot-d { left: 8%; top: 55%; width: 24%; height: 30%; --front-rotate: 8deg; }
    .postcard-front-art.layout-playful-scrapbook-six .slot-e { left: 37%; top: 51%; width: 25%; height: 33%; --front-rotate: -7deg; }
    .postcard-front-art.layout-playful-scrapbook-six .slot-f { left: 66%; top: 57%; width: 25%; height: 28%; --front-rotate: -5deg; }

    .postcard-front-slot {
      position: relative;
      z-index: 1;
      min-width: 0;
      min-height: 0;
      overflow: hidden;
      padding: var(--front-slot-pad);
      background: var(--front-frame-surface);
      border: 1px solid var(--front-frame-border);
    }

    .postcard-front-slot-media {
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: rgba(255, 255, 255, 0.82);
    }

    .postcard-front-slot-media img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }

    .postcard-front-art.is-trio .slot-a {
      grid-column: 1;
      grid-row: 1 / span 2;
    }

    .postcard-front-art.is-trio .slot-b {
      grid-column: 2;
      grid-row: 1;
    }

    .postcard-front-art.is-trio .slot-c {
      grid-column: 2;
      grid-row: 2;
    }

    .postcard-front-art.is-story .slot-a {
      grid-column: 1 / span 2;
      grid-row: 1;
    }

    .postcard-front-art.is-story .slot-b {
      grid-column: 3 / span 2;
      grid-row: 1;
    }

    .postcard-front-art.is-story .slot-c {
      grid-column: 5 / span 2;
      grid-row: 1;
    }

    .postcard-front-art.is-story .slot-d {
      grid-column: 1 / span 3;
      grid-row: 2;
    }

    .postcard-front-art.is-story .slot-e {
      grid-column: 4 / span 3;
      grid-row: 2;
    }

    .postcard-front-art.frame-classic-ivory {
      --front-frame-gap: linear-gradient(180deg, #ece2d3 0%, #e2d4c0 100%);
      --front-frame-surface: linear-gradient(180deg, #fbf6ee 0%, #efe5d8 100%);
      --front-frame-border: rgba(150, 126, 92, 0.2);
    }

    .postcard-front-art.frame-sunlit-paper {
      --front-frame-gap: linear-gradient(180deg, #f1e1c1 0%, #e8d5b1 100%);
      --front-frame-surface: linear-gradient(180deg, #fff4dc 0%, #f6e5c4 100%);
      --front-frame-border: rgba(177, 137, 73, 0.24);
    }

    .postcard-front-art.frame-rose-keepsake {
      --front-frame-gap: linear-gradient(180deg, #efd8d0 0%, #e5c5bc 100%);
      --front-frame-surface: linear-gradient(180deg, #fff0ec 0%, #f2d7ce 100%);
      --front-frame-border: rgba(171, 111, 96, 0.22);
    }

    .postcard-front-art.frame-atlas-stamp {
      --front-frame-gap: linear-gradient(180deg, #d7d4c8 0%, #c7bfad 100%);
      --front-frame-surface: linear-gradient(180deg, #f2ede2 0%, #dfd6c4 100%);
      --front-frame-border: rgba(89, 97, 107, 0.22);
    }

    .postcard-front-art.frame-sea-voyage {
      --front-frame-gap: linear-gradient(180deg, #d7e4e2 0%, #c2d5d0 100%);
      --front-frame-surface: linear-gradient(180deg, #edf6f4 0%, #d6e7e3 100%);
      --front-frame-border: rgba(88, 129, 127, 0.22);
    }

    .front {
      background: #f4eee5;
    }

    .front::after {
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(180deg, rgba(10, 28, 38, 0.02) 0%, rgba(10, 28, 38, 0.1) 44%, rgba(10, 28, 38, 0.5) 100%),
        linear-gradient(135deg, rgba(255,255,255,0.22), transparent 28%),
        radial-gradient(circle at 50% 0%, rgba(255, 232, 173, 0.12), transparent 42%);
      pointer-events: none;
    }

    .back {
      transform: rotateY(180deg);
      background: #faf5ed;
    }

    .back img {
      position: absolute;
      inset: 0;
      z-index: 0;
      object-fit: cover;
      opacity: 1;
      filter: none;
    }

    .message-area {
      position: absolute;
      z-index: 1;
      top: {{ message_style.top }};
      left: {{ message_style.left }};
      width: {{ message_style.width }};
      height: {{ message_style.height }};
      overflow: hidden;
      display: block;
    }

    .message-lines {
      display: none;
    }

    .message-canvas {
      width: 100%;
      height: 100%;
      display: block;
    }

    .message-line:nth-child(2) {
      padding-left: 0.34em;
    }

    .message-line:nth-child(3) {
      padding-left: 0.18em;
    }

    @keyframes revealSweep {
      0% {
        opacity: 0;
        transform: translateX(-34%) translateY(-10px) rotate(-9deg) scaleX(0.88);
      }
      18% {
        opacity: 0.9;
      }
      100% {
        opacity: 0;
        transform: translateX(40%) translateY(-18px) rotate(-7deg) scaleX(1.08);
      }
    }

    @keyframes postcardGleam {
      0% {
        opacity: 0;
        transform: translateX(-34%) skewX(-10deg);
      }
      18% {
        opacity: 0.9;
      }
      100% {
        opacity: 0;
        transform: translateX(38%) skewX(-10deg);
      }
    }

    @keyframes postcardFloat {
      0%, 100% {
        transform:
          translate3d(var(--drift-x), calc(var(--drift-y) * 0.45), 0)
          scale(1.01)
          rotateX(var(--tilt-x))
          rotateY(var(--tilt-y));
      }
      50% {
        transform:
          translate3d(calc(var(--drift-x) + 1px), calc(var(--drift-y) * 0.45 - 8px), 0)
          scale(1.016)
          rotateX(calc(var(--tilt-x) - 0.35deg))
          rotateY(calc(var(--tilt-y) + 0.25deg));
      }
    }

    @keyframes haloPulse {
      0%, 100% {
        opacity: 0.62;
        filter: drop-shadow(0 0 26px rgba(192, 154, 99, 0.18));
      }
      50% {
        opacity: 0.92;
        filter: drop-shadow(0 0 44px rgba(192, 154, 99, 0.3));
      }
    }

    @keyframes orbFloat {
      0%, 100% {
        transform: translate3d(0, 0, 0) scale(1);
      }
      50% {
        transform: translate3d(0, -12px, 0) scale(1.08);
      }
    }

    @keyframes keepsakeSpin {
      0%, 20% {
        transform: rotateY(0deg);
      }
      28%, 56% {
        transform: rotateY(180deg);
      }
      64%, 100% {
        transform: rotateY(360deg);
      }
    }

    @keyframes keepsakeFloat {
      0%, 100% {
        transform: translateY(0) scale(1);
      }
      50% {
        transform: translateY(-5px) scale(1.018);
      }
    }

    .keepsake-preview {
      position: fixed;
      top: 22px;
      right: 22px;
      z-index: 3;
      width: min(22vw, 170px);
      aspect-ratio: 3 / 2;
      border-radius: 18px;
      padding: 10px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.94), rgba(244,236,225,0.82));
      border: 1px solid rgba(255,255,255,0.9);
      box-shadow:
        0 24px 48px rgba(78, 76, 67, 0.18),
        inset 0 1px 0 rgba(255,255,255,0.88);
      backdrop-filter: blur(14px);
      opacity: 0;
      transform: translateY(-8px);
      transition: opacity 0.85s ease, transform 1s var(--ease-soft);
      overflow: hidden;
    }

    .keepsake-preview::after {
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(135deg, rgba(255,255,255,0.34), transparent 34%),
        linear-gradient(180deg, transparent 58%, rgba(127, 101, 65, 0.05));
      pointer-events: none;
      z-index: 1;
    }

    body.is-ready .keepsake-preview {
      opacity: 1;
      transform: translateY(0);
    }

    .keepsake-preview::before {
      content: "Front & back";
      position: absolute;
      top: 10px;
      left: 12px;
      z-index: 2;
      font-size: 10px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: rgba(92, 77, 57, 0.72);
    }

    .keepsake-preview-stage {
      position: absolute;
      left: 12px;
      right: 12px;
      top: 30px;
      bottom: 12px;
      perspective: 900px;
      z-index: 2;
    }

    .keepsake-preview-card {
      position: relative;
      width: 100%;
      height: 100%;
      transform-style: preserve-3d;
      animation: keepsakeSpin 8.4s cubic-bezier(0.65, 0.05, 0.36, 1) infinite;
    }

    .keepsake-preview-inner {
      position: absolute;
      inset: 0;
      animation: keepsakeFloat 3.2s ease-in-out infinite;
      transform-style: preserve-3d;
    }

    .keepsake-preview-face {
      position: absolute;
      inset: 0;
      border-radius: 12px;
      overflow: hidden;
      backface-visibility: hidden;
      -webkit-backface-visibility: hidden;
      box-shadow: 0 14px 24px rgba(49, 40, 26, 0.14);
      background: #fff;
    }

    .keepsake-preview-face::after {
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(135deg, rgba(255,255,255,0.2), transparent 24%),
        linear-gradient(180deg, transparent 64%, rgba(31, 23, 12, 0.08));
      pointer-events: none;
    }

    .keepsake-preview-face img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }

    .keepsake-preview-back {
      transform: rotateY(180deg);
    }

    .controls {
      position: fixed;
      left: 50%;
      bottom: 20px;
      transform: translateX(-50%) translateY(8px);
      width: min(78vw, 332px);
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 12px 14px;
      border-radius: 999px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.88), rgba(248,242,232,0.72));
      border: 1px solid rgba(255,255,255,0.86);
      box-shadow:
        0 22px 48px rgba(90, 112, 126, 0.14),
        inset 0 1px 0 rgba(255,255,255,0.72);
      backdrop-filter: blur(16px);
      opacity: 0;
      transition: opacity 0.85s ease, transform 1s var(--ease-soft), box-shadow 0.4s ease;
      z-index: 2;
    }

    body.is-ready .controls {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }

    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: center;
      width: 100%;
    }

    .button {
      appearance: none;
      border-radius: 999px;
      padding: 12px 18px;
      cursor: pointer;
      font: inherit;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.24em;
      text-transform: uppercase;
      transition: transform 0.25s ease, background 0.25s ease, box-shadow 0.25s ease;
    }

    .button:hover {
      transform: translateY(-1px);
    }

    .button-secondary {
      border: 1px solid rgba(169, 144, 93, 0.32);
      background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(243,235,223,0.82));
      color: rgba(60, 56, 50, 0.9);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.72), 0 14px 28px rgba(98, 83, 54, 0.1);
      backdrop-filter: blur(10px);
    }

    .button-secondary:hover {
      background: linear-gradient(180deg, rgba(255,255,255,1), rgba(245,237,224,0.88));
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.72), 0 14px 28px rgba(98, 83, 54, 0.14);
    }

    @media (max-width: 760px) {
      .keepsake-preview {
        top: 14px;
        right: 14px;
        width: min(31vw, 128px);
        border-radius: 16px;
        padding: 8px;
      }

      .keepsake-preview::before {
        top: 8px;
        left: 10px;
        font-size: 8px;
      }

      .keepsake-preview-stage {
        left: 10px;
        right: 10px;
        top: 24px;
        bottom: 10px;
      }

      .experience {
        min-height: 100svh;
        padding: 12px 10px 56px;
      }

      .scene-layout {
        width: min(92vw, 860px);
        grid-template-columns: 1fr 1fr;
        grid-template-areas:
          "from to"
          "scene scene";
        gap: 12px;
        margin-top: 70px;
      }

      .brand-mark {
        top: 10px;
        min-width: min(56vw, 220px);
        padding: 10px 14px;
      }

      .story-stop {
        gap: 5px;
      }

      .story-stop::before {
        width: 28px;
      }

      .story-stop-from {
        grid-area: from;
        justify-self: stretch;
        text-align: left;
        padding-right: 0;
        padding-left: 34px;
      }

      .story-stop-to {
        grid-area: to;
        justify-self: stretch;
        text-align: right;
        padding-left: 0;
        padding-right: 34px;
      }

      .story-stop-from::before {
        left: 0;
        right: auto;
        transform: translateY(-50%) scaleX(-1);
      }

      .story-stop-to::before {
        left: auto;
        right: 0;
        transform: translateY(-50%);
      }

      .scene {
        grid-area: scene;
        width: min(92vw, calc((100svh - 220px) * 1.5), 620px);
      }

      .controls {
        width: min(92vw, 420px);
      }

      .controls {
        position: static;
        transform: none;
        margin-top: 10px;
      }

      body.is-ready .controls {
        transform: none;
      }

      .actions {
        justify-content: center;
      }

      .button {
        flex: 0 0 auto;
        padding: 10px 14px;
        font-size: 9px;
        letter-spacing: 0.2em;
      }
    }

    @media (max-width: 900px) and (min-width: 561px) {
      .message-lines {
        font-size: {{ message_style.tablet_font_size }};
        line-height: 1.18;
        gap: 0.18em;
      }
    }

    @media (max-width: 560px) {
      .experience {
        padding: 10px 8px 48px;
      }

      .brand-mark {
        top: 8px;
        min-width: min(58vw, 208px);
      }

      .scene-layout {
        width: min(96vw, 520px);
        grid-template-columns: 1fr;
        grid-template-areas:
          "from"
          "scene"
          "to";
        gap: 10px;
        margin-top: 74px;
      }

      .story-stop {
        text-align: left;
        padding-left: 28px;
        padding-right: 0;
      }

      .story-stop::before {
        left: 0;
        right: auto;
        width: 24px;
        transform: translateY(-50%) scaleX(-1);
      }

      .story-stop-to {
        text-align: left;
      }

      .scene {
        width: min(96vw, calc((100svh - 205px) * 1.5), 520px);
      }

      .controls {
        width: min(96vw, 520px);
        margin-top: 6px;
      }

      .message-area {
        top: {{ message_style.top }};
        left: {{ message_style.left }};
        width: {{ message_style.width }};
        height: {{ message_style.height }};
      }

      .message-lines {
        font-size: {{ message_style.mobile_font_size }};
        line-height: 1.16;
        gap: 0.16em;
      }
    }

    @media (max-height: 760px) and (max-width: 760px) {
      .keepsake-preview {
        width: min(27vw, 112px);
      }

      .brand-mark {
        top: 8px;
        min-width: min(62vw, 210px);
      }

      .scene-layout {
        width: min(90vw, 480px);
        margin-top: 62px;
      }

      .scene {
        width: min(90vw, calc((100svh - 190px) * 1.5), 480px);
      }

      .controls {
        width: min(90vw, 480px);
        margin-top: 4px;
      }
    }

    @media (prefers-reduced-motion: reduce) {
      *,
      *::before,
      *::after {
        animation: none !important;
        transition-duration: 0.01ms !important;
        transition-delay: 0ms !important;
        scroll-behavior: auto !important;
      }

      html, body {
        overflow-y: auto;
      }
    }
  </style>
</head>
<body>
  {% set sender_name = postcard['from_name']|default('', true)|trim %}
  {% set recipient_name = postcard['to_name']|default('', true)|trim %}
  {% macro render_front_art(extra_class='') -%}
    <div class="postcard-front-art {{ postcard_layout_class }} {{ postcard_frame_class }} {{ extra_class }}">
      {% set front_background = postcard['postcard_background_image']|default('', true)|trim %}
      {% if front_background %}
        <img class="postcard-front-background" src="{{ front_background }}" alt="" crossorigin="anonymous" referrerpolicy="no-referrer">
      {% endif %}
      {% for slot in front_slots %}
        <div class="postcard-front-slot {{ slot.slot_class }}">
          <div class="postcard-front-slot-media">
            {% if slot.image_url %}
              <img src="{{ slot.image_url }}" alt="Front image {{ loop.index }}" crossorigin="anonymous" referrerpolicy="no-referrer">
            {% endif %}
          </div>
        </div>
      {% endfor %}
    </div>
  {%- endmacro %}
  <div class="sun-glow"></div>
  <div class="sun-rays"></div>
  <div class="sea-haze"></div>
  <div class="sea-shimmer"></div>
  <div class="brand-bar"></div>
  <div class="distant-city"></div>
  <div class="coastline"></div>
  <div class="coast-waves"></div>
  <div class="stage-shadow"></div>
  <div class="keepsake-preview" aria-hidden="true">
    <div class="keepsake-preview-stage">
        <div class="keepsake-preview-card">
          <div class="keepsake-preview-inner">
            <div class="keepsake-preview-face keepsake-preview-front">
              {{ render_front_art('postcard-front-art--preview') }}
            </div>
            <div class="keepsake-preview-face keepsake-preview-back">
              <img src="{{ postcard['back_image_url'] }}" alt="">
            </div>
          </div>
      </div>
    </div>
  </div>

  <main class="experience">
    <div class="brand-mark" id="brandMark" aria-hidden="true">
      <img src="/static/send-a-memory-logo.png" alt="Send a Memory" id="brandLogo">
      <span class="brand-mark-fallback">Send a Memory</span>
    </div>
    <div class="scene-layout">
      <aside class="story-stop story-stop-from" aria-label="Postcard sender">
        <div>
          <span class="story-stop-label">From</span>
          <span class="story-stop-name">{{ sender_name or 'A traveler' }}</span>
        </div>
      </aside>

      <section class="scene" aria-label="Digital postcard reveal scene">
        <div class="reveal-halo"></div>
        <div class="reveal-flash"></div>
        <div class="reveal-sweep"></div>
        <div class="ambient-orbs" aria-hidden="true">
          <span></span>
          <span></span>
          <span></span>
        </div>

        <div class="postcard-shell" id="postcardShell">
          <button class="flip-target" id="flipButton" aria-label="Okreni razglednicu">
            <div class="card-glow"></div>

            <div class="postcard" id="postcard">
              <article class="face front">
                {{ render_front_art('postcard-front-art--main') }}
              </article>

              <article class="face back">
                <img src="{{ postcard['back_image_url'] }}" alt="Back image" id="backImage" crossorigin="anonymous" referrerpolicy="no-referrer">
                {% if not hide_message_overlay %}
                <div
                  class="message-area"
                  id="messageArea"
                  data-message="{{ postcard['message']|e }}"
                  data-message-font-key="{{ message_style.key|e }}"
                  data-message-font-family="{{ message_style.font_family|e }}"
                  data-message-font-weight="{{ message_style.font_weight|e }}"
                  data-message-color="{{ message_style.color|e }}"
                  data-message-font-scale="{{ message_style.font_scale|e }}"
                  data-message-max-font-ratio="{{ message_style.max_font_ratio|e }}"
                  data-message-min-font-size="{{ message_style.min_font_size|e }}"
                  data-message-line-gap-ratio="{{ message_style.line_gap_ratio|e }}"
                  data-message-horizontal-padding-ratio="{{ message_style.horizontal_padding_ratio|e }}"
                  data-message-vertical-padding-ratio="{{ message_style.vertical_padding_ratio|e }}"
                  data-message-vertical-align="{{ message_style.vertical_align|e }}"
                >
                  <canvas class="message-canvas" id="messageCanvas"></canvas>
                  <div class="message-lines" id="messageLines">
                    {% for line in message_lines %}
                      <div class="message-line">{{ line }}</div>
                    {% endfor %}
                  </div>
                </div>
                {% endif %}
              </article>
            </div>
          </button>
        </div>
      </section>

      <aside class="story-stop story-stop-to" aria-label="Postcard recipient">
        <div>
          <span class="story-stop-label">To</span>
          <span class="story-stop-name">{{ recipient_name or 'Someone special' }}</span>
        </div>
        <div class="story-stop-meta">A digital postcard keepsake</div>
      </aside>
    </div>

    <div class="controls">
      <div class="actions">
        <button class="button button-secondary" id="shareButton">Share postcard</button>
        <button class="button button-secondary" id="replayButton">Replay the moment</button>
      </div>
    </div>
  </main>

  <script>
    const body = document.body;
    const postcard = document.getElementById('postcard');
    const flipButton = document.getElementById('flipButton');
    const replayButton = document.getElementById('replayButton');
    const shareButton = document.getElementById('shareButton');
    const messageArea = document.getElementById('messageArea');
    const messageCanvas = document.getElementById('messageCanvas');
    const messageLines = document.getElementById('messageLines');
    const backImage = document.getElementById('backImage');
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    let introTimers = [];
    let flipped = false;
    let audioContext;
    let noiseBuffer;
    let wavesNodes;

    function getAudioContext() {
      if (prefersReducedMotion) return null;
      if (!audioContext) {
        const AudioCtor = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtor) return null;
        audioContext = new AudioCtor();
      }
      return audioContext;
    }

    function getNoiseBuffer(ctx) {
      if (noiseBuffer) return noiseBuffer;
      const buffer = ctx.createBuffer(1, ctx.sampleRate * 0.7, ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < data.length; i += 1) {
        data[i] = (Math.random() * 2 - 1) * 0.28;
      }
      noiseBuffer = buffer;
      return buffer;
    }

    async function warmAudio() {
      const ctx = getAudioContext();
      if (!ctx) return;
      if (ctx.state === 'suspended') {
        try {
          await ctx.resume();
        } catch (error) {
          return;
        }
      }
      startAmbientWaves();
    }

    function startAmbientWaves() {
      const ctx = getAudioContext();
      if (!ctx || ctx.state !== 'running' || wavesNodes) return;

      const master = ctx.createGain();
      master.gain.value = 0.03;
      master.connect(ctx.destination);

      const makeWaveLayer = ({ gainValue, lowpassFreq, bandFreq, bandQ, lfoRate, lfoDepth }) => {
        const source = ctx.createBufferSource();
        source.buffer = getNoiseBuffer(ctx);
        source.loop = true;

        const lowpass = ctx.createBiquadFilter();
        lowpass.type = 'lowpass';
        lowpass.frequency.value = lowpassFreq;

        const bandpass = ctx.createBiquadFilter();
        bandpass.type = 'bandpass';
        bandpass.frequency.value = bandFreq;
        bandpass.Q.value = bandQ;

        const gain = ctx.createGain();
        gain.gain.value = gainValue;

        const lfo = ctx.createOscillator();
        lfo.type = 'sine';
        lfo.frequency.value = lfoRate;

        const lfoGain = ctx.createGain();
        lfoGain.gain.value = lfoDepth;

        source.connect(lowpass);
        lowpass.connect(bandpass);
        bandpass.connect(gain);
        gain.connect(master);
        lfo.connect(lfoGain);
        lfoGain.connect(gain.gain);

        source.start();
        lfo.start();

        return { source, lfo };
      };

      const nearWave = makeWaveLayer({
        gainValue: 0.12,
        lowpassFreq: 700,
        bandFreq: 320,
        bandQ: 0.7,
        lfoRate: 0.18,
        lfoDepth: 0.045,
      });

      const farWave = makeWaveLayer({
        gainValue: 0.07,
        lowpassFreq: 480,
        bandFreq: 180,
        bandQ: 0.5,
        lfoRate: 0.11,
        lfoDepth: 0.028,
      });

      wavesNodes = { master, nearWave, farWave };
    }

    function clearIntroTimers() {
      introTimers.forEach(window.clearTimeout);
      introTimers = [];
    }

    function setFlipState(nextState) {
      flipped = nextState;
      postcard.classList.toggle('flipped', flipped);
    }

    function wrapCanvasLines(ctx, text, maxWidth) {
      const words = text.split(/\s+/).filter(Boolean);
      if (!words.length) return [''];

      const lines = [];
      let current = words[0];

      for (let i = 1; i < words.length; i += 1) {
        const candidate = `${current} ${words[i]}`;
        if (ctx.measureText(candidate).width <= maxWidth) {
          current = candidate;
        } else {
          lines.push(current);
          current = words[i];
        }
      }

      lines.push(current);
      return lines;
    }

    function rgbToHsl(r, g, b) {
      const rn = r / 255;
      const gn = g / 255;
      const bn = b / 255;
      const max = Math.max(rn, gn, bn);
      const min = Math.min(rn, gn, bn);
      let h = 0;
      let s = 0;
      const l = (max + min) / 2;

      if (max !== min) {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

        switch (max) {
          case rn:
            h = (gn - bn) / d + (gn < bn ? 6 : 0);
            break;
          case gn:
            h = (bn - rn) / d + 2;
            break;
          default:
            h = (rn - gn) / d + 4;
            break;
        }

        h /= 6;
      }

      return { h, s, l };
    }

    function hueToRgb(p, q, t) {
      let tn = t;
      if (tn < 0) tn += 1;
      if (tn > 1) tn -= 1;
      if (tn < 1 / 6) return p + (q - p) * 6 * tn;
      if (tn < 1 / 2) return q;
      if (tn < 2 / 3) return p + (q - p) * (2 / 3 - tn) * 6;
      return p;
    }

    function hslToRgb(h, s, l) {
      if (s === 0) {
        const value = Math.round(l * 255);
        return { r: value, g: value, b: value };
      }

      const q = l < 0.5 ? l * (1 + s) : l + s - (l * s);
      const p = 2 * l - q;

      return {
        r: Math.round(hueToRgb(p, q, h + 1 / 3) * 255),
        g: Math.round(hueToRgb(p, q, h) * 255),
        b: Math.round(hueToRgb(p, q, h - 1 / 3) * 255)
      };
    }

    function relativeLuminance(r, g, b) {
      const normalize = (value) => {
        const channel = value / 255;
        return channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
      };

      const rr = normalize(r);
      const gg = normalize(g);
      const bb = normalize(b);
      return (0.2126 * rr) + (0.7152 * gg) + (0.0722 * bb);
    }

    function contrastRatio(foreground, background) {
      const fg = relativeLuminance(foreground.r, foreground.g, foreground.b);
      const bg = relativeLuminance(background.r, background.g, background.b);
      const lighter = Math.max(fg, bg);
      const darker = Math.min(fg, bg);
      return (lighter + 0.05) / (darker + 0.05);
    }

    function deriveInkColorFromBackground(background) {
      const { h, s, l } = rgbToHsl(background.r, background.g, background.b);
      const hueShift = s < 0.08 ? 0.94 : 0.965;
      const targetHue = (h * hueShift + 0.01) % 1;
      const targetSaturation = Math.min(0.42, Math.max(0.18, s * 0.82 + 0.08));
      let targetLightness = l > 0.72 ? Math.max(0.24, l - 0.48) : Math.max(0.18, l - 0.3);
      let ink = hslToRgb(targetHue, targetSaturation, targetLightness);

      while (contrastRatio(ink, background) < 4.6 && targetLightness > 0.12) {
        targetLightness -= 0.04;
        ink = hslToRgb(targetHue, targetSaturation, targetLightness);
      }

      return `rgb(${ink.r}, ${ink.g}, ${ink.b})`;
    }

    function sampleMessageBackgroundColor() {
      if (!backImage || !messageArea) return null;
      if (!backImage.complete || !backImage.naturalWidth || !backImage.naturalHeight) return null;

      const postcardBack = backImage.closest('.face.back');
      if (!postcardBack) return null;

      const backRect = postcardBack.getBoundingClientRect();
      const areaRect = messageArea.getBoundingClientRect();
      if (!backRect.width || !backRect.height || !areaRect.width || !areaRect.height) return null;

      const sampleCanvas = document.createElement('canvas');
      sampleCanvas.width = Math.max(32, Math.round(backRect.width));
      sampleCanvas.height = Math.max(32, Math.round(backRect.height));
      const sampleCtx = sampleCanvas.getContext('2d', { willReadFrequently: true });
      if (!sampleCtx) return null;

      try {
        sampleCtx.drawImage(backImage, 0, 0, sampleCanvas.width, sampleCanvas.height);
        const sampleX = Math.max(0, Math.floor(((areaRect.left - backRect.left) / backRect.width) * sampleCanvas.width));
        const sampleY = Math.max(0, Math.floor(((areaRect.top - backRect.top) / backRect.height) * sampleCanvas.height));
        const sampleWidth = Math.max(8, Math.min(sampleCanvas.width - sampleX, Math.ceil((areaRect.width / backRect.width) * sampleCanvas.width)));
        const sampleHeight = Math.max(8, Math.min(sampleCanvas.height - sampleY, Math.ceil((areaRect.height / backRect.height) * sampleCanvas.height)));
        const imageData = sampleCtx.getImageData(sampleX, sampleY, sampleWidth, sampleHeight).data;

        let totalR = 0;
        let totalG = 0;
        let totalB = 0;
        let count = 0;

        for (let i = 0; i < imageData.length; i += 16) {
          totalR += imageData[i];
          totalG += imageData[i + 1];
          totalB += imageData[i + 2];
          count += 1;
        }

        if (!count) return null;

        return {
          r: Math.round(totalR / count),
          g: Math.round(totalG / count),
          b: Math.round(totalB / count)
        };
      } catch (error) {
        return null;
      }
    }

    function renderMessageCanvas() {
      if (!messageArea || !messageCanvas) return;

      const clampNumber = (value, min, max, fallback) => {
        const numericValue = Number.parseFloat(value);
        if (Number.isNaN(numericValue)) return fallback;
        return Math.min(max, Math.max(min, numericValue));
      };

      const text = (messageArea.dataset.message || '').replace(/\s+/g, ' ').trim();
      const messageFontFamily = messageArea.dataset.messageFontFamily || '"Caveat", "Brush Script MT", cursive';
      const messageFontWeight = messageArea.dataset.messageFontWeight || '600';
      const selectedMessageColor = messageArea.dataset.messageColor || '#a86f7d';
      const fontScale = clampNumber(messageArea.dataset.messageFontScale || '1', 0.65, 1.1, 1);
      const maxFontRatio = clampNumber(messageArea.dataset.messageMaxFontRatio || '0.27', 0.16, 0.34, 0.27);
      const minFont = clampNumber(messageArea.dataset.messageMinFontSize || '8', 6.5, 12, 8);
      const lineGapRatio = clampNumber(messageArea.dataset.messageLineGapRatio || '0.2', 0.08, 0.34, 0.2);
      const horizontalPaddingRatio = clampNumber(messageArea.dataset.messageHorizontalPaddingRatio || '0.024', 0.01, 0.08, 0.024);
      const verticalPaddingRatio = clampNumber(messageArea.dataset.messageVerticalPaddingRatio || '0.11', 0.03, 0.24, 0.11);
      const verticalAlign = clampNumber(messageArea.dataset.messageVerticalAlign || '0.18', 0, 1, 0.18);
      const width = messageArea.clientWidth;
      const height = messageArea.clientHeight;

      if (!width || !height) return;

      const dpr = Math.max(1, window.devicePixelRatio || 1);
      messageCanvas.width = Math.round(width * dpr);
      messageCanvas.height = Math.round(height * dpr);
      messageCanvas.style.width = `${width}px`;
      messageCanvas.style.height = `${height}px`;

      const ctx = messageCanvas.getContext('2d');
      if (!ctx) return;

      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, width, height);

      if (!text) return;

      const horizontalPadding = Math.max(4, width * horizontalPaddingRatio);
      const verticalPadding = Math.max(4, height * verticalPaddingRatio);
      const maxWidth = width - (horizontalPadding * 2);
      const availableHeight = Math.max(0, height - (verticalPadding * 2));
      let fontSize = Math.min(21 * fontScale, height * maxFontRatio);
      let lines = [text];
      let ascent = fontSize * 0.76;
      let descent = fontSize * 0.28;
      let lineGap = fontSize * lineGapRatio;

      while (fontSize >= minFont) {
        ctx.font = `${messageFontWeight} ${fontSize}px ${messageFontFamily}`;
        lines = wrapCanvasLines(ctx, text, maxWidth);
        const metrics = ctx.measureText('AgjpqyQ');
        ascent = metrics.actualBoundingBoxAscent || fontSize * 0.78;
        descent = metrics.actualBoundingBoxDescent || fontSize * 0.32;
        lineGap = fontSize * lineGapRatio;
        const totalHeight = (lines.length * (ascent + descent)) + (Math.max(0, lines.length - 1) * lineGap);
        const widestLine = lines.reduce((max, line) => Math.max(max, ctx.measureText(line).width), 0);

        if (totalHeight <= availableHeight && widestLine <= maxWidth) {
          break;
        }

        fontSize -= 0.5;
      }

      ctx.font = `${messageFontWeight} ${Math.max(fontSize, minFont)}px ${messageFontFamily}`;
      const sampledBackground = sampleMessageBackgroundColor();
      ctx.fillStyle = sampledBackground ? deriveInkColorFromBackground(sampledBackground) : selectedMessageColor;
      ctx.textBaseline = 'alphabetic';
      ctx.textAlign = 'left';
      ctx.shadowColor = 'rgba(255, 255, 255, 0.16)';
      ctx.shadowBlur = 0;
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 1;

      const totalHeight = (lines.length * (ascent + descent)) + (Math.max(0, lines.length - 1) * lineGap);
      const freeHeight = Math.max(0, availableHeight - totalHeight);
      let y = verticalPadding + (freeHeight * verticalAlign) + ascent;

      lines.forEach((line) => {
        ctx.fillText(line, horizontalPadding, y);
        y += ascent + descent + lineGap;
      });
    }

    async function sharePostcard() {
      const shareUrl = window.location.href;
      const shareTitle = document.title;
      const shareText = 'Take a look at this postcard.';

      if (navigator.share) {
        try {
          await navigator.share({
            title: shareTitle,
            text: shareText,
            url: shareUrl
          });
          return;
        } catch (error) {
          if (error && error.name === 'AbortError') {
            return;
          }
        }
      }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        try {
          await navigator.clipboard.writeText(shareUrl);
          if (shareButton) {
            const originalText = shareButton.textContent;
            shareButton.textContent = 'Link copied';
            window.setTimeout(() => {
              shareButton.textContent = originalText;
            }, 1600);
          }
          return;
        } catch (error) {
        }
      }

      window.prompt('Copy this postcard link', shareUrl);
    }

    function runReveal() {
      clearIntroTimers();
      setFlipState(false);
      body.classList.remove('reveal-start', 'reveal-active', 'is-ready');

      introTimers.push(window.setTimeout(() => {
        body.classList.add('reveal-start');
      }, 140));

      introTimers.push(window.setTimeout(() => {
        body.classList.add('reveal-active');
      }, 860));

      introTimers.push(window.setTimeout(() => {
        body.classList.remove('reveal-start', 'reveal-active');
        body.classList.add('is-ready');
      }, 2140));
    }

    function toggleFlip() {
      warmAudio();
      setFlipState(!flipped);
    }

    flipButton.addEventListener('click', toggleFlip);
    replayButton.addEventListener('click', runReveal);
    if (shareButton) {
      shareButton.addEventListener('click', sharePostcard);
    }
    window.addEventListener('pointerdown', warmAudio, { passive: true });
    window.addEventListener('keydown', warmAudio);
    window.addEventListener('load', () => {
      renderMessageCanvas();
      warmAudio();
      runReveal();
    }, { once: true });
    window.addEventListener('resize', renderMessageCanvas);
  </script>
</body>
</html>

"""


PREVIEWS_HTML = r"""
<!doctype html>
<html lang="hr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Postcard Previews</title>
  <style>
    :root {
      --bg: #f6efe4;
      --panel: rgba(255, 252, 247, 0.94);
      --line: rgba(137, 108, 70, 0.16);
      --ink: #2d2a26;
      --muted: #7c6e61;
      --accent: #b54a3f;
      --shadow: 0 24px 60px rgba(64, 45, 21, 0.1);
      --radius: 26px;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Arial, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top, rgba(255,255,255,0.9), transparent 34%),
        linear-gradient(180deg, #fbf7f0 0%, #f3e9da 100%);
    }

    .wrap {
      width: min(1120px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 32px 0 48px;
    }

    .hero {
      margin-bottom: 22px;
      padding: 26px 28px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--panel);
      box-shadow: var(--shadow);
    }

    h1 {
      margin: 0;
      font-size: clamp(28px, 4vw, 40px);
      line-height: 1.05;
    }

    .hero p {
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.6;
    }

    .meta {
      margin-top: 14px;
      color: var(--muted);
      font-size: 13px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 16px;
    }

    .card {
      border: 1px solid var(--line);
      border-radius: 22px;
      overflow: hidden;
      background: var(--panel);
      box-shadow: var(--shadow);
    }

    .thumb {
      display: block;
      aspect-ratio: 3 / 2;
      background: #efe7da;
    }

    .thumb img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }

    .body { padding: 16px; }

    .title {
      margin: 0;
      font-size: 18px;
      line-height: 1.2;
    }

    .info {
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
    }

    .slug {
      margin-top: 12px;
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(181, 74, 63, 0.06);
      color: #7a3f38;
      font-size: 12px;
      overflow-wrap: anywhere;
    }

    .actions {
      display: flex;
      gap: 10px;
      margin-top: 14px;
      flex-wrap: wrap;
    }

    .button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 42px;
      padding: 0 14px;
      border-radius: 999px;
      text-decoration: none;
      font-weight: 700;
      font-size: 13px;
    }

    .button-primary {
      background: var(--accent);
      color: #fff;
    }

    .button-secondary {
      background: rgba(45, 42, 38, 0.06);
      color: var(--ink);
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Postcard previews</h1>
      <p>Pregled svih generiranih razglednica iz baze.</p>
      <div class="meta">{{ postcards|length }} saved</div>
    </section>

    <section class="grid">
      {% for postcard in postcards %}
        <article class="card">
          <a class="thumb" href="{{ base_url }}/p/{{ postcard['slug'] }}" target="_blank" rel="noreferrer">
            <img src="{{ postcard['front_image_url'] }}" alt="{{ postcard['product_title'] }}">
          </a>
          <div class="body">
            <h2 class="title">{{ postcard['product_title'] }}</h2>
            <p class="info">
              Order: {{ postcard['order_name'] or postcard['order_id'] or 'â€”' }}<br>
              To: {{ postcard['to_name'] or 'â€”' }}<br>
              Created: {{ postcard['created_at'] }}
            </p>
            <div class="slug">{{ postcard['slug'] }}</div>
            <div class="actions">
              <a class="button button-primary" href="{{ base_url }}/p/{{ postcard['slug'] }}" target="_blank" rel="noreferrer">Open</a>
              <a class="button button-secondary" href="{{ base_url }}/api/postcard-by-order/{{ postcard['order_id'] }}" target="_blank" rel="noreferrer">JSON</a>
            </div>
          </div>
        </article>
      {% endfor %}
    </section>
  </div>
</body>
</html>
"""


def ensure_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS postcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            order_name TEXT,
            slug TEXT UNIQUE NOT NULL,
            product_title TEXT NOT NULL,
            message TEXT NOT NULL,
            from_name TEXT NOT NULL DEFAULT '',
            to_name TEXT NOT NULL DEFAULT '',
            front_image_url TEXT NOT NULL,
            back_image_url TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    existing_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(postcards)").fetchall()
    }
    if "from_name" not in existing_columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN from_name TEXT NOT NULL DEFAULT ''")
    if "to_name" not in existing_columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN to_name TEXT NOT NULL DEFAULT ''")
    if "front_image_urls" not in existing_columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN front_image_urls TEXT NOT NULL DEFAULT '[]'")
    if "postcard_layout" not in existing_columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN postcard_layout TEXT NOT NULL DEFAULT 'Single Photo'")
    if "postcard_layout_key" not in existing_columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN postcard_layout_key TEXT NOT NULL DEFAULT 'single'")
    if "postcard_frame" not in existing_columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN postcard_frame TEXT NOT NULL DEFAULT 'Classic Ivory'")
    if "postcard_frame_key" not in existing_columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN postcard_frame_key TEXT NOT NULL DEFAULT 'classic-ivory'")
    if "postcard_font" not in existing_columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN postcard_font TEXT NOT NULL DEFAULT 'Caveat'")
    if "postcard_font_key" not in existing_columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN postcard_font_key TEXT NOT NULL DEFAULT 'caveat'")
    if "postcard_background_image" not in existing_columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN postcard_background_image TEXT NOT NULL DEFAULT ''")
    if "postcard_template" not in existing_columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN postcard_template TEXT NOT NULL DEFAULT ''")
    if "rendered_back_image_url" not in existing_columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN rendered_back_image_url TEXT NOT NULL DEFAULT ''")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS webhook_debug_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            topic TEXT NOT NULL,
            order_id TEXT,
            order_name TEXT,
            order_property_keys TEXT NOT NULL DEFAULT '[]',
            line_item_property_keys TEXT NOT NULL DEFAULT '[]',
            extracted_message_length INTEGER NOT NULL DEFAULT 0,
            extracted_from_length INTEGER NOT NULL DEFAULT 0,
            extracted_to_length INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_postcards_order_id ON postcards(order_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_webhook_debug_events_created_at ON webhook_debug_events(created_at)"
    )
    conn.commit()
    conn.close()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


def cors_preflight_response():
    response = make_response("", 204)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_slug() -> str:
    return secrets.token_urlsafe(6)


def build_postcard_url(slug: str) -> str:
    return f"{PUBLIC_POSTCARD_BASE_URL}/p/{slug}"


def normalize_shopify_order_id(order_id) -> str:
    raw_order_id = str(order_id or "").strip()
    if not raw_order_id:
        return ""

    gid_match = re.search(r"gid://shopify/[^/]+/(\d+)$", raw_order_id)
    if gid_match:
        return gid_match.group(1)

    trailing_digits_match = re.search(r"(\d+)$", raw_order_id)
    if trailing_digits_match and "/" in raw_order_id:
        return trailing_digits_match.group(1)

    return raw_order_id


def build_order_id_candidates(order_id):
    raw_order_id = str(order_id or "").strip()
    normalized_order_id = normalize_shopify_order_id(raw_order_id)

    candidates = []
    for candidate in (raw_order_id, normalized_order_id):
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    return candidates


def build_order_name_candidates(order_ref):
    raw_order_ref = str(order_ref or "").strip()
    if not raw_order_ref:
        return []

    normalized_order_ref = normalize_shopify_order_id(raw_order_ref)
    digit_match = re.search(r"(\d+)$", raw_order_ref)

    candidates = []
    for candidate in (
        raw_order_ref,
        normalized_order_ref,
        f"#{normalized_order_ref}" if normalized_order_ref.isdigit() else "",
        digit_match.group(1) if digit_match else "",
        f"#{digit_match.group(1)}" if digit_match else "",
    ):
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    return candidates


def get_template_for_product(product_title: str):
    return TEMPLATES.get(product_title)


MESSAGE_PROPERTY_NAMES = {
    "postcard message",
    "postcard_message",
    "postcard-message",
    "message",
    "postcard note",
    "postcard-note",
}

FRONT_IMAGE_URL_PROPERTY_NAMES = {
    "front image url",
    "uploaded front image",
    "uploaded front image url",
    "front image",
    "front image link",
}

FRONT_IMAGE_URLS_PROPERTY_NAMES = {
    "front image urls",
    "uploaded front image urls",
    "front images",
    "uploaded front images",
}

BACK_IMAGE_URL_PROPERTY_NAMES = {
    "selected postcard back image",
    "back image url",
    "postcard back image",
    "back image",
}

BACKGROUND_IMAGE_PROPERTY_NAMES = {
    "postcard background image",
    "background image",
    "postcard background",
    "front background image",
    "selected background image",
}

RENDERED_BACK_IMAGE_PROPERTY_NAMES = {
    "postcard rendered back image",
    "rendered back image",
    "postcard final back image",
    "final back image",
    "back image with text",
}

FROM_PROPERTY_NAMES = {
    "from",
    "from field",
    "from name",
    "sender",
    "sender name",
}

TO_PROPERTY_NAMES = {
    "to",
    "to field",
    "to name",
    "recipient",
    "recipient name",
}

TEMPLATE_PROPERTY_NAMES = {
    "postcard template",
    "product template",
    "template",
    "template suffix",
    "postcard template suffix",
    "postcard product template",
}

LAYOUT_PROPERTY_NAMES = {
    "postcard layout",
    "layout",
}

LAYOUT_KEY_PROPERTY_NAMES = {
    "postcard layout key",
    "layout key",
}

FRAME_PROPERTY_NAMES = {
    "postcard frame",
    "frame",
    "selected postcard frame",
    "selected frame",
}

FRAME_KEY_PROPERTY_NAMES = {
    "postcard frame key",
    "frame key",
    "selected postcard frame key",
    "selected frame key",
}

FONT_PROPERTY_NAMES = {
    "postcard font",
    "postcard font style",
    "postcard message font",
    "message font",
    "font",
    "selected postcard font",
    "selected font",
}

FONT_KEY_PROPERTY_NAMES = {
    "postcard font key",
    "postcard font style key",
    "postcard message font key",
    "message font key",
    "font key",
    "selected postcard font key",
    "selected font key",
}

PROPERTY_CONTAINER_KEYS = (
    "properties",
    "line_item_properties",
    "lineItemProperties",
    "custom_attributes",
    "customAttributes",
    "note_attributes",
    "noteAttributes",
    "attributes",
    "cart_attributes",
    "cartAttributes",
)


def extract_property_key(raw_value):
    if not isinstance(raw_value, dict):
        return ""

    for key_name in ("name", "key", "property", "title", "label"):
        value = str(raw_value.get(key_name, "") or "").strip()
        if value:
            return value

    return ""


def extract_property_value(raw_value):
    if not isinstance(raw_value, dict):
        return ""

    for value_key in ("value", "text", "content"):
        value = raw_value.get(value_key, "")
        if value is not None:
            normalized = str(value).strip()
            if normalized:
                return normalized

    return ""


def iter_named_values_deep(raw_value, seen=None):
    if seen is None:
        seen = set()

    if isinstance(raw_value, (dict, list)):
        object_id = id(raw_value)
        if object_id in seen:
            return
        seen.add(object_id)

    if isinstance(raw_value, dict):
        key_name = extract_property_key(raw_value)
        prop_value = extract_property_value(raw_value)
        if key_name and prop_value:
            yield key_name, prop_value

        for nested_value in raw_value.values():
            yield from iter_named_values_deep(nested_value, seen)
        return

    if isinstance(raw_value, list):
        for nested_value in raw_value:
            yield from iter_named_values_deep(nested_value, seen)


def iter_named_values(raw_values):
    if isinstance(raw_values, dict):
        key_name = extract_property_key(raw_values)
        prop_value = extract_property_value(raw_values)
        if key_name and prop_value:
            yield key_name, prop_value
            return

        for key, value in raw_values.items():
            yield str(key or "").strip(), str(value or "").strip()
        return

    for item in raw_values or []:
        if isinstance(item, dict):
            key_name = extract_property_key(item)
            prop_value = extract_property_value(item)
            if key_name and prop_value:
                yield key_name, prop_value


def extract_named_values(item, container_keys=PROPERTY_CONTAINER_KEYS):
    for container_key in container_keys:
        if container_key not in item:
            continue

        raw_values = item.get(container_key)
        yield from iter_named_values(raw_values)


def extract_line_item_properties(item):
    yield from extract_named_values(item, ("properties", "custom_attributes", "customAttributes"))


def pick_property_values(named_values):
    message = ""
    from_name = ""
    to_name = ""
    front_image_url = ""
    back_image_url = ""
    postcard_background_image = ""
    rendered_back_image_url = ""
    front_image_urls = []
    numbered_front_images = {}
    postcard_layout = ""
    postcard_layout_key = ""
    postcard_frame = ""
    postcard_frame_key = ""
    postcard_font = ""
    postcard_font_key = ""
    postcard_template = ""

    for prop_name, prop_value in named_values:
        normalized_prop_name = normalize_property_name(prop_name)
        front_image_index = extract_front_image_index(normalized_prop_name)

        if normalized_prop_name in MESSAGE_PROPERTY_NAMES and prop_value and not message:
            message = prop_value
        elif normalized_prop_name in FRONT_IMAGE_URL_PROPERTY_NAMES and prop_value and not front_image_url:
            front_image_url = prop_value
        elif normalized_prop_name in FRONT_IMAGE_URLS_PROPERTY_NAMES and prop_value:
            for image_url in split_image_url_values(prop_value):
                if image_url not in front_image_urls:
                    front_image_urls.append(image_url)
        elif normalized_prop_name in BACK_IMAGE_URL_PROPERTY_NAMES and prop_value and not back_image_url:
            back_image_url = prop_value
        elif normalized_prop_name in BACKGROUND_IMAGE_PROPERTY_NAMES and prop_value and not postcard_background_image:
            postcard_background_image = prop_value
        elif normalized_prop_name in RENDERED_BACK_IMAGE_PROPERTY_NAMES and prop_value and not rendered_back_image_url:
            rendered_back_image_url = prop_value
        elif normalized_prop_name in FROM_PROPERTY_NAMES and prop_value and not from_name:
            from_name = prop_value
        elif normalized_prop_name in TO_PROPERTY_NAMES and prop_value and not to_name:
            to_name = prop_value
        elif normalized_prop_name in TEMPLATE_PROPERTY_NAMES and prop_value and not postcard_template:
            postcard_template = prop_value
        elif normalized_prop_name in LAYOUT_PROPERTY_NAMES and prop_value and not postcard_layout:
            postcard_layout = prop_value
        elif normalized_prop_name in LAYOUT_KEY_PROPERTY_NAMES and prop_value and not postcard_layout_key:
            postcard_layout_key = prop_value
        elif normalized_prop_name in FRAME_PROPERTY_NAMES and prop_value and not postcard_frame:
            postcard_frame = prop_value
        elif normalized_prop_name in FRAME_KEY_PROPERTY_NAMES and prop_value and not postcard_frame_key:
            postcard_frame_key = prop_value
        elif normalized_prop_name in FONT_PROPERTY_NAMES and prop_value and not postcard_font:
            postcard_font = prop_value
        elif normalized_prop_name in FONT_KEY_PROPERTY_NAMES and prop_value and not postcard_font_key:
            postcard_font_key = prop_value
        elif front_image_index is not None and prop_value:
            numbered_front_images[front_image_index] = prop_value

    for index in sorted(numbered_front_images):
        image_url = numbered_front_images[index]
        if image_url and image_url not in front_image_urls:
            front_image_urls.append(image_url)

    if front_image_url and front_image_url not in front_image_urls:
        front_image_urls.insert(0, front_image_url)

    if front_image_urls and not front_image_url:
        front_image_url = front_image_urls[0]

    normalized_layout_key = normalize_postcard_layout_key(postcard_layout_key or postcard_layout)
    normalized_frame_key = normalize_postcard_frame_key(postcard_frame_key or postcard_frame)
    normalized_font_key = normalize_postcard_font_key(postcard_font_key or postcard_font)

    return {
        "message": message,
        "from_name": from_name,
        "to_name": to_name,
        "front_image_url": front_image_url,
        "front_image_urls": front_image_urls[:6],
        "back_image_url": back_image_url,
        "postcard_background_image": postcard_background_image,
        "rendered_back_image_url": rendered_back_image_url,
        "postcard_layout": postcard_layout or POSTCARD_LAYOUT_PRESETS[normalized_layout_key]["label"],
        "postcard_layout_key": normalized_layout_key,
        "postcard_frame": postcard_frame or POSTCARD_FRAME_PRESETS[normalized_frame_key]["label"],
        "postcard_frame_key": normalized_frame_key,
        "postcard_font": postcard_font or POSTCARD_FONT_PRESETS[normalized_font_key]["label"],
        "postcard_font_key": normalized_font_key,
        "postcard_template": postcard_template,
    }


def normalize_property_name(prop_name: str) -> str:
    normalized = str(prop_name or "").strip()

    bracket_match = re.fullmatch(r"(?:properties|property|attributes|custom_attributes|customAttributes)\[(.+?)\]", normalized)
    if bracket_match:
        normalized = bracket_match.group(1)

    return normalized.casefold().replace("_", " ").replace("-", " ").strip()


def split_image_url_values(raw_value):
    raw_text = str(raw_value or "").strip()
    if not raw_text:
        return []

    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, list):
            return [
                str(item).strip()
                for item in parsed
                if str(item or "").strip()
            ]
    except (TypeError, ValueError, json.JSONDecodeError):
        pass

    parts = re.split(r"\s*\|\s*|\s*\n\s*", raw_text)
    return [part.strip() for part in parts if part.strip()]


def extract_front_image_index(normalized_prop_name: str):
    for pattern in (
        r"front image url (\d+)",
        r"front image (\d+)",
        r"uploaded front image url (\d+)",
        r"uploaded front image (\d+)",
    ):
        match = re.fullmatch(pattern, normalized_prop_name)
        if match:
            return max(0, int(match.group(1)) - 1)
    return None


def normalize_postcard_layout_key(value: str) -> str:
    normalized = str(value or "").strip().casefold().replace("_", "-")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return POSTCARD_LAYOUT_ALIASES.get(normalized, "single")


def infer_layout_key_from_image_count(image_count: int) -> str:
    if image_count >= 6:
        return "multi-six-grid"
    if image_count == 5:
        return "multi-story"
    if image_count == 4:
        return "multi-grid"
    if image_count == 3:
        return "multi-top-band"
    if image_count == 2:
        return "multi-split"
    return "single"


def normalize_postcard_frame_key(value: str) -> str:
    normalized = str(value or "").strip().casefold().replace("_", "-")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return POSTCARD_FRAME_ALIASES.get(normalized, "classic-ivory")


def normalize_postcard_font_key(value: str) -> str:
    normalized = str(value or "").strip().casefold().replace("_", "-")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return POSTCARD_FONT_ALIASES.get(normalized, "caveat")


def resolve_message_side(postcard_data) -> str:
    raw_values = " ".join(
        str(postcard_data.get(key, "") or "")
        for key in ("postcard_template", "product_title", "postcard_layout", "back_image_url")
    ).casefold()

    if "split" in raw_values or "personal" in raw_values or "perosnal" in raw_values:
        return "right"

    return "left"


def load_front_image_urls(raw_value, fallback_url: str = ""):
    urls = split_image_url_values(raw_value)
    if fallback_url:
        fallback_url = str(fallback_url).strip()
        if fallback_url and fallback_url not in urls:
            urls.insert(0, fallback_url)
    return urls[:6]


def resolve_message_style(font_key: str, message_side: str = "left"):
    normalized_key = normalize_postcard_font_key(font_key)
    message_style = dict(POSTCARD_MESSAGE_STYLE)
    message_style.update(POSTCARD_FONT_PRESETS.get(normalized_key, {}))
    message_style.update(POSTCARD_MESSAGE_POSITIONS.get(message_side, POSTCARD_MESSAGE_POSITIONS["left"]))
    message_style["key"] = normalized_key
    message_style["label"] = POSTCARD_FONT_PRESETS.get(normalized_key, {}).get("label", "Caveat")
    message_style["side"] = message_side
    return message_style


def slugify_name_part(value: str) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        return ""

    transliteration_map = str.maketrans({
        "\u010d": "c",
        "\u0107": "c",
        "\u0161": "s",
        "\u017e": "z",
        "\u0111": "dj",
        "\u010c": "c",
        "\u0106": "c",
        "\u0160": "s",
        "\u017d": "z",
        "\u0110": "dj",
    })
    normalized = raw_value.translate(transliteration_map)
    normalized = unicodedata.normalize("NFKD", normalized).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.casefold()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized[:80]


def slug_exists(db, slug: str) -> bool:
    return db.execute(
        "SELECT 1 FROM postcards WHERE slug = ? LIMIT 1",
        (slug,),
    ).fetchone() is not None


def generate_unique_slug(db, preferred_slug: str = "") -> str:
    base_slug = slugify_name_part(preferred_slug)

    if not base_slug:
        while True:
            random_slug = generate_slug()
            if not slug_exists(db, random_slug):
                return random_slug

    if not slug_exists(db, base_slug):
        return base_slug

    suffix = 2
    while True:
        candidate = f"{base_slug}-{suffix}"
        if not slug_exists(db, candidate):
            return candidate
        suffix += 1


def is_probably_generated_slug(slug: str) -> bool:
    raw_slug = str(slug or "").strip()
    if not raw_slug:
        return False

    if "_" in raw_slug or re.search(r"[A-Z]", raw_slug):
        return True

    return re.fullmatch(r"[A-Za-z0-9_-]{8,}", raw_slug) is not None and "-to-" not in raw_slug


def build_preferred_postcard_slug(details) -> str:
    from_slug = slugify_name_part(details.get("from_name", ""))
    to_slug = slugify_name_part(details.get("to_name", ""))

    if from_slug and to_slug:
        return f"{from_slug}-to-{to_slug}"
    if to_slug:
        return f"to-{to_slug}"
    if from_slug:
        return f"from-{from_slug}"
    return ""


def extract_postcard_details(payload):
    order_id = normalize_shopify_order_id(payload.get("id", ""))
    order_name = str(payload.get("name", "")).strip()
    order_level_values = pick_property_values(extract_named_values(payload, ("note_attributes", "noteAttributes", "attributes", "custom_attributes", "customAttributes")))
    message = order_level_values["message"]
    from_name = order_level_values["from_name"]
    to_name = order_level_values["to_name"]
    front_image_url = order_level_values["front_image_url"]
    front_image_urls = list(order_level_values["front_image_urls"])
    back_image_url = order_level_values["back_image_url"]
    postcard_background_image = order_level_values["postcard_background_image"]
    rendered_back_image_url = order_level_values["rendered_back_image_url"]
    postcard_layout = order_level_values["postcard_layout"]
    postcard_layout_key = order_level_values["postcard_layout_key"]
    postcard_frame = order_level_values["postcard_frame"]
    postcard_frame_key = order_level_values["postcard_frame_key"]
    postcard_font = order_level_values["postcard_font"]
    postcard_font_key = order_level_values["postcard_font_key"]
    postcard_template = order_level_values["postcard_template"]
    product_title = ""

    for item in payload.get("line_items", []):
        item_product_title = str(item.get("title", "")).strip()
        item_values = pick_property_values(extract_line_item_properties(item))

        if item_product_title and (not product_title or (not get_template_for_product(product_title) and get_template_for_product(item_product_title))):
            product_title = item_product_title

        if item_values["message"] and not message:
            message = item_values["message"]
            if item_product_title:
                product_title = item_product_title

        if item_values["front_image_url"] and not front_image_url:
            front_image_url = item_values["front_image_url"]
            if item_product_title:
                product_title = item_product_title

        if item_values["front_image_urls"]:
            for image_url in item_values["front_image_urls"]:
                if image_url and image_url not in front_image_urls:
                    front_image_urls.append(image_url)
            if item_product_title:
                product_title = item_product_title

        if item_values["back_image_url"] and not back_image_url:
            back_image_url = item_values["back_image_url"]
            if item_product_title:
                product_title = item_product_title

        if item_values["postcard_background_image"] and not postcard_background_image:
            postcard_background_image = item_values["postcard_background_image"]

        if item_values["rendered_back_image_url"] and not rendered_back_image_url:
            rendered_back_image_url = item_values["rendered_back_image_url"]

        if item_values["from_name"] and not from_name:
            from_name = item_values["from_name"]

        if item_values["to_name"] and not to_name:
            to_name = item_values["to_name"]

        if item_values["postcard_template"] and not postcard_template:
            postcard_template = item_values["postcard_template"]

        if item_values["postcard_layout_key"] and postcard_layout_key == "single":
            postcard_layout_key = item_values["postcard_layout_key"]
            postcard_layout = item_values["postcard_layout"]

        if item_values["postcard_frame_key"] and postcard_frame_key == "classic-ivory":
            postcard_frame_key = item_values["postcard_frame_key"]
            postcard_frame = item_values["postcard_frame"]

        if item_values["postcard_font_key"] and postcard_font_key == "caveat":
            postcard_font_key = item_values["postcard_font_key"]
            postcard_font = item_values["postcard_font"]

    if not message or not from_name or not to_name or not front_image_url or not back_image_url or not front_image_urls or not postcard_background_image or not rendered_back_image_url:
        deep_values = pick_property_values(iter_named_values_deep(payload))
        if deep_values["message"] and not message:
            message = deep_values["message"]
        if deep_values["front_image_url"] and not front_image_url:
            front_image_url = deep_values["front_image_url"]
        if deep_values["front_image_urls"]:
            for image_url in deep_values["front_image_urls"]:
                if image_url and image_url not in front_image_urls:
                    front_image_urls.append(image_url)
        if deep_values["back_image_url"] and not back_image_url:
            back_image_url = deep_values["back_image_url"]
        if deep_values["postcard_background_image"] and not postcard_background_image:
            postcard_background_image = deep_values["postcard_background_image"]
        if deep_values["rendered_back_image_url"] and not rendered_back_image_url:
            rendered_back_image_url = deep_values["rendered_back_image_url"]
        if deep_values["from_name"] and not from_name:
            from_name = deep_values["from_name"]
        if deep_values["to_name"] and not to_name:
            to_name = deep_values["to_name"]
        if deep_values["postcard_template"] and not postcard_template:
            postcard_template = deep_values["postcard_template"]
        if deep_values["postcard_layout_key"] and postcard_layout_key == "single":
            postcard_layout_key = deep_values["postcard_layout_key"]
            postcard_layout = deep_values["postcard_layout"]
        if deep_values["postcard_frame_key"] and postcard_frame_key == "classic-ivory":
            postcard_frame_key = deep_values["postcard_frame_key"]
            postcard_frame = deep_values["postcard_frame"]
        if deep_values["postcard_font_key"] and postcard_font_key == "caveat":
            postcard_font_key = deep_values["postcard_font_key"]
            postcard_font = deep_values["postcard_font"]

    if front_image_urls and not front_image_url:
        front_image_url = front_image_urls[0]

    if front_image_url and front_image_url not in front_image_urls:
        front_image_urls.insert(0, front_image_url)

    return {
        "order_id": order_id,
        "order_name": order_name,
        "product_title": product_title,
        "message": message,
        "from_name": from_name,
        "to_name": to_name,
        "front_image_url": front_image_url,
        "front_image_urls": front_image_urls[:6],
        "back_image_url": back_image_url,
        "postcard_background_image": postcard_background_image,
        "rendered_back_image_url": rendered_back_image_url,
        "postcard_layout": postcard_layout,
        "postcard_layout_key": postcard_layout_key,
        "postcard_frame": postcard_frame,
        "postcard_frame_key": postcard_frame_key,
        "postcard_font": postcard_font,
        "postcard_font_key": postcard_font_key,
        "postcard_template": postcard_template,
    }


def format_message_lines(message: str, max_lines: int = 3, max_chars_per_line: int = 26):
    cleaned = " ".join((message or "").replace("\r", " ").replace("\n", " ").split())
    if not cleaned:
        return [""]

    wrapped = wrap(
        cleaned,
        width=max_chars_per_line,
        break_long_words=False,
        break_on_hyphens=False,
    )

    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        last_line = wrapped[-1].rstrip()
        if len(last_line) > max_chars_per_line - 3:
            last_line = last_line[: max_chars_per_line - 3].rstrip()
        wrapped[-1] = f"{last_line}..."

    return wrapped


def resolve_postcard_assets(details):
    template = get_template_for_product(details["product_title"])
    front_image_url = str(details.get("front_image_url", "") or "").strip()
    back_image_url = str(details.get("back_image_url", "") or "").strip()

    if front_image_url and back_image_url:
        return {
            "front": front_image_url,
            "back": back_image_url,
        }

    if template is None:
        return None

    return {
        "front": front_image_url or template["front"],
        "back": back_image_url or template["back"],
    }


def insert_postcard(details, assets):
    db = get_db()
    order_id_candidates = build_order_id_candidates(details["order_id"])
    preferred_slug = build_preferred_postcard_slug(details)

    if order_id_candidates:
        placeholders = ", ".join("?" for _ in order_id_candidates)
        existing = db.execute(
            f"""
            SELECT id, slug
            FROM postcards
            WHERE order_id IN ({placeholders})
            ORDER BY id DESC
            LIMIT 1
            """,
            order_id_candidates,
        ).fetchone()
        if existing:
            next_slug = existing["slug"]
            if preferred_slug and is_probably_generated_slug(existing["slug"]):
                next_slug = generate_unique_slug(db, preferred_slug)

            db.execute(
                """
                UPDATE postcards
                SET order_id = ?,
                    order_name = ?,
                    slug = ?,
                    product_title = ?,
                    message = ?,
                    from_name = ?,
                    to_name = ?,
                    front_image_url = ?,
                    back_image_url = ?,
                    front_image_urls = ?,
                    postcard_background_image = ?,
                    postcard_layout = ?,
                    postcard_layout_key = ?,
                    postcard_frame = ?,
                    postcard_frame_key = ?,
                    postcard_font = ?,
                    postcard_font_key = ?,
                    postcard_template = ?,
                    rendered_back_image_url = ?
                WHERE id = ?
                """,
                (
                    details["order_id"],
                    details["order_name"],
                    next_slug,
                    details["product_title"],
                    details["message"],
                    details["from_name"],
                    details["to_name"],
                    assets["front"],
                    assets["back"],
                    json.dumps(details.get("front_image_urls", []), ensure_ascii=False),
                    details.get("postcard_background_image", ""),
                    details["postcard_layout"],
                    details["postcard_layout_key"],
                    details["postcard_frame"],
                    details["postcard_frame_key"],
                    details["postcard_font"],
                    details["postcard_font_key"],
                    details.get("postcard_template", ""),
                    details.get("rendered_back_image_url", ""),
                    existing["id"],
                ),
            )
            db.commit()
            return next_slug

    slug = generate_unique_slug(db, preferred_slug)
    db.execute(
        """
        INSERT INTO postcards (
            order_id,
            order_name,
            slug,
            product_title,
            message,
            from_name,
            to_name,
            front_image_url,
            back_image_url,
            front_image_urls,
            postcard_background_image,
            postcard_layout,
            postcard_layout_key,
            postcard_frame,
            postcard_frame_key,
            postcard_font,
            postcard_font_key,
            postcard_template,
            rendered_back_image_url,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            details["order_id"],
            details["order_name"],
            slug,
            details["product_title"],
            details["message"],
            details["from_name"],
            details["to_name"],
            assets["front"],
            assets["back"],
            json.dumps(details.get("front_image_urls", []), ensure_ascii=False),
            details.get("postcard_background_image", ""),
            details["postcard_layout"],
            details["postcard_layout_key"],
            details["postcard_frame"],
            details["postcard_frame_key"],
            details["postcard_font"],
            details["postcard_font_key"],
            details.get("postcard_template", ""),
            details.get("rendered_back_image_url", ""),
            utc_now_iso(),
        ),
    )
    db.commit()
    return slug


ensure_db()


def log_webhook_debug_event(topic, payload, details):
    db = get_db()
    order_property_keys = []
    for prop_name, _ in extract_named_values(payload, ("note_attributes", "noteAttributes", "attributes", "custom_attributes", "customAttributes")):
        if prop_name and prop_name not in order_property_keys:
            order_property_keys.append(prop_name)

    line_item_property_keys = []
    for item in payload.get("line_items", []):
        for prop_name, _ in extract_line_item_properties(item):
            if prop_name and prop_name not in line_item_property_keys:
                line_item_property_keys.append(prop_name)

    db.execute(
        """
        INSERT INTO webhook_debug_events (
            created_at,
            topic,
            order_id,
            order_name,
            order_property_keys,
            line_item_property_keys,
            extracted_message_length,
            extracted_from_length,
            extracted_to_length
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now_iso(),
            str(topic or ""),
            details.get("order_id", ""),
            details.get("order_name", ""),
            json.dumps(order_property_keys, ensure_ascii=True),
            json.dumps(line_item_property_keys, ensure_ascii=True),
            len(str(details.get("message", "") or "")),
            len(str(details.get("from_name", "") or "")),
            len(str(details.get("to_name", "") or "")),
        ),
    )
    db.execute(
        """
        DELETE FROM webhook_debug_events
        WHERE id NOT IN (
            SELECT id
            FROM webhook_debug_events
            ORDER BY id DESC
            LIMIT 50
        )
        """
    )
    db.commit()


@app.route("/")
def home():
    return "Server radi", 200


@app.route("/health")
def health():
    return "ok", 200


def process_shopify_order_webhook():
    payload = request.get_json(silent=True) or {}
    source_topic = str(request.headers.get("X-Shopify-Topic", "")).strip()
    details = extract_postcard_details(payload)
    property_names = []
    for item in payload.get("line_items", []):
        for prop_name, _prop_value in extract_line_item_properties(item):
            if prop_name and prop_name not in property_names:
                property_names.append(prop_name)
    log_webhook_debug_event(source_topic, payload, details)
    print(json.dumps({
        "event": "shopify_order_webhook",
        "topic": source_topic,
        "order_id_raw": str(payload.get("id", "")).strip(),
        "order_id_normalized": details["order_id"],
        "order_name": details["order_name"],
        "from_name": details["from_name"],
        "to_name": details["to_name"],
        "line_item_count": len(payload.get("line_items", [])),
        "property_names": property_names,
        "product_titles": [str(item.get("title", "")).strip() for item in payload.get("line_items", [])],
    }, ensure_ascii=True))

    assets = resolve_postcard_assets(details)
    if assets is None:
        return jsonify({
            "ok": False,
            "error": "Could not resolve postcard assets",
            "topic": source_topic,
            "product_title": details["product_title"],
            "order_id": details["order_id"],
        }), 200

    slug = insert_postcard(details, assets)
    postcard_url = build_postcard_url(slug)

    return jsonify({
        "ok": True,
        "slug": slug,
        "url": postcard_url,
        "topic": source_topic,
        "order_id": details["order_id"],
    }), 200


@app.route("/webhooks/orders-paid", methods=["POST", "OPTIONS"])
@app.route("/webhooks/orders-create", methods=["POST", "OPTIONS"])
@app.route("/webhooks/orders-updated", methods=["POST", "OPTIONS"])
def shopify_order_webhook():
    if request.method == "OPTIONS":
        return cors_preflight_response()

    return process_shopify_order_webhook()


@app.route("/api/download-links", methods=["GET", "OPTIONS"])
def download_links():
    if request.method == "OPTIONS":
        return cors_preflight_response()

    order_id = str(request.args.get("orderId", "")).strip()
    order_id_candidates = build_order_id_candidates(order_id)
    order_name_candidates = build_order_name_candidates(order_id)
    print(json.dumps({
        "event": "download_links_lookup",
        "order_id_raw": order_id,
        "order_id_candidates": order_id_candidates,
        "order_name_candidates": order_name_candidates,
    }, ensure_ascii=True))

    if not order_id_candidates:
        return jsonify({
            "ready": False,
            "links": [],
            "error": "Missing orderId",
        }), 400

    db = get_db()
    order_id_placeholders = ", ".join("?" for _ in order_id_candidates)
    order_name_placeholders = ", ".join("?" for _ in order_name_candidates)
    postcard = db.execute(
        f"""
        SELECT slug, product_title
        FROM postcards
        WHERE order_id IN ({order_id_placeholders})
           OR order_name IN ({order_name_placeholders})
        ORDER BY id DESC
        LIMIT 1
        """,
        [*order_id_candidates, *order_name_candidates],
    ).fetchone()

    if not postcard:
        return jsonify({
            "ready": False,
            "links": [],
        }), 200

    postcard_url = build_postcard_url(postcard["slug"])

    return jsonify({
        "ready": True,
        "links": [
            {
                "title": f"Open {postcard['product_title']}",
                "url": postcard_url,
            }
        ],
    }), 200


@app.route("/api/postcard-by-order/<order_id>")
def postcard_by_order(order_id):
    db = get_db()
    order_id_candidates = build_order_id_candidates(order_id)
    order_name_candidates = build_order_name_candidates(order_id)
    order_id_placeholders = ", ".join("?" for _ in order_id_candidates)
    order_name_placeholders = ", ".join("?" for _ in order_name_candidates)
    postcard = db.execute(
        f"""
        SELECT slug
        FROM postcards
        WHERE order_id IN ({order_id_placeholders})
           OR order_name IN ({order_name_placeholders})
        ORDER BY id DESC
        LIMIT 1
        """,
        [*order_id_candidates, *order_name_candidates],
    ).fetchone()

    if not postcard:
        return jsonify({"ok": False, "error": "Postcard not found for order"}), 404

    return jsonify({
        "ok": True,
        "order_id": normalize_shopify_order_id(order_id),
        "slug": postcard["slug"],
        "url": build_postcard_url(postcard["slug"]),
    }), 200


@app.route("/p/<slug>")
def view_postcard(slug):
    db = get_db()
    postcard = db.execute(
        "SELECT * FROM postcards WHERE slug = ?",
        (slug,),
    ).fetchone()

    if not postcard:
        return "Razglednica nije pronadena.", 404

    postcard_data = dict(postcard)
    front_images = load_front_image_urls(
        postcard_data.get("front_image_urls", ""),
        postcard_data.get("front_image_url", ""),
    )
    postcard_layout_key = normalize_postcard_layout_key(
        postcard_data.get("postcard_layout_key", "") or postcard_data.get("postcard_layout", "")
    )
    if postcard_layout_key == "single" and len(front_images) > 1:
        postcard_layout_key = infer_layout_key_from_image_count(len(front_images))
    postcard_frame_key = normalize_postcard_frame_key(
        postcard_data.get("postcard_frame_key", "") or postcard_data.get("postcard_frame", "")
    )
    postcard_font_key = normalize_postcard_font_key(
        postcard_data.get("postcard_font_key", "") or postcard_data.get("postcard_font", "")
    )
    message_style = resolve_message_style(postcard_font_key, resolve_message_side(postcard_data))
    layout_preset = POSTCARD_LAYOUT_PRESETS[postcard_layout_key]
    frame_preset = POSTCARD_FRAME_PRESETS[postcard_frame_key]
    rendered_back_image_url = str(postcard_data.get("rendered_back_image_url", "") or "").strip()

    if front_images:
        postcard_data["front_image_url"] = front_images[0]

    if rendered_back_image_url:
        postcard_data["back_image_url"] = rendered_back_image_url

    postcard_data["front_image_urls"] = json.dumps(front_images, ensure_ascii=False)
    postcard_data["postcard_layout"] = postcard_data.get("postcard_layout") or layout_preset["label"]
    postcard_data["postcard_layout_key"] = postcard_layout_key
    postcard_data["postcard_frame"] = postcard_data.get("postcard_frame") or frame_preset["label"]
    postcard_data["postcard_frame_key"] = postcard_frame_key
    postcard_data["postcard_font"] = postcard_data.get("postcard_font") or message_style["label"]
    postcard_data["postcard_font_key"] = postcard_font_key

    front_slots = [
        {
            "slot_class": slot_class,
            "image_url": front_images[index] if index < len(front_images) else "",
        }
        for index, slot_class in enumerate(layout_preset["slot_classes"])
    ]

    message_lines = format_message_lines(postcard_data["message"])
    return render_template_string(
        VIEW_HTML,
        postcard=postcard_data,
        front_slots=front_slots,
        postcard_layout_class=layout_preset.get("class_name", f"layout-{postcard_layout_key}"),
        postcard_frame_class=f"frame-{postcard_frame_key}",
        message_lines=message_lines,
        message_style=message_style,
        hide_message_overlay=bool(rendered_back_image_url),
    )


@app.route("/api/debug/postcards", methods=["GET"])
def debug_postcards():
    limit = max(1, min(int(request.args.get("limit", "10")), 50))
    order_id = str(request.args.get("orderId", "")).strip()

    db = get_db()
    params = []
    where_sql = ""
    if order_id:
        order_id_candidates = build_order_id_candidates(order_id)
        placeholders = ", ".join("?" for _ in order_id_candidates)
        where_sql = f"WHERE order_id IN ({placeholders})"
        params.extend(order_id_candidates)

    rows = db.execute(
        f"""
        SELECT id, order_id, order_name, product_title, slug, from_name, to_name, created_at
        FROM postcards
        {where_sql}
        ORDER BY id DESC
        LIMIT ?
        """,
        [*params, limit],
    ).fetchall()

    return jsonify({
        "count": len(rows),
        "rows": [dict(row) for row in rows],
    }), 200


@app.route("/api/debug/webhooks", methods=["GET"])
def debug_webhooks():
    limit = max(1, min(int(request.args.get("limit", "10")), 50))
    db = get_db()
    rows = db.execute(
        """
        SELECT
            id,
            created_at,
            topic,
            order_id,
            order_name,
            order_property_keys,
            line_item_property_keys,
            extracted_message_length,
            extracted_from_length,
            extracted_to_length
        FROM webhook_debug_events
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    return jsonify({
        "count": len(rows),
        "rows": [
            {
                **dict(row),
                "order_property_keys": json.loads(row["order_property_keys"] or "[]"),
                "line_item_property_keys": json.loads(row["line_item_property_keys"] or "[]"),
            }
            for row in rows
        ],
    }), 200


@app.route("/latest")
def latest_postcard():
    db = get_db()
    postcard = db.execute(
        "SELECT * FROM postcards ORDER BY id DESC LIMIT 1"
    ).fetchone()

    if not postcard:
        return "Nema razglednica.", 404

    return build_postcard_url(postcard["slug"]), 200


@app.route("/previews")
def previews():
    db = get_db()
    postcards = db.execute(
        """
        SELECT id, order_id, order_name, slug, product_title, to_name, front_image_url, created_at
        FROM postcards
        ORDER BY id DESC
        """
    ).fetchall()
    return render_template_string(
        PREVIEWS_HTML,
        postcards=postcards,
        base_url=request.host_url.rstrip("/"),
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

