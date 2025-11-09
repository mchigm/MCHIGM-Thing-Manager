# Quick Start Guide

## Getting Started with MCHIGM Thing Manager

### 1. Installation

**On Linux (Debian/Ubuntu/MintOS):**
```bash
# Install dependencies
sudo apt-get update
sudo apt-get install nasm build-essential

# Clone and build
git clone https://github.com/mchigm/MCHIGM-Thing-Manager.git
cd MCHIGM-Thing-Manager
make
```

### 2. Running the Application

```bash
./thing-manager
```

### 3. Your First Time Planner

1. When the menu appears, press `1` and Enter
2. Enter a name for your planner (e.g., "Morning Exercise")
3. Enter a description (e.g., "30 minute workout")
4. Enter a time in HH:MM format (e.g., "07:00")
5. You'll see "Time planner created successfully!"

### 4. Your First Timetable

1. From the main menu, press `2` and Enter
2. Enter a name (e.g., "Team Standup")
3. Enter a day (e.g., "Monday")
4. Enter a time slot (e.g., "09:00-09:30")
5. You'll see "Timetable created successfully!"

### 5. Viewing Your Items

1. From the main menu, press `3` and Enter
2. All your planners and timetables will be displayed

### 6. Exiting

Press `4` and Enter to exit the application.

## Example Session

```
=== MCHIGM Thing Manager ===

Main Menu:
1. Create Time Planner
2. Create Timetable
3. List All Items
4. Exit
Select option: 1

Enter time planner name (max 50 chars): Morning Workout
Enter description (max 100 chars): 5km run in the park
Enter time (HH:MM format): 06:30

Time planner created successfully!

Main Menu:
1. Create Time Planner
2. Create Timetable
3. List All Items
4. Exit
Select option: 2

Enter timetable name (max 50 chars): Team Meeting
Enter day (Monday-Sunday): Monday
Enter time slot (e.g., 09:00-10:00): 10:00-11:00

Timetable created successfully!

Main Menu:
1. Create Time Planner
2. Create Timetable
3. List All Items
4. Exit
Select option: 3

=== All Items ===
Time Planner: Morning Workout
5km run in the park
06:30

Timetable: Team Meeting
Monday
10:00-11:00

Main Menu:
1. Create Time Planner
2. Create Timetable
3. List All Items
4. Exit
Select option: 4

Thank you for using MCHIGM Thing Manager!
```

## Tips

- **Data Persistence**: Your data is saved in the `data/` directory
- **Multiple Items**: You can create as many planners and timetables as you need
- **File Storage**: Data is stored in plain text files for easy backup
- **Max Lengths**:
  - Names: 50 characters
  - Descriptions: 100 characters
  - Time: 10 characters (HH:MM format)
  - Day: 15 characters
  - Time slot: 20 characters

## Troubleshooting

**Program won't build:**
- Make sure NASM is installed: `nasm -v`
- Make sure you're on a Linux x86-64 system

**Data not saving:**
- Check that the `data/` directory exists
- Check file permissions in the data directory

**Need to start fresh:**
```bash
make clean
rm -rf data/*.txt
make
```

## What's Next?

- Create more planners and timetables
- Organize your daily schedule
- Track your time commitments
- Use the application as part of your productivity workflow

For more details, see the full [README.md](../README.md) and [Assembly Guide](ASSEMBLY_GUIDE.md).
