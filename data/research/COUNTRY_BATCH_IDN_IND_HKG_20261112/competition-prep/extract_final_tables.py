from html.parser import HTMLParser
from pathlib import Path
import json,re,hashlib
B=Path(__file__).resolve().parent
class Tables(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.tables=[];self.headings={};self.h=None;self.htext=[];self.depth=0;self.cell=None;self.row=None;self.rows=[];self.context=None
 def handle_starttag(self,tag,attrs):
  if tag in ['h2','h3','h4']:self.h=tag;self.htext=[]
  if tag=='table':
   self.depth+=1
   if self.depth==1:self.rows=[];self.context=dict(self.headings)
  elif tag=='tr'and self.depth==1:self.row=[]
  elif tag in ['th','td']and self.depth==1:self.cell=[]
 def handle_data(self,data):
  if self.h:self.htext.append(data)
  if self.depth==1 and self.cell is not None:self.cell.append(data)
 def handle_endtag(self,tag):
  if self.h==tag:
   self.headings[tag]=re.sub(r'\s+',' ',''.join(self.htext)).strip();self.h=None
   for k in ['h3','h4']if tag=='h2'else(['h4']if tag=='h3'else[]):self.headings.pop(k,None)
  if tag in ['th','td']and self.depth==1 and self.cell is not None:
   if self.row is not None:self.row.append(re.sub(r'\s+',' ',''.join(self.cell)).strip())
   self.cell=None
  elif tag=='tr'and self.depth==1 and self.row is not None:self.rows.append(self.row);self.row=None
  elif tag=='table':
   if self.depth==1:self.tables.append(dict(Headings=self.context,Rows=self.rows))
   self.depth-=1
if __name__=='__main__':
 for name in ['idn-liga4-full-final','idn-nusantara-full-final','ind-ifl-full-final']:
  p=B/'sources'/(name+'.html');t=Tables();t.feed(p.read_text(encoding='utf-8'));out=[]
  for table in t.tables:
   if any('Pts'in row and('Pld'in row or'P'in row)for row in table['Rows'][:2]):out.append(table)
  (B/(name+'-tables.json')).write_text(json.dumps(dict(Source=str(p),SHA256=hashlib.sha256(p.read_bytes()).hexdigest(),Tables=out),ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
  print(name,len(out))
  for i,z in enumerate(out):print(i,z['Headings'],z['Rows'][:2])
