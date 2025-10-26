#!/usr/bin/env node
// Ultra-low-latency Pearl item queue watcher using direct PA endpoints
// Requires tokens from the web market (see CLI flags).

function parseArgs(argv){
  const args = {
    region: 'eu',
    base: null, // auto from region if not set
    poll: 300, // ms
    jitter: 0.1,
    cookieToken: null,
    formToken: null,
    session: null,           // ASP.NET_SessionId (older)
    naeuSession: null,       // naeu.Session (newer)
    tradeAuth: null,         // TradeAuth_Session_EU (optional)
    webhook: null,
    once: false,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  }
  for(let i=2;i<argv.length;i++){
    const a = argv[i]
    if(a==='--region') args.region = argv[++i]
    else if(a==='--base') args.base = argv[++i]
    else if(a==='--poll') args.poll = parseInt(argv[++i],10)
    else if(a==='--jitter') args.jitter = parseFloat(argv[++i])
    else if(a==='--cookie-token') args.cookieToken = argv[++i]
    else if(a==='--form-token') args.formToken = argv[++i]
    else if(a==='--session') args.session = argv[++i]
    else if(a==='--naeu-session') args.naeuSession = argv[++i]
    else if(a==='--trade-auth') args.tradeAuth = argv[++i]
    else if(a==='--webhook') args.webhook = argv[++i]
    else if(a==='--once') args.once = true
    else if(a==='--user-agent') args.userAgent = argv[++i]
  }
  return args
}

function defaultBase(region){
  const r = String(region).toLowerCase()
  // Defaults align with PA trade site (EU/NA share naeu domain but separate endpoints)
  if(r==='eu' || r==='na') return 'https://eu-trade.naeu.playblackdesert.com'
  return 'https://eu-trade.naeu.playblackdesert.com'
}

function sleep(ms){ return new Promise(r=>setTimeout(r, ms)) }

function jittered(ms, j){ const d = ms * j; return Math.max(50, Math.round(ms + (Math.random()*2-1)*d)) }

function parseQueue(resultMsg){
  const out=[]
  if(!resultMsg) return out
  for(const chunk of resultMsg.split('|')){
    if(!chunk) continue
    const [id,sid,price,epoch] = chunk.split('-')
    const e = { id: Number(id), sid: Number(sid), price: Number(price), availableEpoch: Number(epoch) }
    if(!Number.isNaN(e.id)) out.push(e)
  }
  return out
}

async function discord(webhook, content){
  try{
    const res = await fetch(webhook, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ content }) })
    if(!res.ok) console.error('Webhook failed:', res.status)
  }catch(e){ console.error('Webhook error:', e.message) }
}

function beep(){ process.stdout.write('\x07') }

function fmt(n){ return n.toLocaleString('en-US') }

async function main(){
  const args = parseArgs(process.argv)
  const base = args.base || defaultBase(args.region)
  const url = new URL('/Home/GetWorldMarketWaitList', base)

  if(!args.cookieToken || !args.formToken){
    console.error('Missing tokens. Provide --cookie-token and --form-token. Optional: --session, --naeu-session, or --trade-auth.')
    process.exit(1)
  }
  
  // Warn if no session cookies provided (they may no longer be required by BDO)
  if(!args.session && !args.naeuSession && !args.tradeAuth){
    console.warn('WARNING: No session/auth cookies provided. Script may fail if BDO requires authentication.')
  }

  // Use built-in fetch (Node 18+) without explicit undici Agent to avoid extra deps
  const agent = null

  let cookie = `__RequestVerificationToken=${args.cookieToken}`
  if(args.session) cookie += `; ASP.NET_SessionId=${args.session}`
  if(args.naeuSession) cookie += `; naeu.Session=${args.naeuSession}`
  if(args.tradeAuth) cookie += `; TradeAuth_Session_EU=${args.tradeAuth}`

  const headers = {
    'User-Agent': args.userAgent,
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': base,
    'Referer': base + '/Home',
    'Cookie': cookie,
  }
  const body = new URLSearchParams({ '__RequestVerificationToken': args.formToken }).toString()

  const seen = new Set()
  console.log(`FAST Pearl queue watch started (region=${args.region}, poll=${args.poll}ms). Ctrl+C to stop.`)

  while(true){
    const tStart = Date.now()
    try{
      const res = await fetch(url, { method:'POST', headers, body })
      if(res.status===429){
        console.error('HTTP 429 throttled; backing off...')
        await sleep(1000)
        continue
      }
      if(!res.ok){
        console.error('HTTP error', res.status)
      } else {
        const data = await res.json().catch(async ()=>({ resultMsg: await res.text() }))
        const msg = data.resultMsg || ''
        const list = parseQueue(msg)
        const now = Date.now()
        for(const e of list){
          const key = `${e.id}-${e.sid}-${e.price}-${e.availableEpoch}`
          if(seen.has(key)) continue
          seen.add(key)
          // Pearl items only: PA marks Pearl items separately; quickest filter is price band and known IDs.
          // We keep it simple: alert all, prefix PEARL? for user validation; user can maintain whitelist later.
          const etaMin = Math.max(0, Math.round((e.availableEpoch*1000 - now)/60000))
          const line = `QUEUE: id:${e.id} sid:${e.sid} price:${fmt(e.price)} ETA~${etaMin}m (epoch ${e.availableEpoch})`
          console.log(new Date().toLocaleTimeString(), line)
          beep()
          if(args.webhook) await discord(args.webhook, line)
        }
      }
    }catch(e){
      console.error('Request error:', e.message)
    }

    if(args.once) break
    const elapsed = Date.now()-tStart
    const wait = Math.max(50, jittered(args.poll, args.jitter) - elapsed)
    await sleep(wait)
  }

  try { agent && agent.close && agent.close() } catch {}
}

main().catch(err=>{ console.error(err); process.exit(1) })
