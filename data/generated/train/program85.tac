v0 = 29
v1 = 20
if v0 < v1 goto smaller
v2 = v0 - v1
goto join
smaller:
v2 = v1 - v0
join:
v3 = v2 * 2
print v3
