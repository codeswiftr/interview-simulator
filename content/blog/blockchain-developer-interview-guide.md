---
title: "Blockchain and Smart Contract Developer Interview Guide"
description: "Technical interview preparation for blockchain engineering roles: Ethereum smart contract development with Solidity, EVM internals, DeFi protocol architecture, security vulnerabilities, and what crypto companies like Coinbase, Uniswap, Aave, and Consensys expect from engineers."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

Blockchain engineering interviews are technically demanding and span a wide surface area: EVM internals, Solidity edge cases, DeFi protocol mechanics, security vulnerabilities, and Layer 2 scaling. Companies hiring in this space expect candidates to have hands-on experience with smart contract development and a working knowledge of the attack surface that comes with deploying immutable code to a public network. This guide covers the core topics you need to own before walking into any of these interviews.

## Ethereum Fundamentals

**Accounts** in Ethereum come in two forms. Externally Owned Accounts (EOAs) are controlled by private keys and can initiate transactions. Contract accounts have no private key — they are controlled by their deployed bytecode and execute when called. Contract accounts hold code, storage, and balance; EOAs hold only balance and a nonce.

**Transactions** on Ethereum are signed messages from EOAs that either send ETH, deploy a contract (no `to` field, `data` is the init bytecode), or call a contract function. Every transaction consumes gas.

**The gas model post-EIP-1559** splits the fee into two parts: a `baseFee` that is burned and dynamically adjusted each block based on demand, and a `priorityFee` (tip) paid to the validator. You specify `maxFeePerGas` and `maxPriorityFeePerGas`. The actual fee paid is `min(maxFeePerGas, baseFee + priorityFee)`. This replaced the first-price auction model and made fee estimation more predictable.

**The EVM** is a stack-based virtual machine. Opcodes like `PUSH`, `ADD`, `SLOAD`, `SSTORE`, `CALL`, and `DELEGATECALL` operate on a 256-bit word stack. Gas costs are opcode-specific — storage operations (`SSTORE`) are expensive because they modify persistent state. Understanding the EVM at the opcode level matters when optimizing contracts for gas or reasoning about what compiled Solidity actually does.

## Solidity Smart Contract Development

**Storage layout** is one of the most commonly tested topics. Each storage slot holds 32 bytes. Variables are packed into slots in declaration order when they are smaller than 32 bytes. For example, two `uint128` values pack into a single slot; a `uint8` followed by a `uint256` wastes a full slot because the `uint256` cannot share a slot. Mappings and dynamic arrays use hash-derived slots and do not pack.

**Function visibility**:
- `public` — callable externally and internally; generates an ABI entry
- `external` — callable only from outside the contract; more gas-efficient for large calldata because arguments are read from `calldata` rather than copied to memory
- `internal` — only callable within the contract and derived contracts
- `private` — only callable within the defining contract

**`payable`** allows a function (or the contract itself) to receive ETH. Without it, a plain ETH transfer to a function reverts.

**`fallback` and `receive`** are special functions. `receive()` handles plain ETH transfers (no calldata). `fallback()` handles calls with calldata that match no function selector, and optionally ETH if marked `payable`. Proxy patterns depend heavily on `fallback` to delegate calls to implementation contracts.

**Events and logs** are the standard mechanism for off-chain indexing. Emitted events are stored in transaction receipts as logs, not in contract storage. They are cheap to emit relative to storage writes. Indexed parameters (up to three per event) become topics that can be filtered efficiently by off-chain consumers.

## Security Vulnerabilities

Blockchain interviews routinely probe your understanding of known vulnerabilities. Expect to explain attack mechanics, not just name them.

**Reentrancy** — The DAO hack (2016, $60M) was a reentrancy attack. A malicious contract calls back into the victim before the victim updates its balance. The fix: use the checks-effects-interactions pattern (update state before external calls) or a reentrancy guard mutex. OpenZeppelin's `ReentrancyGuard` is the standard reference implementation.

**Integer overflow/underflow** — Before Solidity 0.8, arithmetic silently wrapped. `uint8(255) + 1 == 0`. The SafeMath library from OpenZeppelin added overflow checks. Solidity 0.8+ introduced built-in overflow checks that revert on overflow; you only bypass them with `unchecked {}` when you explicitly want wrapping arithmetic for gas savings.

**Access control bugs** — Missing or incorrect `onlyOwner`-style modifiers, unprotected `initialize()` functions in upgradeable contracts, and improper role management in complex governance systems. The Parity multisig wallet hack (2017) was an access control failure on an unprotected initialization function.

**Front-running and MEV** — Miners (and now validators through MEV) can reorder, insert, or censor transactions within a block. Sandwich attacks on DEX trades are the canonical example: a bot sees a large pending swap, front-runs it to move the price, lets the victim trade at a worse price, then back-runs to profit. Mitigations include commit-reveal schemes, slippage tolerance, and private mempools (Flashbots Protect).

**Oracle manipulation** — On-chain price oracles that read from a single AMM pool in a single transaction are vulnerable to flash loan manipulation. An attacker borrows a large amount, distorts the spot price, exploits a protocol that reads the manipulated price, then repays the loan in the same transaction. Time-weighted average price (TWAP) oracles like Uniswap v3's are harder to manipulate because they average over many blocks.

## DeFi Protocol Concepts

**AMMs and the constant product formula** — Uniswap v2 uses `x * y = k`. The pool holds reserves of two tokens; the product must remain constant after any trade (excluding fees). Larger trades cause more slippage because they move the ratio further along the curve. Uniswap v3 introduced concentrated liquidity, allowing LPs to provide liquidity within custom price ranges.

**Liquidity pools** — LPs deposit token pairs and receive LP tokens representing their share of the pool. They earn a fraction of every swap fee. They are exposed to impermanent loss when the price ratio between the two tokens changes relative to the time of deposit.

**Lending protocols** — Aave and Compound implement over-collateralized lending. Borrowers post collateral worth more than their loan. Interest rates are algorithmic, based on utilization ratio. If collateral value drops below the liquidation threshold, liquidators can repay the debt and receive the collateral at a discount.

**Flash loans** — Uncollateralized loans that must be borrowed and repaid within a single transaction. If repayment fails, the entire transaction reverts. They are used for arbitrage, liquidations, and (maliciously) oracle manipulation.

## Testing and Tooling

**Hardhat vs. Foundry** — Hardhat is a JavaScript/TypeScript-based development environment. Foundry (maintained by Paradigm) is a Rust-based toolchain where tests are written in Solidity using the `forge` test runner. Foundry is faster and increasingly preferred for new projects. Writing tests in Solidity means you can test internal functions directly without deploying to a network.

**Static analysis** — Slither (Trail of Bits) analyzes Solidity source for common vulnerability patterns. Mythril uses symbolic execution to explore execution paths and find vulnerabilities. Both should run in CI.

**Fuzz testing** — Echidna (Trail of Bits) is a property-based fuzzer for Solidity. You define invariants (e.g., total supply must equal sum of balances) and Echidna generates thousands of randomized inputs to try to violate them. Foundry's built-in fuzzing via `forge test` supports simple property-based tests. Fuzz testing has caught critical bugs before deployment.

## Layer 2 and Scaling

**Optimistic rollups** (Optimism, Arbitrum) execute transactions off-chain and post compressed transaction data to Ethereum as calldata. They assume transactions are valid unless challenged within a fraud proof window (typically 7 days for withdrawals). Lower latency and cheaper than L1, but the dispute window adds withdrawal delay.

**ZK rollups** (zkSync, Starknet, Polygon zkEVM) generate a cryptographic validity proof (SNARK or STARK) for each batch of transactions. Proofs can be verified on L1 in minutes, eliminating the fraud proof window. Computationally more intensive to generate proofs, but withdrawals are faster.

**Calldata costs** are central to L2 economics. EIP-4844 (proto-danksharding) introduced blob-carrying transactions, which provide cheaper temporary data availability for rollups compared to posting calldata to L1 permanently.

**Bridging** involves locking assets on L1 and minting wrapped equivalents on L2, or vice versa. Bridge contracts are high-value targets — the Ronin bridge hack ($625M, 2022) and Wormhole exploit ($320M, 2022) are the canonical failures.

## Who Hires Blockchain Engineers

- **Coinbase** — infrastructure, wallet, and DeFi product teams; strong emphasis on security and reliability engineering
- **Binance** — exchange infrastructure, BNB Chain development
- **Consensys** — MetaMask, Infura, auditing; deep Ethereum protocol work
- **Uniswap Labs** — protocol development, AMM research, front-end integration with contracts
- **a16z crypto portfolio companies** — broad range from L1 protocols to DeFi applications to NFT infrastructure
- **Traditional finance blockchain teams** — JPMorgan Onyx, Fidelity Digital Assets, and similar institutions hire engineers for permissioned ledger and tokenization work; interviews here lean more toward system design and less on DeFi-specific knowledge

Most serious protocol companies will give you a take-home involving a smart contract with planted vulnerabilities and ask you to find and fix them. Practice reading unfamiliar contracts, running Slither, writing Foundry tests, and explaining your findings clearly.
