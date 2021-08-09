from tisane.variable import AbstractVariable, Nominal, Ordinal, Numeric

from typing import Union

# TODO: Remove RandomEffect
class RandomEffect(object):
    groups: AbstractVariable
#     # The _iv_ is allowed to vary per each group in _groups_

class RandomSlope():
    iv: AbstractVariable
    groups: AbstractVariable 

    def __init__(
        self, iv: AbstractVariable, groups: AbstractVariable
    ):
        self.iv = iv
        self.groups = groups

class RandomIntercept():
    def __init__(self, groups: AbstractVariable):
        self.groups = groups

class CorrelatedRandomSlopeAndIntercept():
    random_slope: RandomSlope
    random_intercept: RandomIntercept
    
    def __init__(self, iv: Union[AbstractVariable, int], groups: AbstractVariable):
        self.random_slope = RandomSlope(iv=iv, groups=groups)
        self.random_intercept = RandomIntercept(groups=groups)

# Each group can have a different random intercept
# Each group in groups is allowed to have a different slope along iv (random slope)
class UncorrelatedRandomSlopeAndIntercept():
    random_slope: RandomSlope
    random_intercept: RandomIntercept
    
    def __init__(self, iv: Union[AbstractVariable, int], groups: AbstractVariable):
        self.random_slope = RandomSlope(iv=iv, groups=groups)
        self.random_intercept = RandomIntercept(groups=groups)

def correlate_random_slope_and_intercept(random_slope: RandomSlope, random_intercept: RandomIntercept) -> CorrelatedRandomSlopeAndIntercept: 
    iv = random_slope.iv
    assert(random_slope.groups == random_intercept.groups) # Assert that tha random slope and intercept pertain to the same groups
    groups = random_slope.groups 
    return CorrelatedRandomSlopeAndIntercept(iv=iv, groups=groups)

def uncorrelate_random_slope_and_intercept(random_slope: RandomSlope, random_intercept: RandomIntercept) -> UncorrelatedRandomSlopeAndIntercept: 
    iv = random_slope.iv
    assert(random_slope.groups == random_intercept.groups) # Assert that tha random slope and intercept pertain to the same groups
    groups = random_slope.groups 
    return UncorrelatedRandomSlopeAndIntercept(iv=iv, groups=groups)
