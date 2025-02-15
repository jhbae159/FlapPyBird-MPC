import cvxpy as cvx
import numpy as np
import matplotlib.pyplot as plt
import copy 


N = 40 # time steps to look ahead
path = cvx.Variable((N, 2)) # initialize the y pos and y velocity
flap = cvx.Variable(N-1, boolean=True) # initialize the inputs, whether or not the bird should flap in each step
last_solution = [False, False, False] # seed last solution
last_path = [(0,0),(0,0)] # seed last path

PIPEGAPSIZE  = 100 # gap between upper and lower pipe
PIPEWIDTH = 52
BIRDWIDTH = 34
BIRDHEIGHT = 24
BIRDDIAMETER = np.sqrt(BIRDHEIGHT**2 + BIRDWIDTH**2) # the bird rotates in the game, so we use it's maximum extent
SKY = 0 # location of sky
GROUND = (512*0.79)-1 # location of ground
PLAYERX = 57 # location of bird


def getPipeConstraintsDistance(x, y, lowerPipes):
    constraints = [] # init pipe constraint list
    pipe_dist = 0 # init dist from pipe center
    for pipe in lowerPipes:
        dist_from_front = pipe['x'] - x - BIRDDIAMETER
        dist_from_back = pipe['x'] - x + PIPEWIDTH
        if (dist_from_front < 0) and (dist_from_back > 0):
            constraints += [y <= (pipe['y'] - BIRDDIAMETER)] # y above lower pipe
            constraints += [y >= (pipe['y'] - PIPEGAPSIZE)] # y below upper pipe
            pipe_dist += cvx.abs(pipe['y'] - (PIPEGAPSIZE//2) - (BIRDDIAMETER//2) - y) # add distance from center
    return constraints, pipe_dist

def solve2(playery, playerVelY, lowerPipes, windAccYList):

    pipeVelX = -4 # speed in x
    playerAccY    =   1   # players downward accleration
    playerFlapAcc =   -9    # players speed on flapping

    # unpack path variables
    y = path[:,0]
    vy = path[:,1]

    c = [] # init constraint list
    c += [y <= GROUND, y >= SKY] # constraints for sky and ground
    c += [y[0] == playery, vy[0] == playerVelY + windAccYList[0]] # initial conditions

    obj = 0

    x = PLAYERX
    xs = [x] # init x list

    #Ignore the pipe that bird have passed
    lowerPipes_tmp = copy.copy(lowerPipes)
    windAccYList_tmp = copy.copy(windAccYList)
    if x + BIRDWIDTH / 2 > lowerPipes_tmp[0]['x'] + PIPEWIDTH / 2:
        lowerPipes_tmp.pop(0)
    windAccY = windAccYList_tmp[0]

    for t in range(N-1): # look ahead
        dt = t//15 + 1 # let time get coarser further in the look ahead
        x -= dt * pipeVelX # update x
        xs += [x] # add to list
        c += [vy[t + 1] ==  vy[t] + playerAccY * dt + playerFlapAcc * flap[t] + windAccY * dt] # add y velocity constraint, f=ma
        c += [y[t + 1] ==  y[t] + vy[t + 1]*dt ] # add y constraint, dy/dt = a
        pipe_c, dist = getPipeConstraintsDistance(x, y[t+1], lowerPipes) # add pipe constraints
        c += pipe_c
        obj += dist
        
        #Update windAccY if bird pass the pipe
        if lowerPipes_tmp and x + BIRDWIDTH / 2 > lowerPipes_tmp[0]['x'] + PIPEWIDTH / 2:
            lowerPipes_tmp.pop(0)
            windAccYList_tmp.pop(0)
            windAccY = windAccYList_tmp[0]

    #objective = cvx.Minimize(cvx.sum(flap) + 10* cvx.sum(cvx.abs(vy))) # minimize total flaps and y velocity
    objective = cvx.Minimize(cvx.sum(cvx.abs(vy)) + 100* obj)

    prob = cvx.Problem(objective, c) # init the problem

    try:
        prob.solve(verbose = False) # use this line for open source solvers
        #prob.solve(verbose = False, solver="GUROBI") # use this line if you have access to Gurobi, a faster solver

        last_path = list(zip(xs, y.value)) # store the path
        last_solution = np.round(flap.value).astype(bool) # store the solution
        return last_solution[0], last_path # return the next input and path for plotting
    except:
        try:
            last_solution = last_solution[1:] # if we didn't get a solution this round, use the last solution
            last_path = [((x-4), y) for (x,y) in last_path[1:]]
            return last_solution[0], last_path
        except:
            return False, [(0,0), (0,0)] # if we fail to solve many times in a row, do nothing


