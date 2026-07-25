---
name: pipewire-wireplumber
description: Configure, troubleshoot, and pin PipeWire/WirePlumber audio nodes on NixOS. Covers diagnosing HDMI/DP output shuffling, disabling unused device profiles, pinning node names, and setting default sinks/sources via wireplumber extraConfig. Load when the user asks about audio node names changing, HDMI outputs appearing/disappearing, WirePlumber config, or PipeWire device profiles.
---

# PipeWire / WirePlumber Audio Configuration

## When to load

- Audio node names or descriptions keep changing across reboots (especially HDMI/DP).
- User wants to disable phantom/unused audio outputs.
- User wants to pin a specific device as default sink/source.
- User asks about WirePlumber config on NixOS (`services.pipewire.wireplumber.extraConfig`).
- User asks about `monitor.alsa.rules`, `node.disabled`, or `priority.session`.

## Diagnostic workflow

### 1. Inspect active nodes

```sh
wpctl status          # list all sinks, sources, devices with their IDs
wpctl inspect <id>    # detailed properties of a specific node/device
```

Key properties to note from `wpctl inspect`:
- `node.name` — the internal PipeWire node identifier (e.g. `alsa_output.pci-0000_01_00.1.hdmi-stereo-extra2`)
- `node.description` — the human-readable name shown in UIs
- `api.alsa.path` — the ALSA device path (e.g. `hdmi:0,2`) — **stable per physical pin**
- `device.profile.name` — the ALSA profile (e.g. `hdmi-stereo-extra2`)
- `alsa.card_name` — card name (e.g. `HDA NVidia`)
- `alsa.name` — ALSA's own name for the output (e.g. `HDMI 2`)

### 2. Inspect all nodes including disabled ones

```sh
pw-dump | python3 -c "
import sys, json
for obj in json.load(sys.stdin):
    if obj.get('type') == 'PipeWire:Interface:Node':
        p = obj.get('info',{}).get('props',{})
        print(f'id={obj[\"id\"]} name={p.get(\"node.name\",\"\")} desc={p.get(\"node.description\",\"\")} path={p.get(\"api.alsa.path\",\"\")} class={p.get(\"media.class\",\"\")}')
"
```

### 3. Inspect card profiles (for disabling unused outputs)

```sh
pw-dump | python3 -c "
import sys, json
for obj in json.load(sys.stdin):
    if obj.get('type') == 'PipeWire:Interface:Device':
        info = obj.get('info', {})
        props = info.get('props', {})
        params = info.get('params', {})
        print(f'Card: {props.get(\"alsa.card_name\", props.get(\"device.name\",\"\"))}')
        for p in params.get('EnumProfile', []):
            n = p.get('name','')
            d = p.get('description','')
            if 'hdmi' in n.lower():
                print(f'  profile={n}  desc={d}')
"
```

### 4. Check which HDMI/DP pins have monitors connected

```sh
cat /proc/asound/card0/eld* 2>/dev/null | grep -E 'monitor_present|monitor_name|codec_pin_nid|connection_type'
```

`monitor_present 1` means a display is connected to that pin. `monitor_present 0` means the output is phantom. This is the ground truth for which HDMI outputs are actually in use.

Also useful:
```sh
cat /proc/asound/cards              # list all sound cards
ls /proc/asound/card0/              # see codec and eld files
```

## Configuration: disabling unused outputs

### The problem

GPU HDA controllers (NVIDIA, AMD) expose multiple HDMI/DP audio pins. ALSA enumerates them as `hdmi:0,0` through `hdmi:0,N`. The enumeration order is **not stable** across reboots or hotplug events, so the same physical port may show up as "HDMI 2" today and "HDMI 3" tomorrow. WirePlumber picks up whatever ALSA enumerates, so the active sink name/description changes.

### The fix: disable unused HDMI profiles via WirePlumber rules

On NixOS, add a config fragment under `services.pipewire.wireplumber.extraConfig`:

```nix
services.pipewire.wireplumber.extraConfig."52-disable-unused-hdmi" = {
  "monitor.alsa.rules" = [
    {
      matches = [
        { "node.name" = "~alsa_output.pci-XXXX_XX_XX.X.hdmi-stereo"; }
        { "node.name" = "~alsa_output.pci-XXXX_XX_XX.X.hdmi-stereo-extra1"; }
        { "node.name" = "~alsa_output.pci-XXXX_XX_XX.X.hdmi-stereo-extra3"; }
        { "node.name" = "~alsa_output.pci-XXXX_XX_XX.X.hdmi-surround.*"; }
        { "node.name" = "~alsa_output.pci-XXXX_XX_XX.X.hdmi-surround71.*"; }
      ];
      actions.update-props = {
        "node.disabled" = true;
      };
    }
  ];
};
```

Replace `pci-XXXX_XX_XX.X` with the actual PCI path from `wpctl inspect` (the `device.bus-path` property or from `node.name`). The `~` prefix means regex match.

### Pinning node names instead of disabling

If you want to keep the node but fix its name:

```nix
actions.update-props = {
  "node.description" = "HDMI 1 (primary monitor)";
  "node.nick" = "HDMI-1";
};
```

Match on `api.alsa.path` for stability (e.g. `~.*,7$` matches `hdmi:0,7`), since the ALSA device number maps to a physical pin and doesn't change.

## Configuration: setting default sink priority

```nix
actions.update-props = {
  "priority.session" = 880;  # higher than other sinks
};
```

## Verification after applying changes

```sh
sudo nixos-rebuild switch
systemctl --user restart wireplumber
wpctl status          # verify only expected sinks appear
wpctl inspect <id>    # verify node.disabled or pinned names
```

## WirePlumber state files

WirePlumber persists state in `~/.local/state/wireplumber/`:
- `default-profile` — which profile is active per card
- `default-routes` — volume/mute per route
- `default-nodes` — which sink/source is default

If the wrong profile persists after config changes, clearing state can help:
```sh
systemctl --user stop wireplumber
rm -rf ~/.local/state/wireplumber/
systemctl --user start wireplumber
```

## Pitfalls

- **Don't match on `node.description` or `alsa.name`** — these are the unstable labels that change. Match on `node.name`, `api.alsa.path`, or `device.profile.name` instead.
- **`hdmi-stereo` (no extra suffix) is pin 0.** `extra1` is pin 1, `extra2` is pin 2, etc. Don't assume "extra2" means the third physical port — check `/proc/asound/card0/eld*` to confirm which pin has a monitor.
- **Surround profiles** (`hdmi-surround`, `hdmi-surround71`) create separate nodes for the same pin. Disable them too if you only use stereo.
- **NixOS `extraConfig` keys must be strings.** The config fragment name (e.g. `"52-disable-unused-hdmi"`) is a string key in the attrset, not an identifier.
- **WirePlumber config fragments are ordered by filename.** Use numeric prefixes (`51-`, `52-`, etc.) to control evaluation order.
- **The `~` prefix in matches means regex.** Without `~`, it's an exact string match.
- **Multiple match entries in one `matches` array are OR'd** — a node matching ANY entry gets the `update-props` applied.

## References

- `references/hdmi-pin-diagnosis.md` — detailed reference for GPU HDMI/DP pin diagnosis, ELD inspection, and WirePlumber rule construction
