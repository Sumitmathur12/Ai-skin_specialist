import os
from pathlib import Path

import gradio as gr

#from brain_of_the_doctor import brain_of_the_doctor
from brain_of_the_doctor_groq import brain_of_the_doctor
from voice_of_the_doctor import convert_text_to_doctor_audio
from voice_of_the_patient import transcribe_patient_voice


APP_TITLE = "AI Skin Specialist"

HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,450;9..144,560;9..144,650&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
"""

CSS = """
/* ------------------------------------------------------------------ *
 *  Token system — "clinical hologram"                                *
 *  A dermatoscope readout floating in a dark exam-room glass panel.  *
 *  Deep space-teal field, frosted glass cards with real depth        *
 *  (perspective + rotateX/Y on hover), a spinning scan-ring, and a   *
 *  clay/coral glow reserved for the one primary action.              *
 * ------------------------------------------------------------------ */
:root {
    --ais-void: #050c0b;
    --ais-bg: #081615;
    --ais-surface: rgba(255, 255, 255, 0.045);
    --ais-surface-strong: rgba(255, 255, 255, 0.07);
    --ais-surface-low: rgba(255, 255, 255, 0.035);
    --ais-border: rgba(220, 240, 235, 0.14);
    --ais-border-strong: rgba(220, 240, 235, 0.28);
    --ais-ink: #eef6f3;
    --ais-muted: #9fb6ae;

    --ais-teal-glow: #2fe0c4;
    --ais-teal-700: #0f3d37;
    --ais-teal-600: #146258;
    --ais-teal-500: #1c8577;
    --ais-teal-soft: rgba(47, 224, 196, 0.16);

    --ais-clay: #ff8a5c;
    --ais-clay-dark: #e8663a;
    --ais-clay-soft: rgba(255, 138, 92, 0.18);

    --ais-primary: var(--ais-teal-600);
    --ais-primary-active: var(--ais-teal-500);
    --ais-danger: #ff7a68;
    --ais-radius: 22px;

    --font-display: "Fraunces", "Iowan Old Style", serif;
    --font-body: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    --font-mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;

    --body-background-fill: #081615;
    --body-text-color: #eef6f3;
    --background-fill-primary: rgba(255, 255, 255, 0.045);
    --background-fill-secondary: rgba(255, 255, 255, 0.035);
    --block-background-fill: rgba(255, 255, 255, 0.045);
    --block-border-color: rgba(220, 240, 235, 0.14);
    --block-info-text-color: #9fb6ae;
    --block-label-background-fill: transparent;
    --block-label-border-color: rgba(220, 240, 235, 0.14);
    --block-label-text-color: #9fb6ae;
    --input-background-fill: rgba(255, 255, 255, 0.05);
    --input-background-fill-focus: rgba(255, 255, 255, 0.07);
    --input-border-color: rgba(220, 240, 235, 0.16);
    --input-border-color-focus: #2fe0c4;
    --input-placeholder-color: #6d8b83;
    --button-primary-background-fill: #146258;
    --button-primary-background-fill-hover: #1c8577;
    --button-primary-text-color: #eef6f3;
    color-scheme: dark;
}

@media (prefers-reduced-motion: reduce) {
    * { animation-duration: 0.001ms !important; animation-iteration-count: 1 !important; transition-duration: 0.001ms !important; }
}

body, .gradio-container {
    background: var(--ais-void) !important;
}

.gradio-container {
    position: relative;
    color: var(--ais-ink) !important;
    font-family: var(--font-body) !important;
    overflow-x: hidden;
    background:
        radial-gradient(900px 560px at 88% -6%, rgba(255, 138, 92, 0.14), transparent 60%),
        radial-gradient(1000px 700px at 6% 8%, rgba(47, 224, 196, 0.14), transparent 55%),
        radial-gradient(1200px 900px at 50% 110%, rgba(20, 98, 88, 0.28), transparent 60%),
        linear-gradient(180deg, #050c0b 0%, #081615 45%, #06110f 100%) !important;
}

.gradio-container,
.gradio-container * {
    color-scheme: dark !important;
}

/* faint schematic grid, like a scanner overlay */
.gradio-container::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(220, 240, 235, 0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(220, 240, 235, 0.035) 1px, transparent 1px);
    background-size: 42px 42px;
    -webkit-mask-image: radial-gradient(1100px 700px at 50% 0%, #000 20%, transparent 75%);
    mask-image: radial-gradient(1100px 700px at 50% 0%, #000 20%, transparent 75%);
    pointer-events: none;
    z-index: 0;
}

.ais-orb {
    position: fixed;
    border-radius: 50%;
    filter: blur(90px);
    pointer-events: none;
    z-index: 0;
    opacity: 0.55;
}

.ais-orb-1 { width: 380px; height: 380px; top: -120px; right: 6%; background: radial-gradient(circle, rgba(47,224,196,0.5), transparent 70%); animation: ais-float 12s ease-in-out infinite; }
.ais-orb-2 { width: 320px; height: 320px; bottom: -140px; left: 4%; background: radial-gradient(circle, rgba(255,138,92,0.4), transparent 70%); animation: ais-float 14s ease-in-out infinite reverse; }

@keyframes ais-float {
    0%, 100% { transform: translate3d(0, 0, 0); }
    50% { transform: translate3d(0, 26px, 0); }
}

.ais-shell {
    position: relative;
    z-index: 1;
    max-width: 1280px;
    margin: 0 auto;
    padding: 32px 40px 48px;
}

/* ---------------- Header / hero band ---------------- */

.ais-topbar {
    position: relative;
    align-items: center;
    background: linear-gradient(155deg, rgba(20, 98, 88, 0.55) 0%, rgba(8, 22, 21, 0.65) 60%, rgba(232, 102, 58, 0.14) 130%);
    backdrop-filter: blur(22px) saturate(140%);
    -webkit-backdrop-filter: blur(22px) saturate(140%);
    border: 1px solid var(--ais-border-strong);
    border-radius: 26px;
    display: flex;
    justify-content: space-between;
    margin-bottom: 28px;
    padding: 32px 38px;
    overflow: hidden;
    box-shadow:
        0 30px 70px -24px rgba(0, 0, 0, 0.7),
        inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.ais-topbar::before {
    content: "";
    position: absolute;
    width: 420px;
    height: 420px;
    right: -160px;
    top: -220px;
    border-radius: 50%;
    border: 1px solid rgba(47, 224, 196, 0.22);
    pointer-events: none;
}

.ais-topbar::after {
    content: "";
    position: absolute;
    width: 260px;
    height: 260px;
    right: -50px;
    top: -90px;
    border-radius: 50%;
    border: 1px solid rgba(255, 138, 92, 0.35);
    pointer-events: none;
}

.ais-eyebrow {
    color: var(--ais-teal-glow);
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin: 0 0 10px;
    position: relative;
    z-index: 1;
    text-shadow: 0 0 18px rgba(47, 224, 196, 0.5);
}

.ais-brand { position: relative; z-index: 1; }

.ais-brand h1 {
    background: linear-gradient(120deg, #ffffff 10%, #bdeee2 55%, #ffcbb0 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    font-family: var(--font-display);
    font-size: 36px;
    font-weight: 560;
    font-optical-sizing: auto;
    letter-spacing: -0.01em;
    line-height: 1.15;
    margin: 0;
    filter: drop-shadow(0 0 22px rgba(47, 224, 196, 0.16));
}

.ais-brand p {
    color: rgba(238, 246, 243, 0.62);
    font-family: var(--font-mono);
    font-size: 11.5px;
    font-weight: 500;
    letter-spacing: 0.1em;
    line-height: 16px;
    margin: 12px 0 0;
    text-transform: uppercase;
}

.ais-security {
    position: relative;
    z-index: 1;
    align-items: center;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--ais-border-strong);
    border-radius: 999px;
    color: var(--ais-ink);
    display: flex;
    font-family: var(--font-mono);
    font-size: 11.5px;
    font-weight: 500;
    letter-spacing: 0.04em;
    gap: 8px;
    padding: 10px 18px;
    white-space: nowrap;
    box-shadow: 0 10px 26px -14px rgba(47, 224, 196, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.ais-security .ais-icon { color: var(--ais-clay); font-size: 18px; }

.ais-inline-note .ais-security { background: none; border: 0; box-shadow: none; padding: 0; }

/* ---------------- Section headings ---------------- */

.ais-grid {
    align-items: start;
    display: grid;
    gap: 26px;
    grid-template-columns: minmax(0, 5fr) minmax(0, 7fr);
    perspective: 1800px;
}

.ais-section-title { display: flex; flex-direction: column; gap: 3px; margin: 4px 0 16px; }

.ais-section-title .ais-eyebrow { color: var(--ais-clay); text-shadow: 0 0 16px rgba(255, 138, 92, 0.35); }

.ais-section-title h2 {
    align-items: center;
    color: var(--ais-ink);
    display: flex;
    font-family: var(--font-display);
    font-size: 26px;
    font-weight: 500;
    gap: 10px;
    line-height: 1.2;
    margin: 0;
}

.ais-section-title .ais-icon { color: var(--ais-teal-glow); font-size: 22px; filter: drop-shadow(0 0 8px rgba(47, 224, 196, 0.6)); }

/* ---------------- Glass cards with real 3D tilt ---------------- */

.ais-card {
    background: linear-gradient(165deg, var(--ais-surface-strong), var(--ais-surface-low));
    backdrop-filter: blur(20px) saturate(150%);
    -webkit-backdrop-filter: blur(20px) saturate(150%);
    border: 1px solid var(--ais-border);
    border-radius: var(--ais-radius);
    box-shadow:
        0 24px 60px -28px rgba(0, 0, 0, 0.75),
        inset 0 1px 0 rgba(255, 255, 255, 0.08);
    padding: 24px;
    position: relative;
    transform-style: preserve-3d;
    transition: transform 0.5s cubic-bezier(.2,.8,.2,1), box-shadow 0.5s ease, border-color 0.5s ease;
    will-change: transform;
}

.ais-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 24px;
    right: 24px;
    height: 2px;
    border-radius: 0 0 4px 4px;
    background: linear-gradient(90deg, var(--ais-teal-glow), var(--ais-clay) 130%);
    box-shadow: 0 0 16px rgba(47, 224, 196, 0.55);
    opacity: 0.9;
    transform: translateZ(1px);
}

.ais-card:hover {
    transform: rotateX(2.5deg) rotateY(-2deg) translateY(-6px) translateZ(8px);
    border-color: rgba(47, 224, 196, 0.4);
    box-shadow:
        0 34px 80px -26px rgba(0, 0, 0, 0.8),
        0 0 40px -10px rgba(47, 224, 196, 0.18),
        inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.ais-input-card { display: flex; flex-direction: column; gap: 18px; }

.ais-field-label {
    align-items: center;
    color: var(--ais-teal-glow);
    display: flex;
    gap: 8px;
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 2px;
}

.ais-field-label .ais-icon { font-size: 17px; color: var(--ais-clay); }

.ais-media-row { display: grid; gap: 16px; grid-template-columns: repeat(2, minmax(0, 1fr)); }

/* ---------------- 3D bevelled analyze button ---------------- */

.ais-submit-wrap { position: relative; }

.ais-submit-wrap .gr-button-primary {
    background: linear-gradient(160deg, #1fa190 0%, #146258 60%, #0f3d37 100%) !important;
    border: 1px solid rgba(47, 224, 196, 0.5) !important;
    border-radius: 18px !important;
    box-shadow:
        0 16px 30px -10px rgba(20, 98, 88, 0.6),
        0 0 30px -6px rgba(47, 224, 196, 0.35),
        inset 0 1px 0 rgba(255, 255, 255, 0.35),
        inset 0 -3px 8px rgba(0, 0, 0, 0.35) !important;
    color: #f4fffb !important;
    font-family: var(--font-body) !important;
    font-size: 17px !important;
    font-weight: 650 !important;
    letter-spacing: 0.01em;
    min-height: 62px !important;
    position: relative;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.25s ease !important;
}

.ais-submit-wrap .gr-button-primary:hover {
    background: linear-gradient(160deg, #2fe0c4 0%, #1c8577 55%, #ff8a5c 140%) !important;
    transform: translateY(-3px);
    box-shadow:
        0 22px 40px -10px rgba(20, 98, 88, 0.7),
        0 0 46px -4px rgba(255, 138, 92, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.4),
        inset 0 -3px 8px rgba(0, 0, 0, 0.3) !important;
}

.ais-submit-wrap .gr-button-primary:active {
    transform: translateY(1px);
    box-shadow:
        0 8px 16px -6px rgba(20, 98, 88, 0.6),
        inset 0 2px 6px rgba(0, 0, 0, 0.4) !important;
}

.ais-submit-wrap .gr-button-primary:focus-visible {
    outline: 2px solid var(--ais-clay) !important;
    outline-offset: 3px;
}

/* ---------------- Info note ---------------- */

.ais-note {
    align-items: flex-start;
    background: var(--ais-clay-soft);
    border: 1px solid rgba(255, 138, 92, 0.35);
    border-radius: 16px;
    color: #ffd9c4;
    display: flex;
    gap: 10px;
    padding: 15px 17px;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.ais-note span:not(.ais-icon) { color: #ffd9c4 !important; font-size: 13.5px; line-height: 20px; font-weight: 500 !important; }
.ais-note .ais-icon { color: var(--ais-clay) !important; flex-shrink: 0; filter: drop-shadow(0 0 6px rgba(255, 138, 92, 0.6)); }

/* ---------------- Response panel + spinning scan-ring ---------------- */

.ais-response-card { min-height: 590px; }

.ais-empty {
    align-items: center;
    color: var(--ais-muted);
    display: flex;
    flex-direction: column;
    gap: 20px;
    justify-content: center;
    min-height: 190px;
    text-align: center;
}

.ais-scan {
    position: relative;
    width: 108px;
    height: 108px;
    display: flex;
    align-items: center;
    justify-content: center;
    transform: translateZ(24px);
}

.ais-scan::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background: conic-gradient(from 0deg, var(--ais-teal-glow), var(--ais-clay), transparent 45%, transparent 55%, var(--ais-teal-glow));
    -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 2.5px), #000 calc(100% - 2.5px));
    mask: radial-gradient(farthest-side, transparent calc(100% - 2.5px), #000 calc(100% - 2.5px));
    animation: ais-spin 3.2s linear infinite;
    filter: drop-shadow(0 0 10px rgba(47, 224, 196, 0.5));
}

.ais-scan::after {
    content: "";
    position: absolute;
    inset: 16px;
    border-radius: 50%;
    border: 1px solid var(--ais-border);
    animation: ais-pulse 2.6s ease-out infinite;
}

.ais-scan .ais-icon {
    position: relative;
    z-index: 1;
    align-items: center;
    background: linear-gradient(160deg, #1fa190, #0f3d37);
    border: 1px solid rgba(47, 224, 196, 0.5);
    border-radius: 999px;
    color: #f4fffb;
    display: inline-flex;
    font-size: 30px;
    height: 60px;
    justify-content: center;
    width: 60px;
    box-shadow: 0 12px 24px -8px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.25);
}

@keyframes ais-spin { to { transform: rotate(360deg); } }

@keyframes ais-pulse {
    0% { transform: scale(0.75); opacity: 0.8; }
    75% { transform: scale(1.6); opacity: 0; }
    100% { transform: scale(1.6); opacity: 0; }
}

.ais-empty strong {
    color: var(--ais-ink) !important;
    display: block;
    font-family: var(--font-display);
    font-size: 20px;
    font-weight: 550;
    line-height: 1.3;
    margin-bottom: 6px;
}

.ais-panel-copy { color: var(--ais-muted) !important; font-size: 13.5px; line-height: 20px; margin: 0; max-width: 320px; }

.ais-output-stack { display: flex; flex-direction: column; gap: 18px; }

.ais-output-stack .gradio-textbox textarea {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid var(--ais-border) !important;
    color: var(--ais-ink) !important;
    font-size: 15.5px !important;
    line-height: 24px !important;
    border-radius: 14px !important;
}

.ais-transcript textarea {
    color: var(--ais-muted) !important;
    font-family: var(--font-mono) !important;
    font-size: 13.5px !important;
    font-style: normal;
}

.ais-audio { border-top: 1px dashed var(--ais-border-strong); padding-top: 18px; }

/* ---------------- Footer ---------------- */

.ais-footer {
    align-items: center;
    background: linear-gradient(165deg, var(--ais-surface-strong), var(--ais-surface-low));
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--ais-border);
    border-radius: 20px;
    display: flex;
    justify-content: space-between;
    margin-top: 30px;
    padding: 18px 26px;
    font-size: 13px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
}

.ais-footer strong { color: var(--ais-ink); font-family: var(--font-display); font-size: 15.5px; font-weight: 550; }
.ais-footer div:first-child { color: var(--ais-muted); line-height: 20px; }
.ais-footer div:last-child { color: var(--ais-border-strong); font-family: var(--font-mono); font-size: 11.5px; letter-spacing: 0.03em; text-transform: uppercase; }

.ais-inline-note { justify-content: center; margin-top: 16px; display: flex; }
.ais-inline-note span { color: var(--ais-muted); font-family: var(--font-mono); font-size: 11.5px; letter-spacing: 0.04em; text-transform: uppercase; }
.ais-inline-note .ais-icon { color: var(--ais-teal-glow); font-size: 17px; margin-right: 8px; }

/* ---------------- Icon base ---------------- */

.ais-icon { font-family: 'Material Symbols Outlined'; font-variation-settings: 'FILL' 0, 'wght' 450, 'GRAD' 0, 'opsz' 24; line-height: 1; }

/* ---------------- Gradio component skinning (dark glass) ---------------- */

.ais-card .gr-form, .ais-card .form { background: transparent !important; border: 0 !important; box-shadow: none !important; gap: 0 !important; }

.ais-card [data-testid="block-label"],
.ais-card div[class*="block-label"],
.ais-card label[class*="container"] {
    background: transparent !important;
    border-color: transparent !important;
    color: var(--ais-muted) !important;
}

.ais-card [data-testid="block-label"] *,
.ais-card div[class*="block-label"] *,
.ais-card label[class*="container"] * { color: var(--ais-muted) !important; }

.ais-card label span, .ais-output-stack label span {
    color: var(--ais-teal-glow) !important;
    font-family: var(--font-mono) !important;
    font-size: 11.5px !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}

.ais-card input, .ais-card textarea, .ais-card select,
.ais-card .upload-container, .ais-card .file-preview, .ais-card .input-container,
.ais-card .dropzone, .ais-card .empty, .ais-card .icon-wrap, .ais-card video, .ais-card img {
    background: rgba(255, 255, 255, 0.045) !important;
    border-color: var(--ais-border) !important;
    color: var(--ais-ink) !important;
    border-radius: 16px !important;
}

.ais-card .upload-container, .ais-card .dropzone {
    border: 1.5px dashed var(--ais-border-strong) !important;
    transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}

.ais-card .upload-container:hover, .ais-card .dropzone:hover {
    border-color: var(--ais-clay) !important;
    background: rgba(255, 138, 92, 0.07) !important;
    box-shadow: 0 0 24px -8px rgba(255, 138, 92, 0.4) !important;
}

.ais-card input:disabled, .ais-card textarea:disabled, .ais-card [aria-disabled="true"], .ais-card .disabled {
    background: rgba(255, 255, 255, 0.045) !important;
    color: var(--ais-ink) !important;
    opacity: 1 !important;
    -webkit-text-fill-color: var(--ais-ink) !important;
}

.ais-card .gradio-audio button, .ais-card .gradio-image button, .ais-card .gradio-video button, .ais-card .gradio-textbox button {
    color: var(--ais-teal-glow) !important;
}

.ais-card .upload-container, .ais-card .dropzone { min-height: 220px !important; }
.ais-card .gradio-audio .upload-container, .ais-card .gradio-audio .dropzone { min-height: 120px !important; }

.ais-media-row .gradio-image, .ais-media-row .gradio-video,
.ais-media-row .gradio-image > div, .ais-media-row .gradio-video > div,
.ais-media-row .gradio-image [class*="container"], .ais-media-row .gradio-video [class*="container"],
.ais-media-row .gradio-image [class*="wrap"], .ais-media-row .gradio-video [class*="wrap"] {
    min-height: 280px !important;
    overflow: visible !important;
}

.ais-media-row .gradio-image .upload-container, .ais-media-row .gradio-video .upload-container,
.ais-media-row .gradio-image .dropzone, .ais-media-row .gradio-video .dropzone {
    height: 210px !important;
    min-height: 210px !important;
}

.ais-media-row .gradio-image button, .ais-media-row .gradio-video button { min-height: 36px !important; }

.ais-card .upload-container *, .ais-card .file-preview *, .ais-card .input-container *, .ais-card .dropzone *, .ais-card .empty * {
    color: var(--ais-ink) !important;
}

.ais-card ::placeholder { color: #6d8b83 !important; }

@media (max-width: 900px) {
    .ais-shell { padding: 20px; }
    .ais-topbar { padding: 24px; }
    .ais-topbar, .ais-footer { align-items: flex-start; flex-direction: column; gap: 14px; }
    .ais-grid, .ais-media-row { grid-template-columns: 1fr; perspective: none; }
    .ais-card:hover { transform: none; }
    .ais-brand h1 { font-size: 27px; }
    .ais-section-title h2 { font-size: 21px; }
}
"""


def process_inputs(audio_filepath, image_filepath, video_filepath):
    if not audio_filepath or not os.path.exists(audio_filepath) or os.path.getsize(audio_filepath) == 0:
        raise gr.Error("Please record or upload your voice description first.")

    if not image_filepath and not video_filepath:
        raise gr.Error("Please upload a skin image or video before analysis.")

    if not image_filepath:
        raise gr.Error("Please upload a skin image for analysis (vision analysis requires an image).")

    try:
        patient_text = transcribe_patient_voice(audio_filepath)
    except Exception as e:
        raise gr.Error(f"Speech transcription failed: {e}")

    try:
        doctor_text = brain_of_the_doctor(
            patient_text=patient_text,
            image_filepath=image_filepath,
            video_filepath=video_filepath,
        )
    except Exception as e:
        raise gr.Error(f"Doctor analysis failed: {e}")

    try:
        doctor_audio = convert_text_to_doctor_audio(doctor_text)
    except Exception as e:
        raise gr.Error(f"Voice synthesis failed: {e}")

    return patient_text, doctor_text, str(Path(doctor_audio).resolve())


with gr.Blocks(title=APP_TITLE, head=HEAD) as iface:
    gr.HTML('<div class="ais-orb ais-orb-1"></div><div class="ais-orb ais-orb-2"></div>')

    with gr.Column(elem_classes="ais-shell"):
        gr.HTML(
            """
            <header class="ais-topbar">
                <div class="ais-brand">
                    <p class="ais-eyebrow">Dermatology · Assisted by AI</p>
                    <h1>AI Skin Specialist</h1>
                    <p>Voice, image &amp; video based skin consultation</p>
                </div>
                <div class="ais-security">
                    <span class="ais-icon">shield_person</span>
                    <span>Privacy-first consultation</span>
                </div>
            </header>
            """
        )

        with gr.Row(elem_classes="ais-grid"):
            with gr.Column(scale=5):
                gr.HTML(
                    """
                    <div class="ais-section-title">
                        <p class="ais-eyebrow">01 · Patient</p>
                        <h2><span class="ais-icon">clinical_notes</span>Patient Input</h2>
                    </div>
                    """
                )

                with gr.Column(elem_classes="ais-card ais-input-card"):
                    gr.HTML(
                        '<span class="ais-field-label">'
                        '<span class="ais-icon">graphic_eq</span>Describe your skin concern</span>'
                    )
                    audio_input = gr.Audio(
                        sources=["microphone", "upload"],
                        type="filepath",
                        label="Patient Voice",
                    )

                    with gr.Row(elem_classes="ais-media-row"):
                        image_input = gr.Image(
                            type="filepath",
                            label="Skin Image",
                            height=280,
                        )
                        video_input = gr.Video(label="Skin Video", height=280)

                    with gr.Column(elem_classes="ais-submit-wrap"):
                        analyze_button = gr.Button(
                            "Analyze Concern",
                            variant="primary",
                            size="lg",
                        )

                    gr.HTML(
                        """
                        <div class="ais-note">
                            <span class="ais-icon">tips_and_updates</span>
                            <span>For better assessment, include a short video showing the affected area from multiple angles and under good lighting.</span>
                        </div>
                        """
                    )

            with gr.Column(scale=7):
                gr.HTML(
                    """
                    <div class="ais-section-title">
                        <p class="ais-eyebrow">02 · Specialist</p>
                        <h2><span class="ais-icon">stethoscope</span>Doctor Response</h2>
                    </div>
                    """
                )

                with gr.Column(elem_classes="ais-card ais-response-card"):
                    gr.HTML(
                        """
                        <div class="ais-empty">
                            <div class="ais-scan">
                                <span class="ais-icon">search</span>
                            </div>
                            <div>
                                <strong>Ready for analysis</strong>
                                <p class="ais-panel-copy">Your consultation summary, transcript, and guidance will appear here once analysis completes.</p>
                            </div>
                        </div>
                        """
                    )

                    with gr.Column(elem_classes="ais-output-stack"):
                        transcript_output = gr.Textbox(
                            label="Your Speech Transcript",
                            lines=4,
                            interactive=False,
                            elem_classes="ais-transcript",
                        )
                        response_output = gr.Textbox(
                            label="Doctor's Guidance",
                            lines=9,
                            interactive=False,
                        )
                        audio_output = gr.Audio(
                            label="Doctor Voice Response",
                            type="filepath",
                            autoplay=True,
                            elem_classes="ais-audio",
                        )

                gr.HTML(
                    """
                    <div class="ais-inline-note">
                        <span class="ais-icon">verified</span>
                        <span>AI guidance is informational and not a medical diagnosis</span>
                    </div>
                    """
                )

        gr.HTML(
            """
            <footer class="ais-footer">
                <div><strong>AI Skin Specialist</strong><br/>Consult a licensed dermatologist for urgent or serious symptoms.</div>
                <div>Privacy Policy · Terms of Service · Medical Disclaimer</div>
            </footer>
            """
        )

    analyze_button.click(
        fn=process_inputs,
        inputs=[audio_input, image_input, video_input],
        outputs=[transcript_output, response_output, audio_output],
    )


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "doctor_audio_cache"
    cache_dir.mkdir(exist_ok=True)
    iface.launch(debug=True, css=CSS, theme=gr.themes.Base(), allowed_paths=[str(cache_dir)])