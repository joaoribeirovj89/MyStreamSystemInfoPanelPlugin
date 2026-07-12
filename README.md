# MyStream System Info Panel

Installable workspace panel that displays MyStream host, SDK and plugin runtime information.

The panel uses Plugin API 20 and SDK 0.1.13. It renders only through `PluginUiApi` and does not link directly against ImGui.

## Build and package

```bash
python3 tools/package_plugin.py --clean
```

The package is generated under `dist/` and can be installed through the MyStream plugin manager.
