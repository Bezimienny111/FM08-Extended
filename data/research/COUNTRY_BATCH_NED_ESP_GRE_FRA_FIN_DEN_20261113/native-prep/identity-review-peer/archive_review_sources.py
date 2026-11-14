"""Bounded review archival. Reuses existing HTTP cache function; no draft/DB/source-roster mutation."""
from pathlib import Path
import sys,json,hashlib,datetime,urllib.request,urllib.error,ast,concurrent.futures
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;ROOT=B.parents[5];R=ROOT/'FmLauncher/data/research';CACHE=B/'sources/http-cache';CACHE.mkdir(parents=True,exist_ok=True)
helper=ROOT/'FmLauncher/data/research/KITS_FC12_20261111/fc12_pipeline.py';tree=ast.parse(helper.read_text(encoding='utf-8-sig'));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='get');scope=dict(CACHE=CACHE,urllib=__import__('urllib'),digest=lambda b:hashlib.sha256(b).hexdigest());exec(compile(ast.Module(body=[node],type_ignores=[]),str(helper),'exec'),scope);get=scope['get']
urls=[('AFC','club_history','https://www.afc.nl/archief/'),('AFC','municipal_distinct_FC_Amsterdam','https://www.amsterdam.nl/stadsarchief/stukken/sport/blauw-wit/'),('Ilves','club_1931_Tammela','https://www.ilvesfootball.com/stadionin-paayhteistyokumppanit-mukana-vaalimassa-tammelan-perinteikasta-historiaa/'),('Ilves','historical_FM_UID','https://sortitoutsi.net/football-manager-2010/team/510307/ilves-tampere'),('Jazz','bankruptcy_separate_juniors','https://yle.fi/a/3-5968347'),('Jazz','federation_2024_identity','https://www-assets.palloliitto.fi/62562/1748415817-jalkapallokirja_2024.pdf'),('Riviera','municipal_rename_identity','https://www.villefranche-sur-mer.fr/association/riviera-fc/'),('Riviera','FFF_20250619_rename','https://media.fff.fr/uploads/documents/pv-cfps-19-juin-25-vok.pdf'),('Elo','club_history_current_2026','https://www.kuopionelo.fi/seura/5017/seura'),('Elo','men_first_team_2026','https://kuopionelo.jopox.fi/joukkueet/16921'),('Calvo','official_new2015','https://calvosotelopuertollano.es/el-club/'),('Calvo','contemporaneous_new2015','https://www.encastillalamancha.es/deportes-cat/el-proyecto-del-nuevo-club-de-futbol-de-puertollano-se-viste-de-largo/')]
def one(item):
 club,kind,url=item
 try:
  raw,p,reused=get(url,24*1024*1024);out=dict(Club=club,Kind=kind,URL=url,File=str(p.relative_to(B)),SHA256=hashlib.sha256(raw).hexdigest(),Bytes=len(raw),FetchedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Reused=reused,Status=200)
 except Exception as e:out=dict(Club=club,Kind=kind,URL=url,Status=getattr(e,'code',None),Error=type(e).__name__+': '+str(e),CheckedAt=datetime.datetime.now(datetime.timezone.utc).isoformat())
 print(json.dumps(out,ensure_ascii=False),flush=True);return out
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:ledger=list(pool.map(one,urls))
(B/'web-source-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(B/'http-helper-pin.json').write_text(json.dumps(dict(Source=str(helper.relative_to(ROOT)),SHA256=hashlib.sha256(helper.read_bytes()).hexdigest(),Reuse='Only existing get() function compiled with cache rooted in peer folder',MaxAdditionalDistinctURLsPerClub=2),indent=2),encoding='utf-8')
# Copy neither source plans nor native data; pin and extract only requested read-only witness rows.
N=B.parent;f=N/'native-world-identities.json';data=json.loads(f.read_text(encoding='utf-8'));uids={102884,859310,510307,810,33004788,5395280,514333,4212117,4212378};rows=[r for r in data if r['ClubUID'] in uids]
(B/'native-witness-extract.json').write_text(json.dumps(dict(Source=str(f.relative_to(ROOT)),SHA256=hashlib.sha256(f.read_bytes()).hexdigest(),Records=rows),ensure_ascii=False,indent=2),encoding='utf-8')
