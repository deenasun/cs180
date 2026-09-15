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
  └─deena_cs180_proj1.pdf        # PDF snapshot of my proj1 portfolio
```

## Website
I included 5 variants of every image in my website's final gallery. All the images in my website can be viewed in higher-resolution/full-screen if you hover your mouse over them for about 1 second :)

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

`align_image_pipeline`: runs the full image alignment pipeline given a path to an input file. The full pipeline includes reading the input file as an image, separating the 3 colored plates, cropping black and white borders, aligning all 3 plates together, stacking the plates into a single RGB image, and trimming wraparound pixels. If the input param `use_image_pyramid` is set to True, this pipeline will use the `pyramid_align` function; otherwise, this pipeline will use the single-scale `align` function. The input param `metric` (`"l2"` or `"ncc"`) is passed to the alignment function calls inside the pipeline.

`edge_detection_align`: runs the full image alignment pipeline, but finds the best alignment between the color plates based on their edges rather than their pixel intensities. This pipeline uses `scikit-image`'s `canny` edge detector to detect edges from each plate before calling the alignment functions. If the input param `use_image_pyramid` is set to True, this pipeline will use the `pyramid_align` function; otherwise, this pipeline will use the single-scale `align` function. The input param `metric` (`"l2"` or `"ncc"`) is passed to the alignment function calls inside the pipeline.

## How to run my automatic alignment code

1. Set up a virtual environment, activate it, and install the dependencies in `requirements.txt`.

2. Create 2 folders at the root of `code/` called `data/` and `out/`. These should match the constants defined inside `main.py`'s `DATA_DIR` and `OUTPUT_DIR`.

3. Put the 14 provided glass plate negatives under `data/`.
  a. I also chose 4 additional glass plate images from the [Library of Congress's Prokudin-Gorskii collection](https://www.loc.gov/collections/prokudin-gorskii/?st=grid) (I used the highest resolution `.tif` files that were available online):
      i. laika.tif - [Studies in the mouth of Kem River - laika (dog)](https://www.loc.gov/item/2018679239/)
      ii. milan_duomo.tif - [Details of Milan Cathedral](https://www.loc.gov/item/2018679122/)
      iii. borodino.tif - [River Koloch at the Village of Gorki with a High Bank. Borodino [Battlefield]](https://www.loc.gov/item/2018679978/)
      iv. st_boris.tif - [Village of Deviatiny and the Saint Boris Dam [Russian Empire]](https://www.loc.gov/item/2018678884/)
    
4. Inside `main.py`'s `main()` function, set `USE_IMAGE_PYRAMID` to `True` to use my image-pyramid algorithm for aligning the images. Set `USE_IMAGE_PYRAMID` to `False` to use my single-scale algorithm for aligning the images. Similarly inside `main()` , set `METRIC` to either `"l2"` or `"ncc"`.

5. Uncomment either the `align_image_pipeline` or `edge_detection_align` line to run the full image processing pipeline on each input file inside `data/`. If you want to run the full pipeline on a batch of images without the code pausing to display matplotlib visuals on-screen, make sure to set the input parameter `display=False` (otherwise the execution will pause until you close the displayed plots). From the root directory of `code/`, run `python3 main.py`.
  a. Alternatively, I like to use my **IDE's interactive Python window** to run my Python code side-by-side as I develop. In interactive Python window mode, I can select and run certain parts of my Python file in real-time, see generated plots/visualizations, and experiment faster :) Interactive window mode executes the selected code sequentially and preserves variables in between executions (for example, you would need to run import statements to initialize them in the `ipykernel` kernel, or run function definitions before trying to call the functions).
  > To turn on interactive Python mode in VSCode/Cursor, set `"jupyter.interactiveWindow.textEditor.executeSelection": true`. Then, open a Python file. Highlight the lines you want to execute and press `shift + enter`. If promped, select the virtual environment created during setup as the Python interpreter.

6. To generate the 5 different variations in my results gallery, run `python3 experiments.py`. The main function in that file runs the `process_results_gallery` function on each input file inside `data/`. The `process_results_gallery` function will generate 5 results for each input image: the original glass plates stacked on top of each other without any alignment, image pyramid + NCC without cropping black/white borders (as a baseline to compare my bells and whistle border-detectiong feature to), image pyramid + L2 + black/white border detection, image pyramid + NCC + black/white border detection, and image pyramid + Canny edge detector + NCC + black/white border detection.

