"""One process-held writer per workspace; never a TTL-only lock."""
from contextlib import contextmanager
import fcntl, hashlib, json, os
from pathlib import Path

class WriterLock:
    def __init__(self,root):self.root=Path(root)
    @contextmanager
    def acquire(self,figma_target_id,run_id='unknown'):
        if not figma_target_id:raise ValueError('Missing verified Figma target ID')
        path=self.root/'.agent/locks/figma-writer.lock';path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('a+') as f:
            try:fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise BlockingIOError('Figma writer already active')
            try:
                f.seek(0);f.truncate();json.dump({'pid':os.getpid(),'run_id':run_id,'target_sha256':hashlib.sha256(figma_target_id.encode()).hexdigest()},f);f.flush();os.fsync(f.fileno())
                yield
            finally:fcntl.flock(f.fileno(),fcntl.LOCK_UN)
