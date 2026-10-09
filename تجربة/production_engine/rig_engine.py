# -*- coding: utf-8 -*-
"""
==============================================================================
  محرك التحريك — «رحلة الجد صوفان»
  Animation Rig Engine  ·  Phase 5
==============================================================================

هذا هو قلب نظام الإنتاج. يقرأ:
  1) rig_spec.json  — الشجرة الهرمية للمفاصل ونقاط الارتكاز
  2) ملفات PNG/SVG  — الطبقات المنفصلة لكل جزء
  3) timeline.json  — مسار الحركة (Keyframes)

ويُخرج إطارات جاهزة للتجميع.

الفكرة: لا رسم جديد في أي مرحلة. التحريك = تغيير أرقام فقط.
==============================================================================
"""
import os, json, math
from PIL import Image

RIGS_ROOT = "/home/user/Animation-cartoon/تجربة/studio_rigs"

# ---------------------------------------------------------------------------
# تحويلات هندسية 2D
# ---------------------------------------------------------------------------
def rot_pt(x, y, deg):
    a = math.radians(deg)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


# ---------------------------------------------------------------------------
# منحنيات التسهيل (Easing)
# ---------------------------------------------------------------------------
def ease_linear(t):      return t
def ease_in_quad(t):     return t * t
def ease_out_quad(t):    return 1 - (1 - t) * (1 - t)
def ease_in_out(t):      return 3*t*t - 2*t*t*t if False else (t*t*(3 - 2*t))
def smoothstep(t):       return t * t * (3 - 2 * t)
def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t-1)**3 + c1 * (t-1)**2
def ease_out_elastic(t):
    if t == 0 or t == 1: return t
    return 2**(-9*t) * math.sin((t*10 - 0.75) * (2*math.pi/3)) + 1

EASINGS = {
    "linear": ease_linear, "in": ease_in_quad, "out": ease_out_quad,
    "in_out": ease_in_out, "smooth": smoothstep,
    "out_back": ease_out_back, "elastic": ease_out_elastic,
}


# ---------------------------------------------------------------------------
# المسار الزمني (Track) — استيفاء القيم بين الإطارات المفتاحية
# ---------------------------------------------------------------------------
class Track:
    def __init__(self, keys, loop=False, duration=None):
        # keys: [{"t": frame, "v": value, "ease": "in_out"}, ...]
        self.keys = sorted(keys, key=lambda k: k["t"])
        self.loop = loop
        self.duration = duration

    def value_at(self, frame):
        if not self.keys:
            return 0.0
        if len(self.keys) == 1:
            return self.keys[0]["v"]

        f = float(frame)
        ks = self.keys
        if self.loop and self.duration:
            f = f % self.duration

        if f <= ks[0]["t"]:
            return ks[0]["v"]
        if f >= ks[-1]["t"]:
            return ks[-1]["v"]

        for i in range(len(ks) - 1):
            k0, k1 = ks[i], ks[i+1]
            if k0["t"] <= f <= k1["t"]:
                span = k1["t"] - k0["t"]
                t = 0.0 if span == 0 else (f - k0["t"]) / span
                fn = EASINGS.get(k0.get("ease", "linear"), ease_linear)
                t = min(1.0, max(0.0, fn(t)))
                v0, v1 = k0["v"], k1["v"]
                if isinstance(v0, list):
                    return [v0[j] + (v1[j] - v0[j]) * t for j in range(len(v0))]
                return v0 + (v1 - v0) * t
        return ks[-1]["v"]


class Timeline:
    """مجموعة مسارات: { "soufan.torso.rot": Track, ... }"""
    def __init__(self, data):
        self.tracks = {}
        self.swaps = {}          # {"soufan.mouth": {frame: "A"}}
        self.duration = data.get("duration", 60)
        for name, spec in data.get("tracks", {}).items():
            self.tracks[name] = Track(spec.get("keys", []),
                                      loop=spec.get("loop", False),
                                      duration=spec.get("loop_duration"))
        for name, events in data.get("swaps", {}).items():
            self.swaps[name] = {int(k): v for k, v in events.items()}

    def value(self, name, frame, default=0.0):
        if name not in self.tracks:
            return default
        return self.tracks[name].value_at(frame)

    def swap_at(self, name, frame):
        """يرجع آخر قيمة تبديل حدثت عند أو قبل هذا الإطار"""
        ev = self.swaps.get(name)
        if not ev:
            return None
        applicable = [f for f in ev if f <= frame]
        return ev[max(applicable)] if applicable else None


# ---------------------------------------------------------------------------
# دمية التحريك (Rig)
# ---------------------------------------------------------------------------
class Rig:
    def __init__(self, char_id, rigs_root=RIGS_ROOT):
        self.char_id = char_id
        self.dir = os.path.join(rigs_root, "characters", char_id)
        self.spec = json.load(open(os.path.join(self.dir, "rig_spec.json"), encoding="utf-8"))
        self.bones = {b["id"]: b for b in self.spec["bones"]}
        self.order = self._topo_order()                       # ترتيب حلقي سليم (الأب قبل الابن)
        self._cache = {}

    def _topo_order(self):
        """ترتيب طبولوجي: لا يُحل مفصل قبل حلّ أبويه"""
        bones = {b["id"]: b for b in self.spec["bones"]}
        out, done = [], set()
        guard = 0
        while len(out) < len(bones) and guard < 100:
            guard += 1
            for b in self.spec["bones"]:
                bid = b["id"]
                if bid in done:
                    continue
                p = b["parent"]
                if p is None or p in done or p not in bones:
                    out.append(bid); done.add(bid)
        # أي مفصل متبقٍ (دورة غير صالحة) يُضاف كما هو
        for b in self.spec["bones"]:
            if b["id"] not in done:
                out.append(b["id"]); done.add(b["id"])
        return out

    def layer(self, part_name):
        if part_name not in self._cache:
            p = os.path.join(self.dir, part_name + ".png")
            self._cache[part_name] = Image.open(p).convert("RGBA")
        return self._cache[part_name]

    # -- حساب الوضع العالمي لكل مفصل --
    def solve(self, pose):
        """
        pose = {
          "pos":[x,y], "scale":s,
          "rot": {bone_id: deg},          # زوايا محلية
          "rot_root": deg,                 # دوران الجسم كله
          "swaps": {slot: variant},        # تبديل طبقة (فم/عين)
          "flip": False
        }
        يرجع dict: bone_id -> (world_x, world_y, world_rot, scale, part_name)
        """
        root = pose.get("pos", [0, 0])
        sc   = pose.get("scale", self.spec.get("default_scale", 1.0))
        root_rot = pose.get("rot_root", 0.0)
        local_rot = pose.get("rot", {})
        swaps = pose.get("swaps", {})

        world = {}
        world["__root__"] = (root[0], root[1], root_rot, sc)

        for bid in self.order:
            b = self.bones[bid]
            parent_id = b["parent"] or "__root__"
            px, py, prot, psc = world[parent_id][:4]

            ox, oy = b["offset"]
            ox, oy = ox * psc, oy * psc
            rx, ry = rot_pt(ox, oy, prot)
            wx, wy = px + rx, py + ry

            wrot = prot + local_rot.get(bid, 0.0)
            wsc = psc

            part = b["part"]
            if b.get("swappable") and b["swappable"] in swaps:
                slot = b["swappable"]
                variant = swaps[slot]
                part = self.spec["swaps"].get(slot, {}).get(variant, part)

            world[bid] = (wx, wy, wrot, wsc, part)

        return world

    def render(self, canvas, pose):
        world = self.solve(pose)
        flip = pose.get("flip", False)

        # depth ordering: back -> mid -> front -> face
        depth_rank = {"back": 0, "mid": 1, "front": 2, "face": 3, None: 1}

        def rank(bid):
            return depth_rank.get(self.bones[bid].get("depth"), 1)

        tmp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))

        for bid in sorted([b for b in self.order if self.bones[b]["part"]], key=rank):
            if bid == "__root__":
                continue
            wx, wy, wrot, wsc, part = world[bid]
            if not part:
                continue
            img = self.layer(part)
            if flip:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)

            b = self.bones[bid]
            piv = b["pivot"]

            # قياس
            if abs(wsc - 1.0) > 1e-6:
                img = img.resize((max(1, int(img.width * wsc)), max(1, int(img.height * wsc))),
                                 Image.LANCZOS)
                piv = [piv[0] * wsc, piv[1] * wsc]

            # تدوير حول نقطة الارتكاز
            rot = img.rotate(-wrot, resample=Image.BICUBIC, center=(piv[0], piv[1]), expand=True)

            # حساب موضع نقطة الارتكاز داخل الصورة الموسّعة
            a = math.radians(-wrot)
            cx, cy = img.width / 2.0, img.height / 2.0
            ox, oy = piv[0] - cx, piv[1] - cy
            npx = rot.width / 2.0 + (ox * math.cos(a) - oy * math.sin(a))
            npy = rot.height / 2.0 + (ox * math.sin(a) + oy * math.cos(a))

            tx = int(round(wx - npx))
            ty = int(round(wy - npy))

            # تعتيم الأطراف الخلفية (اصطلاح ستوديو للعمق الظاهري)
            if b.get("depth") == "back":
                shade = Image.new("RGBA", rot.size, (0, 0, 0, 70))
                rot = Image.alpha_composite(
                    rot, Image.composite(shade, rot, rot))

            tmp.alpha_composite(rot, (tx, ty))

        canvas.alpha_composite(tmp)
        return canvas


# ---------------------------------------------------------------------------
# القاطرة — تجميع ميكانيكي
# ---------------------------------------------------------------------------
class Locomotive:
    def __init__(self, rigs_root=RIGS_ROOT):
        self.dir = os.path.join(rigs_root, "locomotive")
        self._c = {}

    def part(self, name):
        if name not in self._c:
            self._c[name] = Image.open(os.path.join(self.dir, name + ".png")).convert("RGBA")
        return self._c[name]

    def _place(self, canvas, img, pivot, pos, rot=0, scale=1.0):
        if abs(scale - 1.0) > 1e-6:
            img = img.resize((max(1, int(img.width*scale)), max(1, int(img.height*scale))), Image.LANCZOS)
            pivot = [pivot[0]*scale, pivot[1]*scale]
        r = img.rotate(-rot, resample=Image.BICUBIC, center=(pivot[0], pivot[1]), expand=True)
        a = math.radians(-rot)
        cx, cy = img.width/2.0, img.height/2.0
        ox, oy = pivot[0]-cx, pivot[1]-cy
        npx = r.width/2.0 + (ox*math.cos(a) - oy*math.sin(a))
        npy = r.height/2.0 + (ox*math.sin(a) + oy*math.cos(a))
        canvas.alpha_composite(r, (int(round(pos[0]-npx)), int(round(pos[1]-npy))))

    def render(self, canvas, pose, interior_chars=None):
        """pose = {"pos":[x,y], "scale":s, "wheel_rot":deg, "fan_rot":deg, "steam_t":0..1, "bob":px}"""
        pos = pose.get("pos", [0, 0])
        s = pose.get("scale", 1.0)
        wheel_rot = pose.get("wheel_rot", 0)
        fan_rot = pose.get("fan_rot", 0)
        bob = pose.get("bob", 0)

        WHEEL_POS = [(195, 392), (385, 392), (596, 392)]
        for i, (wx, wy) in enumerate(WHEEL_POS):
            bx = pos[0] + wx*s
            by = pos[1] + (wy + 6*math.sin(bob + i*1.1))*s
            self._place(canvas, self.part("part_spring"), [30, 12], (bx, by - 72*s), 0, 0.85*s)
            self._place(canvas, self.part("part_wheel"), [65, 65], (bx, by), wheel_rot, 0.92*s)

        # الشخصيات داخل المقصورة (قبل الهيكل => تظهر عبر النوافذ الشفافة)
        if interior_chars:
            for img, (ix, iy), isc in interior_chars:
                im = img.resize((max(1,int(img.width*isc)), max(1,int(img.height*isc))), Image.LANCZOS)
                canvas.alpha_composite(im, (int(pos[0] + ix*s - im.width/2),
                                            int(pos[1] + iy*s - im.height/2)))

        # الهيكل بنوافذه الشفافة
        body = self.part("part_chassis_body")
        if abs(s-1.0) > 1e-6:
            body = body.resize((int(body.width*s), int(body.height*s)), Image.LANCZOS)
        canvas.alpha_composite(body, (int(pos[0]-50*s), int(pos[1]+80*s)))

        # مروحة الرياح
        self._place(canvas, self.part("part_wind_fan"), [65, 65],
                    (pos[0] + 648*s, pos[1] + 292*s), fan_rot, 1.05*s)

        # نفثات البخار
        t0 = pose.get("steam_t", 0)
        for i in range(3):
            t = (t0 + i * 0.34) % 1.0
            sc = (0.32 + t * 0.8) * s
            alpha = int(235 * (1 - t))
            st = self.part("part_steam_puff")
            st = st.resize((max(1,int(st.width*sc)), max(1,int(st.height*sc))), Image.LANCZOS)
            st.putalpha(st.split()[3].point(lambda p, k=alpha: int(p*k/255)))
            canvas.alpha_composite(st, (int(pos[0] + (598 + 20*t)*s - st.width/2),
                                        int(pos[1] + (72 - 165*t)*s)))
        return canvas


# ---------------------------------------------------------------------------
# الخلفية 2.5D — خمس طبقات Parallax
# ---------------------------------------------------------------------------
class ParallaxBackground:
    LAYERS = ["layer_01_sky", "layer_02_far_hills", "layer_03_mid_trees",
              "layer_04_road_surface", "layer_05_foreground_signpost"]
    SPEEDS = [0.0, 0.12, 0.35, 1.0, 1.55]

    def __init__(self, rigs_root=RIGS_ROOT, size=(1280, 720)):
        self.dir = os.path.join(rigs_root, "parallax_road")
        self.size = size
        self._c = {}

    def layer(self, name):
        if name not in self._c:
            im = Image.open(os.path.join(self.dir, name + ".png")).convert("RGBA")
            self._c[name] = im.resize(self.size, Image.LANCZOS)
        return self._c[name]

    def render(self, canvas, scroll_px):
        W, H = self.size
        for name, sp in zip(self.LAYERS, self.SPEEDS):
            img = self.layer(name)
            dx = int(scroll_px * sp) % W
            tile = Image.new("RGBA", (W*2, H), (0, 0, 0, 0))
            tile.alpha_composite(img, (0, 0))
            tile.alpha_composite(img, (W, 0))
            canvas.alpha_composite(tile.crop((dx, 0, dx + W, H)), (0, 0))
        return canvas
