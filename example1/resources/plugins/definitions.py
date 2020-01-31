import logging
import os

logger = logging.getLogger(__name__)

Series = {
        "ses-LCL": ('localizer',
                    'cmrr_mbep2d_bold_mb2_invertpe', 
                    'cmrr_mbep2d_bold_mb2_task_nfat', 
                    'cmrr_mbep2d_bold_mb2_invertpe', 
                    'cmrr_mbep2d_bold_mb2_rest',
                    'gre_field_mapping',
                    'gre_field_mapping',
                    't1_mpr_sag_p2_iso',
                    't2_spc_da-fl_sag_p2_iso'
                    ),
        "ses-HCL": ('localizer',
                    'cmrr_mbep2d_bold_mb2_invertpe',
                    'cmrr_mbep2d_bold_mb2_task_fat',
                    'cmrr_mbep2d_bold_mb2_invertpe',
                    'cmrr_mbep2d_bold_mb2_rest',
                    'gre_field_mapping',
                    'gre_field_mapping',
                    'cmrr_mbep2d_diff_NODDI_invertpe',
                    'cmrr_mbep2d_diff_NODDI',
                    'cmrr_mbep2d_diff_NODDI_noise'
                    ),
        "ses-STROOP": ('localizer',
                       'al_mtflash3d_sensArray',
                       'al_mtflash3d_sensBody',
                       'al_mtflash3d_PDw',
                       'al_mtflash3d_PDw',
                       'al_mtflash3d_sensArray',
                       'al_mtflash3d_sensBody',
                       'al_mtflash3d_T1w',
                       'al_mtflash3d_T1w',
                       'al_mtflash3d_sensArray',
                       'al_mtflash3d_sensBody',
                       'al_mtflash3d_MTw',
                       'al_mtflash3d_MTw',
                       'al_B1mapping',
                       'gre_field_mapping',
                       'gre_field_mapping'
                       )
        }


countSeries = {}
for ses in Series:
    countSeries[ses] = dict.fromkeys(Series[ses], 0)
    for ser in Series[ses]:
        countSeries[ses][ser] += 1


def checkSeries(path: str,
                subject: str, session: str,
                critical: bool) -> None:
    """
    Retrieve list of series from path and checks 
    its compatibility with defined list

    Parameters:
    -----------
    path: str
        Path to folder containing series folder
    subject: str
        Subject id
    session: str
        Name of session to check
    critical: bool
        If True, mismatches will creeate exceptions 
        and critical level log entries
    """
    if session not in Series:
        msg = "{}/{}: Invalid session".format(subject, session)
        reportError(msg, critical, KeyError)
        return
    passed = True
    series = sorted(os.listdir(path))
    series = [s.split("-",1)[1] for s in series]
    for ind, s in enumerate(series):
        if s not in Series[session]:
            msg = "{}/{}: Invalid serie {}".format(subject, session, s)
            logger.error(msg)
            passed = False
            continue
        if s == "cmrr_mbep2d_bold_mb2_invertpe":
            if ind >= len(series) or\
                    series[ind + 1] not in ("cmrr_mbep2d_bold_mb2_task_nfat",
                                            "cmrr_mbep2d_bold_mb2_task_fat",
                                            "cmrr_mbep2d_bold_mb2_rest"):
                msg = "{}/{}: {:03}-{} isn't followed by task recording"\
                    .format(subject, session, ind, s)
                logger.error(msg)
                passed = False
        elif s == "al_mtflash3d_sensArray":
            if ind >= len(series) - 1 or\
                    series[ind + 2] not in ("al_mtflash3d_PDw",
                                            "al_mtflash3d_MTw",
                                            "al_mtflash3d_T1w"):
                msg = "{}/{}: {:03}-{} isn't followed by weighted recording"\
                        .format(subject, session, ind, s)
                logger.error(msg)
                passed = False
        elif s == "al_mtflash3d_sensBody":
            if ind >= len(series) or\
                    series[ind + 1] not in ("al_mtflash3d_PDw",
                                            "al_mtflash3d_MTw",
                                            "al_mtflash3d_T1w"):
                msg = "{}/{}: {:03}-{} isn't followed by weighted recording"\
                        .format(subject, session, ind, s)
                logger.error(msg)
                passed = False

    for ser, count in countSeries[session].items():
        count_loc = series.count(ser)
        if count != count_loc:
            msg = "{}/{}: Expected {} occurences of {}, got {}"\
                    .format(subject, session, count, ser, count_loc)
            logger.error(msg)
            passed = False

    if not passed:
        msg = "{}/{}: One or several series errors detected"\
                .format(subject, session)
        reportError(msg, critical, ValueError)
    return passed


def reportError(msg: str, critical: bool, error: type=ValueError) -> None:
    """
    reports error. 
    If critical, an exception of type error will raise

    Parametres:
    -----------
    msg: str
        message to report
    critical: bool
        determines level of error
    error: exception
        type of exception to raise in case of critical
    """
    if critical:
        logger.critical(msg)
        raise exception(msg)
    else:
        logger.error(msg)
