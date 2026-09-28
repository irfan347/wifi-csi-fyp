from pathlib import Path
import struct,zlib
for port in ['com6','com7']:
 raw=Path(f'work/esp32/{port}-config-20260919.bin').read_bytes()
 partitions=[]
 for off in range(0,0xc00,32):
  entry=raw[off:off+32]
  if entry[:2]!=b'\xaa\x50':break
  _,t,s,start,size,name,flags=struct.unpack('<HBBII16sI',entry)
  if name.split(b'\0')[0]==b'nvs':partitions.append((start,size))
 assert partitions==[(0x9000,0x6000)]
 original=raw[4096:];b=bytearray(original);entries=[]
 for p in range(0,len(b),4096):
  if struct.unpack_from('<I',b,p)[0]==0xffffffff:continue
  i=0
  while i<126:
   status=(b[p+32+i//4]>>((i%4)*2))&3;o=p+64+i*32;e=b[o:o+32]
   if status==2:
    assert struct.unpack_from('<I',e,4)[0]==zlib.crc32(e[:4]+e[8:],0xffffffff)
    entries.append((o,e,e[8:24].split(b'\0')[0]));i+=e[2]
   else:i+=1
 ns=[e[24] for o,e,k in entries if e[0]==0 and k==b'csi_cfg'];assert len(ns)==1
 matches=[(o,e) for o,e,k in entries if e[0]==ns[0] and k==b'target_ip'];assert len(matches)==1
 o,e=matches[0];assert e[1]==0x21 and e[2]==2
 length=struct.unpack_from('<H',e,24)[0];old=b[o+32:o+32+length]
 assert zlib.crc32(old,0xffffffff)==struct.unpack_from('<I',e,28)[0]
 data=b'10.86.105.192\0'
 struct.pack_into('<H',e,24,len(data));struct.pack_into('<I',e,28,zlib.crc32(data,0xffffffff));struct.pack_into('<I',e,4,zlib.crc32(e[:4]+e[8:],0xffffffff))
 b[o:o+32]=e;b[o+32:o+64]=data+b'\xff'*(32-len(data))
 assert all(x==y or o<=j<o+64 for j,(x,y) in enumerate(zip(original,b)))
 Path(f'work/esp32/{port}-updated-20260919.bin').write_bytes(b)
 print(port,'destination:',old.rstrip(b'\0').decode(),'->',data.rstrip(b'\0').decode(),'; all other bytes preserved')
