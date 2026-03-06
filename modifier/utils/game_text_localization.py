# Keep localized labels for NPCs, locations, buildings, animals, and bundles in one place.
import json
import os
import re
from functools import lru_cache

from .translator import tr


def _normalize_fragment(value):

    normalized = (value or "").strip().lower()

    for source, target in (
        (" ", "_"),
        ("-", "_"),
        ("'", ""),
        ("’", ""),
        (",", ""),
        (".", ""),
        (":", ""),
        ("/", "_"),
        ("(", ""),
        (")", ""),
    ):

        normalized = normalized.replace(source, target)

    return normalized


def _humanize_identifier(value):

    text = (value or "").replace("_", " ").strip()

    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)

    text = re.sub(r"\s+", " ", text).strip()

    if not text:

        return ""

    replacements = {
        "Cc": "Community Center",
        "Df": "Desert Festival",
        "Cf": "Calico Festival",
        "Pk": "Prairie King",
        "Qi": "Qi",
        "Joja": "Joja",
        "Junimo": "Junimo",
        "Movie Theater": "Movie Theater",
    }

    words = []

    for word in text.split():

        normalized = word.title()

        words.append(replacements.get(normalized, normalized))

    return " ".join(words)


def translate_game_name(name, fallback=None):

    if not name:

        return fallback if fallback is not None else ""

    return tr.translate(name, fallback if fallback is not None else name)


WEATHER_TOMORROW_LABELS = {
    "Sun": {"en": "Sun", "zh": "晴天"},
    "Rain": {"en": "Rain", "zh": "雨天"},
    "GreenRain": {"en": "Green Rain", "zh": "绿雨"},
    "Wind": {"en": "Wind", "zh": "风天"},
    "Storm": {"en": "Storm", "zh": "暴风雨"},
    "Festival": {"en": "Festival", "zh": "节日"},
    "Snow": {"en": "Snow", "zh": "雪天"},
    "Wedding": {"en": "Wedding", "zh": "婚礼"},
}


PROFESSION_TRANSLATIONS = {
    "Rancher": {"zh": ("牧场主", "动物产品生产速度提升 20%")},
    "Tiller": {"zh": ("农耕者", "农作物售价提高 10%")},
    "Coopmaster": {"zh": ("鸡舍大师", "鸡舍动物产量翻倍，且友好度增长速度翻倍")},
    "Shepherd": {"zh": ("牧羊人", "畜棚动物产量翻倍，且友好度增长速度翻倍")},
    "Artisan": {"zh": ("工匠", "工匠物品（酒、奶酪、油等）售价提高 40%")},
    "Agriculturist": {"zh": ("农学家", "农作物生长速度提高 10%")},
    "Fisher": {"zh": ("渔夫", "鱼类售价提高 25%")},
    "Trapper": {"zh": ("捕手", "蟹笼无需鱼饵即可工作")},
    "Angler": {"zh": ("垂钓者", "鱼类售价提高 50%")},
    "Pirate": {"zh": ("海盗", "钓鱼时找到宝箱的概率翻倍")},
    "Mariner": {"zh": ("水手", "蟹笼永远不会产出垃圾")},
    "Luremaster": {"zh": ("诱饵大师", "蟹笼无需鱼饵，且永远不会产出垃圾")},
    "Forester": {"zh": ("护林人", "砍树速度提升 50%")},
    "Gatherer": {"zh": ("采集者", "采集物有 20% 概率双倍掉落")},
    "Lumberjack": {"zh": ("伐木工", "橡树、枫树和松树有概率掉落硬木")},
    "Tapper": {"zh": ("树液采集者", "糖浆售价提高 25%")},
    "Botanist": {"zh": ("植物学家", "采集物永远是铱星品质")},
    "Tracker": {"zh": ("追踪者", "在地图上显示可采集物位置")},
    "Miner": {"zh": ("矿工", "宝石和矿石额外掉落 1 个")},
    "Geologist": {"zh": ("地质学家", "宝石节点有概率掉落双倍宝石")},
    "Blacksmith": {"zh": ("铁匠", "敲碎石头和金属矿点速度提升 50%")},
    "Prospector": {"zh": ("勘探者", "石头掉落煤炭的概率翻倍")},
    "Excavator": {"zh": ("挖掘者", "石头掉落晶球的概率翻倍")},
    "Gemologist": {"zh": ("宝石学家", "宝石售价提高 30%")},
    "Fighter": {"zh": ("战士", "造成伤害提高 10%，受到伤害降低 10%")},
    "Scout": {"zh": ("斥候", "暴击率提高 50%")},
    "Brute": {"zh": ("斗士", "造成伤害提高 15%")},
    "Defender": {"zh": ("守卫者", "受到伤害降低 15%")},
    "Acrobat": {"zh": ("杂技师", "特殊攻击冷却时间减少 50%")},
    "Desperado": {"zh": ("亡命徒", "暴击伤害从 2 倍提高到 3 倍")},
}


MAIL_FLAG_OVERRIDES = {
    "ccDoorUnlock": {"zh": "社区中心大门已解锁"},
    "canReadJunimoText": {"zh": "已能读懂祝尼魔文字"},
    "ccBoilerRoom": {"zh": "锅炉房已修复"},
    "ccBulletin": {"zh": "布告栏已修复"},
    "ccCraftsRoom": {"zh": "工艺室已修复"},
    "ccFishTank": {"zh": "鱼缸已修复"},
    "ccPantry": {"zh": "茶水间已修复"},
    "ccVault": {"zh": "金库已修复"},
    "ccIsComplete": {"zh": "社区中心已完成"},
    "abandonedJojaMartAccessible": {"zh": "废弃 Joja 超市可进入"},
    "ccMovieTheater": {"zh": "社区中心电影院已建成"},
    "JojaMember": {"zh": "Joja 会员"},
    "jojaBoilerRoom": {"zh": "Joja 锅炉房项目已完成"},
    "jojaCraftsRoom": {"zh": "Joja 工艺室项目已完成"},
    "jojaFishTank": {"zh": "Joja 鱼缸项目已完成"},
    "jojaPantry": {"zh": "Joja 茶水间项目已完成"},
    "jojaVault": {"zh": "Joja 金库项目已完成"},
    "ccMovieTheaterJoja": {"zh": "Joja 电影院已建成"},
    "birdieQuestFinished": {"zh": "贝啼任务已完成"},
    "birdieQuestBegun": {"zh": "贝啼任务已开始"},
    "gotBirdieReward": {"zh": "已领取贝啼任务奖励"},
    "henchmanGone": {"zh": "女巫仆从已离开"},
    "leoMoved": {"zh": "里奥已搬到山谷"},
    "OpenedSewer": {"zh": "下水道已开启"},
    "willyBoatFixed": {"zh": "威利的船已修好"},
    "CalderaTreasure": {"zh": "已取得火山口宝藏"},
    "guildMember": {"zh": "探险家公会成员"},
    "museumComplete": {"zh": "博物馆收藏已完成"},
    "Egg Festival": {"zh": "已参加复活节彩蛋节"},
    "Ice Festival": {"zh": "已参加冰雪节"},
    "Desert Festival": {"zh": "已参加沙漠节"},
    "GalaxySword": {"zh": "已获得银河之剑"},
    "HasUnlockedSkullDoor": {"zh": "头骨洞穴大门已解锁"},
    "willyBackRoomInvitation": {"zh": "已收到威利后室邀请"},
    "checkedMonsterBoard": {"zh": "已查看怪物讨伐公告板"},
    "GotMysteryBook": {"zh": "已获得神秘之书"},
    "GotWoodcuttingBook": {"zh": "已获得伐木之书"},
    "GotCrabbingBook": {"zh": "已获得捕蟹之书"},
    "DefenseBookDropped": {"zh": "已掉落防御之书"},
    "wizardJunimoNote": {"zh": "法师的祝尼魔纸条"},
    "checkedRaccoonStump": {"zh": "已查看浣熊树桩"},
    "gotFirstBillboardPrizeTicket": {"zh": "已获得第一张公告板奖票"},
    "Desert_Festival_Shady_Guy": {"zh": "沙漠节：神秘人"},
    "Desert_Festival_Marlon": {"zh": "沙漠节：马龙"},
    "DF_Gil_Hat": {"zh": "沙漠节：吉尔的帽子"},
    "Checked_DF_Mine_Explanation": {"zh": "已查看沙漠节矿洞说明"},
    "TH_SandDragon": {"zh": "寻宝线索：沙龙"},
    "TH_LumberPile": {"zh": "寻宝线索：木料堆"},
    "TH_Railroad": {"zh": "寻宝线索：铁路"},
    "TH_Tunnel": {"zh": "寻宝线索：隧道"},
    "willyHours": {"zh": "威利营业时间提示"},
    "qiCave": {"zh": "齐先生洞穴已开启"},
    "sawQiPlane": {"zh": "已看见齐先生的飞机"},
    "FizzFirstDialogue": {"zh": "菲兹初次对话"},
    "Got_Capsule": {"zh": "已获得太空舱"},
    "Broken_Capsule": {"zh": "太空舱已破损"},
    "Capsule_Broken": {"zh": "太空舱已破损"},
    "gotCAMask": {"zh": "已获得 ConcernedApe 面具"},
    "pennyRefurbished": {"zh": "潘妮的房间已翻新"},
    "cursed_doll": {"zh": "诅咒娃娃事件"},
    "GotPerfectionStatue": {"zh": "已获得完美雕像"},
    "read_a_book": {"zh": "已读过一本书"},
    "gotMaxStamina": {"zh": "体力上限已提升"},
    "petLoveMessage": {"zh": "已收到宠物好感提示"},
    "CF_Spouse": {"zh": "节庆事件：配偶"},
    "seenRaccoonFinishEvent": {"zh": "已看过浣熊结局事件"},
    "raccoonMovedIn": {"zh": "浣熊已搬入"},
    "witchStatueGone": {"zh": "女巫雕像已消失"},
    "summit_cheat_event": {"zh": "山顶作弊事件"},
    "checkedBulletinOnce": {"zh": "已首次查看布告栏"},
    "activatedJungleJunimo": {"zh": "丛林祝尼魔已激活"},
    "destroyedPods": {"zh": "已摧毁怪舱"},
    "killedSkeleton": {"zh": "已击败骷髅"},
    "slimeHutchBuilt": {"zh": "史莱姆屋已建成"},
    "Gil_Telephone": {"zh": "吉尔电话服务已解锁"},
    "Gil_FlameSpirits": {"zh": "吉尔的火焰精灵提示"},
    "WizardCatalogue": {"zh": "已获得法师目录"},
    "JojaThriveTerms": {"zh": "已阅读 Joja Thrive 条款"},
    "pamNewChannel": {"zh": "潘姆新频道事件"},
    "beenToWoods": {"zh": "已到过秘密森林"},
    "Island_FirstParrot": {"zh": "姜岛：首次遇见鹦鹉"},
    "islandNorthCaveOpened": {"zh": "姜岛北部洞穴已开启"},
    "reachedCaldera": {"zh": "已到达火山口"},
    "Island Resort": {"zh": "姜岛度假村已开放"},
    "ClintReward": {"zh": "克林特奖励已领取"},
    "ClintReward2": {"zh": "克林特第二份奖励已领取"},
    "junimoPlush": {"zh": "已获得祝尼魔毛绒玩偶"},
    "GiantQiFruitMessage": {"zh": "已收到巨大齐果提示"},
    "CF_Fair": {"zh": "节庆事件：庆典"},
    "CF_Fish": {"zh": "节庆事件：钓鱼"},
    "CF_Sewer": {"zh": "节庆事件：下水道"},
    "CF_Mines": {"zh": "节庆事件：矿井"},
    "CF_Statue": {"zh": "节庆事件：雕像"},
    "grandpaPerfect": {"zh": "爷爷评价已达完美"},
    "Backpack Tip": {"zh": "背包升级提示"},
    "gotMasteryHint": {"zh": "已收到精通提示"},
    "TH_MayorFridge": {"zh": "寻宝线索：镇长的冰箱"},
    "Henchman1": {"zh": "女巫随从事件 1"},
    "FullCrabPond": {"zh": "蟹池已满"},
    "safariGuyIntro": {"zh": "蜗牛教授初次登场"},
    "JojaGreeting": {"zh": "Joja 欢迎信"},
    "somethingToDonate": {"zh": "有物品可捐赠给博物馆"},
    "somethingWasDonated": {"zh": "已向博物馆捐赠物品"},
    "AbigailInMineFirst": {"zh": "阿比盖尔矿洞初遇"},
    "Summit_event": {"zh": "山顶事件"},
    "QiChat1": {"zh": "齐先生对话 1"},
    "QiChat2": {"zh": "齐先生对话 2"},
    "apeChat1": {"zh": "ConcernedApe 对话 1"},
    "hasSeenAbandonedJunimoNote": {"zh": "已看过废弃 Joja 超市祝尼魔纸条"},
    "secretNote21_done": {"zh": "秘密纸条 21 已完成"},
    "addedParrotBoy": {"zh": "鹦鹉男孩已加入"},
    "ISLAND_NORTH_DIGSITE_LOAD": {"zh": "姜岛北部挖掘场事件已初始化"},
    "landslideDone": {"zh": "山体滑坡已清除"},
    "lostWalnutFound": {"zh": "已找到遗失的核桃"},
    "lostBookFound": {"zh": "已找到遗失之书"},
    "ectoplasm Drop": {"zh": "灵外质已掉落"},
    "prismaticJellyDrop": {"zh": "五彩果冻已掉落"},
    "gotMissingStocklist": {"zh": "已获得失落的库存单"},
    "robinWell": {"zh": "罗宾的水井升级已开放"},
    "SeaAmulet": {"zh": "已获得美人鱼吊坠"},
    "foundLostTools": {"zh": "已找回遗失的工具"},
    "ccBulletinThankYou": {"zh": "社区中心布告栏感谢信"},
    "transferredObjectsPamHouse": {"zh": "已转移潘姆家的物品"},
    "transferredObjectsJojaMart": {"zh": "已转移 Joja 超市的物品"},
    "Hatters": {"zh": "帽子鼠已解锁"},
    "MarlonRecovery": {"zh": "马龙物品找回服务已解锁"},
    "gotMummifiedFrog": {"zh": "已获得木乃伊蛙标本"},
    "activateGoldenParrotsTonight": {"zh": "今晚将激活金鹦鹉"},
    "talkedToGourmand": {"zh": "已与美食家青蛙对话"},
    "sawParrotBoyIntro": {"zh": "已看过鹦鹉男孩登场事件"},
    "Island_N_BuriedTreasure": {"zh": "姜岛北部埋藏宝藏"},
    "Saw_Flame_Sprite_North_South": {"zh": "已看过火焰精灵事件：北部南侧"},
    "Saw_Flame_Sprite_North_North": {"zh": "已看过火焰精灵事件：北部北侧"},
    "Island_Secret_BuriedTreasureNut": {"zh": "姜岛：秘密埋藏宝藏核桃"},
    "Island_Secret_BuriedTreasure": {"zh": "姜岛：秘密埋藏宝藏"},
    "Saw_Flame_Sprite_South": {"zh": "已看过火焰精灵事件：南部"},
    "Island_W_Obelisk": {"zh": "姜岛西部方尖碑"},
    "tigerSlimeNut": {"zh": "已获得虎纹史莱姆核桃"},
    "Island_W_BuriedTreasure": {"zh": "姜岛西部埋藏宝藏"},
    "Island_W_BuriedTreasure2": {"zh": "姜岛西部埋藏宝藏 2"},
    "GuildQuest": {"zh": "冒险家公会任务"},
    "Qi Challenge Complete": {"zh": "齐先生挑战已完成"},
    "Visited Quarry Mine": {"zh": "已访问采石场矿洞"},
    "reachedBottomOfHardMines": {"zh": "已到达矿井困难模式底层"},
    "Carolines Necklace": {"zh": "已找到卡洛琳的项链"},
    "Island_VolcanoBridge": {"zh": "姜岛火山桥梁已修复"},
    "Island_VolcanoShortcutOut": {"zh": "姜岛火山出口捷径已开启"},
    "marnieAutoGrabber": {"zh": "玛妮自动采集器事件"},
    "Beat_PK": {"zh": "已通关草原之王"},
    "JunimoKart": {"zh": "祝尼魔卡丁车"},
    "RarecrowSociety": {"zh": "稀有稻草人收集奖励"},
    "GreenRainGus": {"zh": "绿雨天格斯事件"},
    "fieldOfficeFinale": {"zh": "岛屿办事处结局事件"},
    "robinKitchenLetter": {"zh": "罗宾的厨房来信"},
    "krobusUnseal": {"zh": "科罗布斯封印已解除"},
    "communityUpgradeShortcuts": {"zh": "社区升级：山谷捷径已开通"},
    "hasPickedUpMagicInk": {"zh": "已拾取魔法墨水"},
    "hasActivatedForestPylon": {"zh": "森林传送柱已激活"},
    "FizzIntro": {"zh": "菲兹登场事件"},
    "pamHouseUpgrade": {"zh": "潘姆家升级已完成"},
    "Farm_Eternal_Parrots": {"zh": "农场永续事件：鹦鹉"},
    "Farm_Eternal": {"zh": "农场永续事件"},
    "fortuneTeller": {"zh": "占卜师事件"},
    "raccoonTreeFallen": {"zh": "浣熊树已倒下"},
    "button_tut_1": {"zh": "按钮教学 1 已显示"},
    "button_tut_2": {"zh": "按钮教学 2 已显示"},
    "fishing2": {"zh": "钓鱼等级 2 提示"},
    "fishing6": {"zh": "钓鱼等级 6 提示"},
}


ZH_MAIL_WORDS = {
    "Community": "社区",
    "Center": "中心",
    "Door": "大门",
    "Unlock": "解锁",
    "Unlocked": "已解锁",
    "Read": "阅读",
    "Junimo": "祝尼魔",
    "Text": "文字",
    "Boiler": "锅炉房",
    "Room": "房间",
    "Bulletin": "布告栏",
    "Crafts": "工艺室",
    "Fish": "鱼",
    "Tank": "缸",
    "Pantry": "茶水间",
    "Vault": "金库",
    "Complete": "完成",
    "Completed": "已完成",
    "Movie": "电影",
    "Theater": "院",
    "Cursed": "诅咒",
    "Doll": "娃娃",
    "Perfection": "完美",
    "Accessible": "可进入",
    "Member": "会员",
    "Quest": "任务",
    "Finished": "已完成",
    "Begun": "已开始",
    "Reward": "奖励",
    "First": "首次",
    "Purchase": "购买",
    "Build": "建造",
    "Remove": "移除",
    "Bedroom": "卧室",
    "Wall": "墙面",
    "Corner": "角落",
    "Cubby": "小隔间",
    "Dining": "餐厅",
    "Southern": "南侧",
    "Renovation": "翻修",
    "Open": "开放",
    "Moved": "搬来",
    "Void": "虚空",
    "Book": "书",
    "Dropped": "掉落",
    "Golden": "金色",
    "Scythe": "镰刀",
    "Pet": "宠物",
    "Rejected": "拒绝",
    "Adoption": "收养",
    "Crabbing": "捕蟹",
    "Mystery": "神秘",
    "Saw": "看到",
    "Sand": "沙",
    "Dragon": "龙",
    "Plane": "飞机",
    "Checked": "已查看",
    "Billboard": "公告板",
    "Prize": "奖",
    "Monster": "怪物",
    "Board": "告示板",
    "Spring": "春季",
    "Boat": "船",
    "Fixed": "修好",
    "Love": "好感",
    "Message": "提示",
    "Desert": "沙漠",
    "Festival": "节",
    "Shady": "神秘",
    "Guy": "家伙",
    "Spouse": "配偶",
    "Defense": "防御",
    "Cave": "洞穴",
    "Stamina": "体力",
    "Boat": "船",
    "Invitation": "邀请",
    "Seen": "已看见",
    "Finish": "结局",
    "Event": "事件",
    "Raccoon": "浣熊",
    "Stump": "树桩",
    "Wizard": "法师",
    "Island": "姜岛",
    "Turtle": "海龟",
    "Artifact": "文物",
    "Found": "已找到",
    "Pearl": "珍珠",
    "Statue": "雕像",
    "Gone": "已消失",
    "Summit": "山顶",
    "Cheat": "作弊",
    "Activated": "已激活",
    "Jungle": "丛林",
    "Saved": "已救出",
    "Friends": "朋友",
    "Destroyed": "已摧毁",
    "Built": "已建造",
    "Pods": "怪舱",
    "Flame": "火焰",
    "Spirits": "精灵",
    "Pam": "潘姆",
    "Channel": "频道",
    "New": "新",
    "Skull": "头骨",
    "Backpack": "背包",
    "Tip": "提示",
    "Mastery": "精通",
    "Railroad": "铁路",
    "Tunnel": "隧道",
    "Grandpa": "爷爷",
    "Note": "纸条",
    "Secret": "秘密",
    "Return": "回程",
    "Scepter": "权杖",
    "Stocklist": "库存单",
    "Lumber": "木料",
    "Pile": "堆",
    "Landslide": "落石",
    "Copper": "铜矿",
    "Boat": "船",
    "Ticket": "票",
    "Machine": "机器",
    "Anchor": "锚",
    "Hull": "船体",
    "Journey": "旅程",
    "Volcano": "火山",
    "Shortcut": "捷径",
    "Unlocked": "已解锁",
    "Resort": "度假村",
    "Fair": "庆典",
    "Mines": "矿井",
    "Catalogue": "目录",
    "Thrive": "Thrive",
    "Terms": "条款",
    "North": "北部",
    "South": "南部",
    "West": "西部",
    "Parrot": "鹦鹉",
    "Plush": "毛绒玩偶",
    "Digsite": "挖掘场",
    "Load": "初始化",
    "Done": "已完成",
    "Lost": "遗失",
    "Ectoplasm": "灵外质",
    "Prismatic": "五彩",
    "Jelly": "果冻",
    "Well": "水井",
    "Thank": "感谢",
    "You": "信",
    "Transferred": "已转移",
    "Objects": "物品",
    "Mummified": "木乃伊",
    "Frog": "蛙",
    "Tonight": "今晚",
    "Buried": "埋藏",
    "Treasure": "宝藏",
    "Obelisk": "方尖碑",
    "Tiger": "虎纹",
    "Quarry": "采石场",
    "Bottom": "底层",
    "Hard": "困难模式",
    "Necklace": "项链",
    "Kitchen": "厨房",
    "Upgrade": "升级",
    "Forest": "森林",
    "Pylon": "传送柱",
    "Fortune": "占卜",
    "Teller": "师",
    "Crab": "蟹",
    "Pond": "池",
    "Greeting": "欢迎信",
    "Mayor": "镇长",
    "Fridge": "冰箱",
    "Intro": "登场",
    "Gourmand": "美食家青蛙",
    "Magic": "魔法",
    "Ink": "墨水",
    "Eternal": "永续",
}


RENOVATION_LABELS = {
    "build_crib": "育婴房",
    "remove_crib": "移除育婴房",
    "attic": "阁楼",
    "bedroomwall": "卧室墙面",
    "corner": "角落房间",
    "cubby": "小隔间",
    "dining": "餐厅",
    "diningroomwall": "餐厅墙面",
    "extendedcorner": "扩展角落房间",
    "southern": "南侧房间",
    "bedroom": "卧室",
    "farupperroom": "上层房间",
}


ISLAND_UPGRADE_LABELS = {
    "House": "姜岛农舍",
    "House_Mailbox": "姜岛农舍邮箱",
    "Bridge": "姜岛桥梁",
    "Trader": "姜岛商人",
    "ParrotPlatform": "鹦鹉快递平台",
}


MAIL_FLAG_PREFIX_TEMPLATES = (
    ("Got_", "已获得：{label}"),
    ("Got", "已获得：{label}"),
    ("got", "已获得：{label}"),
    ("checked", "已查看：{label}"),
    ("Checked", "已查看：{label}"),
    ("seen", "已看过：{label}"),
    ("Seen", "已看过：{label}"),
    ("hasSeen", "已看过：{label}"),
    ("hasActivated", "已激活：{label}"),
    ("hasPickedUp", "已拾取：{label}"),
    ("Opened", "已开启：{label}"),
    ("opened", "已开启：{label}"),
    ("Visited", "已访问：{label}"),
    ("visited", "已访问：{label}"),
    ("reached", "已到达：{label}"),
    ("completed", "已完成：{label}"),
    ("activated", "已激活：{label}"),
    ("activate", "已激活：{label}"),
    ("saved", "已救出：{label}"),
    ("destroyed", "已摧毁：{label}"),
    ("rejected", "已拒绝：{label}"),
    ("read_", "已阅读：{label}"),
    ("read", "已阅读：{label}"),
)


MAIL_FLAG_CATEGORY_ORDER = (
    "main_story",
    "ginger_island",
    "renovation",
    "festival",
    "hidden_event",
)


MAIL_FLAG_CATEGORY_KEYS = {
    "main_story": "mail_flag_group_main_story",
    "ginger_island": "mail_flag_group_ginger_island",
    "renovation": "mail_flag_group_renovation",
    "festival": "mail_flag_group_festival",
    "hidden_event": "mail_flag_group_hidden_event",
}


MAIL_FLAG_RENOVATION_SET = {
    "pennyRefurbished",
    "pennyQuilt0",
    "pennyQuilt1",
    "pennyQuilt2",
    "robinWell",
    "communityUpgradeShortcuts",
    "pamHouseUpgrade",
    "transferredObjectsPamHouse",
    "transferredObjectsJojaMart",
    "robinKitchenLetter",
}


MAIL_FLAG_FESTIVAL_SET = {
    "Egg Festival",
    "Ice Festival",
    "Desert Festival",
    "Desert_Festival_Shady_Guy",
    "Desert_Festival_Marlon",
    "DF_Gil_Hat",
    "Checked_DF_Mine_Explanation",
    "CF_Spouse",
    "CF_Fair",
    "CF_Fish",
    "CF_Sewer",
    "CF_Mines",
    "CF_Statue",
    "fortuneTeller",
    "spring_2_1",
}


MAIL_FLAG_GINGER_ISLAND_SET = {
    "birdieQuestFinished",
    "birdieQuestBegun",
    "gotBirdieReward",
    "henchmanGone",
    "leoMoved",
    "willyHours",
    "FizzFirstDialogue",
    "qiCave",
    "willyBoatFixed",
    "CalderaTreasure",
    "willyBackRoomInvitation",
    "Island_Turtle",
    "artifactFound",
    "gotPearl",
    "Visited_Island",
    "Island_FirstParrot",
    "islandNorthCaveOpened",
    "reachedCaldera",
    "Island Resort",
    "GiantQiFruitMessage",
    "ISLAND_NORTH_DIGSITE_LOAD",
    "lostWalnutFound",
    "gotMummifiedFrog",
    "activateGoldenParrotsTonight",
    "willyBoatTicketMachine",
    "willyBoatAnchor",
    "willyBoatHull",
    "seenBoatJourney",
    "volcanoShortcutUnlocked",
    "talkedToGourmand",
    "sawParrotBoyIntro",
    "addedParrotBoy",
    "GuildQuest",
    "Qi Challenge Complete",
    "Island_UpgradeHouse",
    "Island_UpgradeBridge",
    "Island_UpgradeTrader",
    "Island_UpgradeHouse_Mailbox",
    "Island_UpgradeParrotPlatform",
    "Island_N_BuriedTreasure",
    "Island_Secret_BuriedTreasureNut",
    "Island_Secret_BuriedTreasure",
    "Island_W_Obelisk",
    "Island_W_BuriedTreasure",
    "Island_W_BuriedTreasure2",
    "Island_VolcanoBridge",
    "Island_VolcanoShortcutOut",
    "Saw_Flame_Sprite_North_South",
    "Saw_Flame_Sprite_North_North",
    "Saw_Flame_Sprite_South",
    "Saw_Flame_Sprite_Volcano",
    "tigerSlimeNut",
    "fieldOfficeFinale",
    "FizzIntro",
    "Farm_Eternal_Parrots",
    "Farm_Eternal",
}


MAIL_FLAG_HIDDEN_EVENT_SET = {
    "cursed_doll",
    "GotPerfectionStatue",
    "sawQiPlane",
    "Got_Capsule",
    "Broken_Capsule",
    "Capsule_Broken",
    "GotMysteryBook",
    "seenRaccoonFinishEvent",
    "raccoonMovedIn",
    "wizardJunimoNote",
    "checkedRaccoonStump",
    "witchStatueGone",
    "SecretNote20_done",
    "SecretNote18_done",
    "SecretNote16_done",
    "SecretNote17_done",
    "SecretNote19_done",
    "secretNote21_done",
    "TH_LumberPile",
    "TH_SandDragon",
    "TH_Railroad",
    "TH_Tunnel",
    "TH_MayorFridge",
    "QiChat1",
    "QiChat2",
    "apeChat1",
    "junimoPlush",
    "hasSeenAbandonedJunimoNote",
    "seenJunimoNote",
    "gotFirstJunimoChest",
    "LewisStatue",
    "raccoonTreeFallen",
    "hasSeenGrandpaNote",
    "grandpaPerfect",
    "summit_cheat_event",
    "Summit_event",
    "Beat_PK",
    "JunimoKart",
}


def translate_weather_tomorrow(value):

    if not value:

        return ""

    labels = WEATHER_TOMORROW_LABELS.get(value)

    if not labels:

        return value

    return labels.get(tr.current_lang, labels["en"])


def get_weather_tomorrow_options(extra_values=None):

    values = list(WEATHER_TOMORROW_LABELS.keys())

    for value in extra_values or []:

        if value and value not in values:

            values.append(value)

    return [translate_weather_tomorrow(value) for value in values]


def parse_display_weather_tomorrow(display_value, extra_values=None):

    if not display_value:

        return ""

    values = list(WEATHER_TOMORROW_LABELS.keys()) + list(extra_values or [])

    for value in values:

        if display_value == value or display_value == translate_weather_tomorrow(value):

            return value

    return display_value


def translate_profession_name(name):

    localized = PROFESSION_TRANSLATIONS.get(name, {})

    if tr.current_lang == "zh" and "zh" in localized:

        return localized["zh"][0]

    return name


def translate_profession_desc(name, default_desc):

    localized = PROFESSION_TRANSLATIONS.get(name, {})

    if tr.current_lang == "zh" and "zh" in localized:

        return localized["zh"][1]

    return default_desc


def _translate_identifier_to_zh(value):

    label = _humanize_identifier(value)

    if not label:

        return value

    translated_parts = []

    for token in label.split():

        translated_token = ZH_MAIL_WORDS.get(token)

        if translated_token is None:

            npc_name = translate_npc_name(token)

            translated_token = npc_name if npc_name != token else token

        translated_parts.append(translated_token)

    return "".join(translated_parts)


def _translate_renovation_label(value):

    normalized = _normalize_fragment(value)

    return RENOVATION_LABELS.get(normalized, _translate_identifier_to_zh(value))


def _translate_mail_flag_zh(flag):

    if flag.startswith("FirstPurchase_"):

        return f"首次购买翻修：{_translate_renovation_label(flag[len('FirstPurchase_') :])}"

    if flag.startswith("renovation_") and flag.endswith("_open"):

        return f"翻修已开放：{_translate_renovation_label(flag[len('renovation_') : -len('_open')])}"

    if flag.startswith("Island_Upgrade"):

        upgrade_key = flag[len("Island_Upgrade") :]

        return f"姜岛建设：{ISLAND_UPGRADE_LABELS.get(upgrade_key, _translate_identifier_to_zh(upgrade_key))}"

    if flag.startswith("Desert_Festival_"):

        return f"沙漠节：{_translate_identifier_to_zh(flag[len('Desert_Festival_') :])}"

    if flag.startswith("DF_"):

        return f"沙漠节：{_translate_identifier_to_zh(flag[len('DF_') :])}"

    if flag.startswith("CF_"):

        return f"节庆事件：{_translate_identifier_to_zh(flag[len('CF_') :])}"

    if flag.startswith("TH_"):

        return f"寻宝线索：{_translate_identifier_to_zh(flag[len('TH_') :])}"

    if flag.startswith("Saw_Flame_Sprite_"):

        return f"火焰精灵事件：{_translate_identifier_to_zh(flag[len('Saw_Flame_Sprite_') :])}"

    if flag.startswith("Island_"):

        return f"姜岛：{_translate_identifier_to_zh(flag[len('Island_') :])}"

    match = re.fullmatch(r"(?i)secretnote(\d+)_done", flag)

    if match:

        return f"秘密纸条 {match.group(1)} 已完成"

    match = re.fullmatch(r"numbersEgg(.+)", flag)

    if match:

        return f"数字彩蛋线索 {match.group(1)}"

    match = re.fullmatch(r"pennyQuilt(\d+)", flag)

    if match:

        return f"潘妮拼布样式 {match.group(1)}"

    match = re.fullmatch(r"(?i)quest(\d+)", flag)

    if match:

        return f"任务 {match.group(1)} 已完成"

    match = re.fullmatch(r"button_tut_(\d+)", flag)

    if match:

        return f"按钮教学 {match.group(1)} 已显示"

    match = re.fullmatch(r"fishing(\d+)", flag)

    if match:

        return f"钓鱼等级 {match.group(1)} 提示"

    match = re.fullmatch(r"QiChat(\d+)", flag)

    if match:

        return f"齐先生对话 {match.group(1)}"

    match = re.fullmatch(r"apeChat(\d+)", flag)

    if match:

        return f"ConcernedApe 对话 {match.group(1)}"

    match = re.fullmatch(r"spring_(\d+)_(\d+)", flag)

    if match:

        return f"春季事件 {match.group(1)}-{match.group(2)}"

    for prefix, template in MAIL_FLAG_PREFIX_TEMPLATES:

        if flag.startswith(prefix):

            remainder = flag[len(prefix) :]

            if remainder:

                return template.format(label=_translate_identifier_to_zh(remainder))

    return _translate_identifier_to_zh(flag)


def translate_mail_flag(flag):

    if flag in MAIL_FLAG_OVERRIDES and tr.current_lang in MAIL_FLAG_OVERRIDES[flag]:

        return MAIL_FLAG_OVERRIDES[flag][tr.current_lang]

    default_label = tr.translate(f"mail_flag_{_normalize_fragment(flag)}", _humanize_identifier(flag))

    if tr.current_lang == "zh" and default_label == _humanize_identifier(flag):

        return _translate_mail_flag_zh(flag)

    return default_label


def get_mail_flag_category(flag):

    if flag.startswith("FirstPurchase_") or flag.startswith("renovation_") or flag in MAIL_FLAG_RENOVATION_SET:

        return "renovation"

    if flag in MAIL_FLAG_FESTIVAL_SET or flag.startswith("Desert_Festival_") or flag.startswith("DF_") or flag.startswith("CF_"):

        return "festival"

    if (
        flag in MAIL_FLAG_GINGER_ISLAND_SET
        or flag.startswith("Island_")
        or flag.startswith("Saw_Flame_Sprite_")
        or "Island" in flag
        or "Caldera" in flag
        or "Parrot" in flag
        or "Walnut" in flag
        or "Volcano" in flag
    ):

        return "ginger_island"

    if flag in MAIL_FLAG_HIDDEN_EVENT_SET:

        return "hidden_event"

    return "main_story"


def get_mail_flag_category_order():

    return MAIL_FLAG_CATEGORY_ORDER


def get_mail_flag_category_label(category_key):

    return tr.translate(MAIL_FLAG_CATEGORY_KEYS.get(category_key, "mail_flag_group_main_story"))


def translate_npc_name(name):

    return tr.translate(f"npc_{_normalize_fragment(name)}", translate_game_name(name, name))


def translate_location_name(name):

    return tr.translate(f"location_{_normalize_fragment(name)}", translate_game_name(name, name))


def translate_building_name(name):

    return tr.translate(f"building_{_normalize_fragment(name)}", translate_game_name(name, name))


def translate_animal_type(name):

    return tr.translate(f"animal_type_{_normalize_fragment(name)}", translate_game_name(name, name))


def translate_bundle_name(name):

    return tr.translate(f"bundle_{_normalize_fragment(name)}", translate_game_name(name, name))


def translate_room_name(name):

    return tr.translate(f"room_{_normalize_fragment(name)}", translate_game_name(name, name))


@lru_cache(maxsize=1)
def get_known_building_names():

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    generated_path = os.path.join(base_dir, "generated", "buildings.json")

    with open(generated_path, "r", encoding="utf-8") as file:

        buildings = json.load(file)

    return tuple(entry["name"] for entry in buildings if entry.get("name"))


def get_display_building_name_options(extra_names=None):

    names = list(get_known_building_names())

    for name in extra_names or []:

        if name and name not in names:

            names.append(name)

    display_names = []

    seen = set()

    for name in names:

        display_name = translate_building_name(name)

        if display_name not in seen:

            seen.add(display_name)

            display_names.append(display_name)

    return display_names


def parse_display_building_name(display_name, extra_names=None):

    if not display_name:

        return ""

    for raw_name in list(get_known_building_names()) + list(extra_names or []):

        if not raw_name:

            continue

        translated_name = translate_building_name(raw_name)

        if display_name == translated_name or display_name == raw_name:

            return raw_name

    return display_name
