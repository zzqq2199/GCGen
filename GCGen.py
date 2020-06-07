from tree import Tree
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("-b", "--body", help="generate body code", action="store_true")
    parser.add_argument("-w", "--wrapper", help="generate wrapper code", action="store_true")
    parser.add_argument("-r", "--register", help="generate register code", action="store_true")
    args = parser.parse_args()
    print(f"parser={args}")
    print(f"parser.input_file={args.input_file}")
    tree = Tree(args.input_file)
    func = tree.block_func()
    if args.body:
        func.dump_body()
    if args.wrapper:
        func.dump_wrapper()
    if args.register:
        func.dump_register()