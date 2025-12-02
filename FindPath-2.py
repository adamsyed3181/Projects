#######################################################
#### Adam Syed and Teagan Clark
#### 11/24/25
#### Purpose: Create a path finding robot to navigate through multiple
#### hospital wards, using A* and Dijkstra to find the optimum path.
#######################################################
import tkinter as tk
from queue import PriorityQueue


######################################################
#### A cell stores f(), g() and h() values
#### A cell is either open or part of a wall
######################################################

class Cell:
    #### Initially, all maze cells have g() = inf and h() = 0
    def __init__(self, x, y, is_wall=False):
        self.x = x
        self.y = y
        self.is_wall = is_wall
        self.g = float("inf")
        self.h = 0
        self.f = float("inf")
        self.parent = None

    #### Compare two cells based on their evaluation functions
    def __lt__(self, other):
        return self.f < other.f


######################################################
# A maze is a grid of size rows X cols
######################################################
class MazeGame:
    def __init__(self, root, maze, input_filename):
        self.input_filename = input_filename
        self.root = root
        self.maze = maze
        
        self.rows = len(maze)
        self.cols = len(maze[0])

        self.path_colors = ['green', 'skyblue', 'orange', 'purple', 'yellow', 'pink']
        self.animation_delay = 100

        self.total_goals = 0
        self.completed_goals = 0

        # Priority by ward code (2–13)
        self.ward_priority = {
            2: 1,   # admissions
            3: 2,   # general
            4: 5,   # emergency
            5: 4,   # maternity
            6: 4,   # surgical
            7: 5,   # oncology
            8: 5,   # ICU
            9: 1,   # isolation
            10: 3,  # pediatric
            11: 5,  # burn ward
            12: 3,  # hematology
            13: 2   # medical ward
        }

        # Map ward *names* to the numeric codes used in the maze
        self.ward_codes = {
            "ADMISSIONS": 2,
            "GENERAL": 3,
            "GENERAL WARD": 3,
            "EMERGENCY": 4,
            "ER": 4,
            "MATERNITY": 5,
            "MATERNITY WARD": 5,
            "SURGICAL": 6,
            "SURGICAL WARD": 6,
            "ONCOLOGY": 7,
            "ICU": 8,
            "ISOLATION": 9,
            "ISOLATION WARD": 9,
            "PEDIATRIC": 10,
            "PEDIATRIC WARD": 10,
            "BURN": 11,
            "BURN WARD": 11,
            "HEMATOLOGY": 12,
            "MEDICAL": 13,
            "MEDICAL WARD": 13
        }

        # Explicit ward → list of (row, col) locations
        self.ward_locations = {
            2:  [(6, 27), (7, 28), (10, 28), (13, 28), (20, 10), (20, 11)],           # admissions (Multiple drop-offs)
            3:  [(6, 6), (6, 7), (7, 5), (7, 18), (12, 7), (13, 7), (16, 14)],       # general
            4:  [(7, 22), (8, 21), (11, 21), (12, 15), (13, 19), (14, 15), (14, 19)],# emergency
            5:  [(5, 6), (5, 7), (6, 4)],                                            # maternity
            6:  [(20, 19), (21, 18), (24, 18), (25, 21)],                            # surgical
            7:  [(14, 7), (17, 6), (17, 17), (20, 6), (21, 21), (22, 5), (24, 4)],   # oncology
            8:  [(15, 21), (18, 22)],                                                # ICU
            9:  [(8, 4), (10, 5), (11, 19), (17, 15), (24, 2)],                      # isolation
            10: [(22, 16), (23, 9), (25, 9)],                                        # pediatric
            11: [(13, 10), (18, 10)],                                                 # burn ward
            12: [(21, 13)],                                                          # hematology
            13: [(25, 20), (25, 22)]                                                 # medical ward
        }

        # Default start state (will be overwritten if input file provides Start:)
        self.agent_pos = (8, 3)

        self.path_index = 0

        # --- Read algorithm + start ward + goal ward names from input file ---
        with open(self.input_filename, "r") as f:
            # First line is the algorithm name (we read it, but currently only use A*)
            self.algorithm = f.readline().strip()
            
            if self.algorithm.lower() == "dijkstra":
                print("\n" + "#" * 50)
                print("#### NOW RUNNING: Dijkstra")
                print("#" * 50 + "\n")
            elif self.algorithm.lower() == "a*":
                print("\n" + "#" * 50)
                print("#### NOW RUNNING: A*")
                print("#" * 50 + "\n")
            else:
                print("Invalid algorithm, defaulting to A*")

            goal_positions = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                        
                # Handle start line: "Start: Admissions"
                if line.lower().startswith("start:"):
                    start_name = line.split(":", 1)[1].strip().upper()
                    if start_name not in self.ward_codes:
                        print(f"WARNING: Unknown start ward name in input file: '{line}' – using default start {self.agent_pos}")
                        continue

                    start_code = self.ward_codes[start_name]
                    locs = self.ward_locations.get(start_code, [])
                    if not locs:
                        print(f"WARNING: No locations mapped for start ward '{start_name}' – using default start {self.agent_pos}")
                        continue

                    # Use the first defined location for that start ward
                    self.agent_pos = locs[0]
                    print(f"Start location set to ward '{start_name}' at {self.agent_pos}")
                    continue

                # Otherwise, treat it as a delivery ward name
                ward_name = line.upper()
                if ward_name not in self.ward_codes:
                    print(f"WARNING: Unknown ward name in input file: '{line}' – skipping.")
                    continue

                ward_code = self.ward_codes[ward_name]
                priority = self.ward_priority.get(ward_code, 1)
                locs = self.ward_locations.get(ward_code, [])

                if not locs:
                    print(f"WARNING: No locations mapped for ward '{ward_name}' – skipping.")
                    continue

                # If ward has multiple drop-offs, pick the nearest one to the current agent position
                best_loc = min(
                    locs,
                    key=lambda pos: abs(pos[0] - self.agent_pos[0]) + abs(pos[1] - self.agent_pos[1])
                )

                goal_positions.append((best_loc[0], best_loc[1], priority, ward_name))              

        # Sort by priority (high first)
        self.goal_positions = sorted(goal_positions, key=lambda x: x[2], reverse=True)

        self.goal_pos = (self.rows - 1, self.cols - 1)
        
        self.cells = [[Cell(x, y, maze[x][y] == 1) for y in range(self.cols)]
                      for x in range(self.rows)]
        
        #### Start state's initial values for f(n) = g(n) + h(n) 
        self.cells[self.agent_pos[0]][self.agent_pos[1]].g = 0
        self.cells[self.agent_pos[0]][self.agent_pos[1]].h = self.heuristic(self.agent_pos)
        self.cells[self.agent_pos[0]][self.agent_pos[1]].f = self.heuristic(self.agent_pos)

        #### The maze cell size in pixels
        self.cell_size = 25
        self.canvas = tk.Canvas(
            root,
            width=self.cols * self.cell_size,
            height=self.rows * self.cell_size,
            bg='white'
        )
        self.canvas.pack()

        self.total_goals = len(self.goal_positions)

        self.draw_maze()
        
        #### Display the optimum path in the maze (multi-goal)
        self.find_path()

        self.terminate_program()

    ############################################################
    #### This is for the GUI part. No need to modify this unless
    #### GUI changes are needed.
    ############################################################
    def draw_maze(self):
        for x in range(self.rows):
            for y in range(self.cols):

                v = self.maze[x][y]
                if v == 1:  # walls
                    color = 'black'
                elif v == 0:  # floor
                    color = 'white'
                elif v == 2:  # admissions
                    color = 'grey'
                elif v == 3:  # general
                    color = 'red'
                elif v == 4:  # emergency
                    color = 'yellow'
                elif v == 5:  # maternity ward
                    color = 'blue'
                elif v == 6:  # surgical ward
                    color = 'maroon'
                elif v == 7:  # oncology
                    color = 'green'
                elif v == 8:  # ICU
                    color = 'orange'
                elif v == 9:  # isolation ward
                    color = 'lightskyblue1'
                elif v == 10:  # pediatric
                    color = 'olivedrab1'
                elif v == 11:  # burn ward
                    color = 'purple'
                elif v == 12:  # hematology
                    color = 'orangered2'
                elif v == 13:  # medical ward
                    color = 'lawngreen'
                else:
                    color = 'white'

                self.canvas.create_rectangle(
                    y * self.cell_size, x * self.cell_size,
                    (y + 1) * self.cell_size, (x + 1) * self.cell_size,
                    fill=color, tags=f"cell_{x}_{y}"
                )
                if not self.cells[x][y].is_wall:
                    text = f'g={self.cells[x][y].g}\nh={self.cells[x][y].h}'
                    self.canvas.create_text(
                        (y + 0.5) * self.cell_size,
                        (x + 0.5) * self.cell_size,
                        font=("Purisa", 8),
                        tags=f"text_{x}_{y}"
                    )

        # Mark the initial start cell (where the agent currently is)
        start_x, start_y = self.agent_pos
        self.canvas.create_rectangle(
            start_y * self.cell_size, start_x * self.cell_size,
            (start_y + 1) * self.cell_size, (start_x + 1) * self.cell_size,
            fill='lime green', tags=f"cell_{start_x}_{start_y}"
        )
        self.canvas.create_text(
            (start_y + 0.5) * self.cell_size,
            (start_x + 0.5) * self.cell_size,
            text='START',
            font=("Purisa", 8, "bold"),
            tags=f"text_{start_x}_{start_y}"
        )
        
        # Mark all goal positions (as targets will change)
        for r, c, _, _ in self.goal_positions:
            self.canvas.create_rectangle(
                c * self.cell_size, r * self.cell_size,
                (c + 1) * self.cell_size, (r + 1) * self.cell_size,
                fill='firebrick', tags=f"goal_cell_{r}_{c}"
            )
            self.canvas.create_text(
                (c + 0.5) * self.cell_size,
                (r + 0.5) * self.cell_size,
                text='GOAL',
                font=("Purisa", 8, "bold"),
                fill='white',
                tags=f"goal_text_{r}_{c}"
            )
        
        self.canvas.create_rectangle(
            self.agent_pos[1] * self.cell_size, self.agent_pos[0] * self.cell_size, 
            (self.agent_pos[1] + 1) * self.cell_size, (self.agent_pos[0] + 1) * self.cell_size, 
            fill='navy', tags="agent"
        )            

    ############################################################
    #### Manhattan distance
    ############################################################
    def heuristic(self, pos):
        return abs(pos[0] - self.goal_pos[0]) + abs(pos[1] - self.goal_pos[1])

    ############################################################
    #### Reset costs function
    ############################################################
    def reset_costs(self):
        for row in self.cells:
            for cell in row:
                cell.g = float("inf")
                cell.h = 0
                cell.f = float("inf")
                cell.parent = None
        start_cell = self.cells[self.agent_pos[0]][self.agent_pos[1]]
        start_cell.g = 0
        start_cell.h = self.heuristic(self.agent_pos)
        start_cell.f = start_cell.g + start_cell.h

    ############################################################
    #### A* Algorithm (multi-goal, sequential by priority)
    ############################################################
    def find_path(self):
        for goal_index, (xn, yn, priority, ward_name) in enumerate(self.goal_positions):
            print(f"Routing to {ward_name} at ({xn}, {yn}) with priority {priority} (Goal {goal_index+1})")
            self.goal_pos = (xn, yn)  # sets current goal trying to reach
            self.reset_costs()        # resets path costs (g, h, and f)
            open_set = PriorityQueue()
            
            #### Add the start state to the queue
            open_set.put((0, self.agent_pos))

            #### Continue exploring until the queue is exhausted
            while not open_set.empty():
                current_cost, current_pos = open_set.get()
                current_cell = self.cells[current_pos[0]][current_pos[1]]

                #### Stop if goal is reached
                if current_pos == self.goal_pos:
                    self.reconstruct_path()
                    self.agent_pos = self.goal_pos

                    self.canvas.delete("agent")
                    self.canvas.create_rectangle(
                        self.agent_pos[1] * self.cell_size, self.agent_pos[0] * self.cell_size, 
                        (self.agent_pos[1] + 1) * self.cell_size, (self.agent_pos[0] + 1) * self.cell_size, 
                        fill='navy', tags="agent"
                    )

                    self.completed_goals += 1 #increment completed goals

                    self.root.update()
                    self.root.after(500)  # small delay for visualization
                    break

                #### Agent goes E, W, N, and S, whenever possible
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    new_pos = (current_pos[0] + dx, current_pos[1] + dy)

                    if 0 <= new_pos[0] < self.rows and 0 <= new_pos[1] < self.cols and not self.cells[new_pos[0]][new_pos[1]].is_wall:
                        #### The cost of moving to a new position is 1 unit

                        if self.algorithm.lower() == "a*":
                            new_g = current_cell.g + 1
                        else:
                            new_g = current_cell.g
                        
                        if new_g < self.cells[new_pos[0]][new_pos[1]].g:
                            ### Update the path cost g()
                            self.cells[new_pos[0]][new_pos[1]].g = new_g
                            
                            ### Update the heuristic h()
                            self.cells[new_pos[0]][new_pos[1]].h = self.heuristic(new_pos)
                            
                            ### Update the evaluation function f(n) = g(n) + h(n)
                            self.cells[new_pos[0]][new_pos[1]].f = new_g + self.cells[new_pos[0]][new_pos[1]].h
                            self.cells[new_pos[0]][new_pos[1]].parent = current_cell
                            
                            #### Add the new cell to the priority queue
                            open_set.put((self.cells[new_pos[0]][new_pos[1]].f, new_pos))
            else:
                print(f"ERROR: Unable to reach {ward_name} (Goal {goal_index+1}) at ({xn}, {yn}) with priority {priority}. Goal skipped.") 
                continue

    ############################################################
    #### Reconstruct path for the current goal (Animated)
    ############################################################
    def reconstruct_path(self):
        # Get path color for this trip
        path_color = self.path_colors[self.path_index % len(self.path_colors)]
        self.path_index += 1
        
        # Traverse from goal back to start to get the path
        path = []
        current_cell = self.cells[self.goal_pos[0]][self.goal_pos[1]]
        while current_cell.parent:
            path.append(current_cell)
            current_cell = current_cell.parent
        
        path.reverse() 
        
        # Animate the path one step at a time
        for cell in path:
            x, y = cell.x, cell.y
            
            # Update the cell's background color
            self.canvas.create_rectangle(
                y * self.cell_size, x * self.cell_size,
                (y + 1) * self.cell_size, (x + 1) * self.cell_size,
                fill=path_color, tags=f"cell_{x}_{y}"
            )
            
            # Update the g/h cost text on the cell
            text = f'g={cell.g}\nh={cell.h}'
            self.canvas.delete(f"text_{x}_{y}")
            self.canvas.create_text(
                (y + 0.5) * self.cell_size,
                (x + 0.5) * self.cell_size,
                text=text,
                font=("Purisa", 8),
                tags=f"text_{x}_{y}"
            )
            
            # Animate the agent moving to this cell
            self.canvas.delete("agent")
            self.canvas.create_rectangle(
                y * self.cell_size, x * self.cell_size, 
                (y + 1) * self.cell_size, (x + 1) * self.cell_size, 
                fill='navy', tags="agent"
            )
            
            # Wait for the animation delay
            self.root.update()
            self.root.after(self.animation_delay)

    ############################################################
    #### Program Termination Conditions Checker
    ############################################################
    def terminate_program(self):
        
        # All requests completed (SUCCESS)
        if self.completed_goals == self.total_goals and self.total_goals > 0:
            print("\n" + "#" * 50)
            print("#### PROGRAM TERMINATION: SUCCESS (All Tasks Completed)")
            print(f"#### All {self.completed_goals} delivery requests were successfully completed.")
            print("#" * 50)
        
        # Some requests completed (SUCCESS with caveats)
        elif 0 < self.completed_goals < self.total_goals:
            print("\n" + "#" * 50)
            print("#### PROGRAM TERMINATION: SUCCESS (Partial Completion)")
            print(f"#### {self.completed_goals} out of {self.total_goals} requests were successfully completed.")
            print("#### The map shows the completed optimum paths.")
            print("#" * 50)
            
        # No tasks completed (FAILURE)
        elif self.completed_goals == 0 and self.total_goals > 0:
            print("\n" + "#" * 50)
            print("#### PROGRAM TERMINATION: FAILURE (Blocked Paths)")
            print("#### WARNING: The robot was not able to complete any of its tasks.")
            print(f"#### All {self.total_goals} delivery paths were blocked. Please check the maze input.")
            print("#" * 50)
        
        # No goals were loaded from the input file
        else:
            print("\n" + "#" * 50)
            print("#### PROGRAM TERMINATION: No Goals Defined")
            print("#### No delivery requests were found in the input file.")
            print("#" * 50)        

    ############################################################
    #### Move agent manually with arrow keys (optional)
    ############################################################
    def move_agent(self, event):
        r, c = self.agent_pos

        #### Move right, if possible
        if event.keysym == 'Right' and c + 1 < self.cols and not self.cells[r][c + 1].is_wall:
            self.agent_pos = (r, c + 1)

        #### Move Left, if possible            
        elif event.keysym == 'Left' and c - 1 >= 0 and not self.cells[r][c - 1].is_wall:
            self.agent_pos = (r, c - 1)
        
        #### Move Down, if possible
        elif event.keysym == 'Down' and r + 1 < self.rows and not self.cells[r + 1][c].is_wall:
            self.agent_pos = (r + 1, c)
   
        #### Move Up, if possible   
        elif event.keysym == 'Up' and r - 1 >= 0 and not self.cells[r - 1][c].is_wall:
            self.agent_pos = (r - 1, c)

        #### Erase agent from the previous cell at time t
        self.canvas.delete("agent")

        ### Redraw the agent in color navy in the new cell position at time t+1
        self.canvas.create_rectangle(
            self.agent_pos[1] * self.cell_size, self.agent_pos[0] * self.cell_size, 
            (self.agent_pos[1] + 1) * self.cell_size, (self.agent_pos[0] + 1) * self.cell_size, 
            fill='navy', tags="agent"
        )


############################################################
#### Maze definition
############################################################
maze = [
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 5, 5, 5, 5, 5, 5, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 5, 5, 5, 5, 5, 5, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 5, 5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 5, 5, 5, 5, 5, 5, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 5, 5, 5, 5, 5, 5, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 5, 1, 3, 3, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0],
    [1, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 1, 4, 4, 4, 1, 2, 2, 2, 0],
    [1, 0, 0, 0, 9, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 0, 4, 4, 4, 4, 1, 2, 2, 1, 0],
    [1, 0, 0, 0, 1, 9, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 9, 1, 0, 1, 4, 4, 4, 1, 2, 2, 1, 0],
    [1, 0, 0, 0, 1, 9, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 9, 1, 0, 1, 4, 4, 4, 1, 2, 2, 2, 0],
    [1, 0, 0, 0, 1, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 9, 9, 0, 4, 4, 4, 4, 1, 2, 2, 1, 0],
    [1, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [1, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 1, 4, 4, 0, 1, 8, 1, 2, 2, 2, 2, 2, 0],
    [1, 0, 0, 0, 1, 1, 1, 7, 1, 1, 11, 1, 3, 3, 3, 4, 4, 1, 1, 4, 0, 1, 8, 1, 1, 1, 1, 1, 1, 0],
    [1, 0, 0, 0, 1, 7, 7, 7, 1, 1, 11, 1, 3, 3, 3, 1, 1, 7, 7, 1, 0, 8, 8, 8, 8, 8, 8, 8, 1, 0],
    [1, 0, 0, 0, 1, 7, 7, 1, 11, 11, 11, 1, 3, 3, 3, 1, 1, 7, 7, 1, 0, 1, 8, 8, 8, 8, 8, 8, 1, 0],
    [1, 0, 0, 0, 1, 1, 7, 1, 1, 1, 11, 1, 1, 1, 0, 5, 1, 7, 1, 1, 0, 1, 1, 8, 8, 8, 8, 8, 1, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8, 8, 8, 8, 8, 1, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 8, 8, 8, 8, 8, 1, 0],
    [1, 1, 1, 0, 0, 1, 7, 7, 1, 1, 2, 2, 1, 1, 1, 1, 1, 0, 1, 6, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 0, 0, 1, 7, 7, 7, 7, 1, 1, 12, 12, 12, 12, 1, 0, 6, 6, 1, 7, 7, 7, 7, 7, 7, 1, 1, 1],
    [1, 1, 1, 0, 0, 7, 7, 7, 1, 1, 10, 10, 1, 1, 1, 1, 10, 0, 6, 6, 1, 7, 7, 7, 7, 7, 7, 1, 1, 1],
    [1, 1, 0, 0, 0, 1, 1, 1, 10, 10, 10, 10, 10, 10, 10, 1, 10, 0, 6, 6, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 1, 1],
    [1, 1, 9, 0, 7, 1, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 1, 6, 1, 13, 6, 13, 1, 6, 6, 6, 6, 1, 1],
    [1, 1, 0, 0, 7, 1, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 1, 6, 1, 13, 13, 13, 1, 6, 6, 6, 6, 1, 1],
    [1, 1, 0, 0, 0, 1, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 1, 6, 1, 13, 13, 13, 1, 6, 6, 6, 6, 1, 1],
    [1, 1, 9, 9, 9, 1, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 1, 6, 1, 13, 13, 13, 1, 6, 6, 6, 6, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

############################################################
#### The mainloop activates the GUI.
############################################################
if __name__ == "__main__":
    base_name = input("Enter input file number or name: ").strip()

    # Build full filename automatically
    if base_name.isdigit():
        filename = f"inputfile{base_name}.txt"
    else:
        filename = f"inputfile_{base_name.upper()}.txt"

    root = tk.Tk()
    root.title("A* Maze - Hospital Delivery")

    game = MazeGame(root, maze, filename)
    root.bind("<KeyPress>", game.move_agent)

    root.mainloop()