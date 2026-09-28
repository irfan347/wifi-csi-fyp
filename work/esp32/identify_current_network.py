import serial,time
ports=[]
try:
 for name in ['COM6','COM9']:
  s=serial.Serial();s.port=name;s.baudrate=115200;s.timeout=.1;s.dtr=False;s.rts=False;s.open();ports.append(s)
  s.rts=True;time.sleep(.15);s.rts=False
 end=time.monotonic()+18
 while time.monotonic()<end:
  for s in ports:
   line=s.readline().decode(errors='replace').strip()
   if any(x in line for x in ['target_ip=','filter_mac=','connected with','Got IP:','CSI streaming active','Node ID:']): print(s.port,line,flush=True)
finally:
 for s in ports:s.close()
