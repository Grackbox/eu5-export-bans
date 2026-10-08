"""Builds "Export Bans: Goods Patch": ban buttons for the goods of other mods, hooked into Export Bans the way
eb_on_actions.txt describes. One patch covers several mods. Each good has an on_action of its own, so a good whose mod
isn't loaded only makes errors in error.log for its own on_actions and leaves the other goods working.
Only goods whose mod defines ban_exports_of_<good> and ban_imports_of_<good> belong here.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))   # eb_build, for the texts
from eb_build import KINDS, LANGS, TEXT   # noqa: E402

OUT = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis V/mod/export_bans_goods_patch")

# Workshop id and name of each mod, and its goods
MODS = [
    ("3785316314", "Just Goods", [
        "zinc", "antimony", "brassware", "pewterware", "silverware", "ornaments", "bells", "printing_type",   # Just Brass
        "cheese",                                                                                            # Just Cheese
        "brass", "clocks", "precision_instruments", "mirrors", "optics",                                     # Just Clocks
        "meat", "bisons",                                                                                    # Just Meat
        "aromatics", "soap", "perfume", "tallow", "potash", "cosmetics", "candles", "palmoil", "whaleoil",   # Just Soap
        "cinnamon", "nutmeg", "cardamom", "ginger", "turmeric", "vanilla", "star_anise",                     # Just Spices
    ]),
]
GOODS = [g for _, _, goods in MODS for g in goods]


def write(path, text):
    full = os.path.join(OUT, *path.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8-sig", newline="\n") as fh:
        fh.write(text)


def modifiers():
    return "".join(f"ebp_{k}_ban_{g} = {{\n\tgame_data = {{\n\t\tcategory = country\n\t}}\n\tban_{k}s_of_{g} = yes\n}}\n\n"
                   for g in GOODS for k in KINDS)


def on_actions():
    out = ("# Export Bans: Goods Patch. One on_action per good, so a missing mod breaks only its own goods.\n\n"
           f"eb_register_goods = {{\n\ton_actions = {{\n" + "".join(f"\t\tebp_register_{g}\n" for g in GOODS) + "\t}\n}\n\n"
           f"eb_custom_bans_changed = {{\n\ton_actions = {{\n" + "".join(f"\t\tebp_apply_{g}\n" for g in GOODS) + "\t}\n}\n")
    for _, name, goods in MODS:
        out += f"\n# {name}\n"
        for g in goods:
            out += (f"\nebp_register_{g} = {{\n\teffect = {{\n"
                    f"\t\tadd_to_global_variable_list = {{ name = eb_supported_goods target = goods:{g} }}\n\t}}\n}}\n")
            out += f"\n# root = the country\nebp_apply_{g} = {{\n\teffect = {{\n"
            for k in KINDS:
                m = f"ebp_{k}_ban_{g}"
                out += (f"\t\tif = {{\n\t\t\tlimit = {{ is_target_in_variable_list = {{ name = eb_{k}_bans target = goods:{g} }} }}\n"
                        f"\t\t\tif = {{\n\t\t\t\tlimit = {{ NOT = {{ has_country_modifier = {m} }} }}\n"
                        f"\t\t\t\tadd_country_modifier = {{ modifier = {m} years = -1 }}\n\t\t\t}}\n\t\t}}\n"
                        f"\t\telse_if = {{\n\t\t\tlimit = {{ has_country_modifier = {m} }}\n\t\t\tremove_country_modifier = {m}\n\t\t}}\n")
            out += "\t}\n}\n"
    return out


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    write("main_menu/common/static_modifiers/ebp_bans.txt", modifiers())
    write("in_game/common/on_action/ebp_hooks.txt", on_actions())
    for lang in LANGS:
        t = TEXT.get(lang, TEXT["english"])
        lines = {f"STATIC_MODIFIER_NAME_ebp_{k}_ban_{g}": t[k][0].format(g=g) for g in GOODS for k in KINDS}
        write(f"main_menu/localization/{lang}/ebp_l_{lang}.yml", f"l_{lang}:\n" + "".join(f' {key}: "{v}"\n' for key, v in lines.items()))
    meta = {"name": "Export Bans: Goods Patch [LOCAL]", "id": "grackbox.export_bans_goods_patch", "version": "1.0.1", "game_id": "eu5",
            "supported_game_version": "1.4.*",
            "short_description": "Export and import ban buttons for the goods of other mods: " + ", ".join(n for _, n, _ in MODS) + ".",
            "tags": ["Economy", "1.4"],
            "relationships": [{"rel_type": "dependency", "id": "grackbox.export_bans", "display_name": "Export Bans",
                               "resource_type": "mod", "version": "1.*"}],
            "game_custom_data": {}}
    write(".metadata/metadata.json", json.dumps(meta, indent=4, ensure_ascii=False) + "\n")
    shutil.copyfile(os.path.join(HERE, "cover.png"), os.path.join(OUT, ".metadata", "thumbnail.png"))
    print("goods:", len(GOODS), "->", OUT)


if __name__ == "__main__":
    main()
