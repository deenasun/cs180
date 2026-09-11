# Deena's CS 180: Project 1 - Colorizing the Prokudin-Gorskii Photo Collection

```
├─code/
| |-data/           # input dir containing glass plate negatives (DATA_DIR)
| |-out/            # output dir where result will be saved (OUTPUT_DIR)
│ ├─main.py         # main auto-alignment algorithms and pipeline
│ |-experiments.py  # contains ad-hoc experiments, visualizations, and comparisons!
| |-requirements.txt
│ └─README.md      # you are here right now :)
└─web/
  └─page.pdf        # PDF snapshot of my proj1 portfolio
```

## `main.py`

`main.py` contains the core functions I implemented for project 1.

`find_colored_edges`: detects and coordinates representing the innermost edge of a solid-color border.
For each side (left, right, top, or bottom), the image starts at the outer edge and iterates inward until less than 70% of the pixels in that row/column match the target color, or until it reaches a certain fraction of the image's total height/width.

`crop_rgb`: a helper function that calls `find_colored_edges` for 3 color plates, then determines a shared border amount to crop from all 3 plates.
Although the exact width of the solid-color borders might differ between each of the 3 plates, I wanted to crop the same amount from all 3 plates so that small differences in cropping here didn't propagate into bigger alignment errors.

`l2_distance` and `normalized_cross_correlation` implement the L2 Norm and NCC between 2 input matrices.

`align`: my single-scale alignment algorithm! Given an `img` and a `base_img`, this function searches a window of possible displacements `(dy, dx)` around `(dy=0, dx=0)`. It then returns a tuple of the best displacements found, based on either minimizing the `l2_distance` or maximizing `normalized_cross_correlation`.

`search`: helper function for my image-pyramid alignment algorithm. This is a generalization of `align` that 1) accepts a parameter specifying a displacement `(dy, dx)` to center the search window around, and 2) extracts a fixed interior rectangle from the `base_img` and the `img` after being shifted by a candidate `(dy, dx)` during the search so that metrics are only computed on interior pixels.

`pyramid_align`: my image-pyramid alignment algorithm! It recursively calls itself with a downsampled version of the `img` and `base_img`, then uses the recursive function's found displacements (scaled back up by 2x) as an initial estimate for finding the best `(dy, dx)` at its current scale. In the base case, when the image's width or height are smaller than 200px, this function searches over a large search window. At bigger scales, it uses a smaller search radius for efficiency to iteratively refine the current displacement vector estimate.

`align_image_pipeline`: runs the full image alignment pipeline given a path to an input file. The full pipeline includes reading the input file as an image, separating the 3 colored plates, cropping black and white borders, aligning all 3 plates together, stacking the plates into a single RGB image, and trimming wraparound pixels. This pipeline uses the `pyramid_align` function.

`edge_detection_align`: runs the full image alignment pipeline, but finds the best alignment between the color plates based on their edges rather than their pixel intensities. This pipeline uses `scikit-image`'s `canny` edge detector to detect edges from each plate before calling `pyramid_align`.

## How to run my automatic alignment code

0. Set up a virtual environment, activate it, and install the dependencies in `requirements.txt`.

1. Create 2 folders at the root of `code/` called `data/` and `out/`. These should match the constants defined in `DATA_DIR` and `OUTPUT_DIR`.

2. Put the 14 provided glass plate negatives under `data/`.
    a. The 4 additional glass plate images I chose can be downloaded here! I used the highest resolution `.tif` files that were available online.

3. Uncomment either the `align_image_pipeline` or `edge_detection_align` line to run the full image processing pipeline on each input file inside `data/`. From the root directory of `code/`, run `python3 main.py`.
    a. Alternatively, I like to use my IDE's interactive Python window to run my Python code side-by-side as I develop. In interactive Python window mode, I can select and run certain parts of my Python file in real-time, see generated plots/visualizations, and experiment faster :) Interactive window mode executes the selected code sequentially and preserves variables in between executions (for example, you would need to run import statements to initialize them in the `ipykernel` kernel, or run function definitions before trying to call the functions).

    To turn on interactive Python mode in VSCode/Cursor, set `"jupyter.interactiveWindow.textEditor.executeSelection": true`. Then, open a Python file. Highlight the lines you want to execute and press `shift + enter`. If promped, select the virtual environment created during setup as the Python interpreter.

4. To generate the 4 different variations in my results gallery, run `python3 experiments.py`. The main function in that file runs the `process_results_gallery` function on each input file inside `data/`. The `process_results_gallery` function will generate 4 results for each input image: the original glass plates stacked on top of each other without any alignment, image pyramid + L2, image pyramid + NCC, and image pyramid + Canny edge detector + NCC.

## Image sources
In addition to the 14 provided images, I also chose 4 glass plate negatives from the [Library of Congress's Prokudin-Gorskii collection](https://www.loc.gov/collections/prokudin-gorskii/?st=grid): laika.tif, milan_duomo.tif, borodino.tif, st_boris.tif.