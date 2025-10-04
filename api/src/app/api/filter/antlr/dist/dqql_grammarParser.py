# Generated from dqql_grammar.g4 by ANTLR 4.10.1
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,27,105,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,1,0,1,0,1,0,1,1,1,1,1,2,1,2,1,2,5,2,39,8,2,10,2,12,2,42,
        9,2,1,3,1,3,1,3,5,3,47,8,3,10,3,12,3,50,9,3,1,4,1,4,1,4,1,4,3,4,
        56,8,4,1,5,1,5,1,5,1,5,1,6,1,6,1,7,1,7,1,7,1,8,1,8,1,8,1,8,1,8,1,
        8,1,8,1,8,3,8,75,8,8,1,9,1,9,1,10,1,10,1,10,5,10,82,8,10,10,10,12,
        10,85,9,10,1,11,1,11,1,12,1,12,1,13,1,13,1,13,5,13,94,8,13,10,13,
        12,13,97,9,13,1,14,1,14,3,14,101,8,14,1,14,1,14,1,14,0,0,15,0,2,
        4,6,8,10,12,14,16,18,20,22,24,26,28,0,2,2,0,6,6,8,12,2,0,17,19,21,
        24,98,0,30,1,0,0,0,2,33,1,0,0,0,4,35,1,0,0,0,6,43,1,0,0,0,8,55,1,
        0,0,0,10,57,1,0,0,0,12,61,1,0,0,0,14,63,1,0,0,0,16,74,1,0,0,0,18,
        76,1,0,0,0,20,78,1,0,0,0,22,86,1,0,0,0,24,88,1,0,0,0,26,90,1,0,0,
        0,28,98,1,0,0,0,30,31,3,2,1,0,31,32,5,0,0,1,32,1,1,0,0,0,33,34,3,
        4,2,0,34,3,1,0,0,0,35,40,3,6,3,0,36,37,5,15,0,0,37,39,3,6,3,0,38,
        36,1,0,0,0,39,42,1,0,0,0,40,38,1,0,0,0,40,41,1,0,0,0,41,5,1,0,0,
        0,42,40,1,0,0,0,43,48,3,8,4,0,44,45,5,14,0,0,45,47,3,8,4,0,46,44,
        1,0,0,0,47,50,1,0,0,0,48,46,1,0,0,0,48,49,1,0,0,0,49,7,1,0,0,0,50,
        48,1,0,0,0,51,56,3,10,5,0,52,56,3,12,6,0,53,56,3,14,7,0,54,56,3,
        16,8,0,55,51,1,0,0,0,55,52,1,0,0,0,55,53,1,0,0,0,55,54,1,0,0,0,56,
        9,1,0,0,0,57,58,5,4,0,0,58,59,3,2,1,0,59,60,5,5,0,0,60,11,1,0,0,
        0,61,62,3,20,10,0,62,13,1,0,0,0,63,64,5,16,0,0,64,65,3,20,10,0,65,
        15,1,0,0,0,66,67,3,20,10,0,67,68,3,18,9,0,68,69,3,22,11,0,69,75,
        1,0,0,0,70,71,3,20,10,0,71,72,5,7,0,0,72,73,3,28,14,0,73,75,1,0,
        0,0,74,66,1,0,0,0,74,70,1,0,0,0,75,17,1,0,0,0,76,77,7,0,0,0,77,19,
        1,0,0,0,78,83,5,25,0,0,79,80,5,13,0,0,80,82,5,25,0,0,81,79,1,0,0,
        0,82,85,1,0,0,0,83,81,1,0,0,0,83,84,1,0,0,0,84,21,1,0,0,0,85,83,
        1,0,0,0,86,87,7,1,0,0,87,23,1,0,0,0,88,89,5,20,0,0,89,25,1,0,0,0,
        90,95,3,24,12,0,91,92,5,26,0,0,92,94,3,24,12,0,93,91,1,0,0,0,94,
        97,1,0,0,0,95,93,1,0,0,0,95,96,1,0,0,0,96,27,1,0,0,0,97,95,1,0,0,
        0,98,100,5,4,0,0,99,101,3,26,13,0,100,99,1,0,0,0,100,101,1,0,0,0,
        101,102,1,0,0,0,102,103,5,5,0,0,103,29,1,0,0,0,7,40,48,55,74,83,
        95,100
    ]

class dqql_grammarParser ( Parser ):

    grammarFileName = "dqql_grammar.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'.'", "'_'", "'-'", "'('", "')'", "'=='", 
                     "'IN'", "'<'", "'>'", "'<='", "'>='", "'!='", "'->'", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "','" ]

    symbolicNames = [ "<INVALID>", "DOT", "UNDERSCORE", "MINUS", "LPAREN", 
                      "RPAREN", "EQ", "IN", "LT", "GT", "LE", "GE", "NEQ", 
                      "ARROW", "AND", "OR", "NOT", "BOOL", "REF", "STR", 
                      "INSTR", "URI", "NUMBER", "DATE", "TIME", "NAME", 
                      "SEP", "SPACES" ]

    RULE_expr = 0
    RULE_cond = 1
    RULE_condOr = 2
    RULE_condAnd = 3
    RULE_term = 4
    RULE_parens = 5
    RULE_has = 6
    RULE_missing = 7
    RULE_cmp = 8
    RULE_cmpOp = 9
    RULE_path = 10
    RULE_val = 11
    RULE_elem = 12
    RULE_elems = 13
    RULE_list = 14

    ruleNames =  [ "expr", "cond", "condOr", "condAnd", "term", "parens", 
                   "has", "missing", "cmp", "cmpOp", "path", "val", "elem", 
                   "elems", "list" ]

    EOF = Token.EOF
    DOT=1
    UNDERSCORE=2
    MINUS=3
    LPAREN=4
    RPAREN=5
    EQ=6
    IN=7
    LT=8
    GT=9
    LE=10
    GE=11
    NEQ=12
    ARROW=13
    AND=14
    OR=15
    NOT=16
    BOOL=17
    REF=18
    STR=19
    INSTR=20
    URI=21
    NUMBER=22
    DATE=23
    TIME=24
    NAME=25
    SEP=26
    SPACES=27

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.10.1")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class ExprContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def cond(self):
            return self.getTypedRuleContext(dqql_grammarParser.CondContext,0)


        def EOF(self):
            return self.getToken(dqql_grammarParser.EOF, 0)

        def getRuleIndex(self):
            return dqql_grammarParser.RULE_expr

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterExpr" ):
                listener.enterExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitExpr" ):
                listener.exitExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExpr" ):
                return visitor.visitExpr(self)
            else:
                return visitor.visitChildren(self)




    def expr(self):

        localctx = dqql_grammarParser.ExprContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_expr)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 30
            self.cond()
            self.state = 31
            self.match(dqql_grammarParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CondContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def condOr(self):
            return self.getTypedRuleContext(dqql_grammarParser.CondOrContext,0)


        def getRuleIndex(self):
            return dqql_grammarParser.RULE_cond

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCond" ):
                listener.enterCond(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCond" ):
                listener.exitCond(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCond" ):
                return visitor.visitCond(self)
            else:
                return visitor.visitChildren(self)




    def cond(self):

        localctx = dqql_grammarParser.CondContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_cond)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 33
            self.condOr()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CondOrContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return dqql_grammarParser.RULE_condOr

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class LogicalConditionOrContext(CondOrContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a dqql_grammarParser.CondOrContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def condAnd(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(dqql_grammarParser.CondAndContext)
            else:
                return self.getTypedRuleContext(dqql_grammarParser.CondAndContext,i)

        def OR(self, i:int=None):
            if i is None:
                return self.getTokens(dqql_grammarParser.OR)
            else:
                return self.getToken(dqql_grammarParser.OR, i)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLogicalConditionOr" ):
                listener.enterLogicalConditionOr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLogicalConditionOr" ):
                listener.exitLogicalConditionOr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLogicalConditionOr" ):
                return visitor.visitLogicalConditionOr(self)
            else:
                return visitor.visitChildren(self)



    def condOr(self):

        localctx = dqql_grammarParser.CondOrContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_condOr)
        self._la = 0 # Token type
        try:
            localctx = dqql_grammarParser.LogicalConditionOrContext(self, localctx)
            self.enterOuterAlt(localctx, 1)
            self.state = 35
            self.condAnd()
            self.state = 40
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==dqql_grammarParser.OR:
                self.state = 36
                self.match(dqql_grammarParser.OR)
                self.state = 37
                self.condAnd()
                self.state = 42
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CondAndContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return dqql_grammarParser.RULE_condAnd

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class LogicalConditionAndContext(CondAndContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a dqql_grammarParser.CondAndContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def term(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(dqql_grammarParser.TermContext)
            else:
                return self.getTypedRuleContext(dqql_grammarParser.TermContext,i)

        def AND(self, i:int=None):
            if i is None:
                return self.getTokens(dqql_grammarParser.AND)
            else:
                return self.getToken(dqql_grammarParser.AND, i)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLogicalConditionAnd" ):
                listener.enterLogicalConditionAnd(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLogicalConditionAnd" ):
                listener.exitLogicalConditionAnd(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLogicalConditionAnd" ):
                return visitor.visitLogicalConditionAnd(self)
            else:
                return visitor.visitChildren(self)



    def condAnd(self):

        localctx = dqql_grammarParser.CondAndContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_condAnd)
        self._la = 0 # Token type
        try:
            localctx = dqql_grammarParser.LogicalConditionAndContext(self, localctx)
            self.enterOuterAlt(localctx, 1)
            self.state = 43
            self.term()
            self.state = 48
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==dqql_grammarParser.AND:
                self.state = 44
                self.match(dqql_grammarParser.AND)
                self.state = 45
                self.term()
                self.state = 50
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TermContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def parens(self):
            return self.getTypedRuleContext(dqql_grammarParser.ParensContext,0)


        def has(self):
            return self.getTypedRuleContext(dqql_grammarParser.HasContext,0)


        def missing(self):
            return self.getTypedRuleContext(dqql_grammarParser.MissingContext,0)


        def cmp(self):
            return self.getTypedRuleContext(dqql_grammarParser.CmpContext,0)


        def getRuleIndex(self):
            return dqql_grammarParser.RULE_term

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTerm" ):
                listener.enterTerm(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTerm" ):
                listener.exitTerm(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTerm" ):
                return visitor.visitTerm(self)
            else:
                return visitor.visitChildren(self)




    def term(self):

        localctx = dqql_grammarParser.TermContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_term)
        try:
            self.state = 55
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,2,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 51
                self.parens()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 52
                self.has()
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 53
                self.missing()
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 54
                self.cmp()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ParensContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return dqql_grammarParser.RULE_parens

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class LogicalParensContext(ParensContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a dqql_grammarParser.ParensContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def LPAREN(self):
            return self.getToken(dqql_grammarParser.LPAREN, 0)
        def cond(self):
            return self.getTypedRuleContext(dqql_grammarParser.CondContext,0)

        def RPAREN(self):
            return self.getToken(dqql_grammarParser.RPAREN, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLogicalParens" ):
                listener.enterLogicalParens(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLogicalParens" ):
                listener.exitLogicalParens(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLogicalParens" ):
                return visitor.visitLogicalParens(self)
            else:
                return visitor.visitChildren(self)



    def parens(self):

        localctx = dqql_grammarParser.ParensContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_parens)
        try:
            localctx = dqql_grammarParser.LogicalParensContext(self, localctx)
            self.enterOuterAlt(localctx, 1)
            self.state = 57
            self.match(dqql_grammarParser.LPAREN)
            self.state = 58
            self.cond()
            self.state = 59
            self.match(dqql_grammarParser.RPAREN)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class HasContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return dqql_grammarParser.RULE_has

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class LogicalHasContext(HasContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a dqql_grammarParser.HasContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def path(self):
            return self.getTypedRuleContext(dqql_grammarParser.PathContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLogicalHas" ):
                listener.enterLogicalHas(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLogicalHas" ):
                listener.exitLogicalHas(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLogicalHas" ):
                return visitor.visitLogicalHas(self)
            else:
                return visitor.visitChildren(self)



    def has(self):

        localctx = dqql_grammarParser.HasContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_has)
        try:
            localctx = dqql_grammarParser.LogicalHasContext(self, localctx)
            self.enterOuterAlt(localctx, 1)
            self.state = 61
            self.path()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MissingContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return dqql_grammarParser.RULE_missing

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class LogicalMissingContext(MissingContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a dqql_grammarParser.MissingContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def NOT(self):
            return self.getToken(dqql_grammarParser.NOT, 0)
        def path(self):
            return self.getTypedRuleContext(dqql_grammarParser.PathContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLogicalMissing" ):
                listener.enterLogicalMissing(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLogicalMissing" ):
                listener.exitLogicalMissing(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLogicalMissing" ):
                return visitor.visitLogicalMissing(self)
            else:
                return visitor.visitChildren(self)



    def missing(self):

        localctx = dqql_grammarParser.MissingContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_missing)
        try:
            localctx = dqql_grammarParser.LogicalMissingContext(self, localctx)
            self.enterOuterAlt(localctx, 1)
            self.state = 63
            self.match(dqql_grammarParser.NOT)
            self.state = 64
            self.path()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CmpContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return dqql_grammarParser.RULE_cmp

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class LogicalCmpContext(CmpContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a dqql_grammarParser.CmpContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def path(self):
            return self.getTypedRuleContext(dqql_grammarParser.PathContext,0)

        def cmpOp(self):
            return self.getTypedRuleContext(dqql_grammarParser.CmpOpContext,0)

        def val(self):
            return self.getTypedRuleContext(dqql_grammarParser.ValContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLogicalCmp" ):
                listener.enterLogicalCmp(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLogicalCmp" ):
                listener.exitLogicalCmp(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLogicalCmp" ):
                return visitor.visitLogicalCmp(self)
            else:
                return visitor.visitChildren(self)


    class InCmpContext(CmpContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a dqql_grammarParser.CmpContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def path(self):
            return self.getTypedRuleContext(dqql_grammarParser.PathContext,0)

        def IN(self):
            return self.getToken(dqql_grammarParser.IN, 0)
        def list_(self):
            return self.getTypedRuleContext(dqql_grammarParser.ListContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterInCmp" ):
                listener.enterInCmp(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitInCmp" ):
                listener.exitInCmp(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInCmp" ):
                return visitor.visitInCmp(self)
            else:
                return visitor.visitChildren(self)



    def cmp(self):

        localctx = dqql_grammarParser.CmpContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_cmp)
        try:
            self.state = 74
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,3,self._ctx)
            if la_ == 1:
                localctx = dqql_grammarParser.LogicalCmpContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 66
                self.path()
                self.state = 67
                self.cmpOp()
                self.state = 68
                self.val()
                pass

            elif la_ == 2:
                localctx = dqql_grammarParser.InCmpContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 70
                self.path()
                self.state = 71
                self.match(dqql_grammarParser.IN)
                self.state = 72
                self.list_()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CmpOpContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EQ(self):
            return self.getToken(dqql_grammarParser.EQ, 0)

        def LE(self):
            return self.getToken(dqql_grammarParser.LE, 0)

        def GE(self):
            return self.getToken(dqql_grammarParser.GE, 0)

        def LT(self):
            return self.getToken(dqql_grammarParser.LT, 0)

        def GT(self):
            return self.getToken(dqql_grammarParser.GT, 0)

        def NEQ(self):
            return self.getToken(dqql_grammarParser.NEQ, 0)

        def getRuleIndex(self):
            return dqql_grammarParser.RULE_cmpOp

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCmpOp" ):
                listener.enterCmpOp(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCmpOp" ):
                listener.exitCmpOp(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCmpOp" ):
                return visitor.visitCmpOp(self)
            else:
                return visitor.visitChildren(self)




    def cmpOp(self):

        localctx = dqql_grammarParser.CmpOpContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_cmpOp)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 76
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << dqql_grammarParser.EQ) | (1 << dqql_grammarParser.LT) | (1 << dqql_grammarParser.GT) | (1 << dqql_grammarParser.LE) | (1 << dqql_grammarParser.GE) | (1 << dqql_grammarParser.NEQ))) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PathContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return dqql_grammarParser.RULE_path

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class LogicalPathContext(PathContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a dqql_grammarParser.PathContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def NAME(self, i:int=None):
            if i is None:
                return self.getTokens(dqql_grammarParser.NAME)
            else:
                return self.getToken(dqql_grammarParser.NAME, i)
        def ARROW(self, i:int=None):
            if i is None:
                return self.getTokens(dqql_grammarParser.ARROW)
            else:
                return self.getToken(dqql_grammarParser.ARROW, i)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLogicalPath" ):
                listener.enterLogicalPath(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLogicalPath" ):
                listener.exitLogicalPath(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLogicalPath" ):
                return visitor.visitLogicalPath(self)
            else:
                return visitor.visitChildren(self)



    def path(self):

        localctx = dqql_grammarParser.PathContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_path)
        self._la = 0 # Token type
        try:
            localctx = dqql_grammarParser.LogicalPathContext(self, localctx)
            self.enterOuterAlt(localctx, 1)
            self.state = 78
            self.match(dqql_grammarParser.NAME)
            self.state = 83
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==dqql_grammarParser.ARROW:
                self.state = 79
                self.match(dqql_grammarParser.ARROW)
                self.state = 80
                self.match(dqql_grammarParser.NAME)
                self.state = 85
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ValContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def BOOL(self):
            return self.getToken(dqql_grammarParser.BOOL, 0)

        def REF(self):
            return self.getToken(dqql_grammarParser.REF, 0)

        def STR(self):
            return self.getToken(dqql_grammarParser.STR, 0)

        def URI(self):
            return self.getToken(dqql_grammarParser.URI, 0)

        def NUMBER(self):
            return self.getToken(dqql_grammarParser.NUMBER, 0)

        def DATE(self):
            return self.getToken(dqql_grammarParser.DATE, 0)

        def TIME(self):
            return self.getToken(dqql_grammarParser.TIME, 0)

        def getRuleIndex(self):
            return dqql_grammarParser.RULE_val

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVal" ):
                listener.enterVal(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVal" ):
                listener.exitVal(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVal" ):
                return visitor.visitVal(self)
            else:
                return visitor.visitChildren(self)




    def val(self):

        localctx = dqql_grammarParser.ValContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_val)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 86
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << dqql_grammarParser.BOOL) | (1 << dqql_grammarParser.REF) | (1 << dqql_grammarParser.STR) | (1 << dqql_grammarParser.URI) | (1 << dqql_grammarParser.NUMBER) | (1 << dqql_grammarParser.DATE) | (1 << dqql_grammarParser.TIME))) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ElemContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INSTR(self):
            return self.getToken(dqql_grammarParser.INSTR, 0)

        def getRuleIndex(self):
            return dqql_grammarParser.RULE_elem

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterElem" ):
                listener.enterElem(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitElem" ):
                listener.exitElem(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitElem" ):
                return visitor.visitElem(self)
            else:
                return visitor.visitChildren(self)




    def elem(self):

        localctx = dqql_grammarParser.ElemContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_elem)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 88
            self.match(dqql_grammarParser.INSTR)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ElemsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def elem(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(dqql_grammarParser.ElemContext)
            else:
                return self.getTypedRuleContext(dqql_grammarParser.ElemContext,i)


        def SEP(self, i:int=None):
            if i is None:
                return self.getTokens(dqql_grammarParser.SEP)
            else:
                return self.getToken(dqql_grammarParser.SEP, i)

        def getRuleIndex(self):
            return dqql_grammarParser.RULE_elems

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterElems" ):
                listener.enterElems(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitElems" ):
                listener.exitElems(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitElems" ):
                return visitor.visitElems(self)
            else:
                return visitor.visitChildren(self)




    def elems(self):

        localctx = dqql_grammarParser.ElemsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_elems)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 90
            self.elem()
            self.state = 95
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==dqql_grammarParser.SEP:
                self.state = 91
                self.match(dqql_grammarParser.SEP)
                self.state = 92
                self.elem()
                self.state = 97
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LPAREN(self):
            return self.getToken(dqql_grammarParser.LPAREN, 0)

        def RPAREN(self):
            return self.getToken(dqql_grammarParser.RPAREN, 0)

        def elems(self):
            return self.getTypedRuleContext(dqql_grammarParser.ElemsContext,0)


        def getRuleIndex(self):
            return dqql_grammarParser.RULE_list

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterList" ):
                listener.enterList(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitList" ):
                listener.exitList(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitList" ):
                return visitor.visitList(self)
            else:
                return visitor.visitChildren(self)




    def list_(self):

        localctx = dqql_grammarParser.ListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_list)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 98
            self.match(dqql_grammarParser.LPAREN)
            self.state = 100
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==dqql_grammarParser.INSTR:
                self.state = 99
                self.elems()


            self.state = 102
            self.match(dqql_grammarParser.RPAREN)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





