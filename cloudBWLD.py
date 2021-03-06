import sys
from collections import Counter
import re
from pytagcloud.lang.stopwords import StopWords
from operator import itemgetter
from copy import copy
from math import sin, cos, ceil
from pygame import transform, font, mask, Surface, Rect, SRCALPHA, draw
from pygame.sprite import Group, Sprite, collide_mask
from random import randint, choice
import colorsys
import math
import os
import pygame
import simplejson

TAG_PADDING = 5
STEP_SIZE = 2 # relative to base step size of each spiral function
RADIUS = 1
ECCENTRICITY = 1.5

LOWER_START = 0.45
UPPER_START = 0.55

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
DEFAULT_FONT = 'Droid Sans'
DEFAULT_PALETTE = 'default'
FONT_CACHE = simplejson.load(open(os.path.join(FONT_DIR, 'fonts.json'), 'r'))

pygame.init()
convsurf = Surface((2 * TAG_PADDING, 2 * TAG_PADDING))
convsurf.fill((255, 0, 255))
convsurf.set_colorkey((255, 0, 255))
draw.circle(convsurf, (0, 0, 0), (TAG_PADDING, TAG_PADDING), TAG_PADDING)
CONVMASK = mask.from_surface(convsurf)

LAYOUT_HORIZONTAL = 0
LAYOUT_VERTICAL = 1
LAYOUT_MOST_HORIZONTAL = 2
LAYOUT_MOST_VERTICAL = 3
LAYOUT_MIX = 4

LAYOUTS = (
           LAYOUT_HORIZONTAL,
           LAYOUT_VERTICAL,
           LAYOUT_MOST_HORIZONTAL,
           LAYOUT_MOST_VERTICAL,
           LAYOUT_MIX
           )

LAST_COLLISON_HIT = None

class Tag(Sprite):
    """
    Font tag sprite. Blit the font to a surface to correct the font padding
    """
    def __init__(self, tag, initial_position, fontname=DEFAULT_FONT):
        Sprite.__init__(self)
        self.tag = copy(tag)
        self.rotation = 0
        
        self.font_spec = load_font(fontname)
        self.font = font.Font(os.path.join(FONT_DIR,
                                           self.font_spec['ttf']),
                                           self.tag['size'])
        fonter = self.font.render(tag['tag'], True, tag['color'])
        frect = fonter.get_bounding_rect()
        frect.x = -frect.x
        frect.y = -frect.y
        self.fontoffset = (-frect.x, -frect.y)
        font_sf = Surface((frect.width, frect.height), pygame.SRCALPHA, 32)
        font_sf.blit(fonter, frect)
        self.image = font_sf
        self.rect = font_sf.get_rect()
        self.rect.width += TAG_PADDING
        self.rect.height += TAG_PADDING
        self.rect.x = initial_position[0]
        self.rect.y = initial_position[1]
        self._update_mask()
        
    def _update_mask(self):
        self.mask = mask.from_surface(self.image)
        self.mask = self.mask.convolve(CONVMASK, None, (TAG_PADDING, TAG_PADDING))

    def flip(self):        
        angle = 90 if self.rotation == 0 else - 90
        self.rotate(angle)
        
    def rotate(self, angle):
        pos = (self.rect.x, self.rect.y)
        self.image = transform.rotate(self.image, angle)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos
        self._update_mask()
        
    def update_fontsize(self):
        self.font = font.Font(os.path.join(FONT_DIR, self.font_spec['ttf']),
                              self.tag['size'])
        
def load_font(name):
    for font in FONT_CACHE:
        if font['name'] == name:
            return font
    raise AttributeError('Invalid font name. Should be one of %s' % 
                         ", ".join([f['name'] for f in FONT_CACHE]))

def defscale(count, mincount, maxcount, minsize, maxsize):
	if maxcount == mincount:
		return int((maxsize - minsize) / 2.0 + minsize)
	return int(minsize + (maxsize - minsize) * (count * 1.0 / (maxcount - mincount)) ** 0.8)

def make_tags(wordcounts, minsize=3, maxsize=36, colors=None, scalef=defscale):
    """
    sizes and colors tags 
    wordcounts is a list of tuples(tags, count). (e.g. how often the
    word appears in a text)
    the tags are assigned sizes between minsize and maxsize, the function used
    is determined by scalef (default: square root)
    color is either chosen from colors (list of rgb tuples) if provided or random
    """
    counts = [tag[1] for tag in wordcounts]
    
    if not len(counts):
        return []

    maxcount = abs(max(counts))
    mincount = abs(min(counts))
    if mincount > maxcount:
    	temp = maxcount
    	maxcount = mincount
    	mincount = temp
    tags = []
    for word_count in wordcounts:
        if word_count[1] > 0:
            color = (255,0,0)
            tags.append({'color': color, 'size': scalef(word_count[1], mincount,
                                                    maxcount, minsize, maxsize),
                     'tag': word_count[0]})
        else:
            color = (0,255,0)
            tags.append({'color': color, 'size': scalef(abs(word_count[1]), mincount,
                                                    maxcount, minsize, maxsize),
                     'tag': word_count[0]})
    return tags

def createCounter(filename):
	words = Counter()
	for w in filename:
		w = w.lower()
		for e in w:
			w = ''.join(e for e in w if (e.isalnum() or e == "'"))
		words[w] += 1
	return words

def get_tag_counts(text1, text2):
    """
    Search tags in a given text. The language detection is based on stop lists.
    This implementation is inspired by https://github.com/jdf/cue.language. Thanks Jonathan Feinberg.
    """
    words1 = map(lambda x:x.lower(), re.findall(r'\w+', text1, re.UNICODE))
    words2 = map(lambda x:x.lower(), re.findall(r'\w+', text2, re.UNICODE))
    
    s = StopWords()     
    s.load_language(s.guess(words1))
    s.load_language(s.guess(words2))
    
    counted = {}
    
    for word in words1:
        if not s.is_stop_word(word) and len(word) > 1:
            if counted.has_key(word):
                counted[word] += 1
            else: 
                counted[word] = 1

    for word in words2:
        if not s.is_stop_word(word) and len(word) > 1:
            if counted.has_key(word):
                counted[word] -= 1
            else: 
                counted[word] = -1
      
    return sorted(counted.iteritems(), key=itemgetter(1), reverse=True)

def _do_collide(sprite, group):
    """
    Use mask based collision detection
    """
    global LAST_COLLISON_HIT
    # Test if we still collide with the last hit
    if LAST_COLLISON_HIT and collide_mask(sprite, LAST_COLLISON_HIT):
        return True
    
    for sp in group:
        if collide_mask(sprite, sp):
            LAST_COLLISON_HIT = sp
            return True
    return False

def _get_tags_bounding(tag_store):
    if not len(tag_store):
        return Rect(0,0,0,0)
    rects = [tag.rect for tag in tag_store]
    return rects[0].unionall(rects[1:])
        
def _get_group_bounding(tag_store, sizeRect):
    if not isinstance(sizeRect, pygame.Rect):
        sizeRect = Rect(0, 0, sizeRect[0], sizeRect[1])
    if tag_store:
        rects = [tag.rect for tag in tag_store]
        union = rects[0].unionall(rects[1:])
        if sizeRect.contains(union):
            return union
    return sizeRect

def _archimedean_spiral(reverse):
    DEFAULT_STEP = 0.05 # radians
    t = 0
    r = 1
    if reverse:
        r = -1
    while True:
        t += DEFAULT_STEP * STEP_SIZE * r
        yield (ECCENTRICITY * RADIUS * t * cos(t), RADIUS * t * sin(t))

def _rectangular_spiral(reverse):
    DEFAULT_STEP = 3 # px
    directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    if reverse:
        directions.reverse()
    direction = directions[0]

    spl = 1
    dx = dy = 0
    while True:
        for step in range(spl * 2):
            if step == spl:
                direction = directions[(spl - 1) % 4]
            dx += direction[0] * STEP_SIZE * DEFAULT_STEP
            dy += direction[1] * STEP_SIZE * DEFAULT_STEP
            yield dx, dy
        spl += 1

def _search_place(current_tag, tag_store, canvas, spiral, ratio):
    """
    Start a spiral search with random direction.
    Resize the canvas if the spiral exceeds the bounding rectangle
    """

    reverse = choice((0, 1))
    start_x = current_tag.rect.x
    start_y = current_tag.rect.y
    min_dist = None
    opt_x = opt_y = 0
    
    current_bounding = _get_tags_bounding(tag_store)
    cx = current_bounding.w / 2.0
    cy = current_bounding.h / 2.0

    for dx, dy in spiral(reverse):
        current_tag.rect.x = start_x + dx
        current_tag.rect.y = start_y + dy
        if not _do_collide(current_tag, tag_store):
            if canvas.contains(current_tag.rect):
                tag_store.add(current_tag)
                return
            else:
                # get the distance from center                
                current_dist = (abs(cx - current_tag.rect.x) ** 2 + 
                                abs(cy - current_tag.rect.y) ** 2) ** 0.5      
                if not min_dist or current_dist < min_dist:
                    opt_x = current_tag.rect.x
                    opt_y = current_tag.rect.y 
                    min_dist = current_dist
                
                # only add tag if the spiral covered the canvas boundaries
                if abs(dx) > canvas.width / 2.0 and abs(dy) > canvas.height / 2.0:
                    current_tag.rect.x = opt_x                    
                    current_tag.rect.y = opt_y                    
                    tag_store.add(current_tag)
                    
                    new_bounding = current_bounding.union(current_tag.rect)
                    
                    delta_x = delta_y = 0.0
                    if new_bounding.w > canvas.width:
                        delta_x = new_bounding.w - canvas.width
                        
                        canvas.width = new_bounding.w
                        delta_y = ratio * new_bounding.w - canvas.height
                        canvas.height = ratio * new_bounding.w                                        
                        
                    if new_bounding.h > canvas.height:                        
                        delta_y = new_bounding.h - canvas.height
                        
                        canvas.height = new_bounding.h
                        canvas.width = new_bounding.h / ratio
                        delta_x = canvas.width - canvas.width
                    
                    # realign
                    for tag in tag_store:
                        tag.rect.x += delta_x / 2.0
                        tag.rect.y += delta_y / 2.0
                    
                    
                    canvas = _get_tags_bounding(tag_store)
                               
                    return  

def _draw_cloud(
        tag_list,
        layout=LAYOUT_MIX,
        size=(500,500),
        fontname=DEFAULT_FONT,
        rectangular=False):
    
    # sort the tags by size and word length
    tag_list.sort(key=lambda tag: len(tag['tag']))
    tag_list.sort(key=lambda tag: tag['size'])
    tag_list.reverse()

    # create the tag space
    tag_sprites = []
    area = 0
    for tag in tag_list:
        tag_sprite = Tag(tag, (0, 0), fontname=fontname)
        area += tag_sprite.mask.count()
        tag_sprites.append(tag_sprite)
    
    canvas = Rect(0, 0, 0, 0)
    ratio = float(size[1]) / size[0]
    
    if rectangular:
        spiral = _rectangular_spiral
    else:
        spiral = _archimedean_spiral
        
    aligned_tags = Group()
    for tag_sprite in tag_sprites:
        angle = 0
        if layout == LAYOUT_MIX and randint(0, 2) == 0:
            angle = 90
        elif layout == LAYOUT_VERTICAL:
            angle = 90
        
        tag_sprite.rotate(angle)

        xpos = canvas.width - tag_sprite.rect.width
        if xpos < 0: xpos = 0
        xpos = randint(int(xpos * LOWER_START) , int(xpos * UPPER_START))
        tag_sprite.rect.x = xpos

        ypos = canvas.height - tag_sprite.rect.height
        if ypos < 0: ypos = 0
        ypos = randint(int(ypos * LOWER_START), int(ypos * UPPER_START))
        tag_sprite.rect.y = ypos

        _search_place(tag_sprite, aligned_tags, canvas, spiral, ratio)            
    canvas = _get_tags_bounding(aligned_tags)
    
    # resize cloud
    zoom = min(float(size[0]) / canvas.w, float(size[1]) / canvas.h)
    
    for tag in aligned_tags:
        tag.rect.x *= zoom
        tag.rect.y *= zoom
        tag.rect.width *= zoom
        tag.rect.height *= zoom
        tag.tag['size'] = int(tag.tag['size'] * zoom)
        tag.update_fontsize() 
    
    canvas = _get_tags_bounding(aligned_tags)
    
    return canvas, aligned_tags

def create_tag_image(
        tags, 
        output, 
        size=(900,900), 
        background=(255, 255, 255), 
        layout=LAYOUT_MIX, 
        fontname=DEFAULT_FONT,
        rectangular=False):
    """
    Create a png tag cloud image
    """
    
    if not len(tags):
        return
    
    sizeRect, tag_store = _draw_cloud(tags,
                                      layout,
                                      size=size, 
                                      fontname=fontname,
                                      rectangular=rectangular)
    
    image_surface = Surface((sizeRect.w, sizeRect.h), SRCALPHA, 32)
    image_surface.fill(background)
    for tag in tag_store:
        image_surface.blit(tag.image, tag.rect)
    pygame.image.save(image_surface, output)

def create_html_data(tags, 
        size=(500,500), 
        layout=LAYOUT_MIX, 
        fontname=DEFAULT_FONT,
        rectangular=False):
    """
    Create data structures to be used for HTML tag clouds.
    """
    
    if not len(tags):
        return
    
    sizeRect, tag_store = _draw_cloud(tags,
                                      layout,
                                      size=size, 
                                      fontname=fontname,
                                      rectangular=rectangular)
    
    tag_store = sorted(tag_store, key=lambda tag: tag.tag['size'])
    tag_store.reverse()
    data = {
            'css': {},
            'links': []
            }
    
    color_map = {}
    for color_index, tag in enumerate(tags):
        if not color_map.has_key(tag['color']):
            color_name = "c%d" % color_index
            hslcolor = colorsys.rgb_to_hls(tag['color'][0] / 255.0, 
                                           tag['color'][1] / 255.0, 
                                           tag['color'][2] / 255.0)
            lighter = hslcolor[1] * 1.4
            if lighter > 1: lighter = 1
            light = colorsys.hls_to_rgb(hslcolor[0], lighter, hslcolor[2])
            data['css'][color_name] = ('#%02x%02x%02x' % tag['color'], 
                                       '#%02x%02x%02x' % (light[0] * 255,
                                                          light[1] * 255,
                                                          light[2] * 255))
            color_map[tag['color']] = color_name

    for stag in tag_store:
        line_offset = 0
        
        line_offset = stag.font.get_linesize() - (stag.font.get_ascent() +  abs(stag.font.get_descent()) - stag.rect.height) - 4
        
        tag = {
               'tag': stag.tag['tag'],
               'cls': color_map[stag.tag['color']],
               'top': stag.rect.y - sizeRect.y,
               'left': stag.rect.x - sizeRect.x,
               'size': int(stag.tag['size'] * 0.85),
               'height': int(stag.rect.height * 1.19) + 4,
               'width': stag.rect.width,
               'lh': line_offset
               }
        
        data['links'].append(tag)
        data['size'] = (sizeRect.w, sizeRect.h * 1.15)
            
    return data


if __name__ == '__main__':
    # if len(sys.argv) != 3:
    #     print('usage: %s <doc1> <doc2>')
    #     sys.exit(1)
    # else:
	file1 = "In spite of these challenges, we felt it was critical to continue to make long-term investments in our infrastructure and our guest experience service model as we believe these efforts will further differentiate our brand. Our new model is established in about 100 company-owned restaurants and it helps create a personal customized experience for our guests. While we are confident this service strategy builds incremental sales, we did experience higher labor costs in the fourth quarter. We are continuing to refine this model to make it scalable before we proceed with system-wide rollouts."
	file2 = "In the third quarter, we made investments in our future as we upgraded our technology infrastructure, continued our international expansion, and worked towards purchasing additional franchise locations. We had successful marketing campaigns in the third quarter. The Summer Olympics provided opportunities for friends to gather in our restaurants and cheer our athletes onto the gold. On the heels of the closing ceremony, we shifted our focus to the gridiron and more football fanatics filled our restaurants for our annual Fantasy Football draft promotions than ever before."	
	file1 = file1.split()
	file2 = file2.split()
	# file1 = readFile(sys.argv[1])
	# file2 = readFile(sys.argv[2])
	words1 = createCounter(file1)
	words2 = createCounter(file2)
	text = {}
	for word in words1:
		if word in words2:
			difference  = words1[word] - words2[word]
			text[word] = difference
		else:
			count = words1[word]
			text[word] = count
	for word in words2:
		if word not in words1:
			count = words2[word]
			text[word] = count*(-1)
	string1 = ""
	string2 = ""
	for w in text:
		if text[w] > 0:
			for j in range(0, text[w]):
				string1 += (w + " ")
		else:
			for j in range(text[w], 0):
				string2 += (w + " ")
	tags = make_tags(get_tag_counts(string1, string2), maxsize = 40)
	create_tag_image(tags, 'BWLDcloud.png', size=(1200, 900), fontname='Droid Sans')
	import webbrowser
	webbrowser.open('BWLDcloud.png')