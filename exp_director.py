import sys
from textwrap import dedent
from copy import copy, deepcopy
from clingo.application import Application, clingo_main
from clingo.ast import ProgramBuilder, Transformer, ASTType, Aggregate, Guard, ComparisonOperator, Rule, Disjunction, Function, ConditionalLiteral, SymbolicTerm, Sign, parse_files, parse_string
from clingo.backend import Observer
from clingo.symbol import parse_term
import clingo.symbol as clisym

# import constraint_handler
# import constraint_handler.unsatCoreSupport as ch_usc


class ExplanationTransformer(Transformer):

    def __init__(self, explainables):
        self._explainables = explainables


    def visit_Rule(self, ast):
        is_marked_for_explanation = False

        for lit in ast.body:
            if (lit.ast_type == ASTType.Literal and
               lit.atom.ast_type == ASTType.SymbolicAtom and
               lit.atom.symbol.ast_type == ASTType.Function and
                    lit.atom.symbol.name == "_explain"):
                exp_lit = deepcopy(lit)
                exp_lit.atom.symbol.name = "_exp"
                exp_lit.sign = Sign.NoSign
                is_marked_for_explanation =True
                break

        # print("Explanation mark:", is_marked_for_explanation)
        # print(ast)
        if  is_marked_for_explanation:
            new_rule = Rule(ast.location,
                            Aggregate(ast.location,
                                      Guard(ComparisonOperator.LessEqual, SymbolicTerm(ast.location, parse_term("1"))),
                                      [ConditionalLiteral(ast.location, ast.head, []),
                                       ConditionalLiteral(ast.location, exp_lit, [])],
                                      Guard(ComparisonOperator.LessEqual, SymbolicTerm(ast.location, parse_term("1")))),
                            ast.body)
            # print(new_rule)
            return new_rule
        return ast


    ## def visit_Rule(self, ast):
    ##     fact = False
    ##     if not ast.body and ast.head.ast_type == ASTType.Literal:
    ##         # it is a fact
    ##         fact = True
    ##     t_ast = ast.update(**self.visit_children(ast,fact))
    ##     if fact and (ast is not t_ast):
    ##         # it is a fact that has been transformed
    ##         return Rule(ast.location,
    ##                     Disjunction(ast.location,
    ##                                 [ConditionalLiteral(ast.location, ast.head, []), ConditionalLiteral(ast.location, t_ast.head, [])]
    ##                                 ),[])
    ##     else:
    ##         return t_ast

    ## def visit_Function(self, ast, is_fact):
    ##     # print(ast, is_fact)
    ##     if is_fact:
    ##         name, argc = str(ast.name), len(ast.arguments)
    ##         if (name,argc) in self._explainables:
    ##             ast = ast.update(name="_exp", arguments=[Function(ast.location, ast.name, ast.arguments, 0)])
    ##     return ast

    #def visit(self, ast):
    #    print(ast.ast_type)
    #    if (ast.ast_type == ASTType.Rule):
    #        # print(ast.head.sign)
    #        print(ast.head.ast_type)
    #        print("Head is ", ast.head)
    #        if ast.head is None:
    #            print("Constraint rule...")
    #        print(repr(ast.head))
    #        if ast.head.ast_type == ASTType.Disjunction:
    #            print(ast.head.elements)
    #        print(ast.body)
    #    return ast


class ExpObserver(Observer):

    def rule(self, choice, head, body):
        # print(choice, head, body)
        pass

    def theory_term_string(self, term_id, name):
        print(term_id, name)


class ExpDirectorProto(Application):

    def __init__(self):
        self.program_name = "exp_director"
        self.version = "0.1"
        self._explainables = []
        self._num_of_assumptions = 10
        self._assumption_budget = []
        self._mapping = {}
        self._current_core = []

    def parse_explainables(self, val):
        preds = val.split()
        for p in preds:
            idx = p.find('/')
            self._explainables.append((p[:idx],int(p[idx+1:])))
        print(self._explainables)
        return True

    def set_number_of_assumptions(self, val):
        self._num_of_assumptions = int(val)
        return True

    def _create_assumption_budget(self, ctl, num):
        with ctl.backend() as backend:
            for i in range(num):
                sym = clisym.Function("assumption"+str(i+1))
                atm = backend.add_atom(sym)
                self._assumption_budget.append(atm)
                backend.add_rule(head=[atm], choice=True)

    def _use_assumption_budget(self, ctl):
        print("Setting the assumptions...")
        with ctl.backend() as backend:
            idx = 0
            for a in ctl.symbolic_atoms.by_signature("_exp",2):
                print(a.symbol, a.literal, "mapped to", self._assumption_budget[idx])
                backend.add_rule(head=[], body=[a.literal, self._assumption_budget[idx]])       # :- _exp(...), assumptionX.
                backend.add_rule(head=[a.literal], body=[-1*self._assumption_budget[idx]], choice=False)  # _exp(...) :- not assumptionX.
                # backend.add_rule(head=[], body=[-1*a.literal, -1*self._assumption_budget[idx]]) # :- not _exp(...), not assumptionX.
                if self._assumption_budget[idx] in self._mapping:
                    self._mapping[self._assumption_budget[idx]].append(a)
                else:
                    self._mapping[self._assumption_budget[idx]] = [a]
                if (idx+1) < len(self._assumption_budget):
                    idx += 1

    def register_options(self, options):
        group = "Explanation director options"

        options.add(
            group,
            "explainables",
            dedent(
                """\
                Explainable predicates. 
                """
            ),
            self.parse_explainables,
            argument="<explainables>",
        )

        options.add(
            group,
            "assumpt-num",
            dedent(
                """\
                Set the number of assumptions in the budget.
                """
            ),
            self.set_number_of_assumptions,
            argument="<num-of-assumptions>",
        )


    def _minimize_core(self, ctl):
        is_corelit_used = {lit: False for lit in self._current_core}
        core_minimized = False

        while not core_minimized:
            current_lit = next(lit for lit in self._current_core if not is_corelit_used[lit])
            self._current_core.remove(current_lit)
            is_corelit_used[current_lit] = True

            #res = ctl.solve(assumptions=[l for l in self._assumption_budget if l != current_lit], on_core=self._on_core)
            res = ctl.solve(assumptions=self._current_core, on_core=self._on_core)
            if res.unsatisfiable:
                print(current_lit,"is not in the minimal core")
                print("Current core:")
                self.print_core()
                pass
            else:
                print(current_lit,"is in the minimal core")
                self._current_core.append(current_lit)

            core_minimized = all((is_corelit_used[lit] for lit in self._current_core))
            print("================")


    def print_core(self):
        for l in self._current_core:
            if l in self._mapping:
                print(l, [str(a.symbol) for a in self._mapping[l]])
                # print(l, [str(a) for a in self._mapping[l]])


    def _on_core(self, core):
        self._current_core = core


    def main(self, ctl, files):
        self._create_assumption_budget(ctl,self._num_of_assumptions)

        if not files:
            files = ["-"]

        with ProgramBuilder(ctl) as bld:
            # constraint_handler.add_encoding_to_program_builder(bld)
            fr = ExplanationTransformer(self._explainables)
            parse_files(files, lambda stm: bld.add(fr.visit(stm)))


        ctl.register_observer(ExpObserver())
        ctl.ground([("base", [])])
        self._use_assumption_budget(ctl)

        ## chexplainMap = dict()
        ## for atom in ctl.symbolic_atoms.by_signature("explain_please", 1):
        ##     chexplainMap[atom.literal] = atom.symbol.arguments[0]
        ## assumptionMap = ch_usc.get_assumptions(ctl)
        ## ch_usc.relax(ctl,chexplainMap.values())
        ## readable = { key : [val] for key,val in assumptionMap.items() }
        ## new_assumptions = assumptionMap.keys()
        ## self._mapping.update(readable)
        ## self._assumption_budget += new_assumptions

        ctl.solve(on_core=self._on_core, assumptions=self._assumption_budget)

        print("First core:", self._current_core)
        self.print_core()
        if self._current_core:
            self._minimize_core(ctl)
        print("Minimal core:")
        self.print_core()

if __name__ == "__main__":
    sys.exit(int(clingo_main(ExpDirectorProto(), sys.argv[1:])))
