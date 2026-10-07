"""Builds the EU5 mod "Export Bans": buttons in each goods row of the Tariffs tab ban that good's export or import for
the country, or lift the ban. The bans are the game's own ban_exports_of_<good> / ban_imports_of_<good> modifiers,
held by country modifiers.
"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
G = "E:/SteamLibrary/steamapps/common/Europa Universalis V/game/"
OUT = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis V/mod/export_bans")
LANGS = ["english", "russian", "german", "french", "spanish", "braz_por", "polish", "turkish", "japanese", "korean", "simp_chinese"]
GOODS = json.load(open(os.path.join(HERE, "goods.json")))    # goods with both ban_exports_of_ and ban_imports_of_ modifiers
KINDS = ("export", "import")
RESET = {"export": "ResetExportTariff", "import": "ResetImportTariff"}


def write(path, text, bom=True):
    full = os.path.join(OUT, *path.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8-sig" if bom else "utf-8", newline="\n") as fh:
        fh.write(text)


# Bans that were mercantilist policy pull the society towards mercantilism, as much per ban as a merchant in a foreign
# market pulls it towards free trade (the game's own societal_value_tiny_monthly_move). Food and religious bans don't.
MERCANTILIST = {
    # bullion, and the raw materials and war stores a country's own workshops and fleets need
    "export": {"goods_gold", "silver", "wool", "cotton", "fiber_crops", "silk", "dyes", "alum", "iron", "copper", "tin", "lead",
               "coal", "saltpeter", "lumber", "tar", "naval_supplies", "horses"},
    # finished goods that compete with the country's own workshops, and luxuries that send money abroad
    "import": {"cloth", "fine_cloth", "glass", "paper", "books", "furniture", "pottery", "porcelain", "lacquerware", "jewelry",
               "tools", "steel", "firearms", "weaponry", "cannons", "wine", "liquor", "pepper", "cloves", "saffron", "tobacco",
               "tea", "coffee", "cocoa", "sugar", "incense", "gems", "pearls"},
}


TINY_MOVE = 0.025   # the game's societal_value_tiny_monthly_move (script_values/default_values.txt)


def merc(k):
    """The mercantilist goods of a kind, in the order of goods.json."""
    return [g for g in GOODS if g in MERCANTILIST[k]]


def modifiers():
    # the bans themselves carry no pull: each would be a line of its own in the society value's breakdown. The pull of
    # all the mercantilist bans of a kind is one modifier, eb_<kind>_pull_<n> for n banned goods (see effects()).
    out = ""
    for k in KINDS:
        for g in GOODS:
            out += f"eb_{k}_ban_{g} = {{\n\tgame_data = {{\n\t\tcategory = country\n\t}}\n\tban_{k}s_of_{g} = yes\n}}\n\n"
        for n in range(1, len(merc(k)) + 1):
            out += (f"eb_{k}_pull_{n} = {{\n\tgame_data = {{\n\t\tcategory = country\n\t}}\n"
                    f"\tmonthly_towards_mercantilism = {round(TINY_MOVE * n, 3)}\n}}\n\n")
    return out


def effects():
    """eb_recount_bans: counts the mercantilist bans of each kind, gives the matching pull modifier, and keeps the
    variables the pull modifier's name and the goods list read (eb_<kind>_on_<good>, and _p1_/_p2_ for the first two)."""
    out = "# Scope: country. Run after a ban changes, and monthly (saves from before the pull was one modifier).\neb_recount_bans = {\n"
    for k in KINDS:
        goods = merc(k)
        out += "".join(f"\tif = {{\n\t\tlimit = {{ has_country_modifier = eb_{k}_pull_{n} }}\n\t\tremove_country_modifier = eb_{k}_pull_{n}\n\t}}\n"
                       for n in range(1, len(goods) + 1))
        out += "".join(f"\tif = {{\n\t\tlimit = {{ has_variable = eb_{k}_{p}_{g} }}\n\t\tremove_variable = eb_{k}_{p}_{g}\n\t}}\n"
                       for g in goods for p in ("on", "p1", "p2"))
        out += "\tset_local_variable = { name = eb_n value = 0 }\n"
        for g in goods:
            out += (f"\tif = {{\n\t\tlimit = {{ has_country_modifier = eb_{k}_ban_{g} }}\n"
                    f"\t\tchange_local_variable = {{ name = eb_n add = 1 }}\n"
                    f"\t\tset_variable = {{ name = eb_{k}_on_{g} value = yes }}\n"
                    f"\t\tif = {{\n\t\t\tlimit = {{ local_var:eb_n = 1 }}\n\t\t\tset_variable = {{ name = eb_{k}_p1_{g} value = yes }}\n\t\t}}\n"
                    f"\t\tif = {{\n\t\t\tlimit = {{ local_var:eb_n = 2 }}\n\t\t\tset_variable = {{ name = eb_{k}_p2_{g} value = yes }}\n\t\t}}\n\t}}\n")
        out += "".join(f"\tif = {{\n\t\tlimit = {{ local_var:eb_n = {n} }}\n\t\tadd_country_modifier = {{ modifier = eb_{k}_pull_{n} years = -1 }}\n\t}}\n"
                       for n in range(1, len(goods) + 1))
    return out + "}\n"


ON_ACTIONS = """monthly_country_pulse = {
	on_actions = {
		eb_monthly_recount
	}
}

# Scope: country. Only players ban goods.
eb_monthly_recount = {
	trigger = {
		is_ai = no
	}
	effect = {
		eb_recount_bans = yes
	}
}
"""


def concepts():
    # the goods word of a pull line with three or more goods: its tooltip lists them
    return "".join(f"eb_{k}_goods = {{\n\ttexture = \"modifiers/_default\"\n\tshown_in_encyclopedia = no\n}}\n" for k in KINDS)


def ru_goods(n):
    return "товар" if n % 10 == 1 and n % 100 != 11 else "товара" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else "товаров"


def pull_loc(lang):
    """Names of the pull modifiers and the goods list. The breakdown shows "Label: rest" with the label on the left and
    the rest, with the value, on the right."""
    ru = lang == "russian"
    lines = {}
    for k in KINDS:
        goods = merc(k)
        def pick(p):
            return "".join(f"[AddLocalizationIf(GetPlayer.MakeScope.GetVariable('eb_{k}_{p}_{g}').IsSet, 'EB_{k.upper()}_NAME_{g}')]"
                           for g in goods)
        label = ("Запреты экспорта" if k == "export" else "Запреты импорта") if ru else ("Export bans" if k == "export" else "Import bans")
        one = ("Запрет экспорта" if k == "export" else "Запрет импорта") if ru else ("Export ban" if k == "export" else "Import ban")
        for n in range(1, len(goods) + 1):
            if n == 1:
                text = f"{one}: {pick('p1')}"
            elif n == 2:
                text = f"{label}: {pick('p1')}, {pick('p2')}"
            else:
                text = f"{label}: {n} [Concept('eb_{k}_goods', '{ru_goods(n) if ru else 'goods'}')|e]"
            lines[f"STATIC_MODIFIER_NAME_eb_{k}_pull_{n}"] = text
        for g in goods:
            lines[f"EB_{k.upper()}_NAME_{g}"] = f"[ShowGoodsName('{g}')]"
            lines[f"EB_{k.upper()}_ITEM_{g}"] = f"\\n• [ShowGoodsName('{g}')]"
        lines[f"game_concept_eb_{k}_goods"] = "товары" if ru else "goods"
        lines[f"game_concept_eb_{k}_goods_desc"] = (
            (("Под запретом экспорта" if k == "export" else "Под запретом импорта") if ru else
             ("Export banned" if k == "export" else "Import banned"))
            + "".join(f"[AddLocalizationIf(GetPlayer.MakeScope.GetVariable('eb_{k}_on_{g}').IsSet, 'EB_{k.upper()}_ITEM_{g}')]"
                      for g in goods))
    return lines


def scripted_guis():
    out = ""
    for k in KINDS:
        banned = "".join(f"\t\t\tAND = {{\n\t\t\t\tscope:eb_goods = goods:{g}\n\t\t\t\thas_country_modifier = eb_{k}_ban_{g}\n\t\t\t}}\n"
                         for g in GOODS)
        toggle = "".join(f"\t\t\tgoods:{g} = {{\n\t\t\t\tif = {{\n\t\t\t\t\tlimit = {{ has_country_modifier = eb_{k}_ban_{g} }}\n"
                         f"\t\t\t\t\tremove_country_modifier = eb_{k}_ban_{g}\n\t\t\t\t}}\n\t\t\t\telse = {{\n"
                         f"\t\t\t\t\tadd_country_modifier = {{ modifier = eb_{k}_ban_{g} years = -1 }}\n\t\t\t\t}}\n\t\t\t}}\n"
                         for g in GOODS)
        out += (f"# Scope: country. Has the advance that unlocks {k} bans.\n"
                f"eb_can_ban_{k} = {{\n\tscope = country\n\tis_shown = {{\n\t\thas_advance = eb_{k}_ban_advance\n\t}}\n}}\n\n"
                f"# Scope: country. Is this good's {k} banned by this mod?\n"
                f"eb_is_{k}_banned = {{\n\tscope = country\n\tsaved_scopes = {{ eb_goods }}\n"
                f"\tis_shown = {{\n\t\tOR = {{\n{banned}\t\t}}\n\t}}\n}}\n\n"
                f"# Scope: country. Bans this good's {k}, or lifts the ban.\n"
                f"eb_toggle_{k}_ban = {{\n\tscope = country\n\tsaved_scopes = {{ eb_goods }}\n"
                f"\teffect = {{\n\t\tswitch = {{\n\t\t\ttrigger = scope:eb_goods\n{toggle}\t\t}}\n\t\teb_recount_bans = yes\n\t}}\n}}\n\n")
    return out


SCOPE = "GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('eb_goods', GoodsTradePolicyItem.GetGoods.MakeScope).End"


def button(k):
    return f"""
				# Export Bans: ban this good's {k} for the country, or lift the ban; shown once the advance is researched, or
				# while a ban is on so it can be lifted. The box keeps its place either way, so the columns don't move.
				widget = {{
					size = {{ 20 20 }}
					parentanchor = vcenter
				button_square_checkbox = {{
					visible = "[Or(GetScriptedGui('eb_can_ban_{k}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End), GetScriptedGui('eb_is_{k}_banned').IsShown({SCOPE}))]"
					size = {{ 20 20 }}
					tooltip = "EB_{k.upper()}_TT"
					blockoverride "check_texture" {{
						texture = "gfx/interface/icons/flat_icons/trade_market/banned_{k}s.dds"
					}}
					blockoverride "checked_icon_size" {{
						size = {{ 16 16 }}
					}}
					blockoverride "unchecked_icon_size" {{
						size = {{ 16 16 }}
					}}
					blockoverride "checked_visible" {{
						visible = "[GetScriptedGui('eb_is_{k}_banned').IsShown({SCOPE})]"
					}}
					blockoverride "unchecked_visible" {{
						visible = "[Not(GetScriptedGui('eb_is_{k}_banned').IsShown({SCOPE}))]"
					}}
					onclick = "[GetScriptedGui('eb_toggle_{k}_ban').Execute({SCOPE})]"
				}}
				}}
"""


def tariffs_override():
    src = open(G + "in_game/gui/trade_policies_lateralview.gui", encoding="utf-8-sig").read().replace("\r", "")
    for k in KINDS:
        # the end of the tariff slider of this row (the right-click reset), before the row's monthly gold
        anchor = (f'\t\t\t\t\t\t\t\ton_action = "[{RESET[k]}(GoodsTradePolicyItem.GetGoods)]"\n'
                  "\t\t\t\t\t\t\t}\n\t\t\t\t\t\t}\n\t\t\t\t\t}\n\t\t\t\t}\n")
        assert src.count(anchor) == 1, f"trade_policies_lateralview.gui changed: update the {k} anchor"
        src = src.replace(anchor, anchor + button(k))
    return src


# Search filters for the goods list: goods whose export / import is banned in a human player's capital market (whether by
# this mod, a religion or a law)
FILTERS = "".join(f"""
eb_{k}_banned = {{
	scope = goods
	tag = goods
	group = 90
	exclusive_group = yes
	trigger = {{
		any_country = {{
			is_ai = no
			capital.market ?= {{ is_{k}_banned = root }}
		}}
	}}
}}
""" for k in KINDS)

# Two advances after the game's Global Trade advance (the Global Trade institution): each unlocks one kind of ban
ADVANCES = {"import": "export_efficiency", "export": "import_efficiency"}
ICONS = {"import": "zan_food_imports", "export": "export_building_country_advance"}


def advances():
    return "".join(f"eb_{k}_ban_advance = {{\n\tage = age_4_reformation\n\ticon = {ICONS[k]}\n\trequires = global_trade_advance\n"
                   f"\tallow = {{ has_embraced_institution = institution:global_trade }}\n\teb_unlocks_{k}_bans = yes\n"
                   f"\t{ADVANCES[k]} = 0.01\n}}\n\n" for k in KINDS)


# A flag modifier for each kind: the advance card lists it as "Unlocks <kind> bans", with an explanation in its tooltip
def modifier_types():
    return "".join(f"eb_unlocks_{k}_bans = {{\n\tboolean = yes\n\tgame_data = {{\n\t\tcategory = country\n\t}}\n}}\n\n" for k in KINDS)


def modifier_icons():
    return "".join(f"eb_unlocks_{k}_bans = {{\n\tpositive = \"gfx/interface/icons/flat_icons/trade_market/banned_{k}s.dds\"\n}}\n\n"
                   for k in KINDS)


UNLOCK_TEXT = {
    "russian": {
        "export": ("Открывает запрет экспорта",
                   "Во вкладке «Экономика → Пошлины» у каждого товара появляется кнопка запрета [Concept('export', 'экспорта')|e]. "
                   "Пока запрет действует, этот товар нельзя вывозить с наших [Concept('markets', 'рынков')|e] на чужие; "
                   "между нашими собственными рынками его по-прежнему можно возить. Запрет вывоза драгоценных металлов и сырья "
                   "для своих мануфактур — меркантилистская политика и понемногу сдвигает общество к меркантилизму."),
        "import": ("Открывает запрет импорта",
                   "Во вкладке «Экономика → Пошлины» у каждого товара появляется кнопка запрета [Concept('import', 'импорта')|e]. "
                   "Пока запрет действует, этот товар нельзя ввозить на наши [Concept('markets', 'рынки')|e] с чужих; "
                   "между нашими собственными рынками его по-прежнему можно возить. Запрет ввоза готовых товаров и роскоши — "
                   "меркантилистская политика и понемногу сдвигает общество к меркантилизму."),
    },
    "english": {
        "export": ("Unlocks export bans",
                   "Every good gets an [export|e] ban button in Economy → Tariffs. While the ban is on, the good can't leave our "
                   "[markets|e] for foreign ones; it still moves freely between our own markets. Banning the export of bullion and "
                   "of raw materials for our own workshops is mercantilist policy and slowly pulls society towards mercantilism."),
        "import": ("Unlocks import bans",
                   "Every good gets an [import|e] ban button in Economy → Tariffs. While the ban is on, the good can't come into our "
                   "[markets|e] from foreign ones; it still moves freely between our own markets. Banning the import of finished "
                   "goods and luxuries is mercantilist policy and slowly pulls society towards mercantilism."),
    },
}


ADV_TEXT = {
    "russian": {"import": ("Запрет импорта", "Мы можем закрыть свои рынки для отдельных товаров из-за границы. Открывает запрет импорта товаров во вкладке «Пошлины»."),
                "export": ("Запрет экспорта", "Мы можем не выпускать отдельные товары со своих рынков за границу. Открывает запрет экспорта товаров во вкладке «Пошлины».")},
    "english": {"import": ("Import Bans", "We can close our markets to single foreign goods. Unlocks import bans in the Tariffs tab."),
                "export": ("Export Bans", "We can keep single goods from leaving our markets. Unlocks export bans in the Tariffs tab.")},
}

TEXT = {
    "russian": {"export": ("Запрет экспорта: [ShowGoodsName('{g}')]", "Запретить экспорт этого товара с наших рынков или снять запрет."),
                "import": ("Запрет импорта: [ShowGoodsName('{g}')]", "Запретить импорт этого товара на наши рынки или снять запрет.")},
    "english": {"export": ("Export ban: [ShowGoodsName('{g}')]", "Ban this good's export from our markets, or lift the ban."),
                "import": ("Import ban: [ShowGoodsName('{g}')]", "Ban this good's import into our markets, or lift the ban.")},
}


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    write("main_menu/common/static_modifiers/eb_bans.txt", modifiers())
    write("in_game/common/scripted_guis/eb_scripted_guis.txt", scripted_guis())
    write("in_game/common/scripted_effects/eb_effects.txt", effects())
    write("in_game/common/on_action/eb_on_actions.txt", ON_ACTIONS)
    write("in_game/common/game_concepts/eb_concepts.txt", concepts())
    write("in_game/gui/trade_policies_lateralview.gui", tariffs_override(), bom=False)
    write("in_game/common/advances/eb_advances.txt", advances())
    write("main_menu/common/modifier_type_definitions/eb_modifier_types.txt", modifier_types())
    write("main_menu/common/modifier_icons/eb_modifier_icons.txt", modifier_icons())
    # (no search filters: the Tariffs list only offers its own filters, hard-coded in the game)
    for lang in LANGS:
        t = TEXT.get(lang, TEXT["english"])
        lines = {}
        for k in KINDS:
            name, tip = t[k]
            lines.update({f"STATIC_MODIFIER_NAME_eb_{k}_ban_{g}": name.format(g=g) for g in GOODS})
            lines[f"EB_{k.upper()}_TT"] = tip
            a_name, a_desc = ADV_TEXT.get(lang, ADV_TEXT["english"])[k]
            lines[f"eb_{k}_ban_advance"] = a_name
            lines[f"eb_{k}_ban_advance_desc"] = a_desc
            u_name, u_desc = UNLOCK_TEXT.get(lang, UNLOCK_TEXT["english"])[k]
            lines[f"MODIFIER_TYPE_NAME_eb_unlocks_{k}_bans"] = u_name
            lines[f"MODIFIER_TYPE_DESC_eb_unlocks_{k}_bans"] = u_desc
        lines.update(pull_loc(lang))
        write(f"main_menu/localization/{lang}/eb_l_{lang}.yml", f"l_{lang}:\n" + "".join(f' {key}: "{v}"\n' for key, v in lines.items()))
    meta = {"name": "Export Bans [LOCAL]", "id": "grackbox.export_bans", "version": "1.0.0", "game_id": "eu5", "supported_game_version": "1.4.*",
            "short_description": "Ban the export or import of single goods from the Tariffs tab.", "tags": ["Economy", "1.4"],
            "relationships": [], "game_custom_data": {}}
    write(".metadata/metadata.json", json.dumps(meta, indent=4) + "\n")
    shutil.copyfile(os.path.join(HERE, "cover.png"), os.path.join(OUT, ".metadata", "thumbnail.png"))   # the launcher's picture
    print("goods:", len(GOODS), "->", OUT)


if __name__ == "__main__":
    main()
