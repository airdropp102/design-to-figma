"""Non-mutating operator diagnostics; socket != Figma plugin readiness."""
import pathlib, shutil
from .runtime_adapters import get_adapter
from .socket_supervisor import SocketSupervisor
class ReadinessDoctor:
    def __init__(self,root):self.root=pathlib.Path(root)
    def check(self,runtime=None):
        runtimes=['codex','claude'] if runtime in (None,'both') else [runtime]
        cli={r:get_adapter(r,self.root).diagnostics() for r in runtimes}
        dependencies={name:bool(shutil.which(name)) for name in ('python3','git','node','bun')}
        socket=SocketSupervisor(self.root).health()
        skills_ready=all(v['ui_ux_pro_max']['ready'] and v['superpowers']['ready'] for v in cli.values())
        agent_ready=all(v['cli']['available'] for v in cli.values()) and skills_ready
        return {'prereqs_ready':all(dependencies.values()),'agent_ready':agent_ready,'socket_ready':socket['running'],'figma_ready':False,'canvas_ready':False,'figma_status':'FIGMA_NOT_VERIFIED', 'dependencies':dependencies,'runtimes':cli,'socket':socket,'next_action':'Join Figma plugin/channel and validate document identity inside interactive agent before mutation'}
