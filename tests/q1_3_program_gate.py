"""Deterministic Q1(3) remediation Gate; no batch or Q2 work."""
from __future__ import annotations
import ast, inspect, json
from pathlib import Path
from math import cos, sin
import numpy as np
import src.q1_3_adjustment as adjustment
from src.q1_3_adjustment import (
 A,B,C,O,ANCHORS,ControllerSettings,LocalControllerInput,ObservationPlant,
 bc_spec,controller_firewall_schema,derivative_audit,exact_local_best_response,
 finite_difference_controller,follower_metrics,pair_cycle_metrics,preloaded_follower_spec,
 table1_coordinates,target_coordinates,transform_positions,pair_angle)
from src.q1_3_evaluator import evaluate_regular_nonagon,holdout_report

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"results"/"q1_3"/"q1_3_program_gate.json"
SETTINGS=ControllerSettings()

def _input(receiver,spec,step): return LocalControllerInput(receiver,tuple(spec["main_angles"]),step)
def _run_action(world,receiver,spec,step,axes,exact=False):
 before={str(i):world[i].round(12).tolist() for i in world}
 plant=ObservationPlant(world,receiver,spec["main_pairs"],spec["main_angles"],axes)
 local=_input(receiver,spec,step)
 trace=exact_local_best_response(local,plant.observe,plant.analytic_jacobian) if exact else finite_difference_controller(local,plant.observe,settings=SETTINGS)
 plant.apply(trace.local_displacement)
 after={str(i):world[i].round(12).tolist() for i in world}
 scheduled_tx=ANCHORS if step=="FOUR_ANCHOR" else sorted(set(sum((list(p) for p in spec["main_pairs"]),[])))
 trace.audit_event={"step":step,"receiver":receiver,"transmitters":scheduled_tx,
                    "before":before,"after":after,"observation_events":plant.observation_events,
                    "exact":exact}
 return trace

def _bootstrap(world,axes,exact=False):
 traces=[]
 for cycle in range(5):
  for receiver,step in ((B,"BC_B"),(C,"BC_C")):
   trace=_run_action(world,receiver,bc_spec(receiver),"{}:{}".format(step,cycle),axes,exact)
   traces.append((str(receiver),trace))
 return {"traces":traces,"events":[t.audit_event for _,t in traces],"max_target_error_m":max(float(np.linalg.norm(world[i]-target_coordinates()[i])) for i in (B,C))}

def _followers(world,axes,ideal):
 specs={i:preloaded_follower_spec(i,target=ideal) for i in (2,3,5,6,8,9)}
 traces={str(i):_run_action(world,i,specs[i],"FOUR_ANCHOR",axes) for i in specs}
 holdouts={str(i):holdout_report(world,i,specs[i]) for i in specs}
 return {"traces":traces,"events":[t.audit_event for t in traces.values()],"holdouts":holdouts,"max_target_error_m":max(float(np.linalg.norm(world[i]-ideal[i])) for i in specs),"preloaded_specs":{str(i):{"main_angles":specs[i]["main_angles"],"holdout_angles":specs[i]["holdout_angles"]} for i in specs}}

def _replay(exact=False,matrix=None):
 matrix=np.eye(2) if matrix is None else matrix; world=transform_positions(table1_coordinates(),matrix); ideal=transform_positions(target_coordinates(),matrix)
 boot=_bootstrap(world,matrix,exact); followers=_followers(world,matrix,ideal)
 base={i:matrix.T@world[i] for i in world}
 return {"world":world,"base_world":base,"bootstrap":boot,"followers":followers,"events":boot["events"]+followers["events"],"metrics":evaluate_regular_nonagon(base)}

def _compact_trace(trace):
 return {"status":trace.status,"final_residual_norm":trace.residual_norms[-1],"probes":trace.probes,"backtracks":trace.backtracks,"local_displacement_m":trace.local_displacement.tolist()}
def _compact(replay):
 return {"bootstrap":{"max_target_error_m":replay["bootstrap"]["max_target_error_m"],"traces":[{"receiver":n,**_compact_trace(t)} for n,t in replay["bootstrap"]["traces"]]},
         "followers":{"max_target_error_m":replay["followers"]["max_target_error_m"],"traces":{n:_compact_trace(t) for n,t in replay["followers"]["traces"].items()},"holdouts":replay["followers"]["holdouts"],"preloaded_specs":replay["followers"]["preloaded_specs"]},"metrics":replay["metrics"]}

def _schedule_audit(events):
 records=[]
 for event in events:
  tx=set(event["transmitters"]); receiver=event["receiver"]; before=event["before"]; after=event["after"]
  unchanged={key:before[key]==after[key] for key in before if int(key)!=receiver}
  records.append({"step":event["step"],"receiver":receiver,"transmitters":sorted(tx),"has_FY00":O in tx,
   "outer_transmitter_count":len(tx-{O}),"receiver_not_transmitter":receiver not in tx,
   "transmitters_unchanged":all(unchanged[str(i)] for i in tx),"only_receiver_changed":all(unchanged.values()),
   "observation_receivers":sorted(set(x["receiver"] for x in event["observation_events"])),
   "observation_dimensions":sorted(set(x["dimension"] for x in event["observation_events"]))})
 initial=events[0]["before"]; final=events[-1]["after"]
 bad_event={**events[0],"transmitters":[A,C]}
 negative_illegal_event_detected=(O not in bad_event["transmitters"]) or (bad_event["receiver"] in bad_event["transmitters"])
 return {"actual_events":records,"FY00_fixed":initial["0"]==final["0"],"FY01_fixed":initial["1"]==final["1"],
  "FY04_FY07_fixed_in_four_anchor_stage":all(r["transmitters"]==[0,1,4,7] and r["receiver"] not in {4,7} for r in records if r["step"]=="FOUR_ANCHOR"),
  "negative_illegal_event":bad_event,"negative_illegal_event_detected":negative_illegal_event_detected}

def _firewall_audit(events):
 schema=controller_firewall_schema(); source=inspect.getsource(adjustment); tree=ast.parse(source)
 imports=[node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
 fd_node=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=="finite_difference_controller")
 exact_node=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=="exact_local_best_response")
 forbidden=("world","truth","coordinates","actual_position","anchor_coordinates","table1_coordinates","target_coordinates","evaluator")
 fd_names={node.id for node in ast.walk(fd_node) if isinstance(node,ast.Name)}
 exact_names={node.id for node in ast.walk(exact_node) if isinstance(node,ast.Name)}
 illegal_inputs=[name for name in list(inspect.signature(finite_difference_controller).parameters) if any(token in name for token in forbidden)]
 event_receiver_failures=sum(1 for e in events for o in e["observation_events"] if o["receiver"]!=e["receiver"] or o["dimension"]!=2)
 fake=type("BadInput",(),{"world":1,"receiver_id":2})()
 negative_detected=any(hasattr(fake,name) for name in forbidden)
 return {**schema,"controller_parameters":list(inspect.signature(finite_difference_controller).parameters),
  "q1_3_evaluator_imports":sum(1 for i in imports if i=="src.q1_3_evaluator"),"fd_forbidden_name_references":sorted(fd_names & set(forbidden)),
  "exact_forbidden_name_references":sorted(exact_names & set(forbidden)),"fd_calls_exact_or_evaluator":sum(1 for n in ast.walk(fd_node) if isinstance(n,ast.Call) and getattr(n.func,"id","") in {"exact_local_best_response","evaluate_regular_nonagon"}),
  "event_receiver_failures":event_receiver_failures,"negative_illegal_field_detected":negative_detected,"illegal_inputs":illegal_inputs}

def _status(ok,evidence): return {"status":"PASS" if ok else "FAIL","evidence":evidence}

def run_gate():
 audit=derivative_audit(); followers=follower_metrics()
 original_fd=adjustment.finite_difference_controller; fd_call_count={"count":0}
 def forbidden_fd(*args,**kwargs): fd_call_count["count"]+=1; raise AssertionError("exact oracle called finite_difference_controller")
 adjustment.finite_difference_controller=forbidden_fd
 try: exact=_replay(exact=True)
 finally: adjustment.finite_difference_controller=original_fd
 numeric=_replay()
 rot=np.array(((cos(.731),-sin(.731)),(sin(.731),cos(.731)))); ref=np.array(((1.,0.),(0.,-1.)))
 rotated,mirrored=_replay(matrix=rot),_replay(matrix=ref)
 # The same cycle metric is used for the frozen pair and a different legal pair.
 ablation={"FY04_FY07":pair_cycle_metrics(B,C),"FY02_FY05":pair_cycle_metrics(2,5)}
 metamorphic={}
 for label,transform,replay in (("rotation",rot,rotated),("reflection",ref,mirrored)):
  errors={str(i):float(np.linalg.norm(transform.T@replay["world"][i]-numeric["world"][i])) for i in range(10)}
  base_traces=numeric["bootstrap"]["traces"]+list(numeric["followers"]["traces"].items()); other_traces=replay["bootstrap"]["traces"]+list(replay["followers"]["traces"].items())
  trace_errors=[float(np.linalg.norm(transform.T@(transform@a.local_displacement)-b.local_displacement)) for (_,a),(_,b) in zip(other_traces,base_traces)]
  residual_errors=[abs(a.residual_norms[-1]-b.residual_norms[-1]) for (_,a),(_,b) in zip(other_traces,base_traces)]
  metric_errors={k:abs(numeric["metrics"][k]-replay["metrics"][k]) for k in ("max_radius_error_m","max_successive_central_angle_error_rad","max_target_position_error_m")}
  metamorphic[label]={"per_node_final_difference_m":errors,"max_final_node_difference_m":max(errors.values()),"local_displacement_trajectory_differences_m":trace_errors,"max_local_displacement_trajectory_difference_m":max(trace_errors),"final_residual_differences":residual_errors,"max_final_residual_difference":max(residual_errors),"metric_differences":metric_errors,"max_metric_difference":max(metric_errors.values())}
 holdouts=numeric["followers"]["holdouts"]; firewall=_firewall_audit(numeric["events"]); schedule=_schedule_audit(numeric["events"])
 preloaded=numeric["followers"]["preloaded_specs"]
 ideal=target_coordinates(); provenance={}
 perturbed=transform_positions(target_coordinates(),np.eye(2)); perturbed[B]+=np.array((.3,-.2)); perturbed[C]+=np.array((-.1,.4))
 for receiver in (2,3,5,6,8,9):
  spec=preloaded_follower_spec(receiver); independent=preloaded_follower_spec(receiver,target=ideal); changed=preloaded_follower_spec(receiver,target=ideal)
  main_diff=float(np.max(abs(np.array(spec["main_angles"])-np.array(independent["main_angles"]))))
  holdout_diff=float(np.max(abs(np.array(spec["holdout_angles"])-np.array(independent["holdout_angles"]))))
  anchor_change=float(max(np.max(abs(np.array(spec["main_angles"])-np.array(changed["main_angles"]))),np.max(abs(np.array(spec["holdout_angles"])-np.array(changed["holdout_angles"])))))
  actual_before=np.array([pair_angle(ideal[receiver],ideal,p)-a for p,a in zip(spec["main_pairs"],spec["main_angles"])])
  actual_after=np.array([pair_angle(ideal[receiver],perturbed,p)-a for p,a in zip(spec["main_pairs"],spec["main_angles"])])
  provenance[str(receiver)]={"main_max_difference":main_diff,"holdout_max_difference":holdout_diff,"anchor_perturbation_preloaded_change":anchor_change,
   "plant_anchor_perturbation_actual_residual_change":float(np.max(abs(actual_after-actual_before)))}
 checks={"derivative_three_way":_status(audit["pass"],audit["errors"]),
  "exact_oracle_independent":_status(all(t.status=="CONVERGED_TARGET_NEAR" for _,t in exact["bootstrap"]["traces"]) and fd_call_count["count"]==0 and exact["bootstrap"]["max_target_error_m"]<1e-6,{"oracle_function":"analytic_jacobian_Newton","monkeypatch_fd_call_count":fd_call_count["count"],"max_target_error_m":exact["bootstrap"]["max_target_error_m"],"target_error_threshold_m":1e-6}),
  "preloaded_signature":_status(all(x["main_max_difference"]<=1e-12 and x["holdout_max_difference"]<=1e-12 and x["anchor_perturbation_preloaded_change"]<=1e-12 and x["plant_anchor_perturbation_actual_residual_change"]>1e-8 for x in provenance.values()),{"signature_threshold":1e-12,"plant_change_lower_bound":1e-8,"per_receiver":provenance}),
  "finite_difference_table1":_status(numeric["metrics"]["max_target_position_error_m"]<1e-3,numeric["metrics"]),
  "holdout":_status(all(v["status"]=="PASS" for v in holdouts.values()),holdouts),
  "information_firewall":_status(not firewall["forbidden_fields_present"] and not firewall["illegal_inputs"] and firewall["q1_3_evaluator_imports"]==0 and not firewall["fd_forbidden_name_references"] and not firewall["exact_forbidden_name_references"] and firewall["event_receiver_failures"]==0 and firewall["negative_illegal_field_detected"],firewall),
  "schedule":_status(all(r["has_FY00"] and r["outer_transmitter_count"]<=3 and r["receiver_not_transmitter"] and r["transmitters_unchanged"] and r["only_receiver_changed"] and r["observation_receivers"]==[r["receiver"]] and r["observation_dimensions"]==[2] for r in schedule["actual_events"]) and schedule["FY00_fixed"] and schedule["FY01_fixed"] and schedule["FY04_FY07_fixed_in_four_anchor_stage"] and schedule["negative_illegal_event_detected"],schedule),
  "full_metamorphic":_status(max(x["max_final_node_difference_m"] for x in metamorphic.values())<2e-6 and max(x["max_local_displacement_trajectory_difference_m"] for x in metamorphic.values())<2e-6 and max(x["max_final_residual_difference"] for x in metamorphic.values())<2e-8 and max(x["max_metric_difference"] for x in metamorphic.values())<2e-6,metamorphic),
  "ablation_same_metric":_status(set(ablation["FY04_FY07"])==set(ablation["FY02_FY05"]) and ablation["FY04_FY07"]["joint_rank"]==4 and ablation["FY02_FY05"]["joint_rank"]==4 and ablation["FY04_FY07"]["spectral_radius"]<1e-10 and ablation["FY04_FY07"]["spectral_radius"]<ablation["FY02_FY05"]["spectral_radius"] and all(np.isfinite(v) and v>0 for x in ablation.values() for k,v in x.items() if k in {"joint_condition","joint_sigma_min"}),ablation)}
 return {"gate":"Q1_3_PROGRAM_GATE","status":"PASS" if all(v["status"]=="PASS" for v in checks.values()) else "FAIL","scope":"deterministic target-neighborhood/Table-1 replay only; no global claim","checks":checks,"derivative_audit":audit,"follower_metrics":followers,"exact_replay":_compact(exact),"finite_difference_replay":_compact(numeric),"information_firewall":firewall,"schedule_audit":schedule,"metamorphic":metamorphic,"ablation":ablation,"preloaded_signature_provenance":provenance}

if __name__=="__main__":
 report=run_gate(); OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"status":report["status"],"output":str(OUT)},ensure_ascii=False)); raise SystemExit(0 if report["status"]=="PASS" else 1)
