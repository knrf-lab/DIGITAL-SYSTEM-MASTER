"""Generate (and verify) every computed piece of the binder.

Everything that is maths is checked here before it is written:
  * derivation steps: every line must have the same truth table as the line before
  * K-map groups: every group must sit on 1s/Xs only, groups must cover all 1s,
    and the final expression must equal the function
  * truth tables, case studies, mock-exam answers: recomputed from the rules
Output: gen/*.html fragments and svg/*.svg, included by build.js.
"""
import itertools
import os
import re

os.makedirs("gen", exist_ok=True)
os.makedirs("svg", exist_ok=True)
CHECKS = 0


def check(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        raise SystemExit("CHECK FAILED: " + msg)


def out(name, html):
    open(f"gen/{name}.html", "w").write(html)


def outsvg(name, svg):
    open(f"svg/{name}.svg", "w").write(svg)


# ---------------------------------------------------------------- expressions
# Syntax: single-letter variables, 0 1, postfix ' = NOT, juxtaposition or . = AND,
# + = OR, ^ = XOR, ( ) or [ ] grouping.
class E:
    def __init__(self, op, *a):
        self.op, self.a = op, a


def parse(s):
    s = re.sub(r"\s", "", s).replace("[", "(").replace("]", ")")
    pos = [0]

    def peek():
        return s[pos[0]] if pos[0] < len(s) else ""

    def orx():
        xs = [xorx()]
        while peek() == "+":
            pos[0] += 1
            xs.append(xorx())
        return xs[0] if len(xs) == 1 else E("or", *xs)

    def xorx():
        xs = [andx()]
        while peek() == "^":
            pos[0] += 1
            xs.append(andx())
        return xs[0] if len(xs) == 1 else E("xor", *xs)

    def andx():
        xs = [post()]
        while peek() and peek() not in "+)^":
            if peek() == ".":
                pos[0] += 1
            xs.append(post())
        return xs[0] if len(xs) == 1 else E("and", *xs)

    def post():
        x = atom()
        while peek() == "'":
            pos[0] += 1
            x = E("not", x)
        return x

    def atom():
        c = peek()
        pos[0] += 1
        if c == "(":
            x = orx()
            assert peek() == ")", s
            pos[0] += 1
            return E("grp", x)
        if c in "01":
            return E("const", int(c))
        if c.isalpha():
            return E("var", c)
        raise ValueError(f"parse error in {s!r} at {pos[0]}")

    x = orx()
    assert pos[0] == len(s), s
    return x


def ev(x, env):
    o = x.op
    if o == "var":
        return env[x.a[0]]
    if o == "const":
        return x.a[0]
    if o == "grp":
        return ev(x.a[0], env)
    if o == "not":
        return 1 - ev(x.a[0], env)
    if o == "and":
        return int(all(ev(y, env) for y in x.a))
    if o == "or":
        return int(any(ev(y, env) for y in x.a))
    if o == "xor":
        v = 0
        for y in x.a:
            v ^= ev(y, env)
        return v


def varsof(x, acc=None):
    acc = set() if acc is None else acc
    if x.op == "var":
        acc.add(x.a[0])
    for y in x.a:
        if isinstance(y, E):
            varsof(y, acc)
    return acc


def strip(x):
    while x.op == "grp":
        x = x.a[0]
    return x


def tex(x):
    o = x.op
    if o == "var":
        return x.a[0]
    if o == "const":
        return str(x.a[0])
    if o == "grp":
        return r"\left(" + tex(x.a[0]) + r"\right)"
    if o == "not":
        inner = strip(x.a[0])
        if inner.op in ("var", "const"):
            return r"\bar{" + tex(inner) + "}"
        return r"\overline{" + tex(inner) + "}"
    if o == "and":
        return r"\,".join(tex(y) for y in x.a)
    if o == "or":
        return " + ".join(tex(y) for y in x.a)
    if o == "xor":
        return r" \oplus ".join(tex(y) for y in x.a)


def T(s):
    """LaTeX for an expression string."""
    return tex(parse(s))


def minterms(s, names):
    x = parse(s)
    n = len(names)
    return {m for m in range(2 ** n) if ev(x, {names[j]: (m >> (n - 1 - j)) & 1 for j in range(n)})}


def deriv(name, steps, names=None, title=None):
    """steps: [(expr, law), ...]. Every step must equal the previous one."""
    if names is None:
        vs = set()
        for e, _ in steps:
            vs |= varsof(parse(e))
        names = sorted(vs)
    ref = minterms(steps[0][0], names)
    for e, law in steps[1:]:
        check(minterms(e, names) == ref, f"{name}: step {e!r} ({law}) differs from {steps[0][0]!r}")
    rows = []
    for i, (e, law) in enumerate(steps):
        eq = "" if i == 0 else "="
        cls = ' class="last"' if i == len(steps) - 1 and i else ""
        rows.append(f"<tr{cls}><td class='eq'>{eq}</td><td>\\({T(e)}\\)</td><td class='law'>{law}</td></tr>")
    h = f"<table class='deriv'>{''.join(rows)}</table>"
    out(name, h)
    return h


# ------------------------------------------------------------- minimisation
def qm(ones, dc, n):
    terms = {(m, 0) for m in ones | dc}
    primes = set()
    while terms:
        nxt, used = set(), set()
        for a, b in itertools.combinations(terms, 2):
            if a[1] == b[1]:
                d = a[0] ^ b[0]
                if d and d & (d - 1) == 0 and not (d & a[1]):
                    nxt.add((a[0] & ~d, a[1] | d))
                    used |= {a, b}
        primes |= terms - used
        terms = nxt
    return list(primes)


def min_literals(ones, dc, n):
    """Smallest literal count of any SOP cover (used to prove our groupings are minimal)."""
    if not ones:
        return 0
    primes = qm(ones, dc, n)
    cov = lambda p: {m for m in ones if m & ~p[1] == p[0] & ~p[1]}
    for k in range(1, len(primes) + 1):
        best = None
        for combo in itertools.combinations(primes, k):
            if set().union(*[cov(p) for p in combo]) >= ones:
                lit = sum(n - bin(p[1]).count("1") for p in combo)
                best = lit if best is None else min(best, lit)
        if best is not None:
            return best


# ------------------------------------------------------------------ K-maps
GRAY = [0, 1, 3, 2]
COLORS = ["#7b3fbf", "#00897b", "#ef6c00", "#1e66d0", "#d81b60", "#43a047", "#8d6e63"]


def term_cells(term, names):
    """'ab'' -> set of minterms covered by the product term."""
    n = len(names)
    lits = re.findall(r"([A-Za-z])('?)", term)
    want = {v: (0 if p else 1) for v, p in lits}
    cells = set()
    for m in range(2 ** n):
        if all(((m >> (n - 1 - names.index(v))) & 1) == b for v, b in want.items()):
            cells.add(m)
    return cells


def prod_tex(term):
    if term == "1":
        return "1"
    return "".join(("\\bar{" + v + "}") if p else v for v, p in re.findall(r"([A-Za-z])('?)", term))


def sum_tex(term):
    """zero-group product term of F' -> maxterm sum for F (complement every literal)."""
    lits = re.findall(r"([A-Za-z])('?)", term)
    return "(" + " + ".join((v if p else "\\bar{" + v + "}") for v, p in lits) + ")"


def layout(n):
    """rows/cols of minterm indices + header labels."""
    if n == 2:
        return [[0, 1], [2, 3]], ["0", "1"], ["0", "1"]
    if n == 3:
        return [[GRAY[c] for c in range(4)], [4 + GRAY[c] for c in range(4)]], ["0", "1"], ["00", "01", "11", "10"]
    if n == 4:
        g = ["00", "01", "11", "10"]
        return [[GRAY[r] * 4 + GRAY[c] for c in range(4)] for r in range(4)], g, g


def kmap(names, ones, dc=frozenset(), groups=(), mode="sop", small=False, title="", offset=0, show_idx=True):
    """groups: list of product terms (for SOP: over 1s; for POS: product terms of F' over 0s)."""
    n = len(names)
    zeros = set(range(2 ** n)) - set(ones) - set(dc)
    target, allowed = (set(ones), set(ones) | set(dc)) if mode == "sop" else (zeros, zeros | set(dc))
    cellsets = []
    for g in groups:
        c = term_cells(g, names)
        check(c <= allowed, f"group {g} in {title} covers a forbidden cell {sorted(c - allowed)}")
        check(len(c) & (len(c) - 1) == 0, f"group {g} size not power of 2")
        cellsets.append(c)
    if groups:
        check(set().union(*cellsets) >= target, f"{title}: groups {groups} miss cells {sorted(target - set().union(*cellsets))}")
        lits = sum(len(re.findall(r"[A-Za-z]", g)) for g in groups)
        check(lits == min_literals(target, set(dc), n), f"{title}: grouping {groups} is not minimal")
    rows, rl, cl = layout(n)
    rv = names[0] if n <= 3 else names[0] + names[1]
    cv = names[1] if n == 2 else (names[1] + names[2] if n == 3 else names[2] + names[3])
    h = [f"<table class='kmap{' small' if small else ''}'>"]
    h.append(f"<tr><th class='corner'><span class='cv'>{cv}</span><span class='rv'>{rv}</span></th>" +
             "".join(f"<th>{c}</th>" for c in cl) + "</tr>")
    for r, row in enumerate(rows):
        h.append(f"<tr><th>{rl[r]}</th>")
        for m in row:
            v = "1" if m in ones else ("X" if m in dc else "0")
            shadows, w = [], 0
            for gi, c in enumerate(cellsets):
                if m in c:
                    w += 2.2
                    shadows.append(f"inset 0 0 0 {w:.1f}px {COLORS[gi % len(COLORS)]}")
                    w += 0.6
                    shadows.append(f"inset 0 0 0 {w:.1f}px #fff")
            st = f" style='box-shadow:{','.join(shadows)}'" if shadows else ""
            cls = {"1": "one", "X": "dc", "0": "zero"}[v]
            if mode == "pos" and v == "0":
                cls = "one"
            if mode == "pos" and v == "1":
                cls = "zero"
            idx = f"<span class='idx'>{m + offset}</span>" if show_idx else ""
            h.append(f"<td class='{cls}'{st}>{idx}{v}</td>")
        h.append("</tr>")
    h.append("</table>")
    legend = ""
    if groups:
        items = []
        for gi, g in enumerate(groups):
            t = prod_tex(g) if mode == "sop" else sum_tex(g)
            items.append(f"<span class='lg'><i style='background:{COLORS[gi % len(COLORS)]}'></i>\\({t}\\)</span>")
        legend = "<div class='legend'>" + " ".join(items) + "</div>"
    return "<div class='kwrap'>" + (f"<div class='kt'>{title}</div>" if title else "") + "".join(h) + legend + "</div>"


def result(names, ones, dc, groups, mode="sop"):
    """verify the expression built from groups equals the function, return its LaTeX."""
    n = len(names)
    if mode == "sop":
        expr = " + ".join(groups)
        got = minterms(expr, names)
        check(got - set(dc) == set(ones) and got >= set(ones), f"SOP {expr} wrong")
        return " + ".join(prod_tex(g) for g in groups)
    zeros = set(range(2 ** n)) - set(ones) - set(dc)
    fbar = minterms(" + ".join(groups), names)
    check(fbar - set(dc) == zeros and fbar >= zeros, f"POS groups {groups} wrong")
    return "".join(sum_tex(g) for g in groups)


def truth_table(names, cols, highlight=None, extra=None, idx=True):
    """cols: list of (header, list of 2^n values). extra: list of per-row notes."""
    n = len(names)
    h = ["<table class='tt'><thead><tr>" + ("<th class='ix'>#</th>" if idx else "") +
         "".join(f"<th>{v}</th>" for v in names) + "<th class='sep'></th>" +
         "".join(f"<th>{c}</th>" for c, _ in cols) + ("<th>alasan / why</th>" if extra else "") + "</tr></thead><tbody>"]
    for m in range(2 ** n):
        bits = [(m >> (n - 1 - j)) & 1 for j in range(n)]
        hl = any(v[m] == 1 for _, v in cols[:1])
        h.append(f"<tr{' class=hl' if hl else ''}>" + (f"<td class='ix'>{m}</td>" if idx else "") +
                 "".join(f"<td>{b}</td>" for b in bits) + "<td class='sep'></td>" +
                 "".join(f"<td class='o'>{v[m]}</td>" for _, v in cols) +
                 (f"<td class='note'>{extra[m]}</td>" if extra else "") + "</tr>")
    h.append("</tbody></table>")
    return "".join(h)


def canon(names, ones):
    n = len(names)
    sop, pos = [], []
    for m in range(2 ** n):
        bits = [(m >> (n - 1 - j)) & 1 for j in range(n)]
        if m in ones:
            sop.append("".join(v if b else "\\bar{" + v + "}" for v, b in zip(names, bits)))
        else:
            pos.append("(" + " + ".join(("\\bar{" + v + "}") if b else v for v, b in zip(names, bits)) + ")")
    return " + ".join(sop), "".join(pos)


# ------------------------------------------------------------------- SVG art
def gate_path(kind, x, y, w=34, h=26):
    """gate body with left edge at x, vertical centre y. Returns (svg, output_x)."""
    top, bot = y - h / 2, y + h / 2
    bubble = kind in ("nand", "nor", "xnor", "not")
    base = {"nand": "and", "nor": "or", "xnor": "xor"}.get(kind, kind)
    s = ""
    if base == "and":
        s = f"<path d='M{x},{top} H{x + w / 2} A{h / 2},{h / 2} 0 0 1 {x + w / 2},{bot} H{x} Z' class='g'/>"
        ox = x + w / 2 + h / 2
    elif base in ("or", "xor"):
        s = (f"<path d='M{x},{top} Q{x + w * 0.55},{top} {x + w + 2},{y} Q{x + w * 0.55},{bot} {x},{bot} "
             f"Q{x + 9},{y} {x},{top} Z' class='g'/>")
        if base == "xor":
            s += f"<path d='M{x - 5},{top} Q{x + 4},{y} {x - 5},{bot}' class='g' fill='none'/>"
        ox = x + w + 2
    elif base == "not":
        s = f"<path d='M{x},{top + 3} L{x + w - 10},{y} L{x},{bot - 3} Z' class='g'/>"
        ox = x + w - 10
    if bubble:
        s += f"<circle cx='{ox + 3}' cy='{y}' r='3' class='g'/>"
        ox += 6
    return s, ox


SVG_STYLE = ("<style>.g{fill:#fff;stroke:#1a1a1a;stroke-width:1.6}.w{stroke:#1a1a1a;stroke-width:1.2;fill:none}"
             ".t{font:11px DejaVu Sans,sans-serif}.ts{font:9px DejaVu Sans,sans-serif;fill:#555}"
             ".tb{font:bold 12px DejaVu Sans,sans-serif}.d{fill:#1a1a1a}</style>")


def gate_icons():
    for kind in ["and", "or", "not", "nand", "nor", "xor", "xnor"]:
        g, ox = gate_path(kind, 14, 18)
        ins = f"<line x1='0' y1='18' x2='16' y2='18' class='w'/>" if kind == "not" else \
              "<line x1='0' y1='11' x2='17' y2='11' class='w'/><line x1='0' y1='25' x2='17' y2='25' class='w'/>"
        outsvg("gate_" + kind, f"<svg xmlns='http://www.w3.org/2000/svg' width='86' height='36' viewBox='0 0 86 36'>{SVG_STYLE}"
               f"{ins}{g}<line x1='{ox}' y1='18' x2='84' y2='18' class='w'/></svg>")


def sop_circuit(name, names, terms, out_label="y", width=None):
    """Two-level AND-OR circuit. terms: list of product terms like "ab'"."""
    parsed = [re.findall(r"([A-Za-z])('?)", t) for t in terms]
    need_bar = {v for p in parsed for v, b in p if b}
    rails, x = {}, 18
    for v in names:
        rails[v] = x
        x += 22 if v in need_bar else 0
        if v in need_bar:
            rails[v + "'"] = x
        x += 26
    rails_end = x
    and_x = rails_end + 12
    gap = 16 + 9 * max(len(p) for p in parsed)
    y0 = 92
    s = []
    total_h = y0 + gap * len(terms) + 10
    for v in names:
        rx = rails[v]
        s.append(f"<text x='{rx - 4}' y='14' class='tb'>{v}</text>")
        s.append(f"<line x1='{rx}' y1='20' x2='{rx}' y2='{total_h - 8}' class='w'/>")
        if v in need_bar:
            bx = rails[v + "'"]
            s.append(f"<line x1='{rx}' y1='30' x2='{bx}' y2='30' class='w'/><circle cx='{rx}' cy='30' r='2.4' class='d'/>")
            s.append(f"<path d='M{bx - 7},34 L{bx + 7},34 L{bx},50 Z' class='g'/><circle cx='{bx}' cy='53' r='3' class='g'/>")
            s.append(f"<line x1='{bx}' y1='56' x2='{bx}' y2='{total_h - 8}' class='w'/>")
            s.append(f"<text x='{bx + 4}' y='70' class='t'>{v}\u0305</text>")
    outs = []
    for i, p in enumerate(parsed):
        yc = y0 + i * gap
        if len(p) == 1:
            v, b = p[0]
            rx = rails[v + ("'" if b else "")]
            s.append(f"<circle cx='{rx}' cy='{yc}' r='2.4' class='d'/>")
            outs.append((rx, yc))
            continue
        h = max(26, 9 * len(p) + 8)
        g, ox = gate_path("and", and_x, yc, 34, h)
        for k, (v, b) in enumerate(p):
            iy = yc - (len(p) - 1) * 9 / 2 + k * 9
            rx = rails[v + ("'" if b else "")]
            s.append(f"<line x1='{rx}' y1='{iy}' x2='{and_x + 1}' y2='{iy}' class='w'/><circle cx='{rx}' cy='{iy}' r='2.4' class='d'/>")
        s.append(g)
        s.append(f"<text x='{ox + 4}' y='{yc - 4}' class='ts'>{terms[i].replace(chr(39), chr(8242))}</text>")
        outs.append((ox, yc))
    or_x = and_x + 34 + 26 + 60
    if len(terms) == 1:
        fx, fy = outs[0]
        end = or_x + 20
        s.append(f"<line x1='{fx}' y1='{fy}' x2='{end}' y2='{fy}' class='w'/>")
        oy, ox = fy, end
    else:
        oy = y0 + (len(terms) - 1) * gap / 2
        h = max(30, 8 * len(terms) + 10)
        g, ox = gate_path("or", or_x, oy, 38, h)
        for i, (fx, fy) in enumerate(outs):
            iy = oy - (len(terms) - 1) * 8 / 2 + i * 8
            mid = or_x - 14 - i * 5 if fy < oy else or_x - 14 - (len(terms) - 1 - i) * 5
            s.append(f"<polyline points='{fx},{fy} {mid},{fy} {mid},{iy} {or_x + 4},{iy}' class='w'/>")
        s.append(g)
    s.append(f"<line x1='{ox}' y1='{oy}' x2='{ox + 26}' y2='{oy}' class='w'/><text x='{ox + 30}' y='{oy + 4}' class='tb'>{out_label}</text>")
    W = ox + 50
    outsvg(name, f"<svg xmlns='http://www.w3.org/2000/svg' width='{width or W}' viewBox='0 0 {W} {total_h}'>{SVG_STYLE}{''.join(s)}</svg>")


def waveform(name, signals, labels=True, hl=None):
    """signals: list of (label, bits). Draws a timing diagram with dashed interval lines."""
    n = len(signals[0][1])
    cw, rh, lx = 34, 30, 34
    W, H = lx + n * cw + 8, 18 + len(signals) * rh
    s = []
    for i in range(n + 1):
        x = lx + i * cw
        s.append(f"<line x1='{x}' y1='12' x2='{x}' y2='{H}' stroke='#bbb' stroke-dasharray='3,3'/>")
    if labels:
        for i in range(n):
            s.append(f"<text x='{lx + i * cw + cw / 2 - 3}' y='10' class='ts'>t{i + 1}</text>")
    for r, (lab, bits) in enumerate(signals):
        base = 18 + r * rh + rh - 6
        hi = base - 16
        col = "#c62828" if hl == r else "#1a1a1a"
        s.append(f"<text x='2' y='{base - 4}' class='tb' fill='{col}'>{lab}</text>")
        pts, prev = [], None
        for i, b in enumerate(bits):
            y = hi if b else base
            x0, x1 = lx + i * cw, lx + (i + 1) * cw
            if prev is not None and prev != y:
                pts.append(f"{x0},{prev}")
            pts.append(f"{x0},{y}")
            pts.append(f"{x1},{y}")
            prev = y
            s.append(f"<text x='{x0 + cw / 2 - 3}' y='{base + 0}' class='ts' fill='#999'>{b}</text>" if False else "")
        s.append(f"<polyline points='{' '.join(pts)}' fill='none' stroke='{col}' stroke-width='2'/>")
    outsvg(name, f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' viewBox='0 0 {W} {H}'>{SVG_STYLE}{''.join(s)}</svg>")


SEG = {  # a..g for digits 0-9 (common cathode, 1 = ON) -- matches the table in the user's picture
    0: "1111110", 1: "0110000", 2: "1101101", 3: "1111001", 4: "0110011",
    5: "1011011", 6: "1011111", 7: "1110000", 8: "1111111", 9: "1111011",
}
HEX = {10: "1110111", 11: "0011111", 12: "1001110", 13: "0111101", 14: "1001111", 15: "1000111"}


def seg_polys(x, y, s):
    """seven segment polygons; s = scale."""
    t, L = 2.2 * s, 9 * s
    def hseg(cx, cy):
        return f"{cx},{cy} {cx + t},{cy - t} {cx + L - t},{cy - t} {cx + L},{cy} {cx + L - t},{cy + t} {cx + t},{cy + t}"
    def vseg(cx, cy):
        return f"{cx},{cy} {cx + t},{cy + t} {cx + t},{cy + L - t} {cx},{cy + L} {cx - t},{cy + L - t} {cx - t},{cy + t}"
    return {
        "a": hseg(x, y), "b": vseg(x + L, y), "c": vseg(x + L, y + L), "d": hseg(x, y + 2 * L),
        "e": vseg(x, y + L), "f": vseg(x, y), "g": hseg(x, y + L),
    }


def digit_svg(pattern, s=1.0, on="#ef6c00"):
    p = seg_polys(4 * s, 4 * s, s)
    W, H = 9 * s + 8 * s, 18 * s + 8 * s
    body = "".join(f"<polygon points='{p[k]}' fill='{on if pattern[i] == '1' else '#eee'}'/>" for i, k in enumerate("abcdefg"))
    return f"<svg xmlns='http://www.w3.org/2000/svg' width='{W:.0f}' height='{H:.0f}' viewBox='0 0 {W} {H}'>{body}</svg>"


def seg_diagram():
    s = 5
    p = seg_polys(30, 14, s)
    body = "".join(f"<polygon points='{p[k]}' fill='#ef6c00' stroke='#fff' stroke-width='1'/>" for k in "abcdefg")
    L = 9 * s
    lab = {"a": (30 + L / 2 - 4, 8), "b": (30 + L + 14, 14 + L / 2 + 4), "c": (30 + L + 14, 14 + 1.5 * L + 4),
           "d": (30 + L / 2 - 4, 14 + 2 * L + 22), "e": (12, 14 + 1.5 * L + 4), "f": (12, 14 + L / 2 + 4), "g": (30 + L / 2 - 4, 14 + L - 6)}
    body += "".join(f"<text x='{x}' y='{y}' class='tb'>{k}</text>" for k, (x, y) in lab.items())
    outsvg("seg_diagram", f"<svg xmlns='http://www.w3.org/2000/svg' width='120' height='{14 + 2 * L + 30}'>{SVG_STYLE}{body}</svg>")


# ==================================================================== CONTENT
gate_icons()
seg_diagram()

# ---------------- Tab 1: timing diagrams
a8, b8 = [0, 0, 1, 1, 0, 1, 0, 1], [0, 1, 0, 1, 1, 1, 0, 0]
and8 = [x & y for x, y in zip(a8, b8)]
waveform("wave_and", [("a", a8), ("b", b8), ("y", and8)], hl=2)
out("wave_and_bits", "".join(f"<td>{v}</td>" for v in and8))

# ---------------- Tab 2: Boolean derivations (all verified)
deriv("d_tut1", [
    ("ab + ab'c + ab'c'", "soal (tutorial)"),
    ("a(b + b'c + b'c')", "factor a (distributive)"),
    ("a(b + b'(c + c'))", "factor b̄"),
    ("a(b + b'.1)", "c + c̄ = 1"),
    ("a(b + b')", "x·1 = x"),
    ("a.1", "b + b̄ = 1"),
    ("a", "a·1 = a"),
])
deriv("d_tut2", [
    ("(a+b+c)(a+b'+c)(a+b+c')", "soal (tutorial)"),
    ("((a+b)+c)(a+b'+c)((a+b)+c')", "misal x = a + b (substitusi)"),
    ("((a+b)+cc')(a+b'+c)", "(x+c)(x+c̄) = x + cc̄  [rule 12]"),
    ("(a+b+0)(a+b'+c)", "cc̄ = 0"),
    ("(a+b)(a+b'+c)", "x + 0 = x"),
    ("a + b(b'+c)", "(a+b)(a+Y) = a + bY  [rule 12]"),
    ("a + bb' + bc", "distributive"),
    ("a + 0 + bc", "bb̄ = 0"),
    ("a + bc", "x + 0 = x"),
])
deriv("d_notes", [
    ("ab c' + ab'c' + bc'", "soal (catatan tutor)"),
    ("ac'(b + b') + bc'", "factor ac̄"),
    ("ac' + bc'", "b + b̄ = 1"),
    ("c'(a + b)", "factor c̄ (opsional, lebih sedikit gate)"),
], names=["a", "b", "c"])
deriv("d_major", [
    ("a'bc + ab'c + abc' + abc", "soal: majority Σm(3,5,6,7)"),
    ("a'bc + ab'c + abc' + abc + abc + abc", "x = x + x (pinjam abc dua kali)"),
    ("bc(a' + a) + ac(b' + b) + ab(c' + c)", "factor tiap pasangan"),
    ("bc + ac + ab", "x + x̄ = 1"),
])
deriv("d_dm", [
    ("[a'b'(c'+d) + (a+b+c'd')']'", "soal (PR4 no. 11)"),
    ("[a'b'(c'+d)]'.(a+b+c'd')''", "De Morgan: (X+Y)′ = X̄·Ȳ"),
    ("[a'b'(c'+d)]'.(a+b+c'd')", "double bar: x̿ = x"),
    ("(a + b + (c'+d)')(a+b+c'd')", "De Morgan: (XYZ)′ = X̄+Ȳ+Z̄"),
    ("(a + b + cd')(a+b+c'd')", "De Morgan: (c̄+d)′ = c d̄"),
    ("a + b + cd'c'd'", "rule 12: (X+P)(X+Q) = X + PQ"),
    ("a + b + 0", "c c̄ = 0"),
    ("a + b", "x + 0 = x"),
])
deriv("d_cons", [
    ("ab + a'cd + bcd", "soal (PR4 no. 14)"),
    ("ab + a'cd + bcd(a + a')", "x·1, 1 = a + ā"),
    ("ab + a'cd + abcd + a'bcd", "distributive"),
    ("ab(1 + cd) + a'cd(1 + b)", "factor"),
    ("ab + a'cd", "1 + x = 1"),
])
deriv("d_xor", [
    ("[(a^b)' + c]' + (a^b)c'", "soal (PR4 no. 18)"),
    ("(a^b)''c' + (a^b)c'", "De Morgan"),
    ("(a^b)c' + (a^b)c'", "double bar"),
    ("(a^b)c'", "x + x = x"),
    ("(a'b + ab')c'", "a⊕b = āb + ab̄"),
    ("a'bc' + ab'c'", "distributive"),
])

# 27-identity worksheet (WhatsApp image). Every pair checked.
WS = [
    ("a + 0", "a", "identity"), ("a'.0", "0", "null"), ("a + a'", "1", "complement"), ("a + a", "a", "idempotent"),
    ("a + ab", "a", "absorption"), ("a + a'b", "a + b", "rule 11"), ("a(a' + b)", "ab", "distrib. + aā = 0"),
    ("ab + a'b", "b", "factor b"), ("(a'+b')(a'+b)", "a'", "rule 12"), ("a(a+b+c+d)", "a", "absorption"),
    ("a + b + ab", "a + b", "f(a,b,ab): absorption"), ("a + b + a'b", "a + b", "f(a,b,āb): absorption"),
    ("a + b + (ab)'", "1", "f(a,b,(ab)′) = a+b+ā+b̄"), ("y + yy'", "y", "yȳ = 0"), ("xy + xy'", "x", "factor x"),
    ("x' + yx'", "x'", "absorption"), ("(w + x' + y + z')y", "y", "absorption"), ("(x+y')(x+y)", "x", "rule 12"),
    ("w + [w + (wx)]", "w", "absorption"), ("x[x + (xy)]", "x", "absorption"), ("(x' + x')'", "x", "idempotent, double bar"),
    ("(x + x')'", "0", "1̄ = 0"), ("w + (wx'yz)", "w", "absorption"), ("w'.(wxyz)'", "w'", "De Morgan + absorption"),
    ("xz + x'y + zy", "xz + x'y", "consensus"), ("(x+z)(x'+y)(z+y)", "(x+z)(x'+y)", "consensus (dual)"),
    ("x' + y' + xyz'", "x' + y' + z'", "(xy)′ + (xy)z̄ → rule 11"),
]
rows = []
for i, (q, a, law) in enumerate(WS, 1):
    vs = sorted(varsof(parse(q)) | varsof(parse(a))) or ["a"]
    check(minterms(q, vs) == minterms(a, vs), f"worksheet {i}")
    rows.append(f"<tr><td class='n'>{i}</td><td>\\({T(q)}\\)</td><td>\\(= {T(a)}\\)</td><td class='law'>{law}</td></tr>")
half = (len(rows) + 1) // 2
out("ws27", "<div class='two'><table class='ws'>" + "".join(rows[:half]) + "</table><table class='ws'>" + "".join(rows[half:]) + "</table></div>")

# ---------------- Tab 3: K-map templates
for n, nm in [(2, "ab"), (3, "abc"), (4, "abcd")]:
    out(f"tpl{n}", kmap(list(nm), set(), show_idx=True, small=True, title=f"{n} variabel").replace(">0</td>", "></td>"))
out("tpl5", "<div class='row'>" +
    kmap(list("bcde"), set(), small=True, title="a = 0  (m0–m15)").replace(">0</td>", "></td>") +
    kmap(list("bcde"), set(), small=True, title="a = 1  (m16–m31)", offset=16).replace(">0</td>", "></td>") + "</div>")

# Got-talent (majority of 3 judges)
N3 = list("abc")
maj = {m for m in range(8) if bin(m).count("1") >= 2}
check(maj == {3, 5, 6, 7}, "majority minterms")
notes = ["0 setuju → gagal", "1 setuju", "1 setuju", "2 setuju → lolos", "1 setuju", "2 setuju → lolos", "2 setuju → lolos", "3 setuju → lolos"]
out("gt_tt", truth_table(N3, [("y", [int(m in maj) for m in range(8)])], extra=notes))
s, p = canon(N3, maj)
out("gt_canon", f"<p>\\(y = {s}\\) &nbsp;=&nbsp; \\(\\Sigma m(3,5,6,7)\\) <span class='tagsop'>SOP / minterm</span></p>"
               f"<p>\\(y = {p}\\) &nbsp;=&nbsp; \\(\\Pi M(0,1,2,4)\\) <span class='tagpos'>POS / maxterm</span></p>")
out("gt_kmap_sop", kmap(N3, maj, groups=["bc", "ac", "ab"], title="SOP: group the 1s"))
out("gt_kmap_pos", kmap(N3, maj, groups=["a'b'", "a'c'", "b'c'"], mode="pos", title="POS: group the 0s"))
out("gt_res", f"\\(y = {result(N3, maj, set(), ['ab', 'ac', 'bc'])}\\) &nbsp;&nbsp;|&nbsp;&nbsp; "
              f"\\(y = {result(N3, maj, set(), [chr(97)+chr(39)+'b'+chr(39), 'a'+chr(39)+'c'+chr(39), 'b'+chr(39)+'c'+chr(39)], 'pos')}\\)")
sop_circuit("c_major", N3, ["ab", "ac", "bc"])
sop_circuit("c_board", list("abcd"), ["cd", "a'bd", "a'b'c"])
check(minterms("cd + a'bd + a'b'c", list("abcd")) == {2, 3, 5, 7, 11, 15}, "board circuit")

# Example of don't care (board): rows 5,6,7 = X
dc_ones, dc_x = {1, 2, 4}, {5, 6, 7}
out("dc_x1", kmap(N3, dc_ones, dc_x, groups=["a", "b'c", "bc'"], small=True, title="X dipakai (X = 1 kalau membantu)"))
out("dc_x0", kmap(N3, dc_ones, set(), groups=["a'b'c", "a'bc'", "ab'c'"], small=True, title="X dianggap 0 (salah strategi)"))
result(N3, dc_ones, dc_x, ["a", "b'c", "bc'"])

# 4-var example from the board: Σm(0,2,3,5,7,8,10,11,14,15)
B4 = {0, 2, 3, 5, 7, 8, 10, 11, 14, 15}
N4 = list("abcd")
out("k4_board", kmap(N4, B4, groups=["cd", "ac", "b'd'", "a'bd"], small=True, title="Σm(0,2,3,5,7,8,10,11,14,15)"))
out("k4_board_res", "\\(y = " + result(N4, B4, set(), ["cd", "ac", "b'd'", "a'bd"]) + "\\)")
# corners & wrap examples
out("k4_corner", kmap(N4, {0, 2, 8, 10}, groups=["b'd'"], small=True, title="4 pojok → \\(\\bar b\\bar d\\)"))
out("k4_wrap", kmap(N4, {0, 4, 8, 12, 2, 6, 10, 14}, groups=["d'"], small=True, title="kolom kiri+kanan → \\(\\bar d\\)"))
# 5-variable example: PR5 Q28 Σm(4,5,6,7,12,13,14,15,20,21,22,23)
Q28 = {4, 5, 6, 7, 12, 13, 14, 15, 20, 21, 22, 23}
N5 = list("abcde")
lo = {m for m in Q28 if m < 16}
hi = {m - 16 for m in Q28 if m >= 16}
out("k5_ex", "<div class='row'>" +
    kmap(list("bcde"), lo, groups=["c"], small=True, title="a = 0") +
    kmap(list("bcde"), hi, groups=["b'c"], small=True, title="a = 1", offset=16) + "</div>")
check(minterms("a'c + b'c", N5) == Q28, "5-var example")

# ---------------- PR5 cases (rules → truth table, recomputed from the wording)
def case_amr(a, b, c):
    if c == 1:
        return int(a != b)                      # exactly one visual warning
    if a == b == c == 0:
        return 0                                # full nominal transit excluded
    return int(a == 0 or (a == 1 and b == 0))   # LiDAR clear, or obstacle with track locked; failsafe a=0,b=1 included


def case_avi(a, b, c):
    if b == 1 and c == 1:
        return 1
    if c == 0 and a != b:
        return 1
    return 0                                    # incl. a=b=0, c=1 rejected as noise


def case_bat(a, b, c):
    if a == 1:
        return int(c == 1)
    if c == 1:
        return int(b == 0)
    return 1                                    # c=0, a=0: fires for b=0 or b=1


CASES = [
    ("amr", case_amr, ["A'B", "AB'"], ["A'B'", "AB"], "\\bar A B + A\\bar B = A \\oplus B"),
    ("avi", case_avi, ["A'B", "BC", "AB'C'"], ["A'B'", "B'C", "ABC'"], None),
    ("bat", case_bat, ["A'C'", "B'C", "AC"], ["AC'", "A'BC"], None),
]
for key, fn, sg, pg, special in CASES:
    ones = {m for m in range(8) if fn(m >> 2 & 1, m >> 1 & 1, m & 1)}
    out(f"case_{key}_tt", truth_table(list("ABC"), [("Y", [int(m in ones) for m in range(8)])]))
    NC = list("ABC")
    out(f"case_{key}_sop", kmap(NC, ones, groups=sg, small=True, title="SOP"))
    out(f"case_{key}_pos", kmap(NC, ones, groups=pg, mode="pos", small=True, title="POS"))
    rs = result(NC, ones, set(), sg)
    rp = result(NC, ones, set(), pg, "pos")
    out(f"case_{key}_res", f"<p class='res'>\\(\\Sigma m({','.join(map(str, sorted(ones)))})\\) → "
                           f"\\(Y = {special or rs}\\) &nbsp;|&nbsp; \\(Y = {rp}\\)</p>")
check({m for m in range(8) if case_amr(m >> 2 & 1, m >> 1 & 1, m & 1)} == {2, 3, 4, 5}, "AMR")
check({m for m in range(8) if case_avi(m >> 2 & 1, m >> 1 & 1, m & 1)} == {2, 3, 4, 7}, "avionics")
check({m for m in range(8) if case_bat(m >> 2 & 1, m >> 1 & 1, m & 1)} == {0, 1, 2, 5, 7}, "battery")

# ---------------- Tab 4: seven segment (A = MSB ... D = LSB)
NS = list("ABCD")
segon = {k: {d for d in range(10) if SEG[d]["abcdefg".index(k)] == "1"} for k in "abcdefg"}
X10 = set(range(10, 16))
# complete table like the user's picture + 10..15 don't care rows
rows = []
for m in range(16):
    bits = [(m >> (3 - j)) & 1 for j in range(4)]
    if m < 10:
        segs = "".join(f"<td class='{'on' if c == '1' else 'off'}'>{c}</td>" for c in SEG[m])
        icon = digit_svg(SEG[m], 1.05)
        rows.append(f"<tr><td class='dec'>{m}</td>" + "".join(f"<td>{b}</td>" for b in bits) +
                    f"<td class='sep'></td>{segs}<td class='icon'>{icon}</td></tr>")
    else:
        rows.append(f"<tr class='xrow'><td class='dec'>{m}</td>" + "".join(f"<td>{b}</td>" for b in bits) +
                    "<td class='sep'></td>" + "<td>X</td>" * 7 + "<td class='icon small'>invalid BCD</td></tr>")
out("seg_table", "<table class='segt'><thead><tr><th>Dec</th><th>A</th><th>B</th><th>C</th><th>D</th><th class='sep'></th>" +
    "".join(f"<th>{k}</th>" for k in "abcdefg") + "<th>tampil</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>")

SEG_GROUPS = {
    "a": ["A", "C", "BD", "B'D'"],
    "b": ["B'", "C'D'", "CD"],
    "c": ["B", "C'", "D"],
    "d": ["A", "B'D'", "B'C", "CD'", "BC'D"],
    "e": ["B'D'", "CD'"],
    "f": ["A", "C'D'", "BC'", "BD'"],
    "g": ["A", "B'C", "BC'", "CD'"],
}
maps, eqrows = [], []
for k in "abcdefg":
    ones = segon[k]
    gs = SEG_GROUPS[k]
    maps.append(kmap(NS, ones, X10, groups=gs, small=True, title=f"segment {k}"))
    r = result(NS, ones, X10, gs)
    off = sorted(set(range(10)) - ones)
    eqrows.append(f"<tr><td class='sg'>{k}</td><td>\\(\\Sigma m({','.join(map(str, sorted(ones)))}) + d(10\\text{{–}}15)\\)</td>"
                  f"<td>{', '.join(map(str, off))}</td><td>\\({k} = {r}\\)</td></tr>")
out("seg_kmaps", "<div class='kgrid'>" + "".join(maps) + "</div>")
out("seg_eqs", "<table class='full eqs'><thead><tr><th>seg</th><th>ON (minterm)</th><th>OFF di</th><th>minimal SOP</th></tr></thead><tbody>" +
    "".join(eqrows) + "</tbody></table>")
# segment c by grouping the single 0
cz = set(range(10)) - segon["c"]
check(cz == {2}, "segment c off only at 2")
out("seg_c_pos", kmap(NS, segon["c"], X10, groups=["B'CD'"], mode="pos", small=True, title="segment c: group the 0"))
result(NS, segon["c"], X10, ["B'CD'"], "pos")
check(minterms("A'B'CD'", NS) == {2}, "maxterm m2")
# hex table (0-F, no don't cares)
hexrows = "".join(f"<td class='icon'>{digit_svg((SEG | HEX)[m], 0.85)}<div class='small'>{'0123456789AbCdEF'[m]}</div></td>" for m in range(16))
out("hex_icons", f"<table class='hexi'><tr>{hexrows}</tr></table>")

# ---------------- Tab R: numbers (PR2 style) -- computed
def conv(n):
    return bin(n)[2:], oct(n)[2:], hex(n)[2:].upper()


b859, o859, h859 = conv(859)
out("num859", f"859 = <b class='mono'>{b859}</b>₂ = <b class='mono'>{o859}</b>₈ = <b class='mono'>{h859}</b>₁₆")
steps = []
n = 859
while n:
    steps.append(f"{n} ÷ 2 = {n // 2} sisa <b>{n % 2}</b>")
    n //= 2
out("div859", "<br>".join(steps))
check(b859 == "1101011011" and o859 == "1533" and h859 == "35B", "859 conversion")
A, B = 0b100001111, 0b100000100
nb = 9
tc = ((~B) & (2 ** nb - 1)) + 1
s_ = A + tc
out("tc_ex", f"""<table class='bin mono'>
<tr><td>A</td><td>{A:09b}</td><td>= {A}</td></tr>
<tr><td>B</td><td>{B:09b}</td><td>= {B}</td></tr>
<tr><td>1's comp B</td><td>{(~B) & (2 ** nb - 1):09b}</td><td>flip semua bit</td></tr>
<tr><td>2's comp B</td><td>{tc:09b}</td><td>+1</td></tr>
<tr><td>A + 2's B</td><td>{s_:010b}</td><td>carry keluar = 1 → buang</td></tr>
<tr class='last'><td>A − B</td><td>{s_ & (2 ** nb - 1):09b}</td><td>= {A - B} ✔ (271 − 260)</td></tr></table>""")
check(s_ & (2 ** nb - 1) == A - B == 11 and s_ >> nb == 1, "2's complement example")
check(A + B == 531, "add example")
out("add_ex", f"<span class='mono'>{A:09b} + {B:09b} = {A + B:b}</span> → {A} + {B} = {A + B} ✔")

# ---------------- Mock exam (answers recomputed)
# Q1 timing: a, b given; NAND and XOR
ma = [0, 1, 1, 0, 1, 0, 1, 1]
mb = [0, 0, 1, 1, 1, 0, 0, 1]
mnand = [1 - (x & y) for x, y in zip(ma, mb)]
mxor = [x ^ y for x, y in zip(ma, mb)]
waveform("mock_wave_q", [("a", ma), ("b", mb)])
waveform("mock_wave_nand", [("a", ma), ("b", mb), ("nand", mnand)], hl=2)
waveform("mock_wave_xor", [("a", ma), ("b", mb), ("xor", mxor)], hl=2)
out("mock_nand_bits", " ".join(map(str, mnand)))
out("mock_xor_bits", " ".join(map(str, mxor)))
check(mnand == [1, 1, 0, 1, 0, 1, 1, 0] and mxor == [0, 1, 0, 1, 0, 0, 1, 0], "mock timing")

# Q2: 3-bit binary (0-7) to common-cathode 7-seg, segments a and g
N3u = list("ABC")
q2a = {d for d in range(8) if SEG[d][0] == "1"}
q2g = {d for d in range(8) if SEG[d][6] == "1"}
check(q2a == {0, 2, 3, 5, 6, 7} and q2g == {2, 3, 4, 5, 6}, "mock Q2 sets")
out("mock_q2_tt", truth_table(N3u, [("a", [int(m in q2a) for m in range(8)]), ("g", [int(m in q2g) for m in range(8)])]))
out("mock_q2_a", kmap(N3u, q2a, groups=["B", "AC", "A'C'"], small=True, title="segment a"))
out("mock_q2_g", kmap(N3u, q2g, groups=["A'B", "AB'", "BC'"], small=True, title="segment g"))
out("mock_q2_res", f"\\(a = {result(N3u, q2a, set(), ['B', 'AC', 'A' + chr(39) + 'C' + chr(39)])}\\) &nbsp;&nbsp; "
                   f"\\(g = {result(N3u, q2g, set(), ['A' + chr(39) + 'B', 'AB' + chr(39), 'BC' + chr(39)])}\\)")
out("mock_q2_apos", kmap(N3u, q2a, groups=["A'B'C", "AB'C'"], mode="pos", small=True, title="a: group 0s"))
result(N3u, q2a, set(), ["A'B'C", "AB'C'"], "pos")

# Q3 simplifications
deriv("mk3a", [
    ("(a + b)(a' + c)(b + c)", "soal"),
    ("(a + b)(a' + c)", "consensus (dual): (b + c) redundant"),
    ("aa' + ac + a'b + bc", "atau buka kurung: distributive"),
    ("ac + a'b", "aā = 0, lalu consensus: bc hilang"),
])
deriv("mk3b", [
    ("(a'b' + c)' + a'b", "soal"),
    ("(a'b')'.c' + a'b", "De Morgan: (X + Y)′ = X̄Ȳ"),
    ("(a + b)c' + a'b", "De Morgan: (āb̄)′ = a + b"),
    ("ac' + bc' + a'b", "distributive"),
    ("ac' + a'b", "consensus: bc̄ (dari ac̄ & āb) redundant"),
])
deriv("mk3c", [
    ("abc + ab'c + abc' + a'b'c", "soal"),
    ("ab(c + c') + b'c(a + a')", "factor (pasangkan abc–abc̄, ab̄c–āb̄c)"),
    ("ab + b'c", "x + x̄ = 1"),
])
# Q4: four judges, a = ketua juri
def judge(a, b, c, d):
    k = a + b + c + d
    return int(k >= 3 or (k == 2 and a == 1))


q4 = {m for m in range(16) if judge(m >> 3 & 1, m >> 2 & 1, m >> 1 & 1, m & 1)}
check(q4 == {7, 9, 10, 11, 12, 13, 14, 15}, "mock Q4 minterms")
out("mock_q4_tt", truth_table(N4, [("y", [int(m in q4) for m in range(16)])]))
out("mock_q4_sop", kmap(N4, q4, groups=["ab", "ac", "ad", "bcd"], small=True, title="SOP"))
out("mock_q4_pos", kmap(N4, q4, groups=["a'b'", "a'c'", "a'd'", "b'c'd'"], mode="pos", small=True, title="POS"))
out("mock_q4_res", f"\\(y = {result(N4, q4, set(), ['ab', 'ac', 'ad', 'bcd'])}\\) &nbsp;|&nbsp; "
                   f"\\(y = {result(N4, q4, set(), ['a' + chr(39) + 'b' + chr(39), 'a' + chr(39) + 'c' + chr(39), 'a' + chr(39) + 'd' + chr(39), 'b' + chr(39) + 'c' + chr(39) + 'd' + chr(39)], 'pos')}\\)")
sop_circuit("c_mock4", N4, ["ab", "ac", "ad", "bcd"])
s4, p4 = canon(N4, q4)
out("mock_q4_canon", f"\\(\\Sigma m(7,9,10,11,12,13,14,15)\\) = \\(\\Pi M(0,1,2,3,4,5,6,8)\\)")
check(set(range(16)) - q4 == {0, 1, 2, 3, 4, 5, 6, 8}, "mock Q4 maxterms")

print(f"gen.py: all {CHECKS} checks passed")
