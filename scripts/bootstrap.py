"""Idempotent fail-closed bootstrap: no guessed versions or curl-pipe-shell."""
import json, pathlib, shutil, re, subprocess
from .runtime_adapters import get_adapter
from .socket_supervisor import SocketSupervisor
from .readiness import ReadinessDoctor

TRUSTED_TALKTOFIGMA_REPO='https://github.com/grab/cursor-talk-to-figma-mcp'

def prepare_checkout(root, lock):
    root=pathlib.Path(root)
    spec=lock.get('talktofigma',{})
    if spec.get('repository') != TRUSTED_TALKTOFIGMA_REPO:
        raise ValueError('TalkToFigma repository must be the audited upstream URL')
    sha=spec.get('commit_sha')
    if not isinstance(sha,str) or not re.fullmatch(r'[0-9a-f]{40}',sha):
        raise RuntimeError('PIN_REQUIRED: exact TalkToFigma commit SHA missing')
    path=root/'.agent/vendor/talktofigma'
    if not (path/'.git').exists():
        if path.exists() and any(path.iterdir()):
            raise RuntimeError('Existing nonempty vendor checkout is unmanaged; refusing overwrite')
        path.parent.mkdir(parents=True,exist_ok=True)
        clone=subprocess.run(['git','clone','--no-checkout','--',TRUSTED_TALKTOFIGMA_REPO,str(path)],capture_output=True,text=True,timeout=120)
        if clone.returncode:raise RuntimeError('Pinned TalkToFigma clone failed; verify network access')
        checkout=subprocess.run(['git','-C',str(path),'checkout','--detach',sha],capture_output=True,text=True,timeout=120)
        if checkout.returncode:raise RuntimeError('Pinned SHA unavailable in checkout; refusing tag fallback')
    head=subprocess.run(['git','-C',str(path),'rev-parse','HEAD'],capture_output=True,text=True)
    dirty=subprocess.run(['git','-C',str(path),'status','--porcelain'],capture_output=True,text=True)
    if head.returncode or head.stdout.strip()!=sha or dirty.returncode or dirty.stdout.strip():
        raise RuntimeError('TalkToFigma checkout revision mismatch or dirty worktree; preserving files')
    return {'path':str(path),'sha':sha}

def setup(root,runtime):
    root=pathlib.Path(root)
    if runtime not in ('both','codex','claude'):raise ValueError('Invalid runtime')
    runtimes=['codex','claude'] if runtime=='both' else [runtime]
    missing=[cmd for cmd in ('python3','git','node','bun',*runtimes) if not shutil.which(cmd)]
    actions=[]
    lock=root/'config/dependencies.lock.json'
    if not lock.exists():actions.append('Create maintainer-verified dependencies.lock.json')
    else:
        pinned=json.loads(lock.read_text())
        if not pinned.get('talktofigma',{}).get('commit_sha'):actions.append('Pin and verify exact TalkToFigma Git commit')
        if not pinned.get('ui_ux_pro_max',{}).get('release_version'):actions.append('Pin and verify UI UX Pro Max version')
        if not pinned.get('superpowers',{}).get('commit_sha'):actions.append('Pin and verify Superpowers Git commit')
    checkout_ready=False
    if 'git' not in missing:
        try:
            prepare_checkout(root,pinned if lock.exists() else {})
            checkout_ready=True
        except (ValueError, RuntimeError, subprocess.TimeoutExpired) as e:actions.append(f'Pinned TalkToFigma checkout: {e}')
    for name in runtimes:
        if name in missing:continue
        try:get_adapter(name,root).register_mcp()
        except RuntimeError as e:actions.append(f'{name} MCP: {e}')
        agent=get_adapter(name,root)
        for skill in ('superpowers','ui-ux-pro-max'):
            outcome=agent.verify_skill(skill)
            if not outcome['ready']:actions.append(f'{name} skill {skill}: {outcome["reason"]}')
    # No unverified installation or changes to ~/.config, even if dependencies absent
    if checkout_ready and 'bun' not in missing:
        try:SocketSupervisor(root).up()
        except (RuntimeError, OSError) as e:actions.append(str(e))
    status='action_required' if missing or actions else 'partial_ready'
    return {'status':status,'missing':missing,'actions':actions,'readiness':ReadinessDoctor(root).check(runtime),'next_action':'Install missing prerequisites and resolve verified lock/config; then connect plugin'}
