"""Figma image-turntable recipes, not a product application."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def rotation_states():
    return [{'key':f'S{32+c*8+i}','color':color,'angle':i*45,'name':f'S{32+c*8+i} An Nhiên — {label} — góc {i*45}'} for c,(color,label) in enumerate([('ivory','Trắng ngà'),('sage','Xanh ngọc')]) for i in range(8)]

def rotation_links(s,states):
    by={(v['color'],v['angle']):v['key'] for v in states}
    return {'angle.next':by[s['color'],(s['angle']+45)%360],'angle.prev':by[s['color'],(s['angle']-45)%360],'color.ivory':by['ivory',s['angle']],'color.sage':by['sage',s['angle']],'book':'S30','home':'S28'}

def viewer_recipe(s):
    nodes=[]
    def frame(id,parent,x,y,w,h,fill='bg',asset=None):
        n={'semantic_id':id,'type':'FRAME','parent':parent,'name':('img/' if asset else 'layout/')+id,'layout':{'x':x,'y':y,'width':w,'height':h,'direction':'NONE'},'tokens':['colors.'+fill],'style':{'fill':fill}}
        if asset:n['assets']=['images:'+asset]
        nodes.append(n)
    def text(id,parent,x,y,value,size=16,color='text',weight=400):
        nodes.append({'semantic_id':id,'type':'TEXT','parent':parent,'name':'text/'+id,'text':value,'layout':{'x':x,'y':y},'tokens':['colors.'+color,'typography.family.ui'],'style':{'fontSize':size,'fontWeight':weight}})
    def button(id,x,y,w,value,chosen=False):
        frame(id,'root',x,y,w,52,'primary' if chosen else 'secondary');text(id+'.label',id,20,16,value,16,'on_primary' if chosen else 'text',500)
    label='Trắng ngà' if s['color']=='ivory' else 'Xanh ngọc'
    text('brand','root',64,28,'NÉT',32,weight=600)
    frame('photo','root',64,96,576,720,asset=f"an-nhien-{s['color']}-{s['angle']:03d}")
    text('kicker','root',728,112,'DÁNG VIỆT / THỬ 8 GÓC',16,'muted')
    text('title','root',728,160,'An Nhiên',48)
    text('price','root',728,240,'2.490.000 đ',24)
    text('description','root',728,296,'Chọn màu và chuyển góc để xem dáng áo.\nẢnh AI minh họa, chưa xác nhận sản phẩm thật.',16,'muted')
    text('color.current','root',728,376,'Màu đang xem: '+label,16,weight=500)
    button('color.ivory',728,416,248,'Trắng ngà'+(' · Chọn' if s['color']=='ivory' else ''),s['color']=='ivory')
    button('color.sage',1000,416,248,'Xanh ngọc'+(' · Chọn' if s['color']=='sage' else ''),s['color']=='sage')
    text('angle.current','root',728,520,f"Góc {s['angle']}° · {s['angle']//45+1}/8",24)
    button('angle.prev',728,576,248,'Góc trước');button('angle.next',1000,576,248,'Góc tiếp theo')
    button('book',728,672,248,'Đặt lịch thử',True);button('home',1000,672,248,'Về trang chủ')
    text('disclosure','root',728,776,'Mô phỏng 8 ảnh, không xoay 3D liên tục.\nGóc sau và chi tiết khuất do AI suy diễn.',16,'muted')
    for n in nodes:
        if n['semantic_id'] in rotation_links(s,rotation_states()) and n['semantic_id']!='color.'+s['color']:
            dest=rotation_links(s,rotation_states())[n['semantic_id']]
            n['style']['prototype']={'destinationScreen':dest,'action':'OVERLAY' if n['semantic_id']=='book' else 'NAVIGATE','transition':'DISSOLVE','duration':0.2 if n['semantic_id'].startswith('color.') else 0.12}
    return {'screen_id':s['key'],'name':s['name'],'root':{'width':1440,'height':900,'x':4800+(s['angle']//45)*1520,'y':4800+(0 if s['color']=='ivory' else 1040),'fill':'bg','layout':'NONE'},'nodes':nodes}

def prepare():
    states=rotation_states()
    for s in states:(ROOT/f'design/screen-recipes/{s["key"]}.json').write_text(json.dumps(viewer_recipe(s),ensure_ascii=False,indent=2)+'\n')
    (ROOT/'design/ROTATION_STATES.json').write_text(json.dumps(states,ensure_ascii=False,indent=2)+'\n')
    print('Prepared16 color/angle recipes, within23 rendered-root quota')

if __name__=='__main__':prepare()
