# Deena's CS 180: Project 4 Part B - Feature Matching for Autostitching

```
├─code/
| |-data/               # images that I used/referenced in my notebooks
│ └─harris.py           # sample code for Harris corner detection and matrix distance calculations provided in the project instructions
│ └─main.py             # my code for parts A and B
│ └─PART_B_README.md    # you are here right now :)
│ └─requirements.txt    # dependencies required for project 4
└─web/
  └─page.pdf        # PDF snapshot of my proj4 portfolio
```

## Website
All the images in my website can be viewed in higher-resolution/full-screen if you hover your mouse over them for about 1 second :)

## `main.py`

This file contains all of my code for project 4 parts A and B!

My implementations for part B are in the following functions:
- Part B.1: Harris Corner Detection - `harris_corner_detection` and `adaptive_nonmaximal_suppression`
- Part B.2: Feature Descriptor Extraction - `extract_feature_descriptors`
- Part B.2: Feature Matching - `match_features` and `plot_feature_matches`
- Part B.3: RANSAC for Robust Homography - `ransac`

The full end-to-end autostitching mosaic-making pipeline is implemented in `autostitch_mosaic`.


## Images inside `data/`

My code and portfolio for project 4 uses the following image files and expects them to be located under `data/`:
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
-`painting.jpg` (used in part A)
-`pompeii.jpg` (used in part A)
-`wall_fresco.jpg` (used in part A)

## How to run my code for project 4

Create a python virtual environment and install the dependencies from `requirements.txt`.

From inside the `code` directory, run `python maij.py`. The `main` function will run the necessary functions to produce the deliverables for project 4 parts A and B. Each subpart's code is separated with a comment labelling which subpart (A.2, A.3, A.4, B.1, B.2, B.3, B.4) it is for.

Many of the subparts will display a matplotlib window with subplots of the images/results. To unblock the code and move onto the next subpart, you will need to close the matplotlib display. Note that the interactive window for selecting correspondences will automatically close after the expected number of correspondences are selected (closing this window manually will cause the function to return however many correspondences are selected so far).

Most of the functions will print out info statements in the terminal as they are called — you can use this to check progress!
