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

    @record_context
    def block_func(self):
        return_type = self.block_typename()
        name_token = self.next_token()
        assert(name_token['type']=='name')
        t = self.next_token()
        if t['str'] != '(':
            raise CompileException("'(' is expected after function name")
        while True:
            t = self.next_token()
            if t['str'] == ')':
                break
            self.i-=1
            one_param = self.block_one_param()
            logging.debug(f"block_func: one_param={one_param}")
            t = self.next_token()
            if t['str'] == ')':
                self.i-=1
            elif t['str'] == ',':
                pass
            else:
                raise CompileException(self.generate_bug(f"',' or ')' expected after each parameter in function definition"))
                
        logging.debug(f'return_type={return_type}')

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
        


if __name__ == '__main__':
    tree = Tree(r'pse/terngrad.pse.txt')
    for token in tree.tokens:
        logging.debug(token['str'])
    tree.block_code()
