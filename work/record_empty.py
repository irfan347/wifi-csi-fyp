import argparse, datetime, json, pathlib, time, urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--label', choices=['empty', 'person_still', 'person_walking'], default='empty')
parser.add_argument('--setup-id', default='legacy_unfiltered')
parser.add_argument('--filter-mac', default=None)
args = parser.parse_args()

base = 'http://127.0.0.1:3000'
def api(path, data=None):
    payload = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(base + path, data=payload, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=8) as response:
        return json.load(response)

stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
rid = ('empty_room' if args.label == 'empty' else args.label) + '_' + stamp
if args.setup_id != 'legacy_unfiltered':
    assert all(c.isalnum() or c in '_-' for c in args.setup_id)
    rid = args.setup_id + '_' + rid
meta = {'id':rid, 'label':args.label, 'label_source':'user confirmation in conversation; not inferred from dashboard predictions', 'requested_seconds':120, 'checks':[]}
meta.update(setup_id=args.setup_id, filter_mac=args.filter_mac)
destination = pathlib.Path('work/ruview-data/recordings')
destination.mkdir(parents=True, exist_ok=True)
manifest = destination / (rid + '.metadata.json')
nodes = api('/api/v1/nodes')
assert {n['node_id'] for n in nodes['nodes'] if n['status']=='active' and n['last_seen_ms']<2000} >= {1,2}, 'Both nodes must be live'
started = False
try:
    result = api('/api/v1/recording/start', {'id':rid})
    print('START', json.dumps(result), flush=True)
    if result.get('success') is not True:
        raise RuntimeError('Recording start not confirmed')
    started = True
    begin = time.monotonic()
    meta['started_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for checkpoint in (30,60,90,120):
        time.sleep(max(0, begin + checkpoint - time.monotonic()))
        if checkpoint < 120:
            try:
                status = api('/api/v1/nodes')
                check = {'elapsed_seconds':round(time.monotonic()-begin,1), 'nodes':status}
                meta['checks'].append(check)
                print('PROGRESS', json.dumps(check), flush=True)
            except Exception as error:
                meta['checks'].append({'elapsed_seconds':checkpoint,'error':str(error)})
finally:
    if started:
        try:
            result = api('/api/v1/recording/stop', {})
            meta['stop_result'] = result
            meta['elapsed_seconds'] = round(time.monotonic()-begin,2)
            print('STOP', json.dumps(result), flush=True)
        except Exception as error:
            meta['stop_error'] = str(error)
            print('STOP FAILED', str(error), flush=True)
    manifest.write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print('METADATA', str(manifest), flush=True)
