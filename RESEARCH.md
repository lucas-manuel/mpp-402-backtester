# Research notes: MPP, Tempo, OUSD, and paid financial data over HTTP 402

Snapshot taken **2026-11-07**. Everything here moves fast, so re-verify before relying on it. Claims we checked directly (by decoding live 402 challenges or making a payment) are marked **[verified]**. Everything else comes from docs or press.

---

## 1. MPP (Machine Payments Protocol)

- **What it is:** an open HTTP-402 payment scheme, co-authored by Stripe and Tempo, launched 2026-03-18 alongside Tempo mainnet.
  - Spec: https://paymentauth.org (repo `tempoxyz/mpp-specs`).
  - Docs: https://mpp.dev.
- **The flow** **[verified]**:
  1. Server → `402` with `WWW-Authenticate: Payment id=…, method="tempo", intent="charge", request=<base64url JSON>, expires=…, opaque=…`.
  2. Client retries with `Authorization: Payment <credential>`.
  3. Server → `200` with a `Payment-Receipt` header.
  - Challenges expire in about 5 minutes.
- **Intents:**
  - `charge`: one-off.
  - `session`: pay-as-you-go over a payment channel with off-chain vouchers; unused deposit is refunded.
  - `subscription`.
- **MCP transport:** JSON-RPC errors `-32042` (payment required) and `-32043`. The credential goes in `_meta["org.paymentauth/credential"]`.
- **SDKs:**
  - TypeScript: `mppx` (wevm, the viem team), v0.17.x, near-daily releases, middleware for Express, Hono, Next.js and Elysia, plus a CLI.
  - Others: Python `pympp`, Rust `mpp`, Go `mpp-go`, Ruby `stripe/mpp-rb`.
- **Stripe side** (`docs.stripe.com/payments/machine`):
  - Payments land as PaymentIntents, with refunds, Connect and fiat settlement.
  - Minimums: $0.50 for shared payment tokens, $0.01 for stablecoins.
  - Accepting stablecoins is US-only, excluding NY.
  - API version `2026-07-29.preview`.
- **x402 compatibility:** `mppx` can emit and accept both MPP and Coinbase's x402 on the same endpoint. 18 directory services already do this **[verified]**.
- **Honest status:**
  - Engineering is very active.
  - Real usage is thin: MPPScan shows about $2.9K total volume. x402 has roughly 20x the usage and 6.8K GitHub stars versus 189 for `mppx`.
  - The IETF draft (`draft-ryan-httpauth-payment`) has expired.
  - Verdict: not dead, but early. That leaves room for a standout POC.

## 2. Tempo and OUSD

- **Tempo:** Stripe/Paradigm payments L1. EVM-compatible, with no native gas token; fees are paid in USD stablecoins through a built-in Fee AMM.

  |          | Mainnet               | Testnet ("Moderato")           |
  |----------|-----------------------|--------------------------------|
  | Chain ID | `4217`                | `42431`                        |
  | RPC      | `https://rpc.tempo.xyz` | `https://rpc.moderato.tempo.xyz` |
  | Explorer | `explore.tempo.xyz`   | `explore.testnet.tempo.xyz`    |

- **Features worth demoing:**
  - 32-byte transfer memos (for reconciliation)
  - batched calls
  - fee sponsorship
  - access keys with spend limits
  - passkeys
  - payment lanes
  - TIP-20 tokens (address prefix `0x20c0…`)
- **OUSD = Open USD:**
  - Live 2026-09-30, governed by Open Standard (https://joinopenstandard.com). Bridge is reportedly the issuer.
  - Reserve yield is shared with the distributing partners.
  - Since launch day, it has been Stripe's default stablecoin.
  - Address (same on mainnet and testnet): `0x20c0000000000000000000006a37da5c996874be`.
- **Other Tempo tokens:**
  - USDC.e (Stargate-bridged USDC): `0x20c000000000000000000000b9537d11c60e8b50`. This is the token most MPP sellers charge in **[verified]**.
  - pathUSD (root quote token): `0x20c0000000000000000000000000000000000000`.
- **Tooling:**
  - `viem/tempo`
  - Foundry with Tempo support (`anvil --tempo`, `--tempo.fee-token`)
  - Tempo CLI (`curl -fsSL https://tempo.xyz/install | bash`)
  - MCP at `mcp.tempo.xyz`

## 3. What's actually live (probe of the mpp.dev directory)

We probed 1,520 of 1,600 endpoints across 138 services. Script and results are in `data/mpp-probe/`.

- **Coverage:** 953 challenges (402s) came back from 883 endpoints across 111 services.
- **No third-party endpoint accepts testnet.** Chains:
  - Tempo mainnet (4217): 1,114
  - Base: 16
  - Stripe live: 10
  - Solana: 2
- **Tempo tokens charged:**
  - USDC.e: 908
  - OUSD: 99, mostly Tempo's own `*.mpp.tempo.xyz` proxies for OpenAI, Anthropic, Firecrawl, fal and storage
  - pathUSD: 96
- **`session` intent:** only 59 challenges, from Dune, tempo-api, Tako, OpenAI and Anthropic.
- **MCP:** no paid MCP-transport server exists in the directory. `mpp.dev/mcp/services` is a free discovery MCP.
- **End-to-end testnet payment** **[verified]**: `npx mppx https://mpp.dev/api/ping/paid --network testnet` paid 0.10 test pathUSD and returned 200. Tx: https://explore.testnet.tempo.xyz/tx/0x9d19ad68ff1c5767a785a61b4525f1d3d88bd4879a02f82f81971bbadbafa619 (log in `data/mpp-probe/results/e2e_ping.txt`).

Cheapest real mainnet targets:

| Service | Price | Token | Intent |
|---|---|---|---|
| `api.tempo.xyz/v1/tokens` | $0.0001/req, $0.01 deposit | OUSD / pathUSD | session |
| `storage.mpp.tempo.xyz` | $0.0001 | OUSD / pathUSD / USDC.e | charge |
| `openai.mpp.tempo.xyz/v1/embeddings` | $0.0001 | OUSD | session |
| `firecrawl.mpp.tempo.xyz/v1/scrape` | $0.002 | OUSD | charge |
| `ipinfo.mpp.paywithlocus.com` | $0.001 | USDC.e | charge |

## 4. AgentCash (agentcash.dev) and the `stable*.dev` family

- **Who:** Merit Systems, the team behind x402scan and mppscan.
- **What:**
  - An agent wallet, CLI (`npx agentcash@latest`) and MCP server (`claude mcp add agentcash -- npx -y agentcash@latest`). It pays x402 *or* MPP from one balance.
  - A server SDK, `@agentcash/router`, with `.paid()`, `.upTo()` and `.session()`.
- **Merit's first-party paid origins**, each with an `/openapi.json`, dual x402 + MPP **[verified]**:
  - `stableenrich.dev`: Exa, Firecrawl, Google Maps, people and email enrichment.
  - `stablesocial.dev`: LinkedIn, GitHub, TikTok, IG at $0.06.
  - Also `stableemail`, `stablestudio`, `stabletravel`, `stableupload`.
  - `stablecrypto.dev`: crypto data.
  - Probably `stablefinance.dev` too (Merit branding not confirmed).
- **Caveats:**
  - Wallet keys are stored in plaintext at `~/.agentcash/wallet.json`.
  - The docs mislabel Tempo 4217 as testnet.
  - No OUSD support.
- **Verdict:** build the core on `mppx`; use AgentCash as an optional buyer-side convenience. (agentcache.dev, by contrast, is a parked domain.)

## 5. Paid financial data over 402

### StableFinance (`stablefinance.dev`)

- **Coverage:** US stocks only. No crypto, FX, options or international.
- **Price:** $0.02/call **[verified]**. Payable via:
  - MPP: Tempo USDC.e on chain 4217.
  - x402: Base USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, or Solana.
- **43 endpoints:**
  - OHLCV (day/week/month/year)
  - fundamentals (30+ years)
  - screener, SEC filings, earnings, insider trades, 13F, ETF holdings, news, policy rates
- **Limits:**
  - Price history advertised as only "3+ years".
  - Probably about 100 bars per call.
  - Split/dividend adjustment undocumented.
  - No dividends endpoint.
- **Source:** it wraps Financial Datasets AI, which notes "Non-Professional use" licensing.

### Other sources (all mainnet only)

| Source | Covers | Backtest-relevant | Price | Rail |
|---|---|---|---|---|
| **Massive** (formerly Polygon), `agent.massive.com` | US stocks, full history | `/v2/aggs/ticker/{T}/range/1/day/{from}/{to}`: 10y in one call, split-adjusted; delisted tickers via `active=false` | $0.01 | x402 only, Base USDC |
| **Alpha Vantage via Locus**, `alphavantage.mpp.paywithlocus.com` | Equities, FX, crypto, macro | daily `outputsize=full` (20y, unadjusted), FX daily, economic indicators | $0.008 **[verified]** | MPP, Tempo USDC.e (x402 twin exists) |
| **StableCrypto**, `stablecrypto.dev` | Crypto (CoinGecko, DefiLlama, …) | chart / ohlc / history | $0.01 **[verified]** | MPP + x402 |
| **EDGAR via Locus** | SEC XBRL | company facts (dividends workaround) | $0.008 | MPP |
| Financial Datasets direct, `api.financialdatasets.ai` | US stocks | prices, fundamentals | $0.02 | x402, Base |

- **Cost of a 20-ticker, 10-year daily backtest:**
  - Massive: about $0.20.
  - Alpha Vantage: about $0.16.
  - StableFinance: about $10, and it probably lacks 10 years of history.
- **Gap:** no 402 source serves dividends or total-return prices.

Raw challenge captures are in `data/finance-402-challenges/`.

## 6. The wider agentic-payments landscape (brief)

- **Stripe's two lanes:**
  - Human-delegated checkout: ACP plus Shared Payment Tokens, Link Agent Wallet, Issuing for agents.
  - Machine-to-machine: MPP, x402 acceptance, Tempo, Metronome-style metering.
  - Stripe positions itself as the neutral layer under every protocol.
- **Open problems people discuss:**
  - Spend policy enforced outside the model. The default x402 client had no spend cap until Aug 2026.
  - Intent receipts for disputes and refunds.
  - Sub-cent metering against settlement floors.
  - Fragmented discovery.
  - Merchant-side observability for agent traffic.
- **Overdone demo ideas:** generic pay-per-call paywalls, "agent buys a sandwich", pay-per-crawl clones.
