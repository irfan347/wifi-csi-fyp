import socket,time,collections
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
s.bind(('0.0.0.0',5005));s.settimeout(1)
counts=collections.Counter(); examples={};end=time.monotonic()+20
try:
 while time.monotonic()<end:
  try:
   data,addr=s.recvfrom(65535);counts[addr[0]]+=1
   examples.setdefault(addr[0],data[:24].hex(' '))
  except socket.timeout: pass
finally:s.close()
for ip,count in counts.items(): print(ip,'packets=',count,'header=',examples[ip])
if not counts:print('No packets received')
