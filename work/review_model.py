import pathlib,urllib.request,hashlib,json,struct
out=pathlib.Path('work/pretrained-review');out.mkdir(exist_ok=True)
rev='b24f225f1a8dd6f9614b7813b81df2cc26398269'
for name in ['config.json','presence-head.json','csi-embed-v2.py','csi-embed-v2-metrics.json','csi-embed-v2.safetensors','model.safetensors']:
 data=urllib.request.urlopen(f'https://huggingface.co/ruvnet/wifi-densepose-pretrained/resolve/{rev}/{name}',timeout=30).read();(out/name).write_bytes(data)
 print(name,len(data),hashlib.sha256(data).hexdigest())
 if name.endswith('.safetensors'):
  n=struct.unpack('<Q',data[:8])[0]; h=json.loads(data[8:8+n]);print({k:v.get('shape') for k,v in h.items() if k!='__metadata__'})
print((out/'csi-embed-v2.py').read_text())
print((out/'config.json').read_text())
print('presence-head keys',list(json.loads((out/'presence-head.json').read_text())))
