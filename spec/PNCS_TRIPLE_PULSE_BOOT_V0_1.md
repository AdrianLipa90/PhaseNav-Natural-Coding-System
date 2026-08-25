# PNCS Triple Pulse Boot Contract v0.1

Canonical sequence:

`IDENTITY -> DOMAIN -> AUTHORITY -> REQUEST -> COUPLING -> ADMISSION`

The first three stages are ordered boot pulses. Each pulse binds a receipt. All three receipts must belong to the same current runtime generation. Admission fails closed on missing, stale, invalid, or cross-generation pulse evidence.

The contract wraps the existing persistent runtime and admission rules. It preserves `/dev/shm/ciel_noema`, current-memory recovery, tether guard, atomic hydration, and O(1) repeated admission after successful session boot.

Native witness: `native/PNCS_TRIPLE_PULSE_BOOT_V0_1.pnv`.

No new PNV opcodes are introduced.

Motto: `Verbis utor, informationem in existentiam converto.`
