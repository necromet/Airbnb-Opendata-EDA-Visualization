import pandas as pd
import numpy as np

def remove_dollar_sign(value):
    if pd.isna(value):
        return value
    if isinstance(value, str): 
        return float(value.replace("$", "").replace(",", "").replace(" ", ""))
    else:
        return float(value)