# -*- coding: utf-8 -*-
"""
==============================================================================
  مكتبة الحركات 2 — مشي بتثبيت القدم (Foot Contact) عبر حلّ الحركة العكسية
==============================================================================
الفرق عن الإصدار الأول: القدم الآن **توضع على الأرض** ويُحسب ثني الركبة تلقائياً،
بدل تدوير الساق ككتلة واحدة (وهو ما كان ينتج حركة "عصا متأرجحة").
==============================================================================
"""
import math


def foot_path(t, cx, ground_y, stride, lift, stance=0.55):
    """
    t: 0..1 موضع الدورة
    مرحلة الارتكاز (stance): القدم ثابتة على الأرض وتنزلق للخلف
    مرحلة النقل (swing): القدم ترتفع وتقوس للأمام
    """
    t = t % 1.0
    if t < stance:
        u = t/stance
        x = cx + stride*0.5 - stride*u
        y = ground_y
    else:
        u = (t-stance)/(1.0-stance)
        x = cx - stride*0.5 + stride*u
        y = ground_y - lift*math.sin(math.pi*u)
    return x, y


def walk_pose(rig, frame, cycle=26, speed=1.0, stride=0.42, lift=0.16,
              bob=0.020, lean=2.5, arm_swing=24.0, phase=0.0, scale=1.0,
              pelvis=None, mouth=None, eyes=None):
    """
    يبني وضعية مشي كاملة. stride و lift و bob كسور من طول الشخصية.
    """
    S = rig.S
    H = rig.H
    t = ((frame*speed)/cycle + phase) % 1.0

    if pelvis is None:
        pelvis = [0, 0]
    px = pelvis[0]
    py_base = pelvis[1]

    # هزّة الجسم: الأعلى عند منتصف الارتكاز، الأدنى عند التماس
    py = py_base - bob*H*scale*abs(math.sin(2*math.pi*t))

    hip_to_ankle = (S["ankle"] - S["hip"][1])*scale
    ground_y = py + hip_to_ankle

    stride_px = stride*H*scale
    lift_px = lift*H*scale

    ik = {
        "shin_front": foot_path(t,          px, ground_y, stride_px, lift_px),
        "shin_back":  foot_path(t + 0.5,   px, ground_y, stride_px, lift_px),
    }
    ik_sign = {"thigh_front": -1.0, "thigh_back": -1.0}   # الركبة تنثني للخلف

    rot = {}
    # ميل الجذع للأمام + التفات خفيف
    rot["torso"] = -lean + 1.6*math.sin(2*math.pi*t)
    # الرأس يعاكس ميل الجذع ليحافظ على استقامة النظر
    rot["head"] = -rot["torso"]*0.75 + 1.8*math.sin(2*math.pi*t + 0.7)

    # تأرجح الذراعين عكس الساقين
    a_f = math.sin(2*math.pi*(t + 0.5))
    a_b = math.sin(2*math.pi*t)
    rot["upperarm_front"] = -arm_swing*a_f
    rot["upperarm_back"]  = -arm_swing*a_b
    rot["forearm_front"]  = -arm_swing*0.55*math.sin(2*math.pi*(t + 0.5) + 0.55)
    rot["forearm_back"]   = -arm_swing*0.55*math.sin(2*math.pi*t + 0.55)

    swaps = {}
    if mouth:
        swaps["mouth"] = mouth
    if eyes:
        swaps["eyes"] = eyes

    return {"pos": [px, py], "scale": scale, "rot": rot,
            "ik": ik, "ik_sign": ik_sign, "swaps": swaps}


def idle_pose(rig, frame, cycle=90, scale=1.0, pelvis=None, mouth=None, eyes=None,
              tail_wag=True, ear_twitch=True):
    """وقفة حيّة: تنفّس + اهتزاز ذيل + حركة أذن (للجرو)"""
    S = rig.S
    t = ((frame)/cycle) % 1.0
    if pelvis is None:
        pelvis = [0, 0]
    hip_to_ankle = (S["ankle"] - S["hip"][1])*scale
    ground_y = pelvis[1] + hip_to_ankle

    px = pelvis[0]
    py = pelvis[1] - 0.004*rig.H*scale*math.sin(2*math.pi*t)
    gy = py + hip_to_ankle

    half = 0.16*rig.H*scale
    ik = {
        "shin_front": (px + half*0.75, gy),
        "shin_back":  (px - half*0.75, gy),
    }
    ik_sign = {"thigh_front": -1.0, "thigh_back": -1.0}

    rot = {
        "torso": 0.9*math.sin(2*math.pi*t),
        "head":  -0.7*math.sin(2*math.pi*t + 0.5),
        "upperarm_front": 3.0*math.sin(2*math.pi*t + 0.3),
        "upperarm_back":  -3.0*math.sin(2*math.pi*t + 0.3),
        "forearm_front":  2.5*math.sin(2*math.pi*t + 0.8),
        "forearm_back":  -2.5*math.sin(2*math.pi*t + 0.8),
    }
    if tail_wag and "tail" in rig.bones:
        rot["tail"] = 26.0*math.sin(2*math.pi*(frame/11.0))
    if ear_twitch and "ear_front" in rig.bones:
        rot["ear_front"] = 7.0*math.sin(2*math.pi*(frame/17.0))
        rot["ear_back"] = -5.0*math.sin(2*math.pi*(frame/17.0) + 1.1)

    swaps = {}
    if mouth:
        swaps["mouth"] = mouth
    if eyes:
        swaps["eyes"] = eyes
    return {"pos": [px, py], "scale": scale, "rot": rot,
            "ik": ik, "ik_sign": ik_sign, "swaps": swaps}
