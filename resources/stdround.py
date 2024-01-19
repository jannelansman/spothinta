def stdround(value, decimals=0):
    """
    ================================================================================
    Standard rounding to fixed number of decimals. 

    If only the one positional argument is given, 'decimals' defaults to 0 and 
    rounding is done to closest whole number. 

    Number of decimals to round to can be also negative and in this case e.g. 
    (value=1234.5678, decimals=-2) rounds to 1200.0.
    
    Valid return value is always a float.
    ================================================================================
    """
    if (not isinstance(value, float)) or (not isinstance(decimals, int)):
        raise TypeError(f"Expected input type to be int or float, but the type was: {type(value)}.")
    value = value*10**decimals
    value = int(value + 0.5)
    return value/10**decimals
