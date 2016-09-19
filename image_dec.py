"""

This module gets and saves the decoded image, given its symbols lists.

"""
# LHE Codec
# Author: Eduardo Rodes Pastor

import math, struct, os
from PIL import Image
from array import *
from numpy import zeros
from example import initHopsCache

# --------------#
# IMAGE DECODER #
# --------------#


#*******************************************************************************#
#	Function symbolsToHops: Given a list of symbols, this returns a list of the #
#	hops they represent. We will use a list of lists called distribution which  #
#	will work as a cache, since two symbols mean different hops based on their  #
#	upper symbol.                                                               #
#	Input: Symbols list, output image width, component symbols we want and      #
#	chrminance mode                                                             #
#	(it can be "y", "cr" or "cb"), chrominance mode and total number of pixels  #
#	Output: List of component hops                                              #
#*******************************************************************************#

def symbolsToHops(sym_list, width, component, mode): 
	"""Transforms a symbols list into its respective hops one.

	Parameters: symbols list (integers from 0 to 255), width and
	height of the image (integers), chrominance mode (integer, 
	0 for 4:2:0, 1 for 4:2:2 or 2 for 4:4:4)

	Exceptions: This function does not throw an exception.

	"""

	sym_list = ['11111111' if e == 'X' else str(e) for e in sym_list]
	sym_list = ''.join(sym_list) # We get all the symbols in a big string

	hops = [0] * len(sym_list)

	distribution = [[4, 0, 5, 3, 6, 2, 7, 1, 8], # If upper hop = 0, symbol 1 is 4, symbol 2 is 0 (up) and so on
					[4, 1, 5, 3, 6, 2, 7, 8, 0], # ...
					[4, 2, 5, 3, 6, 7, 1, 8, 0], 
					[4, 3, 5, 6, 2, 7, 1, 8, 0], 
					[4, 5, 3, 6, 2, 7, 1, 8, 0], # Distribution of hops if upper hop equals 1 or doesnt exist
					[4, 5, 3, 6, 2, 7, 1, 8, 0], # If upper hop = 5, we get the same list as before
					[4, 6, 5, 3, 2, 7, 1, 8, 0], # If upper hop = 6, symbol 1 is 4, symbol 2 is 6 (up) and so on.						
					[4, 7, 5, 3, 6, 2, 1, 8, 0], # ...
					[4, 8, 5, 3, 6, 2, 7, 1, 0]]

	# Hop calculation
	for i in range(0, len(sym_list)):

		# If symbol is 1, hop will always be 4.
		if (sym_list[i] == '1'):
			hops[i] = 4
			continue

		# If we are in the first row, upper symbol doesnt exist and we use distribution[4] (or [5])
		elif (i <= width-1):
			hops[i] = distribution[5][int(sym_list[i])-1]
			continue

		# If upper symbol is not 2, we get the cache (distribution) value
		elif (sym_list[i] != '2'):
			hops[i] = distribution [int(hops[i-width])] [int(sym_list[i])-1]
			continue

		# If upper hop is not 4, we check the upper hop of it, until we get a
		# different hop or we reach the first row
		else:
			if (hops[i-width] != 4):

				try:
					hops[i] = hops[i-width]

				# If upper hop doesn't exist, we use distribution[4] (or [5])
				except:
					hops[i] = distribution[5][int(sym_list[i])-1]

			# If symbol is 2 and upper symbol is 1, hop is always 5
			else:
				hops[i] = 5
			continue

	return hops


#*******************************************************************************#
#	Function hopsToYUV: This gets a specific YUV list given its hops list.      #
#   This method is similar to GetHops in LHEquantizer, since it's its inverse   #
#   function.                                                                   #
#	Input: component hops list, original color of the first pixel, width and    #
#   height of the resulting image, component YUV we want in return.             #
#	chrominance mode                                                            #
#	(it can be "y", "cr" or "cb"), chrominance mode and total number of pixels  #
#	Output: component hops []                                                   #
#*******************************************************************************#

def hopsToYUV(hops, oc, width, height, component, mode):
	"""Returns the y, cb and cr values (YUV) given their hops list.

	Parameters: hops list (integers from 0 to 8), first value of the 
	component we want in the first pixel (integer from 0 to 255), width and
	height of the image (integers), component we want to get data about
	(string), chrominance mode (integer, 0 for 4:2:0, 1 for 4:2:2 or 
	2 for 4:4:4).

	Exceptions: This function does not throw an exception.

	"""
	# Hop1 interval: [4,10]
	max_hop1 = 10
	min_hop1 = 4

	# We start in the center of the interval
	start_hop1 = (max_hop1 + min_hop1) / 2 
	hop1 = start_hop1

	hop0 = 0 # Predicted luminance signal
	hop_number = 4 # Pre-selected hop -> 4 is null hop
	pix = 0 # Pixel possition, from 0 to image size        
	last_small_hop = "false" # Indicates if last hop is small. Used for h1 adaptation mechanism
	rmax = 25 # Ratio used in LHE

	npix = width * height # Total number of pixels in the image
	result = [-1] * npix  # List where we will save the YUV component values

	cache = initHopsCache()	# Initializing hops cache

	x = 0 # Horizontal counter
	h = 0 # Vertical counter

	# If we are in mode 4:2:2 or 4:2:0, we need to check every 2 pixels, so width 
	# is reduced to its half.
	if (mode != 2 and component != "y"): 
		width_adj = width/2
	else:
		width_adj = width # Otherwise, we go normal

	while (h < height): # Output image height
		while (x < width): # Output image width

			try:
				hop_number = hops[pix]
			except:
				break # This prevents unwanted exceptions when using 4:2:2 and 4:2:0

			# HOP0 PREDICTION #
			# ------------------------------------------------------------------------------ #

			# If we are not in a border, we need the previous pixel and the upper-right one.
			if (h > 0 and x > 0 and x != width - 1 and x != width):
				hop0 = (4*result[pix-1]+3*result[pix + 1 - width_adj])/7 

			# If we are in the beginning of a row, we reset Hop1
			elif (x == 0 and h > 0):
				hop0 = result[pix- width_adj] 
				last_small_hop = "false" 
				hop1 = start_hop1 

			# If we are in the end of a row, we need the previous pixel and the upper one
			elif ((x == width - 1 or x == width) and h > 0): 
				hop0 = (4*result[pix-1]+2*result[pix- width_adj])/6 

			# If we are in the first row, the hop (from 0 to 256) will be the result of the previous pixel
			elif (h == 0 and x > 0):
				hop0 = result[pix-1] 

			# First pixel is always perfectly predicted 	
			elif (x == 0 and h == 0):
				hop0 = oc 

			# Assignment of final value
			result[pix] = cache[int(hop1)][int(hop0)][rmax][hop_number] # Final luminance/chrominance

			# Tunning hop1 for the next hop ("h1 adaptation")
			small_hop = "false" 
			if (hop_number <= 5 and hop_number >= 3): 
				small_hop = "true" # Hop 4 is in the center and is null.
			else:
				small_hop = "false"      

			if (small_hop == "true" and last_small_hop == "true"):
				hop1 = hop1-1 
				if (hop1 < min_hop1):
					hop1 = min_hop1 
			else:
				hop1 = max_hop1

			# Let's go for the next pixel
			last_small_hop = small_hop  
			pix = pix + 1

			# If we are in 4:2:2 or 4:2:0, we need to check every 2 pixels in a row.
			if (mode != 2 and component != "y"): 
				x = x + 2
			else:
				x = x + 1 # Otherwise, we go normal

		x = 0 # This resets the horizontal counter

		# If we are in 4:2:0, we need to check pixels every 2 rows.
		if (mode == 0 and component != "y"): 
			h = h + 2
		else:
			h = h + 1 # Otherwise, we go normal

	# We give the result list a more readable format
	for i in range(0, len(result)):
		result[i] = int(result[i]) 

	# Here, we will duplicate values of the chrominance lists if we are in 4:2:2 or 4:2:0, 
	# so they will have the same length as the luminance list.
	if (mode != 2 and component != "y"):
		result = [x for x in result if x != -1] # We remove all non-used slots in the list
		result = [x for x in result for _ in (0, 1)] # We duplicate every element, so we get the same chrominance in 2 consecutive elements.
		
		if (mode == 0):
			i = 0 # Reseting i
			len_res = 2*len(result) # Remember len(result) is half the value of the luminance list length

			# This whole bucle copies every line of values in the image to the row below, so we get a 4:2:0 mode.
			while (i < len_res):

				# We get a new line
				result_width = result[i:i+width] 
				i = i + width

				# We insert that lane in a new one below the original
				for j in range(0, width): 
					result.insert(i, result_width[j])
					i = i + 1

	return result 


#*******************************************************************#
#	Function YUVtoRGB: This converts three YUV lists (y, cb, cr)    #
#	in a tuple of their equivalent RGB lists.                       #
#	Input: y [], cb [], cr []                                       #
#	Output: rgb [] (tuple of r, g, b)                               #
#*******************************************************************#

def YUVtoRGB(y, cb, cr):
	"""Gets the RGB values from the YUV ones.

	Parameters: y, cb and cr (YUV lists, integers from 0 to 255).

	Exceptions: This function does not throw an exception.

	"""
	# All of these have the same length
	r = [0] * len(y)
	g = [0] * len(y)
	b = [0] * len(y)
	result = [0] * len(y)

	# This is just the formula to get RGB from YUV
	for i in range(0, len(y)):
		r[i] = int(y[i] + 1.4075 * (cr[i]-128))
		g[i] = int(y[i] - .3455 * (cb[i]-128) - .7169 * (cr[i]-128))
		b[i] = int(y[i] + 1.779 * (cb[i]-128))
		result[i] = (r[i], g[i], b[i]) # We need this for saving the image

	return result


#*******************************************************************#
#	Function RGBtoBMP: This gets and saves an image in .bmp format  #
#	based on the three lists RGB given                              #
#	Input: r [], g [], b []                                         #
#	Output: None, just saves the image in the output_lhe/images     #
#	subfolder                                                       #
#*******************************************************************#

def RGBtoBMP(rgb, size):
	"""Saves the new image in the specified subfolder given its RGB values.

	Parameters: R, G and B values (integer lists with values from 0 to 255),
	size of the image (integer)

	Exceptions: This function will throw an exception if the specified folder
	does not exist.

	"""
	# New image with our rgb values
	im = Image.new('RGB', size) 
	im.putdata(rgb)

	# We save it as output-image.bmp
	im.save("output_img/output-image.bmp", 'BMP')