
# 特殊能力与成就数据
# 参考 Stardew Valley 存档结构，很多能力通过 mailReceived 标志实现

SPECIAL_POWERS = [
    {"id": "canReadJunimoText", "type": "mail", "name_key": "power_junimo_text", "desc_key": "power_junimo_text_desc"},
    {"id": "hasMagnifyingGlass", "type": "mail", "name_key": "power_magnifying_glass", "desc_key": "power_magnifying_glass_desc"},
    {"id": "hasSpecialCharm", "type": "mail", "name_key": "power_special_charm", "desc_key": "power_special_charm_desc"},
    {"id": "canRideBus", "type": "mail", "name_key": "power_ride_bus", "desc_key": "power_ride_bus_desc"},
    {"id": "ccBoilerRoom", "type": "mail", "name_key": "power_cc_boiler", "desc_key": "power_cc_boiler_desc"},
    {"id": "ccCraftsRoom", "type": "mail", "name_key": "power_cc_crafts", "desc_key": "power_cc_crafts_desc"},
    {"id": "ccPantry", "type": "mail", "name_key": "power_cc_pantry", "desc_key": "power_cc_pantry_desc"},
    {"id": "ccFishTank", "type": "mail", "name_key": "power_cc_fish_tank", "desc_key": "power_cc_fish_tank_desc"},
    {"id": "ccVault", "type": "mail", "name_key": "power_cc_vault", "desc_key": "power_cc_vault_desc"},
    {"id": "ccBulletin", "type": "mail", "name_key": "power_cc_bulletin", "desc_key": "power_cc_bulletin_desc"},
    {"id": "hasDarkTalisman", "type": "mail", "name_key": "power_dark_talisman", "desc_key": "power_dark_talisman_desc"},
    {"id": "hasMagicInk", "type": "mail", "name_key": "power_magic_ink", "desc_key": "power_magic_ink_desc"},
    {"id": "BearKnowledge", "type": "mail", "name_key": "power_bear_knowledge", "desc_key": "power_bear_knowledge_desc"},
    {"id": "ForestMagic", "type": "mail", "name_key": "power_forest_magic", "desc_key": "power_forest_magic_desc"},
    {"id": "spring_onion_pantry", "type": "mail", "name_key": "power_spring_onion", "desc_key": "power_spring_onion_desc"},
    {"id": "gingerIslandAdmit", "type": "mail", "name_key": "power_ginger_island", "desc_key": "power_ginger_island_desc"},
]

# 成就数据 (ID 对应游戏内部 ID)
ACHIEVEMENTS = [
    {"id": 0, "name_key": "ach_greenhorn", "desc_key": "ach_greenhorn_desc"}, # 新手 (15k)
    {"id": 1, "name_key": "ach_cowpoke", "desc_key": "ach_cowpoke_desc"}, # 牛仔 (50k)
    {"id": 2, "name_key": "ach_homesteader", "desc_key": "ach_homesteader_desc"}, # 宅地主 (250k)
    {"id": 3, "name_key": "ach_millionaire", "desc_key": "ach_millionaire_desc"}, # 百万富翁 (1M)
    {"id": 4, "name_key": "ach_legend", "desc_key": "ach_legend_desc"}, # 传奇 (10M)
    {"id": 5, "name_key": "ach_complete_collection", "desc_key": "ach_complete_collection_desc"}, # 全收集
    {"id": 6, "name_key": "ach_new_friend", "desc_key": "ach_new_friend_desc"}, # 新朋友
    {"id": 7, "name_key": "ach_best_friends", "desc_key": "ach_best_friends_desc"}, # 挚友
    {"id": 9, "name_key": "ach_beloved_farmer", "desc_key": "ach_beloved_farmer_desc"}, # 受欢迎的农夫
    {"id": 11, "name_key": "ach_clique", "desc_key": "ach_clique_desc"}, # 帮派
    {"id": 12, "name_key": "ach_singular_talent", "desc_key": "ach_singular_talent_desc"}, # 单项天赋 (Level 10)
    {"id": 13, "name_key": "ach_master_of_the_five", "desc_key": "ach_master_of_the_five_desc"}, # 五项全能 (Level 10)
    {"id": 15, "name_key": "ach_treasure_trove", "desc_key": "ach_treasure_trove_desc"}, # 宝藏
    {"id": 16, "name_key": "ach_full_house", "desc_key": "ach_full_house_desc"}, # 满屋子
    {"id": 17, "name_key": "ach_fisherman", "desc_key": "ach_fisherman_desc"}, # 渔夫
    {"id": 18, "name_key": "ach_ol_mariner", "desc_key": "ach_ol_mariner_desc"}, # 老水手
    {"id": 19, "name_key": "ach_master_angler", "desc_key": "ach_master_angler_desc"}, # 垂钓大师
    {"id": 20, "name_key": "ach_mother_catch", "desc_key": "ach_mother_catch_desc"}, # 妈妈级捕获
    {"id": 21, "name_key": "ach_million_aire", "desc_key": "ach_million_aire_desc"}, # 百万富翁
    {"id": 22, "name_key": "ach_local_legend", "desc_key": "ach_local_legend_desc"}, # 本地传奇
    {"id": 24, "name_key": "ach_polyculture", "desc_key": "ach_polyculture_desc"}, # 多元文化
    {"id": 25, "name_key": "ach_monoculture", "desc_key": "ach_monoculture_desc"}, # 单一文化
    {"id": 26, "name_key": "ach_full_shipment", "desc_key": "ach_full_shipment_desc"}, # 全货运
    {"id": 27, "name_key": "ach_prairie_king", "desc_key": "ach_prairie_king_desc"}, # 草原之王
    {"id": 28, "name_key": "ach_the_bottom", "desc_key": "ach_the_bottom_desc"}, # 到底了
    {"id": 29, "name_key": "ach_protector_of_the_valley", "desc_key": "ach_protector_of_the_valley_desc"}, # 山谷卫士
    {"id": 30, "name_key": "ach_mystery_of_the_stardrops", "desc_key": "ach_mystery_of_the_stardrops_desc"}, # 星之果实的奥秘
    {"id": 31, "name_key": "ach_gourmet_chef", "desc_key": "ach_gourmet_chef_desc"}, # 美食大厨
    {"id": 32, "name_key": "ach_craft_master", "desc_key": "ach_craft_master_desc"}, # 打造大师
]
