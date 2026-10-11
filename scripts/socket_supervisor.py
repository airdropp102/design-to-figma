"""Own a Bun socket process only when pinned and with provable PID identity."""
import json, os, pathlib, socket, subprocess, time

class SocketSupervisor:
    def __init__(self,root,port=3055):
        self.root=pathlib.Path(root).resolve();self.port=port;self.meta=self.root/'.agent/runtime/socket.pid.json'
    def _probe(self):
        try:
            with socket.create_connection(('127.0.0.1',self.port),timeout=.3):return True
        except OSError:return False
    @staticmethod
    def _identity(pid):
        try:
            cmd=subprocess.run(['ps','-p',str(pid),'-o','lstart=','-o','args='],capture_output=True,text=True,timeout=2)
            return cmd.stdout.strip() if cmd.returncode==0 else ''
        except (OSError,subprocess.TimeoutExpired):return ''
    def _owned(self):
        if not self.meta.exists():return False
        try:
            m=json.loads(self.meta.read_text())
            return bool(m.get('identity') and m['identity']==self._identity(int(m['pid'])) and m.get('command')=='bun socket')
        except (ValueError,OSError,KeyError):return False
    def health(self):return {'running':self._probe(),'owned':self._owned()}
    def up(self):
        if self._probe():
            if self._owned():return {'running':True,'reused':True,'owned':True}
            raise RuntimeError('Port in use by unknown process; refuse to attach')
        checkout=self.root/'.agent/vendor/talktofigma'
        lockfile=self.root/'config/dependencies.lock.json'
        lock=json.loads(lockfile.read_text()) if lockfile.exists() else {}
        pin=lock.get('talktofigma',{}).get('commit_sha')
        if not pin or not checkout.exists():raise RuntimeError('TalkToFigma pinned checkout unavailable; cannot start socket')
        head=subprocess.run(['git','-C',str(checkout),'rev-parse','HEAD'],capture_output=True,text=True)
        if head.returncode or head.stdout.strip()!=pin:raise RuntimeError('TalkToFigma checkout does not match pinned SHA')
        self.meta.parent.mkdir(parents=True,exist_ok=True)
        logfile=self.meta.with_name('socket.log')
        # Rotate logs without deleting other application logs
        if logfile.exists() and logfile.stat().st_size>1024*1024:logfile.replace(self.meta.with_name('socket.log.1'))
        with logfile.open('ab') as out:
            proc=subprocess.Popen(['bun','socket'],cwd=str(checkout),stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
        time.sleep(.25)
        ident=self._identity(proc.pid)
        if not ident or proc.poll() is not None:
            raise RuntimeError('Socket failed to start')
        self.meta.write_text(json.dumps({'pid':proc.pid,'identity':ident,'command':'bun socket','port':self.port}))
        return {'running':self._probe(),'owned':True,'reused':False}
    def down(self):
        if not self._owned():return {'stopped':False,'reason':'No owned socket process'}
        pid=int(json.loads(self.meta.read_text())['pid'])
        os.kill(pid,15)
        self.meta.unlink(missing_ok=True)
        return {'stopped':True}
