import os
import shutil
import logging
import random

from bids import BidsSession

from definitions import checkSeries, plugin_root

"""
process_plugin defines all nessesary functions to pre-process
prepared dataset. Essentually it just merges 3D images to 4D
"""

# defining logger this way will prefix plugin messages
# with plugin name
logger = logging.getLogger(__name__)

#############################
# global bidscoin variables #
#############################

# Folder with prepared dataset
preparedfolder = None
# folder with bidsified dataset
bidsfolder = None
# switch if is a dry-run (test run)
dry_run = False


#####################
# Session variables #
#####################

# Some sequences within session (namely fMRI and MPM structural) follows same
# protocol, thus it is impossible to identify them only using metadata
# we will identify them by order they appear in session

# list of sequences in order of acquisition in current session
seq_list = list()


#####################
# Sequence variable #
#####################

# The index of current sequence, corresponds to order in the sequence list
seq_index = -1


def InitEP(source: str, destination: str, dry: bool) -> int:
    """
    Initialisation of plugin

    1. Saves source/destination folders and dry_run switch

    Parameters
    ----------
    source: str
        path to source dataset
    destination:
        path to prepared dataset
    """
    global preparedfolder
    global bidsfolder
    global dry_run

    preparedfolder = source
    bidsfolder = destination
    dry_run = dry


def SubjectEP(scan: BidsSession) -> int:
    """
    Subject modification

    1. Fills the handiness value for subject
    """

    # values in scan.sub_values are pre-filled
    # from participants.tsv file, no need to refill them.
    # If needed to remove value from participants, you
    # can set it to None, or set to new value
    scan.sub_values["handiness"] = random.choice([0, 1])


def SessionEP(scan: BidsSession) -> int:
    """
    Session files modifications

    1. Stores the list of sequences in the session
    2. Checks if session contains correct sequences
    2. Checks if session HCL and LCL contains task and
    KSS/VAS files
    """

    ######################################
    # Initialisation of sesion variables #
    ######################################
    # retrieving sequences and puttintg them into list
    global seq_list
    global seq_index
    path = os.path.join(scan.in_path, "MRI")
    seq_list = sorted(os.listdir(path))
    # removing leading sequence number from name
    seq_list = [s.split("-", 1)[1] for s in seq_list]
    seq_index = -1

    #################################
    # Checking sequences in session #
    #################################
    checkSeries(path, scan.subject, scan.session, False)

    #############################################
    # Checking for existance of auxiliary files #
    #############################################
    # BidsSession.in_path contains current session folder path
    aux_input = os.path.join(scan.in_path, "auxiliary")
    if scan.session in ("ses-LCL", "ses-HCL"):
        if not os.path.isdir(aux_input):
            logger.error("Session {}/{} do not contain auxiliary folder"
                         .format(scan.subject, scan.session))
            return -1
        for old, new in (("FCsepNBack.tsv", "task-rest_events.tsv"),
                         ("FCsepNBack.json", "task-rest_events.json"),
                         ("VAS.tsv", "task-rest_beh.tsv"),
                         ("VAS.json", "task-rest_beh.json")):
            source = "{}/{}".format(aux_input, old)
            if not os.path.isfile(source):
                logger.error("{}/{}: File {} not found"
                             .format(scan.subject, scan.session, source))


def SequenceEP(recording):
    """
    Sequence identification
    """

    global seq_index

    # recording.custom is a dictionary for user-defined variables
    # that can be acessed from bidsmap
    # they are initialized at new sequence, and conserved for all files
    # within sequence, can be used to define sequence-global parameters
    recording.custom["IntendedFor"] = ""
    seq_index += 1
    recid = seq_list[seq_index]

    # checking if current sequence corresponds in correct place in list
    if recid != recording.recId():
        logger.warning("{}: Id mismatch folder {}"
                       .format(recording.recIdentity(False),
                               recid))

    # The inverted fMRI are taken just before normal fMRI
    # looking into the following sequence will identify
    # the current one
    if recid == "cmrr_mbep2d_bold_mb2_invertpe":
        mod = seq_list[seq_index + 1]
        if mod.endswith("cmrr_mbep2d_bold_mb2_task_fat"):
            recording.custom["IntendedFor"] = "nBack"
        elif mod.endswith("cmrr_mbep2d_bold_mb2_task_nfat"):
            recording.custom["IntendedFor"] = "nBack"
        elif mod.endswith("cmrr_mbep2d_bold_mb2_rest"):
            recording.custom["IntendedFor"] = "rest"
        else:
            recording.custom["IntendedFor"] = "invalid"
            logger.warning("{}: Unknown session {}"
                           .format(recording.recIdentity(),
                                   mod))
    # fmap images are taken for HCL, LCL and MPM (STROOP)
    # sessions
    elif recid == "gre_field_mapping":
        if recording.sesId() in ("ses-HCL", "ses-LCL"):
            recording.custom["IntendedFor"] = "HCL/LCL"
        elif recording.sesId() == "ses-STROOP":
            recording.custom["IntendedFor"] = "STROOP"
        else:
            logger.warning("{}: Unknown session {}"
                           .format(recording.recIdentity(),
                                   recording.sesId()))
            recording.custom["IntendedFor"] = "invalid"
    # fmaps sesnsBody and sesnArray are taken just before
    # structural PD , T1 and MT. Looking into next sequences
    # will allow the identification
    elif recid == "al_mtflash3d_sensArray":
        det = seq_list[seq_index + 2]
        if det.endswith("al_mtflash3d_PDw"):
            recording.custom["IntendedFor"] = "PDw"
        elif det.endswith("al_mtflash3d_T1w"):
            recording.custom["IntendedFor"] = "T1w"
        elif det.endswith("al_mtflash3d_MTw"):
            recording.custom["IntendedFor"] = "MTw"
        else:
            logger.warning("{}: Unable determine modality"
                           .format(recording.recIdentity()))
            recording.custom["IntendedFor"] = "invalid"
    elif recid == "al_mtflash3d_sensBody":
        det = seq_list[seq_index + 1]
        if det.endswith("al_mtflash3d_PDw"):
            recording.custom["IntendedFor"] = "PDw"
        elif det.endswith("al_mtflash3d_T1w"):
            recording.custom["IntendedFor"] = "T1w"
        elif det.endswith("al_mtflash3d_MTw"):
            recording.custom["IntendedFor"] = "MTw"
        else:
            logger.warning("{}: Unable determine modality"
                           .format(recording.recIdentity()))
            recording.custom["IntendedFor"] = "invalid"


def SequenceEndEP(outfolder, recording):
    """
    Simulates 3D to 4D images conversion
    """
    modality = recording.Modality()

    # only for fMRI and diffusion images
    if modality not in ("func", "dwi"):
        return

    f4D = os.path.join(outfolder, "4D")
    if not os.path.isfile(f4D + ".nii"):
        logger.info("{}: Converting {} MRI to 4D"
                    .format(recording.recIdentity(index=False),
                            modality))
        first_file = os.path.join(outfolder, recording.files[0])
        # "convertion" is just copy of first file in sequence
        # in real application a external tool should be used
        shutil.copy2(first_file, f4D + ".nii")
        first_file = os.path.splitext(first_file)[0] + ".json"
        # copying the first file json to allow the identification
        shutil.copy2(first_file, f4D + ".json")

        # copying fake bval and bvec values
        # during the bidsifications these files will
        # be automatically picked up
        if modality == "dwi":
            shutil.copy2(os.path.join(plugin_root,
                                      "diffusion",
                                      "NODDI.bval"),
                         os.path.join(outfolder,
                                      "4D.bval"))
            shutil.copy2(os.path.join(plugin_root,
                                      "diffusion",
                                      "NODDI.bvec"),
                         os.path.join(outfolder,
                                      "4D.bvec"))

        # Removing now obsolete files
        for f_nii in recording.files:
            f_nii = os.path.join(outfolder, f_nii)
            f_json = os.path.splitext(f_nii)[0] + ".json"
            os.remove(f_nii)
            os.remove(f_json)
