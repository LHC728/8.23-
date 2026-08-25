"""Q2 正式确定性 Program Gate；每一项 PASS 均保留数值证据与故障注入。"""
from __future__ import annotations

import ast, inspect, json
from itertools import combinations, product
from math import cos, pi, sin, sqrt
from pathlib import Path

import numpy as np

from src.q2_adjustment import LocalControllerInput, finite_difference_controller
from src.q2_evaluator import evaluate_formation
from src.q2_geometry import FOUR_PAIRS, FOUR_REFERENCE_IDS, angle_gradient_receiver, angle_gradient_transmitter, angle_jacobian, circle_intersections, complete_four_reference_candidates, four_angles, independent_multistart_roots, raw_angle, target_lattice

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'results'/'q2'/'q2_program_gate.json'
SEEDS=(11,15); BOOT=(4,3); REFERENCES=(3,4,11,15)
FORBIDDEN_FIELD_FRAGMENTS=('world','truth','coordinate','distance','anchor','evaluator','other_receiver','cross_receiver','future')
# 这些阈值在正式完整回放运行前冻结。建锚终止精度继承既有有限试探
# Gate；端到端节点阈值保守取其十倍，以容纳两次建锚和本机控制的误差传播。
BOOTSTRAP_FINITE_POSITION_TOL=2e-7
END_TO_END_NODE_TOL=10*BOOTSTRAP_FINITE_POSITION_TOL
END_TO_END_EDGE_TOL=2*END_TO_END_NODE_TOL
END_TO_END_COLLINEARITY_TOL=END_TO_END_NODE_TOL
END_TO_END_MAIN_RESIDUAL_TOL=2e-6
END_TO_END_HOLDOUT_TOL=2e-6
# This is an internal action-termination tolerance, deliberately much tighter
# than the frozen acceptance limits above.  It prevents a follower from
# stopping after merely entering the acceptance band while the finite
# bootstrap-terminal perturbation still consumes the formation-error budget.
END_TO_END_ACTION_RESIDUAL_TOL=2e-10
END_TO_END_MAX_BOOTSTRAP_CYCLES=20
END_TO_END_MAX_FOLLOWER_STEPS=50

def _status(ok: bool, **evidence: object) -> dict[str,object]: return {'status':'PASS' if ok else 'FAIL','evidence':evidence}
def _three(point, anchors): return np.array([raw_angle(point,anchors[i],anchors[j]) for i,j in ((0,1),(0,2),(1,2))])
def _three_jac(point,anchors,indices): return np.vstack([angle_gradient_receiver(point,anchors[i],anchors[j]) for i,j in (((0,1),(0,2),(1,2))[k] for k in indices)])

def _exact_response(receiver:int, other:int, other_point:np.ndarray, lattice:dict[int,np.ndarray])->np.ndarray:
    anchors=np.vstack([lattice[11],lattice[15],other_point]); ideal=np.vstack([lattice[11],lattice[15],lattice[other]])
    primary=(0,2) if receiver==4 else (0,1); target=_three(lattice[receiver],ideal)[list(primary)]; point=lattice[receiver].copy()
    for _ in range(30):
        residual=_three(point,anchors)[list(primary)]-target
        if float(np.max(abs(residual)))<2e-11: return point
        jac=_three_jac(point,anchors,primary); action=-np.linalg.solve(jac,residual)
        norm=float(np.linalg.norm(action))
        if norm>.30: action*=.30/norm
        base=float(np.linalg.norm(residual)); accepted=False
        for factor in (1.,.5,.25,.125,.0625):
            trial=point+factor*action
            try: trial_norm=float(np.linalg.norm(_three(trial,anchors)[list(primary)]-target))
            except ValueError: continue
            if trial_norm<base:
                point=trial; accepted=True; break
        if not accepted: raise RuntimeError('exact local response backtracking failed')
    raise RuntimeError('exact local response did not converge')

def _record_event(event_log: dict[str,object] | None, receiver: int, values: np.ndarray) -> None:
    """只保存每个接收机的最小实际调用轨迹与计数，不把真值传给控制器。"""
    if event_log is None: return
    counts=event_log.setdefault('counts',{}); samples=event_log.setdefault('samples',{})
    observed=np.asarray(values); dimension=int(observed.size)
    counts[str(receiver)]=int(counts.get(str(receiver),0))+1
    samples.setdefault(str(receiver),{'receiver_id':receiver,'observation_receiver_id':receiver,'observation_dimension':dimension,'observation_shape':list(observed.shape),'other_receiver_angles_present':bool(observed.ndim!=1 or dimension!=2)})


def _fd_step(receiver:int, other:int, point:np.ndarray, other_point:np.ndarray, lattice:dict[int,np.ndarray], event_log: dict[str,object] | None=None)->np.ndarray:
    anchors=np.vstack([lattice[11],lattice[15],other_point]); ideal=np.vstack([lattice[11],lattice[15],lattice[other]])
    primary=(0,2) if receiver==4 else (0,1); target=tuple(_three(lattice[receiver],ideal)[list(primary)])
    def observe(offset):
        values=_three(point+offset,anchors)[list(primary)]; _record_event(event_log,receiver,values); return values
    trace=finite_difference_controller(LocalControllerInput(receiver,(11,15,other),target,0),observe,max_step=.25)
    return point+trace.action

def _bootstrap_checks(lattice, event_log=None):
    # 解析 Jacobian 与独立中心差分；B 块以另一待建锚节点为变量。
    records={}; responses=[]; blocks=[]
    for receiver,other in ((4,3),(3,4)):
        anchors=np.vstack([lattice[11],lattice[15],lattice[other]]); primary=(0,2) if receiver==4 else (0,1)
        j=_three_jac(lattice[receiver],anchors,primary); b=np.empty((2,2)); b_analytic=np.empty((2,2)); step=1e-6
        pair_table=((0,1),(0,2),(1,2))
        for row,k in enumerate(primary):
            left,right=pair_table[k]
            b_analytic[row]=angle_gradient_transmitter(lattice[receiver],anchors[left],anchors[right],moving='left' if left==2 else 'right') if 2 in (left,right) else np.zeros(2)
        for axis in range(2):
            plus=anchors.copy(); minus=anchors.copy(); plus[2,axis]+=step; minus[2,axis]-=step
            b[:,axis]=(_three(lattice[receiver],plus)[list(primary)]-_three(lattice[receiver],minus)[list(primary)])/(2*step)
        # independently approximate the full receiver block
        jfd=np.empty((2,2))
        for axis in range(2):
            offset=np.zeros(2); offset[axis]=step
            jfd[:,axis]=(_three(lattice[receiver]+offset,anchors)[list(primary)]-_three(lattice[receiver]-offset,anchors)[list(primary)])/(2*step)
        response=-np.linalg.solve(j,b_analytic); responses.append(response); blocks.append((j,b_analytic))
        records[str(receiver)]={'primary_indices':list(primary),'self_jacobian':j.tolist(),'other_jacobian_analytic':b_analytic.tolist(),'other_jacobian_fd':b.tolist(),'self_analytic_fd_max_abs_difference':float(np.max(abs(j-jfd))),'other_analytic_fd_max_abs_difference':float(np.max(abs(b_analytic-b))),'self_sigma_min':float(np.linalg.svd(j,compute_uv=False)[-1])}
    f,g=responses; reduced=g@f; full=np.block([[reduced,np.zeros((2,2))],[f,np.zeros((2,2))]])
    determinant=float(np.linalg.det(np.block([[blocks[0][0],blocks[0][1]],[blocks[1][1],blocks[1][0]]])))
    analytic=_status(max(max(v['self_analytic_fd_max_abs_difference'],v['other_analytic_fd_max_abs_difference']) for v in records.values())<2e-6 and np.max(abs(reduced))<2e-8 and abs(determinant-1/117)<2e-8,records=records,reduced_period_jacobian=reduced.tolist(),spectral_radius=float(max(abs(np.linalg.eigvals(full)))),joint_determinant=determinant,expected_joint_determinant=1/117,threshold=2e-6)
    # 720 exact and 256 finite deterministic replays.
    exact=[]; finite=[]; phases12=[2*pi*k/12 for k in range(12)]; phases8=[2*pi*k/8 for k in range(8)]
    for radius,a,b in product((.01,.05,.10,.20,.30),phases12,phases12):
        d=lattice[3]+radius*np.array([cos(a),sin(a)]); c=lattice[4]+radius*np.array([cos(b),sin(b)])
        for cycle in range(16):
            c=_exact_response(4,3,d,lattice); d=_exact_response(3,4,c,lattice)
            if max(np.linalg.norm(c-lattice[4]),np.linalg.norm(d-lattice[3]))<2e-8: break
        exact.append((cycle+1,max(np.linalg.norm(c-lattice[4]),np.linalg.norm(d-lattice[3]))))
    for radius,a,b in product((.02,.05,.10,.20),phases8,phases8):
        d=lattice[3]+radius*np.array([cos(a),sin(a)]); c=lattice[4]+radius*np.array([cos(b),sin(b)])
        for cycle in range(20):
            c=_fd_step(4,3,c,d,lattice,event_log); d=_fd_step(3,4,d,c,lattice,event_log)
            if max(np.linalg.norm(c-lattice[4]),np.linalg.norm(d-lattice[3]))<2e-7: break
        finite.append((cycle+1,max(np.linalg.norm(c-lattice[4]),np.linalg.norm(d-lattice[3]))))
    return analytic,_status(all(x[1]<2e-8 for x in exact),case_count=len(exact),worst_cycles=max(x[0] for x in exact),worst_error=max(x[1] for x in exact),threshold=2e-8),_status(all(x[1]<2e-7 for x in finite),case_count=len(finite),worst_cycles=max(x[0] for x in finite),worst_error=max(x[1] for x in finite),threshold=2e-7)

def _follower_checks(lattice, event_log=None):
    anchors=np.vstack([lattice[i] for i in REFERENCES]); summaries=[]; certified=[]; stress=[]
    for receiver in sorted(set(lattice)-set(REFERENCES)):
        observed=four_angles(lattice[receiver],anchors); active=tuple(k for k,v in enumerate(observed) if 1e-7<v<pi-1e-7)
        pairs=list(combinations(active,2)); best=max(pairs,key=lambda pair:float(np.linalg.svd(angle_jacobian(lattice[receiver],anchors,pair),compute_uv=False)[-1])); target=tuple(observed[list(best)])
        for radius,theta in product((.02,.05,.10,.20,.30,.40),[2*pi*k/16 for k in range(16)]):
            point=lattice[receiver]+radius*np.array([cos(theta+.173*receiver),sin(theta+.173*receiver)])
            for _ in range(50):
                def observe(offset):
                    values=four_angles(point+offset,anchors)[list(best)]; _record_event(event_log,receiver,values); return values
                trace=finite_difference_controller(LocalControllerInput(receiver,REFERENCES,target,1),observe,max_step=.25)
                point+=trace.action
                if np.linalg.norm(point-lattice[receiver])<2e-8: break
            holdout=tuple(k for k in active if k not in best)
            holdout_error=float(np.max(abs(four_angles(point,anchors)[list(holdout)]-observed[list(holdout)]))) if holdout else 0.0
            entry={'radius_d':radius,'error':float(np.linalg.norm(point-lattice[receiver])),'holdout_residual_inf':holdout_error,'receiver':receiver}
            (certified if radius<=.20 else stress).append(entry)
        summaries.append({'receiver':receiver,'active_indices':list(active),'primary_indices':list(best),'sigma_min':float(np.linalg.svd(angle_jacobian(lattice[receiver],anchors,best),compute_uv=False)[-1])})
    holdout_threshold=5e-8
    return _status(all(x['error']<2e-8 and x['holdout_residual_inf']<holdout_threshold for x in certified),case_count=len(certified)+len(stress),certified_case_count=len(certified),certified_radius=.20,worst_certified_error=max(x['error'] for x in certified),worst_certified_holdout_residual=max(x['holdout_residual_inf'] for x in certified),holdout_threshold=holdout_threshold,stress_failure_count=sum(x['error']>=2e-8 for x in stress),receivers=summaries,threshold=2e-8)

def _candidate_checks(lattice):
    anchors=np.vstack([lattice[i] for i in REFERENCES]); records=[]; independent_ok=True
    for receiver in sorted(set(lattice)-set(REFERENCES)):
        obs=four_angles(lattice[receiver],anchors); production=complete_four_reference_candidates(anchors,obs); independent=independent_multistart_roots(anchors,obs)
        match=len(production['roots'])==len(independent) and all(any(np.linalg.norm(a-b)<2e-5 for b in independent) for a in production['roots'])
        records.append({'receiver':receiver,'production_root_count':len(production['roots']),'independent_root_count':len(independent),'root_sets_match':match,'status':production['status']}); independent_ok &= match and len(production['roots'])==1
    old=np.vstack([lattice[i] for i in (2,6,8,14)]); old_roots=complete_four_reference_candidates(old,four_angles(lattice[11],old))
    boundary=complete_four_reference_candidates(anchors,np.zeros(6)); collision=False
    try: complete_four_reference_candidates(np.vstack([anchors[0],anchors[0],anchors[2],anchors[3]]),four_angles(lattice[1],anchors))
    except ValueError: collision=True
    return _status(all(x['production_root_count']==1 for x in records),records=records),_status(independent_ok,records=records),_status(len(old_roots['roots'])==2,old_reference_ids=[2,6,8,14],receiver=11,actual_root_count=len(old_roots['roots']),required_root_count=2),_status(len(boundary['boundary_indices'])==6 and collision,boundary_indices=boundary['boundary_indices'],collision_rejected=collision)

def _audit_controller_api(source: str, function_name: str='finite_difference_controller') -> dict[str,object]:
    """对实际模块或故障注入伪源码执行同一 AST/API 审计。"""
    tree=ast.parse(source); function=next((n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==function_name),None)
    if function is None: return {'accepted':False,'reason':'controller_function_missing','forbidden_parameters':['missing']}
    parameters=[a.arg for a in (*function.args.posonlyargs,*function.args.args,*function.args.kwonlyargs)]
    names=sorted({n.id for n in ast.walk(function) if isinstance(n,ast.Name)})
    attributes=sorted({n.attr for n in ast.walk(function) if isinstance(n,ast.Attribute)})
    imports=[n.names[0].name for n in ast.walk(tree) if isinstance(n,ast.Import) for _ in n.names]+[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    forbidden_parameters=[x for x in parameters if any(k in x.lower() for k in FORBIDDEN_FIELD_FRAGMENTS)]
    forbidden_names=sorted({x for x in names+attributes if any(k in x.lower() for k in FORBIDDEN_FIELD_FRAGMENTS)})
    evaluator_imports=[x for x in imports if 'q2_evaluator' in x]
    allowed_signature={'local_input','observe_offset','probe','gain','damping','max_step'}
    return {'accepted':set(parameters)==allowed_signature and not forbidden_parameters and not forbidden_names and not evaluator_imports,'parameters':parameters,'forbidden_parameters':forbidden_parameters,'forbidden_names':forbidden_names,'evaluator_imports':evaluator_imports,'observe_offset_call_count':sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='observe_offset' for n in ast.walk(function))}


def _end_to_end_geometry_pass(metrics: dict[str, float|int], *, node_error: float) -> dict[str, object]:
    """实际终态几何判据；边长阈值由节点误差三角不等式导出。"""
    return _status(
        node_error <= END_TO_END_NODE_TOL
        and metrics['edge_max_abs_error_from_d'] <= END_TO_END_EDGE_TOL
        and metrics['maximum_line_distance'] <= END_TO_END_COLLINEARITY_TOL,
        node_error=node_error,
        node_error_threshold=END_TO_END_NODE_TOL,
        edge_error=metrics['edge_max_abs_error_from_d'],
        edge_error_threshold=END_TO_END_EDGE_TOL,
        edge_threshold_source='| ||p_i-p_j||-d* | <= ||p_i-q_i|| + ||p_j-q_j|| <= 2*node_error_threshold',
        edge_relative_std=metrics['edge_relative_std'],
        collinearity_error=metrics['maximum_line_distance'],
        collinearity_threshold=END_TO_END_COLLINEARITY_TOL,
        collinearity_threshold_source='ideal line distance is bounded conservatively by maximum node position error',
    )


def _deterministic_full_formation_initial_state(lattice, radius: float, direction_index: int) -> dict[int, np.ndarray]:
    """构造 15 机离线真值初态；13 架移动机均按编号错开方向非零扰动。"""
    points={node:np.asarray(point,dtype=float).copy() for node,point in lattice.items()}
    for node in sorted(set(lattice)-set(SEEDS)):
        angle=2*pi*direction_index/8 + .173*node
        points[node]=points[node]+radius*np.array([cos(angle),sin(angle)])
    return points


def _run_actual_bootstrap(points: dict[int,np.ndarray], lattice: dict[int,np.ndarray], event_log=None) -> dict[str,object]:
    """固定宏周期的 FY04/FY03 本机建锚；真值仅在排程结束后离线验收。"""
    world={node:np.asarray(point,dtype=float).copy() for node,point in points.items()}
    traces=[]
    for cycle in range(END_TO_END_MAX_BOOTSTRAP_CYCLES):
        before4=world[4].copy(); world[4]=_fd_step(4,3,world[4],world[3],lattice,event_log)
        before3=world[3].copy(); world[3]=_fd_step(3,4,world[3],world[4],lattice,event_log)
        traces.append({'cycle':cycle+1,'FY04_displacement':float(np.linalg.norm(world[4]-before4)),'FY03_displacement':float(np.linalg.norm(world[3]-before3))})
    # 固定排程结束后，离线评估器才可读取仿真真值并计算终点误差。
    errors={str(node):float(np.linalg.norm(world[node]-lattice[node])) for node in BOOT}
    return {'world':world,'cycles':len(traces),'fixed_bootstrap_cycles':END_TO_END_MAX_BOOTSTRAP_CYCLES,'terminal_errors':errors,'max_terminal_error':max(errors.values()),'terminal_error_threshold':BOOTSTRAP_FINITE_POSITION_TOL,'pass':max(errors.values())<=BOOTSTRAP_FINITE_POSITION_TOL,'traces':traces}


def _fixed_bootstrap_schedule_audit() -> dict[str, object]:
    """机械审计：实际端到端建锚不得用真值或跨机残差提前结束排程。"""
    source=inspect.getsource(_run_actual_bootstrap)
    tree=ast.parse(source)
    function=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='_run_actual_bootstrap')
    breaks=[node for node in ast.walk(function) if isinstance(node,ast.Break)]
    loops=[node for node in ast.walk(function) if isinstance(node,ast.For)]
    fixed_range=bool(len(loops)==1 and isinstance(loops[0].iter,ast.Call) and isinstance(loops[0].iter.func,ast.Name) and loops[0].iter.func.id=='range' and len(loops[0].iter.args)==1 and isinstance(loops[0].iter.args[0],ast.Name) and loops[0].iter.args[0].id=='END_TO_END_MAX_BOOTSTRAP_CYCLES')
    # 当且仅当无 break 时，离线真值终点误差不可能控制在线阶段切换。
    truth_based_stage_switch_found=bool(breaks)
    cross_receiver_residual_aggregation_found=any(isinstance(node,ast.Name) and ('residual' in node.id.lower() and node.id not in {'residual'}) for node in ast.walk(function))
    return _status(fixed_range and not truth_based_stage_switch_found and not cross_receiver_residual_aggregation_found,fixed_bootstrap_cycles=END_TO_END_MAX_BOOTSTRAP_CYCLES,for_loop_count=len(loops),break_count=len(breaks),truth_based_stage_switch_found=truth_based_stage_switch_found,cross_receiver_residual_aggregation_found=cross_receiver_residual_aggregation_found,offline_terminal_evaluation_after_schedule=True)


def _audit_follower_anchor_source(anchors: np.ndarray, bootstrap: dict[str,object], lattice: dict[int,np.ndarray], declared_source: str) -> dict[str,object]:
    """比较实际传入的四锚数组与建锚终点，非一致来源必须被机械标记。"""
    world=bootstrap['world']
    expected=np.vstack([world[3],world[4],world[11],world[15]])
    arrays_match=bool(np.array_equal(anchors,expected))
    audit={'follower_anchor_source':declared_source,'actual_reference_ids':list(REFERENCES),'actual_anchor_arrays':anchors.tolist(),'bootstrap_terminal_arrays':expected.tolist(),'arrays_match_bootstrap_terminal':arrays_match,'fy03_fy04_nonideal_difference':max(float(np.linalg.norm(world[node]-lattice[node])) for node in BOOT)}
    audit['status']='PASS' if declared_source=='BOOTSTRAP_TERMINAL_STATE' and arrays_match else 'ANCHOR_SOURCE_VIOLATION'
    return audit


def _actual_reference_terminals(bootstrap: dict[str,object], lattice: dict[int,np.ndarray]) -> tuple[np.ndarray,dict[str,object]]:
    """只从实际建锚终点取 FY03/FY04；审计值会暴露任何理想锚重置。"""
    world=bootstrap['world']
    anchors=np.vstack([world[node] for node in REFERENCES])
    audit=_audit_follower_anchor_source(anchors,bootstrap,lattice,'BOOTSTRAP_TERMINAL_STATE')
    return anchors,audit


def _run_actual_followers(initial: dict[int,np.ndarray], bootstrap: dict[str,object], lattice: dict[int,np.ndarray], event_log=None) -> dict[str,object]:
    """11 架跟随者从实际初态出发，只对实际四参考机作本机观测。"""
    anchors,audit=_actual_reference_terminals(bootstrap,lattice)
    ideal_anchors=np.vstack([lattice[node] for node in REFERENCES])
    final={node:np.asarray(point,dtype=float).copy() for node,point in bootstrap['world'].items()}
    records=[]
    for receiver in sorted(set(lattice)-set(REFERENCES)):
        ideal_observed=four_angles(lattice[receiver],ideal_anchors)
        active=tuple(index for index,value in enumerate(ideal_observed) if 1e-7<value<pi-1e-7)
        pairs=list(combinations(active,2))
        best=max(pairs,key=lambda pair:float(np.linalg.svd(angle_jacobian(lattice[receiver],ideal_anchors,pair),compute_uv=False)[-1]))
        target=tuple(ideal_observed[list(best)])
        point=initial[receiver].copy(); trace_count=0; last_trace=None
        for _ in range(END_TO_END_MAX_FOLLOWER_STEPS):
            def observe(offset):
                values=four_angles(point+offset,anchors)[list(best)]; _record_event(event_log,receiver,values); return values
            last_trace=finite_difference_controller(LocalControllerInput(receiver,REFERENCES,target,1),observe,max_step=.25)
            point=point+last_trace.action; trace_count+=1
            if last_trace.residual_after_norm <= END_TO_END_ACTION_RESIDUAL_TOL: break
        final[receiver]=point
        holdout=tuple(index for index in active if index not in best)
        main_residual=float(np.max(abs(four_angles(point,anchors)[list(best)]-ideal_observed[list(best)])))
        holdout_residual=float(np.max(abs(four_angles(point,anchors)[list(holdout)]-ideal_observed[list(holdout)]))) if holdout else 0.
        singular_values=np.linalg.svd(angle_jacobian(lattice[receiver],anchors,best),compute_uv=False)
        status='PASS' if main_residual<=END_TO_END_MAIN_RESIDUAL_TOL and holdout_residual<=END_TO_END_HOLDOUT_TOL else 'REJECTED'
        records.append({'receiver':receiver,'initial_position':initial[receiver].tolist(),'terminal_position':point.tolist(),'cycles':trace_count,'primary_indices':list(best),'main_residual_inf':main_residual,'main_residual_threshold':END_TO_END_MAIN_RESIDUAL_TOL,'holdout_residual_inf':holdout_residual,'holdout_threshold':END_TO_END_HOLDOUT_TOL,'local_rank':int(np.sum(singular_values>1e-9)),'local_sigma_min':float(singular_values[-1]),'status':status,'last_controller_accepted':None if last_trace is None else last_trace.accepted})
    return {'final':final,'records':records,'anchor_audit':audit}


def run_q2_end_to_end_case(lattice: dict[int,np.ndarray], *, radius: float, direction_index: int, case_id: str, event_log=None, seed_offset: float=0.) -> dict[str,object]:
    """实际 15 机固定排程回放；仿真世界只封装在测试/观测回调中。"""
    initial=_deterministic_full_formation_initial_state(lattice,radius,direction_index)
    if seed_offset:
        initial[11]=initial[11]+seed_offset*np.array([1.,0.])
        initial[15]=initial[15]+seed_offset*np.array([0.,1.])
    bootstrap=_run_actual_bootstrap(initial,lattice,event_log)
    followers=_run_actual_followers(initial,bootstrap,lattice,event_log)
    actual_final=followers['final']
    geometry=evaluate_formation(actual_final)
    node_errors={str(node):float(np.linalg.norm(actual_final[node]-lattice[node])) for node in lattice}
    geometry_status=_end_to_end_geometry_pass(geometry,node_error=max(node_errors.values()))
    rejected=[record['receiver'] for record in followers['records'] if record['status']!='PASS']
    terminal_nonideal=followers['anchor_audit']['fy03_fy04_nonideal_difference']>0.
    passed=bool(bootstrap['pass'] and followers['anchor_audit']['arrays_match_bootstrap_terminal'] and not rejected and geometry_status['status']=='PASS')
    return {'case_id':case_id,'radius_d':radius,'direction_rule':'2*pi*direction_index/8 + 0.173*node_id','direction_index':direction_index,'seed_offset_d':seed_offset,'bootstrap_terminal':{'FY03':actual_final[3].tolist(),'FY04':actual_final[4].tolist(),'errors':bootstrap['terminal_errors'],'max_error':bootstrap['max_terminal_error'],'threshold':bootstrap['terminal_error_threshold'],'cycles':bootstrap['cycles']},'follower_anchor_source':followers['anchor_audit']['follower_anchor_source'],'anchor_data_flow':followers['anchor_audit'],'follower_records':followers['records'],'actual_final_formation':{str(node):actual_final[node].tolist() for node in sorted(actual_final)},'geometry':geometry_status['evidence'],'max_main_residual':max(record['main_residual_inf'] for record in followers['records']),'max_holdout_residual':max(record['holdout_residual_inf'] for record in followers['records']),'slowest_follower_cycles':max(record['cycles'] for record in followers['records']),'rejected_nodes':rejected,'failed_reason':None if passed else 'bootstrap_or_anchor_data_flow_or_follower_or_geometry_threshold','nonideal_bootstrap_terminal':terminal_nonideal,'status':'PASS' if passed else 'FAIL'}


def _end_to_end_checks(lattice, event_log=None):
    cases=[run_q2_end_to_end_case(lattice,radius=0.,direction_index=0,case_id='ideal_zero',event_log=event_log)]
    cases.extend(run_q2_end_to_end_case(lattice,radius=radius,direction_index=direction,case_id=f'r{radius:.2f}_d{direction}',event_log=event_log) for radius in (.02,.05,.10,.20) for direction in range(8))
    nominal=cases[1:]
    actual_anchor_ok=all(case['follower_anchor_source']=='BOOTSTRAP_TERMINAL_STATE' and case['anchor_data_flow']['arrays_match_bootstrap_terminal'] for case in cases)
    nonideal_seen=any(case['nonideal_bootstrap_terminal'] for case in nominal)
    passed=all(case['status']=='PASS' for case in cases) and actual_anchor_ok and nonideal_seen
    compact=[]
    for case in cases:
        compact.append({key:case[key] for key in ('case_id','radius_d','direction_index','bootstrap_terminal','follower_anchor_source','anchor_data_flow','geometry','max_main_residual','max_holdout_residual','slowest_follower_cycles','rejected_nodes','failed_reason','nonideal_bootstrap_terminal','status')})
    # 负对照 1：故意把实际建锚末态替换为理想 FY03/FY04；审计器必须拒绝。
    probe=next(case for case in nominal if case['nonideal_bootstrap_terminal'])
    bootstrap_probe={'world':{3:np.asarray(probe['bootstrap_terminal']['FY03'],dtype=float),4:np.asarray(probe['bootstrap_terminal']['FY04'],dtype=float),11:np.asarray(lattice[11],dtype=float),15:np.asarray(lattice[15],dtype=float)}}
    # 以记录的实际建锚终点重建审计输入；FY03/FY04 在建锚完成后固定。
    ideal_reset_anchors=np.vstack([lattice[node] for node in REFERENCES])
    ideal_reset_audit=_audit_follower_anchor_source(ideal_reset_anchors,bootstrap_probe,lattice,'IDEAL_LATTICE_RESET')
    ideal_reset_audit['trigger_case']=probe['case_id']
    ideal_reset_negative=_status(ideal_reset_audit['status']=='ANCHOR_SOURCE_VIOLATION' and not ideal_reset_audit['arrays_match_bootstrap_terminal'],audit=ideal_reset_audit)
    # 负对照 2：对已通过实际终态副本注入明确位移，最终几何验收必须拒绝。
    valid=next(case for case in cases if case['status']=='PASS')
    altered={int(node):np.asarray(point,dtype=float).copy() for node,point in valid['actual_final_formation'].items()}; altered[1]=altered[1]+np.array([.02,-.015])
    altered_metrics=evaluate_formation(altered); altered_node=max(float(np.linalg.norm(altered[node]-lattice[node])) for node in altered)
    altered_status=_end_to_end_geometry_pass(altered_metrics,node_error=altered_node)
    geometry_negative=_status(altered_status['status']=='FAIL',actual_geometry_check=altered_status,perturbed_node=1,perturbation=[.02,-.015])
    # 可信参考误差仅作离线敏感性诊断；PASS 仅表示传播被记录。
    sensitivity=[]
    for magnitude in (.001,.01):
        diagnostic=run_q2_end_to_end_case(lattice,radius=.05,direction_index=3,case_id=f'trusted_seed_offset_{magnitude:.3f}',seed_offset=magnitude)
        sensitivity.append({'seed_offset_d':magnitude,'status':diagnostic['status'],'worst_node_error':max(diagnostic['geometry']['node_error'],diagnostic['bootstrap_terminal']['max_error']),'edge_error':diagnostic['geometry']['edge_error'],'collinearity_error':diagnostic['geometry']['collinearity_error'],'holdout_residual':diagnostic['max_holdout_residual']})
    sensitivity_status=_status(all(np.isfinite(value) for entry in sensitivity for value in (entry['worst_node_error'],entry['edge_error'],entry['collinearity_error'],entry['holdout_residual'])) and all(entry['worst_node_error']>0 for entry in sensitivity),scenarios=sensitivity,interpretation='离线诊断记录可信参考误差的传播；不构成有偏差参考下的成功保证')
    fixed_cycles=all(case['bootstrap_terminal']['cycles']==END_TO_END_MAX_BOOTSTRAP_CYCLES for case in cases)
    evidence={'fixed_bootstrap_cycles':END_TO_END_MAX_BOOTSTRAP_CYCLES,'fixed_cycles_executed_for_all_cases':fixed_cycles,'full_formation_case_count':len(cases),'nonzero_case_count':len(nominal),'radius_levels':[.02,.05,.10,.20],'directions_per_radius':8,'all_moving_nodes_perturbed':True,'actual_bootstrap_terminal_used':actual_anchor_ok,'nonideal_bootstrap_terminal_seen':nonideal_seen,'cases':compact}
    return _status(passed and fixed_cycles,**evidence),ideal_reset_negative,geometry_negative,sensitivity_status


def _firewall_and_metamorphic(lattice,event_log):
    module_source=(ROOT/'src'/'q2_adjustment.py').read_text(encoding='utf-8'); production=_audit_controller_api(module_source)
    truth_source='def finite_difference_controller(local_input, observe_offset, *, truth_coordinates=None, probe=1, gain=1, damping=1, max_step=1):\n return observe_offset([0,0])\n'
    cross_source='def finite_difference_controller(local_input, observe_offset, *, other_receiver_angles=None, probe=1, gain=1, damping=1, max_step=1):\n return observe_offset([0,0])\n'
    truth_audit=_audit_controller_api(truth_source); cross_audit=_audit_controller_api(cross_source)
    rejected_fields=[]
    for field in ('truth_coordinates','world_coordinates','other_receiver_angles','cross_receiver_angles'):
        try: LocalControllerInput(1,(3,4,11,15),(1.,2.),0,**{field:[]})
        except TypeError: rejected_fields.append(field)
    samples=list(event_log.get('samples',{}).values()); required={3,4}|(set(lattice)-set(REFERENCES)); seen={int(x['receiver_id']) for x in samples}
    evaluator_called=bool(production['evaluator_imports'])
    forbidden_fields_present=bool(production['forbidden_parameters'] or production['forbidden_names'])
    for sample in samples:
        sample['evaluator_called']=evaluator_called
        sample['forbidden_fields_present']=forbidden_fields_present
    event_ok=required<=seen and all(x['receiver_id']==x['observation_receiver_id'] and x['observation_dimension']==2 and not x['other_receiver_angles_present'] and not x['evaluator_called'] and not x['forbidden_fields_present'] for x in samples)
    negative_ok=(not truth_audit['accepted']) and (not cross_audit['accepted']) and set(rejected_fields)=={'truth_coordinates','world_coordinates','other_receiver_angles','cross_receiver_angles'}
    cross_receiver_exchange_detected=any(x['other_receiver_angles_present'] for x in samples)
    firewall=_status(bool(production['accepted']) and negative_ok and event_ok and not cross_receiver_exchange_detected,production_audit=production,illegal_truth_source_audit=truth_audit,illegal_cross_receiver_source_audit=cross_audit,rejected_constructor_fields=rejected_fields,negative_control_illegal_field_rejected=negative_ok,cross_receiver_angle_exchange=cross_receiver_exchange_detected,actual_event_counts=event_log.get('counts',{}),actual_event_samples=samples,event_coverage_receivers=sorted(seen),required_event_coverage_receivers=sorted(required))
    base=np.vstack([lattice[i] for i in REFERENCES]); max_error=0.
    for scale,theta,mirror,shift in ((.37,.41,False,np.array([2.3,-1.7])),(2.4,-.83,False,np.array([-3.2,4.1])),(1.6,1.17,True,np.array([.5,2.2]))):
        rot=np.array([[cos(theta),-sin(theta)],[sin(theta),cos(theta)]]); linear=scale*rot@(np.diag([-1.,1.]) if mirror else np.eye(2)); transformed=(linear@base.T).T+shift
        for i in set(lattice)-set(REFERENCES): max_error=max(max_error,float(np.max(abs(four_angles(linear@lattice[i]+shift,transformed)-four_angles(lattice[i],base)))))
    geometry=evaluate_formation(lattice); metamorphic=_status(max_error<3e-12 and geometry['nearest_neighbor_edge_count']==30 and geometry['line_group_count']==12,max_angle_error=max_error,angle_threshold=3e-12,ideal_target_geometry_only=geometry)
    return firewall,metamorphic

def run_gate():
    lattice=target_lattice(); event_log={}; baseline=float(np.linalg.norm(lattice[11]-lattice[15])); candidate,independent,negative,degenerate=_candidate_checks(lattice); analytic,exact,finite=_bootstrap_checks(lattice,event_log); follower=_follower_checks(lattice,event_log); firewall,metamorphic=_firewall_and_metamorphic(lattice,event_log); fixed_schedule=_fixed_bootstrap_schedule_audit(); end_to_end,ideal_reset,geometry_negative,sensitivity=_end_to_end_checks(lattice,event_log)
    scale_angles=max(float(np.max(abs(four_angles(2*lattice[i],np.vstack([2*lattice[j] for j in REFERENCES]))-four_angles(lattice[i],np.vstack([lattice[j] for j in REFERENCES]))))) for i in lattice if i not in REFERENCES)
    scale=_status(scale_angles<3e-12,maximum_angle_difference=scale_angles,threshold=3e-12,interpretation='无可信基线时 d* 与 2d* 的纯角不可区分')
    checks={'four_reference_complete_candidates':candidate,'independent_root_check':independent,'old_route_double_root_negative':negative,'boundary_collision_negative':degenerate,'bootstrap_analytic_check':analytic,'bootstrap_exact_replay':exact,'bootstrap_finite_replay':finite,'follower_local_replay':follower,'information_firewall':firewall,'fixed_bootstrap_schedule_audit':fixed_schedule,'metamorphic_and_ideal_target_geometry':metamorphic,'scale_indistinguishability_negative':scale,'actual_end_to_end_formation':end_to_end,'ideal_anchor_reset_negative':ideal_reset,'actual_geometry_negative':geometry_negative,'trusted_reference_sensitivity':sensitivity}
    return {'gate':'Q2_PROGRAM_GATE','status':'PASS' if all(v['status']=='PASS' for v in checks.values()) else 'FAIL','scope':'目标邻域、非退化、FY11/FY15 可信基线、确定性回放；不声明全局收敛。','trusted_baseline_length_in_d_star':baseline,'checks':checks}

if __name__=='__main__':
    result=run_gate(); OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'status':result['status'],'output':str(OUT)},ensure_ascii=False)); raise SystemExit(0 if result['status']=='PASS' else 1)
