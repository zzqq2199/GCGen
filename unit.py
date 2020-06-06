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
header = f"""
#include <chrono>
#include <stdint.h>
#include <thrust/copy.h> //copy_if
#include <thrust/execution_policy.h> //thrust::device
#include <thrust/functional.h> //greater<float>
#include <thrust/iterator/counting_iterator.h> // counting_iterator
#include <thrust/random.h>
#include <thrust/sort.h> //sort()
#include <thrust/transform.h> //trnasform

#include "naive_random.hpp"
#include "get_policy_general.h"
using namespace zq_cpp_lib::operate_memory;

#define uint8 uint8_t
#define uint32 uint32_t
#define int32 int32_t
"""


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
        self.use_random = []
        self.statements = []
    def add_statement(self, code:str):
        self.statements.append(code)
    def set_return_type(self, return_type:Utype):
        self.return_type = return_type
    def set_use_random(self, utype:Utype):
        if utype.name not in ['float', 'int']:
            raise CompileException(f"Only support 'float' or 'int' for random, you provided: {utype.name}")
        if utype.name not in self.use_random:
            self.use_random.append(utype.name)
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
        translated_expr = self.translated()
        ans = f"""Func[name:{self.name}
Params:
{params_expr}Vars:
{vars_expr}Translated:
{translated_expr}]"""
        return ans
    def need_aggregation(self):
        return False
    def aggregate_rate(self):
        return 1

    def dump_to_file(self):
        with open(f"output/{self.name}_body.h",'w') as f:
            f.write(header)
            f.write(self.translated())

    def translated(self):
        ans = ""
        var_define = ""
        param_define = ""
        for v in self.params:
            v:Variable = self.params[v]
            param_define += f"\t{v.utype.generate_call()} {v.name},\n"
            if v.utype.is_vector:
                param_define += f"\tint32 _{v.name}_size,\n"
        param_define += f"\tpolicy_t policy,\n"
        param_define += f"\tvoid* stream\n"

        for v in self.vars:
            if v not in self.params:
                v:Variable = self.vars[v]
                if type(v) == Lambda_func:
                    ans = v.translated() + ans
                    continue
                var_define += f"{v.initialize_code};\n"
        body_expr = ""
        for statement in self.statements:
            body_expr += f"{statement};\n"

        ans += f"""template <typename policy_t>
{self.return_type.name} {self.name}_body(
{param_define}
){{
{var_define}{body_expr}
}};"""
        return ans
            


class Lambda_func(Func):
    def __init__(self,name:str):
        super(Lambda_func, self).__init__(name)
        self.refs = dict()
    def need_aggregation(self):
        if self.return_type.name == 'uint' and str(self.return_type.bitwidth) not in ['8','16','32']:
            if len(self.params)!=1:
                raise CompileException("You should provide only 1 params for aggregative lambda_func")
            return True
    def aggregate_rate(self):
        rate = 8 / self.return_type.bitwidth
        return rate
    def add_ref(self, v:Variable):
        self.refs[v.name] = v
        self.vars[v.name] = v
    def generate_call(self, maximum_index):
        refs = []
        for key in self.refs:
            refs.append(key)
        if self.need_aggregation():
            refs.append(str(maximum_index))
        if self.use_random:
            refs.append("std::chrono::high_resolution_clock::now().time_since_epoch().count()")
        refs_expr = ",".join(refs)
        call = f"{self.name}({refs_expr})"
        return call

    def translated(self):
        ref_define = ""
        ref_pass = ""
        ref_assign = ""
        param_define = ""
        var_define = ""
        for v in self.refs:
            v:Variable = self.refs[v]
            ref_define += f"\t{v.utype.generate_call()} {v.name};\n"
            ref_pass += f"\t{v.utype.generate_call()} {v.name}_,\n"
            ref_assign += f"\t{v.name} = {v.name}_;\n"
        if self.need_aggregation():
            ref_define += f"\tint _maximum_index;\n"
            ref_pass += f"\tint _maximum_index_,\n"
            ref_assign += f"\t_maximum_index = _maximum_index_;\n"
        if self.use_random:
            ref_define += f"\tuint32 _t;\n"
            ref_pass += f"\tuint32 _t_,\n"
            ref_assign += f"\t_t = _t_;\n"
        ref_pass = ref_pass[:-2]
        body_expr = ""
        for param in self.params.values():
            param:Variable = param
            param_define += f"{param.utype.generate_call()} {param.name},"
        param_define = param_define[:-1]
        if self.use_random:
            for typename in self.use_random:
                var_define += f"\tRandom<{typename}> random_{typename}(_t);\n"
        for v in self.vars:
            if v not in self.params and v not in self.refs:
                v:Variable = self.vars[v]
                var_define += f"\t{v.initialize_code};\n"
        if self.need_aggregation():
            var_define += f"\tuint8 _q=0;"
        if self.need_aggregation():
            body_expr += f"""for (int _i = 0; _i < {self.aggregate_rate()}; _i++){{
    {param.name}++;
    if ({param.name} < _maximum_index){{
"""
        for statement in self.statements:
            body_expr += f"{statement};\n"
        if self.need_aggregation():
            body_expr += f"""   }} //if
}} // for
return _q;
"""
            
        ans = f"""struct {self.name}{{
{ref_define}
{self.name}(
{ref_pass}
){{
{ref_assign}
}}
__host__ __device__
{self.return_type.generate_call()} operator()({param_define}){{
{var_define}
{body_expr}
}}
}};
"""
        return ans
    
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
Need_aggregation:\t{self.need_aggregation()}
Use_random:\t{self.use_random}
Aggregate_rate:\t{self.aggregate_rate()}
Params:
{params_expr}Refs:
{refs_expr}Vars:
{vars_expr}]Translated:
{self.translated()}"""
        # return cf.yellow(ans)
        return ans


