import pandas as pd
from django.conf import settings


def load_fabaccess_logs():
    """
    load Fab access from fabdev mixins as a dataframe for further analysis.
    """
    df = pd.read_csv(settings.FABACCESSLOG_FILE, sep=";", names=['Date', 'Level', 'User','Method', 'Url', 'Status_code'],
                     header=None)
    df["Date"] = pd.to_datetime(df["Date"], format=settings.LOG_DATEFMT)
    return df
