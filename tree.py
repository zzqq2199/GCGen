import copy
from parser import Parser

from tools import *
from unit import *


class Tree:
    def __init__(self, filename:str):
        self.filename = filename
        self.chs = read_file(filename)
        self.parser = Parser()
        self.tokens = self.parser.parse_all(self.chs)
        self.i = 0 # index of self.tokens
        self.params = dict()
        self.funcs = dict()
        self.context = dict()
        self.contexts = [self.context]

    def record_context(f):
        def wrapper(self, *args, **kwargs):
            context = copy.deepcopy(self.contexts[-1])
            self.contexts.append(context)
            self.context = self.contexts[-1]
            ret = f(self, *args, **kwargs)
            self.contexts = self.contexts[:-1]
            self.context = self.contexts[-1]
            return ret
        return wrapper


    def generate_bug(self, msg:str):
        assert(self.i>0)
        t = self.tokens[self.i-1]
        token = t['token']
        ch:Ch = token[0]
        bug_msg = cf.red(f"[FILENAME:{self.filename}][LINE:{ch.line_no},{ch.column_no}][MSG:{msg}]")
        return bug_msg


    def next_token(self):
        token = self.tokens[self.i]
        self.i+=1
        return token

    @record_context
    def block_typename(self):
        '''
        @return: a list of attributes about type
            typename:
            is_vector: 
            bitwidth:   '' if not appointed
        '''
        ans = dict()
        basic_type = self.next_token()
        ans['typename'] = basic_type['str']
        ans["is_vector"] = False
        ans["bitwidth"] = ''
        t = self.next_token()
        if t['str'] == '<':
            # elongated bitwidth
            raise CompileException("NOT implement now")
        else:
            self.i -= 1 # roll index back
        t = self.next_token()
        if t['str'] == '*':
            ans["is_vector"] = True
        else:
            self.i -= 1
        utype = Utype(ans['typename'], ans['bitwidth'], ans['is_vector'], self.context)
        return utype

    @record_context
    def block_one_param(self):
        '''
        @explanation: to resolve such patterns: "int a", "uint<bitwidth> abc"
        @return: an instance of Var
        '''
        utype = self.block_typename()
        p_name = self.next_token()
        p_var = Variable(p_name['str'], utype)
        logging.debug(f"p_var={p_var}")
        return p_var

    @record_context
    def block_param_define(self):
        assert(self.tokens[self.i-1]['str'] == 'param')
        name = self.next_token()
        assert(name['type']=='name') # not operator nor number
        param_name = name['str']
        logging.debug(f'param_name={param_name}')
        param = Param(param_name)
        token = self.next_token()
        assert(token['str'] == '{')
        while True:
            t = self.next_token()
            if t['str'] == '}':
                break
            self.i-=1
            one_param = self.block_one_param()
            param.add_var(one_param)
            t = self.next_token()
            if t['str'] != ';':
                raise CompileException(self.generate_bug(f"Behind definitioin of param, '{sep}' is expected!"))         
        return param

    def fetch_and_check(self, expected_str):
        t = self.next_token()
        if t['str'] != expected_str:
            raise CompileException(f"Expected {expected_str}")

    @record_context
    def block_reduce(self, l_var=None):
        '''
        @return:
            str:    translated expression
            return_type
        '''
        self.fetch_and_check('reduce')
        self.fetch_and_check('(')
        vector = self.next_token()
        logging.debug(cf.red(f"self.context={self.context}"))
        if vector['str'] not in self.context:
            raise CompileException(f"Unrecognized varname {vector['str']}")
        vector:Variable = self.context[vector['str']]
        if vector.utype.is_vector == False:
            raise CompileException(f"Expected vector type")
        param1 = vector.name
        self.fetch_and_check(',')
        ret = self.block_right_expression(None,end=',')
        param2 = ret['str']
        # no ',', because already resolved in block_right_expression
        param3 = self.next_token()
        param3 = param3['str']
        '''
        do something with param3
        '''
        self.fetch_and_check(')')
        logging.debug(f"param1={param1}\tparam2={param2}\tparam3={param3}")
        expr = f'thrust::reduce(policy, {vector.name}, {vector.name}+{vector.size}, {param2}, {param3})'
        ans=dict()
        ans['str'] = expr
        ans['return_type'] = vector.utype.name
        return ans

    @record_context
    def block_right_expression(self, l_var=None, end=';'):
        '''
        it will resolve end
        @return:
            str:    translated expression
            return_type:    
        '''
        ans = dict()
        t = self.next_token()
        self.i-=1
        logging.debug(f"block_right_expression: t={t}") 
        if t['str'] == 'reduce':
            ret = self.block_reduce()
            self.fetch_and_check(';')
            return ret
        else:
            translated_tokens = []
            while True:
                t = self.next_token()
                if t['str'] == end:
                    break
                if t['str'] == '.':
                    translated_tokens[-1] = '_'+translated_tokens[-1]
                    translated_tokens.append('_')
                else:
                    translated_tokens.append(t['str'])
            translated_expr = ''.join(translated_tokens)
            if l_var != None:
                translated_expr = l_var.name + '=' + translated_expr
            ans['str'] = translated_expr
            ans['return_type'] = 'todo'
        return ans

    @record_context
    def block_statement(self):
        begin_index = self.i
        t = self.next_token()
        if is_typename(t['str']):
            self.i -= 1
            one_var:Varibale = self.block_one_param()
            t = self.next_token()
            if t['str'] == '=':
                ret = self.block_right_expression(l_var=one_var)
                logging.debug(f"ret['str']={ret['str']}")
            elif t['str'] == ';':
                pass
            else:
                raise CompileException(f"UNEXPECTED char: {t['str']}")
            return one_var
            one_var = self.block
        elif t['str'] in self.context:
            ele = self.context[t['str']]
            if type(ele) != Variable:
                raise CompileException(f"Variable type expected here.")
            t = self.next_token()
            if t['str'] == '=':
                self.block_right_expression()
            else:
                raise CompileException(f"UNEXPECTED char: {t['str']}")
            return None
        else: # pure call, example: sort(G, greater)
            self.i -= 1
            self.block_right_expression()
            return None


    @record_context
    def block_func(self):
        return_type = self.block_typename()
        name_token = self.next_token()
        assert(name_token['type']=='name')
        func = Func(name_token['str'])
        func.set_return_type(return_type)
        # resolve parameters
        t = self.next_token()
        if t['str'] != '(':
            raise CompileException("'(' is expected after function name")
        while True:
            t = self.next_token()
            if t['str'] == ')':
                break
            self.i-=1
            one_param = self.block_one_param()
            self.context[one_param.name] = one_param
            func.add_param(one_param)
            t = self.next_token()
            if t['str'] == ')':
                self.i-=1
            elif t['str'] == ',':
                pass
            else:
                raise CompileException(self.generate_bug(f"',' or ')' expected after each parameter in function definition"))
        # resolve body
        t = self.next_token()
        if t['str'] != '{':
            raise CompileException("'{' is expected")
        self.block_statement()
        self.block_statement()
        self.block_statement()
        self.block_statement()

        print(func)

        return func


    def block_code(self):
        '''
        @param i: index of self.tokens
        '''
        try:
            # while self.i < len(self.tokens):
            for cnt in range(2):
                token = self.next_token()
                if token['str'] == 'param':
                    param = self.block_param_define()
                    self.context[param.name] = param
                    logging.debug(f"param = {param}")
                elif is_typename(token['str']):
                    # definition of function
                    # why not definition of variable? no need here. 
                    self.i -= 1
                    self.block_func()
        except CompileException as e:
            logging.error(self.generate_bug(e))
            raise Exception
        


if __name__ == '__main__':
    tree = Tree(r'pse/terngrad.pse.txt')
    for token in tree.tokens:
        logging.debug(token['str'])
    tree.block_code()
