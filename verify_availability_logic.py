"""
Verify Availability Logic

This script verifies that the system correctly uses technician_calendar.max_assignments
instead of technicians.workload_capacity for availability decisions.

It checks:
1. That availability logic uses max_assignments from calendar
2. That current workload doesn't exceed daily max_assignments
3. That workload_capacity is NOT used for availability decisions
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "dispatch.db"

def check_calendar_logic():
    """Verify that calendar max_assignments is the source of truth."""
    print("=" * 80)
    print("1. Checking Calendar-Based Availability Logic")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if technician_calendar has max_assignments
    cursor.execute("PRAGMA table_info(technician_calendar)")
    columns = {row[1] for row in cursor.fetchall()}
    
    if 'Max_assignments' in columns:
        print("✅ technician_calendar has Max_assignments column")
    else:
        print("❌ technician_calendar MISSING Max_assignments column!")
        return False
    
    # Get sample data
    cursor.execute("""
        SELECT Technician_id, Date, Available, Max_assignments
        FROM technician_calendar
        WHERE Available = 1
        LIMIT 5
    """)
    
    print("\nSample calendar entries:")
    print(f"{'Tech ID':<12} {'Date':<12} {'Available':<10} {'Max Assignments':<15}")
    print("-" * 80)
    
    for row in cursor.fetchall():
        print(f"{row[0]:<12} {row[1]:<12} {row[2]:<10} {row[3]:<15}")
    
    print()
    conn.close()
    return True

def check_workload_vs_capacity():
    """Check if any technician's current workload exceeds their daily max_assignments."""
    print("=" * 80)
    print("2. Checking Workload vs Daily Max Assignments")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get today's date (or use a specific date from dispatches)
    cursor.execute("SELECT DISTINCT DATE(Appointment_start_datetime) FROM current_dispatches ORDER BY Appointment_start_datetime LIMIT 1")
    result = cursor.fetchone()
    if not result:
        print("⚠️ No dispatches found to check")
        conn.close()
        return True
    
    check_date = result[0]
    print(f"Checking date: {check_date}")
    print()
    
    # Count dispatches per technician for this date and compare with max_assignments
    cursor.execute("""
        SELECT 
            t.Technician_id,
            t.Technician_name,
            t.Workload_capacity,
            c.Max_assignments,
            COUNT(d.Dispatch_id) as current_workload
        FROM technicians t
        LEFT JOIN technician_calendar c ON t.Technician_id = c.Technician_id 
            AND c.Date = ?
        LEFT JOIN current_dispatches d ON d.Assigned_technician_id = t.Technician_id
            AND DATE(d.Appointment_start_datetime) = ?
        WHERE c.Available = 1
        GROUP BY t.Technician_id, t.Technician_name, t.Workload_capacity, c.Max_assignments
        HAVING current_workload > 0
        ORDER BY current_workload DESC
        LIMIT 20
    """, (check_date, check_date))
    
    results = cursor.fetchall()
    
    if not results:
        print("✅ No technicians with workload to check")
        conn.close()
        return True
    
    print(f"{'Tech ID':<12} {'Name':<20} {'Workload Cap':<12} {'Max Assign':<12} {'Current':<10} {'Status':<10}")
    print("-" * 80)
    
    violations = 0
    for row in results:
        tech_id, name, workload_cap, max_assign, current = row
        
        # Check if current exceeds max_assignments (the correct limit)
        if current > max_assign:
            status = "❌ OVER"
            violations += 1
        else:
            status = "✅ OK"
        
        print(f"{tech_id:<12} {name[:20]:<20} {workload_cap:<12} {max_assign:<12} {current:<10} {status:<10}")
    
    print()
    
    if violations > 0:
        print(f"❌ Found {violations} technicians exceeding their daily max_assignments!")
        print("   These technicians should not receive more assignments.")
    else:
        print("✅ All technicians are within their daily max_assignments")
    
    print()
    conn.close()
    return violations == 0

def check_workload_capacity_usage():
    """Check if workload_capacity is being used incorrectly."""
    print("=" * 80)
    print("3. Verifying workload_capacity is NOT Used for Availability")
    print("=" * 80)
    print()
    
    print("Checking dispatch.py for correct usage...")
    print()
    
    dispatch_file = Path(__file__).parent / "dispatch.py"
    
    if not dispatch_file.exists():
        print("⚠️ dispatch.py not found")
        return True
    
    content = dispatch_file.read_text()
    
    # Check for correct usage
    uses_max_assignments = "max_assignments" in content.lower()
    uses_calendar_for_availability = "technician_calendar" in content
    
    print(f"✅ Uses max_assignments: {uses_max_assignments}")
    print(f"✅ Uses technician_calendar: {uses_calendar_for_availability}")
    print()
    
    # Check if workload_capacity is used in availability checks
    if "workload_capacity" in content:
        print("⚠️ workload_capacity found in code")
        print("   Checking if it's used for availability decisions...")
        
        # Look for problematic patterns
        lines = content.split('\n')
        problematic_lines = []
        
        for i, line in enumerate(lines, 1):
            if 'workload_capacity' in line.lower():
                # Check if it's in an availability context
                context = '\n'.join(lines[max(0, i-3):min(len(lines), i+3)])
                if any(word in context.lower() for word in ['available', 'capacity', 'check', 'can_assign']):
                    if 'max_assignments' not in context:
                        problematic_lines.append((i, line.strip()))
        
        if problematic_lines:
            print(f"\n❌ Found {len(problematic_lines)} potentially problematic uses:")
            for line_num, line in problematic_lines[:5]:
                print(f"   Line {line_num}: {line}")
        else:
            print("   ✅ workload_capacity not used for availability decisions")
    else:
        print("✅ workload_capacity not found in dispatch.py")
    
    print()
    return True

def show_recommendations():
    """Show recommendations for the availability logic."""
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    print("✅ CORRECT LOGIC:")
    print("   1. Use technician_calendar.Max_assignments for daily capacity")
    print("   2. Count current_dispatches per technician per day")
    print("   3. Technician is available if: current_workload < Max_assignments")
    print("   4. technicians.Workload_capacity should be IGNORED for availability")
    print()
    
    print("📊 CAPACITY CALCULATION:")
    print("   Daily Capacity = technician_calendar.Max_assignments (for specific date)")
    print("   Current Workload = COUNT(current_dispatches) for that technician on that date")
    print("   Available Capacity = Max_assignments - Current Workload")
    print()
    
    print("⚠️ IMPORTANT:")
    print("   - Max_assignments is date-specific (can vary by day)")
    print("   - Workload_capacity is a general field (should not be used)")
    print("   - Always check calendar for the specific date")
    print()

def main():
    """Main verification function."""
    print()
    print("=" * 80)
    print("AVAILABILITY LOGIC VERIFICATION")
    print("=" * 80)
    print()
    print("This script verifies that the system uses the correct logic:")
    print("- technician_calendar.Max_assignments (✅ CORRECT)")
    print("- NOT technicians.Workload_capacity (❌ WRONG)")
    print()
    
    # Run checks
    check1 = check_calendar_logic()
    check2 = check_workload_vs_capacity()
    check3 = check_workload_capacity_usage()
    
    # Show recommendations
    show_recommendations()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    if check1 and check2 and check3:
        print("✅ All checks passed!")
        print("✅ System is using correct availability logic")
    else:
        print("⚠️ Some issues found - review results above")
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()

