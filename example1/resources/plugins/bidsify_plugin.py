import os
import shutil
import logging
import random

from definitions import checkSeries


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
# protocol, thus it is impossible to identify them only using
# metadata
# we will identify them by order they appear in session

# list of sequences in order of acquisition in current session
seq_list = list()


#####################
# Sequence variable #
#####################

# The index of current sequence, corresponds to order in the sequence list
seq_index = -1

# Identified tag for fMRI and MPM MRI
# This tag will override "SeriesDescription" DICOM tag
IntendedFor = ""


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
    global rawfolder
    global bidsfolder
    global dry_run

    rawfolder = source
    bidsfolder = destination
    dry_run = dry


def SubjectEP(scan):
    """
    Subject modification
    """

    ####################
    # Subject renaming #
    ####################

    # This will demonstrate the subject renaming
    # namely increasing the id by 1
    """
    sub_id = int(scan.subject[4:])
    scan.subject = "sub-{:03d}".format(sub_id + 1)
    # changing also in participant.tsv file
    if scan.sub_values["paired"]:
        pair_id = int(scan.sub_values["paired"][4:])
        scan.sub_values["paired"] = "sub-{:03d}".format(pair_id + 1)
    """

    #################################
    # Subject metadata manipulation #
    #################################

    # these modifications will appear only if corresponding
    # columns are declared in participants.json
    # they will not allow to add/remove columns

    # to modify the columns, use --part-template cli option

    # this will remove information on sex of subject, from bidsified dataset,
    # but not corresponding columns
    scan.sub_values["sex"] = None

    # this will fill new column "random"
    # if this column is in participant.json, it will be shown
    # in bidsified participant.tsv
    scan.sub_values["random"] = random.random()


def SessionEP(scan):
    """
    Session files modification

    1. Stores the list of sequences in session
    2. Checks the sequences
    3. Copies HCL and LCL task and KSS/VAS files
    to bidsified dataset
    """

    ######################################
    # Initialisation of sesion variables #
    ######################################
    # retrieving list of sequences and puttintg them into list
    global seq_list
    global seq_index
    path = os.path.join(scan.in_path, "MRI")
    seq_list = sorted(os.listdir(path))
    seq_list = [s.split("-", 1)[1] for s in seq_list]
    seq_index = -1

    #################################
    # Checking sequences in session #
    #################################
    checkSeries(path, scan.subject, scan.session, False)

    #############################################
    # Checking for existance of auxiliary files #
    #############################################

    # all the copy instructions must be protected by
    # if not dry_run

    aux_input = os.path.join(scan.in_path, "auxiliary")
    if scan.session in ("ses-LCL", "ses-HCL"):
        if not os.path.isdir(aux_input):
            logger.error("Session {}/{} do not contain auxiliary folder"
                         .format(scan.subject, scan.session))
            raise FileNotFoundError("folder {} not found"
                                    .format(aux_input))
        beh = os.path.join(scan.in_path, "beh")
        if not dry_run:
            os.makedirs(beh, exist_ok=True)
        for old, new in (("FCsepNBack.tsv", "task-rest_events.tsv"),
                         ("FCsepNBack.json", "task-rest_events.json"),
                         ("VAS.tsv", "task-rest_beh.tsv"),
                         ("VAS.json", "task-rest_beh.json")):
            source = "{}/{}".format(aux_input, old)
            dest = "{}/{}_{}_{}".format(beh, scan.subject, scan.session, new)
            if not os.path.isfile(source):
                if dry_run:
                    logger.error("{}/{}: File {} not found"
                                 .format(scan.subject, scan.session, source))
                else:
                    logger.critical("{}/{}: File {} not found"
                                    .format(scan.subject,
                                            scan.session,
                                            source))
                    raise FileNotFoundError(source)
            if os.path.isfile(dest):
                logger.warning("{}/{}: File {} already exists"
                               .format(scan.subject, scan.session, dest))
            if not dry_run:
                shutil.copy2(source, dest)


def SequenceEP(recording):
    """
    Sequence identification
    """
    global seq_index
    global IntendedFor
    IntendedFor = ""
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
            IntendedFor = "nBack"
        elif mod.endswith("cmrr_mbep2d_bold_mb2_task_nfat"):
            IntendedFor = "nBack"
        elif mod.endswith("cmrr_mbep2d_bold_mb2_rest"):
            IntendedFor = "rest"
        else:
            IntendedFor = "invalid"
            logger.warning("{}: Unknown session {}"
                           .format(recording.recIdentity(),
                                   mod))
    # fmap images are taken for HCL, LCL and MPM (STROOP)
    # sessions
    elif recid == "gre_field_mapping":
        if recording.sesId() in ("ses-HCL", "ses-LCL"):
            IntendedFor = "HCL/LCL"
        elif recording.sesId() == "ses-STROOP":
            IntendedFor = "STROOP"
        else:
            logger.warning("{}: Unknown session {}"
                           .format(recording.recIdentity(),
                                   recording.sesId()))
            IntendedFor = "invalid"
    # fmaps sesnsBody and sesnArray are taken just before
    # structural PD , T1 and MT. Looking into next sequences
    # will allow the identification
    elif recid == "al_mtflash3d_sensArray":
        det = seq_list[seq_index + 2]
        if det.endswith("al_mtflash3d_PDw"):
            IntendedFor = "PDw"
        elif det.endswith("al_mtflash3d_T1w"):
            IntendedFor = "T1w"
        elif det.endswith("al_mtflash3d_MTw"):
            IntendedFor = "MTw"
        else:
            logger.warning("{}: Unable determine modality"
                           .format(recording.recIdentity()))
            IntendedFor = "invalid"
    elif recid == "al_mtflash3d_sensBody":
        det = seq_list[seq_index + 1]
        if det.endswith("al_mtflash3d_PDw"):
            IntendedFor = "PDw"
        elif det.endswith("al_mtflash3d_T1w"):
            IntendedFor = "T1w"
        elif det.endswith("al_mtflash3d_MTw"):
            IntendedFor = "MTw"
        else:
            logger.warning("{}: Unable determine modality"
                           .format(recording.recIdentity()))
            IntendedFor = "invalid"


def RecordingEP(recording):
    if IntendedFor != "":
        recording.setAttribute("SeriesDescription", IntendedFor)
