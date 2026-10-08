# Export Bans (EU5 mod)

Ban the export or the import of single goods from the Tariffs tab of Europa Universalis V.

- Two Age of Reformation advances after Global Trade, **Export Bans** and **Import Bans**, unlock the buttons
  (+1% import / export efficiency each).
- Each goods row of Economy → Tariffs gets a ban button next to its export and import tariff.
- Bans are the game's own `ban_exports_of_<good>` / `ban_imports_of_<good>` modifiers, held by country modifiers.
  Trade between the country's own markets stays allowed, as in the game's own trade rules.
- Historically mercantilist bans pull the society towards Mercantilism by `societal_value_tiny_monthly_move` per ban.
  The pull of each kind is one modifier (`eb_<kind>_pull_<n>`), so the breakdown shows one line per kind: the goods
  by name for one or two, otherwise their number, with the list in the tooltip of the word "goods". `eb_recount_bans`
  sets it after every ban change; in a save with bans from an earlier version, the pull comes back with the next ban or lift.
- Goods with no ban modifiers of ours (camels, goods of other mods) get no buttons, unless another mod registers them.

## Goods of other mods

A mod that adds goods hooks them in from its own side (`in_game/common/on_action/eb_on_actions.txt` has the
instructions, `description.txt` an example); without Export Bans its hooks are never run, so it needs no dependency.

- `eb_register_goods` (no scope) runs at game start and on load, after `eb_supported_goods` is cleared: the mod adds
  its goods to that global variable list, and they get ban buttons.
- A button of such a good keeps the ban in the country's variable list `eb_export_bans` / `eb_import_bans` and runs
  `eb_custom_bans_changed` (root = the country): the mod gives or takes away its own country modifier with
  `ban_exports_of_<good>` / `ban_imports_of_<good>` to match the list.
- Such bans don't pull towards Mercantilism.

`python tools/build_test_goods.py` builds a test mod with one good (`eb_test_rations`) hooked in this way.

**Export Bans: Goods Patch** (`python tools/build_goods_patch.py`, Workshop page `patch_description.txt`) hooks in the
goods of mods that don't do it themselves: Just Goods (3785316314) so far. Add a mod's goods to `MODS`; only goods whose
mod defines `ban_exports_of_<good>` / `ban_imports_of_<good>` can be added. Goods of mods that aren't loaded are skipped
with no errors.

Steam Workshop: https://steamcommunity.com/sharedfiles/filedetails/?id=3815303367
No dependencies.

## Build

```
python eb_build.py     # builds the mod into Documents/Paradox Interactive/Europa Universalis V/mod/export_bans
```

| File | What it does |
|---|---|
| `eb_build.py` | the generator: modifiers, scripted GUIs, advances, the Tariffs tab override, localization |
| `goods.json` | goods that have both ban modifiers in the game (74; camels have none) |
| `description.txt`, `cover.jpg`, `shots/` | Workshop page |
| `patch_description.txt` | Workshop page of the Goods Patch |
| `item.vdf` | steamcmd upload file (`publishedfileid` 3815303367 for updates) |
| `tools/` | Steamworks API scripts for tags and screenshots; `build_test_goods.py`, the test goods mod; `build_goods_patch.py`, the Goods Patch |

Overrides `trade_policies_lateralview.gui`.
