# Define profession metadata and grouping used by player skill editors.
PROFESSIONS = {

    "Farming": {

        0: ("Rancher", "Animals produce goods 20% faster", 5, None),

        1: ("Tiller", "Crops are worth 10% more", 5, None),

        2: ("Coopmaster", "All Coop animals produce twice as much and befriend twice as fast", 10, 0),

        3: ("Shepherd", "Barn animals produce twice as much and befriend twice as fast", 10, 0),

        4: ("Artisan", "Artisan goods (wine, cheese, oil, etc.) are worth 40% more", 10, 1),

        5: ("Agriculturist", "Crops grow 10% faster", 10, 1)

    },

    "Fishing": {

        6: ("Fisher", "Fish are worth 25% more", 5, None),

        7: ("Trapper", "Crab pots work without bait", 5, None),

        8: ("Angler", "Fish are worth 50% more", 10, 6),

        9: ("Pirate", "Chance to find treasure while fishing doubled", 10, 6),

        10: ("Mariner", "Crab pots never produce trash", 10, 7),

        11: ("Luremaster", "Crab pots work without bait and never produce trash", 10, 7)

    },

    "Foraging": {

        12: ("Forester", "Chop down trees 50% faster", 5, None),

        13: ("Gatherer", "Chance to double forage (20% chance)", 5, None),

        14: ("Lumberjack", "Oak, Maple, and Pine trees have a chance to drop hardwood", 10, 12),

        15: ("Tapper", "Syrup is worth 25% more", 10, 12),

        16: ("Botanist", "Foraged goods are always iridium quality", 10, 13),

        17: ("Tracker", "Shows location of forageable items on the map", 10, 13)

    },

    "Mining": {

        18: ("Miner", "Gems and ore drop 1 extra", 5, None),

        19: ("Geologist", "Chance for a gem node to drop two gems instead of one", 5, None),

        20: ("Blacksmith", "Breaking rocks and metal nodes is 50% faster", 10, 18),

        21: ("Prospector", "Chance for coal from rocks doubled", 10, 18),

        22: ("Excavator", "Chance for geodes from rocks doubled", 10, 19),

        23: ("Gemologist", "Gems are worth 30% more", 10, 19)

    },

    "Combat": {

        24: ("Fighter", "Deal 10% more damage and take 10% less damage", 5, None),

        25: ("Scout", "Critical hit chance increased by 50%", 5, None),

        26: ("Brute", "Deal 15% more damage", 10, 24),

        27: ("Defender", "Take 15% less damage", 10, 24),

        28: ("Acrobat", "Cooldown of special moves reduced by 50%", 10, 25),

        29: ("Desperado", "Critical hits deal 3x damage instead of 2x", 10, 25)

    }

}
