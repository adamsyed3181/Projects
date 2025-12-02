# Overview
The puropose of our FindPath.py file is to create a path finding robot to navigate through multiple hospital wards, using A* and Dijkstra to avoid obstacles and find the optimum path.

# Instructions
To use the program, simply enter python FindPath.py in the terminal or click run. After that, you will be prompted to enter the name or number of the input file. You will see that all of the input files in this repository are formatted as "inputfile__.txt", so simply enter the corresponding name or number of the file that you wish to run.

# Notable classes:
## MazeGame
For MazeGame, we added self.ward_priority, which lets us categorize the different wards into seperate groups based on their priority. Similarly, self.ward_codes and self.ward_locations let us assign the ward names and locations to a given number. For the maze, we utilized 0 as open spaces, 1 as walls, and 2-13 for the different wards, starting with 2 for Admissions and ending with the Medical Ward at 13. 

The input file containing the algorithm name, starting position, and the list of the goal wards is read in using self.input_filename. This also checks for errors for the start position, as well as a default position to use instead. Similar error checking exists for the goal wards.

## DrawMaze
We mapped each ward to a color, trying to mimic the hospital layout image we were given at the start. The maze will also mark the start and goal positions.

## Heuristic
The heuristic we used is the Manhattan distance.

## ResetCosts
We are able to return the heuristic's costs using ResetCosts.

## FindPath
Multiple paths to be found after reaching its destination. After each new path is found, the values of g, h, and f are reset and a new path is routed. Each completed path is accounted for in here as well. And, there is a simply if statement that checks whether the program is running A* or Dijkstra, and either changes the g value to increment or leaves it as 0.

## ReconstructPath
Shows the user the animated path as the robot moves from its start goal to the end goal. This is also where the path is able to be colored per new destination.

## TerminateProgram
We created this to print a whether the program reached all, partial, or none of the goals after termination. It is used to visually tell the user whether they have achieved these states.
