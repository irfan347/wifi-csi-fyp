import urllib.request,json,pathlib
out=pathlib.Path('work/ml-wheels');out.mkdir(exist_ok=True)
for package in ['numpy','scipy','joblib','threadpoolctl','scikit-learn']:
 version={'numpy':'2.3.5','scipy':'1.16.3','scikit-learn':'1.7.2','joblib':'1.5.2','threadpoolctl':'3.6.0'}[package]
 meta=json.load(urllib.request.urlopen(f'https://pypi.org/pypi/{package}/{version}/json',timeout=20))
 wheels=[x for x in meta['urls'] if x['filename'].endswith('cp311-cp311-win_amd64.whl') or x['filename'].endswith('py3-none-any.whl') or x['filename'].endswith('py2.py3-none-any.whl')]
 assert len(wheels)==1,(package,[x['filename'] for x in wheels])
 f=wheels[0];print('Downloading',f['filename'],flush=True)
 b=urllib.request.urlopen(f['url'],timeout=60).read()
 import hashlib
 assert hashlib.sha256(b).hexdigest()==f['digests']['sha256']
 (out/f['filename']).write_bytes(b)
print('All wheel hashes verified',flush=True)

