from flask import Flask, request, jsonify, render_template_string, g, make_response
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from textwrap import wrap

app = Flask(__name__)
DATABASE = os.getenv("DATABASE_PATH", "postcards.db")

TEMPLATES = {
    "Riva": {
        "front": "https://frostifymart.com/cdn/shop/files/Panorama_Splita.jpg?v=1775754558&width=1200",
        "back": "https://frostifymart.com/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },
    "Peristil": {
        "front": "https://frostifymart.com/cdn/shop/files/Peristil_65009f39-156f-4e41-a913-9e8d7896db8b.jpg?v=1775754568&width=1200",
        "back": "https://frostifymart.com/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },
    "Cathedral of Saint Domnius": {
        "front": "https://frostifymart.com/cdn/shop/files/Sv._Duje.jpg?v=1775754570&width=1200",
        "back": "https://frostifymart.com/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },
    "Old Town": {
        "front": "https://frostifymart.com/cdn/shop/files/Varos_790dd52a-bf89-41bf-a21e-a377b559083a.jpg?v=1775763079&width=1200",
        "back": "https://frostifymart.com/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },
    "Bird View": {
        "front": "https://frostifymart.com/cdn/shop/files/Splitizzraka.jpg?v=1775742362&width=1200",
        "back": "https://frostifymart.com/cdn/shop/files/Split_Straznja_f5e126dd-f237-48d6-aa02-c74712f703c8.png?v=1775749874&width=1200",
    },
}

VIEW_HTML = r"""
<!doctype html>
<html lang="hr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ postcard['product_title'] }}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600&family=Manrope:wght@400;500;600;700&display=swap');
    :root {
      --bg-top: #f7fbfd;
      --bg-mid: #edf5f8;
      --bg-bottom: #f5efe6;
      --ink: #163142;
      --muted: rgba(22, 49, 66, 0.64);
      --line: rgba(65, 105, 124, 0.14);
      --card-radius: 30px;
      --card-shadow: 0 38px 96px rgba(64, 94, 108, 0.16);
      --card-shadow-strong: 0 58px 140px rgba(44, 72, 89, 0.16);
      --glass: rgba(255, 255, 255, 0.7);
      --message-font-size: 18px;
      --ease: cubic-bezier(0.22, 1, 0.36, 1);
      --ease-soft: cubic-bezier(0.16, 1, 0.3, 1);
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
        radial-gradient(circle at 50% 8%, rgba(255, 223, 135, 0.76), transparent 20%),
        radial-gradient(circle at 22% 28%, rgba(255, 243, 209, 0.92), transparent 24%),
        radial-gradient(circle at 82% 26%, rgba(255, 239, 204, 0.7), transparent 22%),
        linear-gradient(180deg, #fffaf0 0%, #fff7df 24%, #f6f0e4 56%, #d6edf9 81%, #5b9fe2 100%);
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
        radial-gradient(circle at 50% 12%, rgba(255, 214, 101, 0.32), transparent 24%),
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
        radial-gradient(circle, rgba(255, 239, 180, 0.98), rgba(255, 224, 126, 0.54) 42%, rgba(255, 223, 127, 0.04) 72%, transparent 76%);
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
        conic-gradient(from 180deg at 50% 0%, rgba(255, 225, 132, 0.18), rgba(255,255,255,0) 12%, rgba(255, 225, 132, 0.08) 22%, rgba(255,255,255,0) 34%, rgba(255, 225, 132, 0.06) 46%, rgba(255,255,255,0) 58%, rgba(255, 225, 132, 0.08) 70%, rgba(255,255,255,0) 82%, rgba(255, 225, 132, 0.16));
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
        radial-gradient(circle, rgba(146, 216, 240, 0.38), rgba(146, 216, 240, 0.12) 58%, transparent 76%);
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
        linear-gradient(180deg, rgba(188, 227, 248, 0.18), rgba(138, 194, 236, 0.74));
      clip-path: ellipse(74% 62% at 50% 100%);
      opacity: 0.95;
    }

    .coast-waves::after {
      height: 17vh;
      background:
        linear-gradient(180deg, rgba(95, 164, 226, 0.88), rgba(39, 111, 189, 0.98));
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
      padding: 20px 20px 96px;
      z-index: 1;
    }

    .brand-mark {
      position: fixed;
      top: 18px;
      left: 50%;
      transform: translateX(-50%) translateY(-10px) scale(0.96);
      display: flex;
      align-items: center;
      justify-content: center;
      width: min(34vw, 190px);
      opacity: 0;
      transition: opacity 0.9s ease, transform 1.1s var(--ease);
      z-index: 2;
    }

    .brand-mark img {
      width: 100%;
      height: auto;
      display: block;
      filter:
        drop-shadow(0 10px 28px rgba(255, 190, 90, 0.18))
        drop-shadow(0 2px 8px rgba(255, 255, 255, 0.34));
    }

    body.reveal-active .brand-mark,
    body.is-ready .brand-mark {
      opacity: 1;
      transform: translateX(-50%) translateY(0) scale(1);
    }

    .scene {
      position: relative;
      width: min(82vw, 660px);
      aspect-ratio: 3 / 2;
      display: grid;
      place-items: center;
      perspective: 2200px;
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

    body.reveal-active .reveal-halo,
    body.reveal-active .reveal-flash,
    body.reveal-active .reveal-sweep,
    body.is-ready .reveal-halo,
    body.is-ready .reveal-flash,
    body.is-ready .reveal-sweep {
      opacity: 1;
    }

    body.reveal-active .reveal-halo,
    body.is-ready .reveal-halo {
      transform: scale(1);
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
      transition: opacity 1.2s ease, filter 1.25s ease, transform 1.75s var(--ease);
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
      transform: translate3d(0, 0, 0) scale(1) rotateX(0deg);
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
      inset: -16px;
      border-radius: calc(var(--card-radius) + 14px);
      background:
        linear-gradient(135deg, rgba(255,255,255,0.52), rgba(255, 231, 193, 0.12) 38%, transparent 72%);
      filter: blur(14px);
      opacity: 0.82;
      transform: translateZ(-8px);
    }

    .card-glow::before {
      content: "";
      position: absolute;
      inset: 8px;
      border-radius: calc(var(--card-radius) + 4px);
      border: 1px solid rgba(255, 243, 218, 0.46);
      opacity: 0.72;
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
      top: 49.6%;
      left: 53.3%;
      width: 38.6%;
      height: 17.8%;
      overflow: hidden;
      display: flex;
      align-items: flex-start;
      justify-content: flex-start;
    }

    .message-lines {
      width: 100%;
      display: grid;
      gap: 0.62em;
      text-align: left;
      align-content: start;
      font-family: "Cinzel", Georgia, serif;
      font-size: 16px;
      line-height: 1.92;
      letter-spacing: 0.015em;
      color: rgba(106, 76, 49, 0.9);
      text-shadow: 0 1px 0 rgba(255,255,255,0.18);
      transform-origin: top left;
    }

    .message-line {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: clip;
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

    .controls {
      position: fixed;
      left: 50%;
      bottom: 18px;
      transform: translateX(-50%) translateY(8px);
      width: min(82vw, 660px);
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 12px;
      opacity: 0;
      transition: opacity 0.85s ease, transform 0.85s var(--ease-soft);
    }

    body.is-ready .controls {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }

    .hint {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 11px 16px;
      border-radius: 999px;
      background: linear-gradient(180deg, rgba(255,255,255,0.82), rgba(255,250,242,0.68));
      border: 1px solid rgba(255,255,255,0.86);
      color: rgba(78, 94, 102, 0.82);
      box-shadow: 0 12px 24px rgba(145, 184, 198, 0.12);
      backdrop-filter: blur(12px);
      font-size: 9px;
      letter-spacing: 0.24em;
      text-transform: uppercase;
    }

    .hint::before {
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: linear-gradient(180deg, #fffdf8, #f0d18d);
      box-shadow: 0 0 14px rgba(245, 206, 113, 0.66);
    }

    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
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
      transition: transform 0.25s ease, background 0.25s ease;
    }

    .button:hover {
      transform: translateY(-1px);
    }

    .button-primary {
      border: 1px solid rgba(255,255,255,0.9);
      background: rgba(255,255,255,0.76);
      color: rgba(47, 80, 93, 0.92);
      box-shadow: 0 14px 30px rgba(133, 176, 192, 0.14);
    }

    .button-secondary {
      border: 1px solid rgba(214, 190, 144, 0.28);
      background: linear-gradient(180deg, rgba(255,255,255,0.52), rgba(255,244,226,0.32));
      color: rgba(97, 101, 96, 0.86);
      box-shadow: 0 10px 22px rgba(201, 170, 103, 0.08);
      backdrop-filter: blur(10px);
    }

    @media (max-width: 760px) {
      .experience {
        min-height: 100svh;
        padding: 12px 10px 56px;
      }

      .brand-mark {
        top: 8px;
        width: min(42vw, 156px);
      }

      .scene {
        width: min(92vw, calc((100svh - 190px) * 1.5), 620px);
      }

      .controls {
        width: min(92vw, 620px);
      }

      .controls {
        position: static;
        transform: none;
        margin-top: 8px;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
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

      .hint {
        padding: 9px 12px;
        font-size: 8px;
        letter-spacing: 0.18em;
      }
    }

    @media (max-width: 560px) {
      .experience {
        padding: 10px 8px 48px;
      }

      .brand-mark {
        top: 6px;
        width: min(40vw, 140px);
      }

      .scene {
        width: min(96vw, calc((100svh - 165px) * 1.5), 520px);
      }

      .controls {
        width: min(96vw, 520px);
        margin-top: 6px;
      }

      .message-area {
        top: 49.8%;
        left: 53.4%;
        width: 38.6%;
        height: 17.6%;
      }

      .message-lines {
        font-size: 11.5px;
        line-height: 1.86;
        gap: 0.5em;
      }
    }

    @media (max-height: 760px) and (max-width: 760px) {
      .brand-mark {
        top: 4px;
        width: min(36vw, 124px);
      }

      .scene {
        width: min(90vw, calc((100svh - 150px) * 1.5), 480px);
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
  <div class="sun-glow"></div>
  <div class="sun-rays"></div>
  <div class="sea-haze"></div>
  <div class="sea-shimmer"></div>
  <div class="brand-bar"></div>
  <div class="distant-city"></div>
  <div class="coastline"></div>
  <div class="coast-waves"></div>
  <div class="stage-shadow"></div>

  <main class="experience">
    <div class="brand-mark" aria-hidden="true">
      <img src="/static/send-a-memory-logo.png" alt="Send a Memory">
    </div>
    <section class="scene" aria-label="Digital postcard reveal scene">
      <div class="reveal-halo"></div>
      <div class="reveal-flash"></div>
      <div class="reveal-sweep"></div>

      <div class="postcard-shell" id="postcardShell">
        <button class="flip-target" id="flipButton" aria-label="Okreni razglednicu">
          <div class="card-glow"></div>

          <div class="postcard" id="postcard">
            <article class="face front">
              <img src="{{ postcard['front_image_url'] }}" alt="Front image">
            </article>

            <article class="face back">
              <img src="{{ postcard['back_image_url'] }}" alt="Back image">
              <div class="message-area" id="messageArea">
                <div class="message-lines" id="messageLines">
                  {% for line in message_lines %}
                    <div class="message-line">{{ line }}</div>
                  {% endfor %}
                </div>
              </div>
            </article>
          </div>
        </button>
      </div>
    </section>

    <div class="controls">
      <div class="hint" id="flipHint">Tap to flip</div>
      <div class="actions">
        <button class="button button-secondary" id="replayButton">Replay reveal</button>
      </div>
    </div>
  </main>

  <script>
    const body = document.body;
    const postcard = document.getElementById('postcard');
    const flipButton = document.getElementById('flipButton');
    const replayButton = document.getElementById('replayButton');
    const flipHint = document.getElementById('flipHint');
    const messageArea = document.getElementById('messageArea');
    const messageLines = document.getElementById('messageLines');
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
      flipHint.textContent = flipped ? 'Tap to turn it back' : 'Tap to flip';
    }

    function fitMessageText() {
      if (!messageArea || !messageLines) return;

      let fontSize = 18;
      messageLines.style.fontSize = fontSize + 'px';

      while (fontSize > 10) {
        const tooTall = messageLines.scrollHeight > messageArea.clientHeight;
        const tooWide = Array.from(messageLines.children).some(
          (line) => line.scrollWidth > messageArea.clientWidth
        );

        if (!tooTall && !tooWide) {
          break;
        }

        fontSize -= 0.5;
        messageLines.style.fontSize = fontSize + 'px';
      }
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
    window.addEventListener('pointerdown', warmAudio, { passive: true });
    window.addEventListener('keydown', warmAudio);
    window.addEventListener('load', () => {
      fitMessageText();
      warmAudio();
      runReveal();
    }, { once: true });
    window.addEventListener('resize', fitMessageText);
  </script>
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
            front_image_url TEXT NOT NULL,
            back_image_url TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
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


def get_template_for_product(product_title: str):
    return TEMPLATES.get(product_title)


def extract_postcard_details(payload):
    order_id = str(payload.get("id", "")).strip()
    order_name = str(payload.get("name", "")).strip()

    for item in payload.get("line_items", []):
        product_title = str(item.get("title", "")).strip()
        for prop in item.get("properties", []):
            prop_name = str(prop.get("name", "")).strip()
            prop_value = str(prop.get("value", "")).strip()
            if prop_name == "Postcard Message" and prop_value:
                return {
                    "order_id": order_id,
                    "order_name": order_name,
                    "product_title": product_title,
                    "message": prop_value,
                }

    return {
        "order_id": order_id,
        "order_name": order_name,
        "product_title": "",
        "message": "",
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


def insert_postcard(details, template):
    db = get_db()
    slug = generate_slug()

    db.execute(
        """
        INSERT INTO postcards (
            order_id,
            order_name,
            slug,
            product_title,
            message,
            front_image_url,
            back_image_url,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            details["order_id"],
            details["order_name"],
            slug,
            details["product_title"],
            details["message"],
            template["front"],
            template["back"],
            utc_now_iso(),
        ),
    )
    db.commit()
    return slug


ensure_db()


@app.route("/")
def home():
    return "Server radi", 200


@app.route("/health")
def health():
    return "ok", 200


@app.route("/webhooks/orders-paid", methods=["POST", "OPTIONS"])
def shopify_orders_paid():
    if request.method == "OPTIONS":
        return cors_preflight_response()

    payload = request.get_json(silent=True) or {}
    details = extract_postcard_details(payload)

    if not details["message"]:
        return jsonify({"ok": False, "error": "Postcard Message not found"}), 200

    template = get_template_for_product(details["product_title"])
    if template is None:
        return jsonify({"ok": False, "error": "Unknown product title"}), 200

    slug = insert_postcard(details, template)
    postcard_url = f"{request.host_url.rstrip('/')}/p/{slug}"

    return jsonify({
        "ok": True,
        "slug": slug,
        "url": postcard_url,
    }), 200


@app.route("/api/download-links", methods=["GET", "OPTIONS"])
def download_links():
    if request.method == "OPTIONS":
        return cors_preflight_response()

    order_id = str(request.args.get("orderId", "")).strip()

    if not order_id:
        return jsonify({
            "ready": False,
            "links": [],
            "error": "Missing orderId",
        }), 400

    db = get_db()
    postcard = db.execute(
        """
        SELECT slug, product_title
        FROM postcards
        WHERE order_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (order_id,),
    ).fetchone()

    if not postcard:
        return jsonify({
            "ready": False,
            "links": [],
        }), 200

    postcard_url = f"{request.host_url.rstrip('/')}/p/{postcard['slug']}"

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
    postcard = db.execute(
        """
        SELECT slug
        FROM postcards
        WHERE order_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (str(order_id).strip(),),
    ).fetchone()

    if not postcard:
        return jsonify({"ok": False, "error": "Postcard not found for order"}), 404

    return jsonify({
        "ok": True,
        "order_id": str(order_id).strip(),
        "slug": postcard["slug"],
        "url": f"{request.host_url.rstrip('/')}/p/{postcard['slug']}",
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

    message_lines = format_message_lines(postcard["message"])
    return render_template_string(VIEW_HTML, postcard=postcard, message_lines=message_lines)


@app.route("/latest")
def latest_postcard():
    db = get_db()
    postcard = db.execute(
        "SELECT * FROM postcards ORDER BY id DESC LIMIT 1"
    ).fetchone()

    if not postcard:
        return "Nema razglednica.", 404

    return f"{request.host_url.rstrip('/')}/p/{postcard['slug']}", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)