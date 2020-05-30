from tools import *
class Parser:
    def __init__(self):
        self.operators2 = ['<<', '>>', '->']
        self.operators1 = ['+', '-', '*', '/', '[', ']', '&', '(', ')', '.', '{', '}']
        self.operators = self.operators1.copy()
        self.operators.extend(self.operators2)

    def is_prefix_of_operator(self, s:str):
        for op in self.operators:
            if op.startswith(s):
                return True
        return False

    def indicate_operator(self, ch:Ch):
        if self.indicate_name(ch) or self.indicate_number(ch):
            return False
        return True

    def indicate_name(self, ch:Ch):
        '''
        return True if ch is beginning of a `name`
        '''
        char = ch.char
        if char.isalpha() or char=='_':
            return True

    def indicate_number(self, ch:Ch):
        '''
        @return: True if ch is beginning of a `number`
        '''
        char = ch.char
        if char.isdigit():
            return True
        return False
    
    def indicate(self, ch:Ch):
        '''
        @return: 'name',  'number' or 'operator'
        '''
        if self.indicate_name(ch):
            return 'name'
        elif self.indicate_number(ch):
            return 'number'
        else:
            return 'operator'

    def find_end_of_current_name(self, chs:list, index:int):
        '''
        @exmaple:
            chs='param abc{',
            index = 6 (pointer to 'a')
            return: 9 (next to last of 'abc'/ index of '{'})
        '''
        while index < len(chs):
            ch:Ch = chs[index]
            if ch.char.isalpha() or ch.char.isdigit() or ch.char == '_':
                index+=1
                continue
            return index
        return index
    def find_end_of_current_number(self, chs: list, index:int):
        while index < len(chs):
            ch: Ch = chs[index]
            if ch.char.isdigit():
                continue
            return index
        return index
    def find_end_of_current_operator(self, chs:list, index:int):
        prefix = ''
        while index < len(chs):
            ch: Ch = ch[index]
            prefix += ch.char
            if self.is_prefix_of_operator(prefix):
                continue
            return index
        return index

    def next_token(self, chs:list, index:int):
        ans = dict()
        while index < len(chs):
            ch:Ch = chs[index]
            if ch.char.isspace():
                continue
            current_type = self.indicate(ch)
            if current_type == 'name':
                end = self.find_end_of_current_name(chs, index)
            elif current_type == 'number':
                end = self.find_end_of_current_number(chs, index)
            elif current_type == 'operator':
                end = self.find_end_of_current_operator(chs, index)
            token = chs[index:end]
            ans['end'] = end
            ans['token'] = token
            return ans
        ans['end'] = index
        ans['token'] = []
        return ans
            

if __name__ == '__main__':
    chs = read_file(r'pse\terngrad.pse.txt')
    parser = Parser()
    ret = parser.next_token(chs, 0)
    logging.debug(ret)
    