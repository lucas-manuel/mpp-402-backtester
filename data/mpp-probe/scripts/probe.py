import json, re, sys, time, base64, urllib.request, urllib.error, ssl, concurrent.futures as cf

SRC, OUT = sys.argv[1], sys.argv[2]
services = json.load(open(SRC))['services']

def b64d(s):
    s = s + '=' * (-len(s) % 4)
    return json.loads(base64.urlsafe_b64decode(s))

PARAM_RE = re.compile(r'(\w+)="((?:[^"\\]|\\.)*)"')

def parse_challenges(headers):
    out = []
    for h in headers:
        # split on "Payment " occurrences
        for part in re.split(r'(?:^|,\s*)(?=Payment\s)', h):
            part = part.strip()
            if not part.startswith('Payment'):
                continue
            p = dict(PARAM_RE.findall(part))
            if 'request' in p:
                try:
                    p['request_decoded'] = b64d(p['request'])
                except Exception as e:
                    p['request_decoded'] = {'_err': str(e)}
            p.pop('opaque', None)
            out.append(p)
    return out

def fill(path):
    return re.sub(r'\{[^}]+\}|:\w+', 'test', path)

def probe(svc):
    base = svc['serviceUrl'].rstrip('/')
    res = []
    for ep in svc.get('endpoints', []):
        url = base + fill(ep['path'])
        m = ep.get('method', 'GET').upper()
        data = b'{}' if m in ('POST', 'PUT', 'PATCH') else None
        req = urllib.request.Request(url, data=data, method=m,
                                     headers={'User-Agent': 'mpp-probe/0.1', 'Content-Type': 'application/json', 'Accept': 'application/json'})
        r = {'service': svc['id'], 'url': url, 'http_method': m, 'listed_payment': ep.get('payment')}
        if m not in ('GET','HEAD') and (not ep.get('payment') or m=='DELETE'):
            r['skipped']='unpaid non-GET'; res.append(r); continue
        t0 = time.time()
        try:
            resp = urllib.request.urlopen(req, timeout=10, context=ssl.create_default_context())
            r['status'] = resp.status; hdrs = resp.headers; body = resp.read(2000)
        except urllib.error.HTTPError as e:
            r['status'] = e.code; hdrs = e.headers; body = e.read(4000)
        except Exception as e:
            r['status'] = None; r['error'] = repr(e)[:200]; hdrs = None; body = b''
        r['ms'] = int((time.time() - t0) * 1000)
        if hdrs is not None:
            wa = hdrs.get_all('WWW-Authenticate') or []
            r['challenges'] = parse_challenges(wa)
            r['www_auth_raw_schemes'] = [w.split(' ')[0] for w in wa]
            x = {k: v[:3000] for k, v in hdrs.items() if k.lower() in ('payment-required', 'x-payment-required', 'x-402', 'accept-payment')}
            r['x402_headers'] = x
            try:
                bj = json.loads(body)
                if isinstance(bj, dict) and ('x402Version' in bj or 'accepts' in bj):
                    r['x402_body'] = {'x402Version': bj.get('x402Version'), 'accepts': bj.get('accepts')}
            except Exception:
                pass
            r['body_snip'] = body[:300].decode('utf-8', 'replace')
        res.append(r)
        time.sleep(0.15)
    return res

allr = []
with cf.ThreadPoolExecutor(10) as ex:
    for i, rs in enumerate(ex.map(probe, services)):
        allr.extend(rs)
        print(i, rs[0]['service'] if rs else '-', len(rs), file=sys.stderr, flush=True)
json.dump(allr, open(OUT, 'w'), indent=1)
