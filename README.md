<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d0000,50:1a0000,100:2d0000&height=160&section=header&text=doom-in-readme&fontSize=48&fontColor=ff2222&animation=fadeIn&fontAlignY=55&desc=DOOM.%20In%20a%20README.%20Playable%20via%20GitHub%20Issues.&descAlignY=75&descSize=14&descColor=888888" />

![GitHub Actions](https://img.shields.io/badge/engine-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![Python](https://img.shields.io/badge/renderer-Python_raycaster-ff2222?style=for-the-badge&logo=python&logoColor=white)
![SVG](https://img.shields.io/badge/output-SVG-orange?style=for-the-badge)
![Playable](https://img.shields.io/badge/status-PLAYABLE-00ff41?style=for-the-badge)

</div>

---

## Current frame

> **This image updates every time someone opens an issue with a move command.**

<div align="center">

![DOOM frame](frame.svg)

</div>

---

## How to play

Open a GitHub Issue with **exactly** one of these titles:

<div align="center">

| Issue title | Action |
|:-----------:|--------|
| `w` | ⬆️ Move forward |
| `s` | ⬇️ Move back |
| `a` | ⬅️ Turn left |
| `d` | ➡️ Turn right |
| `shoot` | 🔫 Shoot |
| `reset` | 🔄 Reset game |

</div>

**[→ Open an issue to make a move](../../issues/new)**

GitHub Actions picks up the issue, runs the raycaster, commits the new `frame.svg`, and closes the issue with a reply. Takes ~20 seconds.

---

## How it works

```
You open issue titled "w"
         │
         ▼
GitHub Actions triggers (issues: opened)
         │
         ▼
python engine/raycaster.py "w"
  ├─ loads state/game.json
  ├─ applies move to player position
  ├─ casts 60 rays via DDA algorithm
  ├─ projects enemies onto screen plane
  ├─ renders HUD (HP, AMMO, KILLS)
  └─ writes frame.svg + saves state
         │
         ▼
git commit "🎮 [w] frame update by @you"
git push
         │
         ▼
Issue gets a reply + closes automatically
         │
         ▼
README updates in real time (SVG is live)
```

---

## Engine

Pure Python raycaster — no dependencies, no pygame, no OpenGL.

- **DDA raycasting** — 60 rays per frame, fisheye correction
- **Enemy projection** — z-buffered sprite rendering
- **HUD** — health bar, ammo counter, kill counter
- **State** — persisted in `state/game.json` between moves
- **Map** — 20×20 hand-crafted maze with 5 enemies

```python
# the entire render pipeline in one line conceptually:
# for each column → cast ray → compute wall height → draw → project enemies → draw HUD
```

---

## Enemies

There are **5 demons** in the map. Find them and shoot them.

To hit an enemy:
- Face it (it needs to be near the center crosshair)
- Be within range (~8 units)
- Open issue: `shoot`

---

<div align="center">

[![Play now](https://img.shields.io/badge/▶_PLAY_NOW-open_an_issue-ff2222?style=for-the-badge)](../../issues/new)

[![](https://img.shields.io/badge/made%20by-stompingcrit-ff2222?style=for-the-badge&logo=github&logoColor=white)](https://github.com/stompingcrit)

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d0000,50:1a0000,100:2d0000&height=80&section=footer" />

</div>
