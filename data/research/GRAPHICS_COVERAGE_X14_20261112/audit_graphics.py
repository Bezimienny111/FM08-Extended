from pathlib import Path
import csv, json, re, collections, hashlib, xml.etree.ElementTree as ET
from PIL import Image
ROOT=Path(r"J:\FM08dev")
R=ROOT/"FmLauncher/data/research"
OUT=R/"GRAPHICS_COVERAGE_X14_20261112"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p,sep=","):return list(csv.DictReader(p.open(encoding="utf-8-sig",newline=""),delimiter=sep))
def dump(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def write(name,data,fields):
 with (OUT/name).open("w",encoding="utf-8-sig",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=fields,delimiter=";");writer.writeheader();writer.writerows(data)
def main():
 OUT.mkdir(exist_ok=True)
 coverage=R/"DATABASE_UPDATE_COVERAGE_X14_20261111"
 players=rows(coverage/"zawodnicy_latest.csv");clubs=rows(coverage/"kluby.csv")
 assert len(players)==30897 and len({p["uid"] for p in players})==30897
 assert len(clubs)==1250 and len({c["club_uid"] for c in clubs})==1250
 pins={str(p.relative_to(ROOT)):sha(p) for p in [coverage/"zawodnicy_latest.csv",coverage/"kluby.csv",coverage/"manifest.json"]}
 leagues={}
 for p in [R/"CLUB_GRAPHICS_20261111/LISTA_KLUBOW_UID_NAZWA_LIGA.csv",R/"SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/graphics-delta/clubs.csv"]:
  for c in rows(p,";"):leagues[c["UID"]]=c["Liga"]
  pins[str(p.relative_to(ROOT))]=sha(p)
 league_new={44:"Liga",45:"Liga de Honra",46:"Second Division - Group A",47:"Second Division - Group B",48:"Second Division - Group C",1070:"Second Division - Group D",49:"Lower division catalogue",501:"Premier Division",502:"First Division",504:"Second Division - Group 1",505:"Second Division - Group 2",506:"Second Division - Group 3",507:"Second Division - Group 4",539:"Lower division catalogue",597:"Primera Division",599:"Lower division catalogue"}
 for c in clubs:
  if c["club_uid"] not in leagues:
   d=int(c["division_index"])
   leagues[c["club_uid"]]=c["country"]+" - "+league_new.get(d,"division index "+str(d))
 clubindex={c["club_uid"]:c for c in clubs}
 configs=[];issues=[];filecache={};maps=collections.defaultdict(list);configpins={}
 patterns=[("face",ROOT/"Dane/graphics",r"graphics/pictures/person/(\d+)/portrait",180),("logo_normal",ROOT/"Dane/graphics",r"graphics/pictures/club/(\d+)/logo",180),("logo_small",ROOT/"Dane/graphics",r"graphics/pictures/club/(\d+)/icon",20),("kit",ROOT/"Dane/graphics",r"graphics/pictures/team/(\d+)/kits/(home|away|third)",130)]
 def inspect(path):
  key=str(path.resolve())
  if key in filecache:return filecache[key]
  result={"path":str(path.relative_to(ROOT)),"exists":path.is_file(),"valid":False}
  if result["exists"]:
   try:
    with Image.open(path) as im:result.update(format=im.format,size=list(im.size));im.verify()
    with Image.open(path) as im:
     im.load()
     if im.width<=0 or im.height<=0:raise ValueError("empty size")
    if result["format"]!="PNG":raise ValueError("not PNG")
    result.update(valid=True,sha256=sha(path))
   except Exception as e:result["error"]=type(e).__name__+": "+str(e)[:180]
  filecache[key]=result;return result
 for kind,base,pattern,expected in patterns:
  for conf in sorted(base.rglob("config.xml")):
   configpins[str(conf.relative_to(ROOT))]=sha(conf)
   modern="modern_2627" in conf.parts
   try:records=list(ET.parse(conf).getroot().iter("record"))
   except Exception as e:
    issues.append({"kind":"config_parse_error","config":str(conf.relative_to(ROOT)),"error":str(e)});continue
   seen=collections.Counter()
   count=0
   for node in records:
    target=node.get("to","");m=re.fullmatch(pattern,target)
    if not m:continue
    seen[target]+=1;count+=1
    src=node.get("from","")
    if not src:
     issues.append({"kind":"empty_source","config":str(conf.relative_to(ROOT)),"target":target});continue
    source=conf.parent/src
    if source.suffix.lower()!=".png":source=Path(str(source)+".png")
    try:source.resolve().relative_to(ROOT/"Dane/graphics")
    except ValueError:
     issues.append({"kind":"source_outside_graphics","config":str(conf.relative_to(ROOT)),"target":target});continue
    asset=inspect(source)
    valid=asset["valid"] and (not modern or asset.get("size")==[expected,expected])
    entry=dict(uid=m[1],kind=kind,slot=m[2] if kind=="kit" else "",config=str(conf.relative_to(ROOT)),target=target,modern=modern,valid=valid,asset=asset)
    maps[(kind,m[1],entry["slot"])].append(entry)
    if not valid:issues.append({"kind":"invalid_mapping","entry":entry})
   for target,n in seen.items():
    if n>1:issues.append({"kind":"duplicate_target_in_config","config":str(conf.relative_to(ROOT)),"target":target,"count":n})
   configs.append({"kind":kind,"config":str(conf.relative_to(ROOT)),"modern":modern,"matching_records":count,"sha256":configpins[str(conf.relative_to(ROOT))]})
 def status(kind,uid,slot=""):
  entries=maps.get((kind,uid,slot),[]);valid=[e for e in entries if e["valid"]];modern=[e for e in valid if e["modern"]]
  return {"modern":bool(modern),"any":bool(valid),"modern_file":modern[0]["asset"]["path"] if modern else "","any_file":valid[0]["asset"]["path"] if valid else "","distinct_hashes":len({e["asset"]["sha256"] for e in valid}),"maps":len(entries)}
 outplayers=[]
 for p in players:
  c=clubindex[p["club_uid"]];s=status("face",p["uid"])
  outplayers.append(dict(uid=p["uid"],imie=p["first"],nazwisko=p["last"],klub=c["club"],klub_uid=p["club_uid"],kraj=p["country"],liga=leagues[p["club_uid"]],ma_zdjecie=int(s["modern"]),ma_zdjecie_lokalnie=int(s["any"]),plik_modern=s["modern_file"],plik_lokalny=s["any_file"],rozne_wersje_lokalne=s["distinct_hashes"],ostatni_import=p["last_import_batch"]))
 outclubs=[]
 for c in clubs:
  uid=c["club_uid"];n=status("logo_normal",uid);s=status("logo_small",uid);kits={slot:status("kit",uid,slot) for slot in ["home","away","third"]}
  outclubs.append(dict(uid=uid,nazwa_klubu=c["club"],kraj=c["country"],liga=leagues[uid],division_index=c["division_index"],herb_normal=int(n["modern"]),herb_small=int(s["modern"]),herb_normal_lokalnie=int(n["any"]),herb_small_lokalnie=int(s["any"]),koszulka_home=int(kits["home"]["modern"]),koszulka_away=int(kits["away"]["modern"]),koszulka_third=int(kits["third"]["modern"]),koszulki_sloty_modern=sum(x["modern"] for x in kits.values()),koszulki_sloty_lokalnie=sum(x["any"] for x in kits.values()),konflikt_herbu_normal=int(n["distinct_hashes"]>1),konflikt_herbu_small=int(s["distinct_hashes"]>1)))
 write("gracze.csv",outplayers,list(outplayers[0]))
 write("kluby.csv",outclubs,list(outclubs[0]))
 missing=[p for p in outplayers if not p["ma_zdjecie"]]
 write("brakujace_zdjecia.csv",missing,list(outplayers[0]))
 gaps=[c for c in outclubs if not(c["herb_normal"] and c["herb_small"] and c["koszulka_home"] and c["koszulka_away"])]
 write("brakujace_grafiki_klubow.csv",gaps,list(outclubs[0]))
 bycountry=[]
 for country in dict.fromkeys(c["country"] for c in clubs):
  pp=[p for p in outplayers if p["kraj"]==country];cc=[c for c in outclubs if c["kraj"]==country]
  bycountry.append(dict(kraj=country,gracze=len(pp),zdjecia_modern=sum(p["ma_zdjecie"] for p in pp),zdjecia_lokalnie=sum(p["ma_zdjecie_lokalnie"] for p in pp),kluby=len(cc),herby_normal=sum(c["herb_normal"] for c in cc),herby_small=sum(c["herb_small"] for c in cc),kluby_koszulka_home=sum(c["koszulka_home"] for c in cc),kluby_koszulka_away=sum(c["koszulka_away"] for c in cc),kluby_koszulka_third=sum(c["koszulka_third"] for c in cc)))
 write("kraje.csv",bycountry,list(bycountry[0]))
 summary=dict(scope="documented_import_lineage_X14_not_all_native_players",players=len(players),clubs=len(clubs),player_photos_modern=sum(x["ma_zdjecie"] for x in outplayers),player_photos_any_local=sum(x["ma_zdjecie_lokalnie"] for x in outplayers),missing_modern_photos=len(missing),club_normal_logos_modern=sum(x["herb_normal"] for x in outclubs),club_small_logos_modern=sum(x["herb_small"] for x in outclubs),club_kits_slots_modern=sum(x["koszulki_sloty_modern"] for x in outclubs),clubs_with_any_modern_kit=sum(x["koszulki_sloty_modern"]>0 for x in outclubs),clubs_home_away=sum(bool(x["koszulka_home"] and x["koszulka_away"]) for x in outclubs),scanned_configs=len(configpins),unique_referenced_images=len(filecache),issues=len(issues),public_graphics_modified=False,game_tested=False,image_identity_visually_verified=False)
 dump("summary.json",summary);dump("inventory-configs.json",configs);dump("inventory-images.json",list(filecache.values()));dump("issues.json",issues)
 assert all(sha(ROOT/p)==h for p,h in configpins.items()),"Config changed during audit"
 pins.update(configpins)
 dump("manifest.json",dict(inputs=pins,script_sha256=sha(Path(__file__)),public_graphics_modified=False,method="Exact UID config target plus existing decodable PNG; modern images require exact dimensions. No native database or running career read; import CSV is source of scope.",outputs={p.name:sha(p) for p in OUT.glob("*") if p.is_file() and p.name not in {"manifest.json","audit_graphics.py"}}))
 lines=["# Audyt grafik X14 - 12 listopada 2026","",f"Zakres: {len(players)} potwierdzonych UID zawodnikow i {len(clubs)} klubow z udokumentowanej linii importow. Nie jest to lista wszystkich osob w bazie ani tylko nowo utworzonych profili.","",f"Zdjecia modern_2627: {summary['player_photos_modern']}; brak: {summary['missing_modern_photos']}. Zdjecia z dowolnych lokalnych folderow: {summary['player_photos_any_local']}.",f"Herby modern_2627 normal/small: {summary['club_normal_logos_modern']}/{summary['club_small_logos_modern']}. Koszulki: {summary['club_kits_slots_modern']} slotow dla {summary['clubs_with_any_modern_kit']} klubow; home+away: {summary['clubs_home_away']}.","","## Sposob weryfikacji","","Ma zdjecie oznacza dokladne mapowanie UID w config.xml oraz istniejacy, poprawnie zdekodowany PNG. W modern_2627 wymagane sa wymiary 180x180 dla twarzy i herbu, 20x20 dla ikony oraz 130x130 dla koszulki. Pozostale lokalne grafiki moga miec inne wymiary; raport rozdziela te zakresy. Sam plik bez mapowania nie daje pokrycia. Audyt nie potwierdza tozsamosci twarzy, aktualnosci herbu/stroju ani rzeczywistego zaladowania w grze. Rozne wersje lokalne nie oznaczaja automatycznie konfliktu ladowania; sprawdzic issues i skorelowac UID.","","## Priorytety uzupelnien","","1. Brakujace herby klubow X14 i X10 z potwierdzonym mapowaniem ClubUID/TMID.","2. Brakujace portrety z istniejacym potwierdzonym URL/identyfikatorem i dokladna tozsamoscia.","3. Koszulki home/away; third opcjonalnie. Zachowac jawny sezon i fallback; nie oznaczac starszych jako aktualne.","","## Publikacja i ograniczenia","","Wczesniej zainstalowane koszulki FC12 maja status personal use only/no redistribution: nie dolaczac ich do publikowanego archiwum bez zgody. Sama dostepnosc obrazu TM/EA/TheSportsDB nie stanowi licencji na redystrybucje; przed publikacja sprawdzic prawa do konkretnego zrodla. Ten etap tworzy raporty, nie publikuje ani nie instaluje grafik.","","## Pliki","","gracze.csv - UID, imie, nazwisko, klub, liga, ma_zdjecie w modern oraz osobno lokalnie.","kluby.csv - UID, nazwa, liga, pokrycie normal/small/home/away/third.","kraje.csv - agregaty; brakujace_zdjecia.csv i brakujace_grafiki_klubow.csv - kolejki brakow.","issues.json - wadliwe mapowania i duplikaty takze w starszych folderach; nie usuwano ich automatycznie.","manifest.json - piny wejsc i configow; inventory-images.json - niezalezna weryfikacja i hashe.",""]
 (OUT/"RAPORT.md").write_text("\n".join(lines),encoding="utf-8")
 print(json.dumps(summary,ensure_ascii=True))
if __name__=="__main__":main()
