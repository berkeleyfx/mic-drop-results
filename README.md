# Mic Drop Results
A program that generates result slides from judging data<br>
**[More info about Mic Drop here](https://discord.gg/ZeGWzgvFcR)**

## Installation
To install, please check out the [latest release](https://github.com/berkeleyfx/mic-drop-results/releases/), download **mic-drop-results.zip**, and extract it. [Round-dependent](https://github.com/berkeleyfx/mic-drop-results#requirements) files are included in **sample.zip**.

## Requirements
The following files are required (five files in total) and they all have to be in the same directory.

**Program-end**<br>
These files are inseparable and should never be modified or renamed unless there is an update.

- **app.exe**
- **config.json** (you can modify if you know exactly what you are doing)
- **Module1.bas**

**Round-dependent**<br>
These files will vary every round. You can find samples of these files in [`/sample`](./sample) or in the **sample.zip** file included in every release.

- **data.xlsx**
- **template.pptm**

<p align="center">
  <img src="https://github.com/berkeleyfx/mic-drop-results/blob/ee91a53c19acde31786945378d71c328a626a00f/.github/ISSUE_TEMPLATE/images/required_files.png"></img>
</p>

## Guides
Here are some things you should keep in mind when editing **data.xlsx**:
- Do not give any two columns the same name
- Column names are preferably given in lowercase without any space between characters
- Do not name any columns `r` because the column for ranks will later use the same name

### Template editing**
<sup>(**This is a very important section)</sup><br>
This section guides you how to customize **template.pptm** and **data.xlsx**.

- Make sure your template presentation has the extension `.pptm` or macros would not be able to run on this presentation
- Look up **Trust Center Settings** and make sure **Trust access to the VBA project object model** is checked
- Each slide is a template. You can specified which template is used for each contestant through the `template` column in **data.xlsx**
- Any texts in the presentation that follow the format `{column_name}` will be replaced with the corresponding value from the `column_name` column
- It is fine to have columns that will not appear on the slides and vice versa, a textbox with `{column_name}` that does not have a column named `column_name` will be left as is. They will not throw an error.
- `{r}` will be replaced with the rank of the contestant in that round

### Ranking
This section explains how ranks are calculated.
- Ranks are based on the first two columns, with the first (usually the average score) sorted in descending order, and the second column (usually the standard deviation) in ascending order
- If two people have a different average score, the one with a higher score will get a higher rank
- If two people have the same average score, the one with a lower std will get a higher rank
- If two people have the same average and std, they will hold the same rank

**Tips for special rounds**<br>
Here are some tips for special themes that do not depend on the average score or standard deviation.
- If you want to invert the sorting order (for example, in a theme where you have to submit the worst songs to all judges, the ones with the lowest scores will win), you can create a new temporary column `avg_temp`, which will not appear on the slides, that multiplies all values in the `avg` column by -1 and put it at the beginning.
- If you want to disable secondary column sorting, you can make a temporary column where every row has the same number, and move it after the first column.
- There is always a way to sort your data no matter how crazy your theme idea is, otherwise we would never know who places first and who places last.

### Conditional formatting
Here are some mechanisms behind the conditional color formatting for scores
- Column names that start with `score` by default (you can change it in **config.json**) will use conditional color formatting for numbers
- The average scores are not formatted by default. If you want them to be formatted, rename the column from `avg` to `score` for example (a reference to the previous rule)
- Conditional formatting will only apply to text in white (**#FFFFFF**)
- You can customize the range and color in **config.json**.

More features are on their way in future updates.

## Contributions
All contributions are appreciated. Make sure you follow this [Python Style Guide](https://peps.python.org/pep-0008/) for consistency when making changes to the code.

#### Additional contributions
- Report a bug or suggest a feature [(here)](https://github.com/berkeleyfx/mic-drop-results/issues/new/choose)
- Contact Banz#6175 on Discord for bug reports, suggestions, and support
