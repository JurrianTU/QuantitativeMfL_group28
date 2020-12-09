# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 12:48:19 2020

@author: Ivo Best
"""



from gurobipy import *
import numpy as np

model = Model ('ME 44206')


# ---- Parameters ----

#Variables n, o, p, and q were introduced in order to change parameters for verification more easily.
#for part E these variables were further defined with r and s, to make global changes to production and storage costs more easily

# Demand per productype[i] per month[k]
n =     [[650, 600, 600, 550, 500, 500, 450, 600, 650, 600, 600, 550],
        [200, 250, 250, 300, 350, 400, 400, 500, 500, 400, 300, 250],
        [300, 350, 400, 350, 300, 400, 400, 300, 350, 350, 300, 350]]

a =     [[1 * i for i in n[0][:]],
         [1 * i for i in n[1][:]],
         [1 * i for i in n[2][:]]]

# Production costs of each operation[1,2,3,4] per month [k]
b =     [[12, 11, 11, 11, 10,  8 , 9, 12, 16, 18, 18, 14],
         [18, 25, 25, 20, 15, 15, 17, 19, 19, 18, 18, 18],
         [10, 12, 11, 12, 11, 12, 12, 12, 12, 11, 11, 12],
         [ 8,  9, 12, 13, 15, 15, 18, 15, 10,  8,  8,  8]]

r =     2   #number used for adjusting production costs for part E

# Production costs of productype[i] per step[j] in month[k]
c =     [[[r * i for i in b[0][:]], [r * i for i in b[1][:]]],
         [[r * i for i in b[1][:]], [r * i for i in b[2][:]]],
         [[r * i for i in b[0][:]], [r * i for i in b[3][:]]]]

# Holding costs of semi-finished[0][i] or finished[1][i] per productype [i]
o =    [[2, 1, 1],
        [4, 3, 4]]

s=      2   #number used for adjusting storage costs for part E

d =     [[ s * i for i in o[0][:]],
         [ s * i for i in o[1][:]]]

# Amount of time available for production
p =     [550, 750, 450, 400]

e =     [1 * i for i in p[:]]

# Amount of time used for operations per type[i] per operation[h]
q =    [[[0.6, 0  , 0  , 0  ], [0  , 0.8, 0  , 0  ]],
        [[0  , 0.3, 0  , 0  ], [0  , 0  , 0.9, 0  ]],
        [[0.4, 0  , 0  , 0  ], [0  , 0  , 0  , 0.7]]]

f =    [[[1 * i for i in q[0][0][:]], [1 * i for i in q[0][1][:]]],
        [[1 * i for i in q[1][0][:]], [1 * i for i in q[1][1][:]]],
        [[1 * i for i in q[2][0][:]], [1 * i for i in q[2][1][:]]]]
        
# ---- Sets ----
ProductName     =('type_1', 'type_2', 'type_3')
State           =[0, 1]
MonthName       = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
Operations      =('operation I', 'operation II', 'operation III', 'operation IV',)
I               = range (len (ProductName) )                
J               = range (len (State) )             
K               = range (len (MonthName))
H               = range (len (Operations))

# ---- Variables ----

# Decision Variable 1: Amount of products[i] produced in state[j] in month[k]
Y = {}
for i in I:
    for j in J:
        for k in K:
            for h in H:
                Y[i,j,k] = model.addVar (lb = 0, vtype = GRB.CONTINUOUS)
            
# Decision Variable 2: Amount of products[i] stored in state[j] in month[k]
Z = {}
for i in I:
    for j in J:
        for k in K:
            Z[i,j,k] = model.addVar (lb = 0, vtype = GRB.CONTINUOUS)
        
            
# Integrate new variables
model.update ()

# ---- Objective Function ----

# The total cost is the sum of products stored * storage costs + products produced * production costs for each product, each step and each month
model.setObjective (quicksum (Z[i,j,k] * d[j][i] + Y[i,j,k] * c[i][j][k] for i in I for j in J for k in K))
model.modelSense = GRB.MINIMIZE
model.update ()

# ---- Constraints ----

# Constraint 1: Satisfy demand per month, over 12 months
con1 = {}
for i in I:
    con1[i] = model.addConstr( quicksum (Y[i,1,k] for k in K) == quicksum ( a[i][k] for k in K ))  

# Constraint 2: Amount of stored finished product     
con2 = {}
for i in I:
    for k in K:
        if k>0:
            con2[i,k] = model.addConstr( Z[i,1,k] == Z[i,1,k-1] + Y[i,1,k] - a[i][k])  

# Constraint 3: Amount of stored semi-finished product
con3 = {}
for i in I:
    for k in K:
        if k>0:
            con3[i,k] = model.addConstr( Z[i,0,k] == Z[i,0,k-1] + Y[i,0,k] - Y[i,1,k])

# Constraint 4: amount of finished product cannot be higher than the amount of semi-finished product        
con4 = {}
for i in I:
    con4[i,k] = model.addConstr( quicksum(Y[i,1,k] for k in K) <= quicksum (Y[i,0,k] for k in K))
    
#Contraint 5-8: Amount of time spent on productions cannot exceed the amount available per operation type
con5 = {}
for k in K:
    for h in H:
        con5[k,h] = model.addConstr( Y[0,0,k] * f[0][0][h] + Y[2,0,k] * f[2][0][h] <= e[h] )
        
con6 = {}
for k in K:
    for h in H:
        con6[k,h] = model.addConstr( Y[0,1,k] * f[0][1][h] + Y[1,0,k] * f[1][0][h] <= e[h] )
        
con7 = {}
for k in K:
    for h in H:
        con7[k,h] = model.addConstr( Y[1,1,k] * f[1][1][h] <= e[h] )
         
con8 = {}
for k in K:
    for h in H:
        con8[k,h] = model.addConstr( Y[2,1,k] * f[2][1][h] <= e[h] )
          
# ---- Solve ----

model.setParam( 'OutputFlag', True) # silencing gurobi output or not
model.setParam ('MIPGap', 0);       # find the optimal solution
model.write("output.lp")            # print the model in .lp format file
model.optimize ()

# --- Print results ---

print ('\n--------------------------------------------------------------------\n')
    
if model.status == GRB.Status.OPTIMAL: # If optimal solution is found
    print ('Total costs : %10.2f euro' % model.objVal)

#printing the total production costs
y=sum(Y[i,j,k].x * c[i][j][k] for i in I for j in J for k in K)
print('production costs:', y)

#printing the total storage costs
z=sum(Z[i,j,k].x * d[j][i] for i in I for j in J for k in K)
print ('storage costs:', z)

#printing the total amount of time spent on production
time=sum(Y[i,j,k].x * f[i][j][h] for i in I for j in J for h in H for k in K)
print('total time spent:', time)

#printing and overview of the decision variables
print ('')
print ('Overview of production and storage:\n')
    
#Printing the amount of finished products produced per month
print('Production amount finished')
s = '%8s' % ''
for k in K:
        s = s + '%8s' %MonthName[k]
print (s)    

for i in I:
        s = '%8s' %ProductName[i]
        for k in K:
            s = s + '%8.0f' %( Y[i,1,k].x )
        s = s + '%8.0f' % sum (Y[i,1,k].x  for k in K)    
        print (s)    

s = '%8s' % ''
for k in K:
       s = s + '%8.0f' % sum (Y[i,1,k].x for i in I)    
print (s)

#Printing the amount of semi-finished products produced per month
print('Production amount semi-finished')
s = '%8s' % ''
for k in K:
        s = s + '%8s' %MonthName[k]
print (s)    

for i in I:
        s = '%8s' %ProductName[i]
        for k in K:
            s = s + '%8.0f' %( Y[i,0,k].x )
        s = s + '%8.0f' % sum (Y[i,0,k].x  for k in K)    
        print (s)    

s = '%8s' % ''
for k in K:
       s = s + '%8.0f' % sum (Y[i,0,k].x for i in I)    
print (s)

#Printing the amount of finished products stored per month
print('Storage amount finished')
s = '%8s' % ''
for k in K:
        s = s + '%8s' %MonthName[k]
print (s)    

for i in I:
        s = '%8s' %ProductName[i]
        for k in K:
            s = s + '%8.0f' % Z[i,1,k].x
        s = s + '%8.0f' % sum (Z[i,1,k].x for k in K)    
        print (s)    

s = '%8s' % ''
for k in K:
       s = s + '%8.0f' % sum (Z[i,1,k].x for i in I)    
print (s)

#Printing the amount of semi-finished products stored per month
print('Storage amount semi-finished')
s = '%8s' % ''
for k in K:
        s = s + '%8s' %MonthName[k]
print (s)    

for i in I:
        s = '%8s' %ProductName[i]
        for k in K:
            s = s + '%8.0f' % Z[i,0,k].x
        s = s + '%8.0f' % sum (Z[i,0,k].x for k in K)    
        print (s)    

s = '%8s' % ''
for k in K:
       s = s + '%8.0f' % sum (Z[i,0,k].x for i in I)    
print (s)

