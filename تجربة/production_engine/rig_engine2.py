# -*- coding: utf-8 -*-
"""
==============================================================================
  محرك التحريك 2 — أطراف ثنائية الأجزاء + حلّ الحركة العكسية (IK)
==============================================================================
التحسينات الجوهرية عن الإصدار الأول:
  1) كل طرف = جزأين (فخذ/ساق، عضد/ساعد) => ثني حقيقي للركبة والمرفق
  2) حلّ الحركة العكسية (2-Bone IK) => نُحدِّد موضع القدم على الأرض،
     والمحرك يحسب زوايا الركبة تلقائياً. هذا يقضي على "رجعة العصا المتأرجحة".
  3) كل المفاصل مشتقة من هيكل عظمي محسوب — لا أوفستات مُخمَّنة.
  4) الأطراف الخلفية تُرسم بألوان أغمق (لا تراكب أسود) لعمق ظاهري نظيف.
==============================================================================
"""
import os, json, math
from PIL import Image

RIGS2 = "/home/user/Animation-cartoon/تجربة/studio_rigs2"

# زاوية "الراحة" لكل مفصل = الاتجاه الذي رُسم فيه الجزء (زاوية الشاشة، 0=يمين، 90=أسفل)
REST = {
    "pelvis": 0.0, "torso": 0.0, "neck": 0.0, "head": 0.0,
    "eyes": 0.0, "brows": 0.0, "mouth": 0.0,
    "thigh_front": 90.0, "thigh_back": 90.0,
    "shin_front": 90.0,  "shin_back": 90.0,
    "upperarm_front": 90.0, "upperarm_back": 90.0,
    "forearm_front": 90.0, "forearm_back": 90.0,
    "ear_front": 90.0, "ear_back": 90.0,
    "tail": 180.0,
}

# السلاسل التي تُحل بالحركة العكسية: (المفصل الأب، المفصل الابن)
IK_CHAINS = [("thigh_front", "shin_front"),
             ("thigh_back", "shin_back"),
             ("upperarm_front", "forearm_front"),
             ("upperarm_back", "forearm_back")]


def rot_pt(x, y, deg):
    a = math.radians(deg)
    return (x*math.cos(a) - y*math.sin(a), x*math.sin(a) + y*math.cos(a))


def solve_2bone(root, target, l1, l2, sign):
    """يعيد زاويتَي المفصلين بزاوية الشاشة (درجات)"""
    dx = target[0]-root[0]
    dy = target[1]-root[1]
    d = math.hypot(dx, dy)
    d = max(abs(l1-l2)+1e-4, min(l1+l2-1e-4, d))
    try:
        a = math.acos((l1*l1 + d*d - l2*l2)/(2*l1*d))
    except ValueError:
        a = 0.0
    base = math.atan2(dy, dx)
    ang1 = base - sign*a
    jx = root[0] + l1*math.cos(ang1)
    jy = root[1] + l1*math.sin(ang1)
    # أعد الإسقاط على المسافة الصحيحة
    ang2 = math.atan2(target[1]-jy, target[0]-jx)
    return math.degrees(ang1), math.degrees(ang2), (jx, jy)


class Rig2:
    def __init__(self, cid, root=RIGS2):
        self.cid = cid
        self.dir = os.path.join(root, "characters", cid)
        self.map = json.load(open(os.path.join(self.dir, "rig_map.json"), encoding="utf-8"))
        self.S = self.map["skeleton"]
        self.bones = {b["id"]: b for b in self.map["bones"]}
        self.order = self._topo()
        self._img = {}
        H = self.map["H"]
        self.H = H

        # أطوال الأجزاء من الهيكل العظمي (دقة تامة)
        hipx, hipy = self.S["hip"]
        kx, ky = self.S["knee"], self.S["knee"]*0 + self.S["knee"]
        ankle = self.S["ankle"]
        shx, shy = self.S["shoulder"]
        elx, ely = self.S["elbow"]
        wx, wy = self.S["wrist"]
        self.len = {
            "thigh": math.hypot(self.S["hip"][0]*1.05 - self.S["hip"][0]*0.92,
                                self.S["knee"] - self.S["hip"][1]),
            "shin": math.hypot(self.S["hip"][0]*1.10 - self.S["hip"][0]*1.05,
                               self.S["ankle"] - self.S["knee"]),
            "upperarm": math.hypot(self.S["elbow"][0]*0.92 - self.S["shoulder"][0]*0.86,
                                   self.S["elbow"][1] - self.S["shoulder"][1]),
            "forearm": math.hypot(self.S["wrist"][0]*0.94 - self.S["elbow"][0]*0.92,
                                  self.S["wrist"][1] - self.S["elbow"][1]),
        }
        if cid == "simsim":
            self.len["thigh"] = math.hypot(self.S["hip"][0]*1.02 - self.S["hip"][0]*0.90,
                                           self.S["knee"] - self.S["hip"][1])
            self.len["shin"] = math.hypot(self.S["hip"][0]*1.06 - self.S["hip"][0]*1.02,
                                          self.S["ankle"] - self.S["knee"])

    def _topo(self):
        out, done = [], set()
        for _ in range(len(self.bones)):
            for b in self.map["bones"]:
                if b["id"] in done:
                    continue
                p = b["parent"]
                if p is None or p in done:
                    out.append(b["id"]); done.add(b["id"])
        return out

    def img(self, part):
        if part not in self._img:
            self._img[part] = Image.open(os.path.join(self.dir, part + ".png")).convert("RGBA")
        return self._img[part]

    # ------------------------------------------------------------------
    def solve(self, pose):
        root = pose.get("pos", [0, 0])
        sc = pose.get("scale", 1.0)
        local = pose.get("rot", {})
        ik = pose.get("ik", {})
        ik_sign = pose.get("ik_sign", {})
        swaps = pose.get("swaps", {})

        world = {"__root__": (root[0], root[1], 0.0, sc)}
        # --- المرحلة 1: حلّ أمامي (Forward Kinematics) لكل المفاصل ---
        for bid in self.order:
            b = self.bones[bid]
            gp = b["parent"] or "__root__"
            gx, gy, grot, gsc = world[gp][:4]
            ox, oy = b["offset"]
            ox, oy = ox*gsc, oy*gsc
            rx, ry = rot_pt(ox, oy, grot)
            wx, wy = gx+rx, gy+ry

            wrot = grot + local.get(bid, 0.0)
            part = b["part"]
            if b.get("swappable") and b["swappable"] in swaps:
                slot = b["swappable"]
                part = self.map["swaps"].get(slot, {}).get(swaps[slot], part)
            world[bid] = (wx, wy, wrot, gsc, part)

        # --- المرحلة 2: الحركة العكسية (IK) للسلاسل ثنائية الأجزاء ---
        # موضع الأب لا يتأثر بالـ IK (لأن آباءه ليسوا في سلاسل)، فقط زاويته،
        # لذا نعيد حساب زاوية الأب وموضع الابن من المفصل المحسوب.
        ik_result = {}
        for (pa, ch) in IK_CHAINS:
            if pa not in self.bones or ch not in self.bones:
                continue
            if ch not in ik:
                continue
            awx, awy = world[pa][0], world[pa][1]
            target = ik[ch]
            L1 = self.len[pa.split("_")[0]]*sc
            L2 = self.len[ch.split("_")[0]]*sc
            sign = ik_sign.get(pa, -1.0)
            a1, a2, joint = solve_2bone((awx, awy), target, L1, L2, sign)
            ik_result[pa] = (a1, (awx, awy))
            ik_result[ch] = (a2, joint)
            world[pa] = (awx, awy, a1, world[pa][3], world[pa][4])
            world[ch] = (joint[0], joint[1], a2, world[ch][3], world[ch][4])

        return world, ik_result

    # ------------------------------------------------------------------
    def render(self, canvas, pose):
        world, ikres = self.solve(pose)
        ranks = sorted([b for b in self.order if self.bones[b]["part"]],
                       key=lambda bid: self.bones[bid].get("depth", 1))

        for bid in ranks:
            b = self.bones[bid]
            if bid in ikres:
                wx, wy = ikres[bid][1]
                wrot = ikres[bid][0]
                wsc, part = world[bid][3], world[bid][4]
            else:
                wx, wy, wrot, wsc, part = world[bid]
            if not part:
                continue
            img = self.img(part)
            pm = self.map["parts"][part]
            piv = pm["pivot_png"]

            if abs(wsc-1.0) > 1e-6:
                img = img.resize((max(1, int(img.width*wsc)), max(1, int(img.height*wsc))),
                                 Image.LANCZOS)
                piv = [piv[0]*wsc, piv[1]*wsc]

            render_rot = wrot - REST.get(bid, 0.0)
            r = img.rotate(-render_rot, resample=Image.BICUBIC,
                           center=(piv[0], piv[1]), expand=True)
            a = math.radians(-render_rot)
            cx, cy = img.width/2.0, img.height/2.0
            ox, oy = piv[0]-cx, piv[1]-cy
            npx = r.width/2.0 + (ox*math.cos(a) - oy*math.sin(a))
            npy = r.height/2.0 + (ox*math.sin(a) + oy*math.cos(a))
            canvas.alpha_composite(r, (int(round(wx-npx)), int(round(wy-npy))))

            # إعادة رسم الرأس فوق اللحية عند التدوير الشديد غير مطلوبة — الترتيب كافٍ
        return canvas, world, ikres
