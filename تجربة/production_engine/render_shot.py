# -*- coding: utf-8 -*-
"""
==============================================================================
  مُصيِّر اللقطة — «رحلة الجد صوفان»
  Shot Renderer · Phase 5
==============================================================================

يجمع كل شيء في لقطة واحدة قابلة للتكرار:
  • خمس طبقات خلفية تتحرك بسرعات Parallax مختلفة
  • القاطرة: عجلات دوّارة + مروحة دوّارة + نفثات بخار + تعليق نابض
  • ثلاث شخصيات داخل المقصورة تظهر عبر النوافذ الشفافة
  • الجد صوفان يتكلّم: طبقة فمه تُبدَّل إطاراً بإطار من تحليل الصوت
  • سمسم يخبّ على الطريق بدورته الخاصة (أسرع + أعلى نطّاً + ذيل وأذنان)
  • رمش العينين من جدول الأحداث

ثم يمزج الفيديو مع شريط الصوت (حوار + محيطي بلا موسيقى).
==============================================================================
"""
import os, sys, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig_engine import Rig, Locomotive, ParallaxBackground
from motion_cycles import sample_cycle, CYCLE_SHEEP_WALK, CYCLE_PUPPY_TROT, CYCLE_IDLE_BREATH, CYCLE_TAIL_WAG

W, H = 1280, 720
FPS = 25
RENDERS = "/home/user/Animation-cartoon/تجربة/production_engine/_renders"
ENG = "/home/user/Animation-cartoon/تجربة/production_engine"


# ---------------------------------------------------------------------------
def cycle_to_rot(sample, exclude_bob=True):
    rot = {}
    for k, v in sample.items():
        if k.endswith(".rot"):
            rot[k[:-4]] = v
    return rot


def render_character(rig, pose, canvas_size=(700, 640)):
    c = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    rig.render(c, pose)
    bb = c.getbbox()
    return c.crop(bb) if bb else c


# ---------------------------------------------------------------------------
def render_shot(dialogue_timeline, n_frames, out_prefix, title=None, subtitle=None):
    bgm = ParallaxBackground(size=(W, H))
    loco = Locomotive()
    rigs = {c: Rig(c) for c in ["soufan", "salma", "fares", "simsim"]}

    LOCO_POS = [230, 150]
    LOCO_S = 1.10

    # مراكز النوافذ بالشاشة (محسوبة من إحداثيات النوافذ داخل ملف الهيكل)
    bx, by = LOCO_POS[0] - 50 * LOCO_S, LOCO_POS[1] + 80 * LOCO_S
    win_centers = []
    for (x0, x1) in [(185, 272), (292, 378), (398, 475)]:
        win_centers.append((
            bx + (x0 + x1) / 2 * LOCO_S,
            by + 122 * LOCO_S,          # أعلى النافذة
            by + 200 * LOCO_S           # أسفل النافذة
        ))
    CLIP = (bx + 185 * LOCO_S, by + 122 * LOCO_S, bx + 475 * LOCO_S, by + 200 * LOCO_S)

    interior_plan = [
        ("soufan", win_centers[0], 0.50),
        ("salma",  win_centers[1], 0.42),
        ("fares",  win_centers[2], 0.42),
    ]

    os.makedirs(f"{RENDERS}/{out_prefix}_frames", exist_ok=True)
    mouth_chart = []

    for f in range(n_frames):
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

        # 1) الخلفية 2.5D
        bgm.render(canvas, scroll_px=f * 9.0)

        # 2) الشخصيات داخل المقصورة (تُرسم قبل الهيكل => تظهر عبر النوافذ الشفافة)
        interior_imgs = []
        for cid, (wcx, wtop, wbot), sc in interior_plan:
            if cid == "soufan":
                # الجد: يتكلّم => الفم من جدول التحليل + تنفّس خفيف
                s = sample_cycle(CYCLE_IDLE_BREATH, f)
                rot = cycle_to_rot(s)
                mv = dialogue_timeline.get("mouth", {}).get(str(f))
                ev = dialogue_timeline.get("eyes", {}).get(str(f))
                swaps = {}
                if mv: swaps["mouth"] = mv
                if ev: swaps["eyes"] = ev
                mouth_chart.append((f, mv or ("closed" if not mv else mv), swaps))
                pose = {"pos": [350, 470], "scale": 1.25 * sc,
                        "rot": rot, "swaps": swaps}
            else:
                s = sample_cycle(CYCLE_IDLE_BREATH, f + (0 if cid == "salma" else 24))
                pose = {"pos": [350, 470],
                        "scale": rigs[cid].spec["default_scale"] * sc,
                        "rot": cycle_to_rot(s), "swaps": {}}
            img = render_character(rigs[cid], pose)
            # قصّ إلى منطقة النافذة
            px = int(wcx - img.width / 2)
            py = int(wtop - 18)   # يرفع الشخصية ليظهر الرأس والفم داخل النافذة
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            layer.alpha_composite(img, (px, py))
            mask = Image.new("L", (W, H), 0)
            ImageDraw.Draw(mask).rectangle(
                [int(CLIP[0]), int(CLIP[1]), int(CLIP[2]), int(CLIP[3])], fill=255)
            # قصّ الشخصية على منطقة النوافذ فقط
            canvas.alpha_composite(Image.composite(
                layer, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask))

        # 3) القاطرة بكل طبقاتها الميكانيكية
        loco.render(canvas, {
            "pos": LOCO_POS, "scale": LOCO_S,
            "wheel_rot": f * 24,
            "fan_rot": f * 41,
            "bob": f * 0.26,
            "steam_t": (f * 0.055) % 1.0,
        })

        # 4) سمسم يخبّ على الطريق
        sp = sample_cycle(CYCLE_PUPPY_TROT, f)
        srot = cycle_to_rot(sp)
        pose = {"pos": [int(900 - (f * 0.7)), int(668 + sp.get("bob", 0) * 1.2)],
                "scale": 0.82, "rot": srot, "swaps": {}}
        # تصغير القفزة: bob داخل الدورة يجعله ينطّ فوق الطريق فعلياً
        sim_canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rigs["simsim"].render(sim_canvas, pose)
        canvas.alpha_composite(sim_canvas)

        out = canvas.convert("RGB")
        if title:
            d = ImageDraw.Draw(out)
            ft = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
            fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            d.text((W // 2, 34), title, font=ft, fill=(35, 25, 21), anchor="mm")
            if subtitle:
                d.text((W // 2, 66), subtitle, font=fs, fill=(80, 62, 52), anchor="mm")

        out.save(f"{RENDERS}/{out_prefix}_frames/f{f:04d}.png")

    return mouth_chart


# ---------------------------------------------------------------------------
def encode(prefix, fps=FPS):
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    src = f"{RENDERS}/{prefix}_frames/f%04d.png"
    dst = f"{RENDERS}/{prefix}.mp4"
    subprocess.run([exe, "-y", "-framerate", str(fps), "-i", src,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                    dst], check=True, capture_output=True)
    return dst


if __name__ == "__main__":
    tl = json.load(open(f"{ENG}/tests/lipsync_result_timeline.json", encoding="utf-8"))

    # تطبيع الشكل: يقبل {"soufan.mouth":{...}} أو {"swaps":{"soufan.mouth":{...}}}
    swaps = tl.get("swaps", tl)
    norm = {
        "duration": tl.get("duration", 74),
        "mouth": swaps.get("soufan.mouth", tl.get("mouth", {})),
        "eyes":  swaps.get("soufan.eyes",  tl.get("eyes", {})),
    }
    print(f"▶ جدول الفم: {len(norm['mouth'])} إطار | جدول الرمش: {sorted(int(k) for k in norm['eyes'])}")

    n = norm["duration"]
    chart = render_shot(norm, n, "SHOT01_talking_drive",
                        title="اللقطة 1 — الجد صوفان يقود ويتكلّم، وسمسم يخبّ على الطريق",
                        subtitle="كل حركة هنا من طبقات منفصلة + أرقام JSON — بلا أي توليد صور. ولا موسيقى.")
    mp4 = encode("SHOT01_talking_drive")

    # جدول الفم للمراجعة
    with open(f"{RENDERS}/SHOT01_mouth_chart.txt", "w", encoding="utf-8") as fh:
        fh.write("إطار | الزمن | حركة الفم المطبَّقة\n")
        fh.write("-" * 40 + "\n")
        for f, mv, sw in chart:
            fh.write(f"{f:4d} | {f/25:5.2f}s | {mv}\n")
    print("✔", mp4)
    print("✔", f"{RENDERS}/SHOT01_mouth_chart.txt")
