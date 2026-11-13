# Compare and Copy Figures

*This page is the English user guide, [CompareCopyFigures.rtf](CompareCopyFigures.rtf). The guide is also available in Spanish ([CompareCopyFigures_sp.rtf](figuras/CompareCopyFigures_sp.rtf)) and French ([CompareCopyFigures_fr.rtf](figures_fr/CompareCopyFigures_fr.rtf)).*

## Purpose

Compares the figures (\fig ... \fig\*) of another project with your project in an HTML report, and copies the figures you select from that project into yours. This tool replaces the separate Compare Figures and Copy Figures tools. Both USFM 2 (pipe-delimited) and USFM 3 (src="...") figures are read.

Two projects are involved:

- The **project to compare with** (an option) is where the pictures come from.
- The **Output project** is where they go. Paratext sets it to the project you run the tool from, so normally it is your own project. Choose another Output project only if you want the figures to go somewhere else, for example a new project.

## How to use

1. Copy CompareCopyFigures.cms, CompareCopyFigures.py and CompareCopyFigures.rtf to your My Paratext Projects\cms folder.

2. In Paratext, open your project and run Compare and Copy Figures from the Figures submenu of the custom tools. Choose the books.

3. **Compare:** type the short name of the project to compare with (for example WSG), leave Mode set to Compare and click OK. The report opens in your browser. It is saved as local\CompareFigures\CompareFiguresReport.html in your project folder. Nothing is changed.

4. In the report, tick the figures you want to copy. "Select missing in ..." ticks every figure your project does not have, and "Select different from ..." ticks every figure where your project has another picture. Then click **Copy selection**. The list (for example GEN 7:24 GEN 12:9b) appears in the box and is copied to the clipboard. If the clipboard is blocked, press Ctrl+C.

5. Mark a point in project history for the Output project.

6. **Copy:** run the tool again with the same books, set Mode to Copy, paste the list into "Figures to copy" and click OK. The results list shows what was removed, added, replaced, skipped or could not be placed.

7. Run Compare again to check the result.

## How to read the report

The left column is the project to compare with, and the right column is the Output project. There is one row per figure reference. GEN 12:9 is the first figure in that verse, and GEN 12:9b is the second. A figure before verse 1 has verse 0. Red means the Output project has no figure there. Yellow means it has a different picture. The checkbox is only active when the project to compare with has the figure.

## How figures are placed

A copied figure goes at the end of the first line of the same verse in the Output project. If that verse is not found, the tool tries the verses up to 3 before or after it and says so ("Fuzzy match"). Several figures copied into one verse keep the order they have in the project to compare with. A figure that is already in that chapter of the Output project is skipped, unless the options below say otherwise.

## Options

**Mode**

- Default: Compare
- Compare makes the report. Copy copies the figures listed in "Figures to copy".

**Project to compare with (copy figures from)**

- Default: (empty)
- The short name of one Paratext project. It must be filled in, and it cannot be the Output project.

**Only show differences**

- Default: No
- Compare mode. Yes lists only the figures that are missing or different in one of the two projects.

**Display captions**

- Default: Yes
- Compare mode. Shows each figure's caption and location under its filename.

**Show/Compare the actual figure filename**

- Default: No
- Compare mode. Normally filenames from known illustration series are shortened, so 'HK01234b.tif' and 'hk01234c.jpg' both show as 'hk01234' and are not flagged as different. Yes shows and compares the full filenames.

**Show picture thumbnails**

- Default: Yes
- Compare mode. Shows a small copy of each picture found in the project's figures folder (.jpg, .png, .gif or .bmp; .tif files cannot be shown in a browser).

**Figures to copy**

- Default: (empty)
- Copy mode. The list made by "Copy selection". You can also type a book code (GEN), a chapter (GEN 12) or ALL. References not found in the project to compare with are listed in the results.

**Remove ALL existing figures from the Output project's book(s) before copying**

- Default: No
- Copy mode. Yes first removes every figure in the chosen books of the Output project, then inserts only the figures in "Figures to copy". If "Figures to copy" is empty, the figures are only removed. Mark a point in project history before using it.

**Copy figures even if they exist in the target project**

- Default: No
- Copy mode. No skips a figure whose picture is already in that chapter of the Output project. Yes replaces a figure at the same reference (for example to bring over a new caption), and adds again one that is elsewhere in the chapter.

**Replace a different figure at the same reference**

- Default: Yes
- Copy mode. When the Output project has a different picture at the same reference (yellow in the report), Yes replaces that figure. No adds the new figure beside it.

**Copy the figure FILES to target project**

- Default: Yes
- Copy mode. Copies the picture files from the figures folder of the project to compare with into the Output project's figures folder. If the file named in \fig is not there, a file with the same name and another picture extension (usually .jpg) is used. A file that is already in the Output project is not overwritten.

**Copy the CAPTIONS from the source to the target project**

- Default: Yes
- Copy mode. No leaves the captions empty.

**Put \[square brackets\] around target captions**

- Default: Yes
- Copy mode. Marks the copied captions as still needing translation.
