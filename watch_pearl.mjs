#!/usr/bin/env node
import fs from 'node:fs/promises'

const ARSHA_BASE = 'https://api.arsha.io'

function parseArgs(argv){
  const args = { region: 'eu', poll: 15, webhook: null, once: false }
  for(let i=2;i<argv.length;i++){
    const a = argv[i]
    if(a==='--region') args.region = argv[++i]
    else if(a==='--poll') args.poll = parseInt(argv[++i],10)
    else if(a==='--webhook') args.webhook = argv[++i]
    else if(a==='--once') args.once = true
  }
  return args
}

async function arshaGet(pathname, params){
  const url = new URL(ARSHA_BASE + pathname)
  if(params) Object.entries(params).forEach(([k,v])=>url.searchParams.set(k,String(v)))
  const res = await fetch(url, { headers: { 'accept':'application/json' } })
  if(!res.ok) throw new Error(`GET ${url} -> ${res.status}`)
  return res.json()
}

function parseQueueV1(resultMsg){
  const out = []
  if(!resultMsg) return out
  for(const chunk of resultMsg.split('|')){
    if(!chunk) continue
    const [id, sid, price, ts] = chunk.split('-')
    out.push({ id:Number(id), sid:Number(sid), price:Number(price), availableEpoch:Number(ts) })
  }
  return out
}

async function sendDiscord(webhook, content){
  try{
    const res = await fetch(webhook,{ method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify({ content }) })
    if(!res.ok) console.error('Webhook failed:', res.status)
  }catch(e){ console.error('Webhook error:', e.message) }
}

function beep(){
  process.stdout.write('\x07')
}

function fmtPrice(n){ return n.toLocaleString('en-US') }

async function main(){
  const args = parseArgs(process.argv)
  const region = String(args.region).toLowerCase()
  const pollMs = Math.max(5, args.poll)*1000

  // Load pearl items map
  let pearlMap = new Map()
  try{
    const data = await arshaGet(`/v2/${region}/pearlItems`)
    // v2 returns array of objects with id and name
    if(Array.isArray(data)){
      for(const it of data){ if(it && typeof it.id !== 'undefined') pearlMap.set(Number(it.id), String(it.name||`Item ${it.id}`)) }
    } else if(data && data.resultMsg){
      // v1 fallback (parse id-sid-count-price|...) -> we only keep ids
      const ids = new Set()
      for(const chunk of data.resultMsg.split('|')){ if(!chunk) continue; const [id] = chunk.split('-'); ids.add(Number(id)) }
      for(const id of ids) pearlMap.set(id, `Item ${id}`)
    }
  }catch(e){
    console.error('Failed to load pearl items list:', e.message)
  }
  if(pearlMap.size===0){
    console.log('Warning: pearl item list empty; will still alert on any queue items (no name).')
  }

  const seen = new Set()
  console.log(`Watching pearl queue for region=${region} (poll=${Math.round(pollMs/1000)}s). Press Ctrl+C to stop.`)

  while(true){
    try{
      const q = await arshaGet(`/v1/${region}/queue`)
      const list = parseQueueV1(q.resultMsg)
      const now = Date.now()
      for(const e of list){
        const key = `${e.id}-${e.sid}-${e.price}-${e.availableEpoch}`
        if(seen.has(key)) continue
        seen.add(key)
        const isPearl = pearlMap.has(e.id)
        if(isPearl){
          const name = pearlMap.get(e.id)
          const etaMs = e.availableEpoch*1000 - now
          const etaMin = Math.max(0, Math.round(etaMs/60000))
          const msg = `PEARL ITEM QUEUED: ${name} (id:${e.id}, sid:${e.sid}) at ${fmtPrice(e.price)}. Available in ~${etaMin}m (epoch ${e.availableEpoch}).`
          console.log(new Date().toLocaleTimeString(), msg)
          beep()
          if(args.webhook) await sendDiscord(args.webhook, msg)
        }
      }
    }catch(e){
      console.error('Queue fetch error:', e.message)
    }

    if(args.once) break
    await new Promise(r=>setTimeout(r, pollMs))
  }
}

main().catch(err=>{ console.error(err); process.exit(1) })
