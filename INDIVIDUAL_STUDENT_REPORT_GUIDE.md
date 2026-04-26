# Individual Student Report Feature - User Guide

## Overview
The Reports page now includes two separate reporting systems:
1. **Batch Report** - View attendance by Batch, Course, Semester, and Paper
2. **Individual Student Report** - View attendance for a specific student by roll number

## How to Use Individual Student Report

### Step 1: Search for Student
1. Navigate to the **Reports** page
2. Scroll to the **"Individual Student Report"** section
3. Enter the student's **Roll Number** in the input field
4. Click the **Search** button (magnifying glass icon)
5. The system will display the student's details if found:
   - Name
   - Roll Number
   - Course
   - Semester

### Step 2: Select Paper (Optional)
1. After finding a student, the **Paper** dropdown will be enabled
2. By default, **"All Papers"** is selected
3. To filter attendance by a specific paper/subject:
   - Click the **Paper** dropdown
   - Select the desired paper/subject
   - The report will only show attendance for that paper

### Step 3: Set Date Range
1. The **Start Date** and **End Date** fields are pre-filled with:
   - Start Date: First day of current month
   - End Date: Today's date
2. To customize the date range:
   - Click on **Start Date** and select your desired start date
   - Click on **End Date** and select your desired end date
3. The report will include all attendance records within this range

### Step 4: Generate Report
1. Click the **"Generate Student Report"** button (green button)
2. The system will:
   - Fetch attendance records for the selected date range
   - Filter by paper if one was selected
   - Calculate attendance statistics
   - Display detailed attendance records in a table

### Step 5: View Report Details
The report shows:
- **Attendance Table**: Lists all attendance records with:
  - Date
  - Paper/Subject Name
  - Status (Present, Absent, or Late)

- **Summary Statistics**:
  - Total Days: Number of days attendance was marked
  - Present: Number of days marked present
  - Absent: Number of days marked absent
  - Late: Number of days marked late
  - Attendance Percentage: Calculated as (Present + Late) / Total Days × 100

### Step 6: Download Report
1. Click the **"Download CSV"** button at the top right of the report
2. The system will download a CSV file with:
   - File name: `student_report_{roll_number}_{date}.csv`
   - Student details
   - Complete attendance records
   - Summary statistics

## Example Workflow

**Scenario**: Check attendance for student with roll number "CSE001" for January 2026, specifically for the "Data Structures" paper.

**Steps**:
1. Enter "CSE001" in Roll Number field
2. Click Search → Student "Akshay Kumar" found (CSE, Semester 3)
3. Select "Data Structures" from Paper dropdown
4. Set Start Date: 01/01/2026
5. Set End Date: 31/01/2026
6. Click Generate Student Report
7. View the detailed attendance records and summary
8. Click Download CSV to save the report

## Tips and Tricks

### Searching Tips
- Roll number search is **case-insensitive** (CSE001, cse001, Cse001 all work)
- Make sure the exact roll number is entered
- Check the search result message for confirmation

### Paper Selection
- Leave Paper as "All Papers" to see attendance for all subjects
- Paper dropdown is only enabled after a valid student is found
- Papers are specific to the student's course and semester

### Date Range Tips
- Use the calendar picker for easy date selection
- Start Date must be before or equal to End Date
- Both dates are required to generate the report
- Attendance records outside the date range will not be shown

### Report Download
- CSV files can be opened in Excel or any spreadsheet application
- The file includes both detailed records and summary statistics
- File name includes roll number and download date for easy identification

## Troubleshooting

### "No student found with roll number: XXX"
- Check the spelling of the roll number
- Ensure the student is registered in the system
- Try without leading/trailing spaces

### Paper dropdown is disabled
- This only happens if the student has no papers configured
- Contact administrator to assign papers to the student

### No attendance records found
- Check if attendance has been marked for the selected student
- Verify the date range includes attendance entries
- Try expanding the date range

### 0% Attendance
- This occurs when no attendance records are found for the student in the date range
- Verify attendance has been marked for this student
- Check if the selected paper matches the attendance records

## Notes
- The Individual Student Report feature works independently from the Batch Report
- Both features can be used simultaneously without affecting each other
- Original Batch Report functionality remains unchanged
- All date ranges are inclusive (includes both start and end dates)

---
**Last Updated**: April 2026
**Version**: 1.0
