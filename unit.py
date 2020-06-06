import sympy
import colorful as cf
from tools import *

bitwidth_of_typename = {
    'uint1': 1,
    'uint2': 2,
    'uint4': 4,
    'uint8': 8,
    'uint': 32,
    'int': 32,
    'float': 32,
    'void': 0,
    'lambda_func': 0
}



def is_typename(typename:str):
    return typename in bitwidth_of_typename
def check_typename(typename:str, context=dict()):
    if is_typename(typename):
        return 'basic_type'
    if typename in context:
        t = context[typename]
        if type(t) == Param:
            return 'param_type'
    raise CompileException(f"CANNOT resolve typename: {typename}")
    
class Utype(): # difer from keyword type
    def __init__(self, name, bitwidth='', is_vector=False, context=dict()):
        ret = check_typename(name, context)
        self.name = name
        self.is_vector = is_vector
        if ret == 'basic_type':
            if bitwidth == '':
                self.bitwidth = bitwidth_of_typename[name]
            else:
                self.bitwidth = sympy.Symbol(bitwidth)
        elif ret == 'param_type':
            self.bitwidth = 0
    def generate_call(self):
        name = self.name
        if name == 'uint':
            name = 'uint8'
        if self.is_vector:
            name+='*'
        return name

    def __str__(self):
        ans = f"Utype[name:{self.name}, bitwidth:{self.bitwidth}, is_vector:{self.is_vector}]"
        return ans

class Variable():
    '''
    @attributes:
        name:   
        typename:
        bitwidth:   bitwidth of a variable
        size:   length of vector. For single variable, size = 1
        bits:  size*bitwidth
        bytes: ceil(bits/8) or (bits+7)//8
    '''
    def __init__(self, name:str, utype: Utype):
        self.name = name
        self.utype = utype
        self.size = 1
        if utype.is_vector:
            self.size = sympy.Symbol(f"_{name}_size")
        self.bits = self.size * utype.bitwidth
        self.bytes = (self.bits + 7 ) // 8
        self.initialize_code = f"{utype.generate_call()} {name}"
    def set_bits(self, bits):
        self.bits = bits
        self.bytes = (self.bits+7)//8
        self.size = bits / self.utype.bitwidth
    def set_initialize_code(self, code):
        self.initialize_code = code

    def __str__(self):
        ans = f"Var[name: {self.name}, utype:{self.utype}, bits:{self.bits}, bytes:{self.bytes}, initlize:{self.initialize_code}]"
        return ans

class Param():
    def __init__(self, name:str):
        self.name = name
        self.vars = dict()
    def add_var(self, v:Variable):
        if v.name in self.vars:
            raise CompileException(f"Redefinition {v.name} in Param {self.name}")
        self.vars[v.name] = v
    def __str__(self):
        vars_expr = ""
        for v in self.vars:
            v = self.vars[v]
            vars_expr += f"\t{v}\n"
        ans = f"""Param[name:{self.name}
{vars_expr}]
"""
        return ans

class Func():
    def __init__(self, name:str):
        self.name = name
        self.params = dict()
        self.vars = dict()
    def set_return_type(self, return_type:Utype):
        self.return_type = return_type
    def add_param(self, v:Variable):
        if v.name in self.params:
            raise CompileException(f"Redefinition {v.name} in parameters declaration of function {self.name}")
        self.params[v.name] = v
        self.vars[v.name] = v
    def add_var(self, v:Variable):
        if v.name in self.vars:
            raise CompileException(f"Redefinition {v.name} in variable declaration of function {self.name}")
        self.vars[v.name] = v
    def __str__(self):
        params_expr = ""
        for v in self.params:
            v = self.params[v]
            params_expr += f"\t{v}\n"
        vars_expr = ""
        for v in self.vars:
            if v not in self.params:
                v = self.vars[v]
                vars_expr += f"\t{v}\n"
        ans = f"""Func[name:{self.name}
Params:
{params_expr}Vars:
{vars_expr}]"""
        return ans



class Lambda_func(Func):
    def __init__(self,name:str):
        super(Lambda_func, self).__init__(name)
        self.refs = dict() 
        self.use_random = False
    def add_ref(self, v:Variable):
        self.refs[v.name] = v
        self.vars[v.name] = v
    def set_use_random(self):
        self.use_random = True
    def generate_call(self, input_vector:Variable):
        refs = []
        for key in self.refs:
            refs.append(key)
        refs_expr = ",".join(refs)
        call = f"{self.name}({refs_expr})"
        return call
    def __str__(self):
        params_expr = ""
        for v in self.params:
            v = self.params[v]
            params_expr += f"\t{v}\n"
        refs_expr = ""
        for v in self.refs:
            v = self.refs[v]
            refs_expr += f"\t{v}\n"
        vars_expr = ""
        for v in self.vars:
            if v not in self.params and v not in self.refs:
                v = self.vars[v]
                vars_expr += f"\t{v}\n"
        ans = f"""Lamda_func[name:{self.name}
Return_type:\t{self.return_type}
Params:
{params_expr}Refs:
{refs_expr}Vars:
{vars_expr}]"""
        # return cf.yellow(ans)
        return ans


