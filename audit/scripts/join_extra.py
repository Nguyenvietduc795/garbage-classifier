"""Tinh them cac so tong hop tu probs da luu (audit/eval_realworld/*_probs.json) de doi chieu bang 4.5/4.6/5.4.
Chay: python audit/scripts/join_extra.py  (cwd C:/AL-PLR)"""
import json, sys
from pathlib import Path
A = Path("audit/eval_realworld")
G = {"organic":"huu-co","battery":"nguy-hiem","clothes":"khong-tai-che"}
grp = lambda c: G.get(c, "tai-che")
OLD102 = ["realworld_test","realworld_test2","realworld_loai_bo/realworld_test","realworld_loai_bo/realworld_test2"]
SETS8 = ["realworld_rw5_test","realworld_mta_test","realworld_bower_test","realworld_bdw_test","realworld_curated","realworld_test","realworld_test2","realworld_clothes_test"]

def pred(p, cls, t, mode):
    if p[0] >= t: return "battery", p[0]
    if mode == "class":
        i = max(range(1,8), key=lambda j: p[j]); return cls[i], p[i]
    s = {}
    for j in range(1,8): s[grp(cls[j])] = s.get(grp(cls[j]),0)+p[j]
    g = max(s, key=s.get); return {"huu-co":"organic","khong-tai-che":"clothes","tai-che":"plastic"}[g], s[g]

def stats(run, names, t, mode="class", key="p_web"):
    d = json.load(open(A/f"{run}_probs.json")); cls = d["classes"]
    ok=n=pin=pinn=fa=0
    for nm in names:
        for r in d["sets"][nm]["records"]:
            c, _ = pred(r[key], cls, t, mode); n+=1
            ok += grp(c)==grp(r["loai"])
            if r["loai"]=="battery": pinn+=1; pin += c=="battery"
            else: fa += c=="battery"
    return ok,n,pin,pinn,fa

def conf(run, names, t, key="p_web", pin_t=0.5):
    d = json.load(open(A/f"{run}_probs.json")); cls = d["classes"]; ok=bad=unsure=0
    for nm in names:
        for r in d["sets"][nm]["records"]:
            c, _ = pred(r[key], cls, pin_t, "class")
            pr = sum(r[key][j] for j in range(8) if grp(cls[j]) == grp(c))  # web: do chac = tong xac suat nhom
            if pr < t: unsure+=1
            elif grp(c)==grp(r["loai"]): ok+=1
            else: bad+=1
    return ok,bad,unsure

out = {}
for t in (0.5, 0.7):
    out[f"v5 t={t} 102cu"] = stats("v5_r18", OLD102, t)
    for s in ("realworld_pin_test","realworld_rw5_test","realworld_bower_test","realworld_mta_test"):
        out[f"v5 t={t} {s}"] = stats("v5_r18", [s], t)
for mode in ("class","group"):
    for key in ("p_web","p_backend"):
        for s in [OLD102,["realworld_pin_test"],["realworld_rw5_test"],["realworld_bower_test"],["realworld_mta_test"]]:
            out[f"v2 pin0.3 {mode} {key} {s[0] if len(s)==1 else '102cu'}"] = stats("v2_r18", s, 0.3, mode, key)
for run in ("v5_r18","v5_r18_s1","v5_r18_s2"):
    out[f"{run} 8bo t0.5"] = stats(run, SETS8, 0.5)
    out[f"{run} pin_test"] = stats(run, ["realworld_pin_test"], 0.5)
    out[f"{run} clothes"] = stats(run, ["realworld_clothes_test"], 0.5)
    out[f"{run} 8bo khong trung curated"] = stats(run, [s for s in SETS8 if s!="realworld_curated"], 0.5)
for run in ("v2_r18","v5_r18"):
    for t in (0.4,0.5,0.6):
        out[f"conf {run} t={t} 102cu"] = conf(run, OLD102, t)
        out[f"conf {run} t={t} curated49"] = conf(run, ["realworld_curated"], t)
for k,v in out.items(): print(k, v)
json.dump(out, open("audit/join_extra.json","w"), indent=1)
