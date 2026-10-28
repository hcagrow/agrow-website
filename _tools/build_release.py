#!/usr/bin/env python3
"""호스팅 서버 업로드용 버전 만들기
사용: python3 _tools/build_release.py https://www.agrow.co.kr  [출력폴더]
- 저장소를 복사하고, 사이트 안 주소를 새 도메인으로 바꾸고, 제품 페이지·사이트맵을 다시 생성합니다.
- GitHub 전용 파일(.git, CNAME, _tools)은 제외합니다."""
import os, sys, shutil, subprocess, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = 'https://agrow.hpagrow.com'
NEW = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'https://www.agrow.co.kr'
if not NEW.startswith(('http://', 'https://')): NEW = 'https://' + NEW  # 도메인만 넣어도 https 붙임
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(ROOT), 'release', re.sub(r'^https?://', '', NEW))
EXCLUDE = {'.git', '.github', '_tools', 'CNAME', 'README.md', '.gitignore'}
if os.path.exists(OUT): shutil.rmtree(OUT)
shutil.copytree(ROOT, OUT, ignore=lambda d, names: [n for n in names if d == ROOT and n in EXCLUDE])
# 주소 치환
n = 0
for dp, _, fs in os.walk(OUT):
    for f in fs:
        if f.endswith(('.html', '.xml', '.txt', '.js', '.webmanifest')) or f == '.htaccess':
            p = os.path.join(dp, f); s = open(p, encoding='utf-8', errors='surrogateescape').read()
            if OLD in s:
                open(p, 'w', encoding='utf-8', errors='surrogateescape').write(s.replace(OLD, NEW)); n += 1
# 어디에도 링크되지 않은 다운로드 파일(옛 버전)은 업로드본에서 제외
allhtml=''.join(open(os.path.join(dp,f),encoding='utf-8',errors='ignore').read() for dp,_,fs in os.walk(OUT) for f in fs if f.endswith('.html'))
for f in sorted(os.listdir(os.path.join(OUT,'downloads'))):
    fp=os.path.join(OUT,'downloads',f)
    if os.path.isfile(fp) and f not in allhtml:
        print('skip unused download:', f); os.remove(fp)
# 인쇄용 사이트 QR을 새 도메인으로 다시 생성
try:
    import segno
    qp=os.path.join(OUT,'images','qr-site.svg')
    segno.make(NEW+'/',error='m').save(qp,scale=4,border=0,dark='#0C1A2E',xmldecl=False,svgns=True)
    q=open(qp,encoding='utf-8').read();w=re.search(r'width="(\d+)"',q).group(1)
    open(qp,'w',encoding='utf-8').write(q.replace(f'height="{w}"',f'height="{w}" viewBox="0 0 {w} {w}"',1))
except ImportError:
    print('경고: segno 없음 - 인쇄용 QR이 기존 주소로 남습니다 (pip install segno)')
# 제품 페이지·사이트맵 재생성
env = dict(os.environ, AGROW_BASE=NEW, AGROW_OUT=OUT)
subprocess.run([sys.executable, os.path.join(ROOT, '_tools', 'gen_products.py')], env=env, check=True)
print('release:', OUT, '| replaced in', n, 'files')
