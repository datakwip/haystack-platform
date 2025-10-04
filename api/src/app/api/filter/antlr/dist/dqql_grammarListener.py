# Generated from dqql_grammar.g4 by ANTLR 4.10.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .dqql_grammarParser import dqql_grammarParser
else:
    from dqql_grammarParser import dqql_grammarParser

# This class defines a complete listener for a parse tree produced by dqql_grammarParser.
class dqql_grammarListener(ParseTreeListener):

    # Enter a parse tree produced by dqql_grammarParser#expr.
    def enterExpr(self, ctx:dqql_grammarParser.ExprContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#expr.
    def exitExpr(self, ctx:dqql_grammarParser.ExprContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#cond.
    def enterCond(self, ctx:dqql_grammarParser.CondContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#cond.
    def exitCond(self, ctx:dqql_grammarParser.CondContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#LogicalConditionOr.
    def enterLogicalConditionOr(self, ctx:dqql_grammarParser.LogicalConditionOrContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#LogicalConditionOr.
    def exitLogicalConditionOr(self, ctx:dqql_grammarParser.LogicalConditionOrContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#LogicalConditionAnd.
    def enterLogicalConditionAnd(self, ctx:dqql_grammarParser.LogicalConditionAndContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#LogicalConditionAnd.
    def exitLogicalConditionAnd(self, ctx:dqql_grammarParser.LogicalConditionAndContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#term.
    def enterTerm(self, ctx:dqql_grammarParser.TermContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#term.
    def exitTerm(self, ctx:dqql_grammarParser.TermContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#LogicalParens.
    def enterLogicalParens(self, ctx:dqql_grammarParser.LogicalParensContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#LogicalParens.
    def exitLogicalParens(self, ctx:dqql_grammarParser.LogicalParensContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#LogicalHas.
    def enterLogicalHas(self, ctx:dqql_grammarParser.LogicalHasContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#LogicalHas.
    def exitLogicalHas(self, ctx:dqql_grammarParser.LogicalHasContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#LogicalMissing.
    def enterLogicalMissing(self, ctx:dqql_grammarParser.LogicalMissingContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#LogicalMissing.
    def exitLogicalMissing(self, ctx:dqql_grammarParser.LogicalMissingContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#LogicalCmp.
    def enterLogicalCmp(self, ctx:dqql_grammarParser.LogicalCmpContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#LogicalCmp.
    def exitLogicalCmp(self, ctx:dqql_grammarParser.LogicalCmpContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#InCmp.
    def enterInCmp(self, ctx:dqql_grammarParser.InCmpContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#InCmp.
    def exitInCmp(self, ctx:dqql_grammarParser.InCmpContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#cmpOp.
    def enterCmpOp(self, ctx:dqql_grammarParser.CmpOpContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#cmpOp.
    def exitCmpOp(self, ctx:dqql_grammarParser.CmpOpContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#LogicalPath.
    def enterLogicalPath(self, ctx:dqql_grammarParser.LogicalPathContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#LogicalPath.
    def exitLogicalPath(self, ctx:dqql_grammarParser.LogicalPathContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#val.
    def enterVal(self, ctx:dqql_grammarParser.ValContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#val.
    def exitVal(self, ctx:dqql_grammarParser.ValContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#elem.
    def enterElem(self, ctx:dqql_grammarParser.ElemContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#elem.
    def exitElem(self, ctx:dqql_grammarParser.ElemContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#elems.
    def enterElems(self, ctx:dqql_grammarParser.ElemsContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#elems.
    def exitElems(self, ctx:dqql_grammarParser.ElemsContext):
        pass


    # Enter a parse tree produced by dqql_grammarParser#list.
    def enterList(self, ctx:dqql_grammarParser.ListContext):
        pass

    # Exit a parse tree produced by dqql_grammarParser#list.
    def exitList(self, ctx:dqql_grammarParser.ListContext):
        pass



del dqql_grammarParser