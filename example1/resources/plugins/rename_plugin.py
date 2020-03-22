import os
import pandas
import logging
import shutil

from tools import tools
from bids import BidsSession

from definitions import Series, checkSeries, plugin_root


# defining logger this way will prefix plugin messages
# with plugin name
logger = logging.getLogger(__name__)


#############################
# global bidscoin variables #
#############################

# Folder with source dataset
rawfolder = None
# folder with prepared dataset
preparedfolder = None
# switch if is a dry-run (test run)
dry_run = False

###########################
# global plugin variables #
###########################

# map of individual sessions
#   key: source folde session (s01234)
#   value: bidsified session (ses-HCL)
scans_map = {}

# scale to convert ms in log-files to seconds
time_scale = 1e-3

# subject balck-list
#   subject folders in this list will be skipped
#   by plugin
sub_black_list = []

# subject xls table columns and their renaiming
excel_col_list = {"Patient": "pat",
                  "Sex": "pat_sex",
                  "Age": "pat_age",
                  "Education": "pat_edu",
                  1: "pat_1", 2: "pat_2", 3: "pat_3",
                  'Control': "cnt",
                  "Sex.1": "cnt_sex",
                  "Age.1": "cnt_age",
                  "Education.1": "cnt_edu",
                  "1.1": "cnt_1", "2.1": "cnt_2", "3.1": "cnt_3"
                  }


# columns prefixes for patient and control subjects
#   0 == False == Control
#   1 == True == Patient
sub_prefix = ["cnt", "pat"]

# pandas dataframe with list of subjects
df_subjects = None


def InitEP(source: str, destination: str,
           dry: bool,
           subjects: str = "") -> int:
    """
    Initialisation of plugin

    1. Saves source/destination folders and dry_run switch
    2. Loads subjects xls table

    Parameters
    ----------
    source: str
        path to source dataset
    destination:
        path to prepared dataset
    subjects: str
        path to subjects xls file, if empty is looked
        in source dataset folder
    """

    global rawfolder
    global preparefolder
    global dry_run

    rawfolder = source
    preparefolder = destination
    dry_run = dry

    #########################
    # Loading subjects list #
    #########################
    if subjects:
        subject_file = subjects
    else:
        subject_file = os.path.join(plugin_root, "Appariement.xlsx")
    if not os.path.isfile(subject_file):
        raise FileNotFoundError("Subject file '{}' not found"
                                .format(subject_file))

    # creating dataframe for subjects
    global df_subjects
    df_subjects = pandas.read_excel(subject_file,
                                    sheet_name=0, header=0,
                                    usecols="A:N"
                                    )
    df_subjects.rename(index=str, columns=excel_col_list, inplace=True)
    df_subjects = df_subjects[df_subjects['pat'].notnull()
                              | df_subjects['cnt'].notnull()]


def SubjectEP(session: BidsSession) -> int:
    """
    Subject determination and initialisation

    1. Checks if subject not in balck list
    2. Loads demographics from subject table
    3. Creates session parcing dictionary

    Parameters
    ----------
    session: BidsSession

    Returns
    -------
    int:
        if 0, plugin succesfull
        if > 0, plugin failed, an exception will be raised
        if < 0, plugin failed, and subject will be skipped
    """

    #################################
    # Skipping if in the black list #
    #################################
    if session.subject in sub_black_list:
        logger.info("Subject '{}' is in black_list"
                    .format(session.subject))
        return -1

    ################################
    # Retriving subject from table #
    ################################
    try:
        # in case if folder name in source dataset
        # cannot be converted to integer
        sub_id = int(session.subject)
    except ValueError as e:
        logger.error("Subject {}: Can't determine subject Id for: {}"
                     .format(session.subject, e))
        return -1

    # storing bidsified subject id into session object
    # optional, but can be easely retrieved
    session.sub_values["participant_id"] = "sub-" + session.subject
    # looking for subject in dataframe
    prefix = "pat"
    index = df_subjects.loc[df_subjects[prefix] == sub_id].index
    # storing participant group in session
    session.sub_values["group"] = "patient"

    if len(index) == 0:
        # Subject not in patient list, looking in control
        prefix = "cnt"
        index = df_subjects.loc[df_subjects[prefix] == sub_id].index
        session.sub_values["group"] = "control"
        if len(index) == 0:
            raise KeyError("Subject {} not found in table"
                           .format(sub_id))
    if len(index) > 1:
        logger.warning("Subject {}: several column entries present"
                       .format(sub_id))
    index = index[0]

    # retrieving demographics
    sex = df_subjects.loc[index, prefix + "_sex"]
    age = df_subjects.loc[index, prefix + "_age"]
    education = df_subjects.loc[index, prefix + "_edu"]

    # session initialised values are Null
    # fill them only if they are retrieved from table
    if pandas.notna(sex):
        session.sub_values["sex"] = sex
    if pandas.notna(age):
        session.sub_values["age"] = float(age)
    if pandas.notna(education):
        session.sub_values["education"] = float(education)

    # looking for pairing
    paired = df_subjects.loc[index, sub_prefix[prefix == "cnt"]]
    if pandas.notna(paired):
        session.sub_values["paired"] = "sub-{:03}".format(int(paired))

    # looking for order of sessions
    scans_map.clear()
    scans_order = sorted([os.path.basename(s) for s in
                          tools.lsdirs(os.path.join(rawfolder,
                                                    session.subject),
                                       "s*")
                          ])
    # looping over session defined in columns
    for ind, s in enumerate(("_1", "_2", "_3")):
        v = "ses-" + str(df_subjects.loc[index, prefix + s]).strip()
        ses = "ses" + s
        if v == "ses-nan":
            # Session not defined in table, but existing
            # in source dataset
            session.sub_values[ses] = ""
            logger.warning("Subject {}({}): missing {} value"
                           .format(session.sub_values["participant_id"],
                                   session.sub_values["group"],
                                   ses)
                           )
        elif v == "ses-OUT":
            # participant left study
            logger.warning("Subject {}({}): seems to be abandoned study"
                           .format(session.sub_values["participant_id"],
                                   session.sub_values["group"],
                                   ses)
                           )
            return -1
        elif v not in Series:
            # invalid session name
            logger.critical("Subject {}({}): Invalid {}: {}"
                            .format(session.sub_values["participant_id"],
                                    session.sub_values["group"],
                                    ses,
                                    session.sub_values[ses])
                            )
            raise KeyError("Invalid {}: {}"
                           .format(ses, v))
        else:
            # session retrieved, storing values
            session.sub_values[ses] = v
            scans_map[scans_order[ind]] = v

    # checking if all scans are identifyable
    # if not, additional scans will be stored
    # with original names
    for scan in scans_order:
        if scan not in scans_map:
            logger.error("Subject {}({}): Can't identify session {}"
                         .format(session.sub_values["participant_id"],
                                 session.sub_values["group"],
                                 scan))
            scans_map[scan] = scan

    # opional, the sub- prefix added automatically
    # if not present
    session.subject = "sub-" + session.subject


def SessionEP(session: BidsSession) -> int:
    """
    1. Set-up session name

    Parameters
    ----------
    session: BidsSession
    """
    # Setting session name from map
    session.session = scans_map[session.session]


def SessionEndEP(session: BidsSession):
    """
    1. Checks the series in the prepared folder
    2. Extract KSS/VAS data from kss_dict to tsv file
    3. Parces in-scan nBack and KSS/VAS log files
    """
    # path contain destination folder, where
    # all data files are placed
    path = os.path.join(preparefolder,
                        session.getPath(True))
    out_path = os.path.join(path,
                            "MRI")

    # checking if session contains correct series
    if not dry_run:
        checkSeries(out_path,
                    session.subject, session.session,
                    False)

    ############################################
    # Retrieving in-scan task and KSS/VAS data #
    ############################################
    if session.session == "ses-STROOP":
        return 0
    # where tsv files are
    inp_dir = os.path.join(session.in_path, "inp")
    # where tsv files should be
    aux_dir = os.path.join(path, "auxiliary")
    if not os.path.isdir(inp_dir):
        raise NotADirectoryError(inp_dir)

    # do not copy if we are in dry mode
    if not dry_run:
        os.makedirs(aux_dir, exist_ok=True)
        # just copy file, in real life application
        # you may parce files
        for file in ("FCsepNBack.tsv", "VAS.tsv"):
            file = os.path.join(inp_dir, file)
            if not os.path.isfile(file):
                raise FileNotFoundError(file)
            shutil.copy2(file, aux_dir)

        # copiyng correspondent json files
        for file in ("FCsepNBack.json", "VAS.json"):
            file = os.path.join(plugin_root, file)
            if not os.path.isfile(file):
                raise FileNotFoundError(file)
            shutil.copy2(file, aux_dir)
