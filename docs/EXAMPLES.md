# Example Data Files

This directory contains example data files showing the format used by MCHIGM Thing Manager.

## Planners Example (planners.txt)

```
Time Planner: Morning Exercise
30 minute cardio workout
07:00

Time Planner: Lunch Break
Take a healthy lunch break
12:30

Time Planner: Evening Review
Review the day's accomplishments and plan tomorrow
21:00
```

## Timetables Example (timetables.txt)

```
Timetable: Team Standup
Monday
09:00-09:30

Timetable: Weekly Planning
Friday
14:00-15:00

Timetable: Client Call
Wednesday
11:00-12:00
```

## File Format Notes

### Time Planner Format
Each time planner entry consists of:
- Label: "Time Planner: "
- Name (up to 50 characters)
- Description (up to 100 characters)
- Time (HH:MM format)
- Blank line separator

### Timetable Format
Each timetable entry consists of:
- Label: "Timetable: "
- Name (up to 50 characters)
- Day of week
- Time slot (e.g., HH:MM-HH:MM)
- Blank line separator

## Data Location

By default, data files are stored in:
```
MCHIGM-Thing-Manager/
└── data/
    ├── planners.txt
    └── timetables.txt
```

## Backup and Restore

### Backup
```bash
cp -r data/ data-backup/
```

### Restore
```bash
cp -r data-backup/* data/
```

## Manual Editing

You can manually edit the data files if needed, but be careful to maintain the correct format:
- Keep the labels intact
- Respect the character limits
- Maintain the structure

## Import/Export

To share your planners and timetables:

**Export:**
```bash
tar -czf my-planners-$(date +%Y%m%d).tar.gz data/
```

**Import:**
```bash
tar -xzf my-planners-20231109.tar.gz
```
