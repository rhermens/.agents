# macOS `.app` bundle icons from Nix/Home Manager

When constructing a macOS app bundle with `home.file` or another Nix-built layout, putting a PNG under `Contents/Resources/` is not enough for Finder/Dock/Launch Services to use it as the app icon.

Required shape:

1. Convert the source PNG to an `.icns` file. `libicns` provides `png2icns` in nixpkgs:

```nix
appIcon = pkgs.runCommand "my-app.icns" {
  nativeBuildInputs = [ pkgs.libicns ];
} ''
  png2icns $out ${myPackage}/share/icons/hicolor/512x512/apps/my-app.png
'';
```

2. Place the `.icns` in the app bundle resources:

```nix
"Applications/My App.app/Contents/Resources/my-app.icns".source = appIcon;
```

3. Declare the icon in `Contents/Info.plist`:

```xml
<key>CFBundleIconFile</key>
<string>my-app.icns</string>
```

Notes:
- `CFBundleIconFile` is the key Finder/Launch Services consults; without it, a valid executable app bundle may still show the default icon.
- Prefer `.icns` over `.png` for app bundle icons.
- Finder/Launch Services caches icons aggressively. After switching the bundle, `touch ~/Applications/"My App.app"` and `killall Finder` may be enough; deeper Launch Services cache refresh may be needed if the old icon remains.
- `nix flake check --no-build` is a useful low-cost verification for Nix evaluation after adding the derivation.
