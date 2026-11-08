# mpp-402-backtester

Research and build plan for a proof of concept: a **portfolio backtester that buys its own market data per request over HTTP 402**. It uses Stripe/Tempo's **Machine Payments Protocol (MPP)** on Tempo mainnet, plus Coinbase's **x402** on Base. It can optionally **sell** backtests back over MPP, priced in **OUSD**.

This repo currently holds research only. Nothing is built yet.

| File | What it is |
|---|---|
| [`RESEARCH.md`](RESEARCH.md) | Findings as of 2026-11-07: MPP, Tempo/OUSD, AgentCash and the `stable*.dev` APIs, paid financial-data sources and prices, the agentic-payments landscape |
| [`PROMPT.md`](PROMPT.md) | A self-contained brief for a coding agent to build the app on mainnet with about $5 |
| [`WALLET_SETUP.md`](WALLET_SETUP.md) | How to create a dedicated key and fund USDC.e on Tempo and USDC on Base |
| [`mockup/`](mockup/) | Clickable UX mockup: a single static `index.html` with simulated data and payments. Open it locally or deploy it with `vercel deploy` |
| [`data/mpp-probe/`](data/mpp-probe/) | Probe scripts and results for the whole mpp.dev service directory: 1,520 endpoints, decoded 402 challenges, one end-to-end testnet payment log |
| [`data/finance-402-challenges/`](data/finance-402-challenges/) | Raw 402 responses from the finance-data providers, plus finance-related x402 Bazaar listings |
| [`data/agentcash/`](data/agentcash/) | AgentCash's `/.well-known/x402` manifest |

## Key findings

- MPP works end to end. We paid `mpp.dev/api/ping/paid` on Tempo testnet: [tx](https://explore.testnet.tempo.xyz/tx/0x9d19ad68ff1c5767a785a61b4525f1d3d88bd4879a02f82f81971bbadbafa619).
- **Every third-party MPP service is mainnet only.** Most charge USDC.e on Tempo; 99 challenges accept OUSD.
- **StableFinance is US stocks only.** Its crypto counterpart is StableCrypto.
- **The best long-history price data is Massive**, at $0.01 per call, but it is x402 / Base only.
- **A 20-ticker, 10-year backtest costs about $0.20 in data.**

The data snapshots are third-party API metadata captured on 2026-11-07, included for reproducibility. Prices and endpoints change.
