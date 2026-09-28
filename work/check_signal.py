import urllib.request,json,time,collections,pathlib
samples=[];end=time.monotonic()+30
while time.monotonic()<end:
 try:
  with urllib.request.urlopen('http://127.0.0.1:3000/api/v1/sensing/latest',timeout=3) as f:r=json.load(f)
  samples.append({'timestamp':r.get('timestamp'),'nodes':[{'id':n['node_id'],'rssi':n.get('rssi_dbm'),'amplitude_len':len(n.get('amplitude',[])),'sync':n.get('sync',{})} for n in r.get('nodes',[])]})
 except Exception as e: samples.append({'error':str(e)})
 time.sleep(.2)
p=pathlib.Path('outputs/csi-preliminary/live-signal-check.json');p.write_text(json.dumps({'condition':'User confirms empty room; equipment unchanged','samples':samples},indent=2))
for nid in (1,2):
 v=[n['rssi'] for s in samples for n in s.get('nodes',[]) if n['id']==nid]
 print(nid,'samples',len(v),'range',min(v) if v else None,max(v) if v else None,'RSSI counts',collections.Counter(v).most_common(12))
