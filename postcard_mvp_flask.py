from flask import Flask, request, jsonify, render_template_string, g, make_response
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from textwrap import wrap
import re

app = Flask(__name__)
DATABASE = os.getenv("DATABASE_PATH", "postcards.db")

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
  <title>{{ postcard['product_title'] }}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Caveat:wght@500;600;700&family=Cormorant+Garamond:wght@500;600&family=Manrope:wght@400;500;600;700&display=swap');
    :root {
      --bg-top: #fbf7f2;
      --bg-mid: #efe6de;
      --bg-bottom: #e7ddd6;
      --ink: #2f2427;
      --muted: rgba(47, 36, 39, 0.58);
      --line: rgba(65, 105, 124, 0.14);
      --card-radius: 30px;
      --card-shadow: 0 38px 96px rgba(64, 94, 108, 0.16);
      --card-shadow-strong: 0 58px 140px rgba(44, 72, 89, 0.16);
      --glass: rgba(255, 255, 255, 0.7);
      --panel-bg: linear-gradient(180deg, rgba(255,255,255,0.82), rgba(255,248,238,0.68));
      --panel-border: rgba(255,255,255,0.84);
      --accent: #b78b4e;
      --message-font-size: 22.4px;
      --message-rotation: -1.8deg;
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

    .story-panel {
      position: fixed;
      top: 94px;
      left: 50%;
      transform: translateX(-50%) translateY(16px);
      width: min(72vw, 520px);
      display: grid;
      gap: 7px;
      padding: 14px 18px;
      border-radius: 24px;
      background: var(--panel-bg);
      border: 1px solid var(--panel-border);
      box-shadow: 0 16px 42px rgba(93, 123, 138, 0.1);
      backdrop-filter: blur(16px);
      text-align: center;
      opacity: 0;
      transition: opacity 0.9s ease, transform 1s var(--ease);
      z-index: 2;
    }

    .story-panel-eyebrow {
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.28em;
      text-transform: uppercase;
      color: rgba(103, 118, 125, 0.72);
    }

    .story-panel-title {
      font-family: "Cinzel", Georgia, serif;
      font-size: clamp(18px, 2.4vw, 28px);
      letter-spacing: 0.04em;
      color: rgba(42, 63, 75, 0.92);
    }

    .story-panel-copy {
      margin: 0 auto;
      max-width: 42ch;
      font-size: 12px;
      line-height: 1.55;
      color: rgba(72, 91, 101, 0.8);
    }

    body.reveal-active .story-panel,
    body.is-ready .story-panel {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }

    .scene {
      position: relative;
      width: min(80vw, 620px);
      aspect-ratio: 3 / 2;
      display: grid;
      place-items: center;
      perspective: 2200px;
      margin-top: 34px;
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
      inset: 10% 16% 20%;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(255, 243, 220, 0.72), rgba(255,255,255,0) 66%);
      filter: blur(38px);
      opacity: 0.72;
      transform: translateY(6px) scale(0.94);
      transition: opacity 0.9s ease, transform 1s var(--ease-soft);
      pointer-events: none;
    }

    body.is-ready .scene::after {
      opacity: 0.82;
      transform: translateY(0) scale(1);
    }

    body.is-open .scene::after {
      opacity: 1;
      transform: translateY(-4px) scale(1.03);
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
      filter: blur(10px);
      transform: translate3d(0, 22px, 0) scale(0.975);
      transform-style: preserve-3d;
      transition: opacity 0.8s ease, filter 0.8s ease, transform 1s var(--ease-soft), box-shadow 0.9s ease;
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

    body.is-ready .postcard-shell::before {
      opacity: 0.72;
    }

    body.is-ready .postcard-shell {
      opacity: 1;
      filter: blur(0);
      transform: translate3d(0, 10px, 0) scale(0.985);
    }

    body.is-open .postcard-shell {
      transform:
        translate3d(var(--drift-x), calc(var(--drift-y) * 0.28 - 10px), 0)
        scale(1.01)
        rotateX(calc(var(--tilt-x) * 0.25))
        rotateY(calc(var(--tilt-y) * 0.25));
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
      inset: -22px;
      border-radius: calc(var(--card-radius) + 18px);
      background:
        radial-gradient(circle at 50% 48%, rgba(255, 239, 205, 0.44), rgba(255,255,255,0) 52%),
        linear-gradient(135deg, rgba(255,255,255,0.66), rgba(243, 228, 202, 0.2) 34%, rgba(183, 164, 139, 0.08) 62%, transparent 78%);
      filter: blur(20px);
      opacity: 0.92;
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
      transition: transform 1s var(--ease-soft);
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

    body.is-open .postcard::after {
      animation: postcardGleam 1.05s var(--ease-soft) 0.14s forwards;
    }

    body.is-open .postcard,
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
      top: 46.4%;
      left: 53.0%;
      width: 38.9%;
      height: 19.2%;
      overflow: hidden;
      display: flex;
      align-items: flex-start;
      justify-content: flex-start;
      padding-right: 2%;
      opacity: 0;
      transform: translateY(18px);
      transition: opacity 0.55s ease, transform 0.7s var(--ease-soft);
      transition-delay: 0s;
    }

    body.is-open .message-area {
      opacity: 1;
      transform: translateY(0);
      transition-delay: 0.34s;
    }

    .message-lines {
      width: 100%;
      display: grid;
      gap: 0.2em;
      text-align: left;
      align-content: start;
      font-family: "Caveat", "Brush Script MT", cursive;
      font-size: var(--message-font-size);
      line-height: 1.14;
      letter-spacing: 0.015em;
      font-weight: 600;
      color: rgba(83, 60, 45, 0.88);
      text-shadow: 0 1px 0 rgba(255,255,255,0.12);
      transform-origin: top left;
      transform: rotate(var(--message-rotation));
      filter: saturate(0.92);
      transition: opacity 0.45s ease, transform 0.7s var(--ease-soft);
    }

    .message-line {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: clip;
      padding-left: 0.08em;
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

    .controls {
      position: fixed;
      left: 50%;
      bottom: 22px;
      transform: translateX(-50%) translateY(8px);
      width: min(82vw, 660px);
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 12px;
      opacity: 0;
      transition: opacity 0.85s ease, transform 1s var(--ease-soft);
      z-index: 2;
    }

    body.is-ready .controls,
    body.is-open .controls {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }

    .hint {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 12px 18px;
      border-radius: 999px;
      background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(246,241,233,0.8));
      border: 1px solid rgba(255,255,255,0.86);
      color: rgba(58, 53, 49, 0.82);
      box-shadow: 0 12px 24px rgba(145, 184, 198, 0.12);
      backdrop-filter: blur(12px);
      font-size: 10px;
      letter-spacing: 0.2em;
      text-transform: uppercase;
    }

    .hint::before {
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: linear-gradient(180deg, #fffdf8, #d8b56f);
      box-shadow: 0 0 14px rgba(194, 153, 75, 0.52);
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
      border: 1px solid rgba(169, 144, 93, 0.34);
      background: linear-gradient(180deg, rgba(255,255,255,0.62), rgba(240,231,215,0.34));
      color: rgba(60, 56, 50, 0.88);
      box-shadow: 0 12px 24px rgba(98, 83, 54, 0.1);
      backdrop-filter: blur(10px);
    }

    @media (max-width: 760px) {
      .experience {
        min-height: 100svh;
        padding: 12px 10px 56px;
      }

      .story-panel {
        top: 76px;
        width: min(90vw, 520px);
        padding: 14px 16px;
      }

      .brand-mark {
        top: 10px;
        min-width: min(56vw, 220px);
        padding: 10px 14px;
      }

      .scene {
        width: min(92vw, calc((100svh - 220px) * 1.5), 620px);
        margin-top: 56px;
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
        top: 8px;
        min-width: min(58vw, 208px);
      }

      .scene {
        width: min(96vw, calc((100svh - 205px) * 1.5), 520px);
        margin-top: 62px;
      }

      .controls {
        width: min(96vw, 520px);
        margin-top: 6px;
      }

      .message-area {
        top: 46.8%;
        left: 53.2%;
        width: 38.9%;
        height: 18%;
      }

      .message-lines {
        font-size: 15.6px;
        line-height: 1.08;
        gap: 0.16em;
      }
    }

    @media (max-height: 760px) and (max-width: 760px) {
      .brand-mark {
        top: 8px;
        min-width: min(62vw, 210px);
      }

      .scene {
        width: min(90vw, calc((100svh - 190px) * 1.5), 480px);
        margin-top: 56px;
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
    <div class="brand-mark" id="brandMark" aria-hidden="true">
      <img src="/static/send-a-memory-logo.png" alt="Send a Memory" id="brandLogo">
      <span class="brand-mark-fallback">Send a Memory</span>
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
      <div class="actions">
        <button class="button button-secondary" id="replayButton">Replay the moment</button>
      </div>
    </div>
  </main>

  <script>
    const body = document.body;
    const postcard = document.getElementById('postcard');
    const postcardShell = document.getElementById('postcardShell');
    const flipButton = document.getElementById('flipButton');
    const replayButton = document.getElementById('replayButton');
    
    const brandMark = document.getElementById('brandMark');
    const brandLogo = document.getElementById('brandLogo');
    const scene = document.querySelector('.scene');
    const messageArea = document.getElementById('messageArea');
    const messageLines = document.getElementById('messageLines');
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    let isOpen = false;

    // Show a clean text fallback when the logo image path is unavailable.
    if (brandLogo) {
      brandLogo.addEventListener('error', () => {
        brandMark?.classList.add('is-fallback');
      }, { once: true });
    }

    function setDrift(x = 0, y = 0) {
      body.style.setProperty('--drift-x', `${x}px`);
      body.style.setProperty('--drift-y', `${y}px`);
      body.style.setProperty('--tilt-x', `${y * -0.12}deg`);
      body.style.setProperty('--tilt-y', `${x * 0.14}deg`);
    }

    function fitMessageText() {
      if (!messageArea || !messageLines) return;

      let fontSize = 22.4;
      messageLines.style.fontSize = `${fontSize}px`;

      while (fontSize > 13.6) {
        const tooTall = messageLines.scrollHeight > messageArea.clientHeight;
        const tooWide = Array.from(messageLines.children).some(
          (line) => line.scrollWidth > messageArea.clientWidth,
        );

        if (!tooTall && !tooWide) break;

        fontSize -= 0.5;
        messageLines.style.fontSize = `${fontSize}px`;
      }
    }

    function syncOpenState(nextState) {
      isOpen = nextState;
      body.classList.toggle('is-open', isOpen);
      postcard.classList.toggle('flipped', isOpen);
      flipButton.setAttribute('aria-expanded', String(isOpen));
    }

    function openPostcard({ replay = false } = {}) {
      if (isOpen && !replay) return;

      if (replay) {
        syncOpenState(false);
        window.setTimeout(() => syncOpenState(true), prefersReducedMotion ? 20 : 120);
        return;
      }

      syncOpenState(true);
    }

    function handlePointerMove(event) {
      if (!scene || !postcardShell || !isOpen || prefersReducedMotion) return;

      const rect = scene.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width - 0.5) * 10;
      const y = ((event.clientY - rect.top) / rect.height - 0.5) * 8;
      setDrift(x, y);
    }

    function resetDrift() {
      setDrift(0, 0);
    }

    flipButton.addEventListener('click', (event) => {
      event.preventDefault();
      openPostcard();
    });

    replayButton.addEventListener('click', () => {
      openPostcard({ replay: true });
    });

    scene?.addEventListener('pointermove', handlePointerMove);
    scene?.addEventListener('pointerleave', resetDrift);

    window.addEventListener('load', () => {
      fitMessageText();
      resetDrift();
      body.classList.add('is-ready');
      syncOpenState(false);
    }, { once: true });

    window.addEventListener('resize', () => {
      fitMessageText();
      resetDrift();
    });
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
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_postcards_order_id ON postcards(order_id)"
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


def extract_line_item_properties(item):
    raw_properties = item.get("properties", [])

    if isinstance(raw_properties, dict):
        iterable = raw_properties.items()
        for key, value in iterable:
            yield str(key or "").strip(), str(value or "").strip()
        return

    for prop in raw_properties or []:
        if isinstance(prop, dict):
            yield str(prop.get("name", "")).strip(), str(prop.get("value", "")).strip()


def extract_postcard_details(payload):
    order_id = normalize_shopify_order_id(payload.get("id", ""))
    order_name = str(payload.get("name", "")).strip()

    for item in payload.get("line_items", []):
        product_title = str(item.get("title", "")).strip()
        for prop_name, prop_value in extract_line_item_properties(item):
            normalized_prop_name = prop_name.casefold().replace("_", " ").replace("-", " ").strip()
            if normalized_prop_name in MESSAGE_PROPERTY_NAMES and prop_value:
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
    order_id_candidates = build_order_id_candidates(details["order_id"])

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
            db.execute(
                """
                UPDATE postcards
                SET order_id = ?,
                    order_name = ?,
                    product_title = ?,
                    message = ?,
                    front_image_url = ?,
                    back_image_url = ?
                WHERE id = ?
                """,
                (
                    details["order_id"],
                    details["order_name"],
                    details["product_title"],
                    details["message"],
                    template["front"],
                    template["back"],
                    existing["id"],
                ),
            )
            db.commit()
            return existing["slug"]

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


def process_shopify_order_webhook():
    payload = request.get_json(silent=True) or {}
    source_topic = str(request.headers.get("X-Shopify-Topic", "")).strip()
    details = extract_postcard_details(payload)
    property_names = []
    for item in payload.get("line_items", []):
        for prop_name, _prop_value in extract_line_item_properties(item):
            if prop_name and prop_name not in property_names:
                property_names.append(prop_name)
    print(json.dumps({
        "event": "shopify_order_webhook",
        "topic": source_topic,
        "order_id_raw": str(payload.get("id", "")).strip(),
        "order_id_normalized": details["order_id"],
        "order_name": details["order_name"],
        "line_item_count": len(payload.get("line_items", [])),
        "property_names": property_names,
        "product_titles": [str(item.get("title", "")).strip() for item in payload.get("line_items", [])],
    }, ensure_ascii=True))

    if not details["message"]:
        return jsonify({
            "ok": False,
            "error": "Postcard message not found in line item properties",
            "topic": source_topic,
            "order_id": details["order_id"],
            "order_name": details["order_name"],
        }), 200

    template = get_template_for_product(details["product_title"])
    if template is None:
        return jsonify({
            "ok": False,
            "error": "Unknown product title",
            "topic": source_topic,
            "product_title": details["product_title"],
            "order_id": details["order_id"],
        }), 200

    slug = insert_postcard(details, template)
    postcard_url = f"{request.host_url.rstrip('/')}/p/{slug}"

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
        SELECT id, order_id, order_name, product_title, slug, created_at
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