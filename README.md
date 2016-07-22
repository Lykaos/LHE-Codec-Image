# LHE-Codec



This is a python image coder-decoder using the LHE algorithm. It will codify chrominance and/or luminance hops, and will use Huffman coding to represent them as symbols.



## C project



You can check a more detailed project in C here: *https://github.com/magonzalezc/LHE*



## More info



You can learn more about LHE in this article: *http://oa.upm.es/37459/1/INVE_MEM_2014_200038.pdf*



## How to use

You will need the numpy module for Python. If you dont have it installed, type *sudo apt-get install python-numpy*.


Then just write in terminal *python example.py*. You will need to be in the folder where the example is.



### Encoding



Use example.py and change the function in the first line of the main method to enc (encoding). You will need an image in the input_img folder, and it will generate a .lhe file in the output_lhe folder.



### Decoding



Use example.py and change the function in the first line of the main method to dec (decoding). You will need a .lhe file in the output_lhe folder, and it will generate a .bmp image in the output_lhe/images subfolder.
