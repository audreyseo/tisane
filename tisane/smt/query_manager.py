from tisane.statistical_model import StatisticalModel
from tisane.design import Design 
from tisane.graph import Graph 

from tisane.smt.declare_constraints import *
# from tisane.smt.helpers import variables, get_facts_as_list
# from tisane.smt.rules import *
import tisane.smt.rules as rules
from tisane.smt.knowledge_base import KB

from z3 import *
from typing import List, Union, Dict

class QueryManager(object): 
    # QueryManager should be state-less? 

    
    def query(self, input_obj: Union[Design, StatisticalModel], output_obj: Union[Graph, StatisticalModel], output: str):
        # if isinstance(input_obj, Design): 
        #     if isinstance(output_obj, StatisticalModel): 
        #         # Figure out main effects care about for modeling 
        #         # Update edge from 'unknown' to 'unknown but model/explain'??

        #         # Figure out interaction effects
            

        # Compile @param input_obj to logical facts
        facts = input_obj.compile_to_facts()
        ambig_facts = input_obj.collect_ambiguous_facts(output=output)
        facts += ambig_facts # Combine all facts

        # Generate consts for grounding KB
        input_obj.generate_consts() 
        # Ground rules to simplify quantification during constraint solving
        dv_const = input_obj.dv.const
        main_effects = input_obj.consts['main_effects']
        interactions = input_obj.consts['interactions']
        mixed_effects = None # mixed effects
        
        
        # TODO: UPDATE main_effects, interactions, mixed effects before ground KB


        # If system should consider possible interactions (involves end-user)
        possible_interactions = False
        if isinstance(input_obj, Design): 
            possible_interactions = True
        KB.ground_rules(dv_const=dv_const, main_effects=main_effects, interactions=interactions, possible_interactions=possible_interactions)

        # After grounding KB, collect rules to guide synthesis
        rules = self.collect_rules(output_obj=output_obj) # dict
        # Incrementally and interactively solve the facts and rules as constraints
        (model, updated_facts) = self.solve(facts=facts, rules=rules, setting=None)
        import pdb; pdb.set_trace()
        result = self.postprocess_query_results(model=model, updated_facts=updated_facts, input_obj=input_obj, output_obj=output_obj)

        return result
    
    # @param outcome describes what the query result should be, can be a list of items, 
    # including: statistical model, variable relationship graph, data schema, data collection procedure
    # @return logical rules to consider during solving process
    def collect_rules(self, output_obj: Union[StatisticalModel, Graph, Design]) -> Dict: 
        # Get and manage the constraints that need to be considered from the rest of Knowledge Base     
        rules_to_consider = dict()

        # TODO: Clean up further so only create Z3 rules/functions for the rules that are added?
        if isinstance(output_obj, StatisticalModel):
            rules_to_consider['interaction_rules'] = KB.interaction_rules
            rules_to_consider['data_type_rules'] = KB.data_type_rules
            rules_to_consider['data_transformation_rules'] = KB.data_transformation_rules
            rules_to_consider['variance_functions_rules'] = KB.variance_functions_rules
        elif isinstance(output_obj, Graph):
            rules_to_consider['graph_rules'] = KB.graph_rules

        elif isinstance(output_obj, Design): 
            # import pdb; pdb.set_trace()
            # TODO: Should allow separate queries for data schema and data collection?? probably not?
            rules_to_consider['data_type_rules'] = KB.data_type_rules
            rules_to_consider['data_transformation_rules'] = KB.data_transformation_rules
            rules_to_consider['variance_functions_rules'] = KB.variance_functions_rules

        else: 
            raise ValueError(f"Query output is not supported: {type(output_obj)}.")
        
        return rules_to_consider

    # @param setting is 'interactive' 'default' (which is interactive), etc.?
    def solve(self, facts: List, rules: dict, setting=None): 
        updated_facts = list()

        s = Solver() # Z3 solver

        for batch_name, rules in rules.items(): 
            print(f'Adding {batch_name} rules.')
            # Add rules
            s.add(rules)

            updated_facts = self.check_update_constraints(solver=s, assertions=facts)[1]
        
        
        mdl =  s.model()
        return (mdl, updated_facts)

    # @param pushed_constraints are constraints that were added as constraints all at once but then caused a conflict
    # @param unsat_core is the set of cosntraints that caused a conflict
    # @param keep_clause is the clause in unsat_core to keep and that resolves the conflict
    def update_clauses(self, pushed_constraints: list, unsat_core: list, keep_clause: list): 
        # Verify that keep_clause is indeed a subset of unsat_core
        for c in keep_clause:
            assert(c in unsat_core)
        
        updated_constraints = list()
        for pc in pushed_constraints: 
            # Should we remove this constraint?
            if (pc in unsat_core) and (pc not in keep_clause): 
                pass
            else: 
                updated_constraints.append(pc)

        return updated_constraints
        
    # @param current_constraints are constraints that are currently SAT before adding @param unsat_core
    # @param unsat_core, which are the conflicting clauses
    # @returns a set of new clauses with the unsat core resolved with user input
    def elicit_user_input(self, current_constraints: list, unsat_core: list): 
        keep = list()
        while True: 
            # TODO: Allow for something totally new or different?
            idx = int(input(f'These cannot be true at the same time. Which is true? If neither, enter -1. {unsat_core}:'))
            if idx == -1: 
                pass
            elif idx in range(len(unsat_core)): 
                # only keep the constraint that is selected. 
                keep.append(unsat_core[idx])
                print(f"Ok, going to add {unsat_core[idx]} and remove the others.")
                break
            else:
                raise ValueError

        # return current_constraints + keep
        return keep

    def check_update_constraints(self, solver: Solver, assertions: list): 
        # updated_assertions = None
        state = solver.check(assertions)
        if (state == unsat): 
            unsat_core = solver.unsat_core() 
            # import pdb; pdb.set_trace()
            assert(len(unsat_core) > 0)


            # solver.push() # save state before add @param assertions

            # Ask user for input
            keep_constraint = self.elicit_user_input(solver.assertions(), unsat_core)
            
            # Modifies @param assertions
            updated_assertions = self.update_clauses(assertions, unsat_core, keep_constraint)
            assertions = updated_assertions
        elif (state == sat): 
            pass
        else: 
            raise ValueError(f"State of solver after adding user input conceptual graph constraints is {state}")

        # Double check that the new_assertions do not cause UNSAT
        new_state = solver.check(assertions)
        # import pdb; pdb.set_trace()
        if new_state == sat: 
            return (solver, assertions) # return the solver and the updated assertions
        elif new_state == unsat: 
            return self.check_update_constraints(solver=solver, assertions=assertions)
        else: 
            raise ValueError (f"Solver state is neither SAT nor UNSAT: {new_state}")

    # UPDATE: After trying to implement this: Realize easier to iterate through updated
    # facts and check that model is true rather than other way around. Have to
    # check which function instance is true anyway, which is what we have in the
    # updated facts. 
    def cast_from_model(self, input_obj: Union[Design], output_obj: Union[Graph], outcome: str, model: z3.ModelRef): 
        consts = dict()
        functions = list()

        # Iterate through the declarations in the model
        for d in model.decls(): 

            if isinstance(input_obj, Design): 
                input_vars = [v.name for v in input_obj.get_variables()]

                if d.name() in input_vars: 
                    consts[model.get_interp(d)] = d
                    # consts.append(d)
                # Is the it the name of a Function included in rules.py? 
                elif d.name() in dir(rules):  
                    functions.append(d)
                else: 
                    raise ValueError(f"Do not recognize this: {d.name()}")
        
        for f in functions: 
            if f.name() == 'Cause': 
                f_interp = model[f] # Get interpretation of f in this model
                num_entries = f_interp.num_entries()
                for i in range(num_entries):
                    (start, end, to_include) = f_interp.entry(i)
                    import pdb; pdb.set_trace()
            elif f.name() == 'Correlate': 
                pass
            elif f.name() == 'Interaction':
                pass
            else: 
                pass
    

    # TODO: START HERE: Probably some hybrid of above and below...
    # I need function name (to give me edge type), variable objects (to update edges to Graph: remove and replace)
    def postprocess_query_results(self, model: z3.ModelRef, updated_facts: List, input_obj: Union[Design], output_obj: Union[Graph]):
        
        def parse_facts(fact: z3.BoolRef) -> List[str]: 
            fact_dict = dict()
            tmp = str(fact).split('(')
            func_name = tmp[0] 
            fact_dict['function'] = func_name
            variables = tmp[1].split(')')[0].split(',')
            fact_dict['start'] = variables[0].strip()
            fact_dict['end'] = variables[1].strip()
            
            return fact_dict
        
        # def get_model_consts(model: z3.ModelRef, input_obj: Union[Design]): 
        #     consts = dict()

        #     # Iterate through the declarations in the model
        #     for d in model.decls(): 
        #         if isinstance(input_obj, Design): 
        #             input_vars = [v.name for v in input_obj.get_variables()]

        #             if d.name() in input_vars: 
        #                 consts[d.name()] = d
            
        #     return consts

        def get_var_names_to_variables(input_obj: Union[Design]): 
            var_names_to_variables = dict()

            if isinstance(input_obj, Design): 
                for v in input_obj.get_variables(): 
                    var_names_to_variables[v.name] = v

            return var_names_to_variables


        
        # var_name_to_consts = get_model_consts(model=model, input_obj=input_obj)
        # consts_to_variables = kwargs['consts_to_variables'] # TODO: May want to make this a named param instead of kwargs
        var_names_to_variables = get_var_names_to_variables(input_obj=input_obj)

        for f in updated_facts: 
            fact_dict = parse_facts(f)
            
            if isinstance(output_obj, Graph): 
                # Get variable names
                start_name = fact_dict['start']
                end_name = fact_dict['end']
                # # Look up consts that have variable names
                # start_const = var_name_to_consts[start_name]
                # end_const = var_name_to_consts[end_name]
                # # Look up variables associated with the consts
                # import pdb; pdb.set_trace()
                start_var = var_names_to_variables[start_name]
                end_var = var_names_to_variables[end_name]

                if fact_dict['function'] == 'Cause': 
                    output_obj.cause(start_var, end_var)
                elif fact_dict['function'] == 'Correlate': 
                    output_obj.correlate(start_var, end_var)
                if fact_dict['function'] == 'Interaction': 
                    # TODO: Should we add Interaction-specific edge??
                    output_obj.correlate(start_var, end_var)
            elif isinstance(output_obj, StatisticalModel): 
                # TODO: START HERE
                raise NotImplementedError
            elif isinstance(output_obj, Design): 
                raise NotImplementedError
            else: 
                raise ValueError (f"Unexpected @param output_obj: {output_obj}")
        
        return output_obj


            


            



    # # TODO: Multiple queries should be handled outside? maybe outcome as a list? 
    # def query(self, input_obj: Union[StatisticalModel], outcome: str): 

    #     # Set up 
    #     # Get and use Z3 consts created for the input_obj
    #     dv_const = input_obj.consts['dv']
    #     main_effects = input_obj.consts['main_effects']
    #     interactions = input_obj.consts['interactions']
    #     self.ground_rules(dv_const=dv_const, main_effects=main_effects, interactions=interactions)

    #     # Collect rules and facts
    #     rules = self.collect_rules(outcome=outcome) # dict
    #     facts = self.collect_facts(input_obj=input_obj, outcome=outcome, z3_consts=z3_consts)
    #     result = self.solve(facts=facts, rules=rules, setting=None)        
        
    #     # TODO: cast the result to a specific object? 

    #     return result

class Query(object): 
    rules : list # rules to consider
    facts : list # facts to consider while solving rules + facts
    
    def __init__(self, rules=list, facts=list): 
        self.rules = rules 
        self.facts = facts
    
    def solve(self): 
        pass

# Goal: just get the example working with last week working with current API/system
# 1. Query Manager (only the implementation that is absolutely necessary)
# 2. Variable Relationship Graph (should be clear if cause or correlate) [M]
# 3. Data Schema (should output clearly a data schema) [M]
# 4. Data collect procedure [T]

# Global QueryManager
QM = QueryManager()