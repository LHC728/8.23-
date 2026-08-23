"""Q1(3) local controller and offline plant, deliberately separated.

The controller uses only a receiver id, preloaded angle targets, local probe
displacements and its own observation history. World coordinates exist only
inside ObservationPlant and the offline evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from math import atan2, cos, pi, sin, sqrt
from typing import Callable

import numpy as np

from src.q1_1_geometry import analytic_angle_gradient, raw_angle
from src.q1_2_identity import target_coordinates

O, A, B, C = 0, 1, 4, 7
TARGET_ANGLE = pi / 6.0
ANCHORS = (O, A, B, C)
FOLLOWER_PAIRS = {2: ((O, A), (O, B)), 3: ((O, A), (O, B)), 5: ((O, B), (O, C)),
                  6: ((O, B), (O, C)), 8: ((O, A), (O, C)), 9: ((O, A), (O, C))}


def table1_coordinates() -> dict[int, np.ndarray]:
    polar = {0:(0,0), 1:(100,0), 2:(98,40.10), 3:(112,80.21), 4:(105,119.75), 5:(98,159.86),
             6:(112,199.96), 7:(105,240.07), 8:(98,280.17), 9:(112,320.28)}
    return {i:r*np.array((cos(d*pi/180), sin(d*pi/180))) for i,(r,d) in polar.items()}


def transform_positions(points: dict[int, np.ndarray], matrix: np.ndarray) -> dict[int, np.ndarray]:
    return {i:matrix @ point for i,point in points.items()}


def pair_angle(point: np.ndarray, world: dict[int, np.ndarray], pair: tuple[int, int]) -> float:
    return raw_angle(point, world[pair[0]], world[pair[1]])


@dataclass(frozen=True)
class LocalControllerInput:
    receiver_id: int
    target_main_angles: tuple[float, float]
    schedule_step: str
    local_action_history: tuple[tuple[float, float], ...] = ()


@dataclass(frozen=True)
class ControllerSettings:
    delta: float = .02
    eta: float = .85
    damping: float = 1e-8
    step_cap: float = 12.0
    inner_steps: int = 24
    residual_tolerance: float = 2e-9


@dataclass
class ControllerTrace:
    local_displacement: np.ndarray
    residual_norms: list[float]
    probes: int
    backtracks: int
    status: str


class ObservationPlant:
    """Simulation-only object: it owns all world coordinates and sensor laws."""
    def __init__(self, world, receiver, main_pairs, target_angles, axes):
        self._world, self._receiver = world, receiver
        self._main_pairs, self._target = main_pairs, target_angles
        self._axes = np.asarray(axes, dtype=float)
        self._start = world[receiver].copy()
        self.observation_events = []

    def observe(self, local_displacement):
        point = self._start + self._axes @ np.asarray(local_displacement, dtype=float)
        residual = np.array([pair_angle(point, self._world, pair)-angle for pair,angle in zip(self._main_pairs,self._target)])
        self.observation_events.append({"receiver": self._receiver, "dimension": int(residual.size), "pairs": [list(pair) for pair in self._main_pairs]})
        return residual

    def analytic_jacobian(self, local_displacement):
        point = self._start + self._axes @ np.asarray(local_displacement, dtype=float)
        return np.vstack([analytic_angle_gradient(point, self._world[i], self._world[j]) for i,j in self._main_pairs]) @ self._axes

    def apply(self, local_displacement):
        self._world[self._receiver] = self._start + self._axes @ np.asarray(local_displacement, dtype=float)


def finite_difference_controller(local_input: LocalControllerInput, observe: Callable[[np.ndarray],np.ndarray], *, settings: ControllerSettings) -> ControllerTrace:
    """Online algorithm: no coordinates, anchors or other receivers are accepted."""
    u = np.zeros(2); norms=[]; probes=backtracks=0
    for _ in range(settings.inner_steps):
        residual=np.asarray(observe(u),dtype=float); norm=float(np.linalg.norm(residual)); norms.append(norm)
        if norm <= settings.residual_tolerance: return ControllerTrace(u,norms,probes,backtracks,"CONVERGED")
        jac=np.empty((2,2))
        for col in range(2):
            d=np.zeros(2); d[col]=settings.delta
            jac[:,col]=(np.asarray(observe(u+d))-np.asarray(observe(u-d)))/(2*settings.delta); probes += 2
        step=-settings.eta*np.linalg.solve(jac.T@jac+settings.damping*np.eye(2),jac.T@residual)
        length=float(np.linalg.norm(step))
        if length>settings.step_cap: step*=settings.step_cap/length
        for factor in (1,.5,.25,.125,.0625):
            if float(np.linalg.norm(observe(u+factor*step))) < norm: u += factor*step; break
            backtracks += 1
        else: return ControllerTrace(u,norms,probes,backtracks,"BACKTRACK_REJECTED")
    norms.append(float(np.linalg.norm(observe(u))))
    return ControllerTrace(u,norms,probes,backtracks,"MAX_INNER_STEPS")


def exact_local_best_response(local_input, observe, analytic_jacobian, *, target_neighborhood_m=30.) -> ControllerTrace:
    """Independent offline Newton oracle using analytic Jacobians, not FD control."""
    u=np.zeros(2); norms=[]
    for _ in range(30):
        residual=np.asarray(observe(u)); norm=float(np.linalg.norm(residual)); norms.append(norm)
        if norm < 1e-12:
            status="CONVERGED_TARGET_NEAR" if float(np.linalg.norm(u))<=target_neighborhood_m else "TARGET_NEAR_BRANCH_REJECTED"
            return ControllerTrace(u,norms,0,0,status)
        step=-np.linalg.solve(np.asarray(analytic_jacobian(u)),residual)
        for factor in (1,.5,.25,.125,.0625):
            if float(np.linalg.norm(observe(u+factor*step)))<norm: u+=factor*step; break
        else: return ControllerTrace(u,norms,0,0,"NEWTON_BACKTRACK_REJECTED")
    return ControllerTrace(u,norms,0,0,"NEWTON_MAX_ITERATIONS")


def preloaded_follower_spec(receiver, *, target=None) -> dict:
    """All desired main/holdout signatures use only ideal slots and ideal anchors."""
    ideal=target_coordinates() if target is None else target
    main_pairs=FOLLOWER_PAIRS[receiver]
    all_pairs=tuple((ANCHORS[i],ANCHORS[j]) for i in range(4) for j in range(i+1,4))
    holdout_pairs=tuple(pair for pair in all_pairs if pair not in main_pairs)
    return {"main_pairs":main_pairs, "main_angles":tuple(pair_angle(ideal[receiver],ideal,pair) for pair in main_pairs),
            "holdout_pairs":holdout_pairs, "holdout_angles":tuple(pair_angle(ideal[receiver],ideal,pair) for pair in holdout_pairs)}


def bc_spec(receiver, *, target=None) -> dict:
    other=C if receiver==B else B
    return {"main_pairs":((O,A),(O,other)),"main_angles":(TARGET_ANGLE,TARGET_ANGLE)}


def _bearing_gradient(vector): return np.array((-vector[1],vector[0]))/float(vector@vector)
def angle_partials(receiver,left,right):
    u,v=left-receiver,right-receiver; sign=1. if np.cross(u,v)>0 else -1.
    gl,gr=-sign*_bearing_gradient(u),sign*_bearing_gradient(v); return -(gl+gr),gl,gr


@dataclass
class Dual:
    value:float; derivative:np.ndarray
    def __add__(self,o): o=_dual(o,len(self.derivative)); return Dual(self.value+o.value,self.derivative+o.derivative)
    __radd__=__add__
    def __sub__(self,o): o=_dual(o,len(self.derivative)); return Dual(self.value-o.value,self.derivative-o.derivative)
    def __rsub__(self,o): return _dual(o,len(self.derivative)).__sub__(self)
    def __mul__(self,o): o=_dual(o,len(self.derivative)); return Dual(self.value*o.value,self.derivative*o.value+o.derivative*self.value)
    __rmul__=__mul__
def _dual(v,n): return v if isinstance(v,Dual) else Dual(float(v),np.zeros(n))
def _ad_angle(x,a,b):
    u=[a[i]-x[i] for i in range(2)];v=[b[i]-x[i] for i in range(2)]; cross=u[0]*v[1]-u[1]*v[0];dot=u[0]*v[0]+u[1]*v[1];sgn=1 if cross.value>0 else -1
    return Dual(atan2(abs(cross.value),dot.value),(dot.value*sgn*cross.derivative-abs(cross.value)*dot.derivative)/(dot.value**2+cross.value**2))


def _bc_blocks(mode):
    q=target_coordinates(); b,c,o,a=q[B],q[C],q[O],q[A]
    if mode=="analytic":
        h1=angle_partials(b,o,a)[0];h2,_,hc=angle_partials(b,o,c); h3=angle_partials(c,o,a)[0];h4,_,hb=angle_partials(c,o,b)
        return {"D_B_f_B":np.vstack((h1,h2)),"D_C_f_B":np.vstack((np.zeros(2),hc)),"D_C_f_C":np.vstack((h3,h4)),"D_B_f_C":np.vstack((np.zeros(2),hb))}
    if mode=="automatic":
        e=np.eye(4); var=lambda p,k:[Dual(float(p[i]),e[k+i]) for i in range(2)]; const=lambda p:[Dual(float(v),np.zeros(4)) for v in p]
        bb,cc,oo,aa=var(b,0),var(c,2),const(o),const(a); f1,f2=_ad_angle(bb,oo,aa),_ad_angle(bb,oo,cc);g1,g2=_ad_angle(cc,oo,aa),_ad_angle(cc,oo,bb)
        return {"D_B_f_B":np.vstack((f1.derivative[:2],f2.derivative[:2])),"D_C_f_B":np.vstack((f1.derivative[2:],f2.derivative[2:])),"D_C_f_C":np.vstack((g1.derivative[2:],g2.derivative[2:])),"D_B_f_C":np.vstack((g1.derivative[:2],g2.derivative[:2]))}
    step=1e-4
    def f(bb,cc): return np.array((raw_angle(bb,o,a)-TARGET_ANGLE,raw_angle(bb,o,cc)-TARGET_ANGLE))
    def g(bb,cc): return np.array((raw_angle(cc,o,a)-TARGET_ANGLE,raw_angle(cc,o,bb)-TARGET_ANGLE))
    def diff(fn,w):
        z=np.empty((2,2))
        for j in range(2):
            d=np.zeros(2);d[j]=step; z[:,j]=(fn(b+d,c)-fn(b-d,c))/(2*step) if w=="b" else (fn(b,c+d)-fn(b,c-d))/(2*step)
        return z
    return {"D_B_f_B":diff(f,"b"),"D_C_f_B":diff(f,"c"),"D_C_f_C":diff(g,"c"),"D_B_f_C":diff(g,"b")}


def pair_cycle_metrics(left,right):
    q=target_coordinates();l,r,o,a=q[left],q[right],q[O],q[A]
    l1=angle_partials(l,o,a)[0];l2,_,lr=angle_partials(l,o,r);r1=angle_partials(r,o,a)[0];r2,_,rl=angle_partials(r,o,l)
    dll=np.vstack((l1,l2));drl=np.vstack((np.zeros(2),lr));drr=np.vstack((r1,r2));dlr=np.vstack((np.zeros(2),rl))
    l_r=-np.linalg.solve(dll,drl);r_l=-np.linalg.solve(drr,dlr);product=r_l@l_r;joint=np.block([[dll,drl],[dlr,drr]]);sv=np.linalg.svd(joint,compute_uv=False)
    return {"spectral_radius":float(max(abs(np.linalg.eigvals(product)))),"joint_rank":int(np.linalg.matrix_rank(joint)),"joint_condition":float(sv[0]/sv[-1]),"joint_sigma_min":float(sv[-1])}


def derivative_audit():
    blocks={m:_bc_blocks(m) for m in ("analytic","automatic","finite_difference")};a=1/(100*sqrt(3));expected={"D_B_f_B":np.array(((a,0),(-a/2,-1/200))),"D_C_f_B":np.array(((0,0),(-a,0))),"D_C_f_C":np.array(((a,0),(-a/2,1/200))),"D_B_f_C":np.array(((0,0),(-a,0)))}
    errors={n:{m:float(np.max(abs(blocks["analytic"][n]-blocks[m][n]))) for m in ("automatic","finite_difference")}|{"expected":float(np.max(abs(blocks["analytic"][n]-expected[n])))} for n in expected}
    core=pair_cycle_metrics(B,C); return {"blocks":{k:v.tolist() for k,v in blocks["analytic"].items()},"errors":errors,"core":core,"pass":max(v for e in errors.values() for v in e.values())<2e-6 and core["spectral_radius"]<1e-10}


def follower_metrics():
    q=target_coordinates();details={}
    for receiver,pairs in FOLLOWER_PAIRS.items():
        jac=np.vstack([analytic_angle_gradient(q[receiver],q[i],q[j]) for i,j in pairs]);sv=np.linalg.svd(jac,compute_uv=False);details[str(receiver)]={"sigma_min":float(sv[-1]),"condition":float(sv[0]/sv[-1])}
    return {"per_receiver":details,"worst_sigma_min":min(x["sigma_min"] for x in details.values()),"max_condition":max(x["condition"] for x in details.values())}


def controller_firewall_schema():
    names=[f.name for f in fields(LocalControllerInput)]
    return {"input_fields":names,"forbidden_fields_present":sorted(set(names)&{"world","point","coordinates","anchors","truth"}),"controller_accepts_world_coordinates":False}
