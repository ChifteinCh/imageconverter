from PIL import Image
import base64
import zlib
import json
import time

start_time = time.time()

entities = {(0, 97, 148): 'iron-chest',
            (206, 162, 67): 'transport-belt',
            (115, 90, 0): 'underground-belt',
            (66, 129, 164): 'pipe',
            (207, 219, 207): 'stone-wall',
            (240, 240, 240): 'stone-wall',
            (123, 125, 122): 'gate',
            (25, 102, 148): 'pipe-to-ground',
            (250, 250, 250): 'blank',
            (0, 0, 0): 'blank'}

tiles = {(81, 81, 73): 'stone-path',
         (59, 61, 58): 'concrete',
         (179, 143, 33): 'hazard-concrete-left',
         (49, 49, 41): 'refined-concrete',
         (10, 10, 10): 'refined-concrete',
         (116, 93, 25): 'refined-hazard-concrete-left'}


def nearest_color(colors, current_color):
    return min(colors, key=lambda subject: sum((s - q) ** 2 for s, q in zip(subject, current_color)))


def decode_base64_and_inflate(b64string):
    decoded_data = base64.b64decode(b64string)
    return zlib.decompress(decoded_data)


def deflate_and_base64_encode(string_val):
    zlibbed_str = zlib.compress(string_val, 9)
    return base64.b64encode(zlibbed_str)


class Entity:
    def __init__(self, number, name, position):
        self.entity_number = number
        self.name = name
        self.position = position


class Tile:
    def __init__(self, name, position):
        self.position = position
        self.name = name


class Position:
    def __init__(self, xx, yy):
        self.x = xx
        self.y = yy


class Icon:
    def __init__(self, signal, index):
        self.signal = signal
        self.index = index


class Signal:
    def __init__(self, type_, name):
        self.type = type_
        self.name = name


class Blueprint:
    def __init__(self):
        self.entities = []
        self.label = 'blueprint'
        self.icons = [Icon(Signal('virtual', 'signal-A'), 1),
                      Icon(Signal('virtual', 'signal-R'), 2),
                      Icon(Signal('virtual', 'signal-T'), 3)]
        self.tiles = []
        self.version = 281479277379584
        self.item = 'blueprint'

    def add_entity(self, number, name, xy):
        for j in range(2):
            xy[j] += 0.5
        self.entities.append(Entity(number, name, Position(*xy)))

    def add_tile(self, name, xy):
        self.tiles.append(Tile(name, Position(*xy)))


blueprint_ = Blueprint()
timing_file = open('timing_solo.txt', 'w')

timing_file.write('Initialization ends in ' + repr(time.time() - start_time) + '\n')
start_time = time.time()

img = Image.open('downsized.png')
new_img = Image.new('RGB', img.size)

timing_file.write('Image opening ends in ' + repr(time.time() - start_time) + '\n')
start_time = time.time()

entity_numbers = 0
for x in range(img.size[0]):
    for y in range(img.size[1]):
        pixel_rgb = img.getpixel((x, y))
        new_pixel_rgb = nearest_color(entities | tiles, pixel_rgb)
        new_img.putpixel((x, y), new_pixel_rgb)
        if new_pixel_rgb in list(entities.keys()) and entities[new_pixel_rgb] != 'blank':
            entity_numbers += 1
            blueprint_.add_entity(entity_numbers, entities[new_pixel_rgb], [x, y])
        elif new_pixel_rgb in list(tiles.keys()):
            blueprint_.add_tile(tiles[new_pixel_rgb], [x, y])

timing_file.write('Image processing ends in ' + repr(time.time() - start_time) + '\n')
start_time = time.time()

new_img.save('colorized.png')
blueprint = {'blueprint': blueprint_}

timing_file.write('Image saving ends in ' + repr(time.time() - start_time) + '\n')
start_time = time.time()

json_data = json.dumps(blueprint, default=lambda o: o.__dict__, indent=4)
output_JSONfile = open('JSON output_solo.txt', 'w')
output_JSONfile.write(json_data)

timing_file.write('JSON conversion in ' + repr(time.time() - start_time) + '\n')
start_time = time.time()

coded_json_data = deflate_and_base64_encode(json_data.encode()).decode()

timing_file.write('JSON compressing in ' + repr(time.time() - start_time) + '\n')
start_time = time.time()

coded_blueprint_string = '0' + coded_json_data
output_string = open('output string.txt', 'w')
output_string.write(coded_blueprint_string)

timing_file.write('String writing in ' + repr(time.time() - start_time) + '\n')
