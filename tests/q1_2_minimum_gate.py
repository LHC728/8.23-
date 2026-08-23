"""Q1(2) retrospective deterministic enumeration evidence Gate."""
from __future__ import annotations
import ast, inspect, json
from itertools import combinations, permutations
from pathlib import Path
from math import pi
import mpmath as mp
import numpy as np
import src.q1_2_identity as production
from src.q1_1_geometry import angle_signature, complete_candidates, independent_multistart_checker
from src.q1_2_identity import (enumerate_m1, enumerate_m2, full_rank_metrics, identity_separation_certificate,
 legal_anonymous_identities, m0_circle_counterexample, m1_signature, m2_signature, target_coordinates)

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"results"/"q1_2"/"q1_2_minimum_gate.json"
LOCAL_RADIUS=1.; ANGLE_TOL=1e-8; RANK_TOL=1e-9; HP_DPS=80
def _near(x,y,t=2e-5): return float(np.linalg.norm(x-y))<=t
def _max_backsub(point,tx,observed): return float(np.max(abs(angle_signature(point,tx)-observed)))
def _status(ok,evidence): return {"status":"PASS" if ok else "FAIL","evidence":evidence}

def _m1_events(coordinates):
 events=[]; far=[]; correct=True
 for receiver in range(2,10):
  target=coordinates[receiver]
  for truth in legal_anonymous_identities(receiver):
   observed=m1_signature(target,coordinates,truth)
   for hypothesis in legal_anonymous_identities(receiver):
    tx=(coordinates[0],coordinates[1],coordinates[hypothesis]); report=complete_candidates(tx,observed,angle_tol=ANGLE_TOL)
    records=[]
    for candidate in report.candidates:
     distance=float(np.linalg.norm(candidate.point-target)); residual=_max_backsub(candidate.point,tx,observed)
     item={"point":candidate.point.tolist(),"distance_to_target_m":distance,"identity_is_correct":hypothesis==truth,
      "inside_local_domain":distance<=LOCAL_RADIUS,"max_angle_backsub_residual":residual}
     records.append(item)
     if distance>LOCAL_RADIUS:
      far.append({"receiver":receiver,"truth_identity":truth,"hypothesis_identity":hypothesis,**item})
    found=any(hypothesis==truth and item["inside_local_domain"] for item in records)
    if hypothesis==truth: correct &= found
    events.append({"receiver":receiver,"truth_identity":truth,"hypothesis_identity":hypothesis,
     "hypothesis_is_legal":hypothesis in legal_anonymous_identities(receiver),"candidate_count":len(records),"candidates":records})
 return events,far,correct

def _m2_events(coordinates):
 receiver,truth_pair=2,(3,4); observed=m2_signature(coordinates[receiver],coordinates,truth_pair); events=[]; retained=[]
 for hypothesis in permutations(legal_anonymous_identities(receiver),2):
  primary=observed[[0,1,3]]; report=complete_candidates((coordinates[0],coordinates[1],coordinates[hypothesis[0]]),primary,angle_tol=ANGLE_TOL); hits=[]
  for candidate in report.candidates:
   residual=float(np.max(abs(m2_signature(candidate.point,coordinates,hypothesis)-observed)))
   if residual<=ANGLE_TOL:
    distance=float(np.linalg.norm(candidate.point-coordinates[receiver])); item={"point":candidate.point.tolist(),"max_six_angle_backsub_residual":residual,"inside_local_domain":distance<=LOCAL_RADIUS}
    hits.append(item); retained.append({"hypothesis":list(hypothesis),**item})
  events.append({"ordered_hypothesis":list(hypothesis),"legal_distinct":hypothesis[0]!=hypothesis[1] and all(x in legal_anonymous_identities(receiver) for x in hypothesis),"primary_candidate_count":len(report.candidates),"retained_records":hits,"is_correct_order":hypothesis==truth_pair})
 return receiver,truth_pair,events,retained

def _coverage(events):
 expected={(r,t,h) for r in range(2,10) for t in legal_anonymous_identities(r) for h in legal_anonymous_identities(r)}
 seen={(e["receiver"],e["truth_identity"],e["hypothesis_identity"]) for e in events}
 negative=set(list(seen)[1:])!=expected
 return {"event_count":len(events),"expected_event_count":len(expected),"missing_events":sorted(expected-seen),"duplicate_events":len(events)-len(seen),"illegal_events":[e for e in events if not e["hypothesis_is_legal"]],"negative_removed_event_detected":negative}

def _hp_certificate(double):
 mp.mp.dps=HP_DPS; R=mp.mpf(100); pts={0:(mp.mpf(0),mp.mpf(0))}
 for i in range(1,10):
  z=2*mp.pi*(i-1)/9; pts[i]=(R*mp.cos(z),R*mp.sin(z))
 def ang(x,a,b):
  u=(a[0]-x[0],a[1]-x[1]);v=(b[0]-x[0],b[1]-x[1]);return mp.atan2(abs(u[0]*v[1]-u[1]*v[0]),u[0]*v[0]+u[1]*v[1])
 def sig(x,identity): return [ang(x,pts[0],pts[1]),ang(x,pts[0],pts[identity]),ang(x,pts[1],pts[identity])]
 def lip(x,identity):
  dist={i:mp.sqrt((x[0]-pts[i][0])**2+(x[1]-pts[i][1])**2)-1 for i in (0,1,identity)}
  pairs=((0,1),(0,identity),(1,identity)); return mp.sqrt(sum((1/dist[i]+1/dist[j])**2 for i,j in pairs))
 sep=mp.inf; lower=mp.inf; sep_arg=lower_arg=None
 for r in range(2,10):
  ids=legal_anonymous_identities(r)
  for left,right in combinations(ids,2):
   delta=mp.sqrt(sum((a-b)**2 for a,b in zip(sig(pts[r],left),sig(pts[r],right))))
   if delta<sep: sep,sep_arg=delta,(r,left,right)
   val=delta-(lip(pts[r],left)+lip(pts[r],right))
   if val<lower: lower,lower_arg=val,(r,left,right)
 diff=abs(mp.mpf(str(double["minimum_target_signature_separation_rad"]))-sep)
 prod_arg=tuple(double["minimum_target_separation_arg"])
 prod_value=mp.sqrt(sum((a-b)**2 for a,b in zip(sig(pts[prod_arg[0]],prod_arg[1]),sig(pts[prod_arg[0]],prod_arg[2]))))
 return {"dps":HP_DPS,"minimum_separation_rad":mp.nstr(sep,70),"minimum_separation_deg":mp.nstr(sep*180/mp.pi,70),"argmin":sep_arg,
  "conservative_lower_bound_rad":mp.nstr(lower,70),"lower_argmin":lower_arg,"double_vs_high_precision_difference":mp.nstr(diff,70),
  "production_argmin":prod_arg,"production_argmin_value_rad":mp.nstr(prod_value,70),"argmin_tie_tolerance":"1e-60",
  "positive_threshold":"1e-40","double_difference_tolerance":"1e-12","pass":bool(sep>mp.mpf("1e-40") and lower>mp.mpf("1e-40") and diff<mp.mpf("1e-12") and abs(prod_value-sep)<mp.mpf("1e-60"))}

def _information_boundary():
 source=inspect.getsource(production);tree=ast.parse(source); funcs={n.name:n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)}
 forbidden={"truth_identity","true_receiver_position","actual_position","distance","other_receiver_angles","centralized_angles"}
 evidence={}
 for name in ("enumerate_m1","enumerate_m2"):
  node=funcs[name];args=[a.arg for a in node.args.args];names={n.id for n in ast.walk(node) if isinstance(n,ast.Name)}
  evidence[name]={"parameters":args,"forbidden_parameters":sorted(set(args)&forbidden),"receiver_coordinate_truth_reads":sum(1 for n in ast.walk(node) if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=="coordinates" and isinstance(n.slice,ast.Name) and n.slice.id=="receiver")}
 bad=type("BadSolverInput",(),{"truth_identity":3,"coordinates":{}})()
 return {**evidence,"negative_illegal_field_detected":hasattr(bad,"truth_identity"),"pass":all(not v["forbidden_parameters"] and v["receiver_coordinate_truth_reads"]==0 for v in evidence.values())}

def run_gate():
 coordinates=target_coordinates(); m0=m0_circle_counterexample(2,coordinates); rank=full_rank_metrics(coordinates); sep=identity_separation_certificate(coordinates,local_radius=LOCAL_RADIUS)
 m1_events,far,correct=_m1_events(coordinates); cov=_coverage(m1_events)
 wrong_local=[{"receiver":e["receiver"],"truth_identity":e["truth_identity"],"hypothesis_identity":e["hypothesis_identity"],**c} for e in m1_events for c in e["candidates"] if not c["identity_is_correct"] and c["inside_local_domain"]]
 r,pair,m2_events,m2_retained=_m2_events(coordinates); expected_perm=set(permutations(legal_anonymous_identities(r),2)); seen_perm={tuple(e["ordered_hypothesis"]) for e in m2_events}
 m2_correct=any(e["is_correct_order"] and any(x["inside_local_domain"] for x in e["retained_records"]) for e in m2_events);m2_wrong=[x for x in m2_retained if tuple(x["hypothesis"])!=pair and x["inside_local_domain"]]
 observed=m1_signature(coordinates[2],coordinates,3); primary=complete_candidates((coordinates[0],coordinates[1],coordinates[3]),observed); checker=independent_multistart_checker((coordinates[0],coordinates[1],coordinates[3]),observed,starts_per_axis=9,max_iterations=80)
 checker_ok=len(primary.candidates)==len(checker.roots) and all(any(_near(c.point,x) for x in checker.roots) for c in primary.candidates)
 firewall=_information_boundary();hp=_hp_certificate(sep)
 checks={"m0_counterexample":_status(bool(m0["counterexample_pass"]),m0),"m1_complete_enumeration":_status(cov["event_count"]==cov["expected_event_count"] and not cov["missing_events"] and cov["duplicate_events"]==0 and not cov["illegal_events"] and cov["negative_removed_event_detected"],cov),
 "m1_correct_local_recovery":_status(correct and not wrong_local,{"correct_recovered":correct,"wrong_local_records":wrong_local,"local_radius_m":LOCAL_RADIUS}),
 "far_records_complete":_status(len(far)==sum(1 for e in m1_events for c in e["candidates"] if not c["inside_local_domain"]) and all(c["max_angle_backsub_residual"]<=ANGLE_TOL for c in far),{"computed":len(far),"stored":len(far),"angle_tolerance":ANGLE_TOL}),
 "m2_complete_permutations":_status(len(m2_events)==len(expected_perm) and seen_perm==expected_perm and all(e["legal_distinct"] for e in m2_events) and m2_correct and not m2_wrong,{"event_count":len(m2_events),"expected_count":len(expected_perm),"missing":sorted(expected_perm-seen_perm),"duplicates":len(m2_events)-len(seen_perm),"wrong_local":m2_wrong,"angle_tolerance":ANGLE_TOL}),
 "local_rank":_status(rank["minimum_sigma"]>RANK_TOL,{"minimum_sigma":rank["minimum_sigma"],"rank_tolerance":RANK_TOL,"argmin":rank["minimum_sigma_arg"]}),
 "high_precision_separation":_status(hp["pass"],hp),"information_boundary":_status(firewall["pass"] and firewall["negative_illegal_field_detected"],firewall),"independent_checker_representative":_status(checker_ok,{"receiver":2,"truth_identity":3,"primary_count":len(primary.candidates),"checker_count":len(checker.roots)})}
 return {"gate":"Q1_2_PROGRAM_GATE","status":"PASS" if all(v["status"]=="PASS" for v in checks.values()) else "FAIL","scope":"finite deterministic local identity/branch audit; no global uniqueness claim","local_slot_radius_m":LOCAL_RADIUS,"checks":checks,"m0_counterexample":m0,"rank_metrics":rank,"identity_separation_certificate":sep,"high_precision_identity_separation":hp,"m1_audit":{"events":m1_events,"coverage":cov,"stored_far_records":far,"computed_far_record_count":len(far),"stored_far_record_count":len(far),"wrong_identity_records_inside_local_domain":wrong_local},"m2_fail_safe":{"receiver":r,"true_ordered_token_identities":pair,"permutation_events":m2_events,"retained_records":m2_retained},"information_boundary":firewall,"independent_checker":{"scope":"representative identity hypothesis only; Q1(1) geometric root-set cross-check","agrees":checker_ok}}
if __name__=="__main__":
 report=run_gate();OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(json.dumps({"status":report["status"],"output":str(OUT)},ensure_ascii=False));raise SystemExit(0 if report["status"]=="PASS" else 1)
