# CS180 (CS280A): Project 1

import numpy as np
import skimage as sk
import skimage.io as skio
import matplotlib.pyplot as plt

DATA_DIR = 'data/'
OUTPUT_DIR = 'output/'

# name of the input file
imname = DATA_DIR + 'cathedral.jpg'

# read in the image
im = skio.imread(imname)
plt.imshow(im)

print(im.dtype) # dtype: unit8

# convert to double (might want to do this later on to save memory)    
im = sk.img_as_float(im)

print(im.dtype) # dtype: float64
    
# compute the height of each part (just 1/3 of total)
# NOTE: need to use uint64 because uint8 is [0, 255] and any value
height = np.floor(im.shape[0] / 3.0).astype(np.uint64)

# separate color channels
# NOTE: each glass plate image in the data folder is in BGR order
b = im[:height]
g = im[height: 2*height]
r = im[2*height: 3*height]

# align the images
# functions that might be useful for aligning the images include:
# np.roll, np.sum, sk.transform.rescale (for multiscale)

def align(img, target_img):
    """
    align img to the target_img
    """
    return img # placeholder

ag = align(g, b)
ar = align(r, b)
# create a color image
im_out = np.dstack([ar, ag, b])

# save the image
fname = OUTPUT_DIR + 'out_fname.jpg'
skio.imsave(fname, im_out)

# display the image
plt.imshow(im_out)
plt.show()