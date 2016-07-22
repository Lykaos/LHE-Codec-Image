# LHE Codec
# Author: Eduardo Rodes Pastor

import huff, math, struct, os
from PIL import Image
from array import *

# ---------------#
# BINARY DECODER #
# ---------------#

def getData(lhe_file): # Get all the data from an lhe_file

	fp = open(lhe_file, "rb")
	data = fp.read()
	i = 0 # Value to seek
	k = 0 # Value of the header array we will write
	header = [0] * 10 # We need 10 slots: lhe type, mode, width, height, 
					  # 2 for number of blocks, 3 for first values of pixels and 1 for the codified luminancy length
	while (i <= 18):
		fp.seek(i)
		if (i != 2 and i != 6 and i != 15): # If we aren't looking for width and height, just get 1 byte and unpack it
			data = fp.read(1)
			prueba = struct.unpack("B", data)[0]
			header[k] = prueba
			k = k + 1
			i = i + 1 # Seek 1 byte forward
		else:
			data = fp.read(4) # if we are looking for width and height, get 4 bytes and unpack them
			prueba = struct.unpack("I", data)[0]
			header[k] = prueba
			k = k + 1
			i = i + 4 # Seek 4 bytes forward

	return header[1], header[2], header[3], header[6], header[7], header[8], header[9] # We only need these values in this decoder

def getSymbolsLists(lhe_file, npix, lum_len, mode): # Given a .lhe file, get the symbols lists from codified luminance and chrominances
	
	y_sym = [0] * npix

	if (mode == 0):
		cb_sym = [0] * int(npix/4)
		cr_sym = [0] * int(npix/4)
	elif (mode == 1):
		cb_sym = [0] * int(npix/2)
		cr_sym = [0] * int(npix/2)

	with open(lhe_file, "rb", 0) as fp:
		fp.seek(19)
		data_lum = fp.read(lum_len)
		data_chrom = fp.read()
	fp.close()

	fp = open("output_lhe/out-huffman_lum.lhe", "wb")
	fp.write(data_lum)
	fp.close()
	fp = open("output_lhe/out-huffman_chrom.lhe", "wb")
	fp.write(data_chrom)
	fp.close()

	dec = huff.Decoder("output_lhe/out-huffman_lum.lhe")
	dec.decode_as("output_lhe/out-lum.lhe")

	dec = huff.Decoder("output_lhe/out-huffman_chrom.lhe")
	dec.decode_as("output_lhe/out-chrom.lhe")

	f = open("output_lhe/out-lum.lhe", "rb")
	lum_sym = f.read()
	f.close()
	f = open("output_lhe/out-chrom.lhe", "rb")
	chrom_sym = f.read()
	f.close()

	lum_sym = [w.replace('X', '11111111') for w in lum_sym]
	chrom_sym = [w.replace('X', '11111111') for w in chrom_sym]
	lum_sym = ''.join(lum_sym)
	chrom_sym = ''.join(chrom_sym)

	for i in range(0, npix):
		y_sym[i] = lum_sym[i]

	if (mode == 0):
		npix = int(npix/4)
	elif (mode == 1):
		npix = int(npix/2)

	cb_sym = [0] * npix
	cr_sym = [0] * npix 

	for i in range(0, npix):
			cb_sym[i] = chrom_sym[i]
			cr_sym[i] = chrom_sym[npix+i]

	return y_sym, cb_sym, cr_sym