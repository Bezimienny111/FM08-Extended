from pathlib import Path
import sys,importlib.util,hashlib,json
from datetime import datetime,timezone
sys.dont_write_bytecode=True
ROOT=Path(r"J:\FM08dev");B=Path(__file__).resolve().parent
engine=ROOT/"FmLauncher/data/research/KITS_FC12_20261111/fc12_pipeline.py"
spec=importlib.util.spec_from_file_location("existing_http_cache_reader",engine);lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
lib.CACHE=B/"sources/web/cache";lib.CACHE.mkdir(parents=True,exist_ok=True)
urls=[
"https://www.football.org.il/leagues/league/?league_id=40&season_id=27",
"https://dimayor.com.co/widget_n/Prod/2025/posicionesTA.html?showMenu=false",
"https://www.rsssf.org/tablesc/col2025.html",
"https://dimayor.com.co/2025/12/12/junior-fc-dio-el-primer-golpe-en-la-final-ida-de-la-liga-betplay-dimayor-ll-2025/",
"https://dimayor.com.co/wp-content/uploads/2025/12/BEST-XI-Dimayor-DIMAYOR-II-2025-Finales-Ida-Vuelta.pdf",
"https://www.rsssf.org/tablesi/isra2026.html"]
ledger=[]
for url in urls:
 try:
  body,path,reused=lib.get(url,8*1024*1024)
  row=dict(url=url,file=str(path.relative_to(B)),sha256=hashlib.sha256(body).hexdigest(),reused=reused,bytes=len(body),fetched_at=datetime.now(timezone.utc).isoformat())
  ledger.append(row);print(json.dumps(dict(url=url,bytes=len(body),reused=reused)),flush=True)
 except Exception as e:ledger.append(dict(url=url,error=type(e).__name__+":"+str(e)));print("FETCH_ERROR",url,str(e)[:120],flush=True)
(B/"public-source-cache-ledger.json").write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
