# -*- coding: utf-8 -*-
"""
==============================================================================
  مُصيِّر اللقطة 2 — بالمحرك الجديد (أطراف ثنائية + IK + رسوم معاد رسمها)
==============================================================================
"""
import os, sys, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig_engine2 import Rig2
from motion2 import walk_pose, idle_pose

W, H = 1920, 1080
FPS = 25
R2 = "/home/user/Animation-cartoon/تجربة/studio_rigs2"
WORLD = R2 + "/world"
REND = "/home/user/Animation-cartoon/تجربة/production_engine/_renders2"
os.makedirs(REND, exist_ok=True)

WMAP = json.load(open(WORLD + "/world_map.json", encoding="utf-8"))
_cache = {}


def wimg(name):
    if name not in _cache:
        _cache[name] = Image.open(WORLD + "/" + name + ".png").convert("RGBA")
    return _cache[name]


def place(canvas, name, ox, oy, s, rot=0.0, piv=None, alpha=255):
    """يرسم جزءاً من العالم؛ (ox,oy) = موضع نقطة التصميم (0,0) على الشاشة"""
    im = wimg(name)
    bb = WMAP[name]["bbox"]
    if abs(s - 1.0) > 1e-6:
        im = im.resize((max(1, int(im.width*s)), max(1, int(im.height*s))), Image.LANCZOS)
    if alpha < 255:
        im = im.copy()
        im.putalpha(im.split()[3].point(lambda p: int(p*alpha/255)))
    if rot and piv is not None:
        px = (piv[0] - bb[0]) * s
        py = (piv[1] - bb[1]) * s
        r = im.rotate(-rot, resample=Image.BICUBIC, center=(px, py), expand=True)
        a = math.radians(-rot)
        cx, cy = im.width/2.0, im.height/2.0
        ddx, ddy = px-cx, py-cy
        npx = r.width/2.0 + (ddx*math.cos(a) - ddy*math.sin(a))
        npy = r.height/2.0 + (ddx*math.sin(a) + ddy*math.cos(a))
        tx = ox + bb[0]*s + px - npx
        ty = oy + bb[1]*s + py - npy
        canvas.alpha_composite(r, (int(round(tx)), int(round(ty))))
    else:
        canvas.alpha_composite(im, (int(round(ox + bb[0]*s)), int(round(oy + bb[1]*s))))


# ---------------------------------------------------------------------------
LOCO_S = 1.30
LOCO_OX, LOCO_OY = 250, 330
WHEELS = [(210, 392), (395, 392), (600, 392)]
WINDOWS = [(206, 140, 296, 224), (316, 140, 404, 224), (424, 140, 498, 224)]
SPEEDS = [0.0, 0.12, 0.35, 1.0, 1.55]
BGS = ["bg_01_sky", "bg_02_far_hills", "bg_03_mid", "bg_04_road", "bg_05_fore"]


def render_bg(canvas, scroll):
    for name, sp in zip(BGS, SPEEDS):
        img = wimg(name)
        dx = int(scroll*sp) % W
        tile = Image.new("RGBA", (W*2, H), (0, 0, 0, 0))
        tile.alpha_composite(img, (0, 0))
        tile.alpha_composite(img, (W, 0))
        canvas.alpha_composite(tile.crop((dx, 0, dx+W, H)), (0, 0))
    return canvas


def render_loco(canvas, f, interior):
    s = LOCO_S
    for i, (wx, wy) in enumerate(WHEELS):
        bob = 5*math.sin(f*0.26 + i*1.1)
        place(canvas, "loco_spring", LOCO_OX, LOCO_OY, s, 0.0)
        place(canvas, "loco_wheel", LOCO_OX, LOCO_OY, s,
              rot=f*26.0, piv=(wx, wy + bob))
    # الركّاب داخل المقصورة (تُرسم قبل الهيكل => تظهر عبر ثقوب النوافذ)
    for img, (cx, cy) in interior:
        canvas.alpha_composite(img, (int(cx - img.width/2), int(cy - img.height/2)))
    place(canvas, "loco_chassis", LOCO_OX, LOCO_OY, s)
    place(canvas, "loco_fan", LOCO_OX, LOCO_OY, s, rot=f*44.0, piv=(706, 224))
    for i in range(3):
        t = ((f*0.055) + i*0.34) % 1.0
        place(canvas, "loco_steam", LOCO_OX, LOCO_OY, s*(0.34 + t*0.85),
              alpha=int(240*(1-t)), piv=None)
    return canvas


def head_top_offset(rig):
    """المسافة من الحوض إلى أعلى الرأس (تصميم) — محسوبة من الطبقة نفسها"""
    hp = rig.map["parts"]["head"]
    neck_y = rig.S["neck"][1]
    top_design = neck_y - hp["pivot_png"][1]
    return rig.S["hip"][1] - top_design


# ---------------------------------------------------------------------------
def build(cid, scale, pelvis, f, mode="idle", mouth=None, eyes=None, cycle=26, phase=0.0):
    rig = RIGS[cid]
    if mode == "walk":
        pose = walk_pose(rig, f, cycle=cycle, scale=scale, pelvis=pelvis,
                         phase=phase, mouth=mouth, eyes=eyes)
    else:
        pose = idle_pose(rig, f, scale=scale, pelvis=pelvis, mouth=mouth, eyes=eyes)
    cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rig.render(cv, pose)
    bb = cv.getbbox()
    return cv.crop(bb) if bb else cv


RIGS = {c: Rig2(c) for c in ["soufan", "salma", "fares", "simsim"]}


def render_frame(f, n_frames, dialogue):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    render_bg(canvas, f*11.0)

    # --- الركّاب داخل القاطرة ---
    interior = []
    win_top = LOCO_OY + WINDOWS[0][1]*LOCO_S
    win_bot = LOCO_OY + WINDOWS[0][3]*LOCO_S
    plan = [("soufan", 0, 0.40), ("salma", 1, 0.42), ("fares", 2, 0.42)]
    for cid, wi, sc in plan:
        rig = RIGS[cid]
        x0, y0, x1, y1 = WINDOWS[wi]
        cx = LOCO_OX + (x0+x1)/2*LOCO_S
        off = head_top_offset(rig)*sc
        py = win_top + 10 + off
        mv = dialogue.get("mouth", {}).get(str(f)) if cid == "soufan" else None
        ev = dialogue.get("eyes", {}).get(str(f)) if cid == "soufan" else None
        img = build(cid, sc, [cx, py], f, mode="idle", mouth=mv, eyes=ev)
        # قصّ على النافذة
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.alpha_composite(img, (int(cx-img.width/2), int(py-img.height/2)))
        interior.append((img, (cx, py)))
        # نستبدل الطبقة بقناع النافذة
        masked = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        msk = Image.new("L", (W, H), 0)
        wx0 = LOCO_OX + x0*LOCO_S
        wx1 = LOCO_OX + x1*LOCO_S
        ImageDraw.Draw(msk).rectangle([int(wx0), int(win_top), int(wx1), int(win_bot)], fill=255)
        interior[-1] = (Image.composite(layer, Image.new("RGBA", (W, H), (0, 0, 0, 0)), msk)
                        .crop((int(wx0)-20, int(win_top)-20, int(wx1)+20, int(win_bot)+20)),
                        ((wx0+wx1)/2, (win_top+win_bot)/2))

    render_loco(canvas, f, interior)

    # --- سمسم يخبّ على الطريق ---
    sim = build("simsim", 0.62, [1430 - (f*1.4), 1000], f, mode="walk",
                cycle=18, phase=0.0)
    canvas.alpha_composite(sim, (int(1430 - (f*1.4) - sim.width/2), int(1000 - sim.height*0.96)))

    return canvas.convert("RGB")


def encode(prefix, fps=FPS):
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    src = REND + "/%s_frames/f%%04d.png" % prefix
    dst = REND + "/%s.mp4" % prefix
    subprocess.run([exe, "-y", "-framerate", str(fps), "-i", src,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", dst],
                   check=True, capture_output=True)
    return dst


if __name__ == "__main__":
    tl = json.load(open("/home/user/Animation-cartoon/تجربة/production_engine/tests/lipsync_result_timeline.json",
                        encoding="utf-8"))
    swaps = tl.get("swaps", tl)
    dialogue = {"mouth": swaps.get("soufan.mouth", {}), "eyes": swaps.get("soufan.eyes", {})}
    N = tl.get("duration", 74)
    os.makedirs(REND + "/SHOT02_frames", exist_ok=True)
    for f in range(N):
        render_frame(f, N, dialogue).save(REND + "/SHOT02_frames/f%04d.png" % f)
        if f % 15 == 0:
            print("  frame", f)
    print("✔", encode("SHOT02"))
