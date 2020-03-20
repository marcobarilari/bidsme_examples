import os
import shutil
import logging
import random

from definitions import checkSeries, plugin_root

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


def SubjectEP(scan):
    scan.sub_values["handiness"] = random.choice([0, 1])


def SessionEP(scan):
    global series
    global sid
    sub = scan.subject
    ses = scan.session
    path = os.path.join(rawfolder,
                        sub, ses,
                        "MRI")
    series = sorted(os.listdir(path))
    series = [s.split("-", 1)[1] for s in series]
    sid = -1
    checkSeries(path, sub, ses, False)
    # copytng behevioral data
    aux_input = os.path.join(rawfolder, sub, ses, "auxiliary")
    if ses in ("ses-LCL", "ses-HCL"):
        if not os.path.isdir(aux_input):
            logger.error("Session {}/{} do not contain auxiliary folder"
                         .format(sub, ses))
            return -1
        for old, new in (("FCsepNBack.tsv", "task-rest_events.tsv"),
                         ("FCsepNBack.json", "task-rest_events.json"),
                         ("VAS.tsv", "task-rest_beh.tsv"),
                         ("VAS.json", "task-rest_beh.json")):
            source = "{}/{}".format(aux_input, old)
            if not os.path.isfile(source):
                logger.error("{}/{}: File {} not found"
                             .format(sub, ses, source))


series = list()
sid = -1
Intended = ""


def SequenceEP(recording):
    global series
    global sid
    global Intended
    Intended = ""
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


def SequenceEndEP(outfolder, recording):
    """
    Simulates 3D to 4D images conversion
    """
    modality = recording.Modality()

    if modality not in ("func", "dwi"):
        return

    f4D = os.path.join(outfolder, "4D")
    if not os.path.isfile(f4D + ".nii"):
        logger.info("{}: Converting {} MRI to 4D"
                    .format(recording.recIdentity(index=False),
                            modality))
        first_file = os.path.join(outfolder, recording.files[0])
        shutil.copy2(first_file, f4D + ".nii")
        first_file = os.path.splitext(first_file)[0] + ".json"
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
        for f_nii in recording.files:
            f_nii = os.path.join(outfolder, f_nii)
            f_json = os.path.splitext(f_nii)[0] + ".json"
            os.remove(f_nii)
            os.remove(f_json)
