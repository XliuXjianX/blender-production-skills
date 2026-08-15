# Inspected Asset Capability Catalog

Build the catalog only after source availability is checked:

```powershell
python scripts/build_asset_capability_catalog.py `
  --blender "F:\SteamLibrary\steamapps\common\Blender\blender.exe" `
  --output "$env:USERPROFILE\.codex\cache\blender-production-suite\5.2\blueish_asset_capabilities.json"
```

The catalog records each asset's metadata, source availability, actual node-tree type, public
inputs/outputs, node types, nested groups, instance/realization behavior, repeat/simulation zones,
recommended owner Skill, and an optional `runtime_probe`. Search the compact asset entry first;
load the original source graph only after a candidate matches a real task.

`inspected` means Blender could open the source and find a matching named node group. It does not
mean the asset is automatically appropriate for any scene. `source_unavailable` means a Git LFS
pointer or missing source prevented inspection and is a hard exclusion from production selection.

Run `probe_local_asset_capabilities.py` after the initial build to populate `runtime_probe`:

- `passed`: Blender 5.2 instantiated the matching data block in isolated background execution.
- `modifier`: a Geometry Nodes group had a geometry output and evaluated through a temporary
  Nodes modifier.
- `nested_group`: a field/helper Geometry Nodes group instantiated inside a temporary GN tree; it
  is not a standalone modifier and must be wired into a parent graph.
- `failed`, `data_block_not_found`, or `source_probe_failed`: do not select until the exact cause
  is repaired and the probe is run again.
- `source_unavailable`: do not claim availability; the source cannot currently be loaded.

A passing probe proves runtime callability only. It does not prove visual suitability, every input
combination, external media availability, render-engine behavior, performance, or task-scene
compatibility. The owning specialist must still inspect the graph and validate the evaluated task
result.
