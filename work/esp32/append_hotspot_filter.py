from pathlib import Path
import struct,zlib

def entries(b):
 out=[]
 for p in range(0,len(b),4096):
  if struct.unpack_from('<I',b,p)[0]==0xffffffff:continue
  i=0
  while i<126:
   state=(b[p+32+i//4]>>((i%4)*2))&3;o=p+64+32*i;e=b[o:o+32]
   if state==2:
    assert 1<=e[2]<=126-i
    assert struct.unpack_from('<I',e,4)[0]==zlib.crc32(e[:4]+e[8:],0xffffffff)
    out.append((o,e,e[8:24].split(b'\0')[0]));i+=e[2]
   else:i+=1
 return out
source=Path('work/esp32/filter-only.bin').read_bytes()
blobs=[(o,e) for o,e,k in entries(source) if k==b'filter_mac']
assert [e[1] for o,e in blobs]==[0x42,0x48]
assert source[blobs[0][0]+32:blobs[0][0]+38]==bytes.fromhex('8a1f6d535333')
for port in ['com6','com7']:
 raw=Path(f'work/esp32/{port}-config-20260920.bin').read_bytes()
 parts=[]
 for off in range(0,0xc00,32):
  e=raw[off:off+32]
  if e[:2]!=b'\xaa\x50':break
  _,t,s,a,n,key,flags=struct.unpack('<HBBII16sI',e)
  if key.split(b'\0')[0]==b'nvs':parts.append((a,n))
 assert parts==[(0x9000,0x6000)]
 original=raw[4096:];b=bytearray(original);es=entries(b)
 ns=[e[24] for o,e,k in es if e[0]==0 and k==b'csi_cfg'];assert len(ns)==1
 assert not any(e[0]==ns[0] and k==b'filter_mac' for o,e,k in es)
 active=[p for p in range(0,len(b),4096) if struct.unpack_from('<I',b,p)[0]==0xfffffffe];assert len(active)==1;p=active[0]
 used=[i for i in range(126) if ((b[p+32+i//4]>>((i%4)*2))&3)!=3];index=max(used,default=-1)+1
 assert index+sum(e[2] for o,e in blobs)<=126
 allowed=set()
 for src,e in blobs:
  span=e[2];chunk=bytearray(source[src:src+span*32]);chunk[0]=ns[0]
  struct.pack_into('<I',chunk,4,zlib.crc32(chunk[:4]+chunk[8:32],0xffffffff))
  dst=p+64+index*32;assert b[dst:dst+len(chunk)]==b'\xff'*len(chunk)
  b[dst:dst+len(chunk)]=chunk;allowed.update(range(dst,dst+len(chunk)))
  for j in range(index,index+span):
   bitmap=p+32+j//4;b[bitmap]&=~(1<<((j%4)*2));allowed.add(bitmap)
  index+=span
 assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(original,b)))
 valid=entries(b);assert len([e for o,e,k in valid if k==b'filter_mac'])==2
 Path(f'work/esp32/{port}-filtered-20260920.bin').write_bytes(b)
 print(port,'appended hotspot filter; existing entries unchanged')
