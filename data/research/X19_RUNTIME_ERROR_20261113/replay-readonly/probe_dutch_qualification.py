"""Bounded FM08 Dutch qualification snapshot. OpenProcess(0x410) only.
No process write, suspend, debugger, remote call, launch, or old heap addresses.
Root invokes against a user-loaded paused diagnostic replay; output is exclusive.
"""
from pathlib import Path
import argparse, ctypes, datetime, hashlib, json, os, struct, sys, time
sys.dont_write_bytecode = True
ROOT = Path('J:/FM08dev')
BASE = Path(__file__).resolve().parent
EXPECTED = '157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
U32 = lambda b, o=0: struct.unpack_from('<I', b, o)[0]
I32 = lambda b, o=0: struct.unpack_from('<i', b, o)[0]
I16 = lambda b, o=0: struct.unpack_from('<h', b, o)[0]
I8 = lambda b, o=0: struct.unpack_from('<b', b, o)[0]
def require(v, why):
    if not v: raise ValueError(why)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
class Memory:
    def __init__(self, pid):
        require(os.name == 'nt' and pid > 0, 'explicit fresh Windows PID required')
        self.pid=pid; self.k=ctypes.WinDLL('kernel32',use_last_error=True)
        k=self.k
        k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];k.OpenProcess.restype=ctypes.c_void_p
        k.ReadProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.ReadProcessMemory.restype=ctypes.c_int
        k.CloseHandle.argtypes=[ctypes.c_void_p]
        k.QueryFullProcessImageNameW.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_uint32)]
        k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(ctypes.c_uint64)]*4
        k.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)]
        self.h=k.OpenProcess(0x410,False,pid);require(self.h,'OpenProcess QUERY_INFORMATION|VM_READ denied')
        self.reads=0;self.total=0;self.started=time.monotonic();self.watch={}
        self.before=self.identity();require(self.before['ImageSHA256']==EXPECTED,'unsupported image')
        require(self.read(0x400000,2)==b'MZ','unsupported image base')
        require(self.read(0x50e1a0,25)==bytes.fromhex('8a44240484c07c113a41087d0c8b49040fbec08b0481c20400'),'signed-byte stage vector getter bytes')
    def identity(self):
        p=ctypes.create_unicode_buffer(32768);n=ctypes.c_uint32(len(p))
        require(self.k.QueryFullProcessImageNameW(self.h,0,p,ctypes.byref(n)),'image query failed')
        vals=[ctypes.c_uint64() for _ in range(4)]
        require(self.k.GetProcessTimes(self.h,*[ctypes.byref(x) for x in vals]),'process times failed')
        code=ctypes.c_uint32();require(self.k.GetExitCodeProcess(self.h,ctypes.byref(code)) and code.value==259,'process exited')
        return dict(PID=self.pid,CreationFileTime=vals[0].value,Image=p.value,ImageSHA256=sha(Path(p.value)),ExitCode=code.value)
    def read(self,a,n,watch=False):
        require(0x10000<=a and 0<n<=1048576 and a+n<=0x80000000,'read bounds')
        require(self.reads<40000 and self.total+n<=32*1024*1024 and time.monotonic()-self.started<90,'bounded capture budget exceeded')
        b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
        require(self.k.ReadProcessMemory(self.h,ctypes.c_void_p(a),b,n,ctypes.byref(got)) and got.value==n,'unreadable '+hex(a))
        self.reads+=1;self.total+=n
        if watch:
            key=(a,n)
            require(key not in self.watch or self.watch[key]==b.raw,'changed during capture '+hex(a))
            self.watch[key]=b.raw
        return b.raw
    def u32(self,a,watch=False): return U32(self.read(a,4,watch))
    def close(self):
        if self.h:self.k.CloseHandle(self.h);self.h=None
    def rtti(self,a):
        vt=self.u32(a);loc=self.u32(vt-4);sig,off,cd,td,chd=struct.unpack('<IIIII',self.read(loc,20))
        require(sig==0 and cd==0 and 0x400000<=td<0x2000000 and off<0x2000,'RTTI guard')
        name=self.read(td+8,128).split(b'\x00')[0].decode('ascii')
        return dict(Type=name,VTable=vt,CompleteObject=a-off,SubobjectOffset=off)
    def uid(self,a):
        require(self.u32(self.u32(a)+0x10)==0x1096c90,'UID getter guard')
        return self.u32(a+0x14)
    def text(self,obj):
        if not obj:return None
        b=self.read(obj,12);n=struct.unpack_from('<H',b,4)[0]
        require(n<=1000,'string length');return self.read(U32(b,8),n*2).decode('utf-16le') if n else ''

def registry(m,address):
    root=m.u32(address,True);col=m.u32(root+4,True)
    require(m.u32(m.u32(col)+0x2c)==0xf9a0d0,'registry vector getter')
    count=m.u32(col+8,True);require(0<count<=100000,'registry count')
    ptrs=bytearray(m.read(m.u32(col+4,True),count*4,True))
    active=m.u32(root+0x18,True);require(active<=count,'active prefix count')
    if active:
        require(m.u32(m.u32(root+0x10)+0x2c)==0xf9a0d0,'active vector getter')
        ptrs[:active*4]=m.read(m.u32(root+0x14,True),active*4,True)
    return dict(Address=root,Collection=col,Count=count,ActivePrefix=active),struct.unpack('<'+'I'*count,ptrs)

def settings(m,a):
    b=m.read(a,0xc0,True)
    return dict(Address=a,RTTI=m.rtti(a),RawHex=b.hex(),Teams=I8(b,0xb),GamesLimit=I8(b,0x10),FlagsC=U32(b,0xc),Quota14_17=[I8(b,i) for i in range(0x14,0x18)],PeriodStageIndex=I8(b,0x2f),Field2E=I8(b,0x2e))

def team(m,a):
    b=m.read(a,0x70,True);require(m.rtti(a)['Type']=='.?AVTEAM@@','not TEAM')
    uid=m.uid(a);family=U32(b,0x38)
    out=dict(Address=a,UID=uid,Name=m.text(U32(b,0x24)),RawHex=b.hex(),RuntimeTeamKind3C=I8(b,0x3c),FamilyOrNationMode40=I8(b,0x40),RawField3C=U32(b,0x3c),FamilyPointer=family,CurrentCOMP=m.uid(U32(b,0x54)) if U32(b,0x54) else None)
    # C9DCE0: physical family member vector and predecessor. Do not equate
    # legal superior, preceding sibling, and sporting parent.
    if I8(b,0x40)==0:
        f=m.read(family,0x70,True);n=I8(f,0x6c);require(0<=n<=64,'family member bound')
        out['FamilyVectorGetter']=m.u32(U32(f,0x64)+0x2c) if n else None
        arr=struct.unpack('<'+'I'*n,m.read(U32(f,0x68),n*4,True)) if n else []
        out['FamilyMembers']=[dict(Address=p,UID=m.uid(p),RuntimeTeamKind3C=I8(m.read(p+0x3c,1)),CurrentCOMP=m.uid(m.u32(p+0x54)) if m.u32(p+0x54) else None) for p in arr]
        out['SportingParentInterpretation']='family first/predecessor captured; not inferred from alias'
    else:out['FamilyInterpretation']='runtime40 nonzero: raw38 may be nation, not FAMILY'
    return out

def stage(m,a,index,owner,depth=0):
    require(depth<=2,'stage recursion bound')
    b=m.read(a,0x54,True);rt=m.rtti(a);typ=rt['Type'];out=dict(Index=index,Address=a,OwnerCOMPUID=owner,RTTI=rt,RawHeaderHex=b.hex(),StageParent=m.uid(U32(b,0x30)) if U32(b,0x30) else None)
    if typ=='.?AVLEAGUE_STAGE@@':
        require(m.u32(rt['VTable']+8)==0xdd3330,'LEAGUE_STAGE status getter not DD3330')
        s=settings(m,U32(b,0x3c));out['Settings']=s;n=s['Teams'];require(0<=n<=64,'league row bound')
        out['Dirty43']=b[0x43];out['Field20']=b[0x20];out['Field21']=b[0x21];out['Field42']=b[0x42];out['Field50']=I16(b,0x50)
        if I16(b,0x50)!=0:out['PureStatus']=dict(Value=0,Proof='DD3330 short[stage+50]!=0 first return')
        elif b[0x20]!=0:out['PureStatus']=dict(Value=2,Proof='DD3330 byte[stage+20]!=0 returns2; no side effects executed')
        else:out['PureStatus']=dict(Value=None,Proof='UNKNOWN: remaining DD3330 may mutate state; never invoked')
        table=U32(b,0x34);raw=m.read(table,n*0x50,True) if n else b'';rows=[]
        for i in range(n):
            q=raw[i*0x50:(i+1)*0x50];t=team(m,U32(q));rows.append(dict(Row=i,RawHex=q.hex(),TEAM=t,Rank40=q[0x40],Rank41=q[0x41],Flags42=struct.unpack_from('<H',q,0x42)[0],Games14=q[0x14],Fate4C=q[0x4c],FateLock4D=I8(q,0x4d),QualFlags4E=q[0x4e],QualLock4F=I8(q,0x4f),NormalPromotionBlocked=bool(q[0x42]&9)))
        out['TableAddress']=table;out['Rows']=rows
        # LEAGUE_SETTINGS action vector: DC7220 appends via settings+B4.
        ac=I8(m.read(s['Address']+0xbc,1,True));require(0<=ac<=32,'fate action bound')
        out['FateActionCount']=ac;acts=[]
        for p in struct.unpack('<'+'I'*ac,m.read(m.u32(s['Address']+0xb8,True),ac*4,True)) if ac else []:
            acts.append(dict(Address=p,RTTI=m.rtti(p),RawHex=m.read(p,0x1c,True).hex()))
        out['FateActions']=acts
    elif typ=='.?AVGROUP_STAGE@@':
        n=I8(b,0x48);require(0<=n<=32,'group child bound')
        require(m.u32(U32(b,0x40)+0x2c)==0x50e1a0,'group child signed-byte vector getter')
        children=struct.unpack('<'+'I'*n,m.read(U32(b,0x44),n*4,True)) if n else []
        out['ChildCount']=n;out['Children']=[stage(m,p,i,owner,depth+1) for i,p in enumerate(children)]
    else:out['DecodeGap']='OTHER_STAGE raw header only'
    return out

def capture(m):
    date=m.read(0x1b1ee14,5,True);day,year=struct.unpack_from('<HH',date);require(1900<=year<9999 and day<(366 if year%4==0 and(year%100!=0 or year%400==0)else 365),'calendar format')
    reg,ptrs=registry(m,0x1b1ece4);comps=[]
    for idx,p in enumerate(ptrs):
        if not p:continue
        uid=m.u32(p+0x14)
        if uid not in (29,30):continue
        require(m.uid(p)==uid and m.u32(p+0x18)==idx,'COMP identity/index guard')
        b=m.read(p,0xd8,True);n=I8(b,0xd4);require(0<=n<=32,'COMP stage count')
        require(m.u32(U32(b,0xcc)+0x2c)==0x50e1a0,'COMP stage signed-byte vector getter')
        arr=struct.unpack('<'+'I'*n,m.read(U32(b,0xd0),n*4,True)) if n else []
        comps.append(dict(UID=uid,Address=p,Index=idx,RTTI=m.rtti(p),Name=m.text(U32(b,0x3c)),RawHex=b.hex(),StageCount=n,Stages=[stage(m,a,i,uid) for i,a in enumerate(arr)]))
    require(sorted(x['UID'] for x in comps)==[29,30],'both COMP29/30 required once')
    return dict(CalendarRawHex=date.hex(),Date=(datetime.date(year,1,1)+datetime.timedelta(days=day)).isoformat(),CompetitionRegistry=reg,Competitions=comps)

def summarize(cap):
    c=next(x for x in cap['Competitions'] if x['UID']==30);s=next(x for x in c['Stages'] if x['RTTI']['Type']=='.?AVLEAGUE_STAGE@@');ps=s['Settings']['PeriodStageIndex'];groups=[g for g in c['Stages'] if g['Index']==ps and g['RTTI']['Type']=='.?AVGROUP_STAGE@@'];retained=sum(r['Fate4C']==2 and r['FateLock4D']!=0 for r in s['Rows']);out=dict(ActualSettingsQUALQuota=s['Settings']['Quota14_17'][1],RetainedFate2=retained,ReservationEnabled=bool(s['Settings']['FlagsC']&0x20),Dirty43=s['Dirty43'],PeriodGroupFound=len(groups)==1,Warning='Read-only captured state; DD0B70/DC0F10 not executed. Not proof of later decision ordering.')
    if len(groups)==1:
        ch=groups[0]['Children'];values=[x.get('PureStatus',{}).get('Value') for x in ch];out['PeriodPureStatusValues']=values;out['PeriodStatusUnknownCount']=values.count(None);out['Status0LowerBound']=values.count(0);out['Status0UpperBound']=values.count(0)+values.count(None)
        out['RemainingQUALInterval']=[out['ActualSettingsQUALQuota']-retained-z for z in (out['Status0UpperBound'],out['Status0LowerBound'])] if out['ReservationEnabled'] else [out['ActualSettingsQUALQuota']-retained]*2
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pid',required=True,type=int);ap.add_argument('--output',required=True,type=Path);args=ap.parse_args()
    out=args.output.resolve();require(out.parent==BASE and not out.exists(),'exclusive output inside replay-readonly required')
    m=None;res=dict(Status='FAIL_CAPTURE',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),ProcessAccess='OpenProcess 0x410 QUERY_INFORMATION|VM_READ',NoProcessWrites=True,NoSuspend=True,NoRemoteCalls=True,NoDebugger=True,NoGameLaunch=True,UserPausedClaimNotIndependentlyVerified=True,ScriptSHA256=sha(Path(__file__)))
    try:
        m=Memory(args.pid);res['IdentityBefore']=m.before;cap=capture(m);res.update(cap);res['QualificationSummary']=summarize(cap)
        changed=[]
        for (a,n),b in list(m.watch.items()):
            if m.read(a,n)!=b:changed.append(dict(Address=a,Bytes=n))
        res['IdentityAfter']=m.identity();res['ChangedWatchedRegions']=changed;res['CalendarAfterHex']=m.read(0x1b1ee14,5).hex()
        require(res['IdentityBefore']==res['IdentityAfter'] and not changed and res['CalendarRawHex']==res['CalendarAfterHex'],'process/calendar/watched data changed; snapshot rejected')
        res['Status']='PASS_STABLE_READ_ONLY_SNAPSHOT'
    except Exception as e:res['CaptureGap']=type(e).__name__+': '+str(e)
    finally:
        if m:res.update(ReadCalls=m.reads,ReadBytes=m.total,ElapsedSeconds=round(time.monotonic()-m.started,3));m.close()
    with out.open('x',encoding='utf-8') as f:json.dump(res,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:res.get(k) for k in ('Status','Date','CaptureGap','QualificationSummary','ReadCalls','ReadBytes','ElapsedSeconds')},ensure_ascii=False));print('OUTPUT_SHA256',sha(out))
    return 0 if res['Status']=='PASS_STABLE_READ_ONLY_SNAPSHOT' else 2
if __name__=='__main__':raise SystemExit(main())
