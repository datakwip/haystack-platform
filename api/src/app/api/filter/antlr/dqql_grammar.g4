grammar dqql_grammar;

DOT : '.';
UNDERSCORE : '_';
MINUS : '-';
LPAREN : '(';
RPAREN : ')';
EQ : '==';
IN : 'IN';
LT : '<';
GT : '>';
LE : '<=';
GE : '>=';
NEQ :'!=';
ARROW : '->';
AND : 'AND' | 'and';
OR  : 'OR'  | 'or';
NOT : 'NOT' | 'not';
BOOL : 'TRUE' | 'FALSE';
/* Grammar rules */

expr : cond EOF ;

cond : condOr;

condOr
        : condAnd (OR condAnd)* # LogicalConditionOr
;

condAnd
    : term (AND term)* # LogicalConditionAnd
    ;

term
    : parens
    | has
    | missing
    | cmp
    ;

parens
    : LPAREN cond RPAREN #LogicalParens
    ;

has
    : path #LogicalHas
    ;

missing
    : NOT path #LogicalMissing
    ;

cmp
    : path cmpOp val #LogicalCmp
    | path IN list #InCmp
    ;

cmpOp
    : EQ
    | LE
    | GE
    | LT
    | GT
    | NEQ
    ;

path
    : NAME (ARROW NAME)* #LogicalPath
    ;
val
    : BOOL
    | REF
    | STR
    | URI
    | NUMBER
    | DATE
    | TIME
    ;

REF : '@' REFCHAR+;
STR : '"' (~'"' | '\\"' )* '"'
    ;

INSTR : '\'' (~('\\'|'\'') )* '\''
    ;
URI : '`' ALPHA* '`';
NUMBER : DECIMAL;
DATE : YEAR '-' MONTH '-' TODAY;
TIME : DIGIT DIGIT ':' DIGIT DIGIT;
NAME : ALPHALO (ALPHALO | ALPHAHI | DIGIT | '_')*;
SEP  : ',';
elem
 : INSTR
 ;
elems
 : elem ( SEP elem )*
 ;
list
 : LPAREN elems? RPAREN
 ;

SPACES
 : [ \u000B\t\r\n] -> channel(HIDDEN)
 ;

fragment ALPHALO : [a-z];
fragment ALPHAHI : [A-Z];
fragment DECIMAL : UNDERSCORE? DIGITS DOT? DIGITS? ('e'|'E' '+'|'-' DIGITS)? ;
fragment DIGITS : DIGIT (DIGIT | UNDERSCORE)*;
fragment DIGIT : [0-9];
fragment ALPHA : ALPHAHI | ALPHALO;
fragment REFCHAR     : ALPHA | DIGIT | UNDERSCORE | ';' | '-' | '.' | '~';
fragment UNIT: (UNITCHAR)*;
fragment UNITCHAR    : ALPHA | '%' | '_' |  '/' | '$';
fragment YEAR : DIGIT DIGIT DIGIT DIGIT;
fragment MONTH : DIGIT DIGIT;
fragment TODAY : DIGIT DIGIT;