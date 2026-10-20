#!/usr/bin/env python3
"""Importa pacotes, hospedagens, experiências e destinos de centraltour.com
(páginas públicas, permitidas pelo robots.txt) e grava o resultado dentro do
index.php, entre os marcadores /*DADOS:INICIO*/ e /*DADOS:FIM*/.
Uso: python atualizar.py [caminho/index.php]   (só biblioteca padrão)
Se a coleta vier suspeita (poucos itens), NÃO altera o arquivo e sai com erro."""
import concurrent.futures as cf, datetime, html, json, re, sys, time, urllib.request

BASE = 'https://centraltour.com'
UA = {'User-Agent': 'Mozilla/5.0 (RJTurismo site updater)'}
ARQ = sys.argv[1] if len(sys.argv) > 1 else 'index.php'

def get(u):
    for i in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read().decode('utf8', 'replace')
            time.sleep(.2)
            return r
        except Exception:
            time.sleep(2 + i * 2)
    return None

def linhas(h):
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', h, flags=re.S)
    t = re.sub(r'<[^>]+>', '\n', t)
    return '|'.join(x.strip() for x in html.unescape(t).split('\n') if x.strip())

def meta(h, k):
    m = re.search(r'(?:name|property)="%s" content="([^"]*)"' % re.escape(k), h)
    return html.unescape(m.group(1)).strip() if m else ''

def curto(s, n=210):
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) <= n: return s
    c = s[:n].rsplit(' ', 1)[0]
    return c.rstrip(',;:') + '…'

def num(s): return int(s.replace('.', ''))

def pacote(u):
    h = get(u)
    if not h: return None
    s = linhas(h)
    g = lambda p: (re.search(p, s) or [None, None])[1]
    t = g(r'Pacote para\|(.+?)\|'); dest = g(r'Destino:\|(.+?)\|')
    noites = g(r'DIAS /\|(\d+)\|NOITES'); saida = g(r'Sa.da em\|(\d\d/\d\d/\d{4})')
    orig = g(r'A.reo saindo de\|(.+?)\|'); p10 = g(r'a partir de\|10\|x\|R\$\|([\d.]+)\|')
    tot = g(r'OU\|Pre.o por pessoa a partir de\|R\$\|([\d.]+)\|')
    img = meta(h, 'og:image')
    if not (t and dest and noites and saida and p10 and tot and img): return None
    inc = re.search(r'Pacote inclui\|.*?Condi..es Gerais\|(.+?)\|Mais op', s)
    inc = inc.group(1).split('|')[:4] if inc else []
    d = saida.split('/')
    if datetime.date(int(d[2]), int(d[1]), int(d[0])) < datetime.date.today(): return None
    cat = 'nacional' if re.search(r' - [A-Z]{2}$', dest) else 'internacional'
    return [t.strip(), dest, int(noites), saida, orig or '', num(p10), num(tot), img, inc, cat]

def ficha(u, fim):
    h = get(u)
    if not h: return None
    m = re.match(r'(.+) em (.+?) [–—-] ' + fim, html.unescape(re.search(r'<title>([^<]*)', h).group(1)))
    img = meta(h, 'og:image')
    if not (m and img): return None
    return [m.group(1).strip(), m.group(2).strip(), curto(meta(h, 'description')), img]

def destino(u):
    h = get(u)
    if not h: return None
    t = html.unescape(re.search(r'<title>([^<]*)', h).group(1))
    m = re.match(r'Viagem para (.+?)(?:, (.+?))? [–—-] ', t)
    img = meta(h, 'og:image')
    if not (m and img): return None
    return [m.group(1).strip(), (m.group(2) or '').strip(), curto(meta(h, 'description'), 260), img]

def lote(fn, urls, *a):
    with cf.ThreadPoolExecutor(4) as ex:
        return [r for r in ex.map(lambda u: fn(u, *a), urls) if r]

sm = get(BASE + '/sitemap.xml')
if not sm: sys.exit('sitemap indisponível')
urls = re.findall(r'<loc>([^<]+)', sm)
sel = lambda rx: [u for u in urls if re.search(rx, u)]

pk = lote(pacote, sel(r'/pacotes/[a-z0-9-]+/\d+$'))
# mesmo pacote em várias datas: fica o mais barato
melhor = {}
for x in pk:
    k = (x[0], x[1], x[4])
    if k not in melhor or x[6] < melhor[k][6]: melhor[k] = x
pk = sorted(melhor.values(), key=lambda r: (r[9] != 'nacional', r[1], r[6]))
hot = sorted(lote(ficha, sel(r'/hospedagem/[a-z0-9-]+$'), 'Hospedagem'), key=lambda r: (r[1], r[0]))
exp = lote(ficha, sel(r'/experiencias/[a-z0-9-]+$'), 'Passeios')
dst = lote(destino, sel(r'/destinos/[a-z0-9-]+$'))
print('pacotes', len(pk), 'hoteis', len(hot), 'experiencias', len(exp), 'destinos', len(dst))
if len(pk) < 20 or len(hot) < 100 or len(exp) < 5 or len(dst) < 30:
    sys.exit('coleta suspeita: arquivo NÃO alterado')

dados = {'atualizado': datetime.date.today().strftime('%d/%m/%Y'), 'pacotes': pk, 'hoteis': hot, 'experiencias': exp, 'destinos': dst}
bloco = '/*DADOS:INICIO*/\n$DADOS = json_decode(<<<\'JSON\'\n' + json.dumps(dados, ensure_ascii=False, separators=(',', ':')) + '\nJSON, true);\n/*DADOS:FIM*/'
src = open(ARQ, encoding='utf8').read()
novo, n = re.subn(r'/\*DADOS:INICIO\*/.*?/\*DADOS:FIM\*/', lambda _: bloco, src, flags=re.S)
if n != 1: sys.exit('marcadores DADOS não encontrados em ' + ARQ)
open(ARQ, 'w', encoding='utf8', newline='\n').write(novo)
print('ok:', ARQ, 'atualizado')
