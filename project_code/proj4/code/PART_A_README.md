# Deena's CS 180: Project 4 Part A - Image Warping and Mosaicing

```
├─code/
| |-data/               # images that I used/referenced in my notebooks
│ └─part_a_main.py      # my code for part A
│ └─PART_A_README.md    # you are here right now :)
│ └─requirements.txt    # dependencies required for part A
└─web/
  └─page.pdf        # PDF snapshot of my proj4 portfolio
```

## Website
All the images in my website can be viewed in higher-resolution/full-screen if you hover your mouse over them for about 1 second :)

## `part_a_main.py`

This file contains all of my code for project 4 part A!

`img_to_np` and `save_np_as_img` are helper functions for reading images from a filepath and converting them into NumPy arrays, or for saving NumPy arrays as images.

`make_2d_gaussian_kernel` is a helper function that creates a 2D Gaussian kernel (for blurring/low-pass filters).

`get_correspondences` uses brings up an interactive window with two images plotted side-by-side for manually selecting correspondences between two images. It takes in an argument specifying the number of correspondences users should click. Users should click on a point in image 1, then its paired point in image 2, and alternate back and forth. Users can press the `esc` key on their keyboard to undo the latest point selection. This function plots the selected points on the two images. It returns the selected points after the specified number of correspondences have been chosen.

`computeH` computes the homography matrix that transforms image 1 into image 2's projective plane. This function creates a system of equations and solves for a flattened vector representing the matrix H using least squares!

`normalize` is a helper function that normalizes 3D homogeneous coordinates so that its last coordinate is 1. It works on a single 3D homogeneous vector or a batch of homogeneous coordinates.

`warpImageNearestNeighbor` and `warpImageBilinear` use nearest neighbor and bilinear interpolation to warp an image given a homography H. Both interpolation methods use inverse interpolation.

`rectify` rectifies an image by transforming it such that a skewed subject inside the image that is a rectangle with right angles + parallel sides in real life is warped back into having right angles + parallel sides.

`get_warped_corners` is a helper function that computes the pixel positions of the 4 corners of an image after applying a given homography H.

`gaussian_stack` and `laplacian_stack` are functions from project 2 that create a Gaussian stack or Laplacian stack of a given image.

`make_mosaic` runs the full end-to-end pipeline for stitching together a list of input images into a photo mosaic.

The `main` function inside this file is set up so that it runs all the code needed to produce the deliverables for project 4 part A (besides shooting the pictures in part A.1 — the pictures I shot can be found under `data/` :)).

## Images inside `data/`

My code and portfolio for project 4 part A uses the following image files, and expects them to be located under `data/`:
- `campus_1.jpg`
- `campus_2.jpg`
- `campus_3.jpg`
- `campus_4.jpg`
- `campus_5.jpg`
- `gec_1.jpg`
- `gec_2.jpg`
- `gec_3.jpg`
- `kresge_1.jpg`
- `kresge_2.jpg`
- `kresge_3.jpg`
- `kresge_4.jpg`
- `kresge_5.jpg`
-`painting.jpg`
-`pompeii.jpg`
-`wall_fresco.jpg`

## How to run my code for project 4 part A

Create a python virtual environment and install the dependencies from `requirements.txt`.

From inside the `code` directory, run `python part_a_main.py`. The `main` function will run the necessary functions to produce the deliverables for project 4 part A. Each subpart's code is separated with a comment labelling which subpart (A.2, A.3, A.4) it is for.

Many of the subparts will display a matplotlib window with subplots of the images/results. To unblock the code and move onto the next subpart, you will need to close the matplotlib display. Note that the interactive window for selecting correspondences will automatically close after the expected number of correspondences are selected (closing this window manually will cause the function to return however many correspondences are selected so far).

Most of the functions will print out info statements in the terminal as they are called — you can use this to check progress!
