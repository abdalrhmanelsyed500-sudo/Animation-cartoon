# -*- coding: utf-8 -*-
"""
تصدير طبقات الشخصيات: PNG لكل جزء + rig_map.json بمفاصل محسوبة (لا مُخمَّنة).
"""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from art_lib import render_svg, bbox_of
from char_design import build_sheep, build_dog

OUT = "/home/user/Animation-cartoon/تجربة/studio_rigs2/characters"
os.makedirs(OUT, exist_ok=True)

SPECS = {
  "soufan": dict(kind="sheep", H=800, n_heads=3.20, body_hw=0.195, shoulder_hw=0.118,
                 hip_hw=0.080, head_hw=0.138,
                 outfit="vest_petrol", cap=True, beard=True, glasses=True, thick_brows=True,
                 colors=dict(wool="#F5EFE2", wool_sh="#DCD1BA", skin="#D7B18A", skin_sh="#B98F65",
                             cloth="#2B5B6C", cloth_sh="#1D4150", brass="#D49B42",
                             cap="#1F3447", beard="#FFFFFF", beard_sh="#DCE3EA",
                             nose="#3A2A24", iris="#5A3D22", accent="#D49B42",
                             leather="#5C4033", hoof="#362821", accent2="#4A6B53")),
  "salma": dict(kind="sheep", H=650, n_heads=3.10, body_hw=0.182, shoulder_hw=0.108,
                hip_hw=0.074, head_hw=0.146,
                outfit="tunic_mustard", clip=True,
                colors=dict(wool="#FBF8F3", wool_sh="#E4DCCE", skin="#E2BE9B", skin_sh="#C29A76",
                            cloth="#E6A832", cloth_sh="#C78B18", accent="#2A9D8F",
                            accent2="#4A6B53", leather="#7A4B3A", brass="#D49B42",
                            nose="#3A2A24", iris="#2E4A3E", hoof="#593A28")),
  "fares": dict(kind="sheep", H=660, n_heads=3.05, body_hw=0.186, shoulder_hw=0.110,
                hip_hw=0.076, head_hw=0.142,
                outfit="vest_brick", forelock=True,
                colors=dict(wool="#FAF6EE", wool_sh="#E1D7C4", skin="#DFB995", skin_sh="#BF9570",
                            cloth="#D9534F", cloth_sh="#B03A36", leather="#5C4033",
                            brass="#D49B42", nose="#3A2A24", iris="#3B2818", hoof="#593A28")),
  "simsim": dict(kind="dog", H=560, n_heads=2.90, body_hw=0.150, shoulder_hw=0.104,
                 hip_hw=0.076, head_hw=0.156,
                 colors=dict(fur="#C68642", fur_sh="#9E6626", patch="#7B4B27",
                             cream="#F4E7D3", collar="#2E8B57", brass="#D49B42",
                             iris="#3A2312")),
}


def build(cid):
    spec = SPECS[cid]
    if spec["kind"] == "sheep":
        return build_sheep(spec), spec
    return build_dog(spec), spec


def export(cid):
    (S, parts, face), spec = build(cid)
    H = S["H"]
    d = os.path.join(OUT, cid)
    os.makedirs(d, exist_ok=True)
    PROBE = (-H*1.0, -H*0.35, H*2.0, H*1.9)

    for v in ("open", "blink"):
        parts[f"eyes_{v}"] = {"draw": (lambda back=False, v=v: face["eyes"](v)),
                              "pivot": (0.0, S["neck"][1])}
    parts["brows"] = {"draw": (lambda back=False: face["brows"]()),
                      "pivot": (0.0, S["neck"][1])}
    for v in ("closed", "A", "O", "E", "frown"):
        parts[f"mouth_{v}"] = {"draw": (lambda back=False, v=v: face["mouth"](v)),
                               "pivot": (0.0, S["neck"][1])}
    if spec["kind"] == "dog":
        for side in ("front", "back"):
            parts[f"ear_{side}"] = {"draw": (lambda back=False, side=side: face["ear"](side)),
                                    "pivot": face["ear_pivot"](side)}
        parts["tail"] = {"draw": (lambda back=False: face["tail"]()),
                         "pivot": face["tail_pivot"]()}

    # ---------- تصدير كل طبقة ----------
    manifest = {"parts": {}, "skeleton": {k: (list(v) if isinstance(v, tuple) else v)
                                          for k, v in S.items()}}
    for name, p in parts.items():
        body, _ = p["draw"]()
        bb, _ = bbox_of(body, pad=8, probe=PROBE, ss=1)
        x0, y0, x1, y1 = bb
        w, h = max(2, x1-x0), max(2, y1-y0)
        img = render_svg(body, x0, y0, w, h, ss=3)
        img.save(os.path.join(d, f"{name}.png"))
        manifest["parts"][name] = {
            "file": f"{name}.png",
            "pivot_png": [round(p["pivot"][0]-x0, 2), round(p["pivot"][1]-y0, 2)],
            "size": [w, h],
            "bbox_design": [x0, y0, x1, y1],
        }
        print(f"  {cid}/{name}.png  {w}x{h}  pivot={manifest['parts'][name]['pivot_png']}")

    # ---------- الشجرة الهرمية بأوفستات محسوبة من الهيكل ----------
    hip = S["hip"][1]
    neck_y = S["neck"][1]
    def piv(n): return parts[n]["pivot"]

    if spec["kind"] == "sheep":
        bones = [
            {"id": "pelvis", "parent": None, "part": None, "offset": [0.0, 0.0], "depth": 1},
            {"id": "thigh_back", "parent": "pelvis", "part": "thigh_back",
             "offset": [piv("thigh_back")[0], piv("thigh_back")[1]-hip], "depth": 0},
            {"id": "shin_back", "parent": "thigh_back", "part": "shin_back",
             "offset": [piv("shin_back")[0]-piv("thigh_back")[0], piv("shin_back")[1]-piv("thigh_back")[1]], "depth": 0},
            {"id": "torso", "parent": "pelvis", "part": "torso", "offset": [0.0, 0.0], "depth": 2},
            {"id": "upperarm_back", "parent": "torso", "part": "upperarm_back",
             "offset": [piv("upperarm_back")[0], piv("upperarm_back")[1]-hip], "depth": 0},
            {"id": "forearm_back", "parent": "upperarm_back", "part": "forearm_back",
             "offset": [piv("forearm_back")[0]-piv("upperarm_back")[0], piv("forearm_back")[1]-piv("upperarm_back")[1]], "depth": 0},
            {"id": "neck", "parent": "torso", "part": None, "offset": [0.0, neck_y-hip], "depth": 3},
            {"id": "head", "parent": "neck", "part": "head", "offset": [0.0, 0.0], "depth": 5},
            {"id": "eyes", "parent": "head", "part": "eyes_open", "offset": [0.0, 0.0], "depth": 7, "swappable": "eyes"},
            {"id": "brows", "parent": "head", "part": "brows", "offset": [0.0, 0.0], "depth": 8},
            {"id": "mouth", "parent": "head", "part": "mouth_closed", "offset": [0.0, 0.0], "depth": 8, "swappable": "mouth"},
            {"id": "thigh_front", "parent": "pelvis", "part": "thigh_front",
             "offset": [piv("thigh_front")[0], piv("thigh_front")[1]-hip], "depth": 5},
            {"id": "shin_front", "parent": "thigh_front", "part": "shin_front",
             "offset": [piv("shin_front")[0]-piv("thigh_front")[0], piv("shin_front")[1]-piv("thigh_front")[1]], "depth": 5},
            {"id": "upperarm_front", "parent": "torso", "part": "upperarm_front",
             "offset": [piv("upperarm_front")[0], piv("upperarm_front")[1]-hip], "depth": 6},
            {"id": "forearm_front", "parent": "upperarm_front", "part": "forearm_front",
             "offset": [piv("forearm_front")[0]-piv("upperarm_front")[0], piv("forearm_front")[1]-piv("upperarm_front")[1]], "depth": 6},
        ]
    else:
        bones = [
            {"id": "pelvis", "parent": None, "part": None, "offset": [0.0, 0.0], "depth": 1},
            {"id": "tail", "parent": "torso", "part": "tail",
             "offset": [piv("tail")[0], piv("tail")[1]-hip], "depth": 0},
            {"id": "thigh_back", "parent": "pelvis", "part": "thigh_back",
             "offset": [piv("thigh_back")[0], piv("thigh_back")[1]-hip], "depth": 0},
            {"id": "shin_back", "parent": "thigh_back", "part": "shin_back",
             "offset": [piv("shin_back")[0]-piv("thigh_back")[0], piv("shin_back")[1]-piv("thigh_back")[1]], "depth": 0},
            {"id": "ear_back", "parent": "head", "part": "ear_back",
             "offset": [piv("ear_back")[0], piv("ear_back")[1]-neck_y], "depth": 3},
            {"id": "torso", "parent": "pelvis", "part": "torso", "offset": [0.0, 0.0], "depth": 2},
            {"id": "upperarm_back", "parent": "torso", "part": "upperarm_back",
             "offset": [piv("upperarm_back")[0], piv("upperarm_back")[1]-hip], "depth": 0},
            {"id": "forearm_back", "parent": "upperarm_back", "part": "forearm_back",
             "offset": [piv("forearm_back")[0]-piv("upperarm_back")[0], piv("forearm_back")[1]-piv("upperarm_back")[1]], "depth": 0},
            {"id": "neck", "parent": "torso", "part": None, "offset": [0.0, neck_y-hip], "depth": 3},
            {"id": "head", "parent": "neck", "part": "head", "offset": [0.0, 0.0], "depth": 5},
            {"id": "eyes", "parent": "head", "part": "eyes_open", "offset": [0.0, 0.0], "depth": 7, "swappable": "eyes"},
            {"id": "brows", "parent": "head", "part": "brows", "offset": [0.0, 0.0], "depth": 8},
            {"id": "mouth", "parent": "head", "part": "mouth_closed", "offset": [0.0, 0.0], "depth": 8, "swappable": "mouth"},
            {"id": "ear_front", "parent": "head", "part": "ear_front",
             "offset": [piv("ear_front")[0], piv("ear_front")[1]-neck_y], "depth": 6},
            {"id": "thigh_front", "parent": "pelvis", "part": "thigh_front",
             "offset": [piv("thigh_front")[0], piv("thigh_front")[1]-hip], "depth": 5},
            {"id": "shin_front", "parent": "thigh_front", "part": "shin_front",
             "offset": [piv("shin_front")[0]-piv("thigh_front")[0], piv("shin_front")[1]-piv("thigh_front")[1]], "depth": 5},
            {"id": "upperarm_front", "parent": "torso", "part": "upperarm_front",
             "offset": [piv("upperarm_front")[0], piv("upperarm_front")[1]-hip], "depth": 6},
            {"id": "forearm_front", "parent": "upperarm_front", "part": "forearm_front",
             "offset": [piv("forearm_front")[0]-piv("upperarm_front")[0], piv("forearm_front")[1]-piv("upperarm_front")[1]], "depth": 6},
        ]

    manifest["swaps"] = {
        "eyes": {"open": "eyes_open", "blink": "eyes_blink"},
        "mouth": {"closed": "mouth_closed", "A": "mouth_A", "O": "mouth_O",
                  "E": "mouth_E", "frown": "mouth_frown"},
    }
    manifest["bones"] = bones
    manifest["H"] = H
    manifest["n_heads"] = spec["n_heads"]
    manifest["kind"] = spec["kind"]
    with open(os.path.join(d, "rig_map.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    return S, parts, manifest


if __name__ == "__main__":
    for cid in ["soufan", "salma", "fares", "simsim"]:
        print(f"\u25b6 {cid}")
        export(cid)
