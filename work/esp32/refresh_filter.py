from pathlib import Path
import struct,zlib
new=bytes.fromhex('1e2fa701d19c')
for port in ['com6','com7']:
 raw=Path(f'work/esp32/{port}-config-20260926.bin').read_bytes()
 partitions=[]
 for o in range(0,0xc00,32):
  e=raw[o:o+32]
  if e[:2]!=b'\xaa\x50':break
  _,t,s,a,n,k,f=struct.unpack('<HBBII16sI',e)
  if k.split(b'\0')[0]==b'nvs':partitions.append((a,n))
 assert partitions==[(0x9000,0x6000)]
 orig=raw[4096:];b=bytearray(orig);entries=[]
 for p in range(0,len(b),4096):
  if struct.unpack_from('<I',b,p)[0]==0xffffffff:continue
  i=0
  while i<126:
   state=(b[p+32+i//4]>>((i%4)*2))&3;o=p+64+i*32;e=b[o:o+32]
   if state==2:
    assert 1<=e[2]<=126-i
    assert struct.unpack_from('<I',e,4)[0]==zlib.crc32(e[:4]+e[8:],0xffffffff)
    entries.append((o,e,e[8:24].split(b'\0')[0]));i+=e[2]
   else:i+=1
 ns=[e[24] for o,e,k in entries if e[0]==0 and k==b'csi_cfg'];assert len(ns)==1
 targets=[(o,e) for o,e,k in entries if e[0]==ns[0] and k==b'filter_mac' and e[1]==0x42];assert len(targets)==1
 o,e=targets[0];assert e[2]==2 and struct.unpack_from('<H',e,24)[0]==6
 old=bytes(b[o+32:o+38]);assert zlib.crc32(old,0xffffffff)==struct.unpack_from('<I',e,28)[0]
 assert old==bytes.fromhex('8a1f6d535333')
 b[o+32:o+38]=new
 struct.pack_into('<I',e,28,zlib.crc32(new,0xffffffff));struct.pack_into('<I',e,4,zlib.crc32(e[:4]+e[8:],0xffffffff));b[o:o+32]=e
 allowed=set(range(o+4,o+8))|set(range(o+28,o+38))
 assert all(x==y or j in allowed for j,(x,y) in enumerate(zip(orig,b)))
 Path(f'work/esp32/{port}-filtered-20260926.bin').write_bytes(b)
 print(port,old.hex(':'),'->',new.hex(':'),'other settings preserved')
