import os
import shutil
import logging
import pandas

import Modules

from definitions import Series, checkSeries

logger = logging.getLogger(__name__)

# global variables
rawfolder = ""
bidsfolder = ""
dry_run = False

participants_table = None
rec_path = ""
countSeries = {}


def InitEP(source: str, destination: str, dry: bool) -> int:
    global rawfolder
    global bidsfolder
    global dry_run

    rawfolder = source
    bidsfolder = destination
    dry_run = dry

    participants = os.path.join(rawfolder, "participants.tsv")
    if not os.path.isfile(participants):
        e = "participants.tsv not found in {}".format(rawfolder)
        logger.critical(e)
        raise FileNotFoundError("participants.tsv not found")

    global participants_table
    participants_table = pandas.read_csv(participants, sep='\t',
                                         header=0,
                                         index_col="participant_id",
                                         na_values="n/a")

    participants_table = participants_table.groupby("participant_id")\
        .ffill().drop_duplicates()
    duplicates = participants_table.index.duplicated(keep=False)
    if duplicates.any():
        logger.error("One or several subjects have conflicting values."
                     "See {} for details"
                     .format(participants))
        raise KeyError("Conflicting values in subject descriptions")
    Modules.baseModule.sub_BIDSfields.LoadDefinitions(os.path.join(rawfolder, 
                                                      "participants.json"))

def SessionEP(scan):
    global series
    global sid
    sub = scan["subject"]
    ses = scan["session"]
    path = os.path.join(rawfolder,
                        sub, ses,
                        "MRI")
    series = sorted(os.listdir(path))
    series = [s.split("-",1)[1] for s in series]
    sid = -1
    checkSeries(path, sub, ses, False)
    # copytng behevioral data
    aux_input = os.path.join(rawfolder, sub, ses, "aux")
    if ses in ("ses-LCL", "ses-HCL"):
        if not os.path.isdir(aux_input):
            logger.error("Session {}/{} do not contain aux folder"
                         .format(sub, ses))
            raise FileNotFoundError("folder {} not found"
                                    .format(aux_input))
        beh = os.path.join(bidsfolder, sub, ses, "beh")
        if not dry_run:
            os.makedirs(beh, exist_ok=True)
        for old, new in (("FCsepNBack.tsv", "task-rest_events.tsv"),
                         ("FCsepNBack.json", "task-rest_events.json"),
                         ("VAS.tsv", "task-rest_beh.tsv"),
                         ("VAS.json", "task-rest_beh.json")):
            source = "{}/{}".format(aux_input, old)
            dest = "{}/{}_{}_{}".format(beh, sub, ses, new)
            if not os.path.isfile(source):
                if dry_run:
                    logger.error("{}/{}: File {} not found"
                                 .format(sub, ses, source))
                else:
                    logger.critical("{}/{}: File {} not found"
                                    .format(sub, ses, source))
                    raise FileNotFoundError(source)
            if os.path.isfile(dest):
                logger.warning("{}/{}: File {} already exists"
                               .format(sub, ses, dest))
            if not dry_run:
                shutil.copy2(source, dest)


series = list()
sid = -1
Intended = ""

def SequenceEP(recording):
    global series
    global sid
    global Intended
    Intended = ""
    sub = recording.subId()
    part = participants_table.loc[sub]
    for f in participants_table.columns:
        recording.sub_BIDSvalues[f] = part[f]
    sid += 1
    recid = series[sid] 
    if recid != recording.recId():
        logger.warning("{}: Id mismatch folder {}"
                       .format(recording.recIdentity(False),
                                recid))
    if recid == "cmrr_mbep2d_bold_mb2_invertpe":
        mod = series[sid + 1]
        if mod.endswith("cmrr_mbep2d_bold_mb2_task_fat"):
            Intended = "nBack"
        elif mod.endswith("cmrr_mbep2d_bold_mb2_task_nfat"):
            Intended = "nBack"
        elif mod.endswith("cmrr_mbep2d_bold_mb2_rest"):
            Intended = "rest"
        else:
            Intended = "invalid"
            logger.warning("{}: Unknown session {}"
                           .format(recording.recIdentity(),
                                   mod))
    elif recid == "gre_field_mapping":
        if recording.sesId() in ("ses-HCL", "ses-LCL"):
            Intended = "HCL/LCL"
        elif recording.sesId() == "ses-STROOP":
            Intended = "STROOP"
        else:
            logger.warning("{}: Unknown session {}"
                           .format(recording.recIdentity(),
                                   recording.sesId()))
            Intended = "invalid"
    elif recid == "al_mtflash3d_sensArray":
        det = series[sid + 2]
        if det.endswith("al_mtflash3d_PDw"):
            Intended = "PDw"
        elif det.endswith("al_mtflash3d_T1w"):
            Intended = "T1w"
            recording.setAttribute("Intended", "T1w")
        elif det.endswith("al_mtflash3d_MTw"):
            Intended = "MTw"
        else:
            logger.warning("{}: Unable determine modality"
                           .format(recording.recIdentity()))
            Intended = "invalid"
    elif recid == "al_mtflash3d_sensBody":
        det = series[sid + 1]
        if det.endswith("al_mtflash3d_PDw"):
            Intended = "PDw"
        elif det.endswith("al_mtflash3d_T1w"):
            Intended = "T1w"
        elif det.endswith("al_mtflash3d_MTw"):
            Intended = "MTw"
        else:
            logger.warning("{}: Unable determine modality"
                           .format(recording.recIdentity()))
            Intended = "invalid"


def RecordingEP(recording):
    if Intended != "":
        recording.setAttribute("SeriesDescription", Intended)
