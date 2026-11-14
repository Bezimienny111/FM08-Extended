import json,zlib,bisect,functools,struct,hashlib
from pathlib import Path
BASE=Path('FmLauncher/data/research/R2_RUNTIME_FAILURE_20261111/root-readonly/memory-regions')
class OfflineMemory:
 def __init__(self):
  self.rows=sorted(json.loads((BASE/'index.json').read_text(encoding='utf-8'))['records'],key=lambda r:r['base']);self.starts=[r['base']for r in self.rows]
 @functools.lru_cache(maxsize=32)
 def chunk(self,i):
  r=self.rows[i];d=zlib.decompress((BASE/r['file']).read_bytes());assert len(d)==r['size'];assert hashlib.sha256(d).hexdigest()==r['sha256'];return d
 def read(self,a,n):
  out=b''
  while n:
   i=bisect.bisect_right(self.starts,a)-1
   if i<0:raise ValueError(hex(a))
   r=self.rows[i];off=a-r['base']
   if off>=r['size']:raise ValueError(hex(a))
   count=min(n,r['size']-off);out+=self.chunk(i)[off:off+count];a+=count;n-=count
  return out
 def u(self,a):return struct.unpack('<I',self.read(a,4))[0]
 def i(self,a):return struct.unpack('<i',self.read(a,4))[0]
 def bag(self,a):
  vt,ptr,n,cap=struct.unpack('<4I',self.read(a,16));assert vt==0x166a12c and 0<=n<=10000
  return [dict(address=p,tag=self.u(p+8).to_bytes(4,'big').decode('ascii','replace'),value=self.u(p),type=self.u(p+4),vtable=self.u(self.u(p+4)))for p in [self.u(ptr+4*i)for i in range(n)]]
