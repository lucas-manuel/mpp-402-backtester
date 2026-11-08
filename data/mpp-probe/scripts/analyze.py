import json,collections as C,sys
R=json.load(open(sys.argv[1]))
TOK={'0x20c000000000000000000000b9537d11c60e8b50':'USDC.e','0x20c0000000000000000000006a37da5c996874be':'OUSD','0x20c0000000000000000000000000000000000000':'pathUSD'}
print('total',len(R),'skipped',sum('skipped' in r for r in R))
print('status',C.Counter(r.get('status') for r in R if 'skipped' not in r).most_common(15))
rows=[]
for r in R:
  for c in r.get('challenges',[]):
    d=c.get('request_decoded',{}); md=d.get('methodDetails',{}) or {}
    rows.append(dict(svc=r['service'],url=r['url'],m=c.get('method'),intent=c.get('intent'),chain=md.get('chainId'),cur=TOK.get(str(d.get('currency','')).lower(),d.get('currency')),amt=d.get('amount'),dec=d.get('decimals'),feePayer=md.get('feePayer'),keys=sorted(d.keys())))
json.dump(rows,open('data/challenges.json','w'),indent=1)
print('challenges',len(rows),'endpoints w/402+payment',len({x['url'] for x in rows}))
print('by method',C.Counter(x['m'] for x in rows))
print('by chain',C.Counter((x['m'],x['chain']) for x in rows))
print('by cur',C.Counter((x['chain'],x['cur']) for x in rows))
print('by intent',C.Counter((x['intent'],x['chain']) for x in rows))
svc_chain=C.defaultdict(set)
for x in rows: svc_chain[x['svc']].add((x['m'],x['chain']))
print('services with any 402 challenge',len(svc_chain))
print('services w testnet:',sorted(s for s,v in svc_chain.items() if any(c==42431 for _,c in v)))
print('services 402 but no challenge parse:',sorted({r['service'] for r in R if r.get('status')==402 and not r.get('challenges')}))
print('x402 headers:',sorted({r['service'] for r in R if r.get('x402_headers')}), 'x402 body:',sorted({r['service'] for r in R if r.get('x402_body')}))
print('schemes',C.Counter(s for r in R for s in r.get('www_auth_raw_schemes',[])))
svcs=C.defaultdict(C.Counter)
for r in R:
  if 'skipped' in r: continue
  svcs[r['service']][r.get('status')]+=1
dead=[s for s,c in svcs.items() if 402 not in c]
print('services with no 402 at all',len(dead))
for s in dead: print('  ',s,dict(svcs[s]))
