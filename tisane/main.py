from tisane.concept import Concept
from tisane.concept_graph import ConceptGraph, CONCEPTUAL_RELATIONSHIP
from tisane.smt.results import AllStatisticalResults

from enum import Enum 
from typing import Union
import copy 
from itertools import chain, combinations
import pandas as pd
import networkx as nx

class TASK(Enum): 
    EXPLANATION = 1
    PREDICTION = 2
    HYPOTHESIS_TESTING = 3 # Maybe hypothesis testing is a mode on top of explanation vs. prediction
    
    @classmethod
    def cast(self, type_str:str): 
        if type_str.upper() == 'EXPLANATION':
            return TASK.EXPLANATION
        elif type_str.upper() == 'PREDICTION': 
            return TASK.PREDICTION
        elif type_str.upper() == 'HYPOTHESIS TESTING': 
            return TASK.HYPOTHESIS_TESTING
        else: 
            raise ValueError(f"Data type {type_str} not supported! Try EXPLANATION, PREDICTION, or HYPOTHESIS TESTING")

class RELATIONSHIP(Enum): 
    LINEAR = 1
    # The choices below are arbitrary
    QUADRATIC = 2
    EXPONENTIAL = 3 

    @classmethod
    def cast(self, type_str:str): 
        if type_str.upper() == 'LINEAR':
            return RELATIONSHIP.LINEAR
        elif type_str.upper() == 'QUADRATIC':
            return RELATIONSHIP.QUADRATIC
        elif type_str.upper() == 'EXPONENTIAL': 
            return RELATIONSHIP.EXPONENTIAL
        else: 
            raise ValueError(f"Relationship type {type_str} not supported! Try LINEAR, QUADRATIC, or EXPONENTIAL")    

class Data(object): 
    pass

class Tisane(object):
    task : TASK
    graph : ConceptGraph # Not clear this is necessary at the moment
    relationship: RELATIONSHIP
    data : Data

    def __init__(self, task:str):
        self.task = TASK.cast(task)
        self.graph = ConceptGraph() # TODO: graph structure might not be the right one?
        self.relationship = None # TODO: Not sure we want to default to none? 
        self.data = None
    
    def __repr__(self):
        pass
    
    def __str__(self):
        pass

    # atomic add of a single Concept
    def addConcept(self, con: Concept): 
        if not self.graph: 
            self.graph = ConceptGraph()
        gr = self.graph
        
        if gr.hasConcept(con): 
            pass
        else: 
            # copy elts already in graph
            gr = copy.deepcopy(gr)
            # add new elt to graph
            gr.addNode(con)

        # assign self.graph to new graph with new concept (if created)
        self.graph = gr
    
    # Atomic add of list of Concepts
    def addConceptList(self, con_list: list): 
        if not self.graph: 
            self.graph = ConceptGraph()
        gr = self.graph

        # add the ivs if they are already not part of the graph 
        for c in con_list:
            if gr.hasConcept(c): 
                pass
            else: 
                # copy elts already in graph
                gr = copy.deepcopy(gr)
                # add new elt to graph
                gr.addNode(c)
        
        self.graph = gr
    
    def addData(self, data: Union[str, pd.DataFrame]):
        raise NotImplementedError
        # May want to do something about CSV (create new object class/type?)
        self.data = data

    def relate(self, ivs:list, dv=list, relationship=str): 
        assert(len(dv) == 1)

        all_cons = copy.deepcopy(ivs) + copy.deepcopy(dv) # deepcopy may not be necessary
        self.addConceptList(all_cons)

        # add the relationship
        self.relationship = RELATIONSHIP.cast(relationship)
        
    def between(self, con:Concept): 
        pass

    def addRelationship(self, lhs_con: Concept, rhs_con: Concept, relationship_type: str): 
        # add all concepts to the graph (nodes before edges)
        all_cons = [copy.deepcopy(lhs_con), copy.deepcopy(rhs_con)] # may not need deep copy
        # all_cons = [lhs_con, rhs_con] # may not need deep copy
        self.addConceptList(all_cons)

        # add Relationship (edge)
        cr = CONCEPTUAL_RELATIONSHIP.cast(relationship_type)
        self.graph.addEdge(lhs_con, rhs_con, cr)
        
    """
    Prediction: Use sets of variables that have BOTH causal and correlational relationships with DV
    """
    def predict(self, dv: Concept): 
        pass
    
    def predictWith(self, dv: Concept, ivs_to_include: list): 
        pass

    def predictWithOnly(self, dv: Concept, ivs_to_include_only: list): 
        pass

    def predictWithout(self, dv: Concept, ivs_to_exclude: list): 
        pass
    
    """
    Explanation: Use sets of variables that have ONLY causal relationships with DV
    """
    # FOR DEBUGGING
    def generate_effects_sets(self, dv: Concept):
        return self.graph.generate_effects_sets(dv=dv)

    def explain(self, dv: Concept): 

        effects_sets = self.graph.generate_effects_sets(dv=dv)

        all_valid_stat_models = AllStatisticalResults()


        # for m in comb_main: 
        #     model = create_model(m)
        #     if check_model(model): # check that model satisfy model requirements
        #         collect_models.append(model)
        
        return all_valid_stat_models
    
    def explainWith(self, dv: Concept, ivs_to_include: list): 
        pass

    def explainWithOnly(self, dv: Concept, ivs_to_include_only: list): 
        pass

    def explainWithout(self, dv: Concept, ivs_to_exclude: list): 
        pass
