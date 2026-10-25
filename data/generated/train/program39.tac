v0 = 5
v1 = 13
v2 = 26
if v0 < v1 goto outer_true
v3 = v0 + v1
if v3 > v2 goto inner_true
v4 = v3 - v2
goto join
inner_true:
v4 = v2 - v3
goto join
outer_true:
v3 = v1 * v2
if v3 != 0 goto outer_nonzero
v4 = 1
goto join
outer_nonzero:
v4 = v3 + v0
join:
v5 = v4 + v0
v6 = v5 + v1
print v6
