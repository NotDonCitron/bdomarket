#!/usr/bin/env node
import fs from 'node:fs/promises'
import path from 'node:path'

const ARSHA_BASE = 'https://api.arsha.io'

function parseArgs(argv) {
  const args = {
    region: 'eu', tax: 0.35, minRoi: 0.05, maxItems: 150, exportJson: null, config: null,
    mode: 'listwait', budget: 0, minSpeed: 0.3, minBuyersSum: 3, minSellersNearBuy: 1,
    sellStrategy: 'buyer_level', sellTickOffset: 1, sellPct: 0.02, buyersK: 5, minProfitPct: 0.02,
  }
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--region') args.region = argv[++i]
    else if (a === '--tax') args.tax = parseFloat(argv[++i])
    else if (a === '--min-roi') args.minRoi = parseFloat(argv[++i])
    else if (a === '--max-items') args.maxItems = parseInt(argv[++i], 10)
    else if (a === '--export-json') args.exportJson = argv[++i]
    else if (a === '--config') args.config = argv[++i]
    else if (a === '--mode') args.mode = argv[++i]
    else if (a === '--budget') args.budget = parseInt(argv[++i], 10)
    else if (a === '--min-speed') args.minSpeed = parseFloat(argv[++i])
    else if (a === '--min-buyers-sum') args.minBuyersSum = parseInt(argv[++i], 10)
    else if (a === '--min-sellers-near-buy') args.minSellersNearBuy = parseInt(argv[++i], 10)
    else if (a === '--sell-strategy') args.sellStrategy = argv[++i]
    else if (a === '--sell-tick-offset') args.sellTickOffset = parseInt(argv[++i], 10)
    else if (a === '--sell-pct') args.sellPct = parseFloat(argv[++i])
    else if (a === '--buyers-k') args.buyersK = parseInt(argv[++i], 10)
    else if (a === '--min-profit-pct') args.minProfitPct = parseFloat(argv[++i])
  }
  return args
}

async function loadConfig(p) {
  if (!p) return {}
  try {
    const data = await fs.readFile(p, 'utf-8')
    return JSON.parse(data)
  } catch {
    return {}
  }
}

async function arshaGet(pathname, params) {
  const url = new URL(ARSHA_BASE + pathname)
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)))
  const res = await fetch(url, { headers: { 'accept': 'application/json' } })
  if (!res.ok) throw new Error(`GET ${url} -> ${res.status}`)
  return res.json()
}

async function arshaPost(pathname, body, params) {
  const url = new URL(ARSHA_BASE + pathname)
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)))
  const res = await fetch(url, { method: 'POST', headers: { 'content-type': 'application/json', 'accept': 'application/json' }, body: body ? JSON.stringify(body) : undefined })
  if (!res.ok) throw new Error(`POST ${url} -> ${res.status}`)
  return res.json()
}

function parseMarketV1(resultMsg) {
  const items = []
  if (!resultMsg) return items
  for (const chunk of resultMsg.split('|')) {
    if (!chunk) continue
    const parts = chunk.split('-')
    if (parts.length < 4) continue
    const [id, stock, trades, base] = parts
    items.push({ id: Number(id), stock: Number(stock), trades: Number(trades), basePrice: Number(base) })
  }
  return items
}

function parseOrdersV1(resultMsg) {
  const levels = []
  if (!resultMsg) return levels
  for (const chunk of resultMsg.split('|')) {
    if (!chunk) continue
    const [price, sellers, buyers] = chunk.split('-')
    levels.push({ price: Number(price), buyers: Number(buyers), sellers: Number(sellers) })
  }
  return levels
}

function computeFlip(levels, tax) {
  let lowestSell = null
  let highestBuy = null
  for (const lv of levels) {
    if (lv.sellers > 0) lowestSell = lowestSell == null ? lv.price : Math.min(lowestSell, lv.price)
    if (lv.buyers > 0) highestBuy = highestBuy == null ? lv.price : Math.max(highestBuy, lv.price)
  }
  if (lowestSell == null || highestBuy == null) return null
  const profit = highestBuy * (1 - tax) - lowestSell
  const roi = profit / lowestSell
  return { lowestSell, highestBuy, profit, roi }
}

function pickTarget(levels, bidIdx, strategy, tickOffset, pct, lowestSell, tax, minProfitPct) {
  const n = levels.length
  if (n === 0 || bidIdx == null || bidIdx < 0) return { price: null, idx: -1 }
  if (strategy === 'min_profitable') {
    const needed = lowestSell * (1 + (minProfitPct||0)) / (1 - tax)
    let idx = 0
    while (idx + 1 < n && levels[idx].price < needed) idx++
    // ensure we don't go below needed
    while (idx < n && levels[idx].price < needed) idx++
    if (idx >= n) idx = n - 1
    return { price: levels[idx].price, idx }
  }
  if (strategy === 'tick_offset') {
    const idx = Math.min(n - 1, Math.max(0, bidIdx + tickOffset))
    return { price: levels[idx].price, idx }
  }
  if (strategy === 'pct_over_buy') {
    const p = levels[bidIdx].price * (1 + pct)
    let idx = bidIdx
    while (idx + 1 < n && levels[idx + 1].price <= p) idx++
    return { price: levels[idx].price, idx }
  }
  // buyer_level
  return { price: levels[bidIdx].price, idx: bidIdx }
}

function buyersSumTopK(levels, k) {
  const withBuyers = levels.filter(l => l.buyers > 0).sort((a, b) => b.price - a.price)
  let sum = 0
  for (let i = 0; i < Math.min(k, withBuyers.length); i++) sum += withBuyers[i].buyers
  return sum
}

function sellersNear(levels, buyIdx) {
  if (buyIdx < 0) return 0
  let s = 0
  s += levels[buyIdx]?.sellers || 0
  s += levels[buyIdx + 1]?.sellers || 0
  return s
}

function speedScore(buyersSum, sellersAtTarget) {
  const demand = 1 - Math.exp(-buyersSum / 5)
  const comp = 1 / (1 + sellersAtTarget)
  let s = demand * comp
  if (s < 0) s = 0
  if (s > 1) s = 1
  return s
}

async function main() {
  const cli = parseArgs(process.argv)
  const cfg = await loadConfig(cli.config)
  const region = String(cfg.region ?? cli.region).toLowerCase()
  const tax = Number(cfg.tax ?? cli.tax)
  const minRoi = Number(cfg.min_roi ?? cfg.minRoi ?? cli.minRoi)
  const maxItems = Number(cfg.max_items ?? cfg.maxItems ?? cli.maxItems)
  const mode = String(cfg.mode ?? cli.mode)
  const budget = Number(cfg.budget ?? cli.budget)
  const minSpeed = Number(cfg.min_speed ?? cfg.minSpeed ?? cli.minSpeed)
  const minBuyersSum = Number(cfg.min_buyers_sum ?? cfg.minBuyersSum ?? cli.minBuyersSum)
  const minSellersNearBuy = Number(cfg.min_sellers_near_buy ?? cfg.minSellersNearBuy ?? cli.minSellersNearBuy)
  const sellStrategy = String(cfg.sell_strategy ?? cfg.sellStrategy ?? cli.sellStrategy)
  const sellTickOffset = Number(cfg.sell_tick_offset ?? cfg.sellTickOffset ?? cli.sellTickOffset)
  const sellPct = Number(cfg.sell_pct ?? cfg.sellPct ?? cli.sellPct)
  const buyersK = Number(cfg.buyers_k ?? cfg.buyersK ?? cli.buyersK)
  const minProfitPct = Number(cfg.min_profit_pct ?? cfg.minProfitPct ?? cli.minProfitPct)

  let market
  try {
    const data = await arshaGet(`/v1/${region}/market`)
    market = parseMarketV1(data.resultMsg)
  } catch (e) {
    console.error('Failed to fetch market list:', e.message)
    process.exit(1)
  }

  market.sort((a, b) => (b.trades - a.trades) || (b.stock - a.stock))
  const selected = market.slice(0, maxItems)

  const candidates = []
  const chunk = 25
  for (let i = 0; i < selected.length; i += chunk) {
    const ids = selected.slice(i, i + chunk).map(r => r.id)
    let batch
    try {
      batch = await arshaPost(`/v2/${region}/GetBiddingInfoList`, ids.map(id => ({ id, sid: 0 })), { lang: 'en' })
    } catch (e) {
      // fallback per id using v1
      const arr = []
      for (const id of ids) {
        try {
          const obj = await arshaGet(`/v1/${region}/orders`, { id, sid: 0 })
          arr.push({ id, sid: 0, orders: parseOrdersV1(obj.resultMsg) })
        } catch {
          // skip id on error
        }
      }
      batch = arr
    }

    const arr = Array.isArray(batch) ? batch : (batch && batch.orders ? [batch] : [])
    for (const obj of arr) {
      const id = Number(obj.id)
      const orders = (obj.orders?.map(o => ({ price: Number(o.price), buyers: Number(o.buyers), sellers: Number(o.sellers) })) || []).sort((a,b)=>a.price-b.price)
      const res = computeFlip(orders, tax)
      const row = selected.find(r => r.id === id)
      if (!row) continue
      // compute levels
      let lowestSellIdx = -1, highestBuyIdx = -1
      for (let j=0;j<orders.length;j++) {
        if (orders[j].sellers>0 && lowestSellIdx===-1) lowestSellIdx=j
        if (orders[j].buyers>0) highestBuyIdx=j
      }
      if (lowestSellIdx===-1 || highestBuyIdx===-1) continue
      const lowestSell = orders[lowestSellIdx].price
      const highestBuy = orders[highestBuyIdx].price

      if (mode === 'instant') {
        if (res && res.profit > 0 && res.roi >= minRoi) {
          candidates.push({ id, buy_at: res.lowestSell, sell_at: res.highestBuy, profit: res.profit, roi: res.roi, base_price: row.basePrice, stock: row.stock, trades: row.trades, speed: 1, buyers_sum: orders[highestBuyIdx].buyers, sellers_near_buy: orders[lowestSellIdx].sellers })
        }
        continue
      }

      const tgt = pickTarget(orders, highestBuyIdx, sellStrategy, sellTickOffset, sellPct, lowestSell, tax, minProfitPct)
      if (tgt.price == null) continue
      const buyersSum = buyersSumTopK(orders, buyersK)
      const sellersNearBuy = sellersNear(orders, lowestSellIdx)
      const speed = speedScore(buyersSum, orders[tgt.idx]?.sellers || 0)
      const profit = tgt.price * (1 - tax) - lowestSell
      const roi = profit / lowestSell
      if (roi >= minRoi && buyersSum >= minBuyersSum && sellersNearBuy >= minSellersNearBuy && speed >= minSpeed && profit > 0) {
        const qtyBudget = budget>0 ? Math.max(1, Math.floor(budget/lowestSell)) : Infinity
        const qty = Math.max(1, Math.min(qtyBudget, orders[lowestSellIdx].sellers || 1))
        const score = 0.6*roi + 0.3*speed + 0.1*Math.min(1, buyersSum/10)
        candidates.push({ id, buy_at: lowestSell, sell_at: tgt.price, profit, roi, qty, speed, buyers_sum: buyersSum, sellers_near_buy: sellersNearBuy, base_price: row.basePrice, stock: row.stock, trades: row.trades, score })
      }
    }
    await new Promise(r => setTimeout(r, 200))
  }

  candidates.sort((a, b) => (b.score ?? 0) - (a.score ?? 0) || (b.roi - a.roi) || (b.profit - a.profit))
  const top = candidates.slice(0, 20)

  if (!top.length) {
    console.log('No candidates found. Consider lowering thresholds or changing sell strategy (e.g., --sell-strategy pct_over_buy --sell-pct 0.03).')
  } else {
    console.log(`Top ${top.length} flip candidates (region=${region}, mode=${mode}, tax=${tax.toFixed(4)}, min_roi=${minRoi.toFixed(2)}):`)
    console.log('id     buy_at     target     profit       roi    qty  speed  buyers  stock   trades')
    for (const c of top) {
      const profitI = Math.trunc(c.profit)
      console.log(`${String(c.id).padEnd(6)}${String(c.buy_at).padEnd(11)}${String(c.sell_at).padEnd(11)}${String(profitI).padEnd(12)}${(c.roi*100).toFixed(1).padStart(5)}%  ${String(c.qty||1).padEnd(4)} ${(c.speed||0).toFixed(2).padEnd(6)} ${String(c.buyers_sum||0).padEnd(6)} ${String(c.stock).padEnd(7)}${c.trades}`)
    }
  }

  if (cli.exportJson) {
    try {
      await fs.writeFile(cli.exportJson, JSON.stringify(top, null, 2), 'utf-8')
      console.log(`Exported ${top.length} candidates to ${cli.exportJson}`)
    } catch (e) {
      console.error('Failed to export JSON:', e.message)
    }
  }
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
