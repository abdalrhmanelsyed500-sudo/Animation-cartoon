# -*- coding: utf-8 -*-
"""
==============================================================================
  عالم المسلسل — قاطرة الطريق الهجينة + خلفيات 2.5D (إعادة رسم كاملة)
==============================================================================
نفس نظام الرسم المتجهي عالي الجودة المستخدم للشخصيات.
النوافذ ثقوب حقيقية في مسار الهيكل (fill-rule="evenodd") => الشخصيات تظهر من داخلها.
==============================================================================
"""
import math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from art_lib import (cr_closed, cr_open, blob, capsule, tapered, ellipse_d,
                     cel, detail_stroke, render_svg, bbox_of, OUTLINE)

OL = OUTLINE
OUT = "/home/user/Animation-cartoon/تجربة/studio_rigs2/world"
os.makedirs(OUT, exist_ok=True)

WOOD   = "#A86B36"; WOOD_SH = "#7E4D24"
STEEL  = "#2B5B6C"; STEEL_SH = "#1B3E4C"
BRASS  = "#D49B42"; BRASS_SH = "#A8762A"
TIRE   = "#3A3F45"; RIM      = "#8C969E"
GLASS  = "#BFE6F5"


# ===========================================================================
# 1) القاطرة
# ===========================================================================
def loco_chassis():
    """الهيكل الخشبي — النوافذ ثقوب حقيقية"""
    g = []
    # الشرفة الخلفية وصندوق العدة
    d_deck = cr_closed([(70, 300), (660, 300), (660, 336), (70, 336)], 0.8)
    g.append(cel(d_deck, (60, 290, 670, 350), WOOD_SH, "#5E381A", sw=5.0, uid="deck"))

    d_box = cr_closed([(92, 232), (186, 232), (190, 296), (88, 296)], 0.85)
    g.append(cel(d_box, (80, 222, 200, 308), "#C4362F", "#8E231E", sw=5.0, uid="box"))
    g.append('<rect x="120" y="252" width="34" height="24" rx="5" fill="' + BRASS +
             '" stroke="' + OL + '" stroke-width="4"/>')

    # الجسم الخارجي مع النوافذ (ثقوب)
    outer = [(175, 108), (520, 108), (520, 300), (175, 300)]
    w1 = [(206, 140), (296, 140), (296, 224), (206, 224)]
    w2 = [(316, 140), (404, 140), (404, 224), (316, 224)]
    w3 = [(424, 140), (498, 140), (498, 224), (424, 224)]
    d = 'M ' + ' L '.join('%g %g' % p for p in outer) + ' Z' + \
        ' M ' + ' L '.join('%g %g' % p for p in w1) + ' Z' + \
        ' M ' + ' L '.join('%g %g' % p for p in w2) + ' Z' + \
        ' M ' + ' L '.join('%g %g' % p for p in w3) + ' Z'
    d_body = d.replace('L', 'L')  # مسار مضلّع حاد (نوافذ مستطيلة)
    bbox = (160, 95, 535, 315)
    # تعبئة خشبية بتظليل خلوي
    g.append('<defs><clipPath id="cb"><path d="' + d_body +
             '" clip-rule="evenodd" fill-rule="evenodd"/></clipPath></defs>')
    g.append('<path d="' + d_body + '" fill-rule="evenodd" fill="' + WOOD + '"/>')
    g.append('<g clip-path="url(#cb)">')
    g.append('<path d="' + ellipse_d(350, 250, 260, 130) + '" fill="' + WOOD_SH + '"/>')
    for i in range(7):                      # ألواح خشب رأسية
        x = 190 + i*48
        g.append(detail_stroke('M %g 108 L %g 300' % (x, x), "#6E4320", 2.6, 0.55))
    g.append('</g>')
    g.append('<path d="' + d_body + '" fill-rule="evenodd" fill="none" stroke="' + OL +
             '" stroke-width="6" stroke-linejoin="round"/>')
    # لمعة زجاج خفيفة جداً (لا تمنع رؤية الركّاب)
    for (x0, x1) in [(206, 296), (316, 404), (424, 498)]:
        g.append('<rect x="%g" y="140" width="%g" height="84" fill="%s" opacity="0.10"/>'
                 % (x0, x1-x0, GLASS))

    # إطار فولاذي علوي وسفلي + مسامير نحاسية
    g.append('<rect x="175" y="108" width="345" height="20" rx="6" fill="' + STEEL +
             '" stroke="' + OL + '" stroke-width="5"/>')
    g.append('<rect x="70" y="282" width="615" height="22" rx="7" fill="' + STEEL +
             '" stroke="' + OL + '" stroke-width="5"/>')
    for i in range(14):
        x = 92 + i*44
        g.append('<circle cx="%g" cy="293" r="4.2" fill="%s"/>' % (x, BRASS))

    # السقف المنحني
    d_roof = cr_closed([(158, 110), (250, 74), (450, 74), (540, 110)], 0.85)
    g.append(cel(d_roof, (145, 62, 555, 122), STEEL, STEEL_SH, sw=5.5, uid="roof"))

    # مقدمة الغلاية
    d_nose = cr_closed([(520, 158), (668, 158), (700, 224), (668, 290), (520, 290)], 0.85)
    g.append(cel(d_nose, (510, 148, 712, 300), WOOD, WOOD_SH, sw=5.5, uid="nose"))
    g.append('<rect x="596" y="158" width="20" height="132" fill="' + STEEL +
             '" stroke="' + OL + '" stroke-width="4"/>')
    g.append('<rect x="648" y="170" width="20" height="108" fill="' + STEEL +
             '" stroke="' + OL + '" stroke-width="4"/>')
    # المدخنة النحاسية
    g.append('<path d="M 596 84 L 636 84 L 640 160 L 592 160 Z" fill="' + BRASS +
             '" stroke="' + OL + '" stroke-width="5" stroke-linejoin="round"/>')
    g.append('<rect x="586" y="72" width="60" height="16" rx="6" fill="' + BRASS +
             '" stroke="' + OL + '" stroke-width="5"/>')
    # المصابيح
    for (cx, cy) in [(712, 250), (712, 196)]:
        g.append('<circle cx="%g" cy="%g" r="26" fill="%s" stroke="%s" stroke-width="5"/>'
                 % (cx, cy, BRASS, OL))
        g.append('<circle cx="%g" cy="%g" r="17" fill="#FFF6C8" stroke="%s" stroke-width="3.5"/>'
                 % (cx, cy, OL))
    return "".join(g), (60, 60, 760, 360)


def loco_wheel():
    """عجلة مطاطية واحدة — تدور حول مركزها"""
    g = []
    d_tire = cr_closed([(65 + 60*math.cos(2*math.pi*i/28), 65 + 60*math.sin(2*math.pi*i/28))
                        for i in range(28)], 0.9)
    g.append(cel(d_tire, (0, 0, 130, 130), TIRE, "#25292E", sw=6.0, uid="tire"))
    # مداس العجلة
    for i in range(16):
        a = 2*math.pi*i/16
        x0, y0 = 65 + 44*math.cos(a), 65 + 44*math.sin(a)
        x1, y1 = 65 + 58*math.cos(a), 65 + 58*math.sin(a)
        g.append(detail_stroke('M %g %g L %g %g' % (x0, y0, x1, y1), "#5A6169", 3.0, 0.9))
    g.append('<circle cx="65" cy="65" r="36" fill="' + RIM + '" stroke="' + OL +
             '" stroke-width="5"/>')
    for i in range(6):                      # قضبان
        a = 2*math.pi*i/6
        x0, y0 = 65 + 12*math.cos(a), 65 + 12*math.sin(a)
        x1, y1 = 65 + 32*math.cos(a), 65 + 32*math.sin(a)
        g.append(detail_stroke('M %g %g L %g %g' % (x0, y0, x1, y1), OL, 5.0, 1.0))
    g.append('<circle cx="65" cy="65" r="13" fill="' + BRASS + '" stroke="' + OL +
             '" stroke-width="4"/>')
    return "".join(g), (0, 0, 130, 130)


def loco_spring():
    spine = [(30, 8)]
    for i in range(1, 12):
        t = i/11.0
        spine.append((30 + 16*math.sin(math.pi*2*t), 8 + 66*t))
    widths = [11.0]*12
    d = tapered(spine, widths)
    g = cel(d, (5, 0, 58, 84), BRASS, BRASS_SH, sw=4.6, uid="spr")
    return g, (0, 0, 64, 90)


def loco_fan():
    g = []
    ang = math.radians(18)
    for k in range(4):
        a = ang + k*math.pi/2
        ca, sa = math.cos(a), math.sin(a)
        spine = [(65, 65)]
        for i in range(1, 8):
            t = i/7.0
            spine.append((65 + 58*t*ca, 65 + 58*t*sa))
        widths = [12 + 26*math.sin(math.pi*(i/7.0)) for i in range(8)]
        d = tapered(spine, widths)
        g.append(cel(d, (0, 0, 130, 130), BRASS, BRASS_SH, sw=4.2, uid="fb%d" % k))
    g.append('<circle cx="65" cy="65" r="15" fill="' + BRASS_SH + '" stroke="' + OL +
             '" stroke-width="5"/>')
    g.append('<circle cx="65" cy="65" r="6" fill="' + OL + '"/>')
    return "".join(g), (0, 0, 130, 130)


def loco_steam():
    pts = [(150, 96), (120, 92), (104, 74), (76, 80), (58, 58), (34, 60),
           (22, 40), (44, 18), (78, 28), (104, 12), (128, 30), (152, 34),
           (148, 60), (162, 78)]
    d = cr_closed(pts, 0.95)
    g = ('<path d="' + d + '" fill="#FFFFFF" opacity="0.94" stroke="#CFE3EC" '
         'stroke-width="4" stroke-linejoin="round"/>')
    g += ('<path d="' + ellipse_d(80, 44, 34, 18) + '" fill="#FFFFFF" opacity="0.85"/>')
    return g, (10, 5, 170, 106)


# ===========================================================================
# 2) الخلفيات — خمس طبقات Parallax بدقة 1920x1080
# ===========================================================================
BW, BH = 1920, 1080


def bg_sky():
    g = ['<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0%" stop-color="#5FB6E4"/>'
         '<stop offset="55%" stop-color="#A9DEF4"/>'
         '<stop offset="100%" stop-color="#E9F6FB"/></linearGradient></defs>',
         '<rect width="%d" height="%d" fill="url(#sky)"/>' % (BW, BH)]
    clouds = [(280, 220, 1.25), (1180, 170, 1.0), (1620, 300, 0.82), (720, 120, 0.66)]
    for (cx, cy, s) in clouds:
        pts = []
        for i in range(14):
            t = 2*math.pi*i/14
            r = (110 + 26*math.sin(3*t + 1.2)) * s
            pts.append((cx + r*1.85*math.cos(t), cy + r*0.62*math.sin(t)))
        d = cr_closed(pts, 0.95)
        g.append('<path d="' + d + '" fill="#FFFFFF" opacity="0.93"/>')
        g.append('<path d="' + ellipse_d(cx + 30*s, cy + 34*s, 150*s, 24*s) +
                 '" fill="#DCEEF8" opacity="0.55"/>')
    return "".join(g), (0, 0, BW, BH)


def bg_far_hills():
    g = []
    d1 = 'M 0 640 ' + ' '.join('Q %d %d %d %d' % (480+960*i, 360+120*((i % 2)*2-1),
                                                  960+960*i, 560+60*((i % 3)-1))
                               for i in range(2)) + ' L 1920 640 L 1920 1080 L 0 1080 Z'
    g.append('<path d="' + d1 + '" fill="#8CC183" stroke="#4A7350" stroke-width="5"/>')
    d2 = 'M 0 700 Q 420 560 900 690 Q 1400 800 1920 660 L 1920 1080 L 0 1080 Z'
    g.append('<path d="' + d2 + '" fill="#75B36C" stroke="#3D6338" stroke-width="5"/>')
    return "".join(g), (0, 0, BW, BH)


def bg_mid():
    g = []
    def tree(cx, base, h, seed):
        trunk = cr_closed([(cx-22, base), (cx+22, base), (cx+15, base-h*0.52),
                           (cx-15, base-h*0.52)], 0.8)
        out = cel(trunk, (cx-40, base-h*0.6, cx+40, base+10), "#7A4E2C", "#5A371C",
                  sw=5.0, uid="tr%d" % seed)
        for k, (oy, rr, amp) in enumerate([(0.0, 0.52, 0.10), (0.18, 0.40, 0.12), (0.34, 0.27, 0.14)]):
            d = blob(cx + (18 if k % 2 else -18), base - h*0.52 - h*rr*0.55,
                     h*rr*1.15, h*rr*0.72, n=20, lobes=6+k, amp=amp, phase=seed+k)
            out += cel(d, (cx-h*rr*1.5, base-h*(0.52+rr*1.3), cx+h*rr*1.5, base-h*0.30),
                       ["#5FA855", "#6FB85F", "#7CC76A"][k], "#437B3B", sw=5.4,
                       uid="cr%d%d" % (seed, k))
        return out
    for (cx, base, h, sd) in [(220, 900, 520, 1), (520, 930, 400, 2),
                              (1560, 890, 560, 3), (1280, 930, 420, 4)]:
        g.append(tree(cx, base, h, sd))
    # بوابة الحجر القديمة
    g.append('<path d="' + cr_closed([(760, 960), (770, 560), (900, 540), (930, 960)], 0.8) +
             '" fill="#A9A294" stroke="#4A463D" stroke-width="6"/>')
    g.append('<path d="' + cr_closed([(1120, 960), (1110, 545), (990, 528), (960, 960)], 0.8) +
             '" fill="#B4AD9E" stroke="#4A463D" stroke-width="6"/>')
    g.append('<path d="' + cr_closed([(735, 560), (1150, 528), (1150, 590), (735, 620)], 0.8) +
             '" fill="#9E9789" stroke="#4A463D" stroke-width="6"/>')
    for i in range(9):                        # نباتات متسلّقة
        x = 760 + i*44
        g.append('<path d="M %g 590 Q %g %g %g %g" fill="none" stroke="#4E8446" '
                 'stroke-width="7" stroke-linecap="round"/>' % (x, x+18, 660, x+6, 730))
    return "".join(g), (0, 0, BW, BH)


def bg_road():
    g = []
    g.append('<path d="M 0 690 L 1920 690 L 1920 1080 L 0 1080 Z" fill="#63A557" '
             'stroke="#3B6B33" stroke-width="5"/>')
    d_road = ('M 0 760 Q 480 726 960 748 Q 1440 770 1920 742 L 1920 990 '
              'Q 1440 1016 960 998 Q 480 980 0 1008 Z')
    g.append('<path d="' + d_road + '" fill="#E3C08A" stroke="#96743F" stroke-width="6"/>')
    g.append('<path d="' + d_road + '" fill="none" stroke="#C9A269" stroke-width="26" '
             'opacity="0.35"/>')
    for i in range(26):                        # حصى
        x = 60 + (i*137) % 1820
        y = 800 + ((i*53) % 160)
        rx = 16 + (i % 4)*7
        g.append('<ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="#C9A269" '
                 'stroke="#96743F" stroke-width="3"/>' % (x, y, rx, rx*0.42))
    return "".join(g), (0, 0, BW, BH)


def bg_fore():
    g = []
    # عمود اللافتة بتروس نحاسية
    g.append('<path d="' + cr_closed([(1668, 520), (1708, 520), (1712, 1080),
                                      (1664, 1080)], 0.8) +
             '" fill="#8A5A31" stroke="#3A2A1E" stroke-width="6"/>')
    g.append('<circle cx="1688" cy="700" r="46" fill="' + BRASS + '" stroke="' + OL +
             '" stroke-width="6"/>')
    for i in range(10):
        a = 2*math.pi*i/10
        g.append('<rect x="%g" y="%g" width="14" height="14" rx="3" fill="%s" '
                 'transform="rotate(%g %g %g)"/>'
                 % (1688 + 46*math.cos(a) - 7, 700 + 46*math.sin(a) - 7, BRASS_SH,
                    math.degrees(a), 1688 + 46*math.cos(a), 700 + 46*math.sin(a)))
    g.append('<circle cx="1688" cy="700" r="18" fill="' + BRASS_SH + '" stroke="' + OL +
             '" stroke-width="4"/>')
    # سهمان خشبيان
    g.append('<path d="' + cr_closed([(1420, 560), (1660, 560), (1700, 592),
                                      (1660, 624), (1420, 624)], 0.85) +
             '" fill="#B8823F" stroke="#3A2A1E" stroke-width="6"/>')
    g.append('<path d="' + cr_closed([(1950, 646), (1710, 646), (1670, 678),
                                      (1710, 710), (1950, 710)], 0.85) +
             '" fill="#9E6633" stroke="#3A2A1E" stroke-width="6"/>')
    # حشائش المقدمة
    for i in range(9):
        x = 40 + i*230
        pts = [(x-46, 1080), (x-30, 966), (x-8, 1016), (x+12, 940), (x+34, 1006), (x+52, 1080)]
        g.append('<path d="' + cr_closed(pts, 0.85) + '" fill="#3F7A37" stroke="#264E21" '
                 'stroke-width="5"/>')
    return "".join(g), (0, 0, BW, BH)


# ===========================================================================
def export_all():
    items = [
        ("loco_chassis", loco_chassis), ("loco_wheel", loco_wheel),
        ("loco_spring", loco_spring), ("loco_fan", loco_fan),
        ("loco_steam", loco_steam),
    ]
    meta = {}
    for name, fn in items:
        body, bb_hint = fn()
        bb, _ = bbox_of(body, pad=10, probe=(-100, -100, 900, 500), ss=1)
        x0, y0, x1, y1 = bb
        w, h = max(2, x1-x0), max(2, y1-y0)
        img = render_svg(body, x0, y0, w, h, ss=3)
        img.save(os.path.join(OUT, name + ".png"))
        meta[name] = {"size": [w, h], "bbox": [x0, y0, x1, y1]}
        print("  %s.png  %dx%d" % (name, w, h))

    bgs = [("bg_01_sky", bg_sky), ("bg_02_far_hills", bg_far_hills),
           ("bg_03_mid", bg_mid), ("bg_04_road", bg_road), ("bg_05_fore", bg_fore)]
    for name, fn in bgs:
        body, _ = fn()
        img = render_svg(body, 0, 0, BW, BH, ss=1)
        img.save(os.path.join(OUT, name + ".png"))
        meta[name] = {"size": [BW, BH], "bbox": [0, 0, BW, BH]}
        print("  %s.png  %dx%d" % (name, BW, BH))

    with open(os.path.join(OUT, "world_map.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export_all()
