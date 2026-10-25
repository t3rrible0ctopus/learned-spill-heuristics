v0 = 0
v1 = 30
v2 = 0
v3 = 1
v4 = 2
long_loop:
v0 = v0 + 1
v2 = v2 + v0
v3 = v3 + v2
v4 = v4 + v0
if v0 < v1 goto long_loop
v5 = v2 + v3
v6 = v5 + v2
v7 = v6 + v3
print v7
