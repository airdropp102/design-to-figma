"""Platform-specific CLI checks. Shared TalkToFigma backend, never a fallback."""
import json, pathlib, re, shutil, subprocess, os, tempfile, tomllib

class RuntimeAdapter:
    command=''
    def __init__(self,root): self.root=pathlib.Path(root).resolve()
    def _lock(self):
        path=self.root/'config/dependencies.lock.json'
        if not path.is_file():raise RuntimeError('No dependency lockfile')
        return json.loads(path.read_text())
    def detect_version(self):
        if not shutil.which(self.command):return {'available':False,'version':None}
        try:
            r=subprocess.run([self.command,'--version'],capture_output=True,text=True,timeout=8,check=False)
            return {'available':r.returncode==0,'version':(r.stdout or r.stderr).strip()[:160]}
        except (OSError,subprocess.TimeoutExpired):return {'available':False,'version':None}
    def verify_skill(self,name):
        if name not in ('ui-ux-pro-max','superpowers'):return {'ready':False,'reason':'Unknown skill'}
        paths=[self.root/'.claude/skills'/name,self.root/'.agents/skills'/name]
        if name=='superpowers':return {'ready':False,'reason':'Plugin/skill invocation cannot be proven from filesystem; run manual runtime smoke test'}
        path=next((p for p in paths if p.exists()),None)
        if path is None:return {'ready':False,'reason':f'{name} skill not installed'}
        search=list(path.rglob('search.py'))
        if not search:return {'ready':False,'reason':'Skill lacks search.py smoke test'}
        try:
            r=subprocess.run(['python3',str(search[0]),'test','--design-system'],capture_output=True,text=True,timeout=25,cwd=str(self.root))
            return {'ready':r.returncode==0,'reason':'smoke-pass' if r.returncode==0 else 'smoke-failed'}
        except (OSError,subprocess.TimeoutExpired):return {'ready':False,'reason':'smoke-failed'}
    @staticmethod
    def _write_config(path, content):
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            current=path.read_text()
            if current==content:return False
            backup=path.with_suffix(path.suffix+'.bak')
            if not backup.exists():backup.write_text(current)
        fd,tmp=tempfile.mkstemp(prefix='.mcp-',dir=path.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf8') as file:
                file.write(content);file.flush();os.fsync(file.fileno())
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
        return True
    def register_mcp(self):
        lock=self._lock()
        sha=lock.get('talktofigma',{}).get('commit_sha')
        if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{40}',sha):raise RuntimeError('PIN_REQUIRED: TalkToFigma SHA not validated, registration blocked')
        checkout=self.root/'.agent/vendor/talktofigma'
        server=checkout/'src/talk_to_figma_mcp/server.ts'
        if not (checkout/'.git').exists() or not server.is_file():raise RuntimeError('Pinned TalkToFigma checkout absent; manual checkout required')
        head=subprocess.run(['git','-C',str(checkout),'rev-parse','HEAD'],capture_output=True,text=True,check=False)
        dirty=subprocess.run(['git','-C',str(checkout),'status','--porcelain'],capture_output=True,text=True,check=False)
        if head.returncode or head.stdout.strip()!=sha or dirty.returncode or dirty.stdout.strip():raise RuntimeError('Pinned checkout absent, dirty or wrong revision; preserving user files')
        entry={'command':'bun','args':[str(server)]}
        if self.command=='claude':
            path=self.root/'.mcp.json'
            try:config=json.loads(path.read_text()) if path.exists() else {}
            except json.JSONDecodeError:raise RuntimeError('Invalid existing .mcp.json; preserving original file')
            if not isinstance(config,dict) or not isinstance(config.get('mcpServers',{}),dict):raise RuntimeError('Unexpected .mcp.json schema')
            servers=config.setdefault('mcpServers',{})
            if 'TalkToFigma' in servers and servers['TalkToFigma']!=entry:raise RuntimeError('Conflicting TalkToFigma server; refusing replacement')
            servers['TalkToFigma']=entry
            changed=self._write_config(path,json.dumps(config,ensure_ascii=False,indent=2)+'\n')
        elif self.command=='codex':
            path=self.root/'.codex/config.toml'
            original=path.read_text() if path.exists() else ''
            try:config=tomllib.loads(original)
            except tomllib.TOMLDecodeError:raise RuntimeError('Existing .codex/config.toml malformed; preserving original')
            servers=config.get('mcp_servers',{})
            if 'TalkToFigma' in servers:
                existing=servers['TalkToFigma']
                if existing.get('command')!=entry['command'] or existing.get('args')!=entry['args']:
                    raise RuntimeError('Conflicting TalkToFigma server; refusing replacement')
                return {'registered':True,'changed':False,'scope':'project'}
            block='[mcp_servers.TalkToFigma]\ncommand = "bun"\nargs = '+json.dumps(entry['args'])+'\n'
            changed=self._write_config(path,original.rstrip()+'\n\n'+block)
        else:raise ValueError('Unknown runtime')
        return {'registered':True,'changed':changed,'scope':'project'}
    def launch_interactive(self,prompt,cwd):
        lock=self._lock()
        info=lock.get('runtime_clis',{}).get(self.command,{})
        if not info.get('verified_interactive_args') or not info.get('version'):
            raise RuntimeError('ADAPTER_UNSUPPORTED: CLI interactive bootstrap has not passed a live smoke test')
        if info.get('verified_interactive_args')!='positional-prompt':
            raise RuntimeError('ADAPTER_UNSUPPORTED: only audited positional-prompt CLI mode is supported')
        detected=self.detect_version()
        if not detected['available'] or detected['version']!=info['version']:
            raise RuntimeError('ADAPTER_UNSUPPORTED: pinned CLI version does not match installed executable')
        help_result=subprocess.run([self.command,'--help'],capture_output=True,text=True,timeout=8)
        if help_result.returncode or 'prompt' not in (help_result.stdout+help_result.stderr).lower():
            raise RuntimeError('ADAPTER_UNSUPPORTED: CLI help does not confirm positional prompt')
        # One blocking interactive session; prompt is an argv value, never shell evaluated.
        return subprocess.call([self.command,prompt],cwd=str(pathlib.Path(cwd).resolve()))
    def diagnostics(self):return {'cli':self.detect_version(),'superpowers':self.verify_skill('superpowers'),'ui_ux_pro_max':self.verify_skill('ui-ux-pro-max')}

class ClaudeAdapter(RuntimeAdapter):command='claude'
class CodexAdapter(RuntimeAdapter):command='codex'

def get_adapter(runtime,root):
    if runtime=='codex':return CodexAdapter(root)
    if runtime=='claude':return ClaudeAdapter(root)
    raise ValueError('Runtime must be claude or codex')
