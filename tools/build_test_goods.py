"""Builds "Export Bans Test Goods": a mod with one good of its own (eb_test_rations), hooked into Export Bans the way
a mod that adds goods would do it (see eb_on_actions.txt in Export Bans). For testing only; not uploaded.
"""
import json
import os
import shutil

G = "E:/SteamLibrary/steamapps/common/Europa Universalis V/game/"
OUT = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis V/mod/export_bans_test_goods")
GOOD = "eb_test_rations"
KINDS = ("export", "import")


def write(path, text):
    full = os.path.join(OUT, *path.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8-sig", newline="\n") as fh:
        fh.write(text)


GOODS = f"""{GOOD} = {{
	category = produced
	color = goods_{GOOD}
	default_market_price = 2.5
	transport_cost = 1.0
	demand_add = {{
		nobles = 0.01
		clergy = 0.01
		burghers = 0.01
		soldiers = 0.01
		laborers = 0.01
		peasants = 0.01
	}}
	base_production = 0.003
}}
"""

# the modifier types the engine expects for every good
TYPES = [(f"ban_exports_of_{GOOD}", "boolean", "country"), (f"ban_imports_of_{GOOD}", "boolean", "country"),
         (f"local_{GOOD}_output_modifier", "percent", "location"), (f"global_{GOOD}_output_modifier", "percent", "country"),
         (f"global_{GOOD}_pop_demand", "percent", "country"), (f"can_extract_{GOOD}", "boolean", "country"),
         (f"{GOOD}_impacts_inflation", "percent", "country"), (f"{GOOD}_used_for_minting", "boolean", "country")]

# The part a goods mod writes for Export Bans: register the good, and keep a ban modifier in step with the ban lists
HOOKS = f"""eb_register_goods = {{ on_actions = {{ ebt_register }} }}
eb_custom_bans_changed = {{ on_actions = {{ ebt_apply }} }}

ebt_register = {{
	effect = {{
		add_to_global_variable_list = {{ name = eb_supported_goods target = goods:{GOOD} }}
	}}
}}

ebt_apply = {{
	effect = {{
""" + "".join(f"""		if = {{
			limit = {{ is_target_in_variable_list = {{ name = eb_{k}_bans target = goods:{GOOD} }} }}
			if = {{
				limit = {{ NOT = {{ has_country_modifier = ebt_{k}_ban_{GOOD} }} }}
				add_country_modifier = {{ modifier = ebt_{k}_ban_{GOOD} years = -1 }}
			}}
		}}
		else_if = {{
			limit = {{ has_country_modifier = ebt_{k}_ban_{GOOD} }}
			remove_country_modifier = ebt_{k}_ban_{GOOD}
		}}
""" for k in KINDS) + "\t}\n}\n"


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    write(f"in_game/common/goods/ebt_goods.txt", GOODS)
    write("main_menu/common/named_colors/ebt_colors.txt", f"colors = {{\n\tgoods_{GOOD} = hsv {{ 0.55 0.6 0.8 }}\n}}\n")
    write("main_menu/common/modifier_type_definitions/ebt_modifier_types.txt",
          "".join(f"{n} = {{\n\t{t} = yes\n\tgame_data = {{\n\t\tcategory = {c}\n\t}}\n}}\n" for n, t, c in TYPES))
    write("main_menu/common/static_modifiers/ebt_bans.txt",
          "".join(f"ebt_{k}_ban_{GOOD} = {{\n\tgame_data = {{\n\t\tcategory = country\n\t}}\n\tban_{k}s_of_{GOOD} = yes\n}}\n\n" for k in KINDS))
    write("in_game/common/on_action/ebt_export_bans.txt", HOOKS)
    for sub in ("", "illustrations/"):   # the wine icon stands in for the good's own
        dst = os.path.join(OUT, "main_menu/gfx/interface/icons/trade_goods", sub, f"icon_goods_{GOOD}.dds")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(G + f"main_menu/gfx/interface/icons/trade_goods/{sub}icon_goods_wine.dds", dst)
    for lang in ("english", "russian"):
        ru = lang == "russian"
        lines = {GOOD: "Тестовые пайки" if ru else "Test Rations", f"{GOOD}_desc": "Test good for Export Bans."}
        lines.update({f"STATIC_MODIFIER_NAME_ebt_{k}_ban_{GOOD}": (("Запрет экспорта" if k == "export" else "Запрет импорта") if ru else
                      ("Export ban" if k == "export" else "Import ban")) + f": [ShowGoodsName('{GOOD}')]" for k in KINDS})
        lines.update({f"MODIFIER_TYPE_NAME_{n}": n for n, _, _ in TYPES})
        write(f"main_menu/localization/{lang}/ebt_l_{lang}.yml", f"l_{lang}:\n" + "".join(f' {k}: "{v}"\n' for k, v in lines.items()))
    meta = {"name": "Export Bans Test Goods [LOCAL]", "id": "grackbox.export_bans_test_goods", "version": "1.0.0", "game_id": "eu5",
            "supported_game_version": "1.4.*", "short_description": "A test good for Export Bans.", "tags": [],
            "relationships": [], "game_custom_data": {}}
    write(".metadata/metadata.json", json.dumps(meta, indent=4) + "\n")
    print("->", OUT)


if __name__ == "__main__":
    main()
