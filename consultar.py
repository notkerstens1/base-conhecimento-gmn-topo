#!/usr/bin/env python3
"""Busca textual local; usa somente Python e SQLite da biblioteca padrão."""
import argparse,json,re,sqlite3,unicodedata
from pathlib import Path
p=argparse.ArgumentParser(description='Consultar sínteses e suas fontes')
p.add_argument('consulta',nargs='?',default='')
p.add_argument('--limite',type=int,default=5)
p.add_argument('--id',dest='chunk_id')
p.add_argument('--json',action='store_true')
a=p.parse_args()
db=Path(__file__).with_name('busca_conhecimento.sqlite')
c=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True)
if a.chunk_id:
 rows=c.execute('SELECT metadata_json FROM chunks WHERE id=?',(a.chunk_id,)).fetchall()
else:
 stop={'a','o','as','os','de','da','do','das','dos','e','em','no','na','nos','nas','para','por','com','um','uma','que','como'}
 terms=[t for t in re.findall(r'[^\W_]+',a.consulta,re.UNICODE) if t.lower() not in stop]
 if not terms:p.error('Informe uma consulta ou --id.')
 def quoted_term(t):
  t=unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode().lower()
  if t.startswith('avaliac'):t='avaliac'
  elif t.startswith('mecanismo'):t='mecanismo'
  elif t in {'falso','falsa','falsos','falsas'}:t='fals'
  return '"'+t.replace('"','""')+'"'+('*' if len(t)>3 else '')
 quoted=[quoted_term(t) for t in terms]
 query=' AND '.join(quoted)
 sql="SELECT c.metadata_json FROM busca JOIN chunks c ON busca.id=c.id WHERE busca MATCH ? ORDER BY CASE c.source_type WHEN 'documentacao_oficial' THEN 0 WHEN 'procedimento' THEN 1 WHEN 'observacao_visual' THEN 3 ELSE 2 END, bm25(busca,0,2,1) LIMIT ?"
 rows=c.execute(sql,(query,max(1,min(a.limite,100)))).fetchall()
 if not rows and len(quoted)>2:
  anchored=quoted[0]+' AND ('+' OR '.join(quoted[1:])+')'
  rows=c.execute(sql,(anchored,max(1,min(a.limite,100)))).fetchall()
 if not rows and len(quoted)>1:
  rows=c.execute(sql,(' OR '.join(quoted),max(1,min(a.limite,100)))).fetchall()
results=[json.loads(x[0]) for x in rows]
if a.json:print(json.dumps(results,ensure_ascii=False,indent=2))
else:
 for x in results:print('['+x['id']+'] '+x['title']+'\n'+x['text']+'\n')
c.close()
