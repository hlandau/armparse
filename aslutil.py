from typing import NamedTuple

class ASL(object):
  def __init__(self, name, rep_section, code, defs, deps):
    self.name = name
    self.rep_section = rep_section
    self.code = code
    self.defs = defs
    self.deps = deps

  def __str__(self):
    return 'ASL{' + ', '.join([self.name, self.rep_section, str(self.defs), str(self.deps)]) + '}'

# Lexing utilities.
class TokenType(object):
  def __init__(self, name):
    self.name = name

  def __repr__(self):
    return 'TokenType(%s)' % self.name

tokEOF       = TokenType('EOF')
tokLPAREN    = TokenType('(')
tokRPAREN    = TokenType(')')
tokSEMICOLON = TokenType(';')
tokCOLON     = TokenType(':')
tokLT        = TokenType('<')
tokLE        = TokenType('<=')
tokGT        = TokenType('>')
tokGE        = TokenType('>=')
tokCOMMA     = TokenType(',')
tokPERIOD    = TokenType('.')
tokPERIODPERIOD = TokenType('..')
tokSLASH     = TokenType('/')
tokAMPERSAND = TokenType('&')
tokPIPE      = TokenType('|')
tokLAND      = TokenType('&&')
tokLOR       = TokenType('||')
tokBANG      = TokenType('!')
tokEQ        = TokenType('=')
tokEQEQ      = TokenType('==')
tokNE        = TokenType('!=')
tokPLUS      = TokenType('+')
tokMINUS     = TokenType('-')
tokASTERISK  = TokenType('*')
tokCARET     = TokenType('^')
tokLBRACKET  = TokenType('[')
tokRBRACKET  = TokenType(']')
tokLBRACE    = TokenType('{')
tokRBRACE    = TokenType('}')
tokINDENT    = TokenType('INDENT')
tokDEDENT    = TokenType('DEDENT')
tokLSH       = TokenType('<<')
tokRSH       = TokenType('>>')
tokPLUSCOLON = TokenType('+:')

tokQSTRING   = TokenType('QSTRING')
tokBITSTRING = TokenType('BITSTRING')
tokBITMATCH  = TokenType('BITMATCH')
tokINT       = TokenType('INTEGER')
tokFLOAT     = TokenType('FLOAT')
tokIDENT     = TokenType('IDENT')

keywords = dict()
for k in ['if', 'then', 'TRUE', 'FALSE', 'enumeration', 'type', 'is', 'bits', 'integer', 'boolean', 'real', 'bit', 'array', 'of', 'elsif', 'else', 'when', 'AND', 'OR', 'EOR', 'MOD', 'DIV', 'case', 'repeat', 'while', 'for', 'try', 'catch', 'UNDEFINED', 'UNPREDICTABLE', 'IMPLEMENTATION_DEFINED', 'CONSTRAINED_UNPREDICTABLE', 'SEE', 'IMPDEF', 'return', 'assert', 'IN', 'UNKNOWN', 'to', 'constant', 'otherwise', 'until', 'do', 'downto', 'NOT', 'REM']:
  keywords[k] = TokenType(k)

class Token(object):
  __slots__ = ['type', 'arg', 'lineNo', 'colNo']

  def __init__(self, type, arg=None, lineNo=None, colNo=None):
    self.type = type
    self.arg = arg
    self.lineNo = lineNo
    self.colNo = colNo

  def __repr__(self):
    return 'Token(%s, %s, %s:%s)' % (repr(self.type), repr(self.arg), self.lineNo, self.colNo)


# Represents a failure of a parse function.
class ParseFailure(NamedTuple):
  msg: str
  token: object = None

def reprNode(x, indent=0):
  if isinstance(x, Node):
    s = 'Node(%s)\n' % x.type
    for c in x.children:
      s += '  '*(indent+1)
      s += reprNode(c, indent+1)
      s += '\n'
    return s.rstrip('\n')
  elif isinstance(x, list) or isinstance(x, tuple):
    s = 'List\n'
    for c in x:
      s += '  '*(indent+1)
      s += reprNode(c, indent+1)
      s += '\n'
    return s.rstrip('\n')
  else:
    return repr(x)

# Represents an AST node.
class Node(NamedTuple):
  type: str
  children: tuple

  def __repr__(self):
    return reprNode(self)

#    def xrepr(x):
#      if isinstance(x, Node):
#        return 'NODE'
#      else:
#        return repr(x)
#
#    s = 'Node(%s)' % self.type
#    for x in self.children:
#      s += '\n  %s' % xrepr(x)
#    return s

def isFailure(x):
  return x is None or isinstance(x, ParseFailure)

def isNode(x):
  return isinstance(x, Node)

class Type(object):
  def __init__(self, name, n=None):
    self.name = name
    self.n = None

  def __repr__(self):
    return 'Type(%s)' % self.name

tBoolean = Type('boolean')
tInteger = Type('integer')
tReal    = Type('real')
