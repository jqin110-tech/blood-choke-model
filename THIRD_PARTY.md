# Third-party material

## Anatomy in the 3D view (`simulator/anatomy.js`)

**Credit.** BodyParts3D, © The Database Center for Life Science licensed
under CC Attribution 4.0 International.

- **What it is.** 3D shapes of the head and neck of a reference adult male
  body: skin, skull, jaw, teeth, neck bones, brain, cerebellum, brainstem
  and the arteries of the head and neck. They come from BodyParts3D 4.0
  (Mitsuhashi et al. 2009, "BodyParts3D: 3D structure database for
  anatomical concepts", https://doi.org/10.1093/nar/gkn613).
- **Where this copy came from.** The npm package `abussola-med-models`,
  version 1.2.0, read by `scripts/build_anatomy.mjs`. That package is itself
  an adaptation, and its own notices ask that these credits be kept:
  - For the whole-body model (used here for the skin): "Anatomy:
    BodyParts3D © The Database Center for Life Science (CC BY 4.0); female
    organs: Human Reference Atlas 3D Reference Organs, HuBMAP (CC BY 4.0);
    female body: MakeHuman (CC0). Modified by open-anatomy-3d
    (https://github.com/MervinR07/open-anatomy-3d), CC BY 4.0." Only the
    male model is used here.
  - For the detailed male body (used here for bones, brain, eyes and
    arteries): "BodyParts3D, © The Database Center for Life Science
    licensed under CC Attribution 4.0 International", with the geometry
    prepared for the browser by human-atlas
    (https://github.com/ashemag/human-atlas, code MIT, data CC BY 4.0) and
    then selected, merged and compressed by the package's authors.
- **Licence.** Creative Commons Attribution 4.0 International,
  https://creativecommons.org/licenses/by/4.0/. BodyParts3D's own licence
  page: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html.
  `simulator/anatomy.js` is shared under the same licence. The rest of
  this repository is not covered by this notice.
- **Changes made here.** This is not the original data. The shapes were cut
  down to the head and neck, simplified to fewer triangles, turned and
  scaled into the page's coordinates, and stored at 16 bits per coordinate.
  The skin was smoothed by subdivision. Points of the brain and arteries
  were given a zone (front or back), the cortex a fold depth and the
  arteries a distance along from the neck, all computed by the script.
  Four plain tubes were added where the source has no artery: between the
  top of each common carotid and the bottom of the internal carotid above
  it, and below the start of each vertebral artery. The eyes' iris, pupil
  and lids and the cerebellum's leaf pattern are drawn by the page, not
  taken from the source.
- **How it is used.** As a picture only. No number in the model, the
  results or the README comes from it. The package's notice says the models
  are for education and visualisation and are not suitable for diagnosis or
  any clinical decision; the same holds here. Using the data is not an
  endorsement of this project by any of the people or organisations
  credited above.

## three.js

The 3D view loads three.js r128 from a public CDN at run time (MIT licence).
It is not copied into this repository.
