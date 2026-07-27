# GPU HDMI/DP Pin Diagnosis Reference

## Background

GPU HDA controllers (NVIDIA, AMD, Intel iGPU) expose multiple HDMI/DisplayPort audio pins. Each pin is a separate ALSA PCM device. The kernel's `snd_hda_intel` driver enumerates them, and ALSA exposes them as `hw:card,device` (e.g. `hw:0,0` through `hw:0,9`).

WirePlumber creates a separate node for each pin's active profile. The node names follow the pattern:

```
alsa_output.pci-XXXX_XX_XX.X.hdmi-stereo       → hw:0,0 (pin 0)
alsa_output.pci-XXXX_XX_XX.X.hdmi-stereo-extra1 → hw:0,1 (pin 1)  
alsa_output.pci-XXXX_XX_XX.X.hdmi-stereo-extra2 → hw:0,2 (pin 2)
alsa_output.pci-XXXX_XX_XX.X.hdmi-stereo-extra3 → hw:0,3 (pin 3)
```

## Why names shuffle

The `node.description` shown in UIs (e.g. "HDMI 2", "HDMI 3") is derived from `alsa.name`, which comes from the HDA codec's pin widget. The **numbering of these names is not stable** — it depends on:

1. GPU firmware pin enumeration order (can change with driver updates)
2. Which pins have active EDID (monitor connected)
3. Hotplug events during boot

So `hdmi:0,2` (ALSA device 2, physical pin NID 0x5) might be labeled "HDMI 2" on one boot and "HDMI 3" on the next.

## ELD (EDID-like Data) inspection

`/proc/asound/card0/eld*` files contain per-pin display information. Each file corresponds to one HDMI/DP pin:

```
monitor_present    1     ← display is connected
eld_valid          1     ← ELD data is valid
codec_pin_nid      0x5   ← HDA codec pin node ID (hardware-level identifier)
codec_dev_id       0x0   ← device ID within the pin
monitor_name       27B2U3601
connection_type    DisplayPort
```

### How to read ELD files

```sh
# List all ELD files
ls /proc/asound/card0/eld*

# Quick scan: which pins have monitors?
grep -l "monitor_present.*1" /proc/asound/card0/eld*

# Detailed info for a specific pin
cat /proc/asound/card0/eld#0.8
```

The `eld#X.Y` naming: X is the card number, Y is an index. The mapping from ELD file to ALSA device number is not always 1:1 — cross-reference with `codec_pin_nid` and `wpctl inspect`'s `api.alsa.path`.

### codec_pin_nid stability

The `codec_pin_nid` (e.g. `0x4`, `0x5`, `0x6`, `0x7`) is the HDA codec's hardware pin node ID. This is **the most stable identifier** — it's fixed by the GPU's hardware design. However, it's not directly accessible from WirePlumber's match rules, so you must use `api.alsa.path` (which maps to the ALSA device number, which maps to the pin NID) as the stable match key.

## WirePlumber match patterns

### Matching by node.name (regex with ~ prefix)

```json
{ "node.name" = "~alsa_output.pci-0000_01_00.1.hdmi-stereo-extra[13]" }
```

This matches `extra1` and `extra3` but not `extra2` (the active one).

### Matching by api.alsa.path

```json
{ "api.alsa.path" = "~hdmi:0,[013]$" }
```

This matches `hdmi:0,0`, `hdmi:0,1`, `hdmi:0,3` but not `hdmi:0,2`.

### Multiple matches in one rule (OR semantics)

```json
matches = [
  { "node.name" = "~alsa_output.*hdmi-stereo"; }
  { "node.name" = "~alsa_output.*hdmi-stereo-extra1"; }
  { "node.name" = "~alsa_output.*hdmi-stereo-extra3"; }
  { "node.name" = "~alsa_output.*hdmi-surround.*"; }
]
```

Each entry in the `matches` array is OR'd. A node matching ANY entry gets the `update-props` applied.

## Disabling vs pinning

### Disable (node won't appear at all)
```json
actions.update-props = { "node.disabled" = true; }
```

### Pin name (node appears but with fixed description)
```json
actions.update-props = {
  "node.description" = "HDMI - Primary Monitor";
  "node.nick" = "HDMI-Primary";
};
```

### Set priority (control which sink is default)
```json
actions.update-props = { "priority.session" = 880; }
```

## Surround profiles

Each HDMI pin can have multiple profiles:
- `hdmi-stereo-extraN` — 2-channel stereo
- `hdmi-surround-extraN` — 5.1 surround
- `hdmi-surround71-extraN` — 7.1 surround

If you only use stereo, disable the surround variants too — they create phantom nodes that can be selected as defaults.

## WirePlumber state persistence

WirePlumber saves state in `~/.local/state/wireplumber/`:
- `default-profile` — the active profile per card
- `default-routes` — volume/mute state per route
- `default-nodes` — the configured default sink/source

If a disabled node was previously saved as a default, WirePlumber may still try to reference it. Clearing state after config changes resolves this:

```sh
systemctl --user stop wireplumber
rm -rf ~/.local/state/wireplumber/
systemctl --user start wireplumber
```

Note: this also clears volume/mute settings and default sink/source selections.
