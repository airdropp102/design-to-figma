"""Operational Figma MCP builder; no product application source."""
import argparse, base64, contextlib, io, json, sys, re
from pathlib import Path
from prototype_mcp import MCP
from writer_lock import WriterLock
from prepare_rotation import rotation_states, viewer_recipe, rotation_links
import state

ROOT=Path(__file__).resolve().parent.parent
FILE='rXrX1FHInMsxbejkvSP9Wl'
REG=ROOT/'design/ROTATION_NODES.json'
def cli(*args):
    old=sys.argv;sys.argv=['state.py',*args];output=io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            try:state.main()
            except SystemExit as e:
                if e.code not in (None,0):raise RuntimeError(output.getvalue())
    finally:sys.argv=old
    return output.getvalue()
def options(key):
    return ['--recipe',f'design/screen-recipes/{key}.json','--tokens','design/tokens.gallery.json','--assets','assets/ASSET_MANIFEST.json']
def flatten(root):
    result={}
    def visit(n,parent):
        if parent:result[n['name']]={**n,'verified_parent':parent}
        for ch in n.get('children',[]):visit(ch,n['id'])
    visit(root,None);return result

def operate(channel,finish=False,wire=False):
    client=MCP();registry=json.loads(REG.read_text()) if REG.exists() else {}
    colors=json.loads((ROOT/'design/tokens.gallery.json').read_text())['colors']
    def call(name,args):
        response=client.tool(name,args)
        for c in response.get('content',[]):
            if c.get('type')!='text':continue
            value=c['text']
            if value.startswith('Error'):raise RuntimeError(value)
            try:return json.loads(value)
            except ValueError:pass
            if name in ('create_frame','create_text','clone_node'):
                match=re.search(r'(?:new ID|ID): ([0-9]+:[0-9]+)',value)
                if match:return {'id':match.group(1)}
            if name in ('rename_node','set_fill_color','set_image_fill','delete_node'):return {'message':value}
        if name=='set_multiple_text_contents':
            messages='\n'.join(c.get('text','') for c in response.get('content',[]))
            if '- 0 failed' in messages:return {'message':messages}
        raise RuntimeError('Unsupported MCP response '+name+': '+str(response)[:400])
    def gate():
        client.tool('join_channel',{'channel':channel});d=call('get_document_info',{})
        assert d['fileKey']==FILE and d['id']=='0:1' and d['fileName']=='Untitled' and d['prototypePluginVersion']=='1.0.0',d
    def save():REG.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
    def export(key,node):
        for attempt in range(2):
            r=client.tool('export_node_as_image',{'nodeId':node,'format':'PNG','scale':0.5})
            images=[c for c in r.get('content',[]) if c.get('type')=='image']
            if images:
                (ROOT/f'design/previews/{key}-rotation.png').write_bytes(base64.b64decode(images[0]['data']));return
            if attempt==0:gate();call('get_node_info',{'nodeId':node})
        raise RuntimeError('Two export failures; visual QA blocked '+key)
    try:
        gate()
        st=json.loads((ROOT/'design/STATE.json').read_text())
        with WriterLock(ROOT).acquire(FILE+':'+channel,st.get('run_id','rotation')):
            if wire:
                payload=json.loads((ROOT/'design/ROTATION_PROTOTYPE_INTENT.json').read_text());payload['readOnly']=True
                before=call('apply_prototype',payload)
                (ROOT/'design/ROTATION_PARTIAL_REACTIONS.json').write_text(json.dumps(before,indent=2)+'\n')
                selected={record['nodes']['color.'+s['color']] for s in rotation_states() for record in [registry[s['key']]]}
                payload['updates']=[u for u in payload['updates'] if u['nodeId'] not in selected]
                for s in rotation_states():
                    key=s['key'];path=ROOT/f'design/screen-recipes/{key}.json';recipe=json.loads(path.read_text())
                    for n in recipe['nodes']:
                        if n['semantic_id']=='color.'+s['color']:n['style'].pop('prototype',None)
                    path.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n');cli('intend','screen',key,*options(key))
                current={n['id']:n['reactions'] for n in before['nodes']}
                remaining=[]
                for u in payload['updates']:
                    reactions=current[u['nodeId']]
                    if not reactions or reactions[0]['actions'][0].get('destinationId')!=u['destinationId']:remaining.append(u)
                gate();call('apply_prototype',{**payload,'readOnly':False,'updates':remaining})
                live=call('apply_prototype',payload);verify_reactions(payload,live)
                (ROOT/'design/ROTATION_PROTOTYPE_INTENT.json').write_text(json.dumps({k:v for k,v in payload.items() if k!='readOnly'},indent=2)+'\n')
                (ROOT/'design/ROTATION_LIVE_REACTIONS.json').write_text(json.dumps(live,indent=2)+'\n');export('S29','69:286')
                print('Verified '+str(len(payload['updates']))+' transitions; selected color has no self-navigation.',flush=True);return
            if finish:
                assert (ROOT/'design/ROTATION_VISUAL_QA.json').exists(),'Interactive visual review required'
                review=json.loads((ROOT/'design/ROTATION_VISUAL_QA.json').read_text())
                assert all(review.get(k)=='passed' for k in [s['key'] for s in rotation_states()]+['S29'])
                intent=json.loads((ROOT/'design/ROTATION_PROTOTYPE_INTENT.json').read_text());intent['readOnly']=True
                live=call('apply_prototype',intent);verify_reactions(intent,live)
                call('get_nodes_info',{'nodeIds':[v['root'] for v in registry.values()]})
                for s in rotation_states():
                    cli('qa','screen',s['key'],'--structural','passed','--visual','passed')
                    cli('done','screen',s['key'],'--note','Live tree/reaction graph verified; exported visual reviewed. AI inferred angles.')
                cli('qa','screen','S29','--structural','passed','--visual','passed');cli('done-update','screen','S29')
                if st.get('paused'):cli('resume')
                print('Committed16 rotation states and detail entry after live/visual QA',flush=True);return
            if registry:
                for key,record in list(registry.items()):
                    item=st['items']['screen:'+key];assert item['status']=='creating' and item['node_id']==record['root']
                    gate();node=call('get_node_info',{'nodeId':record['root']});assert node['name']==item['name']
                    call('delete_node',{'nodeId':record['root']});cli('reset','screen',key,'--reason','Reconciled interrupted operational run','--forgive')
                registry.clear();save();st=json.loads((ROOT/'design/STATE.json').read_text())
            pending=st['items'].get('screen:S32')
            if pending and pending['status']=='creating' and not pending.get('node_id'):
                gate();doc=call('get_document_info',{});matches=[n for n in doc['children'] if n['name']==pending['name']]
                assert len(matches)<=1,'Ambiguous unfinished root'
                if matches:call('get_node_info',{'nodeId':matches[0]['id']});call('delete_node',{'nodeId':matches[0]['id']})
                cli('reset','screen','S32','--reason','Reconciled empty root after MCP response format mismatch','--forgive')
                st=json.loads((ROOT/'design/STATE.json').read_text())
            assert not any(i['status'] in ('creating','updating') for i in st['items'].values())
            done=[i['node_id'] for i in st['items'].values() if i['status']=='done' and i['node_id']]
            live=call('get_nodes_info',{'nodeIds':done});assert {n['id'] for n in live}==set(done)
            assert len(done)+16<=25
            if st.get('paused'):cli('resume')
            for s in rotation_states():
                key=s['key'];recipe=viewer_recipe(s);cli('plan','screen',key,s['name'],'--priority','P0');cli('inspect','screen',key,*options(key))
                gate();cli('begin','screen',key,s['name']);cli('intend','screen',key,*options(key))
                count=0
                def measured(name,args):
                    nonlocal count
                    count+=1;return call(name,args)
                if not registry:
                    r=recipe['root'];root=measured('create_frame',{'name':s['name'],'x':r['x'],'y':r['y'],'width':1440,'height':900,'layoutMode':'NONE','fillColor':colors['bg']['rgba']})['id']
                    cli('node','screen',key,root);ids={'root':root}
                    registry[key]={'root':root,'nodes':ids};save()
                    for n in recipe['nodes']:
                        pos=n['layout'];sty=n['style'];args={'name':n['name'],'parentId':ids[n['parent']],'x':pos['x'],'y':pos['y']}
                        if n['type']=='FRAME':args.update(width=pos['width'],height=pos['height'],layoutMode='NONE',fillColor=colors[sty['fill']]['rgba']);tool='create_frame'
                        else:
                            color=n['tokens'][0].split('.')[1];args.update(text=n['text'],fontSize=sty['fontSize'],fontWeight=sty['fontWeight'],fontColor=colors[color]['rgba']);tool='create_text'
                        ids[n['semantic_id']]=measured(tool,args)['id'];save()
                else:
                    r=recipe['root'];root=measured('clone_node',{'nodeId':registry['S32']['root'],'x':r['x'],'y':r['y']})['id'];cli('node','screen',key,root)
                    registry[key]={'root':root,'nodes':{'root':root}};save();measured('rename_node',{'nodeId':root,'name':s['name']})
                    tree=measured('get_node_info',{'nodeId':root});names=flatten(tree);ids={'root':root,**{n['semantic_id']:names[n['name']]['id'] for n in recipe['nodes']}};registry[key]['nodes']=ids;save()
                    base=viewer_recipe(rotation_states()[0]);old={n['semantic_id']:n for n in base['nodes']}
                    changes=[{'nodeId':ids[n['semantic_id']],'text':n['text']} for n in recipe['nodes'] if n['type']=='TEXT' and n['text']!=old[n['semantic_id']]['text']]
                    if changes:measured('set_multiple_text_contents',{'nodeId':root,'text':changes})
                    if s['color']=='sage':
                        for sid,col in [('color.ivory','secondary'),('color.sage','primary'),('color.ivory.label','text'),('color.sage.label','on_primary')]:measured('set_fill_color',{'nodeId':ids[sid],**colors[col]['rgba']})
                image=ROOT/f"assets/images/an-nhien-{s['color']}-{s['angle']:03d}.png";assert image.exists(),image
                measured('set_image_fill',{'nodeId':ids['photo'],'imagePath':str(image),'scaleMode':'FIT'})
                tree=measured('get_node_info',{'nodeId':root});names=flatten(tree)
                assert tree['name']==s['name']
                for n in recipe['nodes']:
                    v=names[n['name']];assert v['type']==n['type'] and v['verified_parent']==ids[n['parent']]
                    if n['type']=='TEXT':assert v['characters']==n['text'],v
                    cli('bind','screen',key,n['semantic_id'],v['id'],'--type',n['type'],'--parent',ids[n['parent']],'--verified')
                export(key,root);cli('metrics','screen',key,'--calls',str(count+1),'--failed','0','--batch','1' if key!='S32' else '0','--reused',str(len(recipe['nodes']) if key!='S32' else 0))
                print('Built/exported '+key,flush=True)
            # Patch the existing detail button under state update intent.
            path=ROOT/'design/screen-recipes/S29.json';recipe=json.loads(path.read_text())
            for n in recipe['nodes']:
                if n['semantic_id']=='detail.size.label':n['text']='Xem 8 góc / đổi màu'
                if n['semantic_id']=='detail.size':n['style']['prototype']={'trigger':'ON_CLICK','action':'NAVIGATE','destinationId':registry['S32']['root'],'transition':'DISSOLVE','duration':0.2}
            path.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n')
            cli('inspect','screen','S29',*options('S29'));gate();call('get_nodes_info',{'nodeIds':['69:286','69:303','69:304']});cli('begin-update','screen','S29',*options('S29'),'--verified-live')
            call('set_multiple_text_contents',{'nodeId':'69:286','text':[{'nodeId':'69:304','text':'Xem 8 góc / đổi màu'}]})
            updates=[]
            for s in rotation_states():
                for sid,dest in rotation_links(s,rotation_states()).items():
                    target=registry[dest]['root'] if dest in registry else {'S30':'69:310','S28':'69:204'}[dest]
                    updates.append({'nodeId':registry[s['key']]['nodes'][sid],'trigger':'ON_CLICK','action':'OVERLAY' if sid=='book' else 'NAVIGATE','destinationId':target,'transition':'DISSOLVE','duration':0.2 if sid.startswith('color.') else 0.12})
            updates.append({'nodeId':'69:303','trigger':'ON_CLICK','action':'NAVIGATE','destinationId':registry['S32']['root'],'transition':'DISSOLVE','duration':0.2})
            payload={'fileKey':FILE,'pageId':'0:1','ownedRootIds':[v['root'] for v in registry.values()]+['69:286','69:310','69:204'],'updates':updates}
            (ROOT/'design/ROTATION_PROTOTYPE_INTENT.json').write_text(json.dumps(payload,indent=2)+'\n');gate();call('apply_prototype',payload)
            payload['readOnly']=True;live=call('apply_prototype',payload);verify_reactions(payload,live)
            (ROOT/'design/ROTATION_LIVE_REACTIONS.json').write_text(json.dumps(live,indent=2)+'\n');export('S29','69:286')
            print('97 reactions verified. Awaiting interactive export visual review before state commit.',flush=True)
    except BaseException as e:
        if not isinstance(e,KeyboardInterrupt):cli('pause','--reason','Rotation operation requires reconciliation: '+str(e)[:220])
        raise
    finally:client.close()

def verify_reactions(intent,live):
    nodes={n['id']:n for n in live['nodes']}
    for u in intent['updates']:
        r=nodes[u['nodeId']]['reactions'];assert len(r)==1 and r[0]['trigger']['type']=='ON_CLICK'
        a=r[0]['actions'][0];assert a['destinationId']==u['destinationId'] and a['navigation']==u['action'],a

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--channel',required=True);p.add_argument('--finish',action='store_true');p.add_argument('--wire',action='store_true');a=p.parse_args();operate(a.channel,a.finish,a.wire)
