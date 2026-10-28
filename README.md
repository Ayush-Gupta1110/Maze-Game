# Maze Explorer ⚡

**Maze Explorer** is an original, complete, and polished 2D top-down labyrinth adventure built with Python 3.11+ and Pygame. Featuring procedural maze generation, intelligent multi-algorithm pathfinding, real-time AI Agent competition, memorization countdowns, dynamic blindness fog-of-war, and sleek neon geometry, the game delivers an exhilarating arcade experience with zero external asset dependencies.

---

## 🌟 Key Features

- **Race Against the Agent**:
  - Compete head-to-head against an intelligent AI agent navigating the labyrinth in real time.
  - The rival agent calculates optimal paths using the **A* Search algorithm**, picking up the Golden Key if required and racing to the Exit Portal.
  - Adjustable rival pacing based on difficulty: relaxed in Easy, brisk in Medium, and lightning-fast in Hard!
- **Clear Image Memorization Phase**:
  - At the start of each race round, the full labyrinth layout is clearly revealed for 4 seconds.
  - An animated countdown bar challenges the player to inspect corridors, key placement, and dead ends before darkness falls!
- **Dynamic Blindness & Fog of War**:
  - Once the memorization timer expires, deep blindness descends over the labyrinth.
  - Only a circular neon flashlight aura illuminates the corridors around the player.
  - If the Agent approaches your vicinity, catch glimpses of its glowing crimson trail through the dark!
- **Procedural Maze Generation**: True recursive backtracking generation guaranteeing fully connected labyrinths with zero unreachable cells, customizable dimensions, and optional random seed reproducibility.
- **Intelligent Pathfinding Suite**:
  - **A* Search (A-Star)**: Optimal shortest-path computation powered by an admissible Manhattan distance heuristic.
  - **Breadth-First Search (BFS)**: Unweighted shortest-path verification.
  - **Depth-First Search (DFS)**: Deep exploration traversal.
  - **Objective-Aware Hints**: Displays glowing breadcrumb trails directing the player to the Golden Key (if required) and onward to the Exit Portal.
- **Three Tiered Difficulty Modes**:
  - **Easy**: Relaxed $15 \times 15$ maze, generous hints (5), no strict timer pressure, slower rival agent.
  - **Medium**: Balanced $21 \times 21$ maze, 120-second timer, 3 hints, requires finding the Golden Key to unlock the exit.
  - **Hard**: Demanding $27 \times 27$ maze, 75-second countdown, strict 2-hint limit, higher collectible density, and aggressive A* rival speed.
- **Multi-Level Endless Progression**: Successfully clearing a maze preserves your cumulative score and advances you to higher levels with progressively challenging layouts.
- **Strategic Collectibles**:
  - **Gold Coins** ($+50\text{ pts}$): Scattered exploration rewards.
  - **Amethyst Gems** ($+150\text{ pts}$): Rare high-value treasures.
  - **Golden Key** ($+200\text{ pts}$): Essential artifact required to break the portal seal on Medium & Hard.
- **Persistent Player Settings**:
  - Local JSON storage remembers the selected difficulty.
  - Automatic error recovery for missing or corrupted settings.
- **Modern Dark Neon Aesthetics**:
  - Slate walls with neon borders, radiant cyan player aura, shimmering portals, particle sparkles, and responsive auto-scaling for any monitor resolution.

---

## 🛠️ Technology Stack

- **Programming Language**: Python 3.11+ (Tested on Python 3.12)
- **Game Engine**: Pygame 2.6+
- **Maze Generation**: Recursive Backtracking algorithm (`random`, stack-based)
- **Pathfinding & AI**: A*, Breadth-First Search (BFS), Depth-First Search (DFS) (`collections.deque`, `heapq`)
- **Persistence**: JSON serialization (`json`, `pathlib`)

---

## 📋 Prerequisites

- **Operating System**: Windows 10 / 11, macOS, or Linux.
- **Python**: Version `3.11` or higher installed and added to your system `PATH`.

Verify your installation:
```powershell
python --version
```

---

## 🚀 Installation & Setup (Windows PowerShell)

### 1. Clone or Open the Project Directory
```powershell
cd "c:\Maze Game"
```

### 2. Create and Activate a Virtual Environment (Recommended)
```powershell
# Create virtual environment
python -m venv .venv

# Activate in Windows PowerShell
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### 3. Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🎮 How to Run the Game

### Launch the Full Graphical Game
```powershell
python main.py
```

You can also double-click `run_game.bat` in the project folder to launch the game on Windows.
If the game cannot start, the launcher keeps the terminal open and shows the error.

### Advanced Command-Line Options
Maze Explorer supports several command-line flags for debugging, demonstration, and automated verification:

| Flag | Description | Example |
| :--- | :--- | :--- |
| `--difficulty` | Start directly with a specific difficulty (`Easy`, `Medium`, `Hard`) | `python main.py --difficulty Hard` |
| `--seed` | Set a fixed random seed for reproducible maze generation | `python main.py --seed 42` |
| `--headless` | Run in headless mode without opening a display window | `python main.py --headless` |
| `--frames` | Automatically terminate after rendering $N$ frames | `python main.py --headless --frames 120` |

---

## 🕹️ Game Controls

| Action | Primary Key | Secondary Key |
| :--- | :--- | :--- |
| **Move Up** | `Up Arrow` | `W` |
| **Move Down** | `Down Arrow` | `S` |
| **Move Left** | `Left Arrow` | `A` |
| **Move Right** | `Right Arrow` | `D` |
| **Pathfinding Hint** | `H` | — |
| **Pause / Resume** | `P` | `Escape` |
| **Restart Level** | `R` | — |
| **Return to Menu** | `M` | — |
| **Confirm / Select** | `Enter` | `Space` / `Mouse Click` |

---

## 🧠 Architectural Deep Dive

### 1. Procedural Maze Generation (`game/maze_generator.py`)
The generator uses an optimized, stack-based recursive backtracking algorithm to carve paths through an initial grid of walls:
1. Every grid coordinate with odd indices `(2i + 1, 2j + 1)` represents a potential corridor cell.
2. The generator starts at `(1, 1)`, marks it visited, and pushes it onto an explicit traversal stack.
3. At each step, unvisited 2-step orthogonal neighbors are evaluated. A random neighbor is selected, the wall between the two cells is carved open, and the neighbor is pushed to the stack.
4. When a dead end is reached, the stack unwinds until an open branch is discovered.
5. This guarantees that all walkable cells belong to a single spanning tree: **every path is connected, and there are no isolated cells or inaccessible loops**.
6. A subtle loop factor ($5\%$) is selectively applied to remove occasional dead-end walls, offering dynamic tactical shortcuts.

### 2. Pathfinding & Hint Routing (`game/pathfinding.py`)
- **A* Search**: Utilizes an admissible Manhattan distance heuristic $h(n) = |r_n - r_{goal}| + |c_n - c_{goal}|$ and a min-heap priority queue to determine the optimal shortest path in $O(V \log V)$ time.
- **BFS & DFS**: Provide alternative algorithmic benchmarks used in automated unit tests.
- **Objective Staging**: If the current level requires a Golden Key and the player has not yet picked it up, `get_hint_route()` computes a 2-stage multi-segment trajectory:
  $$\text{Player} \xrightarrow{\quad A^*\quad} \text{Golden Key} \xrightarrow{\quad A^*\quad} \text{Exit Portal}$$
  Once the key is acquired, the route seamlessly targets the Exit Portal directly.

### 3. AI Rival Agent & Fog of War (`game/agent.py`)
- **A* Search Engine**: The rival Agent computes the optimal step-by-step path to the Exit Portal (visiting the Golden Key first when required on Medium/Hard difficulties).
- **Delta-Time Movement**: The agent advances smoothly across corridors at difficulty-calibrated step intervals with visual position interpolation and a crimson particle trail.
- **Fog of War**: When blindness activates, the renderer constructs a dark fog layer with an alpha punch-hole centered on the player's position, preserving the top HUD.

---

## 📁 Project Structure

```
c:/Maze Game/
├── main.py                       # Application entry point & CLI parser
├── config.py                     # Central configuration constants & themes
├── requirements.txt              # Project dependencies (pygame)
├── README.md                     # Comprehensive project documentation
├── .gitignore                    # Python & environment ignore rules
├── game/
│   ├── __init__.py               # Package marker
│   ├── agent.py                  # A* AI rival agent entity and path execution
│   ├── app.py                    # Game loop, state machine & event handling
│   ├── maze_generator.py         # Recursive backtracking procedural generator
│   ├── pathfinding.py            # BFS, DFS, and A* pathfinding algorithms
│   ├── player.py                 # Movement logic, collisions & inventory
│   ├── renderer.py               # Dark neon UI, HUD, blindness fog, particle engine
│   └── storage.py                # JSON persistence for player settings
├── assets/
│   └── README.md                 # Procedural asset documentation
├── data/
│   ├── .gitkeep                  # Preserves directory in version control
│   └── settings.json             # Persistent user preferences
```

---

## 🛡️ Reliability & Error Handling

- **Display Scaling**: The renderer dynamically calculates cell sizes and centering offsets, ensuring mazes from $15 \times 15$ up to $35 \times 35$ fit cleanly within the viewport.
- **Corrupted Storage Recovery**: If `settings.json` contains malformed JSON or invalid types, default configurations are safely restored without crashing.
- **Graceful Audio Degradation**: If running on headless servers or systems without audio drivers, `SoundManager` catches initialization errors and disables audio automatically.

---

## 🏆 Scoring Rules

- **Base Clear Bonus**: Awarded upon reaching the exit portal ($500\text{ pts}$ on Easy, $1000\text{ pts}$ on Medium, $2000\text{ pts}$ on Hard).
- **Collectibles**:
  - Coin: $+50\text{ pts}$
  - Gem: $+150\text{ pts}$
  - Golden Key: $+200\text{ pts}$
- **Speed Bonus**: In timed modes, remaining seconds are multiplied by $+25\text{ pts}$.
- **Hint Management**: Hints are limited per level ($5$ on Easy, $3$ on Medium, $2$ on Hard) and incur a cooldown timer.
