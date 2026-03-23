---
title: "Web3 and Crypto Engineer Interview Guide"
description: "Technical interview preparation for Web3 and blockchain engineering roles: Solidity smart contracts, EVM internals, DeFi protocol architecture, wallet and key management, Layer 2 scaling solutions, and what crypto companies and blockchain teams expect from senior Web3 engineers."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

Web3 engineering sits at one of the most demanding intersections in software: distributed systems, cryptography, financial protocol design, and adversarial security. Interviewers at crypto companies expect you to navigate all four fluently. This guide covers what senior Web3 roles demand and how to demonstrate that fluency under pressure.

## The Web3 Engineering Landscape

Web3 roles divide into two broad tracks. **On-chain engineers** write and audit smart contracts, design token economics, and implement DeFi protocols. **Off-chain engineers** build the indexers, RPC nodes, oracles, wallet infrastructure, and APIs that make contracts usable at scale. Most senior roles span both.

Understanding where a company sits matters before your interview. A protocol team like Uniswap Labs or Aave cares deeply about contract correctness and gas efficiency. An exchange like Coinbase or Kraken prioritizes custody architecture, key management, and regulatory compliance. A bridge or L2 team (Arbitrum, Optimism) focuses on fraud proof systems and cross-chain security. Know which track you are interviewing for, and tailor accordingly.

## Solidity Fundamentals

Interviewers probe Solidity at the language level, not just the API level. You should understand:

**Storage layout** — state variables in Solidity are packed into 32-byte slots in declaration order. Structs and arrays have their own layout rules. Misunderstanding this causes gas waste and, in some cases, storage collisions in proxy patterns.

**Gas optimization** — every opcode costs gas. Common optimizations include using `calldata` instead of `memory` for function parameters, packing structs, using `unchecked` arithmetic where overflow is impossible, and caching storage reads in local variables. Expect to be handed a contract and asked to identify inefficiencies.

**Reentrancy** — the canonical Web3 vulnerability. External calls can re-enter your contract before state is updated. The fix is the checks-effects-interactions pattern: update state before making external calls. Reentrancy guards (OpenZeppelin's `ReentrancyGuard`) add defense in depth but do not replace proper ordering.

**OpenZeppelin** — know the standard libraries: `ERC20`, `ERC721`, `Ownable`, `AccessControl`, `Pausable`, `SafeERC20`. Interviewers expect you to know why `SafeERC20` exists (non-standard ERC20 tokens that return false instead of reverting).

## EVM Internals

Understanding the Ethereum Virtual Machine is what separates mid-level from senior Web3 engineers. The EVM is a stack machine: operations pop values off the stack, compute, and push results back. There is no direct access to registers.

**Opcodes** — you should recognize the gas-heavy ones. `SLOAD` (reading from storage) costs 2100 gas cold and 100 gas warm. `SSTORE` (writing to storage) costs up to 22,100 gas for a cold write to a new slot. These costs drive almost every gas optimization decision.

**The gas model** — gas is execution fuel. Every opcode has a base cost. The block gas limit bounds total computation per block. Understanding this is essential for estimating whether a function will fit in a block and for avoiding denial-of-service vectors in loops over unbounded arrays.

**Memory vs. storage vs. calldata** — memory is cheap but ephemeral. Storage is expensive and persistent. Calldata is read-only but cheapest for input data. Know when to use each.

## DeFi Protocol Architecture

**AMMs** — Uniswap V2's constant product formula (`x * y = k`) is foundational. You should be able to derive the swap output formula, explain impermanent loss, and describe why price impact grows with trade size relative to pool liquidity. Uniswap V3's concentrated liquidity changes the mechanics significantly — know the tradeoffs.

**Lending protocols** — Aave and Compound use collateralization ratios, liquidation thresholds, and interest rate models. Understand how health factors work, what triggers liquidation, and how flash loans function (borrow without collateral as long as you repay within the same transaction).

**Oracles** — Chainlink provides tamper-resistant price feeds via a decentralized network of nodes. Oracle manipulation is a common attack vector: if a protocol trusts a single on-chain AMM price, a flash loan can skew it within one transaction. Interviewers often present oracle manipulation scenarios as design questions.

## Wallet Infrastructure

**HD wallets** — hierarchical deterministic wallets derive all keys from a single seed phrase using BIP-32 (derivation algorithm), BIP-39 (mnemonic encoding of the seed), and BIP-44 (derivation path conventions across coin types and accounts). Know the derivation path structure: `m / purpose' / coin_type' / account' / change / address_index`.

**Custodial vs. non-custodial** — custodial wallets (Coinbase, Kraken) hold private keys on behalf of users. Non-custodial wallets (MetaMask, hardware wallets) give users sole control. The tradeoff is security vs. recoverability. Exchanges need to understand MPC (multi-party computation) and HSM (hardware security module) architectures for custody.

**Hardware wallets** — Ledger and Trezor keep private keys on dedicated secure elements. Signing happens on-device; the host computer never sees the key. Know the signing flow and why it matters for institutional custody.

## Layer 2 Scaling

**Optimistic rollups** (Optimism, Arbitrum) — transactions are posted to L1 and assumed valid by default. A challenge window (typically 7 days) allows fraud proofs to be submitted. This delay is the core tradeoff: lower cost, high security, but slow finality for L1 withdrawals.

**ZK rollups** (zkSync, StarkNet) — transactions are bundled with a cryptographic validity proof (SNARK or STARK) that mathematically proves correct execution. Finality is fast once the proof verifies on L1. The tradeoff: proving is computationally expensive, and supporting arbitrary EVM opcodes in circuits is hard.

**Bridge security** — cross-chain bridges have been the largest source of crypto losses. Know the attack surfaces: validator collusion, message replay, oracle manipulation, and upgrade key compromises.

## Testing Smart Contracts

**Hardhat and Foundry** are the dominant testing frameworks. Foundry (written in Rust) has become preferred for smart contract testing because tests are written in Solidity, enabling fast execution and native fuzz testing via `forge fuzz`.

**Fuzzing** — Foundry's fuzzer generates random inputs to find edge cases. Formal verification tools (Certora Prover, Halmos) go further, proving invariants hold across all possible inputs. Senior candidates should be familiar with both approaches.

## Security Auditing

Security auditing is the most valued and highest-compensated skill in Web3. The attack surface is large:

- **Reentrancy** — covered above; still responsible for major losses
- **Flash loan attacks** — using uncollateralized loans to manipulate prices or governance
- **Oracle manipulation** — skewing on-chain price feeds within a transaction
- **Access control failures** — missing `onlyOwner` modifiers, incorrect role checks
- **Integer overflow/underflow** — Solidity 0.8+ checks by default, but `unchecked` blocks reintroduce risk
- **Front-running** — MEV bots watching the mempool can sandwich trades

Companies hiring senior engineers expect you to read a contract and identify vulnerabilities, not just fix them. Practice with historical DeFi exploits — the Nomad bridge, Euler Finance, and Curve reentrancy exploits are worth studying in detail.

## Who Hires Web3 Engineers

**Protocols and DeFi**: Uniswap Labs, Aave, Compound, Curve, and Chainlink hire smart contract engineers with deep DeFi domain knowledge.

**L2 and infrastructure**: Arbitrum, Optimism, zkSync, and StarkNet need engineers who understand rollup mechanics, fraud proofs, and bridge security.

**Exchanges and custody**: Coinbase, Kraken, and Binance prioritize key management, regulatory compliance, and high-availability trading infrastructure.

**Crypto hedge funds**: Jane Street Crypto, Cumberland, and specialist crypto funds hire engineers for trading infrastructure, MEV, and protocol research.

The Web3 job market rewards depth. Pick a specialization — smart contract security, DeFi protocol design, or L2 infrastructure — and go deep. Interviewers can tell the difference between someone who has read documentation and someone who has shipped production contracts and debugged live exploits.
