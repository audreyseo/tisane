from tisane.variable import AbstractVariable
# from tisane.main import Tisane

import pandas as pd 

class Concept(object): 
    def __init__(self, name:str):
        self.name = name
        self.variable = None
    
    def __repr__(self):
        return f"Concept: name:{self.name}, variable:<{self.variable.__repr__()}>"
    
    def __str__(self):
        pass
    
    def specifyData(self, dtype:str, categories=None, order=None, data=None): 
        self.variable = AbstractVariable.create(dtype=dtype, categories=categories, order=order, data=data)
    
    def addData(self, data: pd.DataFrame):         
        if self.variable: 
            self.replaceData(data)
        # Concept does not already have data associated with it
        else: 
            self.variable = AbstractVariable(data) # TODO: This will throw an error for now

    def replaceData(self, df: pd.DataFrame): 
        print("Replace previous data ({self.data}) with new data: {df}")
        self.variable = AbstractVariable(df) # TODO: This will throw an error for now

    def getVariable(self): 
        return self.variable

    def data(self): 
        return self.variable.data
