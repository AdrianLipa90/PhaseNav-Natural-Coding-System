# PhaseNav USB Crystal Probe v0.2 Native

## Purpose

Resolve USB clock topology through the existing PhaseNav Natural execution architecture without introducing a parallel host-command client.

The probe consumes `PNCS_USB_DEVICE_SNAPSHOT_V0_1` objects produced by the bounded read-only sysfs effect and returns a content-addressed clock-evidence receipt.

## Native relation path

```text
USB snapshot
-> IDENTITY
-> CONDITION controller-registry match
-> ORDER evidence confidence
-> TRANSFORM documented controller -> clock candidate
-> CONDITION evidence classification
-> COMPOSITION probe receipt
```

The path uses the currently admitted internal operator subset for the probe relation itself.

## Evidence discipline

`REPORTED`
: bytes exposed by the canonical USB sysfs observation.

`INFERRED`
: clock topology or nominal oscillator frequency derived from an identified controller and a bound documentary reference.

`MEASURED`
: reserved for a direct physical/instrumental frequency observation. v0.2 does not synthesize this label from software timing.

`UNKNOWN`
: no sufficient controller-clock evidence match.

## Important invariant

USB link speed and oscillator frequency are separate fields.

For example, `speed=480` reported by Linux USB sysfs means the device is operating at a USB link-speed class represented in Mbit/s. The probe explicitly stores:

`usb_bus_speed_is_oscillator_frequency = false`

and does not derive a 480 MHz, 12 MHz, 24 MHz or any other oscillator solely from that field.

## Controller registry

A controller record may bind:

- USB VID;
- USB PID;
- product substring;
- controller vendor;
- controller family;
- controller part number;
- clock topology;
- nominal frequency where documented;
- evidence reference;
- confidence.

Matching records are ordered by confidence and stable record ID. Without a match the receipt remains `UNKNOWN`.

## SanDisk Cruzer Blade target

The current target may be filtered with SanDisk VID / Cruzer Blade PID when the actual sysfs receipt confirms them. The repository does not freeze a controller part number or crystal frequency for the product family without controller evidence from the tested hardware revision.

## Next gate

Run the native sysfs read effect on the physical Cruzer Blade through the live `/dev/shm/ciel_noema` runtime, bind the resulting snapshot receipt, identify the controller through a documented registry record if possible, and emit the first hardware-specific crystal-probe receipt.
