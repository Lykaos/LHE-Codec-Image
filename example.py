# LHE Codec
# Author: Eduardo Rodes Pastor

import huff, math, struct, os
from Pillow import PIL
from numpy import zeros
from array import *
from LHEquantizer import *
from binary_enc import *
from binary_dec import *
from image_dec import *
from Aux.huff import *
from Aux.psnr import *

# ------------------------#
# CODING/DECODING EXAMPLE #
# ------------------------#

if __name__=='__main__':

	# Provisional: enc for encoding and dec for decoding
	function = "dec" 

	if function == "enc":
		# -------- Main function for encoding --------- #

		# We get the image by giving the path and select a chrominance mode
		image = "family"
		using = "input_img/" + image + ".jpg" # We will codify .bmp images, but this is for testing only
		mode = 0 # Select mode -> 0 is 4:2:0, 1 is 4:2:2 and 2 is 4:4:4

		# We get the width, height and number of pixels of the image
		width, height, npix = getImageData(using)

		# Getting YUV values
		r, g, b = getRGB(using, npix)
		y, cb, cr = RGBtoYUV(r, g, b)
		
		# We get the hops based on the YUV values

		y_hops, y_pred = getHops(y, cb, cr, "y", using, mode, npix)
		cb_hops, cb_pred = getHops(y, cb, cr, "cb", using, mode, npix)
		cr_hops, cr_pred= getHops(y, cb, cr, "cr", using, mode, npix)

		# We get the image PSNR
		calculatePSNR(y_pred, y, npix)

		# We transform hops into symbols
		y_sym, width, height = getSymbols(y_hops, width, height, npix)
		cb_sym, width, height = getSymbols(cb_hops, width, height, npix)
		cr_sym, width, height = getSymbols(cr_hops, width, height, npix)

		# We write the .lhe file, in the folder output_lhe
		writeFile(y_sym, cb_sym, cr_sym, mode, y[0], cb[0], cr[0], width, height)


	elif function == "dec":
		# -------- Main function for decoding --------- #

		# Getting the path of the .lhe file
		lhe_file = "output_lhe/lhe_file.lhe"
		
		# With that file, we get the chrominance mode, size values, first value of every YUV list
		# and the length of the codified luminance values, so we can separate them from chrominance
		mode, width, height, first_lum, first_cb, first_cr, lum_len = getData(lhe_file)

		# We need the tuple for saving the image, and the number of pixels for the following function
		size = (width, height)
		npix = width * height

		# # We get the chrominance and/or luminance symbols
		y_sym, cb_sym, cr_sym = getSymbolsLists(lhe_file, npix, lum_len, mode)

		# We get the hops represented by those symbols
		y_hops = symbolsToHops(y_sym, width, "y", mode)
		cb_hops = symbolsToHops(cb_sym, width, "cb", mode)
		cr_hops = symbolsToHops(cr_sym, width, "cr", mode)

		# We get the YUV values represented by those hops
		y_YUV = hopsToYUV(y_hops, first_lum, width, height, "y", mode)
		cb_YUV = hopsToYUV(cb_hops, first_cb, width, height, "cb", mode)
		cr_YUV = hopsToYUV(cr_hops, first_cr, width, height, "cr", mode)

		# We transform YUV into the tuple RGB
		rgb = YUVtoRGB(y_YUV, cb_YUV, cr_YUV)

		# Saving the rgb image to .bmp
		RGBtoBMP(rgb, size)