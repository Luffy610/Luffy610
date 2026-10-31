#!/usr/bin/env python3
"""Generate the animated "Control Room" SVGs for the GitHub profile README.

Every asset is written twice, assets/<name>-dark.svg and assets/<name>-light.svg,
so the README can swap them with <picture> + prefers-color-scheme.

Edit the CONTENT section, then run:  python3 scripts/build_assets.py
Only the Python standard library is needed. Animations are SMIL + CSS inside
the SVG, which GitHub keeps when it shows an SVG as an image.
"""
from html import escape
from pathlib import Path
import math

OUT = Path(__file__).resolve().parent.parent / "assets"

# ----------------------------------------------------------------- CONTENT --
NAME = "Dhruv Kotwani"
HEADLINE_1 = "I build"
HEADLINE_2 = "AI solutions."
SUBLINE = [
    "Data engineer turned AI engineer. I ship GenAI that's",
    "secure, scalable and sane, from pipeline to agent.",
]
STATUS = "SYSTEM ONLINE · PUNE, IN"
TYPING = "currently building MCP security middleware"
ORBIT = ["MCP", "Bedrock", "RAG", "Guardrails", "Evals", "Pipelines"]

NOW = [
    "Building MCP security middleware: guardrails between agents and tools",
    "Designing multi-agent pipelines on AWS Bedrock",
    "Moving from Python data engineering into AI engineering",
]

CARDS = [
    dict(slug="f1-mcp", status="LIVE", tone="ok", meta="Python · MCP",
         title="F1-MCP",
         desc="118+ Formula 1 analytics tools: telemetry, lap and sector deltas, "
              "tyre strategy. Works with Claude and any MCP client.",
         code="$ pip install f1-mcp"),
    dict(slug="mcp-guard", status="BUILDING", tone="warn", meta="MCP · Presidio",
         title="MCP Security Middleware",
         desc="A guardrail layer between agents and tools: redacts PII, "
              "enforces policy and logs every call.",
         code="[EMAIL] [PERSON] [ID]"),
    dict(slug="instagram-mcp", status="IN PROGRESS", tone="warn", meta="MCP · Local",
         title="Instagram MCP",
         desc="My own Instagram MCP server, built from scratch to run "
              "locally and plug straight into Claude.",
         code="local · talks to Claude"),
]

STACK = [
    ("AI", ["AWS Bedrock", "Claude API", "MCP", "LangChain", "Presidio"]),
    ("DATA", ["Python", "SQL", "Spark", "Kafka", "Pandas"]),
    ("CLOUD", ["AWS Lambda", "ECS / EKS", "DynamoDB", "Docker"]),
]

# ------------------------------------------------------------------ THEMES --
THEMES = {
    "dark": dict(bg="#0d1117", surface="#161b22", term="#010409", border="#30363d",
                 border2="#21262d", text="#e6edf3", strong="#f0f6fc", body="#c9d1d9",
                 muted="#8b949e", accent="#22d3ee", accent_soft="#22d3ee55",
                 glow="#0b2530", amber="#fbbf24", amber_bg="#3a2e0f", amber_text="#fcd34d",
                 guard_bg="#1f1a0e", ok="#3fb950", core_hi="#e0fbff", core_lo="#083344",
                 core_text="#021014"),
    "light": dict(bg="#ffffff", surface="#f6f8fa", term="#f6f8fa", border="#d0d7de",
                  border2="#d8dee4", text="#1f2328", strong="#1f2328", body="#31373d",
                  muted="#59636e", accent="#0e7490", accent_soft="#0e749055",
                  glow="#e6f7fb", amber="#b45309", amber_bg="#fef3c7", amber_text="#92400e",
                  guard_bg="#fffbeb", ok="#1a7f37", core_hi="#ecfeff", core_lo="#0e7490",
                  core_text="#ffffff"),
}

SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'JetBrains Mono', Menlo, Consolas, monospace"
MONO_W = 0.6  # monospace advance width per em


def e(s):
    return escape(s, quote=True)


def svg(w, h, body, title, t):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{e(title)}">\n'
        f"<title>{e(title)}</title>\n"
        f"<style>\n"
        f"  .sans{{font-family:{SANS}}} .mono{{font-family:{MONO}}}\n"
        f"  @media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}\n"
        f"</style>\n{body}\n</svg>\n"
    )


def ellipse_path(cx, cy, rx, ry):
    # Starts at the right-hand point and runs clockwise: first half = front.
    return (f"M {cx + rx} {cy} A {rx} {ry} 0 1 1 {cx - rx} {cy} "
            f"A {rx} {ry} 0 1 1 {cx + rx} {cy}")


def text_w(s, size, mono=False):
    return len(s) * size * (MONO_W if mono else 0.56)


def wrap(s, limit):
    lines, cur = [], ""
    for word in s.split():
        if cur and len(cur) + 1 + len(word) > limit:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    return lines


def pulse_dot(x, y, r, color, dur="1.6s"):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}">'
            f'<animate attributeName="opacity" values="1;0.35;1" dur="{dur}" '
            f'repeatCount="indefinite"/></circle>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{color}">'
            f'<animate attributeName="r" values="{r};{r * 2.6}" dur="{dur}" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.7;0" dur="{dur}" repeatCount="indefinite"/>'
            f"</circle>")


# -------------------------------------------------------------------- HERO --
def orbiter(inner, path, dur, begin, layer, scale_swing=True):
    """One copy of an orbiting element: 'front' shows on the near half of the
    ellipse, 'back' on the far half, so it passes behind the core."""
    vis = "1;0" if layer == "front" else "0;1"
    scale = ('<animateTransform attributeName="transform" type="scale" '
             'values="1;1.12;1;0.84;1" keyTimes="0;0.25;0.5;0.75;1" '
             f'dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>') if scale_swing else ""
    return (f'<g opacity="0">'
            f'<animate attributeName="opacity" values="{vis}" keyTimes="0;0.5" calcMode="discrete" '
            f'dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
            f'<animateMotion path="{path}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
            f'<g>{scale}{inner}</g></g>')


def hero(t):
    W, H = 1000, 400
    cx, cy = 765, 206
    chip_path = ellipse_path(cx, cy, 168, 56)
    pkt_path = ellipse_path(cx, cy, 104, 34)
    dur, pdur = 24, 8

    def chip(label, dim):
        w = text_w(label, 13, True) + 26
        return (f'<g opacity="{0.55 if dim else 1}">'
                f'<rect x="{-w / 2:.1f}" y="-15" width="{w:.1f}" height="30" rx="15" '
                f'fill="{t["bg"]}" stroke="{t["accent_soft"]}"/>'
                f'<text class="mono" x="0" y="4.5" font-size="13" text-anchor="middle" '
                f'fill="{t["text"]}">{e(label)}</text></g>')

    def packet(dim):
        return (f'<circle r="4.5" fill="{t["accent"]}" opacity="{0.5 if dim else 1}"/>'
                f'<circle r="10" fill="{t["accent"]}" opacity="{0.08 if dim else 0.18}"/>')

    back, front = [], []
    n = len(ORBIT)
    for i, label in enumerate(ORBIT):
        b = -i * dur / n
        back.append(orbiter(chip(label, True), chip_path, dur, b, "back"))
        front.append(orbiter(chip(label, False), chip_path, dur, b, "front"))
    for i in range(3):
        b = -i * pdur / 3
        back.append(orbiter(packet(True), pkt_path, pdur, b, "back", False))
        front.append(orbiter(packet(False), pkt_path, pdur, b, "front", False))

    # typing effect: a clip rect that grows one character at a time
    tx, ty, size = 74, 366, 15
    cw = size * MONO_W
    chars = len(TYPING)
    full = chars * cw
    steps = [f"{i * cw:.2f}" for i in range(chars + 1)]
    type_share, hold = 0.55, 0.40  # of the cycle
    kt = [f"{type_share * i / chars:.4f}" for i in range(chars + 1)]
    widths = ";".join(steps + [f"{full:.2f}", "0"])
    keytimes = ";".join(kt + [f"{type_share + hold:.4f}", "1"])
    xs = ";".join([f"{tx + float(s):.2f}" for s in steps] + [f"{tx + full:.2f}", f"{tx}"])
    cyc = "7s"

    lines = "".join(
        f'<text class="sans" x="48" y="{306 + i * 26}" font-size="17" fill="{t["body"]}">{e(s)}</text>'
        for i, s in enumerate(SUBLINE))
    pill_w = text_w(STATUS, 12, True) + 56

    body = f"""
<defs>
  <radialGradient id="glow" cx="{cx / W}" cy="{cy / H}" r="0.45">
    <stop offset="0" stop-color="{t['glow']}"/><stop offset="1" stop-color="{t['bg']}"/>
  </radialGradient>
  <radialGradient id="core" cx="0.35" cy="0.3" r="0.75">
    <stop offset="0" stop-color="{t['core_hi']}"/><stop offset="0.38" stop-color="{t['accent']}"/>
    <stop offset="1" stop-color="{t['core_lo']}"/>
  </radialGradient>
  <filter id="soft" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="18"/></filter>
  <clipPath id="typeclip"><rect x="{tx}" y="{ty - 16}" height="22" width="0">
    <animate attributeName="width" values="{widths}" keyTimes="{keytimes}" calcMode="discrete" dur="{cyc}" repeatCount="indefinite"/>
  </rect></clipPath>
</defs>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="url(#glow)" stroke="{t['border']}"/>

<g transform="translate(48 50)">
  <rect width="{pill_w:.1f}" height="28" rx="14" fill="{t['bg']}" stroke="{t['border']}"/>
  {pulse_dot(16, 14, 4, t['accent'])}
  <text class="mono" x="30" y="18.5" font-size="12" fill="{t['body']}" letter-spacing="0.5">{e(STATUS)}</text>
</g>
<text class="mono" x="48" y="128" font-size="16" fill="{t['muted']}">Hi, I'm {e(NAME)}</text>
<text class="sans" x="46" y="196" font-size="60" font-weight="700" fill="{t['strong']}" letter-spacing="-1.2">{e(HEADLINE_1)}</text>
<text class="sans" x="46" y="262" font-size="60" font-weight="700" fill="{t['accent']}" letter-spacing="-1.2">{e(HEADLINE_2)}</text>
{lines}
<text class="mono" x="48" y="{ty}" font-size="{size}" fill="{t['accent']}">&gt;</text>
<text class="mono" x="{tx}" y="{ty}" font-size="{size}" fill="{t['text']}" clip-path="url(#typeclip)">{e(TYPING)}</text>
<rect x="{tx}" y="{ty - 15}" width="2" height="19" fill="{t['accent']}">
  <animate attributeName="x" values="{xs}" keyTimes="{keytimes}" calcMode="discrete" dur="{cyc}" repeatCount="indefinite"/>
  <animate attributeName="opacity" values="1;0" dur="0.9s" calcMode="discrete" repeatCount="indefinite"/>
</rect>

<g aria-hidden="true">
  <ellipse cx="{cx}" cy="{cy}" rx="214" ry="72" fill="none" stroke="{t['border2']}"/>
  <ellipse cx="{cx}" cy="{cy}" rx="168" ry="56" fill="none" stroke="{t['accent_soft']}" stroke-dasharray="4 6">
    <animate attributeName="stroke-dashoffset" values="0;-100" dur="6s" repeatCount="indefinite"/>
  </ellipse>
  <ellipse cx="{cx}" cy="{cy}" rx="104" ry="34" fill="none" stroke="{t['border']}"/>
  {''.join(back)}
  <circle cx="{cx}" cy="{cy}" r="58" fill="{t['accent']}" opacity="0.35" filter="url(#soft)">
    <animate attributeName="opacity" values="0.25;0.5;0.25" dur="3.2s" repeatCount="indefinite"/>
  </circle>
  <circle cx="{cx}" cy="{cy}" r="50" fill="url(#core)">
    <animate attributeName="r" values="49;54;49" dur="3.2s" repeatCount="indefinite"/>
  </circle>
  <text class="mono" x="{cx}" y="{cy + 5.5}" font-size="16" font-weight="600" text-anchor="middle" fill="{t['core_text']}">LLM</text>
  {''.join(front)}
</g>"""
    return svg(W, H, body, f"{NAME}: I build AI solutions. Data engineer turned AI engineer, "
                           f"{TYPING}.", t)


# ------------------------------------------------------------- NOW (terminal)
def label(x, y, num, txt, t):
    return (f'<text class="mono" x="{x}" y="{y}" font-size="13" letter-spacing="1.6" '
            f'fill="{t["accent"]}">{num} / {e(txt.upper())}</text>')


def now(t):
    W, top = 1000, 36
    H = top + 64 + len(NOW) * 32 + 30
    rows = []
    for i, s in enumerate(NOW):
        y = top + 94 + i * 32
        begin = 0.6 + i * 0.55
        end = begin + 0.25
        # visible by default (static renderers), faded in when animated
        rows.append(
            f'<g><animate attributeName="opacity" values="0;0;1" keyTimes="0;{begin / end:.3f};1" '
            f'dur="{end:.2f}s" fill="freeze"/>'
            f'<text class="mono" x="28" y="{y}" font-size="16" fill="{t["amber"]}">→</text>'
            f'<text class="mono" x="52" y="{y}" font-size="16" fill="{t["body"]}">{e(s)}</text></g>')
    cursor_y = top + 94 + len(NOW) * 32 - 15
    body = f"""
{label(2, 14, "01", "now", t)}
<rect x="0.5" y="{top + 0.5}" width="{W - 1}" height="{H - top - 1}" rx="10" fill="{t['term']}" stroke="{t['border']}"/>
<line x1="1" y1="{top + 32}" x2="{W - 1}" y2="{top + 32}" stroke="{t['border2']}"/>
<circle cx="22" cy="{top + 16}" r="5" fill="{t['border']}"/><circle cx="40" cy="{top + 16}" r="5" fill="{t['border']}"/><circle cx="58" cy="{top + 16}" r="5" fill="{t['border']}"/>
<text class="mono" x="{W / 2}" y="{top + 20}" font-size="12" text-anchor="middle" fill="{t['muted']}">~/now.md</text>
<text class="mono" x="28" y="{top + 62}" font-size="16"><tspan fill="{t['accent']}">dhruv@pune</tspan><tspan fill="{t['muted']}">:~$ </tspan><tspan fill="{t['text']}">cat now.md</tspan></text>
{''.join(rows)}
<rect x="28" y="{cursor_y}" width="9" height="17" fill="{t['accent']}" opacity="0">
  <animate attributeName="opacity" values="0;1" begin="{0.6 + len(NOW) * 0.55}s" dur="1s" calcMode="discrete" repeatCount="indefinite"/>
</rect>"""
    return svg(W, H, body, "Now: " + "; ".join(NOW), t)


# ------------------------------------------------------------------- CARDS --
def card(c, t):
    W, H = 300, 260
    tone = t["ok"] if c["tone"] == "ok" else t["amber"]
    desc = wrap(c["desc"], 33)
    desc_svg = "".join(
        f'<text class="sans" x="20" y="{110 + i * 21}" font-size="15" fill="{t["body"]}">{e(s)}</text>'
        for i, s in enumerate(desc))
    code_color = t["amber"] if c["tone"] == "warn" and "[" in c["code"] else t["accent"]
    perim = 2 * (W - 1 + H - 1)
    title_size = 20 if len(c["title"]) > 16 else 24
    body = f"""
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="{t['surface']}" stroke="{t['border']}"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{t['accent']}" stroke-width="1.5"
      stroke-dasharray="80 {perim - 80:.0f}" opacity="0.9">
  <animate attributeName="stroke-dashoffset" values="0;-{perim:.0f}" dur="7s" repeatCount="indefinite"/>
</rect>
{pulse_dot(24, 28, 4, tone)}
<text class="mono" x="36" y="32" font-size="12" letter-spacing="0.6" fill="{t['muted']}">{e(c['status'])}</text>
<text class="mono" x="{W - 20}" y="32" font-size="12" text-anchor="end" fill="{t['muted']}">{e(c['meta'])}</text>
<text class="sans" x="20" y="74" font-size="{title_size}" font-weight="700" fill="{t['strong']}">{e(c['title'])}</text>
{desc_svg}
<rect x="20" y="{H - 56}" width="{W - 40}" height="36" rx="7" fill="{t['term']}" stroke="{t['border2']}"/>
<text class="mono" x="32" y="{H - 33}" font-size="12.5" fill="{code_color}">{e(c['code'])}</text>
<text class="sans" x="{W - 32}" y="{H - 32}" font-size="16" text-anchor="end" fill="{t['accent']}">→</text>"""
    return svg(W, H, body, f"{c['title']} ({c['status'].lower()}): {c['desc']}", t)


# --------------------------------------------------------------- GUARDRAIL --
def guardrail(t):
    W, H = 1000, 290
    bw, gap, y0, bh = 200, 56, 104, 168
    xs = [16 + i * (bw + gap) for i in range(4)]

    def box(i, kicker, kcol, fill, stroke, content):
        x = xs[i]
        return (f'<rect x="{x}" y="{y0}" width="{bw}" height="{bh}" rx="10" fill="{fill}" stroke="{stroke}"/>'
                f'<text class="mono" x="{x + 16}" y="{y0 + 28}" font-size="11" letter-spacing="1.4" fill="{kcol}">{kicker}</text>'
                + content(x))

    def mono_lines(x, lines, col):
        return "".join(f'<text class="mono" x="{x + 16}" y="{y0 + 62 + j * 26}" font-size="14" fill="{col}">{e(s)}</text>'
                       for j, s in enumerate(lines))

    def safe(x):
        out = []
        lines = [["Refund to ", "[PERSON]", ","], ["[EMAIL]", ","], ["PAN ", "[ID]"]]
        for j, parts in enumerate(lines):
            cx = x + 16
            y = y0 + 62 + j * 26
            for p in parts:
                w = text_w(p, 14, True)
                if p.startswith("["):
                    out.append(f'<rect x="{cx - 3:.1f}" y="{y - 13}" width="{w + 6:.1f}" height="19" rx="4" fill="{t["amber_bg"]}"/>'
                               f'<text class="mono" x="{cx:.1f}" y="{y}" font-size="14" fill="{t["amber_text"]}">{e(p)}</text>')
                else:
                    out.append(f'<text class="mono" x="{cx:.1f}" y="{y}" font-size="14" fill="{t["text"]}">{e(p)}</text>')
                cx += w
        return "".join(out)

    def plain(x, title, sub, col):
        return (f'<text class="sans" x="{x + 16}" y="{y0 + 64}" font-size="19" font-weight="700" fill="{t["strong"]}">{e(title)}</text>'
                + "".join(f'<text class="sans" x="{x + 16}" y="{y0 + 94 + j * 22}" font-size="15" fill="{col}">{e(s)}</text>'
                          for j, s in enumerate(sub)))

    connectors = []
    cyc = 2.4
    for i in range(3):
        x1, x2, y = xs[i] + bw + 6, xs[i + 1] - 6, y0 + bh / 2
        col = t["amber"] if i == 1 else t["accent"]
        a, b = i / 3, (i + 1) / 3
        if i == 0:
            vis, vkt = "1;0", "0;0.3333"
        else:
            vis, vkt = "0;1;0", f"0;{a:.4f};{b:.4f}"
        connectors.append(
            f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{t["border"]}" stroke-width="2"/>'
            f'<polygon points="{x2},{y} {x2 - 7},{y - 4} {x2 - 7},{y + 4}" fill="{t["border"]}"/>'
            f'<circle r="4.5" fill="{col}" opacity="0">'
            f'<animate attributeName="opacity" values="{vis}" keyTimes="{vkt}" calcMode="discrete" dur="{cyc}s" repeatCount="indefinite"/>'
            f'<animateMotion path="M {x1} {y} L {x2 - 8} {y}" keyPoints="0;0;1;1" keyTimes="0;{a:.4f};{b:.4f};1" '
            f'calcMode="linear" dur="{cyc}s" repeatCount="indefinite"/></circle>')

    gx = xs[1]
    body = f"""
{label(2, 14, "03", "how I build", t)}
<text class="sans" x="0" y="52" font-size="26" font-weight="700" fill="{t['strong']}">Every request passes the guardrail first</text>
<text class="sans" x="0" y="80" font-size="15" fill="{t['muted']}">Personal data is stripped before a model or a tool ever sees it.</text>
{box(0, "INPUT", t['muted'], t['surface'], t['border'], lambda x: mono_lines(x, ["Refund to Asha Rao,", "asha.rao@mail.com,", "PAN ABCDE1234F"], t['text']))}
<rect x="{gx}" y="{y0}" width="{bw}" height="{bh}" rx="10" fill="none" stroke="{t['amber']}" stroke-width="2" opacity="0.5">
  <animate attributeName="stroke-width" values="1;10;1" dur="{cyc}s" repeatCount="indefinite"/>
  <animate attributeName="opacity" values="0.45;0;0.45" dur="{cyc}s" repeatCount="indefinite"/>
</rect>
{box(1, "GUARDRAIL", t['amber'], t['guard_bg'], t['amber'], lambda x: plain(x, "PII redaction", ["Presidio", "policy checks", "audit log"], t['body']))}
{box(2, "SAFE PROMPT", t['muted'], t['surface'], t['border'], safe)}
{box(3, "MODEL + TOOLS", t['accent'], t['glow'], t['accent_soft'], lambda x: plain(x, "Bedrock · Claude", ["MCP tools get only", "what they need"], t['body']))}
{''.join(connectors)}"""
    return svg(W, H, body, "How I build: input with personal data goes through a PII-redaction guardrail "
                           "(Presidio, policy checks, audit log), becomes a safe prompt with [PERSON], [EMAIL] "
                           "and [ID] tokens, then reaches the model and MCP tools.", t)


# ------------------------------------------------------------------- STACK --
def stack(t):
    W = 1000
    H = 28 + len(STACK) * 44
    rows = [label(2, 14, "04", "stack", t)]
    for r, (group, items) in enumerate(STACK):
        y = 34 + r * 44
        rows.append(f'<text class="mono" x="2" y="{y + 22}" font-size="12" fill="{t["muted"]}">{e(group)}</text>')
        x = 92
        for k, item in enumerate(items):
            w = text_w(item, 14) + 30
            rows.append(
                f'<g><rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="32" rx="7" fill="{t["surface"]}" stroke="{t["border"]}"/>'
                f'<text class="sans" x="{x + w / 2:.1f}" y="{y + 21}" font-size="14" text-anchor="middle" fill="{t["text"]}">{e(item)}</text></g>')
            x += w + 10
    flat = "; ".join(f"{g}: {', '.join(i)}" for g, i in STACK)
    return svg(W, H, "\n".join(rows), "Stack. " + flat, t)


# ----------------------------------------------------------- LABEL + BUTTONS
def section_label(num, txt):
    def f(t):
        return svg(1000, 22, label(2, 15, num, txt, t), f"{num} / {txt}", t)
    return f


ICONS = {
    "person": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
}


def button(text, icon, primary=False):
    def f(t):
        W, H = int(text_w(text, 15) + 74), 46
        stroke = t["accent"] if primary else t["border"]
        fill = t["glow"] if primary else t["surface"]
        body = (f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="9" fill="{fill}" stroke="{stroke}"/>'
                f'<g transform="translate(18 11)" fill="none" stroke="{t["accent"]}" stroke-width="2" '
                f'stroke-linecap="round" stroke-linejoin="round">{ICONS[icon]}</g>'
                f'<text class="sans" x="50" y="29" font-size="15" fill="{t["text"]}">{e(text)}</text>')
        return svg(W, H, body, text, t)
    return f


# -------------------------------------------------------------------- MAIN --
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = {
        "hero": hero, "now": now, "guardrail": guardrail, "stack": stack,
        "label-builds": section_label("02", "featured builds"),
        "label-contrib": section_label("05", "contributions, in 3D"),
        "btn-linkedin": button("LinkedIn", "person", True),
        "btn-email": button("Email", "mail"),
    }
    for c in CARDS:
        jobs[f"card-{c['slug']}"] = (lambda c: lambda t: card(c, t))(c)
    for name, fn in jobs.items():
        for mode, t in THEMES.items():
            (OUT / f"{name}-{mode}.svg").write_text(fn(t), encoding="utf-8")
    print(f"wrote {len(jobs) * 2} files to {OUT}")


if __name__ == "__main__":
    main()
