# Contribution rules

## Data pipeline

- Run all commands from the repository root.
- Fetch the ODS mirror first: `python3 src/script/mirror_spreadsheet.py`.
- Convert Health second: `python3 src/script/convert_health.py`.
- Convert Food third: `python3 src/script/convert_food.py`.
- Convert Construction fourth: `python3 src/script/convert_construction.py`.
- Never run conversion against a stale ODS mirror.
- Never edit mirrored or generated data manually.
- Commit the updated ODS and generated JSON together.
- Stop when any script fails; do not commit partial output.

## Roles

### Backend developer

- May change any repository file.
- Owns specifications, scripts, data mappings, and generated datasets.
- Must run the complete data pipeline after data-related changes.

### Front-end developer

- Works only on the `website` branch, where the static website is generated.
- May change presentation only: layouts, styles, typography, colors, and visual assets.
- May consume generated data but must not edit it.
- Must not change `spec/`, `src/script/`, `res/var/data/`, or `res/data/`.
- Must not change schemas, mappings, pipeline behavior, or data semantics.

## Design rules

### Typography

* **Prioritize legibility over personality.** Avoid ornate, handwritten, distorted, or excessively decorative fonts for reading text. ([Brand Center][1])
* **Use 1–2 type families.** Let size, weight and spacing create variation—not a collection of fonts. ([designsystem.illinoisstate.edu][2])
* **Create obvious hierarchy:** H1 → H2 → H3 → body; each level visibly distinct and structurally ordered. ([visualidentity.columbia.edu][3])
* **Body text ≈ 16–20 px** as a practical web baseline. ([designsystem.illinoisstate.edu][2])
* **Keep lines short:** roughly **50–75 characters** is an excellent target; avoid full-screen paragraphs. ([Oregon State Blogs][4])
* **Use generous line-height:** around **1.5× for body copy** is a strong accessibility baseline. ([Elon University][5])
* **Left-align long text.** Avoid justified, centered, or right-aligned paragraphs. ([brandguide.asu.edu][6])
* **Use sentence case.** Avoid long passages in ALL CAPS, excessive italics and excessive underlining. ([Harvard Digital Accessibility][7])
* **Use whitespace deliberately.** More space between sections than between related elements; spacing itself communicates hierarchy. ([Harvard Digital Accessibility][7])
* **No unnecessary decoration:** no waves, blobs, swooshes, ornamental flourishes or gratuitous shapes. Prefer clean typography, whitespace and alignment to create interest. This is a minimalist application of university guidance emphasizing clarity, hierarchy and restrained decoration. ([Brand Center][1])

### Beautiful website palettes

* **Use a small palette.** Too many competing colors weaken hierarchy; strong colors should be intentional and sparse. ([test.solstice.uw.edu][8])
* **Start with neutrals:** background + surface + dark text; introduce color primarily for emphasis and interaction. ([UAL][9])
* **Assign colors roles**, e.g. `background`, `surface`, `text`, `primary`, `accent`, `success`, `warning`, `error`—don't choose colors ad hoc per component. ([HarvardSites Design System][10])
* **A useful balance is ~70 / 20 / 10:** dominant / supporting / accent color. University of Glasgow explicitly recommends this three-colour approach for simplicity and balance. ([University of Glasgow][11])
* **Reserve saturated color for accents:** buttons, links, active states and small highlights—not huge competing areas. ([wds.utdallas.edu][12])
* **Contrast is non-negotiable:** at least **4.5:1 for normal text** and **3:1 for large text** under WCAG AA guidance. ([brand.ucla.edu][13])
* **Never communicate meaning by color alone.** Pair status colors with text, icons or another visual cue. ([accessibility.umn.edu][14])
* **Avoid text directly over busy gradients/photos.** Use a solid surface or sufficiently uniform overlay behind it. ([Harvard Digital Accessibility][15])
* **Use one consistent link/action color.** Consistency makes interfaces calmer and easier to understand. ([University of Greater Manchester][16])
* **Beauty comes from restraint:** neutral space + strong typography + one recognizable primary + one restrained accent generally produces a cleaner system than many decorative colors. ([HarvardSites Design System][10])

**Shortest rule:** **fewer fonts, fewer colors, stronger hierarchy, generous whitespace, excellent contrast, consistent alignment, no decorative clutter.**

[1]: https://brandcenter.ufl.edu/typography/ "Typography - UF Brand Center"
[2]: https://designsystem.illinoisstate.edu/guidelines/typography/ "Typography | Illinois State Design System"
[3]: https://visualidentity.columbia.edu/content/typography-and-headings "Typography and Headings | Visual Identity"
[4]: https://blogs.oregonstate.edu/calverta/line-width-in-digital-typography-for-accessibility-and-comprehension/ "Line Width in Digital Typography for Accessibility and ..."
[5]: https://www.elon.edu/u/university-communications/online-communications/accessibility-toolkit/websites/typography/ "Typography and Font Sizes: Ensuring Readability for All ..."
[6]: https://brandguide.asu.edu/brand-elements/design/fonts "Fonts and typography - ASU Brand Guide"
[7]: https://accessibility.huit.harvard.edu/design-readability "Design for readability | Digital Accessibility​ Services"
[8]: https://test.solstice.uw.edu/foundations/color "Color - Solstice"
[9]: https://www.arts.ac.uk/design-system/foundations/colour "UAL Design System"
[10]: https://designsystem.harvardsites.harvard.edu/color-roles "Color Roles | HarvardSites Design System"
[11]: https://www.gla.ac.uk/myglasgow/staff/webpublishing/advicefort4users/colours/ "University of Glasgow - MyGlasgow - MyGlasgow Staff - Guide to Web Publishing - Using t4 - Use of colours"
[12]: https://wds.utdallas.edu/brand/ "Brand - Web Design System | The University of Texas at Dallas"
[13]: https://brand.ucla.edu/fundamentals/accessibility/color-type "Accessibility | Color & Type"
[14]: https://accessibility.umn.edu/guides-resources/7-core-accessibility-skills/contrast "Contrast | Office for Digital Accessibility (ODA)"
[15]: https://accessibility.huit.harvard.edu/color "Creating an Accessible Color Palette"
[16]: https://greatermanchester.ac.uk/brand/colours-and-palette "Colours and palette | University of Greater Manchester"
