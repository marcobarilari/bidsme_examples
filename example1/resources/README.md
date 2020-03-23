# Bidscoin Example 1

## Introduction

This dataset is an purely fictional, designed to demonstrate the core 
features of `bidscoin` bidsifier tool. 

The structure of dataset is modelled of real-life dataset, currently unpublished.
Several simplifications has been applied, conserving only the MRI images structure,
general participants book-keeping, naming schema and few auxiliary files.

MRI recordings are stored in Nifti format with an additional json file containing 
the dump of Dicom header, created by [hmri toolbox](https://hmri-group.github.io/hMRI-toolbox/) 
for [SPM12](https://www.fil.ion.ucl.ac.uk/spm/software/spm12/). 
All `.nii` images are replaced by an empty file, and any personal information is removed
from json files.

## Experiment description

The experiment is designed to study of effect of fatigue on memory performance.

5 participants are separated into pairs with matched sex, age and years of education.
First persons of pairs are used for study (patient group), while paired persons are used for control.

During experiment, each participant is scanned 3 times (sessions), for each of session they are asked to perform either a memory or a stroop task:

- **HLC** with memory task performed after a tiring task (High Cognitive Load)
  - In additional to functional and structural, a diffusion scan is present
- **LCL** with memory task performed without tiring task (Low Cognitive Load)
  - Session contains structural and functional MRI scans
- **STROOP** with a standard stroop task
  - session contains only multi parametric mapping MRI (MPM)

The order in which each scan is performed may vary from participant to participant.

## Original dataset structure

The original data is stored in `source` directory. Data corresponding to each participants
is stored in `source/<participant id>` sub-folder, where `<participant id>` the code of 
participant padded with `0`.

Inside participants sub-folders, 3 folders of session data is places. The folder names 
don't have a direct correspondence with session, bit represent a code applied by a scanner,
in form `sXYZ`.

The image data is stored directly in session sub-folder `nii`.
For **LCL** and **HCL** sessions, task and assessment are stored in `inp` sub-folder.

Tiring task, and stroop task data are not present in dataset.

### Memory task description

Task consist of a classic n-back working memory update task.
A set of letters is presented to participant. Each letter is presented during `1.7s`,
followed by `0.5s` fixation cross presentation. Participant is asked to remember 
if such letter was present in the last, 2 cards ago or 3 cards age (1back, 2back, 3back).
A participant response ("c" for correct, "n" for non-correct) is registered alongside with
expected response. 
A fill task consists of 18 blocks of 1,2,3-back tasks, with 16 presented letters in each block.

Task results are formatted following [bids](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/05-task-events.html),
and stored in `source/<subject>/<session>/nii/FCsepNBack.tsv` file.

### Assesment description

Each task is followed by visual analogue assessment (VAS) questioner, where participant is 
asked to estimate his psychological state from bad (0) to good (100).
In particular the next estimations are requested:

- **Motivation**
- **Hapiness**
- **Fatigue**
- **Openness**
- **Stress**
- **Anxiety**
- **Effort**

The results are formatted following [bids](https://bids-specification.readthedocs.io/en/stable/03-modality-agnostic-files.html#phenotypic-and-assessment-data),
and stored in `source/<subject>/<session>/nii/VAS.tsv`

### MRI scanning sessions

#### LCL

During the LCL session, the next acquisitions are taken:
 
- localisation (protocol: `localizer`)
- a short fMRI sequence with inverted phase-encoding direction
(protocol: `cmrr_mbep2d_bold_mb2_invertpe`)  
- a fMRI sequence during nBack task execution (protocol: `cmrr_mbep2d_bold_mb2_task_nfat`)
- a short fMRI sequence with inverted phase-encoding direction
(protocol: `cmrr_mbep2d_bold_mb2_invertpe`)  
- a fMRI sequence without task execution -- in resting state (protocol: `cmrr_mbep2d_bold_mb2_rest`)
- a magnitude encoded fieldmap sequence (protocol: `gre_field_mapping`)
- a phase-difference fieldmap sequence (protocol: `gre_field_mapping`)
- a FLAIR sequence (protocol: `t1_mpr_sag_p2_iso`)
- a T2 weighted sequence (protocol: `t2_spc_da-fl_sag_p2_iso`)

#### HCL

During HCL session, the next acquisitions are taken:

- localisation (protocol: `localizer`)
- a short fMRI sequence with inverted phase-encoding direction
(protocol: `cmrr_mbep2d_bold_mb2_invertpe`)  
- a fMRI sequence during nBack task execution (protocol: `cmrr_mbep2d_bold_mb2_task_fat`)
- a short fMRI sequence with inverted phase-encoding direction
(protocol: `cmrr_mbep2d_bold_mb2_invertpe`)  
- a fMRI sequence without task execution -- in resting state (protocol: `cmrr_mbep2d_bold_mb2_rest`)
- a magnitude encoded fieldmap sequence (protocol: `gre_field_mapping`)
- a phase-difference fieldmap sequence (protocol: `gre_field_mapping`)
- a diffusion sequence with inverted gradient direction (protocol: `cmrr_mbep2d_diff_NODDI_invertpe`)
- a diffusion sequence with normal gradient direction (protocol: `cmrr_mbep2d_diff_NODDI`)
- a diffusion sequence without RF-pulse (protocol: `cmrr_mbep2d_diff_NODDI_noise`)


#### STROOP

During STROOP session, the next acquisitions are taken:

- localisation (protocol: `localizer`)
- head-localised fieldmap for PD weighted sMRI (protocol: `al_mtflash3d_sensArray`) 
- body-localised fieldmap for PD weighted sMRI (protocol: `al_mtflash3d_sensBody`) 
- magnitude-encoded PD weighted structural MRI (protocol: `al_mtflash3d_PDw`)
- phase-encoded PD weighted structural MRI (protocol: `al_mtflash3d_PDw`)
- head-localised fieldmap for T1 weighted sMRI (protocol: `al_mtflash3d_sensArray`) 
- body-localised fieldmap for T1 weighted sMRI (protocol: `al_mtflash3d_sensBody`) 
- magnitude-encoded T1 weighted structural MRI (protocol: `al_mtflash3d_T1w`)
- phase-encoded T1 weighted structural MRI (protocol: `al_mtflash3d_T1w`)
- head-localised fieldmap for PD weighted sMRI (protocol: `al_mtflash3d_sensArray`) 
- body-localised fieldmap for PD weighted sMRI (protocol: `al_mtflash3d_sensBody`) 
- magnitude-encoded MT weighted structural MRI (protocol: `al_mtflash3d_MTw`)
- phase-encoded MT weighted structural MRI (protocol: `al_mtflash3d_MTw`)
- a B1 mapping with RF flip-angle relaxation (protocol: `al_B1mapping`)
- a magnitude encoded fieldmap sequence (protocol: `gre_field_mapping`)
- a phase-difference fieldmap sequence (protocol: `gre_field_mapping`)

### Additional files

All non-data files corresponding to dataset are stored in `resources` subfolder

#### Participants bookkeeping `Appariement.xlsx`

`Appariement.xlsx` is an excel table containing the list of participants with key 
demographic data.

Columns are, in order:

- **Patient**: Id of participant, padded with `0`
- **Sex**: Sex of participant, either `M` (male) or `F` (female)
- **Age**: Age of participant, in years
- **Education**: Years of education
- **1**: Name of the first scanned session (session *OUT* signify dropped-out participant)
- **2**: Name of the second scanned session
- **3**: Name of the third scanned session
- **Control**: Id of paired participant, padded with `0`
- **Sex**: Sex of paired participant, either `M` (male) or `F` (female)
- **Age**: Age of paired participant, in years
- **Education**: Years of education
- **1**: Name of the first scanned session (session *OUT* signify dropped-out participant)
- **2**: Name of the second scanned session
- **3**: Name of the third scanned session

#### Sidecar json files

Prepeared json files to use as [descriptions](https://bids-specification.readthedocs.io/en/stable/02-common-principles.html#tabular-files) 
for bidsified `.tsv` files:

- `participants.json` is a sidecar json file for `participant.tsv` file, containing list 
of participants together with demographic information
  - alternative files `participants_add.json` and `participants_remove.json` are used for
demonstration of participant table manipulations by `bidscoin`
- `FCsepNBack.json` is sidecar json file for task table
- `VAS.json` is sidecar json file for VAS


#### bval and bvec files

`bval` and `bvec` files used to accompany [diffusion data](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/01-magnetic-resonance-imaging-data.html#diffusion-imaging-data)
are placed in `resources/diffusion` folder. They are common to all diffusion images used
in this dataset.

#### Bidsmap files

Generated bidsmap files, that can be used to bidsify this dataset are placed in `resources/map` directory:

- `bidsmap.yaml` must be used together with plugins
- `bidsmap_noPlugin.yaml` can be used without plugins

These files can be used with `-b` option directly, or copied into `bids/code/bidscoin` directory.

#### Plugins

The plugins are stored in `resources/plugins` directory, and contains commented example of additional data management provided by `bidscoin` infrastructure.

- `definitions.py` contains some common functions used by plugin and list of sessions and protocols used to check dataset validity
- `rename_plugin.py` retrieves the demographic data and sessions names from `Appariement.xlsx`bookkeeping file
- `process_plugin.py` contains some example of intermediate data processing, namely merging functional and diffusion 3D images into 4D images, it also shows example of subject demographic data modification
- `bidsify_plugin.py` contains examples of recording metadata modification in order to facilitate recordings identification

#### Dataset description files
[The dataset description](https://bids-specification.readthedocs.io/en/stable/03-modality-agnostic-files.html#dataset-description)
consists of two files:

- `dataset_description.json`, a minimal example of json file describing dataset
- `README.md`, this file


## How to run example

Dataset bidsification is composed of two steps: data preparation and data bidsification.
An optional data-processing step can be inserted between preparation and bidsification.

A one-time step of bidsmap creation may be necessary.

### Data preparation

In this step, a generic user-defined dataset is organized in a standardized way.

To run data preparation, it will be enough to run from `example1` directory

```
python3 bidscoin.py prepare --part-template resources/participants.json --recfolder nii=MRI --plugin resources/plugins/rename_plugin.py source/ renamed/
```

The options `--part-template resources/participants.json` will tell bidscoin to use participant json file as template for `participants.tsv` file. 
The column `participant_id` will be filled automatically, while other columns will be filled 
by default by `n/a`, unless they are set in plugin:

```
session.sub_values["sex"] = "M"
```

Without `--part-template` option the only column in participants file will be `participant_id`.

Option `--recfolder nii=MRI` will tell to `bidscoin` that image files are MRI and stored in `nii` folder. 
Without this option `bidscoin` will be unable to find image files.

Option `--plugin resources/plugins/rename-plugin.py` will tell to bidscoin to load corresponding plugin.

Parameters `source/` and `renamed/` tells to bidscoin where to search for source dataset and where place prepared dataset.

After the execution of preparation, the `rename` folder should contain folders and files:

- **code/bidscoin**, with log files of the last execution of preparation step
- **participants.tsv** and **participants.json** files with formatted and filled participant list, all columns for all subjects must be filled except `handiness`, which should contain only `n/a`
- **sub-00X** folders for subjects 1-4
  - **ses-HCL** sub-folders with bidsified session name (either `ses-LCL`, if run with plugin, of `ses-s01905` if run without plugin)
    - **auxiliary** folder with task and VAS tables and json (only if run with plugin)
    - **MRI** subfolder containing MRI data
      - **00x-<seq_name>** folders with original image data organased by sequences

This is prepared dataset, and can be modified freely at condition to conserve general structure.
For example the participant table can be corrected if contain wrong or missing values.

Running bidscoin with all options can be tedious. To streamline the experience, the majority of options can be saved in configuration file by running 

```
python3 bidscoin.py -c conf.yamel --conf-save prepare <options> source/ renamed/
```

This will create a local `conf.yamel` file with passed options. 
To load the configuration:

```
python3 bidscoin.py -c conf.yamel prepare source/ renamed/
```

Passing other options and using switch `--conf-save` will update configuration file.


### Bidsmap creation

Bidsmap is created/tested with `map` command:

```
python3 bidscoin.py map --plugin resources/plugins/bidsify_plugin.py --template bidsmap_template.yaml renamed/ bids/
```

The option `--plugin resources/plugins/bidsify_plugin.py` will load correspondent plugin (the used plugin is the same as for bidsification to ensure that all modifications needed to 
identify scans are applied).

The option `--template bidsmap_template.yaml` tells which template will be used. The template 
reads the common metatdata and tries to guess the modality. This is based on protocol names and can vary from institute to institute.
The `bidsmap_template.yaml` works with example dataset, but for real data a different template may be needed.

The parameters `renamed/` and `bids/` tells where prepared dataset is stored and where the bidsified dataset will be placed.

First execution of `map` usually results into huge amount of warnings and occasional errors.
These warnings and errors must be corrected. The details of various warnings and corrections to apply can be found in `bidscoin` documentation. 

The working bidsmap can be found in `resources/map` directory. 
If placed in `bids/code/bidscoin/` directory, the `map` should not produce any warnings. 



### Process step

The process step is an optional step, which allow limited data manipulation before bidsification.
Without plugins, it just verifies that all data is identifiable, and files with same bids name
do not exists in bids dataset.
So it can be used as check before bidsification.

With plugins, it can be used for data manipulation, and metadata completion.
For example `resources/plugins/process_plugin.py` fills the `nandiness` column, and merges
fMRI and diffusion images in single 4D image.

```
python3 bidscoin.py process --plugin resources/plugins/process_plugin.py renamed/ bids/
```

After running, the column `handiness` must be filled and fMRI files 
(for ex. in `renamed/sub-002/ses-LCL/MRI/004-cmrr_mbep2d_bold_mb2_task_nfat/`)
must be merged in one file.

This step can be easily replaced by any custom script and/or pipeline. The only advantage
is some `bids` and `bidscoin` specific checks and recording identification.


### Bidsification step

The final step is bidsification, it is run with `bidsify` command:

```
python3 bidscoin.py map --plugin resources/plugins/bidsify_plugin.py renamed/ bids/
```

