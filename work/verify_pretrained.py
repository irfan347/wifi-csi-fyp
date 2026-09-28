import json,math,struct,pathlib
p=pathlib.Path('work/pretrained-review')
h=json.loads((p/'presence-head.json').read_text()); norm=math.sqrt(sum(w*w for w in h['weights']));lower=1/(1+math.exp(-(h['bias']-norm)))
print('Head input weights:',len(h['weights']),'bias:',h['bias'],'weight L2 norm:',norm)
print('Minimum sigmoid output for ANY unit-norm embedding:',lower)
b=(p/'model.safetensors').read_bytes();n=struct.unpack('<Q',b[:8])[0]
print('model.safetensors declared header bytes',n,'file bytes',len(b))
print('header end repr:',repr(b[8+n-40:8+n]))
v=(p/'csi-embed-v2.safetensors').read_bytes();m=struct.unpack('<Q',v[:8])[0];t=json.loads(v[8:8+m]); bad=0
for k,val in t.items():
 if val.get('dtype')=='F32':
  a,z=val['data_offsets'];arr=struct.unpack('<'+'f'*((z-a)//4),v[8+m+a:8+m+z]);bad+=sum(not math.isfinite(x) for x in arr)
print('V2 encoder nonfinite weights:',bad)
