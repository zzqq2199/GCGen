import logging
logging.basicConfig(
    level = logging.DEBUG,
    format='%(filename)s[line:%(lineno)d][%(levelname)s] %(message)s',
)
class Ch:
    '''
    char containing its informations of context: line_no & column_no
    '''
    def __init__(self, ch=' ', line_no=0, column_no=0):
        self.ch = ch
        self.line_no = line_no
        self.column_no = column_no
    def __str__(self):
        ans = f'[line_no:{self.line_no},column_no:{self.column_no}]{self.ch}'
        return ans

def read_file(filepath:str):
    '''
    @return: parses file contents into many chars, wrap it as Ch(), return a list of Ch()
    '''
    ans = []
    with open(filepath, 'r') as f:
        line_no = 0
        for line in f.readlines():
            line = line.strip('\n')
            line_no += 1
            for column_no, v in enumerate(line):
                c = Ch(v, line_no, column_no+1)
                ans.append(c)
    return ans

if __name__ == '__main__':
    ret = read_file(r'pse\terngrad.pse.txt')
    for v in ret:
        logging.debug(v)
