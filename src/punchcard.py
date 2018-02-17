# This file is under public domain, NOT covered by git-quality license
# Note:
# Originally written by guanqun (https://github.com/guanqun/) Sep 29, 2011
# Edited by Intrepid (https://github.com/intrepid/) Apr 12, 2012

import math
import numpy as np

import cairocffi as cairo


def plot_punchcard(width, height, dates):
    
    def get_x_y_from_date(day, hour):
        y = top + (days.index(day) + 1) * distance
        x = left + (hour + 1) * distance
        return x, y

    opaque = -1
    
    # Calculate the relative distance
    distance = int(math.sqrt((width*height)/270.5))
    
    # Round the distance to a number divisible by 2
    if distance % 2 == 1:
        distance -= 1
    
    max_range = (distance/2) ** 2
    
    # Good values for the relative position
    left = width/18 + 10  # The '+ 10' is to prevent text from overlapping 
    top = height/20 + 10
    indicator_length = height/20
    
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    hours = ['12am'] + [str(x) for x in range(1, 12)] + ['12pm'] + [str(x) for x in range(1, 12)]

    stats = {}
    for day_idx, d in enumerate(days):
        stats[d] = {}
        for h in range(5, 29):
            stats[d][h] = np.sum(np.logical_and(dates.dayofweek == day_idx, dates.hour == h))
            if np.isnan(stats[d][h]):
                stats[d][h] = np.sum = 0

    days = [days[-1]] + days[:-1]

    def get_length(nr):
        if nr == 0:
            return 0
        for i in range(1, int(distance/2)):
            if i*i <= nr and nr < (i+1)*(i+1):
                return i
        if nr == max_range:
            return distance/2-1
    
    # normalize
    all_values = []
    for d, hour_pair in stats.items():
        for h, value in hour_pair.items():
            all_values.append(value)
    max_value = 1 + max(all_values)
    final_data = []
    for d, hour_pair in stats.items():
        for h, value in hour_pair.items():
            final_data.append( [ get_length(int( float(stats[d][h]) / max_value * max_range )), get_x_y_from_date(d, h) ] )
    
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)
    
    cr.set_line_width (1)
    
    # draw background to bgcolor
    cr.set_source_rgb(250/255., 250/255., 250/255.)
    cr.rectangle(left, top, 25 * distance, 8 * distance)
    cr.fill()
    
    # set font color
    cr.set_source_rgb(33/255., 33/255., 33/255.)
    
    # draw x-axis and y-axis
    cr.move_to(left, top)
    cr.rel_line_to(0, 8 * distance)
    cr.rel_line_to(25 * distance, 0)
    cr.stroke()
    
    # draw indicators on x-axis and y-axis
    x, y = left, top
    for i in range(8):
        cr.move_to(x, y)
        cr.rel_line_to(-indicator_length, 0)
        cr.stroke()
        y += distance
    
    x += distance
    for i in range(25):
        cr.move_to(x, y)
        cr.rel_line_to(0, indicator_length)
        cr.stroke()
        x += distance
    
    # select font
    cr.select_font_face ('sans-serif', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    
    # and set a appropriate font size
    cr.set_font_size(math.sqrt((width*height)/3055.6))
    
    # draw Mon, Sat, ... Sun on y-axis
    x, y = (left - 5), (top + distance)
    for i in range(7):
        x_bearing, y_bearing, width, height, x_advance, y_advance = cr.text_extents(days[i])
        cr.move_to(x - indicator_length - width, y + height/2)
        cr.show_text(days[i])
        y += distance
    
    # draw 12am, 1, ... 11 on x-axis
    x, y = (left + distance), (top + (7 + 1) * distance + 5)
    for i in range(24):
        x_bearing, y_bearing, width, height, x_advance, y_advance = cr.text_extents(hours[i])
        cr.move_to(x - width/2 - x_bearing, y + indicator_length + height)
        cr.show_text(hours[i])
        x += distance

    cr.set_source_rgb(31 / 255., 119 / 255., 180 / 255.)
    # draw circles according to their frequency
    def draw_circle(pos, length):
        # find the position
        # max of length is half of the distance
        x, y = pos
        # clr = (1 - float(length * length) / max_range )
        # if opaque >= 0 and opaque < 1:
        #     clr = opaque
        cr.move_to(x, y)
        cr.arc(x, y, length, 0, 2 * math.pi)
        cr.fill()
    
    for each in final_data:
        draw_circle(each[1], each[0])
    
    return surface
