import pathlib,json,collections
p=pathlib.Path('work/ruview-data/recordings/person_still_20260919T170132Z.jsonl')
n=0;counts=collections.Counter();first=None;last=None
with p.open(encoding='utf8') as f:
 for line in f:
  r=json.loads(line);n+=1
  if first is None:first=r.get('timestamp')
  last=r.get('timestamp')
  for node in r.get('nodes',[]):counts[str(node.get('node_id'))]+=1
print(json.dumps({'frames':n,'bytes':p.stat().st_size,'node_frame_counts':dict(counts),'first_timestamp':first,'last_timestamp':last}))

