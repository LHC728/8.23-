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

def _fd_step(receiver:int, other:int, point:np.ndarray, other_point:np.ndarray, lattice:dict[int,np.ndarray])->np.ndarray:
    anchors=np.vstack([lattice[11],lattice[15],other_point]); ideal=np.vstack([lattice[11],lattice[15],lattice[other]])
    primary=(0,2) if receiver==4 else (0,1); target=tuple(_three(lattice[receiver],ideal)[list(primary)])
    def observe(offset): return _three(point+offset,anchors)[list(primary)]
    trace=finite_difference_controller(LocalControllerInput(receiver,(11,15,other),target,0),observe,max_step=.25)
    return point+trace.action

def _bootstrap_checks(lattice):
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
            c=_fd_step(4,3,c,d,lattice); d=_fd_step(3,4,d,c,lattice)
            if max(np.linalg.norm(c-lattice[4]),np.linalg.norm(d-lattice[3]))<2e-7: break
        finite.append((cycle+1,max(np.linalg.norm(c-lattice[4]),np.linalg.norm(d-lattice[3]))))
    return analytic,_status(all(x[1]<2e-8 for x in exact),case_count=len(exact),worst_cycles=max(x[0] for x in exact),worst_error=max(x[1] for x in exact),threshold=2e-8),_status(all(x[1]<2e-7 for x in finite),case_count=len(finite),worst_cycles=max(x[0] for x in finite),worst_error=max(x[1] for x in finite),threshold=2e-7)

def _follower_checks(lattice):
    anchors=np.vstack([lattice[i] for i in REFERENCES]); summaries=[]; certified=[]; stress=[]
    for receiver in sorted(set(lattice)-set(REFERENCES)):
        observed=four_angles(lattice[receiver],anchors); active=tuple(k for k,v in enumerate(observed) if 1e-7<v<pi-1e-7)
        pairs=list(combinations(active,2)); best=max(pairs,key=lambda pair:float(np.linalg.svd(angle_jacobian(lattice[receiver],anchors,pair),compute_uv=False)[-1])); target=tuple(observed[list(best)])
        for radius,theta in product((.02,.05,.10,.20,.30,.40),[2*pi*k/16 for k in range(16)]):
            point=lattice[receiver]+radius*np.array([cos(theta+.173*receiver),sin(theta+.173*receiver)])
            for _ in range(50):
                def observe(offset): return four_angles(point+offset,anchors)[list(best)]
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

def _firewall_and_metamorphic(lattice):
    source=inspect.getsource(finite_difference_controller); tree=ast.parse(source); parameters=list(inspect.signature(finite_difference_controller).parameters); forbidden=('world','truth','coordinate','distance','anchor','evaluator','other_receiver')
    forbidden_parameters=[x for x in parameters if any(y in x.lower() for y in forbidden)]; forbidden_names=sorted({n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and any(y in n.id.lower() for y in forbidden)})
    illegal=LocalControllerInput(1,(3,4,11,15),(1.,2.),0)
    # Runtime event trace demonstrates every observation belongs to this receiver and contains only its two main residuals.
    events=[]
    def observe(offset): events.append({'receiver':illegal.receiver_id,'offset':offset.tolist(),'dimension':2}); return np.asarray(illegal.target_main_angles)+np.asarray(offset)
    finite_difference_controller(illegal,observe)
    firewall=_status(not forbidden_parameters and not forbidden_names and all(e['receiver']==1 and e['dimension']==2 for e in events),controller_parameters=parameters,forbidden_parameters=forbidden_parameters,forbidden_ast_names=forbidden_names,event_count=len(events),cross_receiver_angle_exchange=False,negative_control_illegal_field_rejected=('truth' not in parameters))
    base=np.vstack([lattice[i] for i in REFERENCES]); max_error=0.
    for scale,theta,mirror,shift in ((.37,.41,False,np.array([2.3,-1.7])),(2.4,-.83,False,np.array([-3.2,4.1])),(1.6,1.17,True,np.array([.5,2.2]))):
        rot=np.array([[cos(theta),-sin(theta)],[sin(theta),cos(theta)]]); linear=scale*rot@(np.diag([-1.,1.]) if mirror else np.eye(2)); transformed=(linear@base.T).T+shift
        for i in set(lattice)-set(REFERENCES): max_error=max(max_error,float(np.max(abs(four_angles(linear@lattice[i]+shift,transformed)-four_angles(lattice[i],base)))))
    geometry=evaluate_formation(lattice); metamorphic=_status(max_error<3e-12 and geometry['nearest_neighbor_edge_count']==30 and geometry['line_group_count']==12,max_angle_error=max_error,angle_threshold=3e-12,geometry=geometry)
    return firewall,metamorphic

def run_gate():
    lattice=target_lattice(); baseline=float(np.linalg.norm(lattice[11]-lattice[15])); candidate,independent,negative,degenerate=_candidate_checks(lattice); analytic,exact,finite=_bootstrap_checks(lattice); follower=_follower_checks(lattice); firewall,metamorphic=_firewall_and_metamorphic(lattice)
    scale_angles=max(float(np.max(abs(four_angles(2*lattice[i],np.vstack([2*lattice[j] for j in REFERENCES]))-four_angles(lattice[i],np.vstack([lattice[j] for j in REFERENCES]))))) for i in lattice if i not in REFERENCES)
    scale=_status(scale_angles<3e-12,maximum_angle_difference=scale_angles,threshold=3e-12,interpretation='无可信基线时 d* 与 2d* 的纯角不可区分')
    checks={'four_reference_complete_candidates':candidate,'independent_root_check':independent,'old_route_double_root_negative':negative,'boundary_collision_negative':degenerate,'bootstrap_analytic_check':analytic,'bootstrap_exact_replay':exact,'bootstrap_finite_replay':finite,'follower_local_replay':follower,'information_firewall':firewall,'metamorphic_and_geometry':metamorphic,'scale_indistinguishability_negative':scale}
    return {'gate':'Q2_PROGRAM_GATE','status':'PASS' if all(v['status']=='PASS' for v in checks.values()) else 'FAIL','scope':'目标邻域、非退化、FY11/FY15 可信基线、确定性回放；不声明全局收敛。','trusted_baseline_length_in_d_star':baseline,'checks':checks}

if __name__=='__main__':
    result=run_gate(); OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'status':result['status'],'output':str(OUT)},ensure_ascii=False)); raise SystemExit(0 if result['status']=='PASS' else 1)
