import json,sys,time,urllib.request,urllib.error,urllib.parse,concurrent.futures as cf,collections as C
sys.path.insert(0,'scripts')
from importlib import util
R=json.load(open('data/probe.json'))
import re,base64
exec(open('scripts/probe.py').read().split('def fill')[0].split("SRC, OUT")[0])  # imports
src=open('scripts/probe.py').read()
ns={}; exec(src[src.index('def b64d'):src.index('def fill')],globals())
SINK={"q":"test","query":"test","url":"https://example.com","text":"hello","model":"gpt-4o-mini","ids":"bitcoin","vs_currencies":"usd","lat":40.7,"lon":-74.0,"ip":"8.8.8.8","prompt":"a cat","domain":"example.com","symbol":"IBM","interval":"5min","i":"2+2","messages":[{"role":"user","content":"hi"}],"input":"hi","source_code":"print(1)","language_id":71,"cik":"0000320193","LOOKUP":"example.com","src":"https://example.com/a.png","content":"hello","address":"1 Main St","city":"Austin","state":"TX","limit":1,"time_frame":"1h","lead":{"name":"x"},"type":"company","value":"x","size":1,"url_to_scrape":"https://example.com","profile":"https://linkedin.com/in/x","li_profile_url":"https://linkedin.com/in/x","customMode":False,"instrumental":True,"model_owner":"x","model_name":"x","target_lang":"DE","github_username":"octocat","amount":100,"recipient":"0x0000000000000000000000000000000000000001","email":"a@example.com","first_name":"a","last_name":"b","organization_name":"x","company":"x","name":"x"}
QS=urllib.parse.urlencode({k:v for k,v in SINK.items() if isinstance(v,(str,int)) and not isinstance(v,bool)})
targets=[r for r in R if r.get('status') in (400,422) and r.get('listed_payment')]
by=C.defaultdict(list)
for r in targets: by[r['service']].append(r)
def go(rs):
  out=[]
  for r in rs:
    m=r['http_method']; url=r['url']
    if m=='GET': url=url+('&' if '?' in url else '?')+QS; data=None
    else: data=json.dumps(SINK).encode()
    req=urllib.request.Request(url,data=data,method=m,headers={'User-Agent':'mpp-probe/0.1','Content-Type':'application/json','Accept':'application/json'})
    try: resp=urllib.request.urlopen(req,timeout=10); st=resp.status; h=resp.headers; b=resp.read(500)
    except urllib.error.HTTPError as e: st=e.code; h=e.headers; b=e.read(500)
    except Exception as e: st=None; h=None; b=repr(e).encode()
    n=dict(r); n['retry']=True; n['status']=st; n['challenges']=parse_challenges(h.get_all('WWW-Authenticate') or []) if h else []; n['body_snip']=b[:300].decode('utf-8','replace')
    out.append(n); time.sleep(0.15)
  return out
res=[]
with cf.ThreadPoolExecutor(10) as ex:
  for o in ex.map(go,by.values()): res+=o
json.dump(res,open('data/retry.json','w'),indent=1)
print(len(res),C.Counter(x['status'] for x in res))
