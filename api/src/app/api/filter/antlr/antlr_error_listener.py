from antlr4.error.ErrorListener import ErrorListener

class AntlrError(Exception):
    """Base class for other exceptions"""
    pass



class AntlrErrorListener( ErrorListener ):

    def __init__(self):
        super(AntlrErrorListener, self).__init__()

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise AntlrError("{}:{} {}".format(line, column, msg))

    def reportAmbiguity(self, recognizer, dfa, startIndex, stopIndex, exact, ambigAlts, configs):
        raise AntlrError("{}:{}".format(startIndex, stopIndex))

    def reportAttemptingFullContext(self, recognizer, dfa, startIndex, stopIndex, conflictingAlts, configs):
        raise AntlrError("{}:{}".format(startIndex, stopIndex))

    def reportContextSensitivity(self, recognizer, dfa, startIndex, stopIndex, prediction, configs):
        raise AntlrError("{}:{}".format(startIndex, stopIndex))