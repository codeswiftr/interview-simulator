# Blockchain and Web3 Engineer Interview Guide

Web3 engineering interviews are technically demanding in unusual ways. You are expected to understand cryptography, distributed consensus, economic incentive design, and smart contract security — simultaneously. Most software engineering preparation resources do not cover this intersection. This guide focuses on the technical depth required for blockchain engineering roles at companies like Coinbase, Consensys, Alchemy, Chainalysis, Uniswap Labs, and infrastructure-facing Web3 companies.

## The Cryptographic Foundations You Actually Need

Blockchain engineering requires genuine cryptography knowledge, not just awareness that cryptography exists. The good news: you do not need to implement cryptographic primitives. The knowledge you need is conceptual but specific.

**Hash functions**: Understand SHA-256 and Keccak-256 (Ethereum's choice) as one-way functions with collision resistance. Know that the proof-of-work puzzle is finding an input (nonce) that produces a hash below a target value — this is computationally hard to produce but trivially easy to verify. Know the properties: deterministic, fixed output size, avalanche effect (small input change → completely different hash).

**Digital signatures (ECDSA)**: Ethereum uses Elliptic Curve Digital Signature Algorithm over the secp256k1 curve (same as Bitcoin). A private key is a random 256-bit integer. The public key is a point on the elliptic curve. The Ethereum address is the last 20 bytes of the Keccak-256 hash of the public key. Understanding this chain — private key → public key → address — is fundamental because it explains why Ethereum addresses are not public keys, why address recovery is possible from a signature, and why private key security is absolute (no recovery mechanism exists).

**Merkle trees**: Transactions in a block are organized as a Merkle tree. Each leaf is a transaction hash; each internal node is the hash of its two children. The Merkle root summarizes all transactions in O(1) bytes. Merkle proofs allow proving a transaction is in a block in O(log n) space without downloading all transactions — essential for light clients.

## Smart Contract Security: The Unique Engineering Domain

Smart contracts are immutable programs running on a shared computer with no administrator access. Bugs cannot be patched; they must be worked around via proxy contracts or abandoned. This creates a security model unlike any other software engineering context.

**Reentrancy**: The most famous exploit pattern. The DAO hack (2016, $50M) used reentrancy. The vulnerability occurs when a contract sends ETH to an external address before updating its own state:

```solidity
// VULNERABLE
function withdraw(uint amount) external {
    require(balances[msg.sender] >= amount);
    // ETH transfer happens here — attacker's fallback function re-enters
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success);
    balances[msg.sender] -= amount; // State update happens too late
}

// FIXED: Check-Effects-Interactions pattern
function withdraw(uint amount) external {
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount;  // Update state first
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success);
}
```

**Integer overflow/underflow**: Before Solidity 0.8.0, arithmetic operations wrapped silently. Sending 1 token to an address with balance of 0 could wrap to 2^256-1. The fix is Solidity 0.8.0's built-in overflow checks, or using OpenZeppelin's SafeMath for older contracts.

**Front-running (MEV)**: Ethereum's mempool is public. Miners (now validators) and bots can see pending transactions and insert their own transactions ahead of (or around) them. This is Maximal Extractable Value (MEV). DEX traders routinely have their trades sandwiched — a bot buys before them (price goes up), their trade executes at worse price, bot sells (price goes back down). Understanding MEV is essential for DeFi protocol engineering.

## Consensus Mechanisms: What the Interview Actually Tests

Consensus is a common interview topic at blockchain companies. The key questions are not "explain Nakamoto consensus" — they are about trade-offs:

**Proof of Work vs. Proof of Stake**: PoW selects block producers via computational lottery (hash rate = probability of winning). PoS selects via staked capital (32 ETH for Ethereum validators). PoS is faster to finality, uses ~99.95% less energy, but introduces new attack vectors (long-range attacks, nothing-at-stake problem — mitigated by slashing).

**Finality**: Bitcoin has probabilistic finality — a transaction is "safe" after 6 blocks (~60 minutes) but never mathematically final. Ethereum post-Merge has checkpoint finality — once a checkpoint is finalized by 2/3 of validators, it cannot be reorged (Casper FFG). This distinction matters for exchange deposit confirmation requirements.

**Layer 2 scaling**: Rollups (Optimistic and ZK) execute transactions off-chain and post compressed data to L1. Optimistic rollups (Arbitrum, Optimism) assume transactions are valid and have a 7-day challenge window. ZK rollups (StarkNet, zkSync) generate cryptographic proofs of execution validity — no challenge period needed, but proof generation is computationally intensive. Understanding this trade-off (7-day withdrawal vs. proof overhead) is a common system design topic.

## The EVM and Gas: How Smart Contract Execution Works

The Ethereum Virtual Machine is a stack-based, sandboxed computation environment where every operation costs gas. Gas prevents infinite loops (Turing completeness requires a halting mechanism) and prices computation by computational cost.

Key gas economics for interviews:
- Storage is extremely expensive (20,000 gas to write a new storage slot, ~100x more than computation)
- Calldata is cheaper than storage — use events for historical data that does not need to be read by contracts
- SLOAD costs 2,100 gas cold, 100 gas warm — cache storage reads in memory variables within a function
- Loop over large arrays is dangerous (unbounded gas cost can cause transactions to fail)

Gas optimization is a real engineering discipline at Web3 companies. Questions like "how would you reduce gas cost for this contract" are common.

## Interview Preparation by Company Type

**Exchange and custody (Coinbase, Kraken)**: Focus on wallet security (HSMs, multi-sig, threshold signatures), transaction signing workflows, and blockchain monitoring infrastructure. Less smart contract focus; more traditional backend + security.

**DeFi protocol (Uniswap Labs, Aave, Compound)**: Deep smart contract knowledge, AMM mathematics (constant product formula x*y=k), liquidity provision economics, MEV awareness, audit processes.

**Infrastructure (Alchemy, Infura, QuickNode)**: Node infrastructure (running Ethereum full nodes, archive nodes), JSON-RPC API engineering, indexing blockchain state, high-availability RPC infrastructure.

**Analytics and compliance (Chainalysis, TRM Labs)**: Graph analysis of blockchain transactions, entity clustering (identifying exchanges, mixers, known bad actors), UTXO vs. account model differences.

Know which category your target company falls into and weight your preparation accordingly. The smart contract security knowledge needed at a DeFi protocol is largely irrelevant at a blockchain analytics company.
