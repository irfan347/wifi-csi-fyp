import serial,time
ports=[]
try:
 for name in ['COM6','COM7']:
  s=serial.Serial();s.port=name;s.baudrate=115200;s.timeout=0.1;s.dtr=False;s.rts=False
  try:s.open();ports.append(s)
  except Exception as e:print(name,str(e))
 end=time.monotonic()+14
 while time.monotonic()<end:
  for s in ports:
   line=s.readline().decode(errors='replace').strip()
   if any(t in line for t in ['target_ip=', 'Node ID:', 'Got IP:', 'CSI streaming active','CSI cb #100','sendto','Failed','Disconnected']):print(s.port,line,flush=True)
finally:
 for s in ports:s.close()
