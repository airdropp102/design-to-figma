"""Operational Figma recipes, not application source code."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def recipe(key,name,width,height,x,y):
    return {'screen_id':key,'name':name,'root':{'width':width,'height':height,'x':x,'y':y,'fill':'bg','layout':'NONE'},'nodes':[]}
def frame(r,id,parent,x,y,w,h,fill='bg',asset=None,direction='NONE'):
    n={'semantic_id':id,'type':'FRAME','parent':parent,'name':('img/' if asset else 'layout/')+id,'layout':{'x':x,'y':y,'width':w,'height':h,'direction':direction},'tokens':['colors.'+fill],'style':{'fill':fill}}
    if asset:n['assets']=['images:'+asset]
    r['nodes'].append(n);return id
def text(r,id,parent,x,y,value,size=16,color='text',weight=400):
    r['nodes'].append({'semantic_id':id,'type':'TEXT','parent':parent,'name':'text/'+color+'/'+id,'text':value,'layout':{'x':x,'y':y},'tokens':['colors.'+color,'typography.family.ui'],'style':{'fontSize':size,'fontWeight':weight}})
def button(r,id,parent,x,y,w,label,fill='primary',color='on_primary'):
    frame(r,id,parent,x,y,w,52,fill);text(r,id+'.label',id,20,16,label,16,color,500)
def header(r):
    frame(r,'header','root',0,0,1440,96)
    text(r,'brand','header',72,28,'NÉT',32,weight=600)
    button(r,'nav.collection','header',456,22,176,'Bộ sưu tập','bg','text')
    button(r,'nav.products','header',648,22,112,'Áo dài','bg','text')
    button(r,'nav.story','header',768,22,176,'Câu chuyện','bg','text')
    button(r,'nav.book','header',1180,22,188,'Đặt lịch thử')

def prepare():
    r=recipe('S28','S28 Fashion v2 — Editable Homepage',1440,4432,4800,0);header(r)
    frame(r,'hero','root',0,96,1440,960,asset='net-aodai-campaign-v1')
    text(r,'hero.kicker','hero',96,176,'ÁO DÀI ĐƯƠNG ĐẠI',16,weight=500)
    text(r,'hero.title','hero',96,232,'Nét Việt.\nDáng hôm nay.',64,weight=500)
    text(r,'hero.body','hero',96,416,'Giữ tinh thần Việt trong dáng áo đương đại,\ndành cho những người phụ nữ hôm nay.',16)
    button(r,'hero.explore','hero',96,496,256,'Khám phá bộ sưu tập','cta')
    button(r,'hero.book','hero',376,496,192,'Đặt lịch thử','surface','text')
    frame(r,'collection','root',0,1056,1440,960)
    text(r,'collection.kicker','collection',72,48,'VỀ NÉT',16,'muted')
    text(r,'collection.title','collection',72,88,'Dáng Việt',48)
    text(r,'collection.body','collection',648,64,'Áo dài là một phần văn hóa sống trong nhịp sống hôm nay.\nNÉT gìn giữ tinh thần Việt qua phom dáng tinh giản,\nchất liệu chọn lọc và những chi tiết đầy dụng ý.',16)
    frame(r,'collection.photo','collection',72,200,640,696,asset='net-aodai-sage-v1')
    frame(r,'collection.detail','collection',760,200,608,384,asset='net-silk-texture-v1')
    text(r,'collection.detail.title','collection',760,616,'Thanh lịch\ntrong từng chi tiết.',32)
    text(r,'collection.detail.body','collection',760,728,'Những đường may tỉ mỉ, phom dáng vừa vặn,\ntôn lên vẻ đẹp tự nhiên của người phụ nữ Việt.',16)
    button(r,'collection.explore','collection',760,808,248,'Khám phá Dáng Việt','bg','text')
    frame(r,'features','root',0,2016,1440,240)
    for i,(title,body) in enumerate([('Phom dáng','Tôn dáng người Việt,\nthoải mái trong từng chuyển động.'),('Chất liệu','Lụa và vải tự nhiên,\nmềm mại, thoáng nhẹ.'),('Chi tiết','Tối giản mà tinh tế,\nlàm nên dấu ấn riêng.')]):
        x=72+i*432;text(r,f'feature.{i}.title','features',x,48,title,24);text(r,f'feature.{i}.body','features',x,96,body)
    frame(r,'material','root',0,2256,1440,560)
    frame(r,'material.photo','material',0,0,816,560,asset='net-silk-texture-v1')
    text(r,'material.kicker','material',872,72,'CHẤT LIỆU',16,'muted')
    text(r,'material.title','material',872,128,'Chạm vào\nchất Việt.',48)
    text(r,'material.body','material',872,296,'Chọn chất liệu tự nhiên với cảm giác\nmềm mại, thoáng nhẹ và vẻ đẹp bền lâu.\nTư vấn chất liệu theo dịp mặc của bạn.',16)
    frame(r,'colors','root',0,2816,1440,288)
    text(r,'colors.kicker','colors',72,48,'BẢNG MÀU',16,'muted')
    text(r,'colors.title','colors',72,88,'Những sắc màu\ncủa nét Việt.',32)
    button(r,'color.ivory','colors',712,104,188,'Trắng ngà · Chọn')
    button(r,'color.sage','colors',920,104,188,'Xanh ngọc','secondary','text')
    button(r,'color.blush','colors',1128,104,188,'Hồng phấn','secondary','text')
    frame(r,'products','root',0,3104,1440,784)
    text(r,'products.kicker','products',72,40,'BỘ SƯU TẬP NỔI BẬT',16,'muted')
    text(r,'products.title','products',72,88,'Dáng áo, muôn sắc.',48)
    for i,(name,price,asset,color) in enumerate([('An Nhiên','2.490.000 đ','net-aodai-sage-v1','Trắng ngà / Xanh ngọc'),('Ngọc Sương','3.290.000 đ','net-aodai-blush-v1','Hồng phấn / Ngọc trai'),('Hạ Miên','1.890.000 đ','net-aodai-linen-v1','Cát / Xanh nhạt'),('Diễm Châu','4.590.000 đ','net-aodai-wine-v1','Đỏ rượu / Champagne')]):
        id=f'product.{i}';frame(r,id,'products',72+i*328,184,312,560)
        frame(r,id+'.photo',id,0,0,312,432,asset=asset)
        text(r,id+'.title',id,0,452,name,24);text(r,id+'.price',id,0,492,price);text(r,id+'.color',id,0,524,color,16,'muted')
    frame(r,'booking','root',0,3888,1440,352,'primary')
    text(r,'booking.title','booking',72,64,'Một cuộc hẹn.\nMột dáng riêng.',48,'on_primary')
    text(r,'booking.body','booking',792,72,'Khám phá phom dáng và chất liệu cùng NÉT.\nĐặt lịch thử để tìm dáng áo phù hợp với bạn.',16,'on_primary')
    button(r,'booking.cta','booking',792,176,248,'Đặt lịch tư vấn','surface','text')
    frame(r,'footer','root',0,4240,1440,192)
    text(r,'footer.brand','footer',72,40,'NÉT',24,weight=600)
    text(r,'footer.links','footer',456,48,'Bộ sưu tập    Áo dài    Câu chuyện',16)
    text(r,'footer.demo','footer',72,112,'Bản thử nghiệm · Ảnh AI minh họa · Không gửi dữ liệu thật',16,'muted')
    out=[r]
    d=recipe('S29','S29 Fashion v2 — Chi tiết An Nhiên',1440,1040,6400,0);header(d)
    frame(d,'detail.photo','root',72,128,576,832,asset='net-aodai-sage-v1')
    text(d,'detail.kicker','root',728,144,'DÁNG VIỆT / AN NHIÊN',16,'muted')
    text(d,'detail.title','root',728,200,'An Nhiên',48)
    text(d,'detail.price','root',728,280,'2.490.000 đ',24)
    text(d,'detail.description','root',728,344,'Dáng áo dài thanh lịch trong nhịp sống hôm nay.\nChất liệu satin mềm mại. Ảnh AI minh họa.\nTư vấn kích thước và màu khi đặt lịch.',16)
    text(d,'detail.color','root',728,448,'Màu đang xem: Xanh ngọc',16,weight=500)
    button(d,'detail.size','root',728,488,248,'Tư vấn chọn kích thước','secondary','text')
    button(d,'detail.book','root',728,584,272,'Đặt lịch thử An Nhiên')
    button(d,'detail.back','root',728,656,272,'Quay lại trang chủ','bg','text')
    text(d,'detail.demo','root',728,784,'Prototype minh họa, không mua hàng\nvà không ghi nhận lịch hẹn thật.',16,'muted');out.append(d)
    b=recipe('S30','S30 Fashion v2 — Đặt lịch demo',640,720,8000,0)
    text(b,'booking.kicker','root',48,40,'TƯ VẤN CÙNG NÉT',16,'muted')
    text(b,'booking.title','root',48,88,'Hẹn một dáng riêng',32)
    text(b,'booking.note','root',48,152,'Dữ liệu mẫu để thử luồng. Không gửi thông tin thật.',16,'muted')
    for i,(label,value) in enumerate([('Họ tên','Khách trải nghiệm'),('Liên hệ','Thông tin liên hệ mẫu'),('Thời gian','Chọn lịch trong buổi tư vấn')]):
        y=208+i*112;text(b,f'field.{i}.label','root',48,y,label)
        frame(b,f'field.{i}','root',48,y+32,544,52,'secondary');text(b,f'field.{i}.value',f'field.{i}',16,16,value)
    button(b,'booking.submit','root',48,584,336,'Xem xác nhận đặt lịch demo')
    button(b,'booking.close','root',408,584,184,'Đóng','bg','text')
    text(b,'booking.disclosure','root',48,664,'Form prototype: không nhập liệu, không gửi dữ liệu.',16,'muted');out.append(b)
    s=recipe('S31','S31 Fashion v2 — Xác nhận demo',1440,900,8800,0)
    text(s,'success.brand','root',72,48,'NÉT',32,weight=600)
    text(s,'success.kicker','root',360,272,'XÁC NHẬN DEMO',16,'muted')
    text(s,'success.title','root',360,328,'Hẹn gặp bạn cùng NÉT.',48)
    text(s,'success.body','root',360,416,'Bạn đã hoàn thành luồng đặt lịch thử nghiệm.\nChưa có lịch hẹn thực tế hay dữ liệu được gửi.\nNhấn bên dưới để quay lại bộ sưu tập.',16)
    button(s,'success.home','root',360,536,272,'Quay lại trang chủ');out.append(s)
    for r in out:(ROOT/f'design/screen-recipes/{r["screen_id"]}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([{ 'id':r['screen_id'],'nodes':len(r['nodes'])} for r in out]))
if __name__=='__main__':prepare()
