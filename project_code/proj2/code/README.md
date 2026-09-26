# Deena's CS 180: Project 2 - Fun with Filters and Frequencies!

```
├─code/
| |-data/           # input dir containing images (DATA_DIR)
| |-out/            # output dir where result will be saved (OUTPUT_DIR)
│ ├─main.py         # implementations for all project parts
│ ├─align_image_code.py         # helper alignment functions for creating hybrid images
| |-requirements.txt
│ └─README.md      # you are here right now :)
└─web/
  └─page.pdf        # PDF snapshot of my proj2 portfolio
```

## The most important thing I learned from project 2...
Anything can be a signal, even images! By thinking of images as signals, we can decompose them into different features. Also, convolutions are awesome.

## Website
All the images in my website can be viewed in higher-resolution/full-screen if you hover your mouse over them for about 1 second :)

## `main.py`

`main.py` contains all the code I wrote for project 2. 

The constants `DATA_DIR` and `OUTPUT_DIR` defined at the top of `main.py` are the default input/output folders the functions in this code will use.

`make_difference_and_box_filters`, `make_box_filter`, `make_2d_gaussian_kernel`, and `make_sharpening_filter` are helper functions I created to reuse throughout my functions whenever I needed to create one of these filters/kernels.

`save_hi_res_img` and `read_img_as_float` are helper functions I defined for saving images via `ski.io.imsave` and reading images + converting them into floating point NumPy arrays.

`crop_into_square` was another helper function I created to make sure crop an image into a square and keep the center region.

**Part 1.1: Convolutions from Scratch!**
`convolve_2d` is my custom implementation of a convolution. I included 2 implementations:
- A quadruple for-loop that first iterates through the output matrix dimensions, then iterates through the kernel.
- A double for-loop that iterates through the output matrix dimensions and uses vectorized operations to compute the dot-product between a flipped kernel and the input image window.

My DIY convolution flips the kernel before convolving. I also used `np.allclose` to verify that my convolution implementation produces the same result as `scipy.signal.convolve2d` within an absolute tolerance of `1e-8`!

**Part 1.2: Finite Difference Operator**
`finite_difference_operator`: convolves an input image with both Dx and Dy (cropping the input image into a square first if needed to ensure that the outputs of both convolutions are the same dimensions), calculates the magnitude of the gradient, then binarizes edges above a certain threshold. I kept the loop I used to try out different candidate thresholds for edge binarizing, but commented it out.

**Part 1.3: Derivative of Gaussian (DoG) Filter**
`derivative_of_gaussian_filter`: this compares the 2-step versus single-step DoG implementations — convolve an image with a Gaussian blurring kernel, then with either Dx or Dy, or convolve the image once with a derivative of a Gaussian. Similarly to part 1.2, I had to find the best binarized edge threshold via visual inspection. The loop I used to test and visualize different thresholds is still in `main.py` but commented out.

**Part 2.1: Image "Sharpening"**
`sharpen`: convolves each RGB channel of image with a sharpening filter, then stacks the color channels back together into a single sharpened image.

`sharpen_alpha_experiments`: calls `sharpen` with different alpha values and plots them for comparison.

`sharpen_then_blur_then_sharpen`: implements the task in part 2.1 that asks to take a sharp image, blur it, then re-sharpen it again.

**Part 2.2: Hybrid Images**
`hybrid_image`: extracts the high frequencies from img1 and the low frequencies from img2, then adds them together to produce a hybrid image. A viewer will percieve img1 from up close but img2 from far away. The low frequency image is made by convolving img2 with a Gaussian kernel. The high frequency image is made by convolving img1 with a Gaussian kernel, then subtracting the blurred version from img1.

`load_align_hybrid`: a helper function that implements the entire pipeline from creating a hybrid image. This function takes care of reading two images from their input file paths, uses `align_image_code.py` to align two images based on two points selected in each image, then calls `hybrid_image`. I also included (but commented out) the double for-loop I used to try different pairs of Gaussian blurring sigma values (where a larger sigma is roughly akin to fewer low-frequencies being kept when convolving an image with the kernel).

**Part 2.3: Gaussian and Laplacian Stacks**
`gaussian_stack`: implements a Gaussian stack by repeatedly convolving an image with Gaussian kernels of bigger sigma-values (and also bigger widths). The 0-th level of the Gaussian stack is the original image.

`laplacian_stack`: implements a Laplacian stack by first creating a Gaussian stack of the same image, then subtracting adjacent Gaussian levels from each other. The n-th level of the Lpalacian stack is set to be the n-th Gaussian level.

**Part 2.4: Multi-resolution Blending (a.k.a. the oraple!)**
`multiresolution_blend`: creates a Laplacian stack for each of the two images, as well as a Gaussian stack for the mask. Then, adds the corresponding Laplacian levels of each stack together, weighting img1 by the mask's Gaussian response at that same level and weighting img2 by (1 - mask's Gaussian response). Finally, adds all the combined levels together into a single picture. This function saves the final blended image, plus side-by-side comparisons of the two original inputs with the blended picture, and a grid of the three stacks and each level's blended result. A visualization detail: Laplacian levels can have negative values; so to make them easier to visualize in the outputs, I adjusted their values just for the plots such that the middle value in each channel corresponded to 0.5 and remapped the other values accordingly.

`make_multiresolution_mask`: takes in an image and uses Matplotlib widgets to create an interactive display where users can select points in the display to build a polygon. Then, uses scikit-image's polygon function to fill in the polygon. Returns a mask of floats with 1's in the pixels corresponding to the filled-in polygon.

## Image files included inside `data/`:
- DerekPicture.jpg
- stanford_tree.jpg
- burger.jpg
- chinatown.jpg
- saturn.jpg
- taj.jpg
- apple.jpg
- orange.jpg
- tetons.jpg
- oski.jpg
- clownfish.jpg
- dinosaur_nuggets.jpg
- jurassic_park.jpg
- deenasun_square.jpg
- cameraman.png
- nutmeg.jpg

## How to run my code for project 2

1. Set up a virtual environment, activate it, and install the dependencies in `requirements.txt`.

2. If the `data/` and `out/` directories do not exist yet, create them as subfolders of `code/`. These should match the values set for `DATA_DIR` and `OUTPUT_DIR` inside `main.py`.

3. From `code`, run:
```
python main.py
```

