# -*- coding: utf-8 -*-
"""
ينشئ ملف rig_spec.json لكل شخصية: يصف الشجرة الهرمية للمفاصل (Bones)،
ونقاط الارتكاز، ونقاط التوصيل بين الأجزاء.
هذا الملف هو "عقد الإنتاج": برنامج التحريك يقرأه، والرسام يرسم وفقه.
"""
import os, json

BASE = "/home/user/Animation-cartoon/تجربة/studio_rigs/characters"

# الأوفستات محسوبة من الفرق بين نقطة الارتكاز ونقطة التوصيل في كل جزء
# (torso pivot=[120,175], neck_joint=[120,48]  =>  offset = [0, -127])
SPECS = {
  "soufan": {
    "display_name": "الجد صوفان",
    "root_bone": "pelvis",
    "bones": [
      {"id":"pelvis",     "parent":None,    "part":None,               "pivot":[0,0],       "offset":[0,0]},
      {"id":"leg_back",   "parent":"pelvis","part":"part_leg",         "pivot":[45,20],     "offset":[-26,6],  "depth":"back"},
      {"id":"arm_back",   "parent":"torso", "part":"part_arm",         "pivot":[45,24],     "offset":[-52,-96],"depth":"back"},
      {"id":"torso",      "parent":"pelvis","part":"part_torso",       "pivot":[120,175],   "offset":[0,0],    "depth":"mid"},
      {"id":"neck",       "parent":"torso", "part":None,               "pivot":[0,0],       "offset":[0,-127]},
      {"id":"head",       "parent":"neck",  "part":"part_head_base",   "pivot":[120,172],   "offset":[0,0],    "depth":"front"},
      {"id":"eyes",       "parent":"head",  "part":"part_eyes_open",   "pivot":[120,172],   "offset":[0,0],    "depth":"face","swappable":"eyes"},
      {"id":"brows",      "parent":"head",  "part":"part_eyebrows",    "pivot":[120,172],   "offset":[0,0],    "depth":"face"},
      {"id":"mouth",      "parent":"head",  "part":"part_mouth_closed_smile","pivot":[120,172],"offset":[0,0],  "depth":"face","swappable":"mouth"},
      {"id":"leg_front",  "parent":"pelvis","part":"part_leg",         "pivot":[45,20],     "offset":[26,6],   "depth":"front"},
      {"id":"arm_front",  "parent":"torso", "part":"part_arm",         "pivot":[45,24],     "offset":[52,-96], "depth":"front"}
    ],
    "swaps": {
      "eyes":  {"open":"part_eyes_open","blink":"part_eyes_blink"},
      "mouth": {"closed":"part_mouth_closed_smile","A":"part_mouth_open_A","O":"part_mouth_open_O","E":"part_mouth_open_E","frown":"part_mouth_frown"}
    },
    "default_scale": 1.25
  },
  "salma": {
    "display_name": "سلمى",
    "root_bone": "pelvis",
    "bones": [
      {"id":"pelvis",    "parent":None,    "part":None,                "pivot":[0,0],     "offset":[0,0]},
      {"id":"leg_back",  "parent":"pelvis","part":"part_leg",          "pivot":[45,20],   "offset":[-24,6], "depth":"back"},
      {"id":"arm_back",  "parent":"torso", "part":"part_arm",          "pivot":[45,24],   "offset":[-46,-92],"depth":"back"},
      {"id":"torso",     "parent":"pelvis","part":"part_torso",        "pivot":[120,175], "offset":[0,0],   "depth":"mid"},
      {"id":"neck",      "parent":"torso", "part":None,                "pivot":[0,0],     "offset":[0,-127]},
      {"id":"head",      "parent":"neck",  "part":"part_head_base",    "pivot":[120,172], "offset":[0,0],   "depth":"front"},
      {"id":"eyes",      "parent":"head",  "part":"part_eyes_open",    "pivot":[120,172], "offset":[0,0],   "depth":"face","swappable":"eyes"},
      {"id":"brows",     "parent":"head",  "part":"part_eyebrows",     "pivot":[120,172], "offset":[0,0],   "depth":"face"},
      {"id":"mouth",     "parent":"head",  "part":"part_mouth_closed_smile","pivot":[120,172],"offset":[0,0],"depth":"face","swappable":"mouth"},
      {"id":"leg_front", "parent":"pelvis","part":"part_leg",          "pivot":[45,20],   "offset":[24,6],  "depth":"front"},
      {"id":"arm_front", "parent":"torso", "part":"part_arm",          "pivot":[45,24],   "offset":[46,-92],"depth":"front"}
    ],
    "swaps": {
      "eyes":  {"open":"part_eyes_open","blink":"part_eyes_blink"},
      "mouth": {"closed":"part_mouth_closed_smile","A":"part_mouth_open_A","O":"part_mouth_open_O","E":"part_mouth_open_E","frown":"part_mouth_frown"}
    },
    "default_scale": 1.0
  },
  "fares": {
    "display_name": "فارس",
    "root_bone": "pelvis",
    "bones": [
      {"id":"pelvis",    "parent":None,    "part":None,                "pivot":[0,0],     "offset":[0,0]},
      {"id":"leg_back",  "parent":"pelvis","part":"part_leg",          "pivot":[45,20],   "offset":[-24,6], "depth":"back"},
      {"id":"arm_back",  "parent":"torso", "part":"part_arm",          "pivot":[45,24],   "offset":[-46,-94],"depth":"back"},
      {"id":"torso",     "parent":"pelvis","part":"part_torso",        "pivot":[120,175], "offset":[0,0],   "depth":"mid"},
      {"id":"neck",      "parent":"torso", "part":None,                "pivot":[0,0],     "offset":[0,-127]},
      {"id":"head",      "parent":"neck",  "part":"part_head_base",    "pivot":[120,172], "offset":[0,0],   "depth":"front"},
      {"id":"eyes",      "parent":"head",  "part":"part_eyes_open",    "pivot":[120,172], "offset":[0,0],   "depth":"face","swappable":"eyes"},
      {"id":"brows",     "parent":"head",  "part":"part_eyebrows",     "pivot":[120,172], "offset":[0,0],   "depth":"face"},
      {"id":"mouth",     "parent":"head",  "part":"part_mouth_closed_smile","pivot":[120,172],"offset":[0,0],"depth":"face","swappable":"mouth"},
      {"id":"leg_front", "parent":"pelvis","part":"part_leg",          "pivot":[45,20],   "offset":[24,6],  "depth":"front"},
      {"id":"arm_front", "parent":"torso", "part":"part_arm",          "pivot":[45,24],   "offset":[46,-94],"depth":"front"}
    ],
    "swaps": {
      "eyes":  {"open":"part_eyes_open","blink":"part_eyes_blink"},
      "mouth": {"closed":"part_mouth_closed_smile","A":"part_mouth_open_A","O":"part_mouth_open_O","E":"part_mouth_open_E","frown":"part_mouth_frown"}
    },
    "default_scale": 1.02
  },
  "simsim": {
    "display_name": "سمسم (الجرو)",
    "root_bone": "pelvis",
    "bones": [
      {"id":"pelvis",    "parent":None,    "part":None,                "pivot":[0,0],     "offset":[0,0]},
      {"id":"tail",      "parent":"torso", "part":"part_tail",         "pivot":[70,78],   "offset":[62,-30],"depth":"back"},
      {"id":"ear_back",  "parent":"head",  "part":"part_ear",          "pivot":[35,18],   "offset":[-72,-140],"depth":"back"},
      {"id":"leg_back",  "parent":"pelvis","part":"part_leg",          "pivot":[45,20],   "offset":[-24,6],  "depth":"back"},
      {"id":"arm_back",  "parent":"torso", "part":"part_arm",          "pivot":[45,24],   "offset":[-44,-88], "depth":"back"},
      {"id":"torso",     "parent":"pelvis","part":"part_torso",        "pivot":[120,175], "offset":[0,0],    "depth":"mid"},
      {"id":"neck",      "parent":"torso", "part":None,                "pivot":[0,0],     "offset":[0,-127]},
      {"id":"head",      "parent":"neck",  "part":"part_head_base",    "pivot":[120,172], "offset":[0,0],    "depth":"front"},
      {"id":"eyes",      "parent":"head",  "part":"part_eyes_open",    "pivot":[120,172], "offset":[0,0],    "depth":"face","swappable":"eyes"},
      {"id":"brows",     "parent":"head",  "part":"part_eyebrows",     "pivot":[120,172], "offset":[0,0],    "depth":"face"},
      {"id":"mouth",     "parent":"head",  "part":"part_mouth_closed_smile","pivot":[120,172],"offset":[0,0], "depth":"face","swappable":"mouth"},
      {"id":"ear_front", "parent":"head",  "part":"part_ear",          "pivot":[35,18],   "offset":[58,-146],"depth":"front"},
      {"id":"leg_front", "parent":"pelvis","part":"part_leg",          "pivot":[45,20],   "offset":[24,6],   "depth":"front"},
      {"id":"arm_front", "parent":"torso", "part":"part_arm",          "pivot":[45,24],   "offset":[44,-88], "depth":"front"}
    ],
    "swaps": {
      "eyes":  {"open":"part_eyes_open","blink":"part_eyes_blink"},
      "mouth": {"closed":"part_mouth_closed_smile","A":"part_mouth_open_A","O":"part_mouth_open_O","E":"part_mouth_open_E","frown":"part_mouth_frown"}
    },
    "default_scale": 0.9,
    "note": "سمسم: ذيل وأذنان بمفاصل مستقلة + حركة رباعية الأطراج => تمييز حركي تام عن الخراف"
  }
}

for cid, spec in SPECS.items():
    d = os.path.join(BASE, cid)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "rig_spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    print(f"✓ rig_spec.json written for {cid} ({spec['display_name']}) — {len([b for b in spec['bones'] if b['part']])} part-bones")
