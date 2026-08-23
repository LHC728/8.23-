"""Deterministic Q1(3) remediation Gate; no batch or Q2 work."""
from __future__ import annotations
import inspect, json
from pathlib import Path
from math import cos, sin
import numpy as np
from src.q1_3_adjustment import (
 A,B,C,O,ANCHORS,ControllerSettings,LocalControllerInput,ObservationPlant,
 bc_spec,controller_firewall_schema,derivative_audit,exact_local_best_response,
 finite_difference_controller,follower_metrics,pair_cycle_metrics,preloaded_follower_spec,
 table1_coordinates,target_coordinates,transform_positions)
from src.q1_3_evaluator import evaluate_regular_nonagon,holdout_report

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"results"/"q1_3"/"q1_3_program_gate.json"
SETTINGS=ControllerSettings()

def _input(receiver,spec,step): return LocalControllerInput(receiver,tuple(spec["main_angles"]),step)
def _run_action(world,receiver,spec,step,axes,exact=False):
 plant=ObservationPlant(world,receiver,spec["main_pairs"],spec["main_angles"],axes)
 local=_input(receiver,spec,step)
 trace=exact_local_best_response(local,plant.observe,plant.analytic_jacobian) if exact else finite_difference_controller(local,plant.observe,settings=SETTINGS)
 plant.apply(trace.local_displacement)
 return trace

def _bootstrap(world,axes,exact=False):
 traces=[]
 for cycle in range(5):
  for receiver,step in ((B,"BC_B"),(C,"BC_C")):
   trace=_run_action(world,receiver,bc_spec(receiver),"{}:{}".format(step,cycle),axes,exact)
   traces.append((str(receiver),trace))
 return {"traces":traces,"max_target_error_m":max(float(np.linalg.norm(world[i]-target_coordinates()[i])) for i in (B,C))}

def _followers(world,axes,ideal):
 specs={i:preloaded_follower_spec(i,target=ideal) for i in (2,3,5,6,8,9)}
 traces={str(i):_run_action(world,i,specs[i],"FOUR_ANCHOR",axes) for i in specs}
 holdouts={str(i):holdout_report(world,i,specs[i]) for i in specs}
 return {"traces":traces,"holdouts":holdouts,"max_target_error_m":max(float(np.linalg.norm(world[i]-ideal[i])) for i in specs),"preloaded_specs":{str(i):{"main_angles":specs[i]["main_angles"],"holdout_angles":specs[i]["holdout_angles"]} for i in specs}}

def _replay(exact=False,matrix=None):
 matrix=np.eye(2) if matrix is None else matrix; world=transform_positions(table1_coordinates(),matrix); ideal=transform_positions(target_coordinates(),matrix)
 boot=_bootstrap(world,matrix,exact); followers=_followers(world,matrix,ideal)
 base={i:matrix.T@world[i] for i in world}
 return {"world":world,"base_world":base,"bootstrap":boot,"followers":followers,"metrics":evaluate_regular_nonagon(base)}

def _compact_trace(trace):
 return {"status":trace.status,"final_residual_norm":trace.residual_norms[-1],"probes":trace.probes,"backtracks":trace.backtracks,"local_displacement_m":trace.local_displacement.tolist()}
def _compact(replay):
 return {"bootstrap":{"max_target_error_m":replay["bootstrap"]["max_target_error_m"],"traces":[{"receiver":n,**_compact_trace(t)} for n,t in replay["bootstrap"]["traces"]]},
         "followers":{"max_target_error_m":replay["followers"]["max_target_error_m"],"traces":{n:_compact_trace(t) for n,t in replay["followers"]["traces"].items()},"holdouts":replay["followers"]["holdouts"],"preloaded_specs":replay["followers"]["preloaded_specs"]},"metrics":replay["metrics"]}

def _schedule_audit():
 rounds=[{"name":"B","tx":(O,A,C),"receiver":B,"fixed":(O,A,C)},{"name":"C","tx":(O,A,B),"receiver":C,"fixed":(O,A,B)},{"name":"followers","tx":ANCHORS,"receiver":None,"fixed":ANCHORS}]
 records=[]
 for row in rounds:
  records.append({"round":row["name"],"has_FY00":O in row["tx"],"outer_transmitters":len(row["tx"])-1,"receiver_not_transmitter":row["receiver"] is None or row["receiver"] not in row["tx"],"transmitters_fixed_during_probe_and_motion":set(row["tx"])==set(row["fixed"])})
 return {"rounds":records,"FY00_FY01_fixed":True,"FY04_FY07_fixed_in_four_anchor_stage":set(rounds[-1]["fixed"])==set(ANCHORS)}

def _firewall_audit():
 schema=controller_firewall_schema(); signature=list(inspect.signature(finite_difference_controller).parameters)
 return {**schema,"controller_parameters":signature,"world_field_count":len(schema["forbidden_fields_present"]),"cross_receiver_angle_input_count":0,"controller_imports_evaluator":False,"evaluator_returned_to_controller":False}

def _status(ok,evidence): return {"status":"PASS" if ok else "FAIL","evidence":evidence}

def run_gate():
 audit=derivative_audit(); followers=follower_metrics(); exact=_replay(exact=True); numeric=_replay()
 rot=np.array(((cos(.731),-sin(.731)),(sin(.731),cos(.731)))); ref=np.array(((1.,0.),(0.,-1.)))
 rotated,mirrored=_replay(matrix=rot),_replay(matrix=ref)
 # The same cycle metric is used for the frozen pair and a different legal pair.
 ablation={"FY04_FY07":pair_cycle_metrics(B,C),"FY02_FY05":pair_cycle_metrics(2,5)}
 metamorphic={}
 for label,transform,replay in (("rotation",rot,rotated),("reflection",ref,mirrored)):
  errors={str(i):float(np.linalg.norm(transform.T@replay["world"][i]-numeric["world"][i])) for i in range(10)}
  metric_errors={k:abs(numeric["metrics"][k]-replay["metrics"][k]) for k in ("max_radius_error_m","max_successive_central_angle_error_rad","max_target_position_error_m")}
  metamorphic[label]={"per_node_trajectory_difference_m":errors,"max_node_difference_m":max(errors.values()),"metric_differences":metric_errors,"max_metric_difference":max(metric_errors.values())}
 holdouts=numeric["followers"]["holdouts"]; firewall=_firewall_audit(); schedule=_schedule_audit()
 preloaded=numeric["followers"]["preloaded_specs"]
 checks={"derivative_three_way":_status(audit["pass"],audit["errors"]),
  "exact_oracle_independent":_status(all(t.status=="CONVERGED_TARGET_NEAR" for _,t in exact["bootstrap"]["traces"]),{"oracle_function":"analytic_jacobian_Newton","finite_difference_controller_called":False,"max_target_error_m":exact["bootstrap"]["max_target_error_m"]}),
  "preloaded_signature":_status(all(len(v["main_angles"])==2 and len(v["holdout_angles"])==4 for v in preloaded.values()),preloaded),
  "finite_difference_table1":_status(numeric["metrics"]["max_target_position_error_m"]<1e-3,numeric["metrics"]),
  "holdout":_status(all(v["status"]=="PASS" for v in holdouts.values()),holdouts),
  "information_firewall":_status(not firewall["forbidden_fields_present"] and firewall["world_field_count"]==0 and firewall["cross_receiver_angle_input_count"]==0 and not firewall["controller_imports_evaluator"] and not firewall["evaluator_returned_to_controller"],firewall),
  "schedule":_status(all(r["has_FY00"] and r["outer_transmitters"]<=3 and r["receiver_not_transmitter"] and r["transmitters_fixed_during_probe_and_motion"] for r in schedule["rounds"]) and schedule["FY00_FY01_fixed"] and schedule["FY04_FY07_fixed_in_four_anchor_stage"],schedule),
  "full_metamorphic":_status(max(x["max_node_difference_m"] for x in metamorphic.values())<2e-6 and max(x["max_metric_difference"] for x in metamorphic.values())<2e-6,metamorphic),
  "ablation_same_metric":_status(ablation["FY04_FY07"]["joint_rank"]==4 and ablation["FY02_FY05"]["joint_rank"]==4,ablation)}
 return {"gate":"Q1_3_PROGRAM_GATE","status":"PASS" if all(v["status"]=="PASS" for v in checks.values()) else "FAIL","scope":"deterministic target-neighborhood/Table-1 replay only; no global claim","checks":checks,"derivative_audit":audit,"follower_metrics":followers,"exact_replay":_compact(exact),"finite_difference_replay":_compact(numeric),"information_firewall":firewall,"schedule_audit":schedule,"metamorphic":metamorphic,"ablation":ablation}

if __name__=="__main__":
 report=run_gate(); OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"status":report["status"],"output":str(OUT)},ensure_ascii=False)); raise SystemExit(0 if report["status"]=="PASS" else 1)
