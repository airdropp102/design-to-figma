"""Strict, safe, design-only workflow policy."""
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass(frozen=True)
class WorkflowPolicy:
    version: int
    backend: str
    screens_per_run: int
    max_questions: int
    targeted_repairs_per_screen: int
    raw: dict

def load_policy(path: Path) -> WorkflowPolicy:
    with open(path, encoding='utf8') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('Unsupported workflow policy version')
    if data.get('backend') != 'talktofigma':
        raise ValueError('Only talktofigma backend permitted')
    brain = data.get('brainstorm', {})
    if not isinstance(brain, dict) or brain.get('required') is not True or brain.get('approval_required') is not True:
        raise ValueError('Brainstorm and user approval are mandatory')
    limits = data.get('limits', {})
    if not isinstance(limits, dict): raise ValueError('limits must be a mapping')
    q = brain.get('max_questions', 8)
    screens = limits.get('screens_per_run', 25)
    repair = limits.get('targeted_repairs_per_screen', 2)
    for key, value, lo, hi in [('max_questions',q,1,8), ('screens_per_run',screens,1,25),('targeted_repairs_per_screen',repair,0,2)]:
        if type(value) is not int or not lo <= value <= hi: raise ValueError(f'Invalid {key}')
    out=data.get('product_output', {})
    if not isinstance(out,dict) or out.get('figma_design_only') is not True or out.get('prohibit_application_code') is not True:
        raise ValueError('Application source code generation prohibited')
    recovery=data.get('recovery', {})
    if not isinstance(recovery,dict) or any(recovery.get(k) is not True for k in ('reconcile_before_retry','forbid_force_resume','file_identity_check')):
        raise ValueError('Safety recovery gates are mandatory')
    return WorkflowPolicy(1,'talktofigma',screens,q,repair,data)
