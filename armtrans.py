#!/usr/bin/env python3
import sys, pickle
from aslutil import Node, Type, Token
import ast, astor


n = ast.UnaryOp()
n.op = ast.USub()
n.operand = ast.Num()
n.operand.n = 5

def visit(n, f):
  assert isinstance(n, Node)
  f('pre', n)
  for x in n.children:
    if isinstance(x, Node):
      f('child', x)
  f('post', n)

def translateName(n):
  if isinstance(n, Node) and n.type == 'namesub':
    return translateName(n.children[0]) + '__' + translateName(n.children[1])
  return n.arg

def translateType(n):
  if isinstance(n, Type):
    if n.name == 'boolean':
      return 'bool'
  return '?TYPE'

keywords = {}
for k in ['from']:
  keywords[k] = True

def mungeName(s):
  if keywords.get(s):
    s += '_'

  return s

def translateRange(n):
  if len(n.children) == 1:
    c = n.children[0]
    assert c.type == 'range2'

    if c.children[1] is None:
      return ast.Index(translateExpr(c.children[0]))

    return ast.Slice(translateExpr(c.children[0]), translateExpr(c.children[1]), None)

  return ast.Slice(ast.Num(9999), ast.Num(8888), None)

def translateExpr(n):
  if isinstance(n, Token):
    if n.type.name == 'INTEGER':
      if n.arg > 2**63:
        return ast.NameConstant('__BIGINT__')
      return ast.Num(n.arg)
    if n.type.name == 'FLOAT':
      return ast.Num(n.arg)
    if n.type.name == 'IDENT':
      return ast.NameConstant(mungeName(n.arg))
    if n.type.name == 'FALSE':
      return ast.NameConstant('False')
    if n.type.name == 'TRUE':
      return ast.NameConstant('True')
    if n.type.name == 'BITSTRING':
      if n.arg.find('x') >= 0:
        return ast.Call(ast.NameConstant('__BITSTRING_MATCH__'), [ast.Str(n.arg)], [])
      return ast.NameConstant('0b'+n.arg)
    raise Exception('q %s' % n)

  if isinstance(n, Type):
    return ast.Num(800)

  if n.type == 'e-land':
    return ast.BoolOp(ast.And(), [translateExpr(n.children[0]), translateExpr(n.children[1])])
  elif n.type == 'e-lor':
    return ast.BoolOp(ast.Or(), [translateExpr(n.children[0]), translateExpr(n.children[1])])
  elif n.type == 'e-eq':
    return ast.Compare(translateExpr(n.children[0]), [ast.Eq()], [translateExpr(n.children[1])])
  elif n.type == 'e-ne':
    return ast.Compare(translateExpr(n.children[0]), [ast.NotEq()], [translateExpr(n.children[1])])
  elif n.type == 'e-call':
    return ast.Call(translateExpr(n.children[0]), [translateExpr(x) for x in n.children[1]], [])
  elif n.type == 'e-range':
    return ast.Subscript(translateExpr(n.children[0]), translateRange(n.children[1]), None)
  elif n.type == 'e-not':
    return ast.UnaryOp(ast.Not(), translateExpr(n.children[0]))
  elif n.type == 'e-negate':
    return ast.UnaryOp(ast.USub(), translateExpr(n.children[0]))
  elif n.type == 'e-add':
    return ast.BinOp(translateExpr(n.children[0]), ast.Add(), translateExpr(n.children[1]))
  elif n.type == 'e-sub':
    return ast.BinOp(translateExpr(n.children[0]), ast.Sub(), translateExpr(n.children[1]))
  elif n.type == 'e-mul':
    return ast.BinOp(translateExpr(n.children[0]), ast.Mult(), translateExpr(n.children[1]))
  elif n.type == 'e-div':
    return ast.BinOp(translateExpr(n.children[0]), ast.FloorDiv(), translateExpr(n.children[1]))
  elif n.type == 'e-fdiv':
    return ast.BinOp(translateExpr(n.children[0]), ast.Div(), translateExpr(n.children[1]))
  elif n.type == 'e-rem':
    return ast.BinOp(translateExpr(n.children[0]), ast.Mod(), translateExpr(n.children[1]))
  elif n.type == 'e-lt':
    return ast.Compare(translateExpr(n.children[0]), [ast.Lt()], [translateExpr(n.children[1])])
  elif n.type == 'e-le':
    return ast.Compare(translateExpr(n.children[0]), [ast.LtE()], [translateExpr(n.children[1])])
  elif n.type == 'e-gt':
    return ast.Compare(translateExpr(n.children[0]), [ast.Gt()], [translateExpr(n.children[1])])
  elif n.type == 'e-ge':
    return ast.Compare(translateExpr(n.children[0]), [ast.GtE()], [translateExpr(n.children[1])])
  elif n.type == 'e-lsh':
    return ast.BinOp(translateExpr(n.children[0]), ast.LShift(), translateExpr(n.children[1]))
  elif n.type == 'e-rsh':
    return ast.BinOp(translateExpr(n.children[0]), ast.RShift(), translateExpr(n.children[1]))
  elif n.type == 'e-eor':
    return ast.BinOp(translateExpr(n.children[0]), ast.BitXor(), translateExpr(n.children[1]))
  elif n.type == 'e-or':
    return ast.BinOp(translateExpr(n.children[0]), ast.BitOr(), translateExpr(n.children[1]))
  elif n.type == 'e-and':
    return ast.BinOp(translateExpr(n.children[0]), ast.BitAnd(), translateExpr(n.children[1]))
  elif n.type == 'e-ternary':
    return ast.IfExp(translateExpr(n.children[0]), translateExpr(n.children[1]), translateExpr(n.children[2]))
  elif n.type == 'e-subrange':
    return ast.Num(113)
  elif n.type == 'e-lnegate':
    return ast.UnaryOp(ast.Invert(), translateExpr(n.children[0]))
  elif n.type == 'e-subscript':
    return ast.Attribute(translateExpr(n.children[0]), n.children[1].arg, None)
  elif n.type == 'e-indexempty':
    return ast.Subscript(translateExpr(n.children[0]), ast.Slice(None, None, None), None)
  elif n.type == 'e-implementation-defined':
    return ast.Call(ast.NameConstant('IMPLEMENTATION_DEFINED'), [], [])
  elif n.type == 'e-exp':
    return ast.BinOp(translateExpr(n.children[0]), ast.Pow(), translateExpr(n.children[1]))
  elif n.type == 'e-mod':
    return ast.BinOp(translateExpr(n.children[0]), ast.Mod(), translateExpr(n.children[1]))
  elif n.type == 'e-unknown':
    return ast.Call(ast.NameConstant('UNKNOWN'), [], [])
  elif n.type == 'e-index':
    return ast.Subscript(translateExpr(n.children[0]), ast.Slice(None,None,None), None)
  elif n.type == 'e-tuple':
    return ast.Tuple([translateExpr(x) for x in n.children[0]], None)
  elif n.type == 'e-set-in':
    return ast.Num(114)
  elif n.type == 'e-concat':
    return ast.Call(ast.NameConstant('_CONCAT_'), [translateExpr(n.children[0]), translateExpr(n.children[1])], [])
  elif n.type == 'tuple-nomatch':
    return ast.NameConstant('_')
  elif n.type == 'range':
    return ast.Num(122) #return translateRange(n)
  else:
    raise Exception('unknown node type: %s' % (n,))

  return ast.Num(42)

def translateStmtIf(n):
  expr = translateExpr(n.children[0])
  t    = translateStmtOrBlock(n.children[1])
  f    = []
  if n.children[2]:
    f = translateStmtOrBlock(n.children[2])

  return ast.If(expr, t, f)

def translateStmtReturn(n):
  expr = None
  if n.children[0]:
    expr = translateExpr(n.children[0])

    return ast.Return(expr)

def translateStmtAssert(n):
  return ast.Assert(translateExpr(n.children[0]), None)

def translateStmtExpr(n):
  return ast.Expr(translateExpr(n.children[0]))

def translateStmtAssign(n):
  return ast.Assign([translateExpr(n.children[0])], translateExpr(n.children[1]))

def translateStmtConstant(n):
  return ast.Assign([translateExpr(n.children[0])], translateExpr(n.children[1]))

def translateStmtDecl(n):
  e = ast.NameConstant('None')
  if n.children[2]:
    e = translateExpr(n.children[2])
  return ast.Assign([translateExpr(n.children[1])], e)

def translateStmtDecls(n):
  return [translateStmtDecl(x) for x in n.children[1]]

i = 0
def translateStmtCase(n):
  global i

  name = '_CaseExp_' + str(i)
  i += 1
  e = ast.Assign([ast.NameConstant(name)], translateExpr(n.children[0]))
  cases = n.children[1]

  ifs = [e]
  for case in cases:
    assert case.type == 's-case-match'
    matches = case.children[0]
    caseStmt = case.children[1]

    q = ast.BoolOp(ast.Or(), [ast.Compare(ast.NameConstant(name), [ast.Eq()], [translateExpr(m)]) for m in matches])
    ee = ast.If(q, translateStmtOrBlock(caseStmt), [])
    if len(ifs) > 1:
      z = ifs[1].orelse
      while len(z) > 0:
        z = z[0].orelse
      z.append(ee)
    else:
      ifs.append(ee)

  if n.children[2]:
    z = ifs[1].orelse
    while len(z) > 0:
      z = z[0].orelse
   
    z += translateStmtOrBlock(n.children[2])

  return ifs

def translateStmt(n):
  if n.type == 's-if':
    return translateStmtIf(n)
  elif n.type == 's-return':
    return translateStmtReturn(n)
  elif n.type == 's-assert':
    return translateStmtAssert(n)
  elif n.type == 's-assign':
    return translateStmtAssign(n)
  elif n.type == 's-case':
    return translateStmtCase(n)
  elif n.type == 's-decls':
    return translateStmtDecls(n)
  elif n.type == 's-for-up':
    return ast.Pass()
  elif n.type == 's-for-down':
    return ast.Pass()
  elif n.type == 's-expr':
    return translateStmtExpr(n)
  elif n.type == 's-constant':
    return translateStmtConstant(n)
  elif n.type == 's-repeat':
    return ast.Pass()
  elif n.type == 's-while':
    return ast.Pass()
  elif n.type == 's-undefined':
    return ast.Expr(ast.Call(ast.NameConstant('UNDEFINED'), [], []))
  elif n.type == 's-implementation-defined':
    return ast.Expr(ast.Call(ast.NameConstant('IMPLEMENTATION_DEFINED'), [], []))
  else:
    raise Exception('unknown node type: %s' % (n,))

def translateBlock(n):
  items = []
  if n is None:
    return [ast.Pass()]

  for x in n.children:
    s = translateStmt(x)
    if not isinstance(s, list):
      s = [s]
    items += s

  if len(items) == 0:
    return [ast.Pass()]

  return items

def translateStmtOrBlock(n):
  if n.type == 's-block':
    return translateBlock(n)

  s = translateStmt(n)
  if not isinstance(s, list):
    s = [s]

  return s

# Translate a function definition to RPython.
#
# (Node~func-def) -> ast.AST
def translateFuncDef(n):
  assert n.type == 'func-def'

  rty    = n.children[0]
  name   = translateName(n.children[1])
  params = n.children[2]
  body   = translateBlock(n.children[3])

  z = ast.FunctionDef(name, ast.arguments([], None, [], [], None, []), body, [], None)
  return z

def translate(asl, fo):
  for k, v in asl.items():
    def f(ty, n):
      if ty != 'pre':
        return

      if n.type == 'func-def':
        z = translateFuncDef(n)
        fo.write(astor.to_source(z, '  '))
        fo.write('\n')

    for t in v.tree:
      if t is not None:
        visit(t, f)
