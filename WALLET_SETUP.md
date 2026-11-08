# Wallet setup: about $5 of mainnet funds for the backtester

The app's data sources take payment on two chains, and both are mainnet only:

| Rail | Chain | Token | Used by |
|---|---|---|---|
| **MPP** | Tempo mainnet (chain `4217`) | **USDC.e** `0x20c000000000000000000000b9537d11c60e8b50` | Alpha Vantage via Locus, StableFinance, StableCrypto, EDGAR via Locus |
| **x402** | Base mainnet (chain `8453`) | **USDC** `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` | Massive (best long-history price data) |
| *(optional)* MPP | Tempo mainnet | **OUSD** `0x20c0000000000000000000006a37da5c996874be` | Tempo-run proxies (`*.mpp.tempo.xyz`) and your own server |

Both are EVM chains, so **one private key gives you the same address on Tempo and on Base**. You fund that address on each chain.

**Suggested split:**
- about **$3 USDC.e on Tempo**
- about **$2 USDC on Base**
- about **$1 of ETH on Base** for gas, only if you bridge from Base (step 3)

A full POC run should spend well under $1.

> ⚠️ This is a hot wallet with a key on disk. Use a **brand-new key** for this project only, keep the balance small, and never commit the key. `.env` is git-ignored in this repo.

---

## 1. Create a dedicated key

Pick **one** option.

```bash
# Option A: Foundry
cast wallet new
```

```bash
# Option B: mppx (stores the key in mppx's local account store)
npx mppx account create
```

Put the key in `.env`, which is git-ignored:

```bash
PAYER_PRIVATE_KEY=0x...
PAYER_ADDRESS=0x...
```

Check that the address is right before you send anything to it.

## 2. Get USDC onto Base

The simplest path is to buy USDC on Coinbase (or another exchange) and **withdraw it to `PAYER_ADDRESS` on the Base network**.
- On Coinbase, USDC withdrawals to Base are typically free or close to free.
- Double-check that the network selector says **Base**. Sending to the wrong network can lose funds.

Also withdraw about $1 of ETH on Base if you'll bridge with Stargate in step 3.

What this funds:
- **x402 payments on Base need no ETH.** The client only signs an EIP-3009 authorization, and the seller's facilitator pays the gas.
- **The Base USDC also covers Massive.**

## 3. Get USDC.e onto Tempo

USDC.e on Tempo is **Stargate-bridged USDC**. Options, in rough order of simplicity:

1. **Tempo Wallet / Tempo CLI:**
   - Go to https://wallet.tempo.xyz, or run `curl -fsSL https://tempo.xyz/install | bash`, then `tempo wallet login` and `tempo wallet fund`.
   - These may offer an onramp or bridge flow.
   - *Unverified on mainnet:* check what `tempo wallet fund` does there before relying on it.
   - Note that the Tempo Wallet may use a passkey account, which is a different address from your `.env` key. If so, transfer the USDC.e from it to `PAYER_ADDRESS` afterwards.
2. **Stargate bridge** (https://stargate.finance):
   - Bridge USDC from Base to Tempo, with the destination set to `PAYER_ADDRESS`.
   - Needs a little Base ETH for gas.
3. **Exchange withdrawal:** if your exchange lists Tempo as a withdrawal network for USDC, withdraw directly. Check it lands as USDC.e (`0x20c0…b9537d11c60e8b50`).

What you **don't** need on Tempo:
- No gas token. Tempo has none; fees are paid in a USD stablecoin and are typically under $0.001.
- Many MPP challenges set `feePayer: true`, which means the server sponsors the fee entirely.

## 4. (Optional) Get some OUSD

Only needed to pay Tempo's own `*.mpp.tempo.xyz` services in OUSD, or to test your own OUSD-priced server on mainnet.
- Swap USDC.e → OUSD on Tempo's built-in stablecoin DEX. See https://viem.sh/tempo/guides/stablecoin-exchange.
- Or use a Tempo Wallet swap, if offered.

For **testnet** OUSD (free), use the faucet. Testnet funds don't work against any real data provider.

```bash
npx mppx account fund --network testnet
```

## 5. Verify balances

```bash
# Tempo mainnet: USDC.e (6 decimals)
cast call 0x20c000000000000000000000b9537d11c60e8b50 "balanceOf(address)(uint256)" $PAYER_ADDRESS --rpc-url https://rpc.tempo.xyz
```

```bash
# Tempo mainnet: OUSD
cast call 0x20c0000000000000000000006a37da5c996874be "balanceOf(address)(uint256)" $PAYER_ADDRESS --rpc-url https://rpc.tempo.xyz
```

```bash
# Base mainnet: USDC
cast call 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 "balanceOf(address)(uint256)" $PAYER_ADDRESS --rpc-url https://mainnet.base.org
```

You can also look the address up in an explorer:
- Tempo: https://explore.tempo.xyz/address/<PAYER_ADDRESS>
- Base: https://basescan.org/address/<PAYER_ADDRESS>

## 6. Smoke test with one real paid call (about $0.008)

```bash
npx mppx "https://alphavantage.mpp.paywithlocus.com/<path>?symbol=SPY"
```

- Find the exact path and params in the Locus docs: https://paywithlocus.com/mpp/alphavantage.md
- If `mppx` doesn't pick up your `.env` key automatically, use the account created with `npx mppx account create`, or pass the key in code via viem's `privateKeyToAccount`.

You should see:
1. a 402 challenge for 8000 base units of USDC.e on chain 4217
2. a 200 with JSON
3. a `Payment-Receipt` whose `reference` is a tx hash you can open on explore.tempo.xyz

## Safety checklist

- [ ] New key, used only for this project
- [ ] Balance kept to about $5 or less
- [ ] `.env` is git-ignored, and you've checked `git status` before every commit
- [ ] The app enforces a hard spend cap (see `PROMPT.md`)
- [ ] When you're done, sweep leftover funds back to a wallet you control long-term
