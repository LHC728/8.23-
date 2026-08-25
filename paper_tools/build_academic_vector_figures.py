"""Build seven restrained, publication-style SVG figures from frozen project data.

The figures are vector graphics with short mathematical labels, axes, line
styles and legends.  They intentionally avoid infographic cards and long text.
"""
from __future__ import annotations

from html import escape
from itertools import combinations
from math import atan2, cos, degrees, pi, sin, sqrt
from pathlib import Path
import json
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.q1_1_geometry import _circle_branches, angle_signature, circle_intersections, raw_angle
from src.q1_2_identity import target_coordinates
from src.q1_3_adjustment import table1_coordinates
from src.q2_geometry import target_lattice
from src.q2_evaluator import nearest_neighbor_edges


OUT = ROOT / "paper_assets" / "figures_svg"
W, H = 1200, 750

BLACK = "#202020"
GRAY = "#737373"
LIGHT = "#D9D9D9"
BLUE = "#2F5597"
RED = "#A61C1C"
GREEN = "#2E7D32"
ORANGE = "#C55A11"
FONT = "Times New Roman, Microsoft YaHei, SimSun"


class SVG:
    def __init__(self, width=W, height=H):
        self.width, self.height = width, height
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#202020"/></marker></defs>',
            '<rect x="0" y="0" width="100%" height="100%" fill="white"/>',
        ]

    def line(self, x1, y1, x2, y2, stroke=BLACK, width=2, dash=None, arrow=False, opacity=1.0):
        attrs = f'stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"'
        if dash:
            attrs += f' stroke-dasharray="{dash}"'
        if arrow:
            attrs += ' marker-end="url(#arrow)"'
        self.parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" {attrs}/>' )

    def circle(self, x, y, r, stroke=BLACK, width=2, fill="white", opacity=1.0):
        self.parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"/>')

    def rect(self, x, y, w, h, stroke=BLACK, width=1.5, fill="white"):
        self.parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')

    def polyline(self, points, stroke=BLACK, width=2, dash=None, fill="none", opacity=1.0):
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        attrs = f'stroke="{stroke}" stroke-width="{width}" fill="{fill}" opacity="{opacity}"'
        if dash:
            attrs += f' stroke-dasharray="{dash}"'
        self.parts.append(f'<polyline points="{pts}" {attrs}/>' )

    def path(self, d, stroke=BLACK, width=2, dash=None, fill="none", opacity=1.0):
        attrs = f'stroke="{stroke}" stroke-width="{width}" fill="{fill}" opacity="{opacity}"'
        if dash:
            attrs += f' stroke-dasharray="{dash}"'
        self.parts.append(f'<path d="{d}" {attrs}/>' )

    def text(self, x, y, value, size=22, anchor="middle", fill=BLACK, italic=False, weight="normal", rotate=None):
        style = f'font-family="{FONT}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" dominant-baseline="middle" font-weight="{weight}"'
        if italic:
            style += ' font-style="italic"'
        if rotate is not None:
            style += f' transform="rotate({rotate} {x} {y})"'
        self.parts.append(f'<text x="{x:.2f}" y="{y:.2f}" {style}>{escape(value)}</text>')

    def save(self, path: Path):
        path.write_text("\n".join(self.parts + ["</svg>"]), encoding="utf-8")


def mapper(bounds, panel):
    xmin, xmax, ymin, ymax = bounds
    x0, y0, x1, y1 = panel
    scale = min((x1 - x0) / (xmax - xmin), (y1 - y0) / (ymax - ymin))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    mx, my = (xmin + xmax) / 2, (ymin + ymax) / 2
    return lambda p: (cx + scale * (float(p[0]) - mx), cy - scale * (float(p[1]) - my)), scale


def axes(svg: SVG, panel, x_label="x", y_label="y", ticks=4):
    x0, y0, x1, y1 = panel
    svg.line(x0, y1, x1, y1, BLACK, 1.5)
    svg.line(x0, y0, x0, y1, BLACK, 1.5)
    for k in range(1, ticks):
        x = x0 + k * (x1 - x0) / ticks
        y = y0 + k * (y1 - y0) / ticks
        svg.line(x, y0, x, y1, LIGHT, 1)
        svg.line(x0, y, x1, y, LIGHT, 1)
    svg.text((x0 + x1) / 2, y1 + 38, x_label, 20, italic=True)
    svg.text(x0 - 35, (y0 + y1) / 2, y_label, 20, italic=True, rotate=-90)


def mark(svg, point, label, color=BLUE, shape="circle", dx=0, dy=-24, size=20):
    x, y = point
    if shape == "square":
        svg.rect(x - 7, y - 7, 14, 14, color, 2, color)
    elif shape == "cross":
        svg.line(x - 7, y - 7, x + 7, y + 7, color, 2.5)
        svg.line(x - 7, y + 7, x + 7, y - 7, color, 2.5)
    else:
        svg.circle(x, y, 7, color, 2, color)
    if label:
        svg.text(x + dx, y + dy, label, size, fill=color)


def sampled_circle(center, radius, angle_start=0, angle_end=2 * pi, n=241):
    return [
        (center[0] + radius * cos(t), center[1] + radius * sin(t))
        for t in np.linspace(angle_start, angle_end, n)
    ]


def fig01():
    svg = SVG()
    panel = (125, 75, 1080, 625)
    axes(svg, panel, "x", "y")
    mp, scale = mapper((-1.8, 1.8, -2.0, 2.0), panel)
    a, b = np.array([-1.0, 0.0]), np.array([1.0, 0.0])
    alpha = pi / 3
    radius = 1 / sin(alpha)
    offset = 1 / np.tan(alpha)
    centers = [np.array([0.0, offset]), np.array([0.0, -offset])]
    colors = [BLUE, ORANGE]
    for center, color in zip(centers, colors):
        svg.polyline([mp(p) for p in sampled_circle(center, radius)], color, 1.5, "7 6", opacity=0.75)
    # Admissible outer arcs giving alpha = pi/3.
    svg.polyline([mp(p) for p in sampled_circle(centers[0], radius, 11 * pi / 6, 19 * pi / 6)], BLUE, 4)
    svg.polyline([mp(p) for p in sampled_circle(centers[1], radius, 5 * pi / 6, 13 * pi / 6)], ORANGE, 4)
    pa, pb = mp(a), mp(b)
    mark(svg, pa, "A", RED, "square", -18, -22)
    mark(svg, pb, "B", RED, "square", 18, -22)
    p_plus, p_minus = np.array([0.0, 1.0 + offset]), np.array([0.0, -1.0 - offset])
    for p, label, color, dy in [(p_plus, "P⁺", BLUE, -24), (p_minus, "P⁻", ORANGE, 26)]:
        pp = mp(p)
        mark(svg, pp, label, color, "circle", 0, dy)
        svg.line(pp[0], pp[1], pa[0], pa[1], GRAY, 1.4)
        svg.line(pp[0], pp[1], pb[0], pb[1], GRAY, 1.4)
        svg.text(pp[0] + 34, pp[1] + (-5 if p[1] > 0 else 5), "α", 24, fill=BLACK, italic=True)
    svg.text(600, 675, "∠AP⁺B = ∠AP⁻B = α；两侧候选分支必须同时保留", 22)
    svg.save(OUT / "fig01_two_sided_angle_locus_academic.svg")


def fig02():
    svg = SVG()
    q = target_coordinates()
    tx = [q[0], q[1], q[4]]
    target = q[2]
    observed = angle_signature(target, tx)
    names = ("ab", "ac")
    circles = []
    for name, theta, pair in [("ab", observed[0], (0, 1)), ("ac", observed[1], (0, 2))]:
        branches, _ = _circle_branches(np.asarray(tx[pair[0]]), np.asarray(tx[pair[1]]), float(theta), name, boundary_eps=1e-8)
        circles.append(branches)
    intersections = []
    for c1 in circles[0]:
        for c2 in circles[1]:
            pts, _ = circle_intersections(c1, c2)
            intersections.extend(pts)
    # Deduplicate and classify by the third angle.
    unique = []
    for p in intersections:
        if not any(np.linalg.norm(p - r) < 1e-6 for r in unique):
            unique.append(p)
    keep = [p for p in unique if abs(raw_angle(p, tx[1], tx[2]) - observed[2]) < 1e-7]
    all_points = tx + unique
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    pad = 35
    mp, scale = mapper((min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad), (100, 70, 1090, 625))
    axes(svg, (100, 70, 1090, 625), "x / m", "y / m")
    for branch_set, color in zip(circles, [BLUE, ORANGE]):
        for c in branch_set:
            svg.polyline([mp(p) for p in sampled_circle(c.center, c.radius)], color, 1.6, "8 6", opacity=0.7)
    for label, p in zip(["FY00", "FY01", "FY04"], tx):
        mark(svg, mp(p), label, RED, "square", 0, -22, 18)
    for idx, p in enumerate(unique, 1):
        if any(np.linalg.norm(p - k) < 1e-6 for k in keep):
            mark(svg, mp(p), "P*", GREEN, "circle", 0, -24)
        else:
            mark(svg, mp(p), f"P{idx}", RED, "cross", 0, -22, 17)
    svg.text(600, 675, "虚线：前两条夹角的双侧轨迹圆；×：第三角回代拒绝；P*：三角同时满足", 21)
    svg.save(OUT / "fig02_complete_candidates_academic.svg")


def fig03():
    svg = SVG()
    # Left: one angle gives a continuum.
    svg.text(285, 45, "(a) m = 0", 23, weight="bold")
    svg.text(875, 45, "(b) m = 1", 23, weight="bold")
    left_panel = (80, 100, 540, 610)
    axes(svg, left_panel, "x", "y")
    mp, _ = mapper((-1.7, 1.7, -0.5, 2.2), left_panel)
    a, b = np.array([-1.0, 0.0]), np.array([1.0, 0.0])
    alpha = pi / 3
    radius, offset = 1 / sin(alpha), 1 / np.tan(alpha)
    branch = sampled_circle(np.array([0.0, offset]), radius, 11 * pi / 6, 19 * pi / 6)
    svg.polyline([mp(p) for p in branch], BLUE, 4)
    mark(svg, mp(a), "FY00", RED, "square", -16, -22, 17)
    mark(svg, mp(b), "FY01", RED, "square", 16, -22, 17)
    svg.text(300, 650, "h₀₁(x)=α：连续圆弧解集", 21)

    # Right: two varying components of the three-dimensional observation vector.
    q = target_coordinates()
    receiver = 2
    identities = [k for k in range(2, 10) if k != receiver]
    values = []
    for b_id in identities:
        x = q[receiver]
        values.append((b_id, degrees(raw_angle(x, q[0], q[b_id])), degrees(raw_angle(x, q[1], q[b_id]))))
    xs = [v[1] for v in values]
    ys = [v[2] for v in values]
    right_panel = (660, 100, 1130, 610)
    axes(svg, right_panel, "h₀b / (°)", "h₁b / (°)")
    mp2, _ = mapper((min(xs) - 12, max(xs) + 12, min(ys) - 12, max(ys) + 12), right_panel)
    true_id = identities[0]
    for b_id, xval, yval in values:
        color = GREEN if b_id == true_id else BLUE
        shape = "square" if b_id == true_id else "circle"
        mark(svg, mp2((xval, yval)), f"b={b_id}", color, shape, 0, -20, 16)
    svg.text(895, 650, "不同编号假设在观测平面中形成分离点集", 21)
    svg.save(OUT / "fig03_identity_observation_separation_academic.svg")


def fig04():
    svg = SVG()
    cols = ["子轮 1", "子轮 2", "四锚阶段"]
    nodes = list(range(10))
    x0, y0, cw, rh = 260, 90, 280, 50
    for j, col in enumerate(cols):
        svg.text(x0 + j * cw, 52, col, 21, weight="bold")
    for i, node_id in enumerate(nodes):
        y = y0 + i * rh
        svg.text(115, y, f"FY{node_id:02d}", 18, anchor="start")
        svg.line(190, y, 930, y, LIGHT, 1)
    transmit = [{0, 1, 7}, {0, 1, 4}, {0, 1, 4, 7}]
    receive = [{4}, {7}, {2, 3, 5, 6, 8, 9}]
    for j in range(3):
        x = x0 + j * cw
        for i in nodes:
            y = y0 + i * rh
            if i in transmit[j]:
                svg.rect(x - 7, y - 7, 14, 14, BLACK, 1.5, BLACK)
            elif i in receive[j]:
                svg.circle(x, y, 8, RED, 2, "white")
    svg.rect(985, 185, 14, 14, BLACK, 1.5, BLACK)
    svg.text(1010, 192, "发射", 18, anchor="start")
    svg.circle(992, 240, 8, RED, 2, "white")
    svg.text(1010, 240, "接收并移动", 18, anchor="start")
    svg.text(600, 625, "每个红圈仅处理本机纯方位观测；不同接收机之间不汇总夹角", 21)
    svg.save(OUT / "fig04_q1_schedule_matrix_academic.svg")


def fig05():
    svg = SVG()
    svg.text(300, 40, "(a) 表 1 初始位置与目标位置", 22, weight="bold")
    svg.text(900, 40, "(b) 最终误差（有限试探回放）", 22, weight="bold")
    initial = table1_coordinates()
    ideal = target_coordinates()
    panel = (80, 90, 560, 610)
    axes(svg, panel, "x / m", "y / m")
    mp, scale = mapper((-125, 125, -125, 125), panel)
    c = mp((0, 0))
    svg.circle(c[0], c[1], 100 * scale, GRAY, 1.5, "none")
    for k in range(1, 10):
        pi0, pt = mp(initial[k]), mp(ideal[k])
        svg.line(pi0[0], pi0[1], pt[0], pt[1], GRAY, 1.2, "5 4", arrow=True)
        mark(svg, pi0, f"{k}", ORANGE, "circle", 0, -17, 15)
        mark(svg, pt, "", BLUE, "circle")
    mark(svg, mp(ideal[0]), "FY00", RED, "square", 0, -20, 16)
    svg.line(125, 650, 165, 650, ORANGE, 3)
    svg.text(175, 650, "初始位置", 17, anchor="start")
    svg.line(285, 650, 325, 650, BLUE, 3)
    svg.text(335, 650, "目标位置", 17, anchor="start")

    gate = json.loads((ROOT / "results" / "q1_3" / "q1_3_program_gate.json").read_text(encoding="utf-8"))
    ev = gate["checks"]["finite_difference_table1"]["evidence"]
    radii = np.asarray(ev["radii_m"], dtype=float)
    gaps = np.asarray(ev["central_gaps_rad"], dtype=float)
    angles = np.zeros(9)
    angles[1:] = np.cumsum(gaps[:8])
    final = np.column_stack((radii * np.cos(angles), radii * np.sin(angles)))
    target = np.vstack([ideal[k] for k in range(1, 10)])
    pos_err = np.linalg.norm(final - target, axis=1) * 1e7
    rad_err = np.abs(radii - 100.0) * 1e7
    x0, y0, x1, y1 = 670, 110, 1130, 610
    svg.line(x0, y1, x1, y1, BLACK, 1.5)
    svg.line(x0, y0, x0, y1, BLACK, 1.5)
    ymax = max(3.2, float(max(pos_err.max(), rad_err.max())) * 1.12)
    for k in range(5):
        yy = y1 - k * (y1 - y0) / 4
        svg.line(x0, yy, x1, yy, LIGHT, 1)
        svg.text(x0 - 12, yy, f"{ymax*k/4:.1f}", 16, anchor="end")
    bw = 16
    for idx in range(9):
        x = x0 + 34 + idx * 48
        hp = pos_err[idx] / ymax * (y1 - y0)
        hr = rad_err[idx] / ymax * (y1 - y0)
        svg.rect(x - bw, y1 - hp, bw, hp, BLUE, 1, BLUE)
        svg.rect(x + 2, y1 - hr, bw, hr, ORANGE, 1, ORANGE)
        svg.text(x + 1, y1 + 24, str(idx + 1), 16)
    svg.text(900, 672, "无人机编号", 18)
    svg.text(622, 360, "误差 / (10⁻⁷ m)", 18, rotate=-90)
    svg.rect(760, 75, 12, 12, BLUE, 1, BLUE)
    svg.text(780, 82, "位置误差", 16, anchor="start")
    svg.rect(920, 75, 12, 12, ORANGE, 1, ORANGE)
    svg.text(940, 82, "半径误差", 16, anchor="start")
    svg.save(OUT / "fig05_q1_adjustment_errors_academic.svg")


def fig06():
    svg = SVG()
    lattice = target_lattice()
    panel = (120, 70, 1050, 620)
    axes(svg, panel, "x / d*", "y / d*")
    mp, _ = mapper((-3.9, 0.4, -2.5, 2.5), panel)
    for i, j in nearest_neighbor_edges():
        p, q = mp(lattice[i]), mp(lattice[j])
        svg.line(p[0], p[1], q[0], q[1], LIGHT, 1.5)
    refs = {3, 4, 11, 15}
    for k, p in lattice.items():
        mark(svg, mp(p), f"{k}", RED if k in refs else BLUE, "square" if k in refs else "circle", 0, -18, 15)
    p11, p15 = mp(lattice[11]), mp(lattice[15])
    svg.line(p11[0], p11[1] + 30, p15[0], p15[1] + 30, RED, 2.5, arrow=True)
    svg.text((p11[0] + p15[0]) / 2, p11[1] + 55, "4d*", 21, fill=RED, italic=True)
    svg.rect(1080, 180, 14, 14, RED, 1, RED)
    svg.text(1105, 187, "参考机", 18, anchor="start")
    svg.circle(1087, 235, 7, BLUE, 1, BLUE)
    svg.text(1105, 235, "跟随机", 18, anchor="start")
    svg.text(600, 675, "FY11-FY15 注入尺度；FY03、FY04 交替建锚；其余 11 架使用四参考机归槽", 21)
    svg.save(OUT / "fig06_q2_lattice_academic.svg")


def fig07():
    svg = SVG()
    gate = json.loads((ROOT / "results" / "q2" / "q2_program_gate.json").read_text(encoding="utf-8"))
    cases = gate["checks"]["actual_end_to_end_formation"]["evidence"]["cases"]
    values = {
        "节点位置": max(float(c["geometry"]["node_error"]) for c in cases),
        "相邻边长": max(float(c["geometry"]["edge_error"]) for c in cases),
        "共线距离": max(float(c["geometry"]["collinearity_error"]) for c in cases),
        "留出角": max(float(c["max_holdout_residual"]) for c in cases),
    }
    thresholds = {"节点位置": 2e-6, "相邻边长": 4e-6, "共线距离": 2e-6, "留出角": 2e-6}
    ratios = {k: values[k] / thresholds[k] for k in values}
    x0, y0, x1, y1 = 250, 100, 1070, 610
    svg.line(x0, y1, x1, y1, BLACK, 1.5)
    svg.line(x0, y0, x0, y1, BLACK, 1.5)
    # threshold-normalized horizontal axis 0..1
    for k in range(6):
        x = x0 + k * (x1 - x0) / 5
        svg.line(x, y0, x, y1, LIGHT, 1)
        svg.text(x, y1 + 26, f"{k/5:.1f}", 17)
    svg.line(x1, y0, x1, y1, RED, 2, "8 6")
    svg.text(x1 - 8, 75, "验收阈值", 18, anchor="end", fill=RED)
    names = list(values)
    for idx, name in enumerate(names):
        y = y0 + 75 + idx * 110
        svg.text(x0 - 25, y, name, 20, anchor="end")
        bar = ratios[name] * (x1 - x0)
        svg.rect(x0, y - 18, bar, 36, BLUE, 1, BLUE)
        unit = "rad" if name == "留出角" else "d*"
        svg.text(x0 + bar + 12, y, f"{values[name]:.2e} {unit}", 18, anchor="start", fill=BLACK)
    svg.text(660, 665, "最坏误差 / 对应验收阈值（33/33 个端到端算例通过）", 21)
    svg.save(OUT / "fig07_q2_acceptance_ratios_academic.svg")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for fn in (fig01, fig02, fig03, fig04, fig05, fig06, fig07):
        fn()
    files = sorted(OUT.glob("fig*.svg"))
    print(f"SVG_COUNT={len(files)}")
    for path in files:
        print(path)


if __name__ == "__main__":
    main()
