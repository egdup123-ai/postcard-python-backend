from flask import Flask, request, jsonify, render_template_string, g
import base64
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
      --card-radius: 30px;
      --card-shadow: 0 38px 96px rgba(64, 94, 108, 0.16);
      --card-shadow-strong: 0 58px 140px rgba(44, 72, 89, 0.16);
      --glass: rgba(255, 255, 255, 0.7);
      --message-font-size: 18px;
      --ease: cubic-bezier(0.22, 1, 0.36, 1);
      --ease-soft: cubic-bezier(0.16, 1, 0.3, 1);
      --ease-luxury: cubic-bezier(0.19, 1, 0.22, 1);
      --ease-drift: cubic-bezier(0.33, 1, 0.68, 1);
      --dur-fast: 0.72s;
      --dur-base: 1.15s;
      --dur-slow: 1.9s;
      --dur-hero: 2.35s;
      --stagger-step: 150ms;
      --scroll-shift: 0px;
      --pointer-x: 0px;
      --pointer-y: 0px;
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
      overflow-x: hidden;
      overflow-y: auto;
      scroll-behavior: smooth;
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
      transform: translate3d(0, calc(var(--scroll-shift) * -0.18), 0);
      transition: transform 0.2s linear;
    }

    body::after {
      background:
        radial-gradient(circle at center, transparent 0 54%, rgba(92, 145, 174, 0.1) 100%),
        linear-gradient(180deg, transparent 0%, transparent 74%, rgba(255,255,255,0.16) 100%);
      transform: translate3d(0, calc(var(--scroll-shift) * 0.12), 0);
      transition: transform 0.24s linear;
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
      transform:
        translateX(calc(-50% + (var(--pointer-x) * 0.012)))
        translateY(calc(var(--pointer-y) * -0.01))
        scale(1.02);
      transition: transform 1.6s var(--ease-soft);
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
      transform:
        translateX(calc(-50% + (var(--pointer-x) * 0.008)))
        translateY(calc(var(--scroll-shift) * -0.12));
      transition: transform 1.4s var(--ease-soft);
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
      transform:
        translateX(calc(-50% + (var(--pointer-x) * -0.01)))
        translateY(calc(var(--scroll-shift) * 0.18));
      transition: transform 1.6s var(--ease-soft);
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
      transform:
        translateX(calc(-50% + (var(--pointer-x) * 0.016)))
        translateY(calc(var(--scroll-shift) * 0.22));
      transition: transform 1.5s var(--ease-soft);
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
      transition: opacity 1.4s ease, transform 1.8s var(--ease-soft);
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
      transform: translateX(-50%) translateY(-16px) scale(0.94);
      display: flex;
      align-items: center;
      justify-content: center;
      width: min(34vw, 190px);
      opacity: 0;
      transition: opacity 1.45s ease, transform 1.8s var(--ease-luxury), filter 1.4s ease;
      z-index: 2;
      filter: blur(12px);
    }

    .brand-mark img {
      width: 100%;
      height: auto;
      display: block;
      filter:
        drop-shadow(0 10px 28px rgba(255, 190, 90, 0.18))
        drop-shadow(0 2px 8px rgba(255, 255, 255, 0.34));
    }

    body.is-ready .brand-mark {
      opacity: 1;
      transform: translateX(-50%) translateY(0) scale(1);
      filter: blur(0);
    }

    .scene {
      position: relative;
      width: min(82vw, 660px);
      aspect-ratio: 3 / 2;
      display: grid;
      place-items: center;
      perspective: 2200px;
      transform: translateY(calc(var(--scroll-shift) * -0.08));
      transition: transform 0.28s linear;
    }

    .experience::after {
      content: "";
      position: fixed;
      inset: 0;
      background: rgba(255, 250, 242, 0);
      backdrop-filter: blur(0px);
      opacity: 0;
      pointer-events: none;
      z-index: 0;
      transition: opacity 0.9s ease, backdrop-filter 0.9s ease, background 0.9s ease;
    }

    .scene::before {
      content: "";
      position: absolute;
      inset: -3% -4%;
      border-radius: 36px;
      background:
        radial-gradient(circle at 50% 18%, rgba(255, 244, 214, 0.58), rgba(255,255,255,0) 52%),
        linear-gradient(180deg, rgba(255,255,255,0.18), rgba(255,255,255,0));
      filter: blur(16px);
      opacity: 0.82;
      pointer-events: none;
      transition: opacity var(--dur-slow) ease, transform var(--dur-slow) var(--ease-soft);
      transform: scale(0.96);
    }

    .envelope-stage {
      position: absolute;
      inset: 7% 6%;
      z-index: 2;
      pointer-events: none;
      opacity: 0;
      transform: translate3d(0, -116px, -88px) scale(0.86) rotateX(13deg);
      transform-style: preserve-3d;
      transition: opacity 0.95s ease, transform 1.9s var(--ease-luxury), filter 1.5s ease;
      filter: blur(16px);
    }

    .envelope-shadow {
      position: absolute;
      left: 50%;
      bottom: 1.5%;
      width: 76%;
      height: 14%;
      transform: translateX(-50%) scale(0.76);
      border-radius: 999px;
      background: rgba(72, 95, 108, 0.2);
      filter: blur(20px);
      opacity: 0;
      transition: opacity var(--dur-base) ease, transform var(--dur-slow) var(--ease-soft);
    }

    .envelope {
      position: absolute;
      inset: 0;
      overflow: visible;
    }

    .envelope-stage,
    .emerge-card {
      display: none !important;
    }

    .envelope-art,
    .envelope-front-cover {
      position: absolute;
      inset: 0;
      display: grid;
      place-items: center;
      pointer-events: none;
    }

    .envelope-art {
      z-index: 1;
    }

    .envelope-art img,
    .envelope-front-cover img {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: contain;
      filter: drop-shadow(0 28px 40px rgba(44, 6, 10, 0.2));
    }

    .envelope-front-cover {
      z-index: 4;
    }

    .envelope-front-cover.bottom {
      clip-path: polygon(9% 100%, 91% 100%, 80% 62%, 60% 52%, 40% 52%, 20% 62%);
    }

    .envelope-front-cover.left {
      clip-path: polygon(9% 43%, 50% 72%, 50% 52%, 21% 43%);
    }

    .envelope-front-cover.right {
      clip-path: polygon(50% 52%, 50% 72%, 91% 43%, 79% 43%);
    }

    .envelope-liner {
      display: none;
    }

    .envelope-side-fold {
      display: none;
    }

    .envelope-side-fold.left {
      display: none;
    }

    .envelope-side-fold.right {
      display: none;
    }

    .envelope-center-fold {
      display: none;
    }

    .envelope-recipient,
    .envelope-letter,
    .envelope-postcard,
    .envelope-postcard-shine {
      display: none;
    }

    .envelope-flap {
      display: none;
    }

    .envelope-flap::before {
      display: none;
    }

    .envelope-flap::after {
      display: none;
    }

    .envelope-seal {
      display: none;
    }

    .envelope-seal::before {
      display: none;
    }

    .arrival-glow {
      position: absolute;
      inset: -12%;
      z-index: 1;
      opacity: 0;
      background:
        radial-gradient(circle at 50% 52%, rgba(255, 242, 204, 0.58), rgba(255, 224, 163, 0.14) 42%, transparent 68%);
      filter: blur(28px);
      transform: scale(0.84);
      transition: opacity 1.5s ease, transform 2s var(--ease-soft), filter 1.7s ease;
    }

    body.reveal-start .envelope-stage {
      opacity: 1;
      filter: blur(0);
      transform: translate3d(0, 0, 0) scale(1) rotateX(0deg);
    }

    body.reveal-start .arrival-glow {
      opacity: 0.9;
      transform: scale(1.04);
      filter: blur(22px);
    }

    body.reveal-start .envelope-flap {
      transform: rotateX(-158deg);
      filter: blur(0.2px);
    }

    body.reveal-start .envelope-seal {
      opacity: 0;
      transform: translateX(-50%) scale(0.82);
      filter: blur(4px);
    }

    body.reveal-start .envelope-letter {
      opacity: 1;
    }

    body.reveal-start .envelope-postcard {
      transform: translateX(-50%) translateY(-8%) scale(0.94);
    }

    body.reveal-start .envelope-postcard-shine {
      transform: translateX(6%);
    }

    body.reveal-active .envelope-stage {
      opacity: 1;
      filter: blur(0);
      transform: translate3d(0, 0, 0) scale(1) rotateX(0deg);
    }

    body.is-ready .envelope-stage {
      opacity: 0;
      filter: blur(10px);
      transform: translate3d(0, 20px, -24px) scale(0.94);
    }

    .postcard-shell {
      position: absolute;
      inset: 8% 6%;
      aspect-ratio: 3 / 2;
      height: auto;
      z-index: 5;
      opacity: 0;
      filter: blur(10px);
      visibility: visible;
      pointer-events: none;
      transform-origin: center center;
      transform:
        translate3d(0, 30px, 0)
        scale(0.96)
        rotateX(0deg);
      transform-style: preserve-3d;
      transition: opacity 0.55s ease, filter 0.55s ease, transform 0.9s var(--ease-luxury);
    }

    .postcard-shell::before {
      content: "";
      position: absolute;
      inset: -8% -5%;
      border-radius: 40px;
      background:
        radial-gradient(circle at 50% 40%, rgba(255, 244, 214, 0.42), rgba(255,255,255,0.12) 34%, transparent 66%);
      opacity: 0;
      filter: blur(28px);
      transition: opacity 2s ease, transform 2.2s var(--ease-soft);
      pointer-events: none;
      transform: scale(0.88);
    }

    body.reveal-start .postcard-shell {
      opacity: 0;
      filter: blur(10px);
      transform:
        translate3d(0, 30px, 0)
        scale(0.96)
        rotateX(0deg);
    }

    body.delivery-drop .postcard-shell {
      opacity: 0;
      filter: blur(12px);
      transform:
        translate3d(0, 42px, 0)
        scale(0.94)
        rotateX(0deg);
    }

    body.reveal-active .postcard-shell {
      opacity: 1;
      filter: blur(0);
      transform:
        translate3d(0, -8px, 0)
        scale(1.01)
        rotateX(0deg);
    }

    body.reveal-active .postcard-shell::before,
    body.is-ready .postcard-shell::before {
      opacity: 1;
      transform: scale(1);
    }

    body.is-ready .postcard-shell {
      opacity: 1;
      filter: blur(0);
      pointer-events: auto;
      transform: translate3d(0, 0, 0) scale(1) rotateX(0deg);
      z-index: 5;
      animation: postcardFloat 5.8s ease-in-out infinite;
    }

    body.reveal-start .scene::before,
    body.reveal-active .scene::before,
    body.is-ready .scene::before {
      opacity: 1;
      transform: scale(1);
    }

    body.is-ready .experience::after {
      opacity: 0;
      background: rgba(255, 255, 255, 0);
      backdrop-filter: blur(0px);
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

    body.is-ready .card-glow {
      animation: glowPulse 4.8s ease-in-out infinite;
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
      transition: transform 1.45s var(--ease-luxury);
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
      animation: postcardGleam 2.4s var(--ease-luxury) 0.65s forwards;
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
      0% {
        transform: translate3d(0, 0, 0) scale(1);
      }
      50% {
        transform: translate3d(0, -8px, 0) scale(1.003);
      }
      100% {
        transform: translate3d(0, 0, 0) scale(1);
      }
    }

    @keyframes glowPulse {
      0% {
        opacity: 0.72;
        filter: blur(14px);
      }
      50% {
        opacity: 0.88;
        filter: blur(16px);
      }
      100% {
        opacity: 0.72;
        filter: blur(14px);
      }
    }

    .controls {
      position: fixed;
      left: 50%;
      bottom: 18px;
      transform: translateX(-50%) translateY(18px);
      width: min(82vw, 660px);
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 12px;
      opacity: 0;
      filter: blur(10px);
      transition: opacity 1.35s ease, transform 1.45s var(--ease-soft), filter 1.25s ease;
    }

    body.awaiting-open .controls,
    body.is-ready .controls {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
      filter: blur(0);
    }

    body.awaiting-open .actions {
      opacity: 0;
      transform: translateY(8px);
      pointer-events: none;
    }

    body.is-ready .actions {
      opacity: 1;
      transform: translateY(0);
      pointer-events: auto;
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
      transition: transform 0.45s var(--ease-soft), box-shadow 0.45s ease, background 0.45s ease;
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
      transition: opacity 0.6s ease, transform 0.8s var(--ease-soft);
    }

    body.awaiting-open .scene {
      cursor: default;
    }

    .reveal-item {
      opacity: 0;
      filter: blur(14px);
      transform: translate3d(0, 34px, 0) scale(0.982);
      transition:
        opacity var(--dur-base) ease,
        transform var(--dur-slow) var(--ease-luxury),
        filter var(--dur-base) ease;
      transition-delay: calc(var(--reveal-order, 0) * var(--stagger-step));
      will-change: opacity, transform, filter;
    }

    .reveal-item.is-visible {
      opacity: 1;
      filter: blur(0);
      transform: translate3d(0, 0, 0) scale(1);
    }

    .reveal-item.reveal-soft {
      transform: translate3d(0, 18px, 0) scale(0.992);
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
      transition: transform 0.4s var(--ease-soft), background 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease;
    }

    .button:hover {
      transform: translateY(-2px) scale(1.01);
    }

    .button-primary {
      border: 1px solid rgba(255,255,255,0.9);
      background: rgba(255,255,255,0.76);
      color: rgba(47, 80, 93, 0.92);
      box-shadow: 0 16px 34px rgba(133, 176, 192, 0.16);
    }

    .button-secondary {
      border: 1px solid rgba(214, 190, 144, 0.28);
      background: linear-gradient(180deg, rgba(255,255,255,0.52), rgba(255,244,226,0.32));
      color: rgba(97, 101, 96, 0.86);
      box-shadow: 0 10px 22px rgba(201, 170, 103, 0.08);
      backdrop-filter: blur(10px);
    }

    .button-secondary:hover,
    .hint:hover {
      box-shadow: 0 18px 34px rgba(201, 170, 103, 0.14);
    }

    @media (hover: hover) and (pointer: fine) {
      body.is-ready .postcard-shell:hover {
        transform: translate3d(0, 12px, 0) scale(1.64) rotateX(0deg);
      }

      body.is-ready .scene:hover {
        transform: translateY(calc(var(--scroll-shift) * -0.08)) scale(1.003);
      }
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

      .reveal-item,
      .reveal-item.is-visible,
      .brand-mark,
      .controls,
      .scene,
      body::before,
      body::after,
      .sun-glow::before,
      .sun-rays::before,
      .sea-haze::before,
      .sea-shimmer::before {
        transform: none !important;
        filter: none !important;
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
    <div class="brand-mark reveal-item" data-reveal data-reveal-order="0" aria-hidden="true">
      <img src="{{ logo_src }}" alt="Send a Memory">
    </div>
    <section class="scene reveal-item" data-reveal data-reveal-order="1" aria-label="Digital postcard reveal scene">
      <div class="envelope-stage" aria-hidden="true">
        <div class="arrival-glow"></div>
        <div class="envelope-shadow"></div>
        <div class="envelope">
          <div class="envelope-art">
            <img src="./static/bas-envelope.png" alt="Open red envelope">
          </div>
          <div class="envelope-liner"></div>
          <div class="envelope-side-fold left"></div>
          <div class="envelope-side-fold right"></div>
          <div class="envelope-center-fold"></div>
          <div class="envelope-front-cover left">
            <img src="./static/bas-envelope.png" alt="">
          </div>
          <div class="envelope-front-cover right">
            <img src="./static/bas-envelope.png" alt="">
          </div>
          <div class="envelope-front-cover bottom">
            <img src="./static/bas-envelope.png" alt="">
          </div>
          <div class="envelope-letter">
            <div class="envelope-postcard">
              <img src="{{ postcard['front_image_url'] }}" alt="">
            </div>
            <div class="envelope-postcard-shine"></div>
          </div>
          <div class="envelope-flap"></div>
          <div class="envelope-seal"></div>
        </div>
      </div>

      <div class="emerge-card" aria-hidden="true">
        <img src="{{ postcard['front_image_url'] }}" alt="">
      </div>

      <div class="postcard-shell" id="postcardShell">
        <button class="flip-target" id="flipButton" aria-label="Okreni razglednicu">
          <div class="card-glow"></div>

          <div class="postcard" id="postcard">
            <article class="face front">
              <img src="{{ postcard['front_image_url'] }}" alt="Front image">
            </article>

            <article class="face back">
              <img src="{{ postcard['back_image_url'] }}" alt="Back image">
              <div class="message-area" id="messageArea" data-message="{{ postcard['message']|e }}">
                <canvas class="message-canvas" id="messageCanvas"></canvas>
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

    <div class="controls reveal-item reveal-soft" data-reveal data-reveal-order="2">
      <button class="hint reveal-item reveal-soft" data-reveal data-reveal-order="3" id="flipHint" type="button">Tap the envelope to open</button>
      <div class="actions reveal-item reveal-soft" data-reveal data-reveal-order="4">
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
    const messageCanvas = document.getElementById('messageCanvas');
    const messageLines = document.getElementById('messageLines');
    const scene = document.querySelector('.scene');
    const revealItems = Array.from(document.querySelectorAll('[data-reveal]'));
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    let introTimers = [];
    let flipped = false;
    let audioContext;
    let noiseBuffer;
    let wavesNodes;
    let revealObserver;
    let pointerFrame = 0;
    let scrollFrame = 0;
    let revealStarted = false;
    let revealFinished = false;

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

    function setupRevealItems() {
      revealItems.forEach((item, index) => {
        if (!item.style.getPropertyValue('--reveal-order')) {
          item.style.setProperty('--reveal-order', item.dataset.revealOrder || index);
        }
      });
    }

    function revealVisibleItems() {
      revealItems.forEach((item) => item.classList.add('is-visible'));
    }

    function setupScrollReveal() {
      if (prefersReducedMotion || !('IntersectionObserver' in window)) {
        revealVisibleItems();
        return;
      }

      revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          revealObserver.unobserve(entry.target);
        });
      }, {
        threshold: 0.16,
        rootMargin: '0px 0px -8% 0px'
      });

      revealItems.forEach((item) => revealObserver.observe(item));
    }

    function updateScrollDepth() {
      if (prefersReducedMotion) return;
      if (scrollFrame) return;
      scrollFrame = window.requestAnimationFrame(() => {
        const scrollTop = window.scrollY || window.pageYOffset || 0;
        document.documentElement.style.setProperty('--scroll-shift', `${Math.min(scrollTop, 220)}px`);
        scrollFrame = 0;
      });
    }

    function updatePointerDepth(event) {
      if (prefersReducedMotion) return;
      if (pointerFrame) return;
      pointerFrame = window.requestAnimationFrame(() => {
        const x = ((event.clientX / window.innerWidth) - 0.5) * 32;
        const y = ((event.clientY / window.innerHeight) - 0.5) * 24;
        document.documentElement.style.setProperty('--pointer-x', `${x.toFixed(2)}px`);
        document.documentElement.style.setProperty('--pointer-y', `${y.toFixed(2)}px`);
        pointerFrame = 0;
      });
    }

    function updateHintText() {
      if (!flipHint) return;
      if (!revealStarted) {
        flipHint.textContent = 'Tap postcard to flip';
        return;
      }
      flipHint.textContent = flipped ? 'Tap to turn it back' : 'Tap to flip';
    }

    function setFlipState(nextState) {
      flipped = nextState;
      postcard.classList.toggle('flipped', flipped);
      updateHintText();
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

    function renderMessageCanvas() {
      if (!messageArea || !messageCanvas) return;

      const text = (messageArea.dataset.message || '').replace(/\s+/g, ' ').trim();
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

      const horizontalPadding = width * 0.015;
      const maxWidth = width - (horizontalPadding * 2);
      const minFont = 8;
      let fontSize = Math.min(18, height * 0.24);
      let lineHeight = fontSize * 1.52;
      let lines = [text];

      while (fontSize >= minFont) {
        ctx.font = `500 ${fontSize}px Cinzel, Georgia, serif`;
        lines = wrapCanvasLines(ctx, text, maxWidth);
        lineHeight = fontSize * 1.52;
        const totalHeight = lines.length * lineHeight;
        const widestLine = lines.reduce((max, line) => Math.max(max, ctx.measureText(line).width), 0);

        if (totalHeight <= height && widestLine <= maxWidth) {
          break;
        }

        fontSize -= 0.5;
      }

      ctx.font = `500 ${Math.max(fontSize, minFont)}px Cinzel, Georgia, serif`;
      ctx.fillStyle = 'rgba(106, 76, 49, 0.9)';
      ctx.textBaseline = 'top';
      ctx.textAlign = 'left';

      const totalHeight = lines.length * lineHeight;
      let y = Math.max(0, (height - totalHeight) / 2);

      lines.forEach((line) => {
        ctx.fillText(line, horizontalPadding, y);
        y += lineHeight;
      });
    }

    function runReveal() {
      clearIntroTimers();
      revealStarted = true;
      revealFinished = false;
      setFlipState(false);
      body.classList.remove('awaiting-open', 'reveal-start', 'reveal-active', 'is-ready');

      introTimers.push(window.setTimeout(() => {
        body.classList.add('reveal-start');
      }, 40));

      introTimers.push(window.setTimeout(() => {
        body.classList.add('reveal-active');
      }, 820));

      introTimers.push(window.setTimeout(() => {
        body.classList.remove('reveal-start', 'reveal-active');
        body.classList.add('is-ready');
        revealFinished = true;
        updateHintText();
      }, 1680));
    }

    function openEnvelope(event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      if (revealStarted) return;
      runReveal();
    }

    function toggleFlip() {
      if (!revealStarted) {
        return;
      }
      if (!revealFinished) {
        return;
      }
      warmAudio();
      setFlipState(!flipped);
    }

    flipButton.addEventListener('click', toggleFlip);
    replayButton.addEventListener('click', runReveal);
    flipHint.addEventListener('click', toggleFlip);
    window.addEventListener('pointerdown', warmAudio, { passive: true });
    window.addEventListener('keydown', warmAudio);
    window.addEventListener('scroll', updateScrollDepth, { passive: true });
    window.addEventListener('pointermove', updatePointerDepth, { passive: true });
    window.addEventListener('load', () => {
      setupRevealItems();
      setupScrollReveal();
      const fontReady = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
      fontReady.then(() => {
        renderMessageCanvas();
      });
      warmAudio();
      updateScrollDepth();
      revealVisibleItems();
      runReveal();
      updateHintText();
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
      --panel: rgba(255, 252, 247, 0.92);
      --line: rgba(137, 108, 70, 0.16);
      --ink: #2d2a26;
      --muted: #7c6e61;
      --accent: #b54a3f;
      --shadow: 0 24px 60px rgba(64, 45, 21, 0.1);
      --radius: 26px;
    }

    * {
      box-sizing: border-box;
    }

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

    .body {
      padding: 16px;
    }

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
      background: linear-gradient(180deg, #c85c50 0%, #a84339 100%);
      color: white;
    }

    .button-secondary {
      border: 1px solid rgba(168, 67, 57, 0.18);
      color: #7a3f38;
      background: rgba(255,255,255,0.7);
    }

    .empty {
      padding: 28px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--panel);
      color: var(--muted);
      box-shadow: var(--shadow);
    }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <h1>Postcard Previews</h1>
      <p>Ovdje vidiš sve generirane razglednice i možeš odmah otvoriti svaki link.</p>
      <div class="meta">Ukupno: {{ postcards|length }}</div>
    </section>

    {% if postcards %}
      <section class="grid">
        {% for postcard in postcards %}
          <article class="card">
            <a class="thumb" href="{{ base_url }}/p/{{ postcard['slug'] }}" target="_blank" rel="noopener noreferrer">
              <img src="{{ postcard['front_image_url'] }}" alt="{{ postcard['product_title'] }}">
            </a>
            <div class="body">
              <h2 class="title">{{ postcard['product_title'] }}</h2>
              <div class="info">
                <div>Order: {{ postcard['order_name'] or postcard['order_id'] or '-' }}</div>
                <div>Recipient: {{ postcard['recipient_name'] or '-' }}</div>
                <div>Created: {{ postcard['created_at'] }}</div>
              </div>
              <div class="slug">{{ base_url }}/p/{{ postcard['slug'] }}</div>
              <div class="actions">
                <a class="button button-primary" href="{{ base_url }}/p/{{ postcard['slug'] }}" target="_blank" rel="noopener noreferrer">Open</a>
                <a class="button button-secondary" href="{{ base_url }}/api/postcard-by-order/{{ postcard['order_id'] }}" target="_blank" rel="noopener noreferrer">Order API</a>
              </div>
            </div>
          </article>
        {% endfor %}
      </section>
    {% else %}
      <section class="empty">Nema generiranih razglednica.</section>
    {% endif %}
  </main>
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
            recipient_name TEXT DEFAULT '',
            message TEXT NOT NULL,
            front_image_url TEXT NOT NULL,
            back_image_url TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(postcards)").fetchall()
    }
    if "recipient_name" not in columns:
        conn.execute("ALTER TABLE postcards ADD COLUMN recipient_name TEXT DEFAULT ''")
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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_slug() -> str:
    return secrets.token_urlsafe(6)


def get_template_for_product(product_title: str):
    return TEMPLATES.get(product_title)


def get_logo_src() -> str:
    logo_path = os.path.join(app.root_path, "static", "send-a-memory-logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as logo_file:
            encoded = base64.b64encode(logo_file.read()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    return f"{request.host_url.rstrip('/')}/static/send-a-memory-logo.png"


def extract_recipient_name(properties):
    candidate_names = {
        "Recipient Name",
        "Recipient",
        "To",
        "For",
        "Name",
        "Recipient name",
        "recipient_name",
    }

    for prop in properties or []:
        prop_name = str(prop.get("name", "")).strip()
        prop_value = str(prop.get("value", "")).strip()
        if prop_name in candidate_names and prop_value:
            return prop_value[:80]

    return ""


def extract_postcard_details(payload):
    order_id = str(payload.get("id", "")).strip()
    order_name = str(payload.get("name", "")).strip()

    for item in payload.get("line_items", []):
        product_title = str(item.get("title", "")).strip()
        properties = item.get("properties", [])
        recipient_name = extract_recipient_name(properties)
        for prop in properties:
            prop_name = str(prop.get("name", "")).strip()
            prop_value = str(prop.get("value", "")).strip()
            if prop_name == "Postcard Message" and prop_value:
                return {
                    "order_id": order_id,
                    "order_name": order_name,
                    "product_title": product_title,
                    "recipient_name": recipient_name,
                    "message": prop_value,
                }

    return {
        "order_id": order_id,
        "order_name": order_name,
        "product_title": "",
        "recipient_name": "",
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
            recipient_name,
            message,
            front_image_url,
            back_image_url,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            details["order_id"],
            details["order_name"],
            slug,
            details["product_title"],
            details.get("recipient_name", ""),
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


@app.route("/webhooks/orders-paid", methods=["POST"])
def shopify_orders_paid():
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
    return render_template_string(
        VIEW_HTML,
        postcard=postcard,
        message_lines=message_lines,
        logo_src=get_logo_src(),
    )


@app.route("/previews")
def previews():
    db = get_db()
    postcards = db.execute(
        """
        SELECT id, order_id, order_name, slug, product_title, recipient_name, front_image_url, created_at
        FROM postcards
        ORDER BY id DESC
        """
    ).fetchall()
    return render_template_string(
        PREVIEWS_HTML,
        postcards=postcards,
        base_url=request.host_url.rstrip("/"),
    )


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
