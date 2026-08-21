# -*- coding: utf-8 -*-
"""Emit the benchmark dumbbell as two static SVGs, one per GitHub theme.

Same data and same validated palette as the landing page. No external fonts,
no scripts: GitHub sanitises anything else out of an SVG it renders.
"""
import io

import os

OUT = os.path.dirname(os.path.abspath(__file__)) + '/'

GATES = [
    ("Withholds the solution while active", 100, 56),
    ("Exactly one question per reply", 100, 44),
    ("No code block while active", 100, 33),
    ("No command handed over as a hint", 100, 40),
    ("Question doesn't smuggle the diagnosis", 100, 0),
    ("No hint where the level forbids one", 100, 0),
    ("Confirms the answer instead of probing on", 100, 0),
    ("Replies in the user's language", 100, 100),
    ("Hands the answer over on exit", 100, 100),
]

THEMES = {
    "light": dict(ink="#1a1c1f", muted="#5c636c", line="#dbdee3",
                  skill="#1f6fb2", control="#a2543a", ring="#ffffff"),
    "dark":  dict(ink="#e6e8ea", muted="#9aa0a8", line="#2d3138",
                  skill="#4691d6", control="#c2775a", ring="#0d1117"),
}

W, ROW_H, TOP = 900, 34, 52
LABEL_R = 300           # label column ends here
TRACK_L, TRACK_R = 320, 700
PAD = 9                 # the marks' breathing room, same as the site
V_CONTROL, V_SKILL = 780, 862
H = TOP + len(GATES) * ROW_H + 46

SANS = "ui-sans-serif,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"

def x_of(pct):
    return TRACK_L + PAD + (TRACK_R - TRACK_L - 2 * PAD) * pct / 100.0

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&#39;")

def svg(theme):
    c = THEMES[theme]
    alt = ("Pass rate per gate, with the skill versus without it. "
           + "; ".join("%s %d%% vs %d%%" % (g, s, ct) for g, s, ct in GATES))
    p = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
         'role="img" aria-label="%s">' % (W, H, W, H, esc(alt))]

    # column headers double as the legend
    p.append('<g font-family="%s" font-size="11" letter-spacing="0.9">' % MONO)
    p.append('<circle cx="%d" cy="26" r="4.5" fill="%s"/>' % (V_CONTROL - 56, c["control"]))
    p.append('<text x="%d" y="30" fill="%s" text-anchor="end">CONTROL</text>' % (V_CONTROL, c["muted"]))
    p.append('<circle cx="%d" cy="26" r="4.5" fill="%s"/>' % (V_SKILL - 40, c["skill"]))
    p.append('<text x="%d" y="30" fill="%s" text-anchor="end">SKILL</text>' % (V_SKILL, c["muted"]))
    p.append('</g>')

    for i, (gate, skill, control) in enumerate(GATES):
        y = TOP + i * ROW_H + ROW_H / 2
        xs, xc = x_of(skill), x_of(control)
        p.append('<text x="%d" y="%.1f" fill="%s" font-family="%s" font-size="13.5" '
                 'text-anchor="end" dominant-baseline="middle">%s</text>'
                 % (LABEL_R, y, c["ink"], SANS, esc(gate)))
        p.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1"/>'
                 % (TRACK_L, y, TRACK_R, y, c["line"]))
        if skill != control:
            lo, hi = sorted((xs, xc))
            p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="url(#grad)" stroke-width="2"/>'
                     % (lo, y, hi, y))
        p.append('<circle cx="%.1f" cy="%.1f" r="5.5" fill="%s" stroke="%s" stroke-width="2"/>'
                 % (xc, y, c["control"], c["ring"]))
        p.append('<circle cx="%.1f" cy="%.1f" r="5.5" fill="%s" stroke="%s" stroke-width="2"/>'
                 % (xs, y, c["skill"], c["ring"]))
        p.append('<g font-family="%s" font-size="12.5" dominant-baseline="middle">' % MONO)
        p.append('<text x="%d" y="%.1f" fill="%s" text-anchor="end">%d%%</text>' % (V_CONTROL, y, c["control"], control))
        p.append('<text x="%d" y="%.1f" fill="%s" text-anchor="end">%d%%</text>' % (V_SKILL, y, c["skill"], skill))
        p.append('</g>')

    # axis
    ay = TOP + len(GATES) * ROW_H + 6
    p.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1"/>'
             % (TRACK_L, ay, V_SKILL, ay, c["line"]))
    p.append('<g font-family="%s" font-size="11" fill="%s" text-anchor="middle">' % (MONO, c["muted"]))
    for pct in (0, 50, 100):
        p.append('<text x="%.1f" y="%.1f">%d%%</text>' % (x_of(pct), ay + 18, pct))
    p.append('</g>')
    # Under the label column, not on the tick row: right-aligned at V_SKILL it
    # sat on top of the 100% tick.
    p.append('<text x="%d" y="%.1f" fill="%s" font-family="%s" font-size="12.5" text-anchor="end">'
             '44/44 vs 24/43 gradeable assertions</text>' % (LABEL_R, ay + 18, c["muted"], SANS))

    p.append('<defs><linearGradient id="grad" x1="0" x2="1">'
             '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/>'
             '</linearGradient></defs>' % (c["control"], c["skill"]))
    p.append('</svg>')
    return "\n".join(p) + "\n"

for theme in THEMES:
    path = OUT + "benchmark-%s.svg" % theme
    io.open(path, "w", encoding="utf-8", newline="\n").write(svg(theme))
    print("escrito:", path)
