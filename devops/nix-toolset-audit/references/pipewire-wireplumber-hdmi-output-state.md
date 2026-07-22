# PipeWire/WirePlumber HDMI output state and broad ALSA rules

Session-derived notes for debugging NixOS PipeWire/WirePlumber audio issues where speakers appear muted after changing ALSA/WirePlumber channel mapping.

## Symptom pattern

- User has a WirePlumber rule under `services.pipewire.wireplumber.extraConfig` using `monitor.alsa.rules`.
- Rule broadly matches ALSA sinks, e.g. `"node.name" = "~alsa_output.*";`.
- Rule swaps stereo channels with `"audio.position" = [ "FR" "FL" ];`.
- Sound sometimes appears muted, but PipeWire volume/mute state is not actually muted.
- User sometimes must switch from HDMI2 to HDMI1 manually.

## Checks that distinguished the likely cause

Useful commands:

```bash
wpctl status
wpctl get-volume @DEFAULT_AUDIO_SINK@
wpctl inspect @DEFAULT_AUDIO_SINK@
```

Look for these fields in `wpctl inspect @DEFAULT_AUDIO_SINK@`:

```text
node.name
audio.position
device.profile.description
device.profile.name
node.description
```

Also inspect persisted WirePlumber state:

```bash
grep -R "alsa_output\|default.configured.audio.sink\|hdmi" ~/.local/state/wireplumber
```

In the observed case:

- Live sink was `alsa_output.pci-0000_01_00.1.hdmi-stereo-extra1` / HDMI 2.
- Persisted default was `default.configured.audio.sink=alsa_output.pci-0000_01_00.1.hdmi-stereo-extra2`.
- This mismatch supports a routing/profile restoration problem: audio may be routed to a different HDMI/DP port while volume and mute look fine.

## Interpretation

Do not assume a broad `audio.position = [ "FR" "FL" ]` rule is the direct cause if it is already using valid stereo positions. For normal stereo L/R swap, `FR FL` is correct. Avoid suggesting rear-channel names unless the sink is actually rear-channel/surround.

For GPU HDMI/DP audio, `hdmi-stereo`, `hdmi-stereo-extra1`, `hdmi-stereo-extra2`, etc. can correspond to different physical monitor/DP/HDMI outputs. Monitor sleep/replug/EDID changes can make WirePlumber restore or prefer the wrong one, causing apparent mute/silence.

## Remediation options

Manual test/switch:

```bash
wpctl status
wpctl set-profile <device-id> <profile-index>
wpctl set-default @DEFAULT_AUDIO_SINK@
```

Example if the NVIDIA audio card is device `54` and HDMI1 is profile index `1`:

```bash
wpctl set-profile 54 1
wpctl set-default @DEFAULT_AUDIO_SINK@
```

Clear stale default state:

```bash
wpctl clear-default
```

More forceful state reset:

```bash
mv ~/.local/state/wireplumber ~/.local/state/wireplumber.bak
systemctl --user restart wireplumber pipewire pipewire-pulse
```

Then select the correct output once and save it as default.

## Caution for broad ALSA rules

`matches = [ { ... } { ... } ];` in WirePlumber rules behaves as alternatives, not a combined AND. A broad regex like `~alsa_output.*` catches HDMI, IEC958, analog, USB, and pro-output profiles. If the goal is all normal stereo sinks, consider `~alsa_output.*stereo.*` to avoid clobbering `pro-output-*` style nodes while keeping broad stereo L/R swap behavior.
