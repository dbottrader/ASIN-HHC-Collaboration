# Decision Record — ASIN-NCEA Integrated Harness v0.1

```text
date_utc: 2026-07-23
artifact: ASIN-NCEA_INTEGRATED_HARNESS_v0.1
status: PASS_WITH_HOLD
evidence_level: E3_LOCAL_INTEGRATION
promotion_verdict: HOLD
witness_class: MACHINE_EXECUTION_UNATTESTED
```

## Decision

Preserve the ASIN-NCEA text snapshots as lineage evidence and integrate the usable architecture into a clean local harness rather than promoting the raw snapshot code as production cryptography.

## Rationale

The raw v2.0 lineage has a dependency/import mismatch around `Crypto` versus `Cryptodome`, and the raw encryption/decryption design has unresolved deterministic key-recovery concerns. The integrated harness keeps the lineage visible while moving the architecture test onto standard primitives:

- HKDF-SHA256
- ChaCha20-Poly1305 AEAD
- Ed25519 signed receipt
- canonical JSON and SHA-256 hashes
- hash-linked ledger and Merkle root
- gated HHC-SIM reward simulation

## Local run anchors

```text
bundle_sha256: 14e3eaaf71461e35d31f185ed3c84083c516539a057e66c1bb3f5485da7c9807
source_entries: 13
source_hashes_ok: true
source_syntax_ok: true
raw_v2_runtime_ready: false
integrated_core_pass: true
deterministic_core_hash: ee93c43c62eccb6dd9eaf14787bdfe6af2965f66763216221f504af282447274
ledger_merkle_root: ffc27df9d1d33a454e858284b19694c5c7513a9833e25113550f0acd8ec68405
```

## Claim boundary

Can claim:

- integrated local architecture harness exists
- source snapshot hashes and syntax passed in the sealed local bundle
- integrated AEAD/tamper/signature/ledger checks passed locally
- HHC-SIM mint gate only opens after verification checks pass

Cannot claim:

- production cryptographic security
- live token issuance
- external consensus
- independent human reproduction
- promotion beyond HOLD

## Cross-repo placement

```text
core implementation: dbottrader/Holbrook-CP8-HHC
artifact registry: dbottrader/ASIN-HHC-Artifacts
token boundary note: dbottrader/ASINHHCCP8-Token-Project-
```