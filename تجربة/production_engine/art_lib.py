# -*- coding: utf-8 -*-
"""
==============================================================================
  مكتبة الرسم المتجهي — رسوم متجهية عالية الجودة بأسلوب Cel-Shaded 2.5D
==============================================================================
الهدف: إنتاج أشكال ناعمة بمنحنيات بيزييه حقيقية (لا دوائر ومستطيلات بدائية)،
مع تظليل خلوي ثلاثي المستويات وخطوط خارجية مدبّبة.
"""
import math
import resvg_py
from io import BytesIO
from PIL import Image

OUTLINE = "#2B211B"


# ---------------------------------------------------------------------------
# 1) هندسة المنحنيات
# ---------------------------------------------------------------------------
def cr_closed(pts, tension=1.0):
    """Catmull-Rom مغلق → مسار بيزييه تكعيبي ناعم"""
    n = len(pts)
    if n < 3:
        return ""
    d = f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"
    for i in range(n):
        p0, p1, p2, p3 = pts[(i-1) % n], pts[i], pts[(i+1) % n], pts[(i+2) % n]
        c1 = (p1[0] + (p2[0]-p0[0])*tension/6.0, p1[1] + (p2[1]-p0[1])*tension/6.0)
        c2 = (p2[0] - (p3[0]-p1[0])*tension/6.0, p2[1] - (p3[1]-p1[1])*tension/6.0)
        d += f" C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}"
    return d + " Z"


def cr_open(pts, tension=1.0):
    n = len(pts)
    if n < 2:
        return ""
    ext = [pts[0]] + list(pts) + [pts[-1]]
    d = f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"
    for i in range(1, len(ext)-2):
        p0, p1, p2, p3 = ext[i-1], ext[i], ext[i+1], ext[i+2]
        c1 = (p1[0] + (p2[0]-p0[0])*tension/6.0, p1[1] + (p2[1]-p0[1])*tension/6.0)
        c2 = (p2[0] - (p3[0]-p1[0])*tension/6.0, p2[1] - (p3[1]-p1[1])*tension/6.0)
        d += f" C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}"
    return d


def blob(cx, cy, rx, ry, n=20, lobes=5, amp=0.09, phase=0.0, squash_top=0.0):
    """شكل عضوي مغلق (صوف، فرو، أوراق...)"""
    pts = []
    for i in range(n):
        t = 2*math.pi*i/n
        m = 1.0 + amp*math.sin(lobes*t + phase)
        y = cy + ry*math.sin(t)*m
        if squash_top and y < cy:
            y = cy + (y-cy)*(1.0-squash_top)
        pts.append((cx + rx*math.cos(t)*m, y))
    return cr_closed(pts, 0.95)


def capsule(x0, y0, x1, y1, w0, w1, n=16, bow=0.0, bow_dir=1):
    """جسم مدبّب بين نقطتين بعرض متغيّر (أطراف، ذيول، آذان)"""
    spine = []
    for i in range(n):
        t = i/(n-1.0)
        x = x0 + (x1-x0)*t
        y = y0 + (y1-y0)*t
        if bow:
            x += bow_dir*bow*math.sin(math.pi*t)*0.0
        spine.append((x, y))
    # انحناء خفيف للعمود الفقري
    if bow:
        mx, my = (x0+x1)/2, (y0+y1)/2
        dx, dy = x1-x0, y1-y0
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy/L, dx/L
        for i in range(n):
            t = i/(n-1.0)
            k = math.sin(math.pi*t)*bow
            spine[i] = (spine[i][0]+nx*k, spine[i][1]+ny*k)
    widths = [w0 + (w1-w0)*(i/(n-1.0)) for i in range(n)]
    return tapered(spine, widths)


def tapered(spine, widths):
    """يحوّل عموداً فقرياً + ملف عرض إلى مسار مغلق ناعم"""
    n = len(spine)
    left, right = [], []
    for i, (x, y) in enumerate(spine):
        if i == 0:
            tx, ty = spine[1][0]-x, spine[1][1]-y
        elif i == n-1:
            tx, ty = x-spine[i-1][0], y-spine[i-1][1]
        else:
            tx, ty = spine[i+1][0]-spine[i-1][0], spine[i+1][1]-spine[i-1][1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty/L, tx/L
        w = widths[i]/2.0
        left.append((x+nx*w, y+ny*w))
        right.append((x-nx*w, y-ny*w))
    pts = left + right[::-1]
    # تنعيم الأطراف: أضف نقاط وسطية عند كل طرف
    pts = [left[0], ((left[0][0]+right[0][0])/2, (left[0][1]+right[0][1])/2)] + left[1:-1] + \
          [((left[-1][0]+right[0][0])/2, (left[-1][1]+right[0][1])/2)] + right[::-1]
    return cr_closed(pts, 0.6)


def ellipse_d(cx, cy, rx, ry, rot=0.0):
    if rot:
        return (f"M {cx-rx:.2f} {cy:.2f} A {rx:.2f} {ry:.2f} {rot:.1f} 1 0 {cx+rx:.2f} {cy:.2f} "
                f"A {rx:.2f} {ry:.2f} {rot:.1f} 1 0 {cx-rx:.2f} {cy:.2f} Z")
    return (f"M {cx-rx:.2f} {cy:.2f} A {rx:.2f} {ry:.2f} 0 1 0 {cx+rx:.2f} {cy:.2f} "
            f"A {rx:.2f} {ry:.2f} 0 1 0 {cx-rx:.2f} {cy:.2f} Z")


# ---------------------------------------------------------------------------
# 2) تظليل خلوي (Cel Shading) ثلاثي المستويات
# ---------------------------------------------------------------------------
def cel(base_d, bbox, fill, shadow, sw=5.0,
        shadow_d=None, highlight=None, details=(), uid=None):
    """
    base_d : مسار الشكل الأساسي
    bbox   : (x0,y0,x1,y1)
    """
    x0, y0, x1, y1 = bbox
    cx, cy = (x0+x1)/2, (y0+y1)/2
    rx, ry = (x1-x0)/2, (y1-y0)/2
    if shadow_d is None:
        sx, sy = cx + rx*0.20, cy + ry*0.52
        shadow_d = ellipse_d(sx, sy, rx*1.30, ry*1.22)
    uid = uid or f"u{abs(hash(base_d))%100000}"
    out = [f'<defs><clipPath id="c{uid}"><path d="{base_d}"/></clipPath></defs>']
    out.append(f'<path d="{base_d}" fill="{fill}"/>')
    out.append(f'<g clip-path="url(#c{uid})">')
    out.append(f'<path d="{shadow_d}" fill="{shadow}"/>')
    if highlight:
        out.append(f'<path d="{highlight}" fill="#FFFFFF" opacity="0.42"/>')
    for d in details:
        out.append(d)
    out.append('</g>')
    out.append(f'<path d="{base_d}" fill="none" stroke="{OUTLINE}" stroke-width="{sw:.2f}" '
               f'stroke-linejoin="round" stroke-linecap="round"/>')
    return "".join(out)


def detail_stroke(d, color, w=3.0, op=1.0):
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w:.2f}" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="{op:.2f}"/>')


# ---------------------------------------------------------------------------
# 3) التصيير
# ---------------------------------------------------------------------------
def render_svg(body, x, y, w, h, ss=3):
    """يصيّر محتوى SVG في مستطيل (x,y,w,h) بمضاعفة ss لجودة الحواف"""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x:.2f} {y:.2f} {w:.2f} {h:.2f}" '
           f'width="{int(w*ss)}" height="{int(h*ss)}">{body}</svg>')
    png = resvg_py.svg_to_bytes(svg)
    im = Image.open(BytesIO(bytes(png))).convert("RGBA")
    if ss != 1:
        im = im.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)
    return im


def bbox_of(body, pad=6, probe=(0, 0, 1400, 1400), ss=1):
    """يجد الصندوق الحاصر لمحتوى SVG تجريبياً (ثم نعيد التصيير بجودة عالية)"""
    x, y, w, h = probe
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" '
           f'width="{w}" height="{h}">{body}</svg>')
    png = resvg_py.svg_to_bytes(svg)
    im = Image.open(BytesIO(bytes(png))).convert("RGBA")
    bb = im.getbbox()
    if bb is None:
        return (x, y, x+2, y+2), im
    x0, y0, x1, y1 = bb
    return (x+int(x0)-pad, y+int(y0)-pad, x+int(x1)+pad, y+int(y1)+pad), im
