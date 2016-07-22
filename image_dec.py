# LHE Codec
# Author: Eduardo Rodes Pastor

import huff, math, struct, os
from PIL import Image
from numpy import zeros
from array import *

# --------------#
# IMAGE DECODER #
# --------------#

def initHopsCache(): # Initializes pre-computed hop values
	
	# This is a cache of ratio ("r") to avoid pow functions
	#float[][][][] cache_ratio  #meaning : [+/-][h1][h0][rmax]
	# we will compute cache ratio for different rmax values, although we will use 
	# finally only rmax=25 (which means 2.5f). This function is generic and experimental
	# and this is the cause to compute more things than needed.

	
	# h1 value belongs to [4..10]
	# Given a certain h1 value, and certaing h0 luminance, the "luminance hop" of hop "i" is stored here:
	# hn[absolute h1 value][luminance of h0 value]
	# for example,  h4 (null hop) is always 0, h1 is always hop1 (from 4 to 10), h2 is hop1*r,
	# however this is only the hop. the final luminance of h2 is luminace=(luminance of h0)+hop1*r    
	# hn is, therefore, the array of "hops" in terms of luminance but not the final luminances.
	# float[][] h0,h1,h2,h6,h7,h8 # h0,h1,h2 are negative hops. h6,h7,h8 are possitive hops
	
	h1range = 20 # in fact h1range is only from 4 to 10. However i am going to fill more possible values in the pre-computed hops
	
	h0 = zeros((h1range, 256))
	h1 = zeros((h1range, 256))
	h2 = zeros((h1range, 256))
	# in the center is located h3=h4-hop1, and h5=h4+hop1, but I dont need array for them
	h6 = zeros((h1range, 256))
	h7 = zeros((h1range, 256))
	h8 = zeros((h1range, 256)) 
	
	
	# pccr is the value of the REAL cache. This is the cache to be used in the LHE quantizer
	# sorry...i dont remenber why this cache is named "pccr" :) instead of "cache"
	# this array takes into account the ratio
	# meaning: pccr [h1][luminance][ratio][hop_index]
	pccr = zeros((h1range, 256, 50, 9)) 
	
	#cache of ratios ( to avoid Math.pow operation)
	#---------------------------------------------
	cache_ratio = zeros((2, h1range, 256, 50)) 
	
	
	for hop0 in range (0, 256):
		for hop1 in range (1, h1range):
			percent_range=0.8 # 80%
			
			#this bucle allows computations for different values of rmax from 20 to 40. 
			#however, finally only one value (25) is used in LHE
			for rmax in range (20, 41):
				# r values for possitive hops	
				cache_ratio[0][hop1][hop0][rmax] = pow(percent_range * (255-hop0)/(hop1), 0.33333333) 
				
				# r' values for negative hops
				cache_ratio[1][hop1][hop0][rmax] = pow(percent_range * (hop0)/(hop1), 0.3333333) 	
				
				# control of limits
				maximum = float(rmax)/10 # if rmax is 25 then max is 2.5f 
				if (cache_ratio[0][hop1][hop0][rmax] > maximum):
					cache_ratio[0][hop1][hop0][rmax] = maximum 
				if (cache_ratio[1][hop1][hop0][rmax] > maximum):
					cache_ratio[1][hop1][hop0][rmax] = maximum 
		#assignment of precomputed hop values, for each ofp value
		#--------------------------------------------------------
		for hop1 in range(1, h1range):

			#finally we will only use one value of rmax rmax=30, 
			#however we compute from r=2.0f (rmax=20) to r=4.0f (rmax=40)
			for rmax in range(20, 41):
		        #get r value for possitive hops from cache_ratio	
				ratio_pos = cache_ratio[0][hop1][hop0][rmax] 
				
				#get r' value for negative hops from cache_ratio
				ratio_neg = cache_ratio[1][hop1][hop0][rmax] 

				# COMPUTATION OF LUMINANCES:
				# luminance of possitive hops
				h6[hop1][hop0] = hop1 * ratio_pos 
				h7[hop1][hop0] = h6[hop1][hop0] * ratio_pos 
				h8[hop1][hop0] = h7[hop1][hop0] * ratio_pos 

				#luminance of negative hops	                        
				h2[hop1][hop0] =hop1 * ratio_neg 
				h1[hop1][hop0] = h2[hop1][hop0] * ratio_neg 
				h0[hop1][hop0] = h1[hop1][hop0] * ratio_neg 
			
				#final color component ( luminance or chrominance). depends on hop1
				#from most negative hop (pccr[hop1][hop0][0]) to most possitive hop (pccr[hop1][hop0][8])
				#--------------------------------------------------------------------------------------
				pccr[hop1][hop0][rmax][0] = hop0  - int(h0[hop1][hop0])
				if (pccr[hop1][hop0][rmax][0] <= 0):
					pccr[hop1][hop0][rmax][0] = 1
				pccr[hop1][hop0][rmax][1] = hop0  - int(h1[hop1][hop0])
				if (pccr[hop1][hop0][rmax][1] <= 0): 
					pccr[hop1][hop0][rmax][1] = 1
				pccr[hop1][hop0][rmax][2] = hop0  - int(h2[hop1][hop0])  
				if (pccr[hop1][hop0][rmax][2] <= 0):
					pccr[hop1][hop0][rmax][2] = 1
				pccr[hop1][hop0][rmax][3] = hop0 - hop1 
				if (pccr[hop1][hop0][rmax][3] <= 0):
					pccr[hop1][hop0][rmax][3] = 1 
				pccr[hop1][hop0][rmax][4] = hop0  # null hop
				
				#check of null hop value. This control is used in "LHE advanced", where value of zero is forbidden
				#in basic LHE there is no need for this control
				if (pccr[hop1][hop0][rmax][4] <= 0):
					pccr[hop1][hop0][rmax][4] = 1  # null hop
				if (pccr[hop1][hop0][rmax][4] > 255):
					pccr[hop1][hop0][rmax][4] = 255 # null hop
				
				pccr[hop1][hop0][rmax][5] = hop0+hop1 
				if (pccr[hop1][hop0][rmax][5] > 255):
					pccr[hop1][hop0][rmax][5] = 255 
				pccr[hop1][hop0][rmax][6] = hop0  + int(h6[hop1][hop0])
				if (pccr[hop1][hop0][rmax][6] > 255):
					pccr[hop1][hop0][rmax][6] = 255
				pccr[hop1][hop0][rmax][7] = hop0  + int(h7[hop1][hop0]) 
				if (pccr[hop1][hop0][rmax][7] > 255):
					pccr[hop1][hop0][rmax][7] = 255
				pccr[hop1][hop0][rmax][8] = hop0  + int(h8[hop1][hop0]) 
				if (pccr[hop1][hop0][rmax][8] > 255):
					pccr[hop1][hop0][rmax][8] = 255
	return pccr	

def symbolsToHops(sym_list, width, component, mode): # Given a list of symbols, return a list of the hops they represent

	sym_list = ['11111111' if e == 'X' else str(e) for e in sym_list]
	sym_list = ''.join(sym_list) # We get all the symbols in a big string

	k = 2 # Counter for getting the upper pixel
	hops = [0] * len(sym_list)

	distribution = [[4, 0, 5, 3, 6, 2, 7, 1, 8],
					[4, 1, 5, 3, 6, 2, 7, 8, 0],
					[4, 2, 5, 3, 6, 7, 1, 8, 0], # ...
					[4, 3, 5, 6, 2, 7, 1, 8, 0], # If upper hop = 3, symbol 1 is 4, symbol 2 is 3 (up) and so on
					[4, 5, 3, 6, 2, 7, 1, 8, 0],
					[4, 5, 3, 6, 2, 7, 1, 8, 0], # Distribution of hops if upper hop equals 1 or doesnt exist: 4 is sym '1', 5 is sym '2', etc. 
					[4, 6, 5, 3, 2, 7, 1, 8, 0], # If upper hop = 6, symbol 1 is 4, symbol 2 is 6 (up) and so on.						
					[4, 7, 5, 3, 6, 2, 1, 8, 0],
					[4, 8, 5, 3, 6, 2, 7, 1, 0]]

	for i in range(0, len(sym_list)):
		if (sym_list[i] == '1'):
			hops[i] = 4
			continue
		elif (i <= width-1):
			hops[i] = distribution[5][int(sym_list[i])-1] # Or distribution[4]... Both are ok.
			continue
		elif (sym_list[i] != '2'):
			hops[i] = distribution [int(hops[i-width])] [int(sym_list[i])-1]
			continue
		else:
			if (hops[i-width] != 4):
				try:
					hops[i] = hops[i-width]
				except:
					hops[i] = distribution[5][int(sym_list[i])-1]
			else:
				hops[i] = 5
			continue

	return hops
	
def hopsToYUV(hops, oc, width, height, component, mode): # Given a list of hops, return his YUV component list
	
	max_hop1 = 10 # hop1 interval 4..10
	min_hop1 = 4 # Minimum value of hop1 is 4 
	start_hop1 = (max_hop1+min_hop1)/2	

	hop1 = start_hop1
	hop0 = 0 # predicted luminance signal
	hop_number = 4 # pre-selected hop. 4 is NULL HOP
	pix = 0 # pixel possition, from 0 to image size        
	last_small_hop = "false" # indicates if last hop is small. Used for h1 adaptation mechanism
	rmax = 25

	npix = width * height # Total number of pixels in the image

	result = [-1] * npix 

	pccr = initHopsCache()	# y_hops = symbolsToHops(y_sym, width)

	x = 0 # Horizontal counter
	h = 0 # Vertical counter

	if (mode != 2 and component != "y"): # If we are in mode 4:2:2 or 4:2:0, we need to check every 2 pixels, so width is reduced to its half.
		width_adj = width/2
	else:
		width_adj = width


	while (h < height):
		while (x < width):

			try:
				hop_number = hops[pix]
			except:
				break

			if (h > 0 and x > 0 and x != width - 1 and x != width):
				hop0 = (4*result[pix-1]+3*result[pix + 1 - width_adj]) / 7 	

			elif (x == 0 and h > 0):
				hop0 = result[pix - width_adj] 
				last_small_hop = "false" 
				hop1 = start_hop1 

			elif ((x == width - 1 or x == width) and h > 0):
				hop0 = (4*result[pix-1]+2*result[pix- width_adj])/6 

			elif (h == 0 and x > 0):
				hop0 = result[pix-1]

			elif (x == 0 and h == 0):
				hop0 = oc # first pixel is always perfectly predicted 	

			result[pix] = pccr[hop1][hop0][rmax][hop_number] # Final luminance/chrominance
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

			if (mode != 2 and component != "y"): # If we are in 4:2:2 or 4:2:0, we need to check every 2 pixels in a row.
				x = x + 2
			else:
				x = x + 1 # Otherwise, we go normal

		x = 0 # This resets the horizontal counter

		if (mode == 0 and component != "y"): # If we are in 4:2:0, we need to check pixels every 2 rows.
			h = h + 2
		else:
			h = h + 1 # Otherwise, we go normal

	for i in range(0, len(result)):
		result[i] = int(result[i]) # We give the array result a more readable format

	# Here, we'll duplicate values of the chrominance lists if we are in 4:2:2 or 4:2:0, so they have the same length as the luminance list.
	if (mode != 2 and component != "y"):
		result = [x for x in result if x != -1] # We remove all non-used slots in the list
		result = [x for x in result for _ in (0, 1)] # We duplicate every element, so we get the same chrominance in 2 consecutive elements.
		if (mode == 0):
			i = 0
			len_res = 2*len(result) # Remember len(result) is half the value of the luminance list length

			# This whole bucle copies every line of values in the image to the row below, so we get a 4:2:0 mode.
			while (i < len_res):
				result_width = result[i:i+width] # We get a new lane
				i = i + width
				for j in range(0, width): # We insert that lane in a new one below the original
					result.insert(i, result_width[j])
					i = i + 1

	return result 

def YUVtoRGB(y, cb, cr):

	r = [0] * len(y)
	g = [0] * len(y)
	b = [0] * len(y)
	result = [0] * len(y)

	for i in range(0, len(y)):
		r[i] = int(y[i] + 1.4075 * (cr[i]-128))
		g[i] = int(y[i] - .3455 * (cb[i]-128) - .7169 * (cr[i]-128))
		b[i] = int(y[i] + 1.779 * (cb[i]-128))
		result[i] = (r[i], g[i], b[i])

	return r, g, b, result

def RGBtoBMP(rgb, size):
	im = Image.new('RGB', size)
	im.putdata(rgb)

	im.save("output_lhe/images/output-image.bmp", 'BMP')