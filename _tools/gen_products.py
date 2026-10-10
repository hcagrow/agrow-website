#!/usr/bin/env python3
"""제품 상세 페이지 생성기 (products/{lang}/{slug}.html + sitemap.xml)
사용: python3 _tools/gen_products.py        (저장소 루트에서 실행, node 필요)
도메인 변경 시 BASE만 바꾸고 다시 실행."""
import json, os, re, subprocess, html, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://agrow.hpagrow.com'
LANGS = ['ko','en','ru','uz','zh','ja','vi','id']
HREFLANG = {'ko':'ko','en':'en','ru':'ru','uz':'uz','zh':'zh-Hans','ja':'ja','vi':'vi','id':'id'}
LOCALE = {'ko':'ko_KR','en':'en_US','ru':'ru_RU','uz':'uz_UZ','zh':'zh_CN','ja':'ja_JP','vi':'vi_VN','id':'id_ID'}
FLAG = {'ko':'🇰🇷','en':'🇺🇸','ru':'🇷🇺','uz':'🇺🇿','zh':'🇨🇳','ja':'🇯🇵','vi':'🇻🇳','id':'🇮🇩'}
LNAME = {'ko':'한국어','en':'English','ru':'Русский','uz':"O'zbekcha",'zh':'中文','ja':'日本語','vi':'Tiếng Việt','id':'Indonesia'}

# slug, 표시명(키 또는 고정), 모델번호, 분류키, 설명키, 배지키, 이미지, 카탈로그 PDF
PRODUCTS = [
 ('perfect',   'Agrow-Perfect',     'HPA-9001',       'cat_n','pd_perfect','bdg_new', 'agrow_perfect.jpg',   'agrow'),
 ('7000plus',  'Agrow-7000 Plus',   'HPA-7000 PLUS',  'cat_n','pd_7000p',  'bdg_top', 'agrow_7000plus.jpg',  'agrow'),
 ('6000plus',  'Agrow-6000 Plus',   'HPA-6000 PLUS',  'cat_n','pd_6000p',  'bdg_no1', 'agrow_6000plus.jpg',  'agrow'),
 ('7000',      'Agrow-7000',        'HPA-7000',       'cat_n','pd_7000',   None,      'agrow_7000.jpg',      'agrow'),
 ('6000',      'Agrow-6000',        'HPA-6000',       'cat_n','pd_6000',   None,      'agrow_6000.jpg',      'agrow'),
 ('5000master','Agrow-5000 Master', 'HPA-5002',       'cat_n','pd_5000m',  'bdg_2024','agrow_5000master.jpg','agrow'),
 ('5000magic', 'Agrow-5000 Magic',  'HPA-5001',       'cat_n','pd_5000mg', 'bdg_2024','agrow_5000magic.jpg', 'agrow'),
 ('2000a',     '@n2000a',           'HPA-2005A',      'cat_i','pd_2000a',  'bdg_2024','agrow_2000star_a.jpg','agrow'),
 ('2000b',     '@n2000b',           'HPA-2005B',      'cat_i','pd_2000b',  'bdg_2024','agrow_2000star_b.jpg','agrow'),
 ('aplus',     'A⁺-green',          'HPAG-8001',      'cat_e','pd_aplus',  None,      'agrow_aplusgreen.jpg','aplus'),
]

# 카탈로그에서 앞줄에 이어지는 줄(0부터 센 번호) → 앞 항목에 합침
CONT = {'perfect':{13:' / ',19:' / '},'7000plus':{24:' '},'6000plus':{20:' '},'7000':{17:' '},'6000':{12:' '},
        '5000master':{8:' / ',10:' / '},'5000magic':{12:' / '},'2000b':{8:' / ',12:' / '},'2000a':{8:' / '},'aplus':{}}
def feat_items(slug,lines):
    out=[]
    for i,f in enumerate(lines):
        f=f.strip()
        if i in CONT[slug] and out: out[-1][1]+=CONT[slug][i]+f.lstrip('- ').strip(); continue
        out.append([f.startswith('-'), f.lstrip('- ').strip()])
    return out

UI = {
'ko':dict(brand='브랜드',specs='주요 사양 및 기능',model='모델명',catalog='카탈로그 보기',pdf='카탈로그 PDF',inquire='제품 문의',others='다른 제품',home='홈',products='제품',ctitle='구매 · 견적 문의',cdesc='모델 선정, 견적, 설치·수출 상담은 편하게 연락주세요.',subj='[제품 문의] ',maker='제조사',made='대한민국 제조'),
'en':dict(brand='Brand',specs='Key Specifications & Features',model='Model No.',catalog='View Catalog',pdf='Catalog PDF',inquire='Inquire',others='Other Products',home='Home',products='Products',ctitle='Sales & Quotation',cdesc='Contact us for model selection, quotes, installation and export.',subj='[Product inquiry] ',maker='Manufacturer',made='Made in Korea'),
'ru':dict(brand='Бренд',specs='Основные характеристики и функции',model='Модель',catalog='Открыть каталог',pdf='Каталог PDF',inquire='Отправить запрос',others='Другие продукты',home='Главная',products='Продукция',ctitle='Продажи и коммерческое предложение',cdesc='Свяжитесь с нами по вопросам выбора модели, цены, установки и экспорта.',subj='[Запрос о продукте] ',maker='Производитель',made='Сделано в Корее'),
'uz':dict(brand='Brend',specs='Asosiy xususiyatlar va funksiyalar',model='Model',catalog="Katalogni ko'rish",pdf='Katalog PDF',inquire="So'rov yuborish",others='Boshqa mahsulotlar',home='Bosh sahifa',products='Mahsulotlar',ctitle="Sotuv va narx so'rovi",cdesc="Model tanlash, narx, o'rnatish va eksport bo'yicha biz bilan bog'laning.",subj="[Mahsulot bo'yicha so'rov] ",maker='Ishlab chiqaruvchi',made='Koreyada ishlab chiqarilgan'),
'zh':dict(brand='品牌',specs='主要规格与功能',model='型号',catalog='查看目录',pdf='目录 PDF',inquire='咨询',others='其他产品',home='首页',products='产品',ctitle='销售与报价咨询',cdesc='型号选择、报价、安装及出口事宜，欢迎随时联系我们。',subj='[产品咨询] ',maker='制造商',made='韩国制造'),
'ja':dict(brand='ブランド',specs='主な仕様と機能',model='型番',catalog='カタログを見る',pdf='カタログ PDF',inquire='お問い合わせ',others='その他の製品',home='ホーム',products='製品',ctitle='販売・お見積りのお問い合わせ',cdesc='機種選定、お見積り、設置・輸出のご相談はお気軽にご連絡ください。',subj='[製品お問い合わせ] ',maker='メーカー',made='韓国製'),
'vi':dict(brand='Thương hiệu',specs='Thông số và tính năng chính',model='Mã model',catalog='Xem catalogue',pdf='Catalogue PDF',inquire='Liên hệ',others='Sản phẩm khác',home='Trang chủ',products='Sản phẩm',ctitle='Liên hệ mua hàng & báo giá',cdesc='Liên hệ với chúng tôi để được tư vấn chọn model, báo giá, lắp đặt và xuất khẩu.',subj='[Hỏi về sản phẩm] ',maker='Nhà sản xuất',made='Sản xuất tại Hàn Quốc'),
'id':dict(brand='Merek',specs='Spesifikasi & Fitur Utama',model='No. Model',catalog='Lihat Katalog',pdf='Katalog PDF',inquire='Tanya Produk',others='Produk Lainnya',home='Beranda',products='Produk',ctitle='Penjualan & Penawaran Harga',cdesc='Hubungi kami untuk pemilihan model, penawaran harga, instalasi, dan ekspor.',subj='[Pertanyaan produk] ',maker='Produsen',made='Buatan Korea'),
}

def load_T():
    s = open(os.path.join(ROOT,'index.html'),encoding='utf-8').read()
    a = s.index('const T={'); b = s.index('Object.assign(T, T2);') + len('Object.assign(T, T2);')
    js = s[a:b] + '\nprocess.stdout.write(JSON.stringify(T));'
    out = subprocess.run(['node','-'],input=js,capture_output=True,text=True,check=True)
    return json.loads(out.stdout)

E = lambda x: html.escape(str(x), quote=True)
def strip_br(x): return re.sub(r'<br\s*/?>',' ',str(x)).replace('\n',' ')

def pname(p,t): return t[p[1][1:]] if p[1].startswith('@') else p[1]
def img_rel(p,lang): return ('images/'+p[6]) if lang=='ko' else ('images/loc/%s/%s'%(lang,p[6]))
def url(lang,slug): return '%s/products/%s/%s.html'%(BASE,lang,slug)
def pdf_rel(p,lang): return ('downloads/%s_catalog.pdf'%p[7]) if lang=='ko' else ('downloads/catalog/%s_catalog_%s.pdf'%(p[7],lang))

SUN='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="4.5" fill="currentColor"/><path d="M12 1.5v2.5M12 20v2.5M1.5 12H4M20 12h2.5M4.6 4.6l1.8 1.8M17.6 17.6l1.8 1.8M4.6 19.4l1.8-1.8M17.6 6.4l1.8-1.8"/></svg>'
MOON='<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>'
def cls(svg,c): return svg.replace('<svg ','<svg class="'+c+'" ',1)

CSS = r'''
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
[data-theme="light"]{--bg:#F4F6F9;--bg2:#EAEDF2;--card:#fff;--t1:#0C1A2E;--t2:#3D5068;--t3:#7A8FA6;--bdr:rgba(12,26,46,.09);--acc:#00C87A;--acc2:#009F62;--nav:rgba(244,246,249,.94);--sh:0 2px 8px rgba(12,26,46,.06),0 12px 32px rgba(12,26,46,.08)}
[data-theme="dark"]{--bg:#080F1C;--bg2:#0D1726;--card:#112035;--t1:#E8EFF8;--t2:#9DB1C7;--t3:#6A86A4;--bdr:rgba(0,200,122,.14);--acc:#00E5A0;--acc2:#00C87A;--nav:rgba(8,15,28,.94);--sh:0 2px 8px rgba(0,0,0,.3),0 12px 32px rgba(0,0,0,.3)}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--t1);font-family:'Noto Sans KR','Inter',system-ui,sans-serif;line-height:1.6;transition:background .3s,color .3s}
a{color:inherit}
.wrap{max-width:1160px;margin:0 auto;padding:0 20px}
header{position:sticky;top:0;z-index:50;background:var(--nav);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border-bottom:1px solid var(--bdr)}
.hd{display:flex;align-items:center;gap:12px;height:60px}
.logo{font-family:'Inter',sans-serif;font-weight:900;font-size:21px;letter-spacing:-1px;color:var(--acc);text-decoration:none}
.hd-r{margin-left:auto;display:flex;align-items:center;gap:8px}
.lsel{position:relative}
.lsel summary{list-style:none;cursor:pointer;padding:6px 12px;border:1.5px solid var(--bdr);border-radius:100px;font-size:12.5px;font-weight:600;color:var(--t2);white-space:nowrap}
.lsel summary::-webkit-details-marker{display:none}
.lsel[open] summary{border-color:var(--acc)}
.lsel ul{position:absolute;right:0;top:calc(100% + 6px);list-style:none;background:var(--card);border:1px solid var(--bdr);border-radius:12px;padding:6px;min-width:150px;box-shadow:var(--sh)}
.lsel li a{display:block;padding:7px 10px;border-radius:8px;font-size:13px;text-decoration:none;color:var(--t2);white-space:nowrap}
.lsel li a:hover,.lsel li a[aria-current]{background:var(--bg2);color:var(--acc);font-weight:700}
.tog{width:54px;height:28px;border-radius:14px;border:1px solid var(--bdr);cursor:pointer;background:#E3E9F0;position:relative;flex-shrink:0;padding:0}
[data-theme="dark"] .tog{background:#1B2A40}
.tog .tb{position:absolute;top:50%;width:13px;height:13px;margin-top:-6.5px;opacity:.45;pointer-events:none}
.tog .tb.s{left:7px;color:#C98A00}.tog .tb.m{right:7px;color:#5A6B82}
.tog-k{position:absolute;top:2px;left:2px;width:22px;height:22px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 4px rgba(0,0,0,.25);transition:transform .3s,background .3s;pointer-events:none}
[data-theme="dark"] .tog-k{transform:translateX(26px);background:#0C1A2E}
.tog-k svg{width:14px;height:14px}.tog-k .i-s{color:#F5A623}.tog-k .i-m{color:#FFD95A;display:none}
[data-theme="dark"] .tog-k .i-s{display:none}[data-theme="dark"] .tog-k .i-m{display:block}
.crumb{font-size:12.5px;color:var(--t3);padding:18px 0 4px}
.crumb a{text-decoration:none;color:var(--t3)}.crumb a:hover{color:var(--acc)}
.crumb span{margin:0 6px}
.hero{display:grid;grid-template-columns:1.1fr 1fr;gap:40px;align-items:center;padding:18px 0 40px}
.pimg{background:#fff;border-radius:18px;border:1px solid var(--bdr);box-shadow:var(--sh);padding:18px;display:flex;align-items:center;justify-content:center;position:relative}
.pimg img{width:100%;height:auto;max-height:440px;object-fit:contain;display:block}
.bdg{position:absolute;top:14px;left:14px;background:#0C1A2E;color:#fff;font-size:12px;font-weight:700;padding:4px 12px;border-radius:100px}
.bdg.gold{background:#C8902A}
.cat{font-size:12px;font-weight:800;letter-spacing:2px;color:var(--acc2);text-transform:uppercase}
[data-theme="dark"] .cat{color:var(--acc)}
h1{font-family:'Inter','Noto Sans KR',sans-serif;font-size:clamp(30px,4.4vw,46px);line-height:1.15;letter-spacing:-1px;margin:8px 0 10px}
.mno{display:inline-block;font-family:'Inter',sans-serif;font-size:14px;font-weight:700;color:var(--t2);background:var(--bg2);border:1px solid var(--bdr);border-radius:8px;padding:4px 10px}
.desc{font-size:16.5px;color:var(--t2);margin:18px 0 26px}
.btns{display:flex;flex-wrap:wrap;gap:10px}
.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 20px;border-radius:100px;font-size:14px;font-weight:700;text-decoration:none;border:1.5px solid var(--bdr);color:var(--t1);background:var(--card);white-space:nowrap;transition:all .2s}
.btn:hover{border-color:var(--acc);color:var(--acc)}
.btn.pri{background:var(--acc);border-color:var(--acc);color:#fff}
[data-theme="dark"] .btn.pri{color:#080F1C}
.btn.pri:hover{background:var(--acc2);border-color:var(--acc2);color:#fff}
.btn.tg{background:#229ED9;border-color:#229ED9;color:#fff}
.meta{display:flex;flex-wrap:wrap;gap:18px;margin-top:22px;font-size:13px;color:var(--t3)}
.meta b{color:var(--t2);font-weight:700}
section{padding:36px 0}
h2{font-size:24px;letter-spacing:-.5px;margin-bottom:18px}
.feat{list-style:none;background:var(--card);border:1px solid var(--bdr);border-radius:16px;padding:10px 24px;box-shadow:var(--sh)}
.feat li{padding:11px 0 11px 22px;border-bottom:1px solid var(--bdr);position:relative;font-size:15px;color:var(--t2)}
.feat li:last-child{border-bottom:none}
.feat li::before{content:'';position:absolute;left:2px;top:20px;width:8px;height:8px;border-radius:50%;background:var(--acc)}
.feat li.sub{padding-left:40px;border-top:none;margin-top:-6px}
.feat li.sub::before{left:22px;width:6px;height:6px;background:var(--t3)}
.cbox{background:linear-gradient(135deg,#0C1A2E,#123052);color:#fff;border-radius:18px;padding:30px;display:grid;grid-template-columns:1.2fr 1fr;gap:26px;align-items:center}
.cbox h2{color:#fff;margin-bottom:8px}.cbox p{color:#B8C7D9;font-size:15px}
.clist{display:flex;flex-direction:column;gap:10px}
.clist a{display:flex;align-items:center;gap:12px;padding:13px 18px;border-radius:14px;text-decoration:none;color:#fff;font-weight:700;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);transition:background .2s}
.clist a:hover{background:rgba(255,255,255,.16)}
.clist .tgl{background:#229ED9;border-color:#229ED9}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:14px}
.oc{display:block;background:var(--card);border:1px solid var(--bdr);border-radius:14px;overflow:hidden;text-decoration:none;transition:transform .2s,border-color .2s}
.oc:hover{transform:translateY(-3px);border-color:var(--acc)}
.oc .im{background:#fff;height:120px;display:flex;align-items:center;justify-content:center;padding:8px}
.oc img{max-width:100%;max-height:104px;object-fit:contain}
.oc .nm{padding:10px 12px;font-size:13.5px;font-weight:700;color:var(--t1)}
.oc .nm small{display:block;font-size:11px;font-weight:600;color:var(--t3)}
footer{border-top:1px solid var(--bdr);margin-top:30px;padding:28px 0 36px;font-size:13px;color:var(--t3)}
footer b{color:var(--t2)}
.mbar{display:none}
@media(max-width:860px){.hero{grid-template-columns:1fr;gap:22px}.cbox{grid-template-columns:1fr}}
@media(max-width:768px){
  .mbar{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:60;background:var(--nav);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border-top:1px solid var(--bdr);padding:8px 10px calc(8px + env(safe-area-inset-bottom));gap:8px}
  .mbar a{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;min-height:48px;border-radius:12px;text-decoration:none;font-size:12px;font-weight:700;color:#fff;white-space:nowrap}
  .mbar .mi{font-size:18px;line-height:1}
  .mbar .m-call{background:#00C87A}.mbar .m-tg{background:#229ED9}.mbar .m-mail{background:#3A4A5E}
  body{padding-bottom:calc(70px + env(safe-area-inset-bottom))}
  .feat{padding:6px 16px}.feat li{font-size:14.5px}
  .btn{padding:11px 16px;font-size:13.5px}
}
@media print{header,.mbar,.btns,.cbox .clist,.tog,.lsel{display:none!important}body{background:#fff;color:#000}.feat,.pimg{box-shadow:none}}
'''

def page(p, lang, T):
    t = T[lang]; u = UI[lang]; slug = p[0]
    name = pname(p,t); cat = t[p[3]]; desc = strip_br(t[p[4]])
    feats = FEATS[slug][lang]
    title = '%s (%s) – %s | Agrow %s' % (name, p[2], cat, t['brand_n'])
    mdesc = (desc + ' ' + ' '.join(feats[:3]))[:180]
    img = img_rel(p,lang); r = '../../'
    abs_img = BASE + '/' + img
    alts = ''.join('<link rel="alternate" hreflang="%s" href="%s">\n' % (HREFLANG[l], url(l,slug)) for l in LANGS)
    alts += '<link rel="alternate" hreflang="x-default" href="%s">\n' % url('en',slug)
    ld = [{
        "@context":"https://schema.org","@type":"Product","name":name,"model":p[2],"mpn":p[2],"sku":p[2],
        "category":cat,"description":desc,"image":[abs_img],"url":url(lang,slug),
        "brand":{"@type":"Brand","name":"Agrow"},
        "manufacturer":{"@type":"Organization","name":"한가람농업개발 (Hangaram Agricultural Development)","url":BASE+'/',
                        "telephone":"+82-33-747-5114","email":"hpagrow@hanmail.net",
                        "address":{"@type":"PostalAddress","streetAddress":"우무개로 274, 호저면","addressLocality":"원주시","addressRegion":"강원특별자치도","postalCode":"26349","addressCountry":"KR"}},
        "countryOfOrigin":{"@type":"Country","name":"KR"},
        "additionalProperty":[{"@type":"PropertyValue","name":u['model'],"value":p[2]}]
    },{
        "@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":u['home'],"item":BASE+'/?lang='+lang},
            {"@type":"ListItem","position":2,"name":u['products'],"item":BASE+'/?lang='+lang+'#products'},
            {"@type":"ListItem","position":3,"name":name,"item":url(lang,slug)}]
    }]
    li = ''.join('<li%s>%s</li>' % (' class="sub"' if sub else '', E(txt)) for sub,txt in feat_items(slug,feats))
    langs = ''.join('<li><a href="%s.html" hreflang="%s" lang="%s"%s>%s %s</a></li>' % (
        ('../%s/%s' % (l,slug)), HREFLANG[l], l, ' aria-current="page"' if l==lang else '', FLAG[l], LNAME[l]) for l in LANGS)
    others = ''.join('<a class="oc" href="%s.html"><div class="im"><img src="%s%s" alt="%s" loading="lazy"></div><div class="nm">%s<small>%s</small></div></a>' % (
        q[0], r, img_rel(q,lang), E(pname(q,t)), E(pname(q,t)), E(q[2])) for q in PRODUCTS if q[0]!=slug)
    bdg = ''
    if p[5]:
        bdg = '<span class="bdg%s">%s</span>' % (' gold' if p[5] in ('bdg_top','bdg_no1') else '', E(t[p[5]]))
    mail = 'mailto:hpagrow@hanmail.net?subject=' + __import__('urllib.parse').parse.quote(u['subj'] + name + ' (' + p[2] + ')')
    home = r + 'index.html?lang=' + lang
    tg_lbl = t['th_dark']
    return f'''<!DOCTYPE html>
<html lang="{lang}" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{E(title)}</title>
<meta name="description" content="{E(mdesc)}">
<link rel="canonical" href="{url(lang,slug)}">
{alts}<meta property="og:type" content="product">
<meta property="og:site_name" content="Agrow · 한가람농업개발">
<meta property="og:title" content="{E(name)} ({E(p[2])}) – {E(cat)}">
<meta property="og:description" content="{E(mdesc)}">
<meta property="og:url" content="{url(lang,slug)}">
<meta property="og:image" content="{abs_img}">
<meta property="og:locale" content="{LOCALE[lang]}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{r}favicon.ico" sizes="any">
<link rel="icon" href="{r}icons/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{r}icons/icon-180.png">
<meta name="theme-color" content="#00C87A">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Noto+Sans+KR:wght@400;500;700;900&display=swap" rel="stylesheet">
<script>try{{document.documentElement.dataset.theme=localStorage.getItem('ag-theme')||'light';localStorage.setItem('ag-lang','{lang}')}}catch(e){{}}</script>
<script type="application/ld+json">{json.dumps(ld,ensure_ascii=False)}</script>
<style>{CSS}</style>
</head>
<body>
<header><div class="wrap hd">
  <a class="logo" href="{home}">Agrow</a>
  <div class="hd-r">
    <details class="lsel"><summary>{FLAG[lang]} {LNAME[lang]} ▾</summary><ul>{langs}</ul></details>
    <button class="tog" id="togBtn" type="button" role="switch" aria-checked="false" title="{E(tg_lbl)}" aria-label="{E(tg_lbl)}">{cls(SUN,'tb s')}{cls(MOON,'tb m')}<span class="tog-k">{cls(SUN,'i-s')}{cls(MOON,'i-m')}</span></button>
  </div>
</div></header>
<main class="wrap">
  <nav class="crumb" aria-label="breadcrumb"><a href="{home}">{E(u['home'])}</a><span>›</span><a href="{home}#products">{E(u['products'])}</a><span>›</span>{E(name)}</nav>
  <div class="hero">
    <div class="pimg">{bdg}<img src="{r}{img}" alt="{E(name)} {E(p[2])} {E(cat)}" width="700" height="560"></div>
    <div>
      <div class="cat">{E(cat)}</div>
      <h1>{E(name)}</h1>
      <span class="mno">{E(u['model'])} {E(p[2])}</span>
      <p class="desc">{E(desc)}</p>
      <div class="btns">
        <a class="btn pri" href="{r}catalog.html?product={slug}&amp;lang={lang}">📖 {E(u['catalog'])}</a>
        <a class="btn" href="{r}{pdf_rel(p,lang)}" download>⬇ {E(u['pdf'])}</a>
        <a class="btn" href="{E(mail)}">✉ {E(u['inquire'])}</a>
        <a class="btn tg" href="https://t.me/Seongchan89" target="_blank" rel="noopener">✈ Telegram</a>
      </div>
      <div class="meta"><span><b>{E(u['maker'])}</b> {E(t['brand_n'])}</span><span><b>{E(u['brand'])}</b> Agrow</span><span>🇰🇷 {E(u['made'])}</span></div>
    </div>
  </div>
  <section><h2>{E(u['specs'])}</h2><ul class="feat">{li}</ul></section>
  <section><div class="cbox"><div><h2>{E(u['ctitle'])}</h2><p>{E(u['cdesc'])}</p></div>
    <div class="clist"><a href="tel:+82337475114">📞 033-747-5114</a><a href="{E(mail)}">✉️ hpagrow@hanmail.net</a><a class="tgl" href="https://t.me/Seongchan89" target="_blank" rel="noopener">✈️ Telegram @Seongchan89</a></div></div></section>
  <section><h2>{E(u['others'])}</h2><div class="grid">{others}</div></section>
</main>
<footer><div class="wrap"><b>Agrow · {E(t['brand_n'])}</b><br>{E(strip_br(t['con_addr']))}<br>TEL 033-747-5114 · FAX 033-746-1909 · hpagrow@hanmail.net<br>{E(strip_br(t['copyright']))}</div></footer>
<div class="mbar" role="navigation" aria-label="Quick contact">
  <a href="tel:+82337475114" class="m-call"><span class="mi">📞</span><span>{E(t['mb_call'])}</span></a>
  <a href="https://t.me/Seongchan89" target="_blank" rel="noopener" class="m-tg"><span class="mi">✈️</span><span>Telegram</span></a>
  <a href="{E(mail)}" class="m-mail"><span class="mi">✉️</span><span>{E(t['mb_mail'])}</span></a>
</div>
<script>
(function(){{var h=document.documentElement,b=document.getElementById('togBtn'),L={json.dumps([t['th_dark'],t['th_light']],ensure_ascii=False)};
function s(){{var d=h.dataset.theme==='dark';b.title=b.ariaLabel=L[d?1:0];b.setAttribute('aria-label',L[d?1:0]);b.setAttribute('aria-checked',d)}}
b.addEventListener('click',function(){{h.dataset.theme=h.dataset.theme==='dark'?'light':'dark';try{{localStorage.setItem('ag-theme',h.dataset.theme)}}catch(e){{}}s()}});s();
document.addEventListener('click',function(e){{var d=document.querySelector('.lsel');if(d&&d.open&&!d.contains(e.target))d.open=false}});}})();
</script>
</body>
</html>
'''

def sitemap():
    today = datetime.date.today().isoformat()
    def alt(f):
        return ''.join('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>\n' % (HREFLANG[l], f(l)) for l in LANGS)
    out = ['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
           '  <url>\n    <loc>%s/</loc>\n    <lastmod>%s</lastmod>\n    <priority>1.0</priority>\n  </url>' % (BASE, today)]
    for l in LANGS:
        out.append('  <url>\n    <loc>%s/?lang=%s</loc>\n%s    <lastmod>%s</lastmod>\n    <priority>1.0</priority>\n  </url>' % (BASE,l,alt(lambda x:'%s/?lang=%s'%(BASE,x)),today))
    out.append('  <url>\n    <loc>%s/catalog.html</loc>\n    <lastmod>%s</lastmod>\n    <priority>0.6</priority>\n  </url>' % (BASE,today))
    for p in PRODUCTS:
        for l in LANGS:
            out.append('  <url>\n    <loc>%s</loc>\n%s    <lastmod>%s</lastmod>\n    <priority>0.8</priority>\n  </url>' % (url(l,p[0]),alt(lambda x,s=p[0]:url(x,s)),today))
    out.append('</urlset>\n')
    open(os.path.join(ROOT,'sitemap.xml'),'w',encoding='utf-8').write('\n'.join(out))

if __name__ == '__main__':
    T = load_T()
    FEATS = json.load(open(os.path.join(ROOT,'_tools','features.json'),encoding='utf-8'))
    n = 0
    for lang in LANGS:
        d = os.path.join(ROOT,'products',lang); os.makedirs(d,exist_ok=True)
        for p in PRODUCTS:
            open(os.path.join(d,p[0]+'.html'),'w',encoding='utf-8').write(page(p,lang,T)); n += 1
    sitemap()
    print('generated', n, 'pages + sitemap.xml')
