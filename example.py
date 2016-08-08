# LHE Codec
# Author: Eduardo Rodes Pastor

import math, struct, os, sys
import PIL
from numpy import zeros
from array import *
from LHEquantizer import *
from binary_enc import *
from binary_dec import *
from image_dec import *
from Auxiliary.psnr import *

# ------------------------#
# CODING/DECODING EXAMPLE #
# ------------------------#

if __name__=='__main__':

	# User can write enc for encoding, dec for decoding and exit for...exiting.
	function = "none"
	
	# SELECT FUNCTION #
	while (function != "enc" and function != "dec" and function != "exit"):
		print ""
		function = raw_input("Select the function. Please, type enc for encoding, dec for decoding or exit if you want to close the program: ")

	if function == "enc":
		# -------- Main function for encoding --------- #

		mode = -1 # Default, user needs to select one

		# SELECT CHROMINANCE MODE #
		while (mode < 0 or mode > 2):
			try:
				print ""
				mode = int(raw_input("Select the chrominance mode. Please, type 0 for 4:2:0, 1 for 4:2:2 and 2 for 4:4:4: ")) # Select mode -> 0 is 4:2:0, 1 is 4:2:2 and 2 is 4:4:4
			except:
				mode = -1 # So we can keep asking the user until we get a valid value

		valid_image = "false" # Image needs to be in the input_img folder and have .bmp format

		# SELECT IMAGE #
		while (valid_image == "false"):
			# We get the image by giving the path and select a chrominance mode
			print ""
			image = raw_input("Select the image. Please, type the name (without extension) of the .bmp image you want to encode. It must be in the input_img folder: ")
			using = "input_img/" + image + ".bmp" # This is for testing only

			try:
				# We get the width, height and number of pixels of the image
				width, height, npix = getImageData(using)
				valid_image = "true"
				print ""
			except:
				print ""
				print "ERROR: Image does not exist or it is not saved in the input_img folder."
				valid_image = "false"

		# Getting YUV values
		r, g, b = getRGB(using, npix)
		y, cb, cr = RGBtoYUV(r, g, b)
		
		# We get the hops based on the YUV values
		y_hops, y_pred = getHops(y, cb, cr, "y", using, mode, npix)
		cb_hops, cb_pred = getHops(y, cb, cr, "cb", using, mode, npix)
		cr_hops, cr_pred= getHops(y, cb, cr, "cr", using, mode, npix)
		
		# We get the image PSNR
		calculatePSNR(y_pred, y, npix)
		print ""

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
		
		valid_lhe_file = "false" # .lhe file needs to exist and be in the output_lhe folder 

		# GETTING LHE FILE #
		while (valid_lhe_file == "false"):
			try:
				# With that file, we get the chrominance mode, size values, first value of every YUV list
				# and the length of the codified luminance values, so we can separate them from chrominance
				mode, width, height, first_lum, first_cb, first_cr, lum_len = getData(lhe_file)
				valid_lhe_file = "true"
			except:
				print ""
				print "ERROR: .lhe file does not exist or it is not saved in the output_lhe folder. Exiting..."
				print ""
				valid_lhe_file = "false"
				sys.exit(0)


		# We need the tuple for saving the image, and the number of pixels for the following function
		size = (width, height)
		npix = width * height

		# We get the chrominance and/or luminance symbols
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

	elif function == "exit":
		sys.exit(1)

