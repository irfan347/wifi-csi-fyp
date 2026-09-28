from pathlib import Path
import struct,zlib
src=Path('work/esp32/com7-config-backup.bin').read_bytes()[4096:]
b=bytearray(src)
def crc(e):
 struct.pack_into('<I',e,4,zlib.crc32(e[:4]+e[8:],0xffffffff))
 return e
entries=[]
for p in range(0,len(b),4096):
 if struct.unpack_from('<I',b,p)[0]==0xffffffff: continue
 i=0
 while i<126:
  status=(b[p+32+i//4]>>((i%4)*2))&3
  o=p+64+i*32;e=b[o:o+32]
  if status==2:
   key=e[8:24].split(b'\0')[0].decode(errors='replace'); entries.append((p,i,o,e,key)); i+=e[2]
  else: i+=1
ns=[e[24] for p,i,o,e,k in entries if e[0]==0 and k=='csi_cfg']; assert len(ns)==1
ns=ns[0]
target=[x for x in entries if x[3][0]==ns and x[4]=='target_ip']; assert len(target)==1
p,i,o,e,k=target[0]; assert e[1]==0x21 and e[2]==2
oldlen=struct.unpack_from('<H',e,24)[0]
assert zlib.crc32(b[o+32:o+32+oldlen],0xffffffff)==struct.unpack_from('<I',e,28)[0]
data=b'172.22.241.192\0'; assert len(data)<=32
struct.pack_into('<H',e,24,len(data)); struct.pack_into('<I',e,28,zlib.crc32(data,0xffffffff))
b[o:o+32]=crc(e); b[o+32:o+64]=data+b'\xff'*(32-len(data))
assert not any(e[0]==ns and k=='node_id' for p,i,o,e,k in entries)
active=[p for p in range(0,len(b),4096) if struct.unpack_from('<I',b,p)[0]==0xfffffffe];assert len(active)==1
p=active[0]
used=[i for i in range(126) if ((b[p+32+i//4]>>((i%4)*2))&3)!=3];i=max(used)+1;assert i<126
o=p+64+i*32;assert b[o:o+32]==b'\xff'*32
e=bytearray(b'\xff'*32);e[0:4]=bytes([ns,1,1,255]);e[8:24]=b'node_id'+b'\0'*9;e[24]=2;b[o:o+32]=crc(e)
b[p+32+i//4]&=~(1<<((i%4)*2))
allowed=set(range(target[0][2],target[0][2]+64))|set(range(o,o+32))|{p+32+i//4}
assert all(a==c or j in allowed for j,(a,c) in enumerate(zip(src,b)))
Path('work/esp32/com7-config-updated.bin').write_bytes(b)
print('Prepared NVS update: target_ip=172.22.241.192, node_id=2; all other configuration bytes preserved.')
