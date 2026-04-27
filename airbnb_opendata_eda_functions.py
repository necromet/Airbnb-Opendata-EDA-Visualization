import pandas as pd
import numpy as np

def remove_dollar_sign(value):
    if pd.isna(value):
        return np.nan
    else:
        return float(value.replace("$", "").replace(",", "").replace(" ", ""))