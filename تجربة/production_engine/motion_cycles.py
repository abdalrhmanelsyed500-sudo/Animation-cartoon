# -*- coding: utf-8 -*-
"""
==============================================================================
  مكتبة الحركات الجاهزة — «رحلة الجد صوفان»
  Motion Cycle Library · Phase 5
==============================================================================
كل حركة هنا = جدول إطارات مفتاحية (Keyframes) يُغذّي محرك التحريك.
لا رسم جديد، لا توليد صور. أرقام فقط.
==============================================================================
"""

# ---------------------------------------------------------------------------
# 1) مشية الخراف (صوفان / سلمى / فارس) — ثقيلة، متزنة، واضحة
#    الدورة = 24 إطار (ثانية واحدة عند 24fps) = خطوة كاملة
# ---------------------------------------------------------------------------
CYCLE_SHEEP_WALK = {
    "_comment": "مشية بشرية ثنائية: الساقان خارج الطور 180°، الذراعان عكسياً، الجسم يهتز مرتين",
    "duration": 24,
    "leg_front.rot": [{"t": 0, "v": -26, "ease": "smooth"}, {"t": 6, "v": 0,  "ease": "smooth"},
                      {"t": 12, "v": 26, "ease": "smooth"}, {"t": 18, "v": 0,  "ease": "smooth"},
                      {"t": 24, "v": -26, "ease": "smooth"}],
    "leg_back.rot":  [{"t": 0, "v": 26,  "ease": "smooth"}, {"t": 6, "v": 0,  "ease": "smooth"},
                      {"t": 12, "v": -26,"ease": "smooth"}, {"t": 18, "v": 0,  "ease": "smooth"},
                      {"t": 24, "v": 26,  "ease": "smooth"}],
    "arm_front.rot": [{"t": 0, "v": 24,  "ease": "smooth"}, {"t": 12, "v": -24, "ease": "smooth"},
                      {"t": 24, "v": 24,  "ease": "smooth"}],
    "arm_back.rot":  [{"t": 0, "v": -24, "ease": "smooth"}, {"t": 12, "v": 24,  "ease": "smooth"},
                      {"t": 24, "v": -24, "ease": "smooth"}],
    "bob":           [{"t": 0, "v": 0,   "ease": "smooth"}, {"t": 6, "v": -7, "ease": "smooth"},
                      {"t": 12, "v": 0,  "ease": "smooth"}, {"t": 18, "v": -7, "ease": "smooth"},
                      {"t": 24, "v": 0,  "ease": "smooth"}],
    "torso.rot":     [{"t": 0, "v": -2.5,"ease": "smooth"}, {"t": 12, "v": 2.5, "ease": "smooth"},
                      {"t": 24, "v": -2.5,"ease": "smooth"}],
    "head.rot":      [{"t": 0, "v": 2.5, "ease": "smooth"}, {"t": 12, "v": -2.5,"ease": "smooth"},
                      {"t": 24, "v": 2.5, "ease": "smooth"}],
}

# ---------------------------------------------------------------------------
# 2) خبب الجرو (سمسم) — سريع، نطّاط، وأذناه وذيله يتحركان
#    الدورة = 16 إطار (أسرع من الخراف بـ 1.5×) = تمييز حركي صريح
# ---------------------------------------------------------------------------
CYCLE_PUPPY_TROT = {
    "_comment": "خبب رباعي الإيقاع: أقصر وأسرع وأكثر نطّاً + ذيل يهتز + أذنان تتأرجحان",
    "duration": 16,
    "leg_front.rot": [{"t": 0, "v": -34, "ease": "smooth"}, {"t": 4, "v": 0,  "ease": "smooth"},
                      {"t": 8, "v": 34,  "ease": "smooth"}, {"t": 12, "v": 0,  "ease": "smooth"},
                      {"t": 16, "v": -34, "ease": "smooth"}],
    "leg_back.rot":  [{"t": 0, "v": 34,  "ease": "smooth"}, {"t": 4, "v": 0,  "ease": "smooth"},
                      {"t": 8, "v": -34, "ease": "smooth"}, {"t": 12, "v": 0,  "ease": "smooth"},
                      {"t": 16, "v": 34,  "ease": "smooth"}],
    "arm_front.rot": [{"t": 0, "v": 30,  "ease": "smooth"}, {"t": 8, "v": -30, "ease": "smooth"},
                      {"t": 16, "v": 30,  "ease": "smooth"}],
    "arm_back.rot":  [{"t": 0, "v": -30, "ease": "smooth"}, {"t": 8, "v": 30,  "ease": "smooth"},
                      {"t": 16, "v": -30, "ease": "smooth"}],
    "bob":           [{"t": 0, "v": 0,   "ease": "smooth"}, {"t": 4, "v": -15,"ease": "smooth"},
                      {"t": 8, "v": 0,   "ease": "smooth"}, {"t": 12, "v": -15,"ease": "smooth"},
                      {"t": 16, "v": 0,  "ease": "smooth"}],
    "torso.rot":     [{"t": 0, "v": -5,  "ease": "smooth"}, {"t": 8, "v": 5,   "ease": "smooth"},
                      {"t": 16, "v": -5, "ease": "smooth"}],
    "head.rot":      [{"t": 0, "v": 4,   "ease": "smooth"}, {"t": 8, "v": -4,  "ease": "smooth"},
                      {"t": 16, "v": 4,  "ease": "smooth"}],
    "tail.rot":      [{"t": 0, "v": -32, "ease": "smooth"}, {"t": 4, "v": 0,   "ease": "smooth"},
                      {"t": 8, "v": 32,  "ease": "smooth"}, {"t": 12, "v": 0,  "ease": "smooth"},
                      {"t": 16, "v": -32, "ease": "smooth"}],
    "ear_front.rot": [{"t": 0, "v": -18, "ease": "smooth"}, {"t": 5, "v": 14,  "ease": "smooth"},
                      {"t": 10, "v": -10,"ease": "smooth"}, {"t": 16, "v": -18, "ease": "smooth"}],
    "ear_back.rot":  [{"t": 0, "v": 16,  "ease": "smooth"}, {"t": 5, "v": -14, "ease": "smooth"},
                      {"t": 10, "v": 12, "ease": "smooth"}, {"t": 16, "v": 16,  "ease": "smooth"}],
}

# ---------------------------------------------------------------------------
# 3) وقفة التنفّس (Idle) — تُشغَّل تحت أي حركة أخرى
# ---------------------------------------------------------------------------
CYCLE_IDLE_BREATH = {
    "_comment": "تنفّس خفيف يمنع جمود الشخصية عندما لا تتحرك",
    "duration": 72,
    "torso.rot": [{"t": 0, "v": 0, "ease": "smooth"}, {"t": 36, "v": -1.6, "ease": "smooth"},
                  {"t": 72, "v": 0, "ease": "smooth"}],
    "head.rot":  [{"t": 0, "v": 0, "ease": "smooth"}, {"t": 36, "v": 1.4, "ease": "smooth"},
                  {"t": 72, "v": 0, "ease": "smooth"}],
    "bob":       [{"t": 0, "v": 0, "ease": "smooth"}, {"t": 36, "v": -3, "ease": "smooth"},
                  {"t": 72, "v": 0, "ease": "smooth"}],
}

# ---------------------------------------------------------------------------
# 4) ذيل سمسم — اهتزاز فرح (يُشغَّل وحده عند الوقوف)
# ---------------------------------------------------------------------------
CYCLE_TAIL_WAG = {
    "_comment": "اهتزاز الذيل: أسرع من أي حركة أخرى => علامة الشخصية",
    "duration": 10,
    "tail.rot": [{"t": 0, "v": -38, "ease": "smooth"}, {"t": 5, "v": 34, "ease": "smooth"},
                 {"t": 10, "v": -38, "ease": "smooth"}],
    "ear_front.rot": [{"t": 0, "v": -12, "ease": "smooth"}, {"t": 5, "v": 8, "ease": "smooth"},
                      {"t": 10, "v": -12, "ease": "smooth"}],
}

CYCLES = {
    "sheep_walk": CYCLE_SHEEP_WALK,
    "puppy_trot": CYCLE_PUPPY_TROT,
    "idle_breath": CYCLE_IDLE_BREATH,
    "tail_wag": CYCLE_TAIL_WAG,
}


def sample_cycle(cycle, frame, cycle_len=None):
    """يقرأ قيمة كل مسار في دورة الحركة عند إطار معيّن (مع التكرار اللانهائي)"""
    from rig_engine import Track
    length = cycle_len or cycle["duration"]
    out = {}
    for key, keys in cycle.items():
        if key.startswith("_") or key == "duration":
            continue
        tr = Track(keys, loop=True, duration=length)
        out[key] = tr.value_at(frame % length)
    return out


def merge_cycles(*samples):
    """يدمج عدّة دورات: الدورات اللاحقة تتجاوز السابقة"""
    merged = {}
    for s in samples:
        merged.update(s)
    return merged
