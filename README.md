# Deena's CS 180 Portfolio

---

This repo contains my CS 180 project code and portfolio website 🌌

```
cs180/
├── src/               # Portfolio website
├── public/            # Image assets deployed on the website
├── project_code/      # Code for each CS 180 project
│   ├── proj1/
│   ├── proj2/
│   ├── proj3/
│   ├── proj4/
│   └── final-project/
```

The code (e.g. python files, .ipynb notebooks, datasets) for each project is located inside `project_code/`.

The code for my portfolio's website is located inside `src/`. A GitHub actions workflow will run `next build` to generate the `out/` directory, and serve the static bundle in `out/` directory on GitHub pages. Any assets for the website located inside `public/` will be copied into the exported site.