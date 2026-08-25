# PNCS USB Sysfs Read Effect v0.1

## Purpose

Provide a bounded read-only hardware observation boundary for PhaseNav Natural programs while preserving the frozen v0.26 write-effect contract.

The effect enumerates Linux USB devices through the canonical sysfs path:

`/sys/bus/usb/devices`

Every accepted node must resolve inside:

`/sys/devices`

Only a fixed whitelist of text attributes is readable.

## Runtime binding

Execution requires an exact v0.25 resident dispatch receipt. The dispatch origin generation must equal the live generation before and after the read. Operational receipts are append-only under:

`/dev/shm/ciel_noema/pncs/usb-sysfs-read-v0.1/receipts/`

No static runtime fallback exists in the operational path.

## Attribute whitelist

- `idVendor`
- `idProduct`
- `manufacturer`
- `product`
- `serial`
- `bcdDevice`
- `bcdUSB`
- `speed`
- `busnum`
- `devnum`
- `devpath`
- `version`
- `maxchild`

Each attribute is bounded to 4096 bytes and decoded as UTF-8 text.

## Effect authority

The contract admits only observation of sysfs metadata.

The following authorities remain closed:

- block-device write;
- raw USB write;
- SCSI/ATA mutation;
- vendor-specific command;
- firmware command;
- subprocess execution;
- network access.

The existing PNCS v0.26 effect contract remains unchanged and retains `device_allowed=False`.

## Evidence classes

A sysfs value is `REPORTED` evidence.

USB bus speed is kept separate from oscillator frequency.

Clock topology/frequency becomes `INFERRED` only after an identified controller is matched to a documented clock topology. A direct physical frequency observation remains `MEASURED`.

## USB crystal probe path

The native probe uses the internal path:

`USB identity -> reported snapshot -> controller candidate -> clock candidate -> evidence gate -> receipt`

The v0.1 read effect closes the first two stages. Controller-registry resolution is a separate data/evidence layer so an absent controller match remains explicit.

## Fail-closed rules

Execution fails if:

- the live NOEMA generation is stale or changes during the read;
- a canonical sysfs node resolves outside `/sys/devices`;
- a requested VID/PID has no match;
- a non-whitelisted attribute is injected into a snapshot;
- an attribute exceeds the fixed byte bound;
- receipt persistence cannot use the live `/dev/shm/ciel_noema` surface.
