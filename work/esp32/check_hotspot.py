import serial,time
ports=[]
try:
 for name in ['COM6','COM7']:
  s=serial.Serial();s.port=name;s.baudrate=115200;s.timeout=.1;s.dtr=False;s.rts=False;s.open();ports.append(s)
  s.rts=True;time.sleep(.15);s.rts=False
 end=time.monotonic()+16
 while time.monotonic()<end:
  for s in ports:
   line=s.readline().decode(errors='replace').strip()
   if any(x in line for x in ['connected with','Got IP:','filter_mac','CSI streaming active','target_ip=','Node ID:']):print(s.port,line,flush=True)
finally:
 for s in ports:s.close()
