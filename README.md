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
| `item.vdf` | steamcmd upload file (`publishedfileid` 3815303367 for updates) |
| `tools/` | Steamworks API scripts for tags and screenshots |

Overrides `trade_policies_lateralview.gui`.
