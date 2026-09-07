#!/usr/bin/env python3
"""Generates the profile header banners (light + dark).

The motif on the right is a 2-D projection of an embedding space: one query
vector, its nearest neighbours, and the retrieval radius. It is a picture of
what the work actually is, not decoration.
"""
import math, random
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

W, H = 1200, 300

THEMES = {
    "light": dict(bg="#ffffff", ink="#11131a", muted="#5b6472", accent="#c2410c",
                  rule="#e6e9ee", dot="#ced5df", dotdim="#e4e8ee", ring="#e6e9ee"),
    "dark":  dict(bg="#0d1117", ink="#e9eef5", muted="#8b97a8", accent="#ff8a5b",
                  rule="#20262e", dot="#2c3540", dotdim="#1c222a", ring="#20262e"),
}

NAME = "Diar Azemi"
ROLE = "Software Engineer"
FOCUS = "AI retrieval systems &amp; healthcare platforms"
META = "PRISHTINA, KOSOVO"

SANS = ("ui-sans-serif,-apple-system,BlinkMacSystemFont,'Segoe UI',"
        "Inter,Roboto,Helvetica,Arial,sans-serif")
MONO = ("ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'Liberation Mono',monospace")

# --- embedding-space motif -------------------------------------------------
CX, CY, R = 966.0, 150.0, 118.0
random.seed(1987)

def make_points(n=66):
    pts = []
    tries = 0
    while len(pts) < n and tries < 6000:
        tries += 1
        a = random.random() * math.tau
        # bias outward a little so the cloud reads as a shell, not a blob
        r = R * math.sqrt(random.random()) * (0.55 + 0.45 * random.random())
        x, y = CX + r * math.cos(a), CY + r * math.sin(a) * 0.86
        if all((x - px) ** 2 + (y - py) ** 2 > 18.5 ** 2 for px, py in pts):
            pts.append((x, y))
    return pts

pts = make_points()
query = min(pts, key=lambda p: (p[0] - CX) ** 2 + (p[1] - CY) ** 2)
rest = [p for p in pts if p is not query]
rest.sort(key=lambda p: (p[0] - query[0]) ** 2 + (p[1] - query[1]) ** 2)
neighbours = rest[:5]
radius = max(math.dist(query, p) for p in neighbours) + 13


def svg(theme_name):
    t = THEMES[theme_name]
    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
      f'viewBox="0 0 {W} {H}" role="img" '
      f'aria-label="{NAME} — {ROLE}, {META.title()}">')
    rad = int(radius)
    a('<style>'
      '@keyframes sweep{0%{r:14px;opacity:.55}70%{opacity:0}100%{r:' + str(rad) + 'px;opacity:0}}'
      '.sweep{animation:sweep 4.6s cubic-bezier(.22,.61,.36,1) infinite}'
      '@keyframes glow{0%,100%{opacity:.55}50%{opacity:1}}'
      '.nb{animation:glow 4.6s ease-in-out infinite}'
      '@media (prefers-reduced-motion:reduce){.sweep,.nb{animation:none}}'
      '</style>')
    a(f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>')

    # --- motif
    a(f'<g>')
    a(f'<circle cx="{CX:.1f}" cy="{CY:.1f}" r="{R:.0f}" fill="none" '
      f'stroke="{t["ring"]}" stroke-width="1"/>')
    a(f'<circle cx="{CX:.1f}" cy="{CY:.1f}" r="{R*0.62:.0f}" fill="none" '
      f'stroke="{t["ring"]}" stroke-width="1" stroke-dasharray="2 6"/>')
    for x, y in pts:
        if (x, y) is query or (x, y) in neighbours:
            continue
        a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{t["dot"]}"/>')
    for i, (x, y) in enumerate(neighbours):
        a(f'<line x1="{query[0]:.1f}" y1="{query[1]:.1f}" x2="{x:.1f}" y2="{y:.1f}" '
          f'stroke="{t["accent"]}" stroke-width="1" opacity=".38"/>')
        a(f'<circle class="nb" cx="{x:.1f}" cy="{y:.1f}" r="3.4" '
          f'fill="{t["accent"]}" opacity=".7" '
          f'style="animation-delay:{i*0.14:.2f}s"/>')
    a(f'<circle cx="{query[0]:.1f}" cy="{query[1]:.1f}" r="{radius:.0f}" '
      f'fill="none" stroke="{t["accent"]}" stroke-width="1" stroke-dasharray="3 5" '
      f'opacity=".45"/>')
    a(f'<circle class="sweep" cx="{query[0]:.1f}" cy="{query[1]:.1f}" r="14" '
      f'fill="none" stroke="{t["accent"]}" stroke-width="1.4"/>')
    a(f'<circle cx="{query[0]:.1f}" cy="{query[1]:.1f}" r="5.6" fill="{t["accent"]}"/>')
    a('</g>')

    # --- type
    a(f'<text x="72" y="132" font-family="{SANS}" font-size="58" font-weight="640" '
      f'letter-spacing="-1.8" fill="{t["ink"]}">{NAME}</text>')
    a(f'<text x="74" y="169" font-family="{SANS}" font-size="20.5" font-weight="500" '
      f'letter-spacing="-.2" fill="{t["muted"]}">{ROLE} '
      f'<tspan fill="{t["accent"]}">·</tspan> {FOCUS}</text>')
    a(f'<line x1="74" y1="201" x2="322" y2="201" stroke="{t["rule"]}" stroke-width="1.5"/>')
    a(f'<text x="74" y="231" font-family="{MONO}" font-size="12.5" letter-spacing="2.6" '
      f'fill="{t["muted"]}">{META}</text>')
    a('</svg>')
    return "".join(o)


for name in THEMES:
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / f"header-{name}.svg").write_text(svg(name), encoding="utf-8")
print("wrote both banners")
