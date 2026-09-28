from pathlib import Path
import struct,zlib
b=Path('work/esp32/com7-config-backup.bin').read_bytes()
for o in range(0,0xc00,32):
 e=b[o:o+32]
 if e[:2]!=b'\xaa\x50': break
 _,t,s,off,size,label,flags=struct.unpack('<HBBII16sI',e)
 print('partition',label.split(b'\0')[0].decode(),hex(off),hex(size))
n=b[4096:]
for p in range(0,len(n),4096):
 page=n[p:p+4096]; state,seq=struct.unpack_from('<II',page)
 if state==0xffffffff: continue
 print('page',p,'state',hex(state),'seq',seq)
 i=0
 while i<126:
  status=(page[32+i//4]>>((i%4)*2))&3
  e=page[64+i*32:96+i*32]
  if status==2:
   key=e[8:24].split(b'\0')[0].decode('utf8',errors='replace')
   assert struct.unpack_from('<I',e,4)[0]==zlib.crc32(e[:4]+e[8:],0xffffffff)
   print('entry',i,'ns',e[0],'type',hex(e[1]),'span',e[2],'key',key)
   i+=e[2]
  else: i+=1
