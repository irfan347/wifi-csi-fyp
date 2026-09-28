import json, pathlib, math, statistics, collections, datetime
ROOT=pathlib.Path(__file__).resolve().parents[2]
DATA=ROOT/'work/ruview-data/recordings'
OUT=ROOT/'outputs/csi-preliminary'; OUT.mkdir(parents=True,exist_ok=True)
CACHE=ROOT/'work/csi-window-cache.json'

def stats(v):
    return [statistics.fmean(v),statistics.pstdev(v)]

def extract():
    rows=[];audit=[]; excluded=[]
    for path in sorted(DATA.glob('*.jsonl')):
        mp=path.with_suffix('.metadata.json')
        if not mp.exists():excluded.append({'file':path.name,'reason':'No confirmed label metadata'});continue
        m=json.loads(mp.read_text(encoding='utf8'))
        if m.get('usable_for_training') is False or not m.get('stop_result',{}).get('success'):
            excluded.append({'file':path.name,'reason':m.get('reason','No confirmed successful stop')});continue
        label=m['label'];bins={};count=bad=0;first=last=None;nodecounts=collections.Counter();lengths=collections.Counter();pred=collections.Counter()
        for line in path.open(encoding='utf8'):
            try:r=json.loads(line)
            except (ValueError,UnicodeError):bad+=1;continue
            if r.get('source')!='esp32' or not isinstance(r.get('timestamp'),(float,int)):continue
            t=r['timestamp'];first=t if first is None else first;last=t;count+=1
            pred[str(r.get('classification',{}).get('presence'))]+=1
            for node in r.get('nodes',[]):
                nid=node.get('node_id')
                if nid not in (1,2):continue
                nodecounts[nid]+=1
                a=node.get('amplitude',[]);lengths[len(a)]+=1
                if not a or any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in a):continue
                # Discard transitions; fixed 2 s bins, no overlap.
                elapsed=t-first
                if not 10<=elapsed<114:continue
                nf=next((x for x in r.get('node_features',[]) if x.get('node_id')==nid),{})
                if nf.get('stale',False) or nf.get('last_seen_ms',0)>500:continue
                rss=node.get('rssi_dbm')
                if not isinstance(rss,(int,float)) or not math.isfinite(rss):continue
                # Signal values only: no inferred presence, counts, pose, vitals, timestamps or node position as predictors.
                ordered=sorted(a); n=len(a)
                vec=[rss,statistics.fmean(a),statistics.pstdev(a),ordered[int(.1*(n-1))],ordered[int(.9*(n-1))],sum(x==0 for x in a)/n]
                bucket=bins.setdefault(int((elapsed-10)//2),{1:[],2:[]})
                bucket[nid].append(vec)
        for key,bucket in sorted(bins.items()):
            if min(len(bucket[1]),len(bucket[2]))<10:continue
            features=[]
            for nid in (1,2):
                for col in zip(*bucket[nid]):features.extend(stats(col))
            rows.append({'session':path.stem,'label':label,'window':key,'x':features})
        audit.append({'session':path.stem,'label':label,'frames':count,'malformed_lines':bad,'duration_seconds':None if first is None else last-first,'node_frames':dict(nodecounts),'amplitude_lengths':dict(lengths),'dashboard_presence_counts':dict(pred),'windows':sum(x['session']==path.stem for x in rows)})
        print('AUDIT',json.dumps(audit[-1]),flush=True)
    result={'rows':rows,'audit':audit,'excluded':excluded}
    CACHE.write_text(json.dumps(result),encoding='utf8')
    return result

if __name__=='__main__':
    import sys
    d=json.loads(CACHE.read_text()) if '--cached' in sys.argv and CACHE.exists() else extract()
    if '--extract-only' in sys.argv:sys.exit()
    import numpy as np, sklearn, joblib
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.dummy import DummyClassifier
    from sklearn.metrics import accuracy_score,balanced_accuracy_score,confusion_matrix,classification_report
    rows=d['rows'];X=np.array([r['x'] for r in rows]);sessions=np.array([r['session'] for r in rows])
    classes=['empty','person_still','person_walking']
    grouped={label:sorted({r['session'] for r in rows if r['label']==label}) for label in classes}
    assert all(len(v)>=3 for v in grouped.values()),grouped
    folds=[]
    def model():return RandomForestClassifier(n_estimators=200,max_depth=8,min_samples_leaf=5,class_weight='balanced',random_state=42,n_jobs=1)
    for task in ['three_conditions','presence']:
        y=np.array([r['label'] if task=='three_conditions' else ('empty' if r['label']=='empty' else 'occupied') for r in rows])
        labels=classes if task=='three_conditions' else ['empty','occupied']
        allpred=np.empty(len(y),dtype=object)
        for fold in range(3):
            held=[grouped[c][fold] for c in classes]; test=np.isin(sessions,held);train=~test
            assert not set(sessions[train])&set(sessions[test])
            clf=model().fit(X[train],y[train]);p=clf.predict(X[test]);allpred[test]=p
            dummy=DummyClassifier(strategy='most_frequent').fit(X[train],y[train])
            folds.append({'task':task,'fold':fold+1,'held_out_sessions':held,'train_windows':int(train.sum()),'test_windows':int(test.sum()),'accuracy':accuracy_score(y[test],p),'balanced_accuracy':balanced_accuracy_score(y[test],p),'dummy_accuracy':accuracy_score(y[test],dummy.predict(X[test])),'labels':labels,'confusion_matrix':confusion_matrix(y[test],p,labels=labels).tolist()})
        final=model().fit(X,y)
        joblib.dump({'model':final,'feature_names':[f'node{nid}_{v}_{s}' for nid in (1,2) for v in ['rssi','amplitude_mean','amplitude_std','amplitude_p10','amplitude_p90','zero_fraction'] for s in ['window_mean','window_std']],'window_seconds':2,'labels':labels,'status':'preliminary; not deployed; training-session performance is not validation'},OUT/f'{task}-random-forest.joblib')
        print('RESULT',task,classification_report(y,allpred,labels=labels,zero_division=0),flush=True)
        d[task]={'accuracy':accuracy_score(y,allpred),'balanced_accuracy':balanced_accuracy_score(y,allpred),'labels':labels,'confusion_matrix':confusion_matrix(y,allpred,labels=labels).tolist(),'report':classification_report(y,allpred,labels=labels,output_dict=True,zero_division=0),'per_session':[{'session':s,'label':str(y[sessions==s][0]),'accuracy':accuracy_score(y[sessions==s],allpred[sessions==s])} for s in sorted(set(sessions))]}
    d.pop('rows');d['folds']=folds;d['sklearn_version']=sklearn.__version__;d['feature_count']=X.shape[1];d['total_windows']=len(X)
    (OUT/'evaluation.json').write_text(json.dumps(d,indent=2),encoding='utf8')

