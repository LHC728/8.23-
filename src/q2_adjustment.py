"""Q2 在线本机控制器；不导入 evaluator，也不保存仿真世界坐标。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import numpy as np


@dataclass(frozen=True)
class LocalControllerInput:
    receiver_id: int
    transmitter_ids: tuple[int, ...]
    target_main_angles: tuple[float, float]
    schedule_step: int
    local_action_history: tuple[tuple[float, float], ...] = ()


@dataclass
class ControllerTrace:
    action: np.ndarray
    residual_before: np.ndarray
    residual_after_norm: float
    probe_calls: int
    accepted: bool


def finite_difference_controller(local_input: LocalControllerInput, observe_offset: Callable[[np.ndarray], np.ndarray], *, probe: float = 2e-4, gain: float = .9, damping: float = 1e-7, max_step: float = .25) -> ControllerTrace:
    """只从当前接收机的 offset->两维主角残差获得一步本机动作。"""
    target = np.asarray(local_input.target_main_angles)
    origin = np.zeros(2)
    observed = np.asarray(observe_offset(origin)); calls = 1
    residual = observed - target
    jac = np.empty((2,2))
    for axis in range(2):
        delta = np.zeros(2); delta[axis] = probe
        jac[:,axis] = (np.asarray(observe_offset(delta))-np.asarray(observe_offset(-delta)))/(2*probe); calls += 2
    action = -gain*np.linalg.solve(jac.T@jac+damping*np.eye(2), jac.T@residual)
    norm=float(np.linalg.norm(action))
    if norm>max_step: action*=max_step/norm
    base=float(np.linalg.norm(residual)); selected=np.zeros(2); after=base
    for factor in (1.,.5,.25,.125,.0625,0.):
        trial=factor*action; trial_norm=float(np.linalg.norm(np.asarray(observe_offset(trial))-target)); calls+=1
        if trial_norm < base or factor==0.:
            selected=trial; after=trial_norm; break
    return ControllerTrace(selected,residual,after,calls,bool(np.linalg.norm(selected)>0))
