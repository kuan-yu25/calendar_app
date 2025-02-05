import sqlite3, threading, time, sys
from datetime import datetime, timedelta
from functools import wraps

def db_connection(func):
    """裝飾器，自動管理資料庫連接和關閉"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            result = func(self, cursor, *args, **kwargs)
            conn.commit()
            return result
        except sqlite3.Error as e:
            sys.stderr.write(f"資料庫錯誤: {e}\n")
        finally:
            if conn:
                conn.close()
    return wrapper

class CalendarApp:
    # 初始化
    def __init__(self, db_name="calendar.db"):
        # 指定資料庫名稱，並初始化資料庫
        self.db_name = db_name
        self.init_db()
        # 控制通知執行緒的運行
        self.running = True

    # 初始化資料庫及表格
    @db_connection
    def init_db(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY ,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                notified INTEGER DEFAULT 0
            )
        ''')

    # 增加待辦
    @db_connection
    def add_event(self, cursor, date, time, title, description):
        try:
            cursor.execute('''
                INSERT INTO events (date, time, title, description, notified)
                VALUES (?, ?, ?, ?, 0)
            ''', (date, time, title, description))
            print("\nEvent added successfully!\n")
        except Exception as e:
            sys.stderr.write(f"Failed to add record(s): {e}\n")

    # 檢視待辦，並依時間順序排列
    @db_connection
    def view_events(self, cursor):
        try:
            cursor.execute('''
                SELECT * FROM events
                ORDER BY date ASC, time ASC
            ''')
            records = cursor.fetchall()
        except Exception as e:
            sys.stderr.write(f"Error loading schedule: {e}\n")
            records = []

        # 如果沒有待辦
        if not records:
            print("No events found!\n")
            return []

        # 格式化輸出清單
        print("\nYour Events:")
        print(f"{'ID':<4} | {'Date':<12} | {'Time':<8} | {'Title':<20} | {'Description'}")
        print("-" * 60)
        for row in records:
            print(f"{row[0]:<4} | {row[1]:<12} | {row[2]:<8} | {row[3]:<20} | {row[4]}")
        print()
        return records

    # 檢查資料庫是否為空
    @db_connection
    def test_data(self, cursor):
        cursor.execute('SELECT * FROM events')
        all_records = cursor.fetchall()

        # 若無待辦給出指示
        if not all_records:
            sys.stderr.write("No schedules found. Please add some events first.\n\n")
            return False
        return True

    # 檢查ID是否存在
    @db_connection
    def test_ID(self, cursor, event_id):
        cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
        record = cursor.fetchone()

        # 若ID無效提示使用者
        if record is None:
            sys.stderr.write(f"No event found with ID: {event_id}\n\n")
            return False
        return True

    # 用ID刪除資料
    @db_connection
    def delete_event(self, cursor, event_id):
        try:
            cursor.execute('''
                DELETE FROM events WHERE id = ?
            ''', (event_id,))
            print("\nEvent deleted successfully!\n")
        except Exception as e:
            print(f"An error occurred: {e}\n")

    # 用ID修改現有資料
    @db_connection
    def modify_event(self, cursor, event_id, date, time, title, description):
        try:
            cursor.execute('''
                UPDATE events
                SET date = ?, time = ?, title = ?, description = ?
                WHERE id = ?
            ''', (date, time, title, description, event_id))
            print("\nEvent modified successfully!\n")
        except Exception as e:
            print(f"An error occurred: {e}\n")

    # 用日期找到當天待辦
    @db_connection
    def find_events_by_date(self, cursor, date):
        cursor.execute('''
            SELECT * FROM events
            WHERE date = ?
            ORDER BY time ASC
        ''', (date,))
        records = cursor.fetchall()

        # 如果指定日期沒有待辦
        if not records:
            print(f"No events found for {date}\n")
            return

        print(f"\nEvents on {date}:")
        print(f"{'ID':<4} | {'Time':<8} | {'Title':<20} | {'Description'}")
        print("-" * 50)
        for row in records:
            print(f"{row[0]:<4} | {row[2]:<8} | {row[3]:<20} | {row[4]}")
        print()

    # 主程式
    def main_menu(self):

        while True:
            print("--- Calendar App ---")
            print("1. Add Event")
            print("2. View Events")
            print("3. Delete Event")
            print("4. Modify Event")
            print("5. Find Events by Date")
            print("6. Exit")
            choice = input("Enter your choice: ")

            if choice == '1':
                date = input("Enter date (YYYY-MM-DD): ")
                time = input("Enter time (HH:MM): ")
                title = input("Enter event title: ")
                description = input("Enter description: ")
                try:
                    datetime.strptime(date, "%Y-%m-%d")  # 驗證日期格式
                    datetime.strptime(time, "%H:%M")    # 驗證時間格式
                    self.add_event(date, time, title, description)
                except ValueError:
                    print("Invalid date or time format! Please try again.\n")

            elif choice == '2':
                self.view_events()

            elif choice == '3':
                records = self.view_events()
                if not records:
                    continue
                event_id = input("Enter Event ID to delete: ")
                if event_id.isdigit():
                    if not self.test_ID(event_id):
                        continue
                    self.delete_event(event_id)
                else:
                    print("Invalid ID! Please enter a number.\n")

            elif choice == '4':
                records = self.view_events()
                if not records:
                    continue
                event_id = input("Enter Event ID to modify: ")
                if event_id.isdigit():
                    if not self.test_ID(event_id):
                        continue
                    event_id = int(event_id)
                    date = input("Enter new date (YYYY-MM-DD): ")
                    time = input("Enter new time (HH:MM): ")
                    title = input("Enter new event title: ")
                    description = input("Enter new description: ")
                    try:
                        datetime.strptime(date, "%Y-%m-%d")
                        datetime.strptime(time, "%H:%M")
                        self.modify_event(event_id, date, time, title, description)
                    except ValueError:
                        print("Invalid date or time format! Please try again.\n")
                else:
                    print("Invalid ID! Please enter a number.\n")

            elif choice == '5':
                date = input("Enter date (YYYY-MM-DD) to find events: ")
                try:
                    datetime.strptime(date, "%Y-%m-%d")
                    self.find_events_by_date(date)
                except ValueError:
                    print("Invalid date format! Please use YYYY-MM-DD.\n")

            elif choice == '6':
                print("Goodbye!")
                self.running = False  # 停止通知執行緒
                break

            else:
                print("Invalid choice! Please try again.\n")

if __name__ == "__main__":
    app = CalendarApp()
    app.main_menu()
