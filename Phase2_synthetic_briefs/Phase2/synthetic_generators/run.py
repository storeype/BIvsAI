import sys, json, subprocess, os
from briefs import ALL
from synlib import build
from openpyxl import load_workbook
REC='/root/.claude/skills/synced/0e3a9db2-e807-4390-8c3a-d46da7688164_b63a5743-b914-4b2e-a4f8-c6119225bc1e/xlsx/scripts/recalc.py'
OUT='/mnt/user-data/outputs/Phase2/'
res={}
for n in [int(x) for x in sys.argv[1:]] or ALL:
    cfg=ALL[n](); os.makedirs(OUT+cfg['slug'],exist_ok=True); path=OUT+cfg['slug']+'/'+cfg['file']
    lay=build(cfg,path)
    r=json.loads(subprocess.run(['python3',REC,path,'90'],capture_output=True,text=True).stdout)
    print(n, r.get('status'), r.get('total_formulas'), r.get('total_errors'), r.get('error_summary') if r.get('total_errors') else '')
    wb=load_workbook(path,data_only=True); sc=wb['Scores']; L=lay
    items=[]
    for i in range(L['R0'],L['RN']+1):
        row=[sc.cell(i,c).value for c in range(1,L['cDec']+1)]
        items.append(dict(name=row[0],crit=row[L['cC']-1:L['cC']-1+L['nC']],s=row[L['cS']-1:L['cS']-1+L['nC']],idx=row[L['cI']-1],rank=row[L['cR']-1],dec=row[L['cDec']-1]))
    se=wb['Sensitivity']; sens=[[se.cell(5+k,c).value for c in [1]+list(range(2+L['nC'],6+L['nC']))] for k in range(len(cfg['sens']))]
    g=wb['Generation_Log']; checks=[[g.cell(r_,c).value for c in range(1,6)] for r_ in range(1,g.max_row+1) if g.cell(r_,5).value in ('PASS','CHECK')]
    summ=[[sc.cell(r_,1).value,sc.cell(r_,3).value] for r_ in range(L['RN']+4,L['RN']+9) if sc.cell(r_,1).value]
    res[n]=dict(items=items,sens=sens,checks=checks,summary=summ,crit=[c['label'] for c in cfg['criteria']],w=[x[2] for x in cfg['inputs'][:5]])
    for it in sorted(items,key=lambda x:x['rank'])[:8]: print('  ',it['rank'],it['name'],round(it['idx'],1),it['dec'])
    print('  sens',sens); print('  checks',[(c[0][:40],round(c[1],2),round(c[2],2),c[4]) for c in checks]); print('  summ',summ)
old=json.load(open('synres.json')) if os.path.exists('synres.json') else {}
old.update({str(k):v for k,v in res.items()}); json.dump(old,open('synres.json','w'),default=str)
