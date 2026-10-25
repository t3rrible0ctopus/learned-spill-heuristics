v0 = 0
v1 = 8
v2 = 1
loop:
v0 = v0 + 1
v2 = v2 * v0
if v0 < v1 goto loop
v3 = v2 + v1
print v3
