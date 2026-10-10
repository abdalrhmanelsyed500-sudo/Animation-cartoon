# -*- coding: utf-8 -*-
"""
==============================================================================
  تصميم الشخصيات — إعادة رسم كاملة
==============================================================================
كل الهندسة تُشتق من **هيكل عظمي واحد** بمعالم محسوبة. لا إحداثيات مُخمَّنة.
الأطراف ثنائية الأجزاء (فخذ/ساق، عضد/ساعد) لتسمح بثني الركبة والمرفق
وتثبيت القدم على الأرض أثناء المشي.

قاعدة الكود (مهم): لا تستخدم أبداً شرطة مائلة أو علامات اقتباس متداخلة
داخل تعبيرات f-string — بايثون 3.11 لا يسمح بذلك. كل قيمة تُحسب مسبقاً.
==============================================================================
"""
import math, os, json
from art_lib import (cr_closed, cr_open, blob, capsule, tapered, ellipse_d,
                     cel, detail_stroke, render_svg, bbox_of, OUTLINE)

OL = OUTLINE


# ---------------------------------------------------------------------------
# 1) الهيكل العظمي — مصدر الحقيقة الوحيد
# ---------------------------------------------------------------------------
def skeleton(H, n_heads, body_hw=0.155, shoulder_hw=0.112, hip_hw=0.072,
             head_hw=0.118, knee_frac=0.52):
    hh = H / n_heads
    shoulder_y = hh * 1.18
    hip_y = H * 0.66                      # الورك عند ثلثي الطول دائماً (نسبة تشريحية ثابتة)
    if hip_y < shoulder_y + 0.16*H:       # حماية: لا جذع أقصر من 16% من الطول
        hip_y = shoulder_y + 0.16*H
    ankle_y = H * 0.955
    knee_y = hip_y + (ankle_y - hip_y) * knee_frac
    return {
        "H": H, "hh": hh, "n_heads": n_heads,
        "head_hw": head_hw * H,
        "face_top": hh * 0.34,
        "face_bot": hh * 1.00,
        "face_hw": head_hw * H * 0.78,
        "chin": hh * 1.00,
        "neck": (0.0, hh * 1.06),
        "shoulder": (shoulder_hw * H, shoulder_y),
        "chest": hh * 1.45,
        "waist": hh * 1.82,
        "hip": (hip_hw * H, hip_y),
        "knee": knee_y,
        "ankle": ankle_y,
        "ground": H,
        "torso_cy": (shoulder_y + hip_y) / 2.0,
        "torso_hw": body_hw * H,
        "body_hw": body_hw * H,
        "elbow": (shoulder_hw * H * 1.12, hh * 1.72),
        "wrist": (shoulder_hw * H * 1.20, hh * 2.30),
    }


# ---------------------------------------------------------------------------
# 2) الألوان
# ---------------------------------------------------------------------------
def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rgb2hex(c):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(v))) for v in c)


def shade(h, k):
    r, g, b = hex2rgb(h)
    if k < 1:
        return rgb2hex((r*k, g*k, b*k))
    return rgb2hex((r + (255-r)*(k-1), g + (255-g)*(k-1), b + (255-b)*(k-1)))


def palette(base, back=False):
    if not back:
        return base
    return {k: (shade(v, 0.80) if (isinstance(v, str) and v.startswith("#")) else v)
            for k, v in base.items()}


# ---------------------------------------------------------------------------
# 3) أشكال الرأس والأذن
# ---------------------------------------------------------------------------
def head_silhouette(hw, top, bot):
    fh = bot - top
    r = [(0.00,   top + 0.00*fh), (0.40*hw, top + 0.03*fh), (0.76*hw, top + 0.12*fh),
         (1.00*hw, top + 0.29*fh), (0.99*hw, top + 0.45*fh), (0.86*hw, top + 0.60*fh),
         (0.62*hw, top + 0.76*fh), (0.38*hw, top + 0.90*fh), (0.16*hw, top + 0.98*fh),
         (0.00,   top + 1.00*fh)]
    pts = r + [(-x, y) for (x, y) in reversed(r)][1:]
    return cr_closed(pts, 0.9)


def ear_shape(x, y, L, W, droop, flip=1):
    spine = [(x, y)]
    for i in range(1, 10):
        t = i/9.0
        ang = math.radians(droop*t)
        spine.append((x + flip*L*math.sin(ang), y + L*t*0.92))
    widths = [W*(0.55 - 0.30*(i/9.0)) for i in range(10)]
    return tapered(spine, widths)


# ===========================================================================
# 4) شخصية الخروف (صوفان / سلمى / فارس)
# ===========================================================================
def build_sheep(spec):
    S = skeleton(spec["H"], spec["n_heads"],
                 body_hw=spec.get("body_hw", 0.155),
                 shoulder_hw=spec.get("shoulder_hw", 0.112),
                 hip_hw=spec.get("hip_hw", 0.072),
                 head_hw=spec.get("head_hw", 0.118))
    C = spec["colors"]
    H = S["H"]
    hh = S["hh"]
    parts = {}

    # ---------------- الجذع ----------------
    def torso(back=False):
        p = palette(C, back)
        wool = p["wool"]; wool_sh = p["wool_sh"]
        cloth = p["cloth"]; cloth_sh = p["cloth_sh"]
        leather = p.get("leather", "#5C4033")
        brass = p["brass"]
        accent2 = p.get("accent2", "#4A6B53")
        hw = S["torso_hw"]
        top = S["shoulder"][1] - hh*0.14
        bot = S["hip"][1] + hh*0.10
        ry = (bot - top)/2.0
        d = blob(0, (top+bot)/2, hw, ry, n=26, lobes=7, amp=0.055, phase=0.6)
        bbox = (-hw*1.15, top-hw*0.25, hw*1.15, bot+hw*0.25)

        det = []
        for i in range(4):
            yy = top + ry*(0.45 + i*0.30)
            xx = (-1 if i % 2 else 1) * hw*0.42
            det.append(detail_stroke(
                cr_open([(xx-hw*0.22, yy), (xx, yy-ry*0.13), (xx+hw*0.22, yy)], 0.9),
                wool_sh, 3.4, 0.85))
        body = cel(d, bbox, wool, wool_sh, sw=6.0, details=det, uid="tw")

        outfit = spec["outfit"]
        sy = S["shoulder"][1]
        hy = S["hip"][1]
        g = []

        if outfit == "vest_petrol":
            sw_x = S["shoulder"][0]*0.96
            d1 = cr_closed([(-sw_x, sy+2), (-hw*0.55, sy-6), (-hw*0.72, hy-hh*0.30),
                            (-sw_x*0.62, hy+4), (-sw_x*0.80, hy+6), (-sw_x*0.86, sy+8)], 0.9)
            d2 = cr_closed([(sw_x, sy+2), (hw*0.55, sy-6), (hw*0.72, hy-hh*0.30),
                            (sw_x*0.62, hy+4), (sw_x*0.80, hy+6), (sw_x*0.86, sy+8)], 0.9)
            g.append('<path d="' + d1 + '" fill="' + cloth + '" stroke="' + OL +
                     '" stroke-width="4.5" stroke-linejoin="round"/>')
            g.append('<path d="' + d2 + '" fill="' + cloth + '" stroke="' + OL +
                     '" stroke-width="4.5" stroke-linejoin="round"/>')
            for sx in (-1, 1):
                px = sx*hw*0.50
                py = hy - hh*0.22
                g.append('<rect x="' + format(px-26, '.1f') + '" y="' + format(py, '.1f') +
                         '" width="52" height="46" rx="9" fill="' + cloth_sh +
                         '" stroke="' + OL + '" stroke-width="4"/>')
            g.append('<path d="M ' + format(hw*0.50, '.1f') + ' ' + format(hy-hh*0.22, '.1f') +
                     ' L ' + format(hw*0.62, '.1f') + ' ' + format(hy-hh*0.55, '.1f') +
                     '" stroke="' + brass + '" stroke-width="9" stroke-linecap="round"/>')
            g.append('<circle cx="' + format(hw*0.645, '.1f') + '" cy="' + format(hy-hh*0.62, '.1f') +
                     '" r="10" fill="none" stroke="' + brass + '" stroke-width="5.5"/>')

        elif outfit == "tunic_mustard":
            hy2 = hy + hh*0.06
            dt = cr_closed([(-hw*0.86, sy+4), (-hw*0.50, sy-8), (hw*0.50, sy-8), (hw*0.86, sy+4),
                            (hw*0.92, hy2-hh*0.10), (hw*0.70, hy2), (0, hy2+hh*0.08),
                            (-hw*0.70, hy2), (-hw*0.92, hy2-hh*0.10)], 0.9)
            g.append('<path d="' + dt + '" fill="' + cloth + '" stroke="' + OL +
                     '" stroke-width="5" stroke-linejoin="round"/>')
            dc = cr_closed([(-hw*0.34, sy+2), (0, sy+hh*0.20), (hw*0.34, sy+2),
                            (hw*0.20, sy-8), (-hw*0.20, sy-8)], 0.9)
            g.append('<path d="' + dc + '" fill="' + accent2 + '" stroke="' + OL +
                     '" stroke-width="4" stroke-linejoin="round"/>')
            g.append('<path d="M ' + format(-hw*0.30, '.1f') + ' ' + format(sy+hh*0.10, '.1f') +
                     ' L ' + format(hw*0.66, '.1f') + ' ' + format(hy2-hh*0.06, '.1f') +
                     '" stroke="' + leather + '" stroke-width="14" stroke-linecap="round"/>')
            g.append('<rect x="' + format(hw*0.42, '.1f') + '" y="' + format(hy2-hh*0.46, '.1f') +
                     '" width="66" height="56" rx="10" fill="' + leather +
                     '" stroke="' + OL + '" stroke-width="4.5"/>')
            g.append('<rect x="' + format(hw*0.46, '.1f') + '" y="' + format(hy2-hh*0.62, '.1f') +
                     '" width="42" height="24" rx="4" fill="#FFFDF7" stroke="' + OL +
                     '" stroke-width="3.6"/>')

        elif outfit == "vest_brick":
            d1 = cr_closed([(-hw*0.80, sy+2), (-hw*0.46, sy-8), (-hw*0.60, hy-hh*0.28),
                            (-hw*0.52, hy+2), (-hw*0.74, hy+4), (-hw*0.82, sy+8)], 0.9)
            d2 = cr_closed([(hw*0.80, sy+2), (hw*0.46, sy-8), (hw*0.60, hy-hh*0.28),
                            (hw*0.52, hy+2), (hw*0.74, hy+4), (hw*0.82, sy+8)], 0.9)
            g.append('<path d="' + d1 + '" fill="' + cloth + '" stroke="' + OL +
                     '" stroke-width="4.5" stroke-linejoin="round"/>')
            g.append('<path d="' + d2 + '" fill="' + cloth + '" stroke="' + OL +
                     '" stroke-width="4.5" stroke-linejoin="round"/>')
            g.append('<path d="M ' + format(-hw*0.86, '.1f') + ' ' + format(hy-hh*0.10, '.1f') +
                     ' Q 0 ' + format(hy+hh*0.10, '.1f') + ' ' + format(hw*0.86, '.1f') + ' ' +
                     format(hy-hh*0.10, '.1f') + '" fill="none" stroke="' + leather +
                     '" stroke-width="11" stroke-linecap="round"/>')
            g.append('<rect x="' + format(hw*0.44, '.1f') + '" y="' + format(hy-hh*0.30, '.1f') +
                     '" width="52" height="40" rx="8" fill="' + leather +
                     '" stroke="' + OL + '" stroke-width="4"/>')
            g.append('<circle cx="' + format(hw*0.44+26, '.1f') + '" cy="' +
                     format(hy-hh*0.30+20, '.1f') + '" r="7" fill="' + brass + '"/>')

        body += "".join(g)
        return body, bbox

    parts["torso"] = {"draw": torso, "pivot": (0.0, S["hip"][1])}

    # ---------------- الرأس ----------------
    def head(back=False):
        p = palette(C, back)
        wool = p["wool"]; wool_sh = p["wool_sh"]
        skin = p["skin"]; skin_sh = p["skin_sh"]
        hw = S["head_hw"]
        top = S["face_top"]
        bot = S["face_bot"]
        fh = bot - top
        g = []

        # الأذنان خلف الرأس
        for sx in (-1, 1):
            d_ear = ear_shape(sx*hw*0.86, top + fh*0.42, fh*0.52, fh*0.30, droop=52, flip=sx)
            eb = (-hw*2.0, top, hw*2.0, bot + fh*0.60)
            g.append(cel(d_ear, eb, skin_sh, shade(skin_sh, 0.88), sw=5.0, uid="er%d" % sx))

        # الجمجمة + الخطم
        dsk = head_silhouette(hw, top, bot)
        bbox = (-hw*1.7, top-fh*0.10, hw*1.7, bot+fh*0.15)
        det = [detail_stroke(
            cr_open([(-hw*0.30, bot-fh*0.10), (0, bot-fh*0.02), (hw*0.30, bot-fh*0.10)], 0.9),
            shade(skin_sh, 0.9), 3.0, 0.7)]
        g.append(cel(dsk, bbox, skin, skin_sh, sw=6.0, details=det, uid="sk"))

        # غطاء الصوف
        wy = top + fh*0.06
        dwool = blob(0, wy, hw*1.16, fh*0.34, n=22, lobes=6, amp=0.10, phase=1.1)
        g.append(cel(dwool, (-hw*1.45, wy-fh*0.50, hw*1.45, wy+fh*0.50),
                     wool, wool_sh, sw=5.5, uid="hw"))

        if spec.get("forelock"):
            dt = cr_closed([(-hw*0.30, top-fh*0.02), (-hw*0.10, top-fh*0.34),
                            (hw*0.06, top-fh*0.16), (hw*0.24, top-fh*0.30),
                            (hw*0.34, top+fh*0.02)], 0.9)
            g.append(cel(dt, (-hw*0.55, top-fh*0.45, hw*0.55, top+fh*0.12),
                         wool, wool_sh, sw=4.6, uid="fl"))

        if spec.get("clip"):
            acc = p["accent"]
            g.append('<polygon points="' + format(-hw*0.92, '.1f') + ',' + format(top+fh*0.10, '.1f') +
                     ' ' + format(-hw*0.62, '.1f') + ',' + format(top-fh*0.10, '.1f') +
                     ' ' + format(-hw*0.50, '.1f') + ',' + format(top+fh*0.14, '.1f') +
                     ' ' + format(-hw*0.80, '.1f') + ',' + format(top+fh*0.26, '.1f') +
                     '" fill="' + acc + '" stroke="' + OL + '" stroke-width="4" stroke-linejoin="round"/>')

        # الأنف
        ny = top + fh*0.70
        dn = cr_closed([(-hw*0.16, ny-fh*0.05), (0, ny-fh*0.10), (hw*0.16, ny-fh*0.05),
                        (hw*0.10, ny+fh*0.06), (-hw*0.10, ny+fh*0.06)], 0.9)
        g.append('<path d="' + dn + '" fill="' + p["nose"] + '" stroke="' + OL +
                 '" stroke-width="3.4"/>')

        # اللحية
        if spec.get("beard"):
            by = bot - fh*0.02
            dbeard = blob(0, by+fh*0.16, hw*0.62, fh*0.30, n=18, lobes=5, amp=0.13, phase=0.4)
            g.append(cel(dbeard, (-hw*0.85, by-fh*0.08, hw*0.85, by+fh*0.60),
                         p["beard"], p["beard_sh"], sw=5.0, uid="bd"))

        # القبعة
        if spec.get("cap"):
            cap = p["cap"]
            brass = p["brass"]
            cy0 = top - fh*0.02
            dcap = cr_closed([(-hw*0.98, cy0), (0, cy0-fh*0.42), (hw*0.98, cy0)], 0.85)
            g.append('<path d="' + dcap + '" fill="' + cap + '" stroke="' + OL +
                     '" stroke-width="5" stroke-linejoin="round"/>')
            dbrim = cr_closed([(-hw*1.06, cy0+fh*0.02), (0, cy0-fh*0.06), (hw*1.06, cy0+fh*0.02),
                               (hw*0.98, cy0+fh*0.14), (0, cy0+fh*0.08), (-hw*0.98, cy0+fh*0.14)], 0.9)
            g.append('<path d="' + dbrim + '" fill="' + shade(cap, 0.78) + '" stroke="' + OL +
                     '" stroke-width="4.6" stroke-linejoin="round"/>')
            g.append('<path d="M ' + format(-hw*0.90, '.1f') + ' ' + format(cy0-fh*0.03, '.1f') +
                     ' Q 0 ' + format(cy0-fh*0.14, '.1f') + ' ' + format(hw*0.90, '.1f') + ' ' +
                     format(cy0-fh*0.03, '.1f') + '" fill="none" stroke="' + brass +
                     '" stroke-width="6" stroke-linecap="round"/>')
            g.append('<circle cx="0" cy="' + format(cy0-fh*0.22, '.1f') + '" r="' +
                     format(fh*0.11, '.1f') + '" fill="' + brass + '" stroke="' + OL +
                     '" stroke-width="3.4"/>')
            g.append('<circle cx="0" cy="' + format(cy0-fh*0.22, '.1f') + '" r="' +
                     format(fh*0.045, '.1f') + '" fill="' + cap + '"/>')

        # النظارة
        if spec.get("glasses"):
            brass = p["brass"]
            ey = top + fh*0.52
            for sx in (-1, 1):
                g.append('<circle cx="' + format(sx*hw*0.40, '.1f') + '" cy="' + format(ey, '.1f') +
                         '" r="' + format(hw*0.27, '.1f') + '" fill="none" stroke="' + brass +
                         '" stroke-width="4.4"/>')
            g.append('<path d="M ' + format(-hw*0.13, '.1f') + ' ' + format(ey, '.1f') +
                     ' L ' + format(hw*0.13, '.1f') + ' ' + format(ey, '.1f') +
                     '" stroke="' + brass + '" stroke-width="4.4"/>')

        return "".join(g), bbox

    parts["head"] = {"draw": head, "pivot": (0.0, S["neck"][1])}

    # ---------------- العينان ----------------
    def eyes(state="open"):
        hw = S["head_hw"]
        top = S["face_top"]
        bot = S["face_bot"]
        fh = bot - top
        ey = top + fh*0.50
        iris = C["iris"]
        g = []
        for sx in (-1, 1):
            ex = sx*hw*0.40
            rx = hw*0.235
            ry = fh*0.135
            if state == "blink":
                g.append('<path d="M ' + format(ex-rx, '.1f') + ' ' + format(ey, '.1f') +
                         ' Q ' + format(ex, '.1f') + ' ' + format(ey+ry*0.85, '.1f') +
                         ' ' + format(ex+rx, '.1f') + ' ' + format(ey, '.1f') +
                         '" fill="none" stroke="' + OL + '" stroke-width="5" stroke-linecap="round"/>')
            else:
                g.append('<ellipse cx="' + format(ex, '.1f') + '" cy="' + format(ey, '.1f') +
                         '" rx="' + format(rx, '.1f') + '" ry="' + format(ry, '.1f') +
                         '" fill="#FFFFFF" stroke="' + OL + '" stroke-width="4.2"/>')
                g.append('<ellipse cx="' + format(ex, '.1f') + '" cy="' + format(ey, '.1f') +
                         '" rx="' + format(rx*0.60, '.1f') + '" ry="' + format(ry*0.72, '.1f') +
                         '" fill="' + iris + '"/>')
                g.append('<ellipse cx="' + format(ex, '.1f') + '" cy="' + format(ey, '.1f') +
                         '" rx="' + format(rx*0.32, '.1f') + '" ry="' + format(ry*0.40, '.1f') +
                         '" fill="#141013"/>')
                g.append('<ellipse cx="' + format(ex-rx*0.34, '.1f') + '" cy="' +
                         format(ey-ry*0.40, '.1f') + '" rx="' + format(rx*0.24, '.1f') +
                         '" ry="' + format(ry*0.20, '.1f') + '" fill="#FFFFFF"/>')
                g.append('<ellipse cx="' + format(ex+rx*0.40, '.1f') + '" cy="' +
                         format(ey+ry*0.46, '.1f') + '" rx="' + format(rx*0.13, '.1f') +
                         '" ry="' + format(ry*0.10, '.1f') + '" fill="#FFFFFF" opacity="0.75"/>')
        return "".join(g), (-hw*1.3, top, hw*1.3, bot)

    # ---------------- الحاجبان ----------------
    def brows():
        hw = S["head_hw"]
        top = S["face_top"]
        bot = S["face_bot"]
        fh = bot - top
        by = top + fh*0.335
        w = fh*0.075 if spec.get("thick_brows") else fh*0.045
        col = C["wool"] if spec.get("thick_brows") else "#3D291A"
        g = []
        for sx in (-1, 1):
            g.append('<path d="M ' + format(sx*hw*0.16, '.1f') + ' ' + format(by+fh*0.03, '.1f') +
                     ' Q ' + format(sx*hw*0.40, '.1f') + ' ' + format(by-fh*0.05, '.1f') +
                     ' ' + format(sx*hw*0.66, '.1f') + ' ' + format(by+fh*0.02, '.1f') +
                     '" fill="none" stroke="' + col + '" stroke-width="' + format(w, '.1f') +
                     '" stroke-linecap="round"/>')
        return "".join(g), (-hw*1.1, top, hw*1.1, bot)

    # ---------------- الفم ----------------
    def mouth(variant="closed"):
        hw = S["head_hw"]
        top = S["face_top"]
        bot = S["face_bot"]
        fh = bot - top
        my = top + fh*0.845
        g = []
        if variant == "closed":
            g.append('<path d="M ' + format(-hw*0.20, '.1f') + ' ' + format(my, '.1f') +
                     ' Q 0 ' + format(my+fh*0.055, '.1f') + ' ' + format(hw*0.20, '.1f') + ' ' +
                     format(my, '.1f') + '" fill="none" stroke="' + OL +
                     '" stroke-width="4.4" stroke-linecap="round"/>')
        elif variant == "A":
            dm = cr_closed([(-hw*0.24, my-fh*0.01), (-hw*0.16, my+fh*0.12), (0, my+fh*0.16),
                            (hw*0.16, my+fh*0.12), (hw*0.24, my-fh*0.01), (0, my-fh*0.03)], 0.9)
            g.append('<path d="' + dm + '" fill="#5B1E1E" stroke="' + OL +
                     '" stroke-width="4" stroke-linejoin="round"/>')
            g.append('<path d="M ' + format(-hw*0.11, '.1f') + ' ' + format(my+fh*0.10, '.1f') +
                     ' Q 0 ' + format(my+fh*0.035, '.1f') + ' ' + format(hw*0.11, '.1f') + ' ' +
                     format(my+fh*0.10, '.1f') + '" fill="none" stroke="#E88A8A" '
                     'stroke-width="4" stroke-linecap="round"/>')
        elif variant == "O":
            g.append('<ellipse cx="0" cy="' + format(my+fh*0.045, '.1f') + '" rx="' +
                     format(hw*0.145, '.1f') + '" ry="' + format(fh*0.070, '.1f') +
                     '" fill="#4A1717" stroke="' + OL + '" stroke-width="4"/>')
        elif variant == "E":
            dm = cr_closed([(-hw*0.26, my-fh*0.005), (-hw*0.27, my+fh*0.075),
                            (hw*0.27, my+fh*0.075), (hw*0.26, my-fh*0.005)], 0.85)
            g.append('<path d="' + dm + '" fill="#5B1E1E" stroke="' + OL +
                     '" stroke-width="4" stroke-linejoin="round"/>')
            g.append('<path d="M ' + format(-hw*0.19, '.1f') + ' ' + format(my+fh*0.036, '.1f') +
                     ' L ' + format(hw*0.19, '.1f') + ' ' + format(my+fh*0.036, '.1f') +
                     '" stroke="#FFFFFF" stroke-width="' + format(fh*0.030, '.1f') +
                     '" stroke-linecap="round"/>')
        elif variant == "frown":
            g.append('<path d="M ' + format(-hw*0.20, '.1f') + ' ' + format(my+fh*0.05, '.1f') +
                     ' Q 0 ' + format(my-fh*0.03, '.1f') + ' ' + format(hw*0.20, '.1f') + ' ' +
                     format(my+fh*0.05, '.1f') + '" fill="none" stroke="' + OL +
                     '" stroke-width="4.4" stroke-linecap="round"/>')
        return "".join(g), (-hw*1.1, top, hw*1.1, bot)

    # ---------------- الأطراف ----------------
    def limb(kind, side, back=False):
        p = palette(C, back)
        wool = p["wool"]; wool_sh = p["wool_sh"]
        skin = p["skin"]; skin_sh = p["skin_sh"]
        hoof = p.get("hoof", "#593A28")
        sgn = 1 if side == "front" else -1
        sw_x = S["shoulder"][0]
        sy = S["shoulder"][1]
        ex = S["elbow"][0]
        ey = S["elbow"][1]
        wx = S["wrist"][0]
        wy = S["wrist"][1]
        hx = S["hip"][0]
        hy = S["hip"][1]
        kx = sgn*hx*1.05
        ky = S["knee"]
        ax = sgn*hx*1.10
        ay = S["ankle"]

        if kind == "upperarm":
            x0 = sgn*sw_x*0.86; y0 = sy
            x1 = sgn*ex*0.92;  y1 = ey
            d = capsule(x0, y0, x1, y1, H*0.070, H*0.058, bow=H*0.012, bow_dir=sgn)
            bbox = (min(x0, x1)-H*0.08, min(y0, y1)-H*0.06, max(x0, x1)+H*0.08, max(y0, y1)+H*0.06)
            return cel(d, bbox, wool, wool_sh, sw=5.4, uid="ua"+side+str(back)), bbox

        if kind == "forearm":
            x0 = sgn*ex*0.92; y0 = ey
            x1 = sgn*wx*0.94; y1 = wy - H*0.018
            d = capsule(x0, y0, x1, y1, H*0.056, H*0.046, bow=H*0.010, bow_dir=sgn)
            bbox = (min(x0, x1)-H*0.09, min(y0, y1)-H*0.07, max(x0, x1)+H*0.09, max(y0, y1)+H*0.09)
            body = cel(d, bbox, skin, skin_sh, sw=5.0, uid="fa"+side+str(back))
            hxx = x1; hyy = y1 + H*0.022
            dh = blob(hxx, hyy, H*0.042, H*0.034, n=14, lobes=3, amp=0.07)
            body += cel(dh, (hxx-H*0.08, hyy-H*0.07, hxx+H*0.08, hyy+H*0.07),
                        skin, skin_sh, sw=4.6, uid="hd"+side+str(back))
            body += detail_stroke(cr_open([(hxx-H*0.022, hyy+H*0.022),
                                           (hxx+H*0.022, hyy+H*0.022)], 0.9),
                                  shade(skin_sh, 0.85), 3.0, 0.8)
            return body, bbox

        if kind == "thigh":
            x0 = sgn*hx*0.92; y0 = hy
            x1 = kx; y1 = ky
            d = capsule(x0, y0, x1, y1, H*0.098, H*0.070, bow=H*0.010, bow_dir=sgn)
            bbox = (min(x0, x1)-H*0.09, min(y0, y1)-H*0.07, max(x0, x1)+H*0.09, max(y0, y1)+H*0.06)
            return cel(d, bbox, wool, wool_sh, sw=5.6, uid="th"+side+str(back)), bbox

        # shin
        x0 = kx; y0 = ky
        x1 = ax; y1 = ay
        d = capsule(x0, y0, x1, y1, H*0.062, H*0.044, bow=H*0.008, bow_dir=-sgn)
        bbox = (min(x0, x1)-H*0.08, min(y0, y1)-H*0.06, max(x0, x1)+H*0.08, max(y0, y1)+H*0.10)
        body = cel(d, bbox, skin, skin_sh, sw=5.0, uid="sn"+side+str(back))
        fx = x1 + sgn*H*0.012
        fy = ay + H*0.026
        df = cr_closed([(fx-H*0.055, fy-H*0.010), (fx-H*0.050, fy+H*0.030),
                        (fx+H*0.030, fy+H*0.036), (fx+H*0.062, fy+H*0.028),
                        (fx+H*0.058, fy-H*0.018), (fx+H*0.010, fy-H*0.030)], 0.85)
        body += cel(df, (fx-H*0.10, fy-H*0.08, fx+H*0.11, fy+H*0.08),
                    hoof, shade(hoof, 0.78), sw=4.8, uid="ft"+side+str(back))
        return body, bbox

    piv = {
        ("upperarm", "front"): (S["shoulder"][0]*0.86, S["shoulder"][1]),
        ("upperarm", "back"):  (-S["shoulder"][0]*0.86, S["shoulder"][1]),
        ("forearm",  "front"): (S["elbow"][0]*0.92, S["elbow"][1]),
        ("forearm",  "back"):  (-S["elbow"][0]*0.92, S["elbow"][1]),
        ("thigh",    "front"): (S["hip"][0]*0.92, S["hip"][1]),
        ("thigh",    "back"):  (-S["hip"][0]*0.92, S["hip"][1]),
        ("shin",     "front"): (S["hip"][0]*1.05, S["knee"]),
        ("shin",     "back"):  (-S["hip"][0]*1.05, S["knee"]),
    }
    for kind in ("upperarm", "forearm", "thigh", "shin"):
        for side in ("front", "back"):
            back = (side == "back")
            parts[kind + "_" + side] = {
                "draw": (lambda back=back, k=kind, s=side: limb(k, s, back)),
                "pivot": piv[(kind, side)],
            }

    face = {"eyes": eyes, "brows": brows, "mouth": mouth}
    return S, parts, face


# ===========================================================================
# 5) شخصية الكلب (سمسم)
# ===========================================================================
def build_dog(spec):
    S = skeleton(spec["H"], spec["n_heads"], body_hw=0.130, shoulder_hw=0.100,
                 hip_hw=0.072, head_hw=0.138)
    C = spec["colors"]
    H = S["H"]
    hh = S["hh"]
    parts = {}

    def torso(back=False):
        p = palette(C, back)
        fur = p["fur"]; fur_sh = p["fur_sh"]
        cream = p["cream"]; collar = p["collar"]; brass = p["brass"]
        top = S["shoulder"][1] - hh*0.10
        bot = S["hip"][1] + hh*0.08
        hw = S["body_hw"]
        ry = (bot-top)/2
        d = cr_closed([(0, top-ry*0.06), (hw*0.82, top+ry*0.16), (hw*0.94, top+ry*0.62),
                       (hw*0.80, bot-ry*0.18), (hw*0.46, bot), (0, bot+ry*0.10),
                       (-hw*0.46, bot), (-hw*0.80, bot-ry*0.18), (-hw*0.94, top+ry*0.62),
                       (-hw*0.82, top+ry*0.16)], 0.9)
        bbox = (-hw*1.30, top-ry*0.40, hw*1.30, bot+ry*0.40)
        dch = cr_closed([(0, top+ry*0.20), (hw*0.42, top+ry*0.70), (hw*0.30, bot-ry*0.10),
                         (0, bot-ry*0.02), (-hw*0.30, bot-ry*0.10), (-hw*0.42, top+ry*0.70)], 0.9)
        det = ['<path d="' + dch + '" fill="' + cream + '" opacity="0.95"/>']
        body = cel(d, bbox, fur, fur_sh, sw=6.0, details=det, uid="dt")
        ny = top + ry*0.10
        dcol = cr_closed([(-hw*0.80, ny-ry*0.06), (0, ny-ry*0.02), (hw*0.80, ny-ry*0.06),
                          (hw*0.78, ny+ry*0.14), (0, ny+ry*0.20), (-hw*0.78, ny+ry*0.14)], 0.9)
        body += '<path d="' + dcol + '" fill="' + collar + '" stroke="' + OL + \
                '" stroke-width="4.4" stroke-linejoin="round"/>'
        body += '<circle cx="0" cy="' + format(ny+ry*0.48, '.1f') + '" r="' + \
                format(ry*0.20, '.1f') + '" fill="' + brass + '" stroke="' + OL + \
                '" stroke-width="3.6"/>'
        body += '<circle cx="0" cy="' + format(ny+ry*0.48, '.1f') + '" r="' + \
                format(ry*0.13, '.1f') + '" fill="#FFFDF7"/>'
        body += '<path d="M 0 ' + format(ny+ry*0.48, '.1f') + ' L ' + format(ry*0.07, '.1f') + \
                ' ' + format(ny+ry*0.38, '.1f') + '" stroke="#D94B43" stroke-width="3.2" ' \
                'stroke-linecap="round"/>'
        return body, bbox
    parts["torso"] = {"draw": torso, "pivot": (0.0, S["hip"][1])}

    def head(back=False):
        p = palette(C, back)
        fur = p["fur"]; fur_sh = p["fur_sh"]
        patch = p["patch"]; cream = p["cream"]
        hw = S["head_hw"]
        top = S["face_top"]
        bot = S["face_bot"]
        fh = bot - top
        dsk = cr_closed([(0, top), (hw*0.62, top+fh*0.06), (hw*1.00, top+fh*0.28),
                         (hw*0.98, top+fh*0.50), (hw*0.74, top+fh*0.70), (hw*0.50, top+fh*0.86),
                         (hw*0.24, top+fh*0.96), (0, top+fh*1.00),
                         (-hw*0.24, top+fh*0.96), (-hw*0.50, top+fh*0.86), (-hw*0.74, top+fh*0.70),
                         (-hw*0.98, top+fh*0.50), (-hw*1.00, top+fh*0.28), (-hw*0.62, top+fh*0.06)], 0.9)
        bbox = (-hw*1.75, top-fh*0.10, hw*1.75, bot+fh*0.15)
        dp = cr_closed([(hw*0.10, top+fh*0.06), (hw*0.72, top+fh*0.10), (hw*0.86, top+fh*0.40),
                        (hw*0.40, top+fh*0.56), (hw*0.02, top+fh*0.42)], 0.9)
        g = [cel(dsk, bbox, fur, fur_sh, sw=6.0,
                 details=['<path d="' + dp + '" fill="' + patch + '"/>'], uid="ds")]
        my = top + fh*0.80
        dmuz = cr_closed([(-hw*0.42, my-fh*0.06), (-hw*0.30, my+fh*0.10), (0, my+fh*0.15),
                          (hw*0.30, my+fh*0.10), (hw*0.42, my-fh*0.06), (hw*0.30, my-fh*0.16),
                          (0, my-fh*0.19), (-hw*0.30, my-fh*0.16)], 0.9)
        g.append(cel(dmuz, (-hw*0.65, my-fh*0.35, hw*0.65, my+fh*0.35),
                     cream, shade(cream, 0.88), sw=4.8, uid="dm"))
        dn = cr_closed([(-hw*0.13, my-fh*0.10), (0, my-fh*0.15), (hw*0.13, my-fh*0.10),
                        (hw*0.08, my-fh*0.01), (-hw*0.08, my-fh*0.01)], 0.9)
        g.append('<path d="' + dn + '" fill="#241A16" stroke="' + OL + '" stroke-width="3.2"/>')
        return "".join(g), bbox
    parts["head"] = {"draw": head, "pivot": (0.0, S["neck"][1])}

    def eyes(state="open"):
        hw = S["head_hw"]
        top = S["face_top"]
        bot = S["face_bot"]
        fh = bot - top
        ey = top + fh*0.44
        iris = C["iris"]
        g = []
        for sx in (-1, 1):
            ex = sx*hw*0.42
            rx = hw*0.20
            ry = fh*0.115
            if state == "blink":
                g.append('<path d="M ' + format(ex-rx, '.1f') + ' ' + format(ey, '.1f') +
                         ' Q ' + format(ex, '.1f') + ' ' + format(ey+ry*0.8, '.1f') + ' ' +
                         format(ex+rx, '.1f') + ' ' + format(ey, '.1f') +
                         '" fill="none" stroke="' + OL + '" stroke-width="4.6" stroke-linecap="round"/>')
            else:
                g.append('<ellipse cx="' + format(ex, '.1f') + '" cy="' + format(ey, '.1f') +
                         '" rx="' + format(rx, '.1f') + '" ry="' + format(ry, '.1f') +
                         '" fill="#FFFFFF" stroke="' + OL + '" stroke-width="4"/>')
                g.append('<ellipse cx="' + format(ex, '.1f') + '" cy="' + format(ey, '.1f') +
                         '" rx="' + format(rx*0.62, '.1f') + '" ry="' + format(ry*0.74, '.1f') +
                         '" fill="' + iris + '"/>')
                g.append('<ellipse cx="' + format(ex, '.1f') + '" cy="' + format(ey, '.1f') +
                         '" rx="' + format(rx*0.33, '.1f') + '" ry="' + format(ry*0.42, '.1f') +
                         '" fill="#141013"/>')
                g.append('<ellipse cx="' + format(ex-rx*0.34, '.1f') + '" cy="' +
                         format(ey-ry*0.42, '.1f') + '" rx="' + format(rx*0.26, '.1f') +
                         '" ry="' + format(ry*0.22, '.1f') + '" fill="#FFFFFF"/>')
        return "".join(g), (-hw*1.3, top, hw*1.3, bot)

    def brows():
        hw = S["head_hw"]
        top = S["face_top"]
        bot = S["face_bot"]
        fh = bot - top
        by = top + fh*0.27
        col = shade(C["patch"], 0.85)
        g = []
        for sx in (-1, 1):
            g.append('<path d="M ' + format(sx*hw*0.20, '.1f') + ' ' + format(by+fh*0.03, '.1f') +
                     ' Q ' + format(sx*hw*0.44, '.1f') + ' ' + format(by-fh*0.04, '.1f') + ' ' +
                     format(sx*hw*0.68, '.1f') + ' ' + format(by+fh*0.02, '.1f') +
                     '" fill="none" stroke="' + col + '" stroke-width="' + format(fh*0.045, '.1f') +
                     '" stroke-linecap="round"/>')
        return "".join(g), (-hw*1.1, top, hw*1.1, bot)

    def mouth(variant="closed"):
        hw = S["head_hw"]
        top = S["face_top"]
        bot = S["face_bot"]
        fh = bot - top
        my = top + fh*0.90
        g = []
        if variant == "closed":
            g.append('<path d="M ' + format(-hw*0.18, '.1f') + ' ' + format(my, '.1f') +
                     ' Q 0 ' + format(my+fh*0.06, '.1f') + ' ' + format(hw*0.18, '.1f') + ' ' +
                     format(my, '.1f') + '" fill="none" stroke="' + OL +
                     '" stroke-width="4.2" stroke-linecap="round"/>')
        elif variant == "A":
            dm = cr_closed([(-hw*0.22, my), (-hw*0.14, my+fh*0.14), (0, my+fh*0.175),
                            (hw*0.14, my+fh*0.14), (hw*0.22, my), (0, my-fh*0.02)], 0.9)
            g.append('<path d="' + dm + '" fill="#5B1E1E" stroke="' + OL +
                     '" stroke-width="4" stroke-linejoin="round"/>')
            g.append('<path d="M ' + format(-hw*0.06, '.1f') + ' ' + format(my+fh*0.135, '.1f') +
                     ' L ' + format(hw*0.06, '.1f') + ' ' + format(my+fh*0.135, '.1f') +
                     '" stroke="#FFFFFF" stroke-width="' + format(fh*0.035, '.1f') +
                     '" stroke-linecap="round"/>')
        elif variant == "O":
            g.append('<ellipse cx="0" cy="' + format(my+fh*0.05, '.1f') + '" rx="' +
                     format(hw*0.13, '.1f') + '" ry="' + format(fh*0.072, '.1f') +
                     '" fill="#4A1717" stroke="' + OL + '" stroke-width="4"/>')
        elif variant == "E":
            dm = cr_closed([(-hw*0.24, my), (-hw*0.25, my+fh*0.085),
                            (hw*0.25, my+fh*0.085), (hw*0.24, my)], 0.85)
            g.append('<path d="' + dm + '" fill="#5B1E1E" stroke="' + OL +
                     '" stroke-width="4" stroke-linejoin="round"/>')
            g.append('<path d="M ' + format(-hw*0.16, '.1f') + ' ' + format(my+fh*0.043, '.1f') +
                     ' L ' + format(hw*0.16, '.1f') + ' ' + format(my+fh*0.043, '.1f') +
                     '" stroke="#FFFFFF" stroke-width="' + format(fh*0.030, '.1f') +
                     '" stroke-linecap="round"/>')
        elif variant == "frown":
            g.append('<path d="M ' + format(-hw*0.18, '.1f') + ' ' + format(my+fh*0.05, '.1f') +
                     ' Q 0 ' + format(my-fh*0.03, '.1f') + ' ' + format(hw*0.18, '.1f') + ' ' +
                     format(my+fh*0.05, '.1f') + '" fill="none" stroke="' + OL +
                     '" stroke-width="4.2" stroke-linecap="round"/>')
        return "".join(g), (-hw*1.1, top, hw*1.1, bot)

    def ear(side, back=False):
        p = palette(C, back)
        patch = p["patch"]
        hw = S["head_hw"]
        top = S["face_top"]
        fh = S["face_bot"] - top
        sgn = 1 if side == "front" else -1
        x0 = sgn*hw*0.80
        y0 = top + fh*0.30
        spine = [(x0, y0)]
        for i in range(1, 10):
            t = i/9.0
            spine.append((x0 + sgn*hw*0.16*math.sin(math.pi*t*0.8), y0 + fh*0.72*t))
        widths = [fh*0.30*(1.0-0.45*(i/9.0)) for i in range(10)]
        d = tapered(spine, widths)
        bbox = (min(q[0] for q in spine)-fh*0.30, y0-fh*0.18,
                max(q[0] for q in spine)+fh*0.30, y0+fh*0.90)
        return cel(d, bbox, patch, shade(patch, 0.78), sw=5.2, uid="de"+side+str(back)), bbox

    def tail(back=False):
        p = palette(C, back)
        fur = p["fur"]; fur_sh = p["fur_sh"]
        hw = S["body_hw"]
        y0 = S["hip"][1] - hh*0.10
        x0 = -hw*0.80
        spine = [(x0, y0)]
        for i in range(1, 12):
            t = i/11.0
            spine.append((x0 - hw*1.05*t, y0 - hh*0.55*math.sin(math.pi*t*0.85)))
        widths = [hw*0.34*(1.0-0.55*(i/11.0)) for i in range(12)]
        d = tapered(spine, widths)
        bbox = (x0-hw*1.60, y0-hh*0.85, x0+hw*0.55, y0+hw*0.55)
        return cel(d, bbox, fur, fur_sh, sw=5.4, uid="dt"+str(back)), bbox

    def limb(kind, side, back=False):
        p = palette(C, back)
        fur = p["fur"]; fur_sh = p["fur_sh"]
        cream = p["cream"]
        sgn = 1 if side == "front" else -1
        sw_x = S["shoulder"][0]; sy = S["shoulder"][1]
        ex = S["elbow"][0]; ey = S["elbow"][1]
        wx = S["wrist"][0]; wy = S["wrist"][1]
        hx = S["hip"][0]; hy = S["hip"][1]
        kx = sgn*hx*1.02; ky = S["knee"]
        ax = sgn*hx*1.06; ay = S["ankle"]

        if kind == "upperarm":
            x0 = sgn*sw_x*0.84; y0 = sy
            x1 = sgn*ex*0.90;  y1 = ey
            d = capsule(x0, y0, x1, y1, H*0.062, H*0.050, bow=H*0.010, bow_dir=sgn)
            bbox = (min(x0, x1)-H*0.08, min(y0, y1)-H*0.06, max(x0, x1)+H*0.08, max(y0, y1)+H*0.06)
            return cel(d, bbox, fur, fur_sh, sw=5.2, uid="du"+side+str(back)), bbox

        if kind == "forearm":
            x0 = sgn*ex*0.90; y0 = ey
            x1 = sgn*wx*0.92; y1 = wy - H*0.016
            d = capsule(x0, y0, x1, y1, H*0.050, H*0.042, bow=H*0.008, bow_dir=sgn)
            bbox = (min(x0, x1)-H*0.09, min(y0, y1)-H*0.07, max(x0, x1)+H*0.09, max(y0, y1)+H*0.10)
            body = cel(d, bbox, fur, fur_sh, sw=4.8, uid="df"+side+str(back))
            px = x1; py = y1 + H*0.024
            dp = blob(px, py, H*0.046, H*0.032, n=14, lobes=3, amp=0.06)
            body += cel(dp, (px-H*0.09, py-H*0.07, px+H*0.09, py+H*0.07),
                        cream, shade(cream, 0.86), sw=4.4, uid="dp"+side+str(back))
            return body, bbox

        if kind == "thigh":
            x0 = sgn*hx*0.90; y0 = hy
            x1 = kx; y1 = ky
            d = capsule(x0, y0, x1, y1, H*0.088, H*0.060, bow=H*0.008, bow_dir=sgn)
            bbox = (min(x0, x1)-H*0.09, min(y0, y1)-H*0.07, max(x0, x1)+H*0.09, max(y0, y1)+H*0.06)
            return cel(d, bbox, fur, fur_sh, sw=5.4, uid="dh"+side+str(back)), bbox

        x0 = kx; y0 = ky
        x1 = ax; y1 = ay
        d = capsule(x0, y0, x1, y1, H*0.054, H*0.040, bow=H*0.008, bow_dir=-sgn)
        bbox = (min(x0, x1)-H*0.08, min(y0, y1)-H*0.06, max(x0, x1)+H*0.08, max(y0, y1)+H*0.10)
        body = cel(d, bbox, fur, fur_sh, sw=4.8, uid="ds"+side+str(back))
        fx = x1 + sgn*H*0.014
        fy = ay + H*0.024
        df = blob(fx, fy, H*0.058, H*0.030, n=14, lobes=3, amp=0.06)
        body += cel(df, (fx-H*0.10, fy-H*0.07, fx+H*0.10, fy+H*0.07),
                    cream, shade(cream, 0.86), sw=4.4, uid="dft"+side+str(back))
        return body, bbox

    piv = {
        ("upperarm", "front"): (S["shoulder"][0]*0.84, S["shoulder"][1]),
        ("upperarm", "back"):  (-S["shoulder"][0]*0.84, S["shoulder"][1]),
        ("forearm",  "front"): (S["elbow"][0]*0.90, S["elbow"][1]),
        ("forearm",  "back"):  (-S["elbow"][0]*0.90, S["elbow"][1]),
        ("thigh",    "front"): (S["hip"][0]*0.90, S["hip"][1]),
        ("thigh",    "back"):  (-S["hip"][0]*0.90, S["hip"][1]),
        ("shin",     "front"): (S["hip"][0]*1.02, S["knee"]),
        ("shin",     "back"):  (-S["hip"][0]*1.02, S["knee"]),
    }
    for kind in ("upperarm", "forearm", "thigh", "shin"):
        for side in ("front", "back"):
            back = (side == "back")
            parts[kind + "_" + side] = {
                "draw": (lambda back=back, k=kind, s=side: limb(k, s, back)),
                "pivot": piv[(kind, side)],
            }

    def ear_pivot(side):
        sgn = 1 if side == "front" else -1
        return (sgn*S["head_hw"]*0.80, S["face_top"] + (S["face_bot"]-S["face_top"])*0.30)

    def tail_pivot():
        return (-S["body_hw"]*0.80, S["hip"][1] - hh*0.10)

    face = {"eyes": eyes, "brows": brows, "mouth": mouth, "ear": ear, "tail": tail,
            "ear_pivot": ear_pivot, "tail_pivot": tail_pivot}
    return S, parts, face
