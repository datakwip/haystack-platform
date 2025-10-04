# Generated from dqql_grammar.g4 by ANTLR 4.10.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .dqql_grammarParser import dqql_grammarParser
else:
    from dqql_grammarParser import dqql_grammarParser

# This class defines a complete generic visitor for a parse tree produced by dqql_grammarParser.

class dqql_grammarVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by dqql_grammarParser#expr.
    def visitExpr(self, ctx:dqql_grammarParser.ExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#cond.
    def visitCond(self, ctx:dqql_grammarParser.CondContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#LogicalConditionOr.
    def visitLogicalConditionOr(self, ctx:dqql_grammarParser.LogicalConditionOrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#LogicalConditionAnd.
    def visitLogicalConditionAnd(self, ctx:dqql_grammarParser.LogicalConditionAndContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#term.
    def visitTerm(self, ctx:dqql_grammarParser.TermContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#LogicalParens.
    def visitLogicalParens(self, ctx:dqql_grammarParser.LogicalParensContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#LogicalHas.
    def visitLogicalHas(self, ctx:dqql_grammarParser.LogicalHasContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#LogicalMissing.
    def visitLogicalMissing(self, ctx:dqql_grammarParser.LogicalMissingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#LogicalCmp.
    def visitLogicalCmp(self, ctx:dqql_grammarParser.LogicalCmpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#InCmp.
    def visitInCmp(self, ctx:dqql_grammarParser.InCmpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#cmpOp.
    def visitCmpOp(self, ctx:dqql_grammarParser.CmpOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#LogicalPath.
    def visitLogicalPath(self, ctx:dqql_grammarParser.LogicalPathContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#val.
    def visitVal(self, ctx:dqql_grammarParser.ValContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#elem.
    def visitElem(self, ctx:dqql_grammarParser.ElemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#elems.
    def visitElems(self, ctx:dqql_grammarParser.ElemsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by dqql_grammarParser#list.
    def visitList(self, ctx:dqql_grammarParser.ListContext):
        return self.visitChildren(ctx)



del dqql_grammarParser