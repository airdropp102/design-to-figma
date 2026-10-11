"""Operate the local TalkToFigma MCP extension over stdio (never direct WS).

The interactive agent owns state transitions/QA. --apply requires all affected
screens already updating and registered source/destination IDs on this page.
"""
import argparse, base64, json, os, select, subprocess, time
from pathlib import Path
from writer_lock import WriterLock

ROOT=Path(__file__).resolve().parent.parent

class MCP:
    def __init__(self):
        self.p=subprocess.Popen(['/Users/thuannv/.local/bin/bun',str(ROOT/'.agent/mcp/talktofigma-prototype/server.ts')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
        self.seq=0
        self.rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'figma-prototype-operator','version':'1'}})
        self.send({'jsonrpc':'2.0','method':'notifications/initialized'})
        self.catalog={t['name']:t for t in self.rpc('tools/list',{})['tools']}
    def send(self,msg):
        self.p.stdin.write(json.dumps(msg)+'\n');self.p.stdin.flush()
    def rpc(self,method,params):
        self.seq+=1;i=self.seq
        self.send({'jsonrpc':'2.0','id':i,'method':method,'params':params})
        deadline=time.monotonic()+65
        while time.monotonic()<deadline:
            if select.select([self.p.stdout],[],[],1)[0]:
                line=self.p.stdout.readline()
                if not line:raise RuntimeError('MCP process exited')
                try:r=json.loads(line)
                except ValueError:continue
                if r.get('id')==i:
                    if 'error' in r:raise RuntimeError(str(r['error']))
                    return r['result']
        raise TimeoutError(method+'; reconcile live before retry')
    def tool(self,name,args):
        if name not in self.catalog:raise RuntimeError('Tool not exposed: '+name)
        r=self.rpc('tools/call',{'name':name,'arguments':args})
        if r.get('isError'):raise RuntimeError(str(r))
        return r
    def data(self,name,args):
        r=self.tool(name,args)
        for c in r.get('content',[]):
            if c.get('type')=='text':
                try:return json.loads(c['text'])
                except ValueError:continue
        raise RuntimeError('Expected JSON tool evidence: '+name)
    def close(self):
        self.p.terminate();self.p.wait(timeout=5)

def operate(channel,apply=False):
    intent=json.loads((ROOT/'design/PROTOTYPE_INTENT.json').read_text())
    state=json.loads((ROOT/'design/STATE.json').read_text())
    # Confirm state structure using the actual state file before mutation.
    items=state.get('items',{})
    if not items:raise RuntimeError('State item registry unavailable')
    owned=set()
    for key in ('S28','S29','S30','S31'):
        item=items.get('screen:'+key)
        if not item:raise RuntimeError('Missing state screen '+key)
        if apply and item['status']!='updating':raise RuntimeError('begin-update required for '+key)
        owned.add(item['node_id'])
        owned.update(v['node_id'] for v in item.get('semantic_nodes',{}).values())
    if not set(intent['ownedRootIds']).issubset(owned):raise RuntimeError('Unregistered root')
    for u in intent['updates']:
        if u['nodeId'] not in owned or (u.get('destinationId') and u['destinationId'] not in owned):raise RuntimeError('Unregistered prototype target')
    client=MCP()
    try:
        client.tool('join_channel',{'channel':channel})
        doc=client.data('get_document_info',{})
        if doc.get('fileKey')!=intent['fileKey'] or doc.get('id')!=intent['pageId'] or doc.get('fileName')!='Untitled':raise RuntimeError('Live document mismatch')
        if doc.get('prototypePluginVersion')!='1.0.0':raise RuntimeError('Prototype plugin not loaded')
        nodes=client.data('get_nodes_info',{'nodeIds':intent['ownedRootIds']})
        if {n['id'] for n in nodes}!=set(intent['ownedRootIds']):raise RuntimeError('Live roots missing')
        payload={k:v for k,v in intent.items() if k not in ('notes',)}
        payload['readOnly']=not apply
        if apply:
            with WriterLock(ROOT).acquire(intent['fileKey']+':'+channel,state.get('run_id','prototype')):
                live=client.data('apply_prototype',payload)
                payload['readOnly']=True
                verified=client.data('apply_prototype',payload)
        else:verified=client.data('apply_prototype',payload)
        path=ROOT/'.agent/runtime/prototype-live-read.json'
        path.write_text(json.dumps(verified,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'applied':apply,'evidence':str(path),'nodes':len(verified['nodes']),'viewports':verified.get('viewports',[])},ensure_ascii=False))
    finally:client.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--channel',required=True);p.add_argument('--apply',action='store_true');args=p.parse_args();operate(args.channel,args.apply)
