from threading import Thread, Lock
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


def image_cropping(image):
    cropped_images = [Image.new('RGB', (1, 1)) for im in range(4)]
    cropping_ranges = [(0, 0, int(image.width / 2), int(image.height / 2)),
                       (int(image.width / 2), 0, image.width, int(image.height / 2)),
                       (0, int(image.height / 2), int(image.width / 2), image.height),
                       (int(image.width / 2), int(image.height / 2), image.width, image.height)]
    for k in range(4):
        cropped_images[k] = image.crop(cropping_ranges[k])
    return cropped_images


def image_processing(image, new_image, blueprint__, lockers, xy_shifts):
    global entity_numbers
    for x in range(image.width):
        for y in range(image.height):
            pixel_rgb = image.getpixel((x, y))
            new_pixel_rgb = nearest_color(entities | tiles, pixel_rgb)
            new_image.putpixel((x, y), new_pixel_rgb)
            if new_pixel_rgb in list(entities.keys()) and entities[new_pixel_rgb] != 'blank':
                with lockers[0]:
                    entity_numbers += 1
                    blueprint__.add_entity(entity_numbers, entities[new_pixel_rgb], [x + xy_shifts[0], y + xy_shifts[1]])
            elif new_pixel_rgb in list(tiles.keys()):
                with lockers[1]:
                    blueprint__.add_tile(tiles[new_pixel_rgb], [x + xy_shifts[0], y + xy_shifts[1]])

def nearest_color(colors, current_color):
    return min(colors, key=lambda subject: sum((s - q) ** 2 for s, q in zip(subject, current_color)))


def image_merging(images_to_merge, image):
    x, y = images_to_merge[0].size
    merged_image = Image.new('RGB', image.size)
    merged_image.paste(images_to_merge[0])
    merged_image.paste(images_to_merge[1], (x, 0))
    merged_image.paste(images_to_merge[2], (0, y))
    merged_image.paste(images_to_merge[3], (x, y))
    return merged_image


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


locker_list = [Lock() for lock in range(2)]
blueprint_ = Blueprint()
timing_file = open('timing_thread.txt', 'w')

timing_file.write('Initialization ends in ' + repr(time.time() - start_time) + '\n')
start_time = time.time()

img = Image.open('downsized.png')
new_img = Image.new('RGB', img.size)
cropped_img = image_cropping(img)
cropped_new_img = image_cropping(new_img)

timing_file.write('Image opening ends in ' + repr(time.time() - start_time) + '\n')
start_time = time.time()

xy_shift = [(0, 0),
            (int(img.width), 0),
            (0, int(img.height)),
            (int(img.width), int(img.height))]
entity_numbers = 0
thread_list = []

for i in range(4):
    thread = Thread(target=image_processing, args=(cropped_img[i], cropped_new_img[i], blueprint_, locker_list, xy_shift[i]))
    thread_list.append(thread)
    thread.start()

for thread in thread_list:
    thread.join()

timing_file.write('Image processing ends in ' + repr(time.time() - start_time) + '\n')
start_time = time.time()

new_img = image_merging(cropped_new_img, img)
new_img.save('colorized.png')
blueprint = {'blueprint': blueprint_}

timing_file.write('Image saving ends in ' + repr(time.time() - start_time) + '\n')
start_time = time.time()

json_data = json.dumps(blueprint, default=lambda o: o.__dict__, indent=4)
output_JSONfile = open('JSON output_threads.txt', 'w')
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
