# Define appearance lookup data used by character customization screens.
CHARACTER_COLORS = {

    'primary_skin': [

        (249, 174, 137), (225, 140, 102), (240, 160, 130), (247, 185, 154),

        (196, 100, 71), (174, 95, 57), (162, 70, 18), (210, 138, 59),

        (189, 121, 68), (255, 171, 178), (214, 178, 169), (232, 138, 94),

        (226, 226, 177), (239, 140, 160), (140, 84, 41), (218, 131, 84),

        (104, 191, 232), (189, 232, 136), (255, 142, 142), (178, 145, 255),

        (255, 221, 140), (221, 210, 211), (255, 205, 158), (255, 211, 181),

    ],

    'secondary_skin': [

        (224, 107, 101), (168, 67, 61), (209, 110, 72), (227, 149, 135),

        (154, 63, 45), (112, 42, 25), (119, 32, 20), (190, 94, 44),

        (162, 72, 26), (194, 115, 110), (154, 97, 108), (163, 64, 45),

        (152, 130, 95), (172, 78, 90), (90, 40, 19), (175, 64, 41),

        (0, 113, 206), (64, 178, 22), (175, 22, 22), (120, 0, 206),

        (204, 133, 26), (136, 124, 129), (250, 130, 117), (255, 155, 135),

    ],

    'tertiary_skin': [

        (107, 0, 58), (85, 36, 53), (85, 36, 53), (112, 51, 57),

        (88, 29, 21), (65, 24, 18), (66, 19, 11), (102, 32, 26),

        (85, 37, 24), (124, 57, 52), (83, 52, 76), (85, 33, 39),

        (84, 54, 52), (85, 36, 53), (46, 11, 4), (85, 38, 49),

        (0, 6, 81), (3, 65, 16), (63, 3, 3), (60, 26, 86),

        (78, 39, 3), (66, 60, 67), (121, 12, 62), (114, 47, 50),

    ],

    'primary_boot': [

        (212, 0, 0), (136, 178, 77), (179, 85, 0), (163, 118, 42),

        (150, 162, 162), (181, 125, 116), (92, 239, 255), (66, 66, 66),

        (103, 0, 0), (188, 0, 235), (99, 1, 229), (179, 85, 0),

        (119, 47, 21), (11, 99, 180), (50, 133, 48), (113, 7, 39),

        (9, 101, 130), (170, 129, 196), (242, 242, 242),

    ],

    'secondary_boot': [

        (170, 0, 0), (95, 124, 50), (142, 66, 0), (123, 85, 26),

        (109, 116, 131), (152, 105, 96), (43, 197, 226), (54, 54, 54),

        (77, 0, 0), (140, 0, 175), (75, 1, 151), (142, 66, 0),

        (91, 32, 16), (0, 56, 145), (14, 93, 58), (65, 4, 28),

        (0, 56, 145), (92, 74, 147), (219, 215, 206),

    ],

    'tertiary_boot': [

        (125, 0, 0), (67, 89, 37), (105, 44, 0), (87, 58, 11),

        (65, 70, 81), (88, 58, 54), (25, 92, 98), (38, 38, 38),

        (51, 7, 2), (107, 0, 151), (54, 0, 101), (83, 28, 0),

        (63, 21, 28), (18, 28, 107), (0, 62, 65), (44, 6, 17),

        (30, 38, 104), (40, 37, 107), (145, 140, 127),

    ],

    'quaternary_boot': [

        (85, 0, 0), (3, 50, 43), (67, 22, 0), (35, 0, 0),

        (15, 20, 47), (41, 25, 32), (0, 53, 57), (0, 0, 0),

        (17, 13, 8), (46, 0, 74), (15, 20, 47), (35, 0, 0),

        (33, 11, 5), (0, 0, 51), (0, 30, 42), (16, 10, 9),

        (14, 14, 51), (30, 38, 104), (33, 33, 33),

    ],

}

HAIRSTYLE_INFO = {

    'min': 0,

    'max': 73,

    'sheet1_max': 55,

    'description': 'Hairstyle 0-55 use first sheet, 56-73 use second sheet'

}

SKIN_INFO = {

    'min': 0,

    'max': 23,

    'description': 'Skin tone index (0-23)'

}

ACCESSORY_INFO = {

    'min': -1,

    'max': 29,

    'description': 'Accessory index (-1 = none, 0-29 = accessories)'

}

# Return the skin colors.
# It reads or mutates the XML-backed save model used by the editor.
def get_skin_colors(skin_index):

    if 0 <= skin_index < 24:

        return {

            'primary': CHARACTER_COLORS['primary_skin'][skin_index],

            'secondary': CHARACTER_COLORS['secondary_skin'][skin_index],

            'tertiary': CHARACTER_COLORS['tertiary_skin'][skin_index],

        }

    return None

# Return the boot colors.
# It reads or mutates the XML-backed save model used by the editor.
def get_boot_colors(boot_index):

    if 0 <= boot_index < 19:

        return {

            'primary': CHARACTER_COLORS['primary_boot'][boot_index],

            'secondary': CHARACTER_COLORS['secondary_boot'][boot_index],

            'tertiary': CHARACTER_COLORS['tertiary_boot'][boot_index],

            'quaternary': CHARACTER_COLORS['quaternary_boot'][boot_index],

        }

    return None

# Convert an RGB tuple into a hexadecimal color string.
# It reads or mutates the XML-backed save model used by the editor.
def rgb_to_hex(r, g, b):

    return f'#{r:02x}{g:02x}{b:02x}'

# Convert a hexadecimal color string into an RGB tuple.
# It reads or mutates the XML-backed save model used by the editor.
def hex_to_rgb(hex_color):

    hex_color = hex_color.lstrip('#')

    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
