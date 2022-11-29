from gboml.parsing import parse, parse_file

tree = parse("""#TIMEHORIZON
    T = 8760;
#GLOBAL
    a = 2;
    b = 2.2;
    c = 2e2;
    d = -1;
    e = 2e-2;
#NODE nodeI  = import nodeA from "hello.gboml";
#NODE nodeI2 = import nodeA from "hello.gboml" with
    a = 2;
    b external;
    c internal;
#NODE node1
    #PARAMETERS
        a = 2;
        b = import "lol.csv";
    #NODE A
        #VARIABLES
            external: x;
            external: y;
    #HYPEREDGE E
        #PARAMETERS
            a = 2;
        #CONSTRAINTS
            A.x == A.y;
    #VARIABLES
        internal: a;
        external: b;
        internal continuous: c[T];
        internal integer: d[T+2];
        internal binary: e[T-2];
    #CONSTRAINTS
        2+f(2,2,{2})*(2-2/2%2**2) == -2.2*0;
        2 >= 0;
        0 <= 2;
        a == b;
        named: a == b for i in [0:2] where ((i % 2) == 0) and i > 0 or (i < 0 or i != 0 and not i == i and i <= 0 and i >= 0);
        SOS1 {a, b};
        SOS2 {a, b};
        sum(a*2 for a in [0:2]) == 2;
    #OBJECTIVES
        min named: a;
        max: b[i] for i in [0:2*4] where i % 2 == 1;
#HYPEREDGE he1 = import lal from "x" with
    a = 2;
    b = 2;
""")

print(tree)
print(tree.meta)
#parse_file("test/test1.txt")