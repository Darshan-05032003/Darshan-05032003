"""Generate the animated SVGs used by the profile README.

Every animation is plain CSS inside the SVG, so it runs when GitHub shows the
image with no JavaScript and no external requests. Run:

    python3 tools/gen_svgs.py

and commit the files it writes to assets/.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"

THEMES = {
    "light": dict(paper="#E7EEE2", paper2="#DAE4D3", paper3="#F1F5EE", rule="#BFD0C8", margin="#D0786F",
                  ink="#15213B", ink2="#4E5A70", blue="#2443B0", blue_soft="#D6DDF3", red="#B3261E",
                  red_soft="#F2D9D3", on_blue="#FFFFFF", term_bg="#15213B", term_fg="#E7EEE2",
                  term_dim="#8C98AE", term_prompt="#8FB3FF", term_ok="#7BD88F", term_err="#FF8A80",
                  term_border="#15213B"),
    "dark": dict(paper="#0E1524", paper2="#16203A", paper3="#121B2E", rule="#22304B", margin="#9A4540",
                 ink="#E9EFE5", ink2="#9AA8BF", blue="#86A5FF", blue_soft="#24345F", red="#FF7268",
                 red_soft="#3A1E25", on_blue="#0E1524", term_bg="#0A0F1C", term_fg="#E9EFE5",
                 term_dim="#7D8AA3", term_prompt="#86A5FF", term_ok="#7BD88F", term_err="#FF8A80",
                 term_border="#2A3958"),
}

SERIF = "'Bodoni 72','Didot','Bodoni Moda',Georgia,'Times New Roman',serif"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
MONO_W = 0.6  # advance width of a monospace glyph, in em


def pct(t, cycle):
    return f"{max(0.0, min(100.0, t / cycle * 100)):.3f}%"


class SVG:
    def __init__(self, w, h, theme, label):
        self.w, self.h, self.p, self.label = w, h, THEMES[theme], label
        self.css, self.defs, self.body = [], [], []
        self.n = 0

    def uid(self, prefix="a"):
        self.n += 1
        return f"{prefix}{self.n}"

    def anim(self, cycle, frames, extra="", loop=True):
        """frames: list of (seconds, css, optional timing-function for the next segment)."""
        name = self.uid("k")
        steps = []
        for f in frames:
            t, props = f[0], f[1]
            timing = f"animation-timing-function:{f[2]};" if len(f) > 2 and f[2] else ""
            steps.append(f"{pct(t, cycle)}{{{props};{timing}}}")
        self.css.append(f"@keyframes {name}{{{''.join(steps)}}}")
        count = "infinite" if loop else "1"
        self.css.append(f".{name}{{animation:{name} {cycle}s linear {count} both;{extra}}}")
        return name

    # --- common animations ---------------------------------------------------
    def window(self, cycle, t_in, t_out, fade=0.3, dy=0, dx=0, loop=True):
        """Visible between t_in and t_out, with a fade (and optional slide) in and out."""
        hidden = f"opacity:0;transform:translate({dx}px,{dy}px)"
        shown = "opacity:1;transform:translate(0px,0px)"
        frames = [(0, hidden), (t_in, hidden, "cubic-bezier(.2,.8,.3,1)"), (min(t_in + fade, cycle), shown)]
        if t_out is not None and t_out < cycle:
            frames += [(t_out, shown), (min(t_out + fade, cycle), "opacity:0;transform:translate(0px,0px)"),
                       (cycle, "opacity:0;transform:translate(0px,0px)")]
        else:
            frames += [(cycle, shown)]
        return self.anim(cycle, frames, loop=loop)

    def typing(self, cycle, t0, n, cps, t_out):
        """scaleX reveal in n steps (one per character)."""
        dur = n / cps
        frames = [(0, "transform:scaleX(0)"), (t0, "transform:scaleX(0)", f"steps({n},end)"),
                  (t0 + dur, "transform:scaleX(1)"), (t_out, "transform:scaleX(1)"),
                  (t_out + 0.2, "transform:scaleX(0)"), (cycle, "transform:scaleX(0)")]
        return self.anim(cycle, frames, "transform-box:fill-box;transform-origin:0 50%;")

    def caret(self, cycle, t0, n, cps, width, t_hide):
        """Caret that travels with a typing reveal, then blinks until t_hide."""
        dur = n / cps
        move = self.anim(cycle, [(0, "transform:translateX(0px)"),
                                 (t0, "transform:translateX(0px)", f"steps({n},end)"),
                                 (t0 + dur, f"transform:translateX({width}px)"),
                                 (cycle, f"transform:translateX({width}px)")])
        vis = self.window(cycle, t0, t_hide, fade=0.01)
        return move, vis

    # --- output ----------------------------------------------------------------
    def render(self):
        css = "".join(self.css)
        css += "@media (prefers-reduced-motion: reduce){*{animation-duration:0.001s!important;animation-iteration-count:1!important;animation-delay:0s!important}}"
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.label)}">'
                f"<title>{escape(self.label)}</title>"
                f"<style>{css}</style><defs>{''.join(self.defs)}</defs>{''.join(self.body)}</svg>")

    def add(self, s):
        self.body.append(s)


def text(x, y, s, size, fill, family=SANS, weight=400, anchor="start", style="", extra=""):
    st = f' font-style="{style}"' if style else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{st} {extra}>{escape(s)}</text>')


def g(cls, inner, extra=""):
    return f'<g class="{cls}" {extra}>{inner}</g>'


def typed_line(svg, cycle, x, y, s, size, fill, t0, cps, t_out, family=MONO, weight=400, caret=None,
               caret_linger=None):
    """Monospace line revealed one character at a time through a clip."""
    n = max(1, len(s))
    w = MONO_W * size * n + 6
    cid = svg.uid("c")
    cls = svg.typing(cycle, t0, n, cps, t_out)
    svg.defs.append(f'<clipPath id="{cid}"><rect class="{cls}" x="{x}" y="{y - size}" width="{w:.1f}" '
                    f'height="{size * 1.4:.1f}"/></clipPath>')
    svg.add(f'<g clip-path="url(#{cid})">{text(x, y, s, size, fill, family, weight, extra="xml:space=\"preserve\"")}</g>')
    if caret:
        hide = t0 + n / cps + caret_linger if caret_linger is not None else t_out
        move, vis = svg.caret(cycle, t0, n, cps, MONO_W * size * n, hide)
        svg.add(g(vis, g(move, f'<rect x="{x + 1}" y="{y - size * 0.85:.1f}" width="{size * 0.55:.1f}" '
                                 f'height="{size:.1f}" fill="{caret}" opacity="0.85"/>')))
    return t0 + n / cps


# =============================================================================
# HERO
# =============================================================================
def hero(theme):
    p = THEMES[theme]
    W, H = 1200, 400
    s = SVG(W, H, theme, "Darshan Sonawane. Backend and Android engineer. Backends that stay correct "
                         "under concurrency; Android apps that work with the app closed.")
    s.defs.append(f'<pattern id="rules" width="{W}" height="32" patternUnits="userSpaceOnUse">'
                  f'<rect width="{W}" height="32" fill="{p["paper"]}"/>'
                  f'<rect y="31" width="{W}" height="1" fill="{p["rule"]}"/></pattern>')
    s.add(f'<rect width="{W}" height="{H}" fill="url(#rules)" rx="10"/>')

    # margin rule draws down once
    draw = s.anim(1.2, [(0, "transform:scaleY(0)", "cubic-bezier(.6,0,.2,1)"), (1.2, "transform:scaleY(1)")],
                  "transform-box:fill-box;transform-origin:50% 0;", loop=False)
    s.add(g(draw, f'<rect x="126" y="0" width="1.5" height="{H}" fill="{p["margin"]}"/>'
                  f'<rect x="130" y="0" width="1.5" height="{H}" fill="{p["margin"]}"/>'))

    once = 3.2
    s.add(g(s.anim(once, [(0, "opacity:0"), (0.4, "opacity:0"), (1.0, "opacity:1"), (once, "opacity:1")], loop=False),
            text(112, 58, "2026", 13, p["ink2"], anchor="end") +
            text(112, 150, "Backend ·", 13, p["ink2"], anchor="end") +
            text(112, 168, "Android", 13, p["ink2"], anchor="end")))

    # name: ink settles in, with an underline that draws itself
    def rise(t0):
        return s.anim(t0 + 1.0, [(0, "opacity:0;transform:translateY(18px)"),
                                 (t0, "opacity:0;transform:translateY(18px)", "cubic-bezier(.16,1,.3,1)"),
                                 (t0 + 0.9, "opacity:1;transform:translateY(0px)"),
                                 (t0 + 1.0, "opacity:1;transform:translateY(0px)")], loop=False)
    s.add(g(rise(0.3), text(160, 124, "Darshan", 92, p["ink"], SERIF, 700, extra='letter-spacing="-2"')))
    s.add(g(rise(0.75), text(205, 206, "Sonawane", 92, p["ink"], SERIF, 500, style="italic",
                             extra='letter-spacing="-1"')))
    ul = s.anim(2.4, [(0, "stroke-dashoffset:520"), (1.4, "stroke-dashoffset:520", "cubic-bezier(.6,0,.2,1)"),
                      (2.4, "stroke-dashoffset:0")], loop=False)
    s.add(f'<path class="{ul}" d="M205 224 C 320 217, 470 228, 590 219" fill="none" stroke="{p["blue"]}" '
          f'stroke-width="3" stroke-linecap="round" stroke-dasharray="520"/>')

    # open-to-work pulse
    pulse = s.anim(2.0, [(0, "transform:scale(1);opacity:.55"), (1.6, "transform:scale(2.6);opacity:0"),
                         (2.0, "transform:scale(2.6);opacity:0")], "transform-box:fill-box;transform-origin:center;")
    s.add(f'<circle class="{pulse}" cx="166" cy="356" r="6" fill="{p["blue"]}"/>'
          f'<circle cx="166" cy="356" r="6" fill="{p["blue"]}"/>')
    s.add(text(182, 361, "Open to freelance and full-time backend / Android work", 14, p["ink2"]))

    # rotating lede, typed
    lines = [
        "I build backends that stay correct when 20 people click at once.",
        "I build Android apps that keep working after you close them.",
        "I write the failing test first, then the code, then the load test.",
        "I keep money in a ledger you append to, never overwrite.",
    ]
    slot, cps, size = 5.0, 34, 19
    cycle = slot * len(lines)
    s.add(text(160, 300, ">", size, p["blue"], MONO, 700))
    x0 = 160 + MONO_W * size * 2
    for i, ln in enumerate(lines):
        t0 = i * slot + 0.2
        typed_line(s, cycle, x0, 300, ln, size, p["ink"], t0, cps, t0 + slot - 0.45, caret=p["blue"])

    s.add(text(160, 330, "Java · Spring Boot · PostgreSQL · Kafka · Kotlin · Jetpack Compose · Testcontainers",
               14, p["ink2"]))

    # closing balance panel with odometers
    px, pr = 800, 1160
    s.add(g(s.anim(once, [(0, "opacity:0"), (0.6, "opacity:0"), (1.2, "opacity:1"), (once, "opacity:1")], loop=False),
            text(px, 52, "CLOSING BALANCE", 12, p["ink2"], extra='letter-spacing="2"') +
            f'<rect x="{px}" y="62" width="{pr - px}" height="2" fill="{p["ink"]}"/>'))
    rows = [("Tests across featured repos", "3,100+"), ("Oversold units in a 20-vs-5 race", "0"),
            ("Double charges on retried payments", "0"), ("Unbalanced journals accepted", "0")]
    for i, (label, value) in enumerate(rows):
        y = 98 + i * 44
        t0 = 1.0 + i * 0.35
        s.add(g(rise(t0), text(px, y, label, 14, p["ink2"]) +
                f'<rect x="{px}" y="{y + 14}" width="{pr - px}" height="1" fill="{p["rule"]}"/>'))
        odometer(s, pr, y + 2, value, 30, p["ink"], t0 + 0.2)

    stamp = s.anim(5.0, [(0, "opacity:0;transform:scale(1.9) rotate(-6deg)"),
                         (3.4, "opacity:0;transform:scale(1.9) rotate(-6deg)", "cubic-bezier(.2,1.5,.4,1)"),
                         (3.75, "opacity:1;transform:scale(1) rotate(-6deg)"),
                         (5.0, "opacity:1;transform:scale(1) rotate(-6deg)")],
                   "transform-box:fill-box;transform-origin:center;", loop=False)
    s.add(g(stamp, f'<rect x="976" y="282" width="184" height="42" rx="3" fill="none" stroke="{p["red"]}" '
                   f'stroke-width="3"/>' + text(1068, 311, "BALANCED", 19, p["red"], SANS, 800, "middle",
                                                extra='letter-spacing="3"')))
    return s.render()


def odometer(s, x_right, baseline, value, size, fill, t0):
    """Right-aligned rolling digits that land on `value` (non-digits are static)."""
    lh = size * 1.1
    dw, cw = size * 0.62, size * 0.32
    x = x_right
    cells = []
    for ch in reversed(value):
        w = dw if ch.isdigit() or ch == "+" else cw
        x -= w
        cells.append((ch, x + w / 2))
    for k, (ch, cx) in enumerate(cells):
        if not ch.isdigit():
            s.add(g(s.window(t0 + 1.4, t0 + 1.0, None, 0.3, loop=False), text(cx, baseline, ch, size, fill, SERIF, 700, "middle")))
            continue
        d = int(ch)
        seq = [(d + 1 + i) % 10 for i in range(10)]
        cid = s.uid("o")
        s.defs.append(f'<clipPath id="{cid}"><rect x="{cx - dw / 2 - 1:.1f}" y="{baseline - size * 0.82:.1f}" '
                      f'width="{dw + 2:.1f}" height="{size * 1.02:.1f}"/></clipPath>')
        delay = t0 + k * 0.12
        spin = s.anim(delay + 1.3, [(0, "transform:translateY(0px)"),
                                     (delay, "transform:translateY(0px)", "cubic-bezier(.15,.85,.25,1)"),
                                     (delay + 1.3, f"transform:translateY({-9 * lh:.1f}px)")], loop=False)
        strip = "".join(text(cx, baseline + i * lh, str(n), size, fill, SERIF, 700, "middle") for i, n in enumerate(seq))
        s.add(f'<g clip-path="url(#{cid})"><g class="{spin}">{strip}</g></g>')


# =============================================================================
# CARDS
# =============================================================================
CW, CH = 540, 330


def card(theme, title, tagline, stack, figure, figure_label, label):
    p = THEMES[theme]
    s = SVG(CW, CH, theme, label)
    s.add(f'<rect x="8" y="8" width="528" height="318" rx="4" fill="{p["ink"]}"/>'
          f'<rect x="2" y="2" width="528" height="318" rx="4" fill="{p["paper3"]}" stroke="{p["ink"]}" stroke-width="1.5"/>')
    s.add(text(22, 44, title, 28, p["ink"], SERIF, 700))
    nudge = s.anim(2.4, [(0, "transform:translate(0px,0px)"), (1.6, "transform:translate(0px,0px)"),
                         (1.9, "transform:translate(3px,-3px)"), (2.2, "transform:translate(0px,0px)"),
                         (2.4, "transform:translate(0px,0px)")])
    s.add(text(498, 40, "open repo", 13, p["blue"], SANS, 600, "end"))
    s.add(g(nudge, f'<path d="M503 40 L513 30 M506 30 H513 V37" stroke="{p["blue"]}" stroke-width="1.8" fill="none" '
                   f'stroke-linecap="round"/>'))
    s.add(text(22, 68, tagline, 15, p["ink2"]))
    s.add(f'<rect x="2" y="82" width="528" height="1" fill="{p["rule"]}"/>'
          f'<rect x="2" y="270" width="528" height="1" fill="{p["rule"]}"/>')
    s.add(text(22, 300, stack, 12.5, p["ink2"], MONO))
    s.add(text(516, 296, figure, 26, p["ink"], SERIF, 700, "end"))
    s.add(text(516, 313, figure_label, 11.5, p["ink2"], SANS, 400, "end"))
    return s, p


def card_race(theme):
    s, p = card(theme, "ecommerce-backend", "20 concurrent buyers, last 5 units. Exactly 5 orders.",
                "Java 21 · Spring Boot 4 · MySQL · Redis", "600 tests", "99.3% line coverage",
                "ecommerce-backend: twenty concurrent buyers race for five units and exactly five orders succeed")
    C = 10.0
    typed_line(s, C, 22, 222, "UPDATE product SET stock = stock - 1", 12.5, p["ink"], 0.3, 40, 9.4)
    typed_line(s, C, 22, 240, "WHERE id = ? AND stock >= 1", 12.5, p["ink"], 1.25, 40, 9.4)
    winners = [2, 6, 7, 11, 16]
    stock_t = []
    for i in range(20):
        cx, cy = 38 + (i % 10) * 36, 118 if i < 10 else 158
        t = 2.0 + i * 0.15
        s.add(f'<circle cx="{cx}" cy="{cy}" r="14" fill="none" stroke="{p["ink2"]}" stroke-width="1.2"/>')
        s.add(text(cx, cy + 3.5, f"B{i + 1}", 9.5, p["ink2"], MONO, 600, "middle"))
        ring = s.window(C, t - 0.12, t + 0.12, 0.08)
        s.add(g(ring, f'<circle cx="{cx}" cy="{cy}" r="17" fill="none" stroke="{p["blue"]}" stroke-width="2.5"/>'))
        res = s.window(C, t + 0.1, 9.4, 0.15)
        if i in winners:
            stock_t.append(t + 0.1)
            s.add(g(res, f'<circle cx="{cx}" cy="{cy}" r="14" fill="{p["blue"]}"/>' +
                    text(cx, cy + 3.5, f"B{i + 1}", 9.5, p["on_blue"], MONO, 700, "middle")))
        else:
            s.add(g(res, f'<circle cx="{cx}" cy="{cy}" r="14" fill="{p["red_soft"]}" stroke="{p["red"]}" stroke-width="1.2"/>' +
                    text(cx, cy + 3.5, f"B{i + 1}", 9.5, p["red"], MONO, 600, "middle") +
                    f'<path d="M{cx - 9} {cy + 9} L{cx + 9} {cy - 9}" stroke="{p["red"]}" stroke-width="1.5"/>'))
    # counters
    for label, x, start, step in (("stock", 432, 5, -1), ("orders", 492, 0, 1)):
        s.add(text(x, 172, label, 12, p["ink2"], SANS, 400, "middle"))
        times = [0] + stock_t
        for k in range(6):
            val = start + step * k
            t_in = times[k]
            t_out = times[k + 1] if k < 5 else 9.4
            red = label == "stock" and val == 0
            s.add(g(s.window(C, t_in, t_out, 0.05),
                    text(x, 150, str(val), 44, p["blue"] if (label == "orders" and val == 5) else p["ink"],
                         SERIF, 700, "middle")))
    s.add(g(s.window(C, 5.4, 9.4, 0.3, dy=6),
            text(22, 260, "→ 5 orders · 15 × 409 Conflict · oversold: 0", 13, p["blue"], MONO, 700)))
    return s.render()


def card_ledger(theme):
    s, p = card(theme, "core-banking-ledger", "Double-entry, append-only. Edits are refused by Postgres.",
                "Java 21 · Spring Boot 4 · PostgreSQL · Kafka", "711 tests", "98.5% line coverage",
                "core-banking-ledger: journals post balanced debits and credits; an attempt to edit a ledger row is rejected")
    C = 10.0
    hdr = 12
    s.add(text(22, 104, "JOURNAL", hdr, p["ink2"], MONO, 600, extra='letter-spacing="1"'))
    s.add(text(112, 104, "ACCOUNT", hdr, p["ink2"], MONO, 600, extra='letter-spacing="1"'))
    s.add(text(410, 104, "DEBIT", hdr, p["ink2"], MONO, 600, "end", extra='letter-spacing="1"'))
    s.add(text(510, 104, "CREDIT", hdr, p["ink2"], MONO, 600, "end", extra='letter-spacing="1"'))
    s.add(f'<rect x="22" y="111" width="494" height="1.5" fill="{p["ink"]}"/>')
    rows = [("J0001", "Cash vault (GL)", "10,000", ""), ("", "Asha", "", "10,000"),
            ("J0002", "Asha", "1,500", ""), ("", "Ravi", "", "1,500")]
    for i, (j, acct, dr, cr) in enumerate(rows):
        y = 132 + i * 21
        t = 0.4 + i * 0.45 + (0.3 if i >= 2 else 0)
        s.add(g(s.window(C, t, 9.4, 0.35, dx=-12),
                text(22, y, j, 13, p["ink"], MONO, 600) + text(112, y, acct, 13, p["ink"], MONO) +
                text(410, y, dr, 13, p["ink"], MONO, 400, "end") + text(510, y, cr, 13, p["ink"], MONO, 400, "end")))
    # attack: try to edit a row
    shake = s.anim(C, [(0, "transform:translateX(0px)"), (3.2, "transform:translateX(0px)"),
                       (3.28, "transform:translateX(-6px)"), (3.36, "transform:translateX(6px)"),
                       (3.44, "transform:translateX(-5px)"), (3.52, "transform:translateX(5px)"),
                       (3.6, "transform:translateX(0px)"), (C, "transform:translateX(0px)")])
    s.add(g(s.window(C, 2.5, 4.6, 0.3),
            g(shake, f'<rect x="22" y="222" width="494" height="30" fill="{p["red_soft"]}"/>'
                     f'<rect x="22" y="222" width="3" height="30" fill="{p["red"]}"/>' +
              text(34, 242, "UPDATE ledger_entry SET amount = 0  →  ✗ append-only trigger", 12.5, p["red"], MONO, 600))))
    # trial balance, after the edit was refused
    tb = s.window(C, 4.9, 9.4, 0.3)
    s.add(g(tb, f'<rect x="22" y="219" width="494" height="1.5" fill="{p["ink"]}"/>' +
            text(22, 252, "Trial balance", 14, p["ink"], SANS, 700)))
    s.add(g(tb, text(410, 252, "11,500", 20, p["ink"], SERIF, 700, "end") +
            text(510, 252, "11,500", 20, p["ink"], SERIF, 700, "end")))
    stamp = s.anim(C, [(0, "opacity:0;transform:scale(1.8) rotate(-6deg)"),
                       (6.0, "opacity:0;transform:scale(1.8) rotate(-6deg)", "cubic-bezier(.2,1.5,.4,1)"),
                       (6.3, "opacity:1;transform:scale(1) rotate(-6deg)"), (9.4, "opacity:1;transform:scale(1) rotate(-6deg)"),
                       (9.7, "opacity:0;transform:scale(1) rotate(-6deg)"), (C, "opacity:0;transform:scale(1) rotate(-6deg)")],
                   "transform-box:fill-box;transform-origin:center;")
    s.add(g(stamp, f'<rect x="180" y="234" width="124" height="28" rx="2" fill="none" stroke="{p["red"]}" stroke-width="2.5"/>' +
            text(242, 254, "BALANCED", 14, p["red"], SANS, 800, "middle", extra='letter-spacing="2"')))
    return s.render()


def card_states(theme):
    s, p = card(theme, "CheckoutKit", "A payment state machine you can't push into an illegal state.",
                "Kotlin Multiplatform · Compose · JitPack", "97.5%", "core line coverage",
                "CheckoutKit: a payment moves Created, Processing, Pending, Success, then Refunded; an illegal transition is rejected")
    C = 10.0
    nodes = {"Created": (72, 150), "Processing": (198, 150), "Pending": (324, 150), "Success": (450, 150),
             "Cancelled": (72, 222), "Failed": (198, 222), "Refunded": (450, 222)}
    nw, nh = 104, 30
    s.defs.append(f'<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
                  f'<path d="M0 0 L10 5 L0 10 z" fill="{p["ink2"]}"/></marker>'
                  f'<marker id="arb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
                  f'<path d="M0 0 L10 5 L0 10 z" fill="{p["blue"]}"/></marker>')
    edges = [("Created", "Processing"), ("Processing", "Pending"), ("Pending", "Success"),
             ("Created", "Cancelled"), ("Processing", "Failed"), ("Success", "Refunded")]

    def edge_path(a, b):
        (ax, ay), (bx, by) = nodes[a], nodes[b]
        if ay == by:
            return f"M{ax + nw / 2} {ay} L{bx - nw / 2 - 2} {by}"
        return f"M{ax} {ay + nh / 2} L{bx} {by - nh / 2 - 2}"

    for a, b in edges:
        s.add(f'<path d="{edge_path(a, b)}" stroke="{p["ink2"]}" stroke-width="1.3" fill="none" marker-end="url(#ar)"/>')
    for name, (x, y) in nodes.items():
        s.add(f'<rect x="{x - nw / 2}" y="{y - nh / 2}" width="{nw}" height="{nh}" rx="15" fill="{p["paper3"]}" '
              f'stroke="{p["ink"]}" stroke-width="1.2"/>' + text(x, y + 4.5, name, 12.5, p["ink"], MONO, 600, "middle"))
    timeline = [("Created", 0.4, 1.4), ("Processing", 1.4, 2.4), ("Pending", 2.4, 3.4), ("Success", 3.4, 7.2),
                ("Refunded", 7.2, 9.4)]
    for name, t_in, t_out in timeline:
        x, y = nodes[name]
        s.add(g(s.window(C, t_in, t_out, 0.15),
                f'<rect x="{x - nw / 2}" y="{y - nh / 2}" width="{nw}" height="{nh}" rx="15" fill="{p["blue"]}"/>' +
                text(x, y + 4.5, name, 12.5, p["on_blue"], MONO, 700, "middle")))
    for (a, b), t in ((("Created", "Processing"), 1.25), (("Processing", "Pending"), 2.25),
                      (("Pending", "Success"), 3.25), (("Success", "Refunded"), 7.05)):
        s.add(g(s.window(C, t, t + 0.45, 0.1),
                f'<path d="{edge_path(a, b)}" stroke="{p["blue"]}" stroke-width="3" fill="none" marker-end="url(#arb)"/>'))
    # illegal attempt
    shake = s.anim(C, [(0, "transform:translateX(0px)"), (5.0, "transform:translateX(0px)"),
                       (5.08, "transform:translateX(-5px)"), (5.16, "transform:translateX(5px)"),
                       (5.24, "transform:translateX(-4px)"), (5.32, "transform:translateX(0px)"),
                       (C, "transform:translateX(0px)")])
    s.add(g(s.window(C, 4.4, 6.7, 0.3),
            g(shake, f'<path d="M450 134 C 400 96, 250 96, 204 132" stroke="{p["red"]}" stroke-width="2.2" fill="none" '
                     f'stroke-dasharray="6 5"/>' +
              f'<path d="M196 126 L212 140 M212 126 L196 140" stroke="{p["red"]}" stroke-width="2.6"/>' +
              text(326, 98, "SUCCESS → PROCESSING", 12, p["red"], MONO, 700, "middle"))))
    s.add(g(s.window(C, 4.4, 6.7, 0.3),
            text(22, 258, "✗ IllegalTransition · compare-and-set left it untouched", 12.5, p["red"], MONO, 600)))
    s.add(g(s.window(C, 0.2, 4.0, 0.3), text(22, 258, "all 49 state × event pairs tested exhaustively", 12.5, p["ink2"], MONO)))
    s.add(g(s.window(C, 6.9, 9.4, 0.3), text(22, 258, "refund settles · 0 'failed but captured' under 8 s spikes", 12.5,
                                              p["blue"], MONO, 600)))
    return s.render()


def card_retry(theme):
    s, p = card(theme, "PayFlow", "Pay ₹499, lose the response twice. Charged exactly once.",
                "Kotlin · Compose · Room · ML Kit", "1,000", "concurrent payments · 0 duplicates",
                "PayFlow: a payment request is retried twice after lost responses and the customer is charged once")
    C = 10.0
    # phone
    s.add(f'<rect x="22" y="98" width="76" height="140" rx="12" fill="{p["ink"]}"/>'
          f'<rect x="28" y="110" width="64" height="116" rx="6" fill="{p["paper"]}"/>'
          f'<rect x="50" y="102" width="20" height="3" rx="1.5" fill="{p["paper"]}" opacity=".5"/>')
    s.add(text(60, 130, "₹499", 17, p["ink"], SERIF, 700, "middle"))
    for msg, t_in, t_out, col in (("paying…", 0.4, 2.5, p["ink2"]), ("retrying…", 2.5, 7.6, p["red"]),
                                  ("Paid ✓", 7.6, 9.4, p["blue"])):
        s.add(g(s.window(C, t_in, t_out, 0.15), text(60, 176, msg, 12, col, SANS, 700, "middle")))
    # server
    s.add(f'<rect x="384" y="98" width="132" height="140" rx="6" fill="{p["paper"]}" stroke="{p["ink"]}" stroke-width="1.3"/>')
    s.add(text(450, 118, "PSP", 13, p["ink2"], MONO, 700, "middle", extra='letter-spacing="2"'))
    s.add(text(400, 148, "charges", 12, p["ink2"]))
    s.add(g(s.window(C, 0, 1.35, 0.01), text(500, 152, "0", 26, p["ink"], SERIF, 700, "end")))
    s.add(g(s.window(C, 1.35, 9.4, 0.15), text(500, 152, "1", 26, p["blue"], SERIF, 700, "end")))
    for k, (msg, t) in enumerate((("#1 charged ₹499", 1.35), ("#2 replayed", 3.95), ("#3 replayed", 6.55))):
        s.add(g(s.window(C, t, 9.4, 0.2, dx=-6), text(396, 176 + k * 18, msg, 10.5, p["blue"] if k == 0 else p["ink2"], MONO, 600)))
    # lanes
    s.add(f'<path d="M106 140 H376" stroke="{p["rule"]}" stroke-width="1.5" stroke-dasharray="3 4"/>'
          f'<path d="M376 200 H106" stroke="{p["rule"]}" stroke-width="1.5" stroke-dasharray="3 4"/>')
    for k in range(3):
        t = 0.5 + k * 2.6
        req_w = 150
        move = s.anim(C, [(0, "transform:translateX(0px)"), (t, "transform:translateX(0px)", "cubic-bezier(.4,0,.2,1)"),
                          (t + 0.8, f"transform:translateX({376 - 106 - req_w}px)"), (C, f"transform:translateX({376 - 106 - req_w}px)")])
        s.add(g(s.window(C, t, t + 0.85, 0.08),
                g(move, f'<rect x="106" y="129" width="{req_w}" height="22" rx="11" fill="{p["ink"]}"/>' +
                  text(106 + req_w / 2, 144, "POST /pay · key 7f3a", 11, p["paper"], MONO, 600, "middle"))))
        resp_w = 86
        lost = k < 2
        end = 106 + (376 - 106 - resp_w) * (0.45 if lost else 0.0)
        move2 = s.anim(C, [(0, "transform:translateX(0px)"), (t + 1.1, "transform:translateX(0px)", "linear"),
                           (t + (1.6 if lost else 1.9), f"transform:translateX({end - (376 - resp_w):.0f}px)"),
                           (C, f"transform:translateX({end - (376 - resp_w):.0f}px)")])
        s.add(g(s.window(C, t + 1.1, t + (1.65 if lost else 1.95), 0.08),
                g(move2, f'<rect x="{376 - resp_w}" y="189" width="{resp_w}" height="22" rx="11" fill="{p["blue"]}"/>' +
                  text(376 - resp_w / 2, 204, "200 Paid", 11, p["on_blue"], MONO, 700, "middle"))))
        if lost:
            cx = end + resp_w / 2
            s.add(g(s.window(C, t + 1.6, t + 2.3, 0.1),
                    f'<path d="M{cx - 9} 191 L{cx + 9} 209 M{cx + 9} 191 L{cx - 9} 209" stroke="{p["red"]}" stroke-width="3"/>' +
                    text(cx, 228, "4G dropped", 11, p["red"], MONO, 600, "middle")))
    s.add(g(s.window(C, 7.7, 9.4, 0.3, dy=6),
            text(22, 260, "requests 3 · charges 1 · Idempotent-Replayed: true", 13, p["blue"], MONO, 700)))
    return s.render()


def card_recon(theme):
    s, p = card(theme, "transaction-reconciliation-batch", "Every line matched or explained. Restarts never double-post.",
                "Java 21 · Spring Batch · PostgreSQL", "309 tests", "97.0% line coverage",
                "transaction-reconciliation-batch: ledger lines are matched to a bank statement and three breaks are classified")
    C = 10.0
    s.add(text(22, 104, "LEDGER", 12, p["ink2"], MONO, 700, extra='letter-spacing="1"'))
    s.add(text(516, 104, "BANK STATEMENT", 12, p["ink2"], MONO, 700, "end", extra='letter-spacing="1"'))
    left = [("TX-1041", "2,000.00"), ("TX-1042", "450.00"), ("TX-1043", "1,250.00"), ("TX-1044", "999.00"), ("TX-1045", "310.00")]
    right = [("TX-1041", "2,000.00"), ("TX-1042", "450.00"), ("TX-1043", "1,249.50"), ("TX-1045", "310.00"), ("TX-1046", "75.00")]
    ys = [126 + i * 22 for i in range(5)]
    for i in range(5):
        t = 0.3 + i * 0.18
        s.add(g(s.window(C, t, 9.4, 0.3, dx=-10),
                text(22, ys[i], left[i][0], 12.5, p["ink"], MONO, 600) + text(200, ys[i], "₹" + left[i][1], 12.5, p["ink"], MONO, 400, "end")))
        s.add(g(s.window(C, t + 0.09, 9.4, 0.3, dx=10),
                text(338, ys[i], right[i][0], 12.5, p["ink"], MONO, 600) + text(516, ys[i], "₹" + right[i][1], 12.5, p["ink"], MONO, 400, "end")))
    links = [(0, 0, "ok"), (1, 1, "ok"), (2, 2, "bad"), (4, 3, "ok")]
    for k, (a, b, kind) in enumerate(links):
        y1, y2 = ys[a] - 4, ys[b] - 4
        length = ((330 - 208) ** 2 + (y2 - y1) ** 2) ** 0.5 + 2
        t = 1.7 + k * 0.45
        col = p["blue"] if kind == "ok" else p["red"]
        draw = s.anim(C, [(0, f"stroke-dashoffset:{length:.0f};opacity:1"), (t, f"stroke-dashoffset:{length:.0f};opacity:1", "ease-out"),
                          (t + 0.4, "stroke-dashoffset:0;opacity:1"), (9.4, "stroke-dashoffset:0;opacity:1"),
                          (9.7, "stroke-dashoffset:0;opacity:0"), (C, f"stroke-dashoffset:{length:.0f};opacity:0")])
        s.add(f'<path class="{draw}" d="M208 {y1} L330 {y2}" stroke="{col}" stroke-width="2" fill="none" '
              f'stroke-dasharray="{length:.0f}"/>')
    # breaks
    hl = s.window(C, 3.6, 9.4, 0.3)
    s.add(g(hl, f'<rect x="18" y="{ys[2] - 15}" width="186" height="20" fill="none" stroke="{p["red"]}" stroke-width="1.5"/>'
                f'<rect x="334" y="{ys[2] - 15}" width="186" height="20" fill="none" stroke="{p["red"]}" stroke-width="1.5"/>'))
    s.add(g(s.window(C, 4.0, 9.4, 0.3),
            f'<rect x="18" y="{ys[3] - 15}" width="186" height="20" fill="{p["red_soft"]}" opacity=".7"/>' +
            text(22, ys[3], left[3][0], 12.5, p["red"], MONO, 700) + text(200, ys[3], "₹" + left[3][1], 12.5, p["red"], MONO, 600, "end") +
            f'<rect x="334" y="{ys[4] - 15}" width="186" height="20" fill="{p["red_soft"]}" opacity=".7"/>' +
            text(338, ys[4], right[4][0], 12.5, p["red"], MONO, 700) + text(516, ys[4], "₹" + right[4][1], 12.5, p["red"], MONO, 600, "end")))
    s.add(g(s.window(C, 4.4, 9.4, 0.3, dy=6),
            text(22, 240, "3 breaks: AMOUNT_MISMATCH ₹0.50 · NOT_ON_STATEMENT · UNBOOKED", 12, p["red"], MONO, 700)))
    # progress bar
    s.add(f'<rect x="22" y="252" width="494" height="6" rx="3" fill="{p["paper2"]}"/>')
    fill = s.anim(C, [(0, "transform:scaleX(0)"), (0.4, "transform:scaleX(0)", "cubic-bezier(.3,0,.2,1)"),
                      (4.4, "transform:scaleX(1)"), (9.4, "transform:scaleX(1)"), (9.8, "transform:scaleX(0)"), (C, "transform:scaleX(0)")],
                  "transform-box:fill-box;transform-origin:0 50%;")
    s.add(f'<rect class="{fill}" x="22" y="252" width="494" height="6" rx="3" fill="{p["blue"]}"/>')
    s.add(g(s.window(C, 0.4, 4.0, 0.3), text(516, 247, "1,000,000 rows · exactly once", 10.5, p["ink2"], MONO, 400, "end")))
    return s.render()


# =============================================================================
# TERMINAL
# =============================================================================
def terminal(theme):
    p = THEMES[theme]
    W, H = 1200, 360
    s = SVG(W, H, theme, "Terminal: a retried order is replayed, not charged twice; an edit to the ledger is refused; "
                         "711 tests pass with 98.5 percent coverage")
    s.add(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12" fill="{p["term_bg"]}" stroke="{p["term_border"]}" stroke-width="1.5"/>')
    for i, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        s.add(f'<circle cx="{28 + i * 22}" cy="26" r="6.5" fill="{c}"/>')
    s.add(text(W / 2, 31, "darshan@ledger: ~/systems", 13, p["term_dim"], MONO, 400, "middle"))
    s.add(f'<rect x="1" y="48" width="{W - 2}" height="1" fill="{p["term_border"]}"/>')
    C = 17.0
    size, lh, x = 16.5, 30, 34
    script = [
        ("cmd", 'curl -X POST /api/v1/me/orders -H "Idempotency-Key: 7f3a" -d @cart.json'),
        ("ok", "HTTP/1.1 201 Created"),
        ("cmd", 'curl -X POST /api/v1/me/orders -H "Idempotency-Key: 7f3a" -d @cart.json  # 4G dropped, retry'),
        ("ok", "HTTP/1.1 201 Created   Idempotent-Replayed: true   (same order, no second charge)"),
        ("cmd", 'psql -c "UPDATE ledger_entry SET amount = 0 WHERE id = 1"'),
        ("err", "ERROR:  ledger_entry is append-only (trigger rejects UPDATE, DELETE, TRUNCATE)"),
        ("cmd", "./mvnw verify"),
        ("ok", "Tests run: 711, Failures: 0, Errors: 0 · line coverage 98.5% (gate 95%) · BUILD SUCCESS"),
    ]
    t = 0.5
    end = C - 0.6
    for i, (kind, line) in enumerate(script):
        y = 84 + i * lh
        if kind == "cmd":
            s.add(g(s.window(C, t, end, 0.01), text(x, y, "$", size, p["term_prompt"], MONO, 700)))
            t = typed_line(s, C, x + MONO_W * size * 2, y, line, size, p["term_fg"], t, 42, end,
                           caret=p["term_fg"], caret_linger=0.35)
            t += 0.35
        else:
            col = {"ok": p["term_ok"], "err": p["term_err"]}[kind]
            s.add(g(s.window(C, t, end, 0.05), text(x, y, line, size, col, MONO, 600, extra='xml:space="preserve"')))
            t += 0.9 if i < len(script) - 1 else 0.3
    y = 84 + len(script) * lh
    s.add(g(s.window(C, t, end, 0.01), text(x, y, "$", size, p["term_prompt"], MONO, 700)))
    blink = s.anim(1.0, [(0, "opacity:1"), (0.5, "opacity:1", "steps(1,end)"), (0.5001, "opacity:0"), (1.0, "opacity:0")])
    s.add(g(s.window(C, t, end, 0.01), g(blink, f'<rect x="{x + MONO_W * size * 2}" y="{y - size * 0.85:.1f}" '
                                                f'width="{size * 0.55:.1f}" height="{size}" fill="{p["term_fg"]}"/>')))
    return s.render()


# =============================================================================
# STACK MARQUEE
# =============================================================================
def marquee(theme):
    p = THEMES[theme]
    W, H = 1200, 112
    s = SVG(W, H, theme, "Stack: Java 21, Spring Boot, Spring Batch, PostgreSQL, MySQL, Redis, Kafka, Testcontainers, "
                         "Kotlin, Jetpack Compose, Kotlin Multiplatform, Room, WorkManager, Firebase, Flutter, Docker")
    s.defs.append('<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  '<stop offset=".08" stop-color="#fff"/><stop offset=".92" stop-color="#fff"/>'
                  '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                  f'<mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>')
    rows = [
        ["Java 21", "Spring Boot 4", "Spring Security", "Spring Batch", "PostgreSQL", "MySQL", "Redis", "Kafka",
         "Flyway", "Testcontainers", "JUnit 5", "ArchUnit", "JaCoCo", "Docker", "Prometheus"],
        ["Kotlin", "Jetpack Compose", "Kotlin Multiplatform", "Hilt", "Room", "WorkManager", "CameraX", "ML Kit",
         "Keystore", "Firebase", "FCM", "Flutter", "Kover", "JitPack", "Python"],
    ]
    size = 14
    for r, items in enumerate(rows):
        y = 14 + r * 50
        pills, x = [], 0
        for it in items:
            w = MONO_W * size * len(it) + 30
            accent = p["blue"] if r == 0 else p["ink"]
            pills.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="34" rx="17" fill="{p["paper3"]}" '
                         f'stroke="{accent}" stroke-width="1.3"/>' +
                         f'<circle cx="{x + 15:.1f}" cy="{y + 17}" r="3.5" fill="{accent}"/>' +
                         text(x + 24, y + 22, it, size, p["ink"], MONO, 600))
            x += w + 12
        setw = x
        speed = 45
        a, b = (0, -setw) if r == 0 else (-setw, 0)
        mv = s.anim(setw / speed, [(0, f"transform:translateX({a:.1f}px)"), (setw / speed, f"transform:translateX({b:.1f}px)")])
        strip = "".join(pills)
        s.add(f'<g mask="url(#m)"><g class="{mv}">{strip}<g transform="translate({setw:.1f} 0)">{strip}</g>'
              f'<g transform="translate({2 * setw:.1f} 0)">{strip}</g></g></g>')
    return s.render()


# =============================================================================
# BUTTON
# =============================================================================
def button(theme, label, w=380):
    p = THEMES[theme]
    H = 70
    s = SVG(w, H, theme, label)
    ring = s.anim(2.2, [(0, "transform:scale(1);opacity:.7"), (1.6, "transform:scale(1.06,1.35);opacity:0"),
                        (2.2, "transform:scale(1.06,1.35);opacity:0")], "transform-box:fill-box;transform-origin:center;")
    s.add(f'<rect class="{ring}" x="10" y="12" width="{w - 20}" height="46" rx="23" fill="none" stroke="{p["blue"]}" stroke-width="2"/>')
    s.add(f'<rect x="10" y="12" width="{w - 20}" height="46" rx="23" fill="{p["ink"]}"/>')
    bob = s.anim(1.1, [(0, "transform:translateX(0px)"), (0.55, "transform:translateX(3px)"), (1.1, "transform:translateX(0px)")])
    s.add(g(bob, f'<path d="M36 25 L54 35 L36 45 Z" fill="{p["paper"]}"/>'))
    s.add(text(66, 41, label, 17, p["paper"], SANS, 700))
    return s.render()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        files = {
            f"hero-{theme}.svg": hero(theme),
            f"card-race-{theme}.svg": card_race(theme),
            f"card-ledger-{theme}.svg": card_ledger(theme),
            f"card-states-{theme}.svg": card_states(theme),
            f"card-retry-{theme}.svg": card_retry(theme),
            f"card-recon-{theme}.svg": card_recon(theme),
            f"terminal-{theme}.svg": terminal(theme),
            f"stack-{theme}.svg": marquee(theme),
            f"cta-{theme}.svg": button(theme, "Play with the systems live"),
        }
        for name, svg in files.items():
            (OUT / name).write_text(svg, encoding="utf-8")
            print(f"{name:28s} {len(svg) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
