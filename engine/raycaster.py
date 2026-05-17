"""
doom-in-readme — raycaster engine
Renders a DOOM-like 3D view as an SVG image.
State is persisted in state/game.json.
"""

import math
import json
import os
import sys

# ── constants ────────────────────────────────────────────────────────────────

WIDTH = 60        # ray columns
HEIGHT = 40       # SVG rows (visual height units)
FOV = math.pi / 3
MOVE_SPEED = 0.4
ROT_SPEED = 0.12

SVG_W = 600
SVG_H = 400
COL_W = SVG_W // WIDTH

# ── map ───────────────────────────────────────────────────────────────────────
# 1 = wall, 0 = floor, S = start

MAP = [
    "####################",
    "#........#.........#",
    "#........#.........#",
    "#....##..#....###..#",
    "#....#...#.........#",
    "#....#...######....#",
    "#........#.........#",
    "#........#....#....#",
    "#...####.#....#....#",
    "#........#.........#",
    "#........#.........#",
    "####.###.#....#....#",
    "#........#....#....#",
    "#........######....#",
    "#........#.........#",
    "#........#.....#...#",
    "#....#...#.....#...#",
    "#....#...#.....#...#",
    "#....#.............#",
    "####################",
]

MAP_W = len(MAP[0])
MAP_H = len(MAP)

# ── colors ────────────────────────────────────────────────────────────────────

WALL_COLORS = [
    "#8B0000", "#A00000", "#B50000", "#CC0000",
    "#E00000", "#FF1111", "#FF3333", "#FF5555",
]
CEILING_COLOR = "#111111"
FLOOR_COLOR   = "#1a1a1a"
ENEMY_COLOR   = "#00FF41"

# ── state ─────────────────────────────────────────────────────────────────────

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "state", "game.json")

DEFAULT_STATE = {
    "x": 2.5,
    "y": 2.5,
    "angle": 0.0,
    "health": 100,
    "ammo": 50,
    "kills": 0,
    "messages": [],
    "enemies": [
        {"x": 10.5, "y": 5.5, "alive": True},
        {"x": 15.5, "y": 10.5, "alive": True},
        {"x": 5.5,  "y": 15.5, "alive": True},
        {"x": 17.5, "y": 3.5,  "alive": True},
        {"x": 8.5,  "y": 12.5, "alive": True},
    ]
}

def load_state():
    try:
        with open(STATE_PATH) as f:
            s = json.load(f)
            # migrate missing keys
            for k, v in DEFAULT_STATE.items():
                if k not in s:
                    s[k] = v
            return s
    except Exception:
        return dict(DEFAULT_STATE)

def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

# ── map helpers ───────────────────────────────────────────────────────────────

def is_wall(x, y):
    mx, my = int(x), int(y)
    if mx < 0 or my < 0 or mx >= MAP_W or my >= MAP_H:
        return True
    return MAP[my][mx] == "#"

# ── raycaster ─────────────────────────────────────────────────────────────────

def cast_ray(px, py, angle):
    ray_cos = math.cos(angle)
    ray_sin = math.sin(angle)

    for depth in [i * 0.05 for i in range(1, 400)]:
        rx = px + ray_cos * depth
        ry = py + ray_sin * depth
        if is_wall(rx, ry):
            return depth, rx, ry
    return 20.0, px + ray_cos * 20, py + ray_sin * 20

# ── enemy projection ──────────────────────────────────────────────────────────

def project_enemy(px, py, pangle, ex, ey):
    dx = ex - px
    dy = ey - py
    dist = math.sqrt(dx*dx + dy*dy)
    if dist < 0.1:
        return None

    enemy_angle = math.atan2(dy, dx)
    delta = enemy_angle - pangle
    # normalize
    while delta > math.pi:  delta -= 2 * math.pi
    while delta < -math.pi: delta += 2 * math.pi

    if abs(delta) > FOV / 2 + 0.1:
        return None

    screen_x = int((delta / FOV + 0.5) * SVG_W)
    h = int(SVG_H / (dist + 0.001) * 0.8)
    return {"screen_x": screen_x, "dist": dist, "h": h}

# ── SVG renderer ──────────────────────────────────────────────────────────────

def render_svg(state):
    px    = state["x"]
    py    = state["y"]
    angle = state["angle"]

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" style="background:#000;font-family:monospace">')

    # ceiling
    lines.append(f'<rect x="0" y="0" width="{SVG_W}" height="{SVG_H//2}" fill="{CEILING_COLOR}"/>')
    # floor
    lines.append(f'<rect x="0" y="{SVG_H//2}" width="{SVG_W}" height="{SVG_H//2}" fill="{FLOOR_COLOR}"/>')

    # walls
    z_buffer = [999.0] * SVG_W
    for col in range(WIDTH):
        ray_angle = angle - FOV / 2 + FOV * col / WIDTH
        dist, _, _ = cast_ray(px, py, ray_angle)

        # fix fisheye
        dist_fixed = dist * math.cos(ray_angle - angle)
        dist_fixed = max(dist_fixed, 0.1)

        wall_h = int(SVG_H / dist_fixed * 0.9)
        wall_h = min(wall_h, SVG_H)

        shade_idx = min(int(dist_fixed * 1.2), len(WALL_COLORS) - 1)
        color = WALL_COLORS[-(shade_idx + 1)]

        x0 = col * COL_W
        y0 = (SVG_H - wall_h) // 2
        lines.append(f'<rect x="{x0}" y="{y0}" width="{COL_W}" height="{wall_h}" fill="{color}"/>')

        # store z for enemies
        for px2 in range(x0, x0 + COL_W):
            if px2 < SVG_W:
                z_buffer[px2] = dist_fixed

    # enemies
    for enemy in state.get("enemies", []):
        if not enemy.get("alive", True):
            continue
        proj = project_enemy(px, py, angle, enemy["x"], enemy["y"])
        if proj is None:
            continue
        if proj["dist"] > z_buffer[min(proj["screen_x"], SVG_W-1)]:
            continue  # occluded by wall

        eh = proj["h"]
        ex = proj["screen_x"] - eh // 4
        ey = (SVG_H - eh) // 2
        ew = eh // 2

        # draw enemy as ASCII-art sprite boxes
        lines.append(f'<rect x="{ex}" y="{ey}" width="{ew}" height="{eh}" fill="#001a00" stroke="{ENEMY_COLOR}" stroke-width="1"/>')
        # eyes
        eye_y = ey + eh // 5
        lines.append(f'<rect x="{ex + ew//4}" y="{eye_y}" width="{max(ew//6,2)}" height="{max(eh//8,2)}" fill="{ENEMY_COLOR}"/>')
        lines.append(f'<rect x="{ex + ew*3//5}" y="{eye_y}" width="{max(ew//6,2)}" height="{max(eh//8,2)}" fill="{ENEMY_COLOR}"/>')

    # HUD — health bar
    hud_y = SVG_H - 36
    lines.append(f'<rect x="0" y="{hud_y}" width="{SVG_W}" height="36" fill="#000000cc"/>')

    hp = state.get("health", 100)
    hp_color = "#00ff41" if hp > 50 else ("#ffaa00" if hp > 25 else "#ff2222")
    hp_w = int(SVG_W * 0.3 * hp / 100)
    lines.append(f'<rect x="10" y="{hud_y+8}" width="{int(SVG_W*0.3)}" height="12" fill="#222" rx="2"/>')
    lines.append(f'<rect x="10" y="{hud_y+8}" width="{hp_w}" height="12" fill="{hp_color}" rx="2"/>')
    lines.append(f'<text x="10" y="{hud_y+30}" fill="{hp_color}" font-size="10">HP {hp}</text>')

    # ammo
    ammo = state.get("ammo", 50)
    lines.append(f'<text x="{SVG_W//2 - 20}" y="{hud_y+28}" fill="#ffaa00" font-size="14" font-weight="bold">AMMO {ammo}</text>')

    # kills
    kills = state.get("kills", 0)
    lines.append(f'<text x="{SVG_W - 80}" y="{hud_y+28}" fill="#ff4444" font-size="12">KILLS {kills}</text>')

    # crosshair
    cx, cy = SVG_W // 2, SVG_H // 2
    lines.append(f'<line x1="{cx-8}" y1="{cy}" x2="{cx+8}" y2="{cy}" stroke="#ffffff88" stroke-width="1"/>')
    lines.append(f'<line x1="{cx}" y1="{cy-8}" x2="{cx}" y2="{cy+8}" stroke="#ffffff88" stroke-width="1"/>')

    # last message
    msgs = state.get("messages", [])
    if msgs:
        msg = msgs[-1]
        lines.append(f'<text x="{SVG_W//2}" y="20" fill="#00ff41" font-size="11" text-anchor="middle">{msg}</text>')

    lines.append("</svg>")
    return "\n".join(lines)

# ── commands ──────────────────────────────────────────────────────────────────

def apply_command(state, cmd):
    cmd = cmd.strip().lower()
    msg = None

    if cmd == "w":
        nx = state["x"] + math.cos(state["angle"]) * MOVE_SPEED
        ny = state["y"] + math.sin(state["angle"]) * MOVE_SPEED
        if not is_wall(nx, state["y"]): state["x"] = nx
        if not is_wall(state["x"], ny): state["y"] = ny
        msg = "moved forward"

    elif cmd == "s":
        nx = state["x"] - math.cos(state["angle"]) * MOVE_SPEED
        ny = state["y"] - math.sin(state["angle"]) * MOVE_SPEED
        if not is_wall(nx, state["y"]): state["x"] = nx
        if not is_wall(state["x"], ny): state["y"] = ny
        msg = "moved back"

    elif cmd == "a":
        state["angle"] -= ROT_SPEED
        msg = "turned left"

    elif cmd == "d":
        state["angle"] += ROT_SPEED
        msg = "turned right"

    elif cmd in ("shoot", "fire", "e"):
        if state.get("ammo", 0) <= 0:
            msg = "out of ammo!"
        else:
            state["ammo"] -= 1
            hit = False
            for enemy in state.get("enemies", []):
                if not enemy.get("alive", True):
                    continue
                proj = project_enemy(
                    state["x"], state["y"], state["angle"],
                    enemy["x"], enemy["y"]
                )
                if proj and abs(proj["screen_x"] - SVG_W // 2) < SVG_W // WIDTH * 2:
                    if proj["dist"] < 8:
                        enemy["alive"] = False
                        state["kills"] = state.get("kills", 0) + 1
                        msg = f"ENEMY DOWN! kills: {state['kills']}"
                        hit = True
                        break
            if not hit and msg is None:
                msg = "BANG! missed"

    elif cmd == "reset":
        return dict(DEFAULT_STATE), "game reset"

    else:
        msg = f"unknown command: {cmd}"

    if msg:
        msgs = state.get("messages", [])
        msgs.append(msg)
        state["messages"] = msgs[-5:]  # keep last 5

    return state, msg

# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    state = load_state()

    if cmd:
        state, msg = apply_command(state, cmd)
        print(f"Command: {cmd} → {msg}")

    svg = render_svg(state)
    save_state(state)

    out_path = os.path.join(os.path.dirname(__file__), "..", "frame.svg")
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"Frame rendered → frame.svg")
