#!/usr/bin/env python3
"""FTP 업로드 (표준 라이브러리만 사용, 비밀번호는 출력하지 않음)
사용: python3 _tools/ftp_deploy.py <로컬폴더> <서버폴더> [--dry-run]
환경변수: FTP_SERVER, FTP_USERNAME, FTP_PASSWORD (FTP_PORT 선택)
- 서버에 없는 폴더는 한 단계씩 만들고, 이미지·PDF 등은 크기가 같으면 건너뜁니다.
- HTML·설정·스크립트류는 크기가 같아도 항상 다시 올립니다. 서버 쪽 파일은 지우지 않습니다."""
import ftplib, os, posixpath, sys, time

TEXT = ('.html', '.htaccess', '.xml', '.json', '.js', '.css', '.txt', '.webmanifest', '.svg')
args = [a for a in sys.argv[1:] if not a.startswith('--')]
DRY = '--dry-run' in sys.argv
if len(args) != 2:
    sys.exit(__doc__)
LOCAL, REMOTE = os.path.abspath(args[0]), '/' + args[1].strip('/')
HOST, USER, PW = (os.environ.get(k, '') for k in ('FTP_SERVER', 'FTP_USERNAME', 'FTP_PASSWORD'))
PORT = int(os.environ.get('FTP_PORT') or 21)
if not (HOST and USER and PW):
    sys.exit('FTP_SERVER / FTP_USERNAME / FTP_PASSWORD 가 비어 있습니다 (Secrets 확인)')

ftp = None
def connect():
    global ftp
    try:
        if ftp: ftp.close()
    except Exception:
        pass
    ftp = ftplib.FTP(timeout=60)
    ftp.encoding = 'utf-8'
    ftp.connect(HOST, PORT)
    ftp.login(USER, PW)
    ftp.set_pasv(True)
    ftp.voidcmd('TYPE I')

def retry(fn, *a):
    for i in range(4):
        try:
            return fn(*a)
        except ftplib.error_perm:
            raise
        except (ftplib.Error, OSError, EOFError) as e:
            if i == 3: raise
            print(f'  재시도 {i+1}: {type(e).__name__}', flush=True)
            time.sleep(2 * (i + 1)); connect()

def remote_list(d):
    """서버 폴더의 {이름: 크기 또는 None(폴더)} / 폴더가 없으면 None
    존재 여부는 CWD로 먼저 확인하고(서버마다 목록 명령 응답이 달라서), 목록은 MLSD → NLST 순으로 시도"""
    try:
        ftp.cwd(d)
    except ftplib.error_perm:
        return None
    finally:
        try: ftp.cwd(HOME)
        except Exception: pass
    try:
        out = {}
        for name, f in ftp.mlsd(d, facts=['type', 'size']):
            t = f.get('type', '')
            if t in ('cdir', 'pdir'): continue
            out[name] = int(f['size']) if t == 'file' and 'size' in f else None
        return out
    except ftplib.error_perm:                                    # MLSD 미지원/거부: 이름만 받아 SIZE로 확인
        out = {}
        try: names = ftp.nlst(d)
        except ftplib.error_perm: return {}                      # 비어 있는 폴더도 550을 주는 서버가 있음
        for n in names:
            n = posixpath.basename(n)
            if n in ('.', '..', ''): continue
            try: out[n] = ftp.size(posixpath.join(d, n))
            except ftplib.error_perm: out[n] = None
        return out

def ensure_dir(d, cache):
    if d in cache: return cache[d]
    lst = retry(remote_list, d)
    if lst is None:
        if d == REMOTE:
            sys.exit(f'서버에 {REMOTE} 폴더가 없습니다 (경로 확인 필요)')
        ensure_dir(posixpath.dirname(d), cache)
        print(f'폴더 만들기 {d}', flush=True)
        if not DRY: retry(ftp.mkd, d)
        lst = {}
    cache[d] = lst
    return lst

def upload(lp, rp):
    def go():
        with open(lp, 'rb') as fh: ftp.storbinary('STOR ' + rp, fh)
    retry(go)

connect()
HOME = ftp.pwd()
found = None
for cand in dict.fromkeys([REMOTE, REMOTE.lstrip('/'), posixpath.join(HOME, REMOTE.lstrip('/'))]):
    try:
        ftp.cwd(cand); ftp.cwd(HOME); found = cand; break
    except ftplib.error_perm as e:
        print(f'  경로 확인 실패 {cand!r}: {e}', flush=True)
if found is None:
    try: names = sorted(ftp.nlst())
    except ftplib.error_perm: names = []
    sys.exit(f'서버에서 {REMOTE} 폴더를 찾지 못했습니다. 접속 위치={HOME!r}, 그 안의 항목={[n for n in names if not n.startswith(".")]}')
REMOTE = found
print('접속 성공' + (' (미리보기: 서버에 올리지 않음)' if DRY else ''), flush=True)
cache, up, skip, fail, size = {}, 0, 0, [], 0
for dp, dirs, files in os.walk(LOCAL):
    dirs.sort()
    rel = os.path.relpath(dp, LOCAL)
    rdir = REMOTE if rel == '.' else posixpath.join(REMOTE, *rel.split(os.sep))
    lst = ensure_dir(rdir, cache)
    for f in sorted(files):
        lp, rp = os.path.join(dp, f), posixpath.join(rdir, f)
        ls = os.path.getsize(lp)
        if lst.get(f) == ls and not f.lower().endswith(TEXT):
            skip += 1; continue
        try:
            print(('올릴 파일 ' if DRY else '올리는 중 ') + rp + f'  ({ls:,}B)', flush=True)
            if not DRY: upload(lp, rp)
            up += 1; size += ls
        except Exception as e:
            fail.append(rp); print(f'  실패: {rp}: {e}', flush=True)
print(f'완료: 올림 {up}개 ({size/1048576:.1f}MB), 건너뜀 {skip}개, 실패 {len(fail)}개')
try: ftp.quit()
except Exception: pass
sys.exit(1 if fail else 0)
