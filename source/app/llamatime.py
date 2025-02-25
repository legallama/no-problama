import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import Menu
import csv
from datetime import datetime, timedelta
from collections import defaultdict
from fpdf import FPDF
import pystray
from PIL import Image, ImageDraw, ImageFont
from tkcalendar import DateEntry
import threading
import time
import shutil
import matplotlib.pyplot as plt
import os
import tempfile
from threading import Timer
from tkinter import simpledialog
import winsound


class ReminderSystem:
    def __init__(self, app):
        self.app = app
        self.reminder_timer = None
        self.reminder_interval = 30 * 60  # 30 minutes

    def start_reminder(self):
        self.stop_reminder()  # Cancel any existing reminder
        self.reminder_timer = Timer(self.reminder_interval, self.show_reminder)
        self.reminder_timer.start()

    def stop_reminder(self):
        if self.reminder_timer:
            self.reminder_timer.cancel()

    def show_reminder(self):
        # Play a sound when the reminder is shown
        winsound.PlaySound("SystemHand", winsound.SND_ALIAS)

        if not self.app.is_timer_running:
            messagebox.showinfo("Reminder", "Don't forget to start your timer!")
        else:
            messagebox.showinfo("Reminder", "Remember to stop your timer if you're done working!")
        self.start_reminder()  # Schedule the next reminder


class TimeEntryApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Llama Time")
        self.apply_light_style()
        self.tray_icon_created = False
        self.reminder_system = ReminderSystem(self)

       # List to store time entries
        self.entries = []
        # Index of the currently selected entry in the listbox
        self.selected_entry_index = None
        # Dictionary to store total time spent on each project
        self.total_time = defaultdict(timedelta)
        # Flag to track if the timer is running
        self.is_timer_running = False
        # Start time of the timer
        self.start_time = None
        # Elapsed time of the timer
        self.elapsed_time = timedelta()
        
        # Set the icon
        icon = tk.PhotoImage(file="no-problama-master/source/app/llama-icon.gif")
        self.root.iconphoto(False, icon)

        # Apply dark style to the UI
        self.apply_light_style()

        # Create UI components
        self.create_widgets()

        # Load existing entries from the CSV file
        self.load_entries()

        # Configure grid layout
        self.configure_grid()

        # Create the menu bar
        menu_bar = Menu(root)
        root.config(menu=menu_bar)

        # Add File menu items
        file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New")
        file_menu.add_command(label="Open")
        file_menu.add_command(label="Save")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)

        # Create the edit report bar items
        edit_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo")
        edit_menu.add_command(label="Redo")

        # Create the help report bar items
        reports_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Reports", menu=reports_menu)
        reports_menu.add_command(label="Updates")
        reports_menu.add_separator()
        reports_menu.add_command(label="Docs")
        reports_menu.add_command(label="Support")
        
        # Create the views menu bar items
        view_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Dark Theme", command=self.apply_dark_style)
        view_menu.add_command(label="Light Theme", command=self.apply_light_style)

        # Create the tools menu bar items
        tools_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Set Reminder Interval", command=self.set_reminder_interval)
        tools_menu.add_separator()
        tools_menu.add_command(label="Backup Data", command=self.backup_data)
        tools_menu.add_command(label="Restore Data", command=self.restore_data)

        # Create the help menu bar items
        help_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_separator()
        help_menu.add_command(label="Update")
        help_menu.add_command(label="Documents")

        # Create the system tray icon
        self.create_system_tray()

        # Update timer in system tray
        self.update_timer_in_tray()

    def apply_light_style(self):
        self.root.configure(bg="#f0f0f0")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#f0f0f0", foreground="black")
        style.configure("TButton", background="#e0e0e0", foreground="black")
        style.configure("TEntry", fieldbackground="white", foreground="black")
        style.configure("TCombobox", fieldbackground="white", foreground="black")
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TListbox", background="white", foreground="black")
        style.configure("Danger.TButton", background="red", foreground="black")

    def apply_dark_style(self):
        self.root.configure(bg="#2e2e2e")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#2e2e2e", foreground="white")
        style.configure("TButton", background="#555555", foreground="white")
        style.configure("TEntry", fieldbackground="#3e3e3e", foreground="white")
        style.configure("TCombobox", fieldbackground="#3e3e3e", foreground="black")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TListbox", background="#3e3e3e", foreground="white")
        style.configure("Danger.TButton", background="red", foreground="white")

        # Create backup data
    def backup_data(self):
        try:
            shutil.copy("time_entries.csv", "time_entries_backup.csv")
            messagebox.showinfo("Backup Success", "Data backup created successfully.")
        except Exception as e:
            messagebox.showerror("Backup Error", f"An error occurred while creating the backup: {str(e)}")

        # Restore data from backup
    def restore_data(self):
        try:
            shutil.copy("time_entries_backup.csv", "time_entries.csv")
            messagebox.showinfo("Restore Success", "Data restored from backup successfully.")
            self.load_entries()
        except Exception as e:
            messagebox.showerror("Restore Error", f"An error occurred while restoring the backup: {str(e)}")

    def create_widgets(self):
        # Project Name
        self.project_label = ttk.Label(self.root, text="Project Name:")
        self.project_label.grid(column=0, row=0, padx=5, pady=5, sticky="w")
        self.project_entry = ttk.Entry(self.root, width=30)
        self.project_entry.grid(column=1, row=0, padx=5, pady=5, sticky="ew")

        # Date
        self.date_label = ttk.Label(self.root, text="Date (YYYY-MM-DD):")
        self.date_label.grid(column=0, row=1, padx=5, pady=5, sticky="w")
        self.date_entry = DateEntry(self.root, width=30, background='darkblue',
                foreground='white', borderwidth=2, year=datetime.now().year,
                month=datetime.now().month, day=datetime.now().day, date_pattern='yyyy-mm-dd')
        self.date_entry.grid(column=1, row=1, padx=5, pady=5, sticky="ew")

        # Start Time
        self.start_time_label = ttk.Label(self.root, text="Start Time:")
        self.start_time_label.grid(column=0, row=2, padx=5, pady=10, sticky="w")
        self.start_time_entry = self.create_time_picker(self.root)
        self.start_time_entry.grid(column=1, row=2, padx=5, pady=10, sticky="ew")

        # End Time
        self.end_time_label = ttk.Label(self.root, text="End Time:")
        self.end_time_label.grid(column=0, row=3, padx=5, pady=5, sticky="w")
        self.end_time_entry = self.create_time_picker(self.root)
        self.end_time_entry.grid(column=1, row=3, padx=5, pady=5, sticky="ew")

        # Note
        self.note_label = ttk.Label(self.root, text="Notes:")
        self.note_label.grid(column=0, row=4, padx=5, pady=2, sticky="w")
        self.note_entry = tk.Text(self.root, height=4, width=25)  # Change the height value here
        self.note_entry.grid(column=0, row=5, padx=5, pady=2, sticky="ew")

        # Start/Stop Button
        self.start_stop_button = ttk.Button(self.root, text="Start", command=self.toggle_timer)
        self.start_stop_button.grid(column=1, row=5, padx=(0), pady=(0, 33), sticky="ew")

        # Submit Button
        self.submit_button = ttk.Button(self.root, text="Submit", command=self.save_entry)
        self.submit_button.grid(column=1, row=5, padx=(0), pady=(33, 0), sticky="ew")

        # Filter by Project
        self.filter_label = ttk.Label(self.root, text="Filter by Project:")
        self.filter_label.grid(column=0, row=7, padx=10, pady=5, sticky="w")
        self.filter_combobox = ttk.Combobox(self.root, state="readonly")
        self.filter_combobox.grid(column=1, row=7, padx=10, pady=5, sticky="ew")
        self.filter_combobox.bind("<<ComboboxSelected>>", self.filter_entries)

        # Start Date Filter
        self.start_date_filter_label = ttk.Label(self.root, text="Start Date (YYYY-MM-DD):")
        self.start_date_filter_label.grid(column=0, row=9, padx=10, pady=5, sticky="w")
        self.start_date_filter_entry = DateEntry(self.root, width=30, background='darkblue',
                    foreground='white', borderwidth=2, year=datetime.now().year,
                    month=datetime.now().month, day=datetime.now().day, date_pattern='yyyy-mm-dd')
        self.start_date_filter_entry.grid(column=1, row=9, padx=10, pady=5, sticky="ew")

        # End Date Filter
        self.end_date_filter_label = ttk.Label(self.root, text="End Date (YYYY-MM-DD):")
        self.end_date_filter_label.grid(column=0, row=10, padx=10, pady=5, sticky="w")
        self.end_date_filter_entry = DateEntry(self.root, width=30, background='darkblue',
                    foreground='white', borderwidth=2, year=datetime.now().year,
                    month=datetime.now().month, day=datetime.now().day, date_pattern='yyyy-mm-dd')
        self.end_date_filter_entry.grid(column=1, row=10, padx=10, pady=5, sticky="ew")

        self.filter_date_range_button = ttk.Button(self.root, text="Filter by Date Range", command=self.filter_entries_by_date_range)
        self.filter_date_range_button.grid(column=0, row=11, columnspan=2, padx=10, pady=5, sticky="ew")

        # Entries Display
        self.entries_frame = ttk.LabelFrame(self.root, text="Entries")
        self.entries_frame.grid(column=0, row=11, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        self.entries_listbox = tk.Listbox(self.entries_frame, height=10, width=60, bg="#3e3e3e", fg="white")
        self.entries_listbox.pack(padx=10, pady=11, fill="both", expand=True)
        self.entries_listbox.bind('<<ListboxSelect>>', self.on_select)

        # Edit and Delete Buttons
        self.edit_button = ttk.Button(self.root, text="Save Edit", command=self.edit_entry, state='enabled')
        self.edit_button.grid(column=0, row=12, padx=10, pady=5, sticky="ew")

        self.delete_button = ttk.Button(self.root, text="Delete", command=self.delete_entry, state='disabled')
        self.delete_button.grid(column=1, row=12, padx=10, pady=5, sticky="ew")

        # Total Time Display
        self.total_time_label = ttk.Label(self.root, text="Total Time Spent on Projects:")
        self.total_time_label.grid(column=0, row=13, padx=10, pady=5, sticky="w")
        self.total_time_text = tk.Text(self.root, height=5, width=60, state='disabled', bg="#3e3e3e", fg="white")
        self.total_time_text.grid(column=0, row=13, columnspan=2, padx=10, pady=5, sticky="nsew")

        # Sorting Buttons
        self.sort_project_button = ttk.Button(self.root, text="Sort by Project", command=lambda: self.sort_entries("project"))
        self.sort_project_button.grid(column=0, row=14, padx=10, pady=5, sticky="ew")

        self.sort_date_button = ttk.Button(self.root, text="Sort by Date", command=lambda: self.sort_entries("date"))
        self.sort_date_button.grid(column=1, row=14, padx=10, pady=5, sticky="ew")

        self.sort_total_time_button = ttk.Button(self.root, text="Sort by Total Time", command=lambda: self.sort_entries("total_time"))
        self.sort_total_time_button.grid(column=0, row=15, columnspan=2, padx=10, pady=5, sticky="ew")

        # Report Generation
        self.report_label = ttk.Label(self.root, text="Generate Report:")
        self.report_label.grid(column=0, row=16, padx=10, pady=5, sticky="w")
        
        self.start_date_label = ttk.Label(self.root, text="Start Date (YYYY-MM-DD):")
        self.start_date_label.grid(column=0, row=17, padx=10, pady=5, sticky="w")
        self.start_date_entry = DateEntry(self.root, width=30, background='darkblue',
                    foreground='white', borderwidth=2, year=datetime.now().year,
                    month=datetime.now().month, day=datetime.now().day, date_pattern='yyyy-mm-dd')
        self.start_date_entry.grid(column=1, row=17, padx=10, pady=5, sticky="ew")

        self.end_date_label = ttk.Label(self.root, text="End Date (YYYY-MM-DD):")
        self.end_date_label.grid(column=0, row=18, padx=10, pady=5, sticky="w")
        self.end_date_entry = DateEntry(self.root, width=30, background='darkblue',
                    foreground='white', borderwidth=2, year=datetime.now().year,
                    month=datetime.now().month, day=datetime.now().day, date_pattern='yyyy-mm-dd')
        self.end_date_entry.grid(column=1, row=18, padx=10, pady=5, sticky="ew")

        self.report_button = ttk.Button(self.root, text="Generate Report", command=self.generate_report)
        self.report_button.grid(column=0, row=19, columnspan=2, padx=10, pady=5, sticky="ew")

        # Export to PDF Button
        self.export_button = ttk.Button(self.root, text="Export to PDF", command=self.export_to_pdf)
        self.export_button.grid(column=0, row=20, columnspan=2, padx=10, pady=5, sticky="ew")
        
    
    def create_time_picker(self, parent):
        frame = ttk.Frame(parent)
        hours = ttk.Combobox(frame, values=[f"{i:02}" for i in range(24)], width=3, state="readonly")
        hours.current(0)
        hours.pack(side="left")

        minutes = ttk.Combobox(frame, values=[f"{i:02}" for i in range(60)], width=3, state="readonly")
        minutes.current(0)
        minutes.pack(side="left")

        seconds = ttk.Combobox(frame, values=[f"{i:02}" for i in range(60)], width=3, state="readonly")
        seconds.current(0)
        seconds.pack(side="left")

        # Bind to the ComboboxSelected event for each combobox
        hours.bind("<<ComboboxSelected>>", self.update_time_entry)
        minutes.bind("<<ComboboxSelected>>", self.update_time_entry)
        seconds.bind("<<ComboboxSelected>>", self.update_time_entry)

        return frame
    
    def update_time_entry(self, event):
        if self.selected_entry_index is not None:
            # Get the updated time values from the time pickers
            start_time = self.get_time_from_picker(self.start_time_entry)
            end_time = self.get_time_from_picker(self.end_time_entry)

            # Update the corresponding entry in the list
            self.entries[self.selected_entry_index][2] = start_time
            self.entries[self.selected_entry_index][3] = end_time

            # Update the listbox display (you might need to adjust the formatting)
            self.entries_listbox.delete(self.selected_entry_index)
            self.entries_listbox.insert(self.selected_entry_index,
                                        f"Project: {self.entries[self.selected_entry_index][0]}, "
                                        f"Date: {self.entries[self.selected_entry_index][1]}, "
                                        f"Start Time: {start_time}, "
                                        f"End Time: {end_time}, "
                                        f"Note: {self.entries[self.selected_entry_index][4]}")

    def get_time_from_picker(self, frame):
        hours, minutes, seconds = frame.winfo_children()
        return f"{hours.get()}:{minutes.get()}:{seconds.get()}"
    
    def update_total_time(self):
        self.total_time.clear()
        for entry in self.entries:
            start_time = datetime.strptime(f"{entry[1]} {entry[2]}", "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(f"{entry[1]} {entry[3]}", "%Y-%m-%d %H:%M:%S")
            self.total_time[entry[0]] += (end_time - start_time)
        self.display_total_time()

    def configure_grid(self):
        for i in range(21):
            self.root.rowconfigure(i, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

    def save_entry(self):
        project = self.project_entry.get().strip()
        date = self.date_entry.get().strip()
        start_time = self.get_time_from_picker(self.start_time_entry)
        end_time = self.get_time_from_picker(self.end_time_entry)
        note = self.note_entry.get("1.0", "end-1c")  # Get the text from the Text widget

        if not project or not date or not start_time or not end_time:
            messagebox.showerror("Input Error", "All fields are required.")
            return

        try:
            datetime.strptime(date, "%Y-%m-%d")
            start_time_obj = datetime.strptime(start_time, "%H:%M:%S")
            end_time_obj = datetime.strptime(end_time, "%H:%M:%S")
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date or time format. Use YYYY-MM-DD for date and HH:MM:SS for time.")
            return

        if end_time_obj <= start_time_obj:
            messagebox.showerror("Input Error", "End time must be after start time.")
            return

        new_entry = [project, date, start_time, end_time, note]

        if self.selected_entry_index is None:
            self.entries.append(new_entry)
        else:
            self.entries[self.selected_entry_index] = new_entry
            self.selected_entry_index = None

        self.write_entries()
        self.load_entries()
        self.update_total_time()
        self.clear_fields()

    def load_entries(self):
        self.entries_listbox.delete(0, tk.END)
        self.total_time.clear()
        self.update_project_filter()
        self.update_total_time()
        self.entries = []
        
        try:
            with open("time_entries.csv", "r") as file:
                reader = csv.reader(file)
                self.entries = list(reader)
        except FileNotFoundError:
            pass

        for entry in self.entries:
            self.entries_listbox.insert(tk.END, f"Project: {entry[0]}, Date: {entry[1]}, Start Time: {entry[2]}, End Time: {entry[3]}, Note: {entry[4]}")
            start_time = datetime.strptime(f"{entry[1]} {entry[2]}", "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(f"{entry[1]} {entry[3]}", "%Y-%m-%d %H:%M:%S")
            self.total_time[entry[0]] += (end_time - start_time)

        self.update_project_filter()
        self.display_total_time()

    def write_entries(self):
        with open("time_entries.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(self.entries)

    def clear_fields(self):
        self.project_entry.delete(0, tk.END)
        self.date_entry.set_date(datetime.now())
        self.start_time_entry.children['!combobox'].current(0)
        self.start_time_entry.children['!combobox2'].current(0)
        self.start_time_entry.children['!combobox3'].current(0)
        self.end_time_entry.children['!combobox'].current(0)
        self.end_time_entry.children['!combobox2'].current(0)
        self.end_time_entry.children['!combobox3'].current(0)
        self.note_entry.delete("1.0", tk.END)
        self.edit_button.config(state='disabled')
        self.delete_button.config(state='disabled')

    def on_select(self, event=None):  # Allow the method to be called without an event
        selection = self.entries_listbox.curselection()
        if selection:
            self.selected_entry_index = selection[0]
            entry = self.entries[self.selected_entry_index]

            # Update input fields only if they are empty or the date is different
            if not self.project_entry.get() or self.date_entry.get() != entry[1]:
                self.project_entry.delete(0, tk.END)
                self.project_entry.insert(0, entry[0])
                self.date_entry.set_date(entry[1])
                self.set_time_picker(self.start_time_entry, entry[2])
                self.set_time_picker(self.end_time_entry, entry[3])
                self.note_entry.delete("1.0", tk.END)
                self.note_entry.insert("1.0", entry[4])

            self.edit_button.config(state='normal')
            self.delete_button.config(state='normal')
        else:
            self.selected_entry_index = None
            self.clear_fields() 

    def set_time_picker(self, frame, time_str):
        hours, minutes, seconds = time_str.split(':')
        frame.children['!combobox'].set(hours)
        frame.children['!combobox2'].set(minutes)
        frame.children['!combobox3'].set(seconds)

    def edit_entry(self):
        self.save_entry()

    def delete_entry(self):
        if self.selected_entry_index is not None:
            del self.entries[self.selected_entry_index]
            self.write_entries()
            self.load_entries()
            self.update_total_time()
            self.clear_fields()

    def display_total_time(self):
        self.total_time_text.config(state='normal')
        self.total_time_text.delete(1.0, tk.END)
        for project, total_time in self.total_time.items():
            hours, remainder = divmod(total_time.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            self.total_time_text.insert(tk.END, f"Project: {project}, Total Time: {int(hours)}h {int(minutes)}m\n")
        self.total_time_text.config(state='disabled')

    def update_project_filter(self):
        projects = sorted(set(entry[0] for entry in self.entries))
        self.filter_combobox['values'] = ["All"] + projects
        self.filter_combobox.set("All")

    def filter_entries(self, event):
        filter_value = self.filter_combobox.get()
        self.entries_listbox.delete(0, tk.END)
        for entry in self.entries:
            if filter_value == "All" or entry[0] == filter_value:
                self.entries_listbox.insert(tk.END, f"Project: {entry[0]}, Date: {entry[1]}, Start Time: {entry[2]}, End Time: {entry[3]}")

    def filter_entries_by_date_range(self):
        start_date = self.start_date_filter_entry.get().strip()
        end_date = self.end_date_filter_entry.get().strip()

        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        if end_date_obj < start_date_obj:
            messagebox.showerror("Input Error", "End date must be after start date.")
            return

        self.entries_listbox.delete(0, tk.END)
        for entry in self.entries:
            entry_date = datetime.strptime(entry[1], "%Y-%m-%d")
            if start_date_obj <= entry_date <= end_date_obj:
                self.entries_listbox.insert(tk.END, f"Project: {entry[0]}, Date: {entry[1]}, Start Time: {entry[2]}, End Time: {entry[3]}, Note: {entry[4]}")

    def sort_entries(self, criterion):
        if criterion == "project":
            self.entries.sort(key=lambda x: x[0])
        elif criterion == "date":
            self.entries.sort(key=lambda x: x[1])
        elif criterion == "total_time":
            self.entries.sort(key=lambda x: self.total_time[x[0]], reverse=True)

        self.load_entries()

    def generate_report(self):
        """Generates a time report based on user input."""
        
        # Get the start and end dates and filter project from the GUI elements.
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()
        filter_project = self.filter_combobox.get()

        # Validate the date format.
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        # Validate that the end date is after the start date.
        if end_date_obj < start_date_obj:
            messagebox.showerror("Input Error", "End date must be after start date.")
            return

        # Filter the time entries based on the selected date range and project.
        filtered_entries = [entry for entry in self.entries if start_date <= entry[1] <= end_date and (filter_project == "All" or entry[0] == filter_project)]
        
        # Calculate the total time spent on each project.
        total_time = defaultdict(timedelta)
        for entry in filtered_entries:
            start_time = datetime.strptime(f"{entry[1]} {entry[2]}", "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(f"{entry[1]} {entry[3]}", "%Y-%m-%d %H:%M:%S")
            total_time[entry[0]] += (end_time - start_time)

        # Format the report text.
        report_text = ""
        for project, time in total_time.items():
            hours, remainder = divmod(time.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            report_text += f"Project: {project}, Total Time: {int(hours)}h {int(minutes)}m\n"
        
        # Display the report in a message box.
        messagebox.showinfo("Report", report_text)

    def export_to_pdf(self):
        # Generate the pie chart
        labels = list(self.total_time.keys())
        values = [total_time.total_seconds() / 3600 for total_time in self.total_time.values()]
        # Convert to hours
        
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(values, labels=labels, autopct='%1.1f%%')
        ax.axis('equal')  # Ensure the pie chart is circular
        ax.set_title('Time Spent on Projects')

        # Save the chart as a temporary PNG file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file_path = temp_file.name
            plt.savefig(temp_file_path, format='png')

        # Create the PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=12)
        
        # Add the chart image to the PDF
        pdf.image(temp_file_path, x=10, y=10, w=180)

        # Add the rest of the report content
        pdf.set_xy(10, 180)  # Set the cursor position below the chart
        pdf.cell(200, 10, txt="Project Time Entries", ln=True, align="C")

        pdf.cell(200, 10, txt="Entries:", ln=True, align="L")
        for entry in self.entries:
            pdf.cell(200, 10, txt=f"Project: {entry[0]}, Date: {entry[1]}, Start Time: {entry[2]}, End Time: {entry[3]}", ln=True)

        pdf.cell(200, 10, txt="Total Time Spent on Projects:", ln=True, align="L")
        for project, total_time in self.total_time.items():
            hours, remainder = divmod(total_time.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            pdf.cell(200, 10, txt=f"Project: {entry[0]}, Date: {entry[1]}, Start Time: {entry[2]}, End Time: {entry[3]}, Note: {entry[4]}", ln=True)

        # Remove the temporary file
        os.remove(temp_file_path)
        
        pdf.output("project_time_entries.pdf")
        messagebox.showinfo("Export Success", "Entries exported to project_time_entries.pdf successfully!")

    def toggle_timer(self):
        if self.is_timer_running:
            # Stop the timer
            self.stop_time = datetime.now()
            self.elapsed_time += self.stop_time - self.start_time
            self.set_time_picker(self.end_time_entry, self.stop_time.strftime("%H:%M:%S"))
            self.start_stop_button.config(text="Start", style="TButton")
            self.is_timer_running = False
            self.reminder_system.stop_reminder()
        else:
            # Start the timer
            self.start_time = datetime.now()
            self.set_time_picker(self.start_time_entry, self.start_time.strftime("%H:%M:%S"))
            self.start_stop_button.config(text="Stop", style="Danger.TButton")
            self.is_timer_running = True
            self.elapsed_time = timedelta()
            self.reminder_system.start_reminder()

    def set_reminder_interval(self):
        interval = simpledialog.askinteger("Set Reminder Interval", "Enter reminder interval in minutes:", 
                                       minvalue=1, maxvalue=120)
        if interval:
            self.reminder_system.reminder_interval = interval * 60
            messagebox.showinfo("Reminder Interval", f"Reminder interval set to {interval} minutes.")       

    def create_system_tray(self):
        """Creates the system tray icon and menu."""
        image = Image.new('RGB', (64, 64), color=(73, 109, 137))  # Create a blank image
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 64, 64), fill=(0, 0, 0))  # Draw a black rectangle
        draw.text((10, 10), "Timer", fill=(255, 255, 255))  # Add "Timer" text

        if not self.tray_icon_created:
        # Create the tray icon with menu options
            self.tray_icon = pystray.Icon("TimeEntryApp", image, "Time Entry App", menu=pystray.Menu(
            pystray.MenuItem("Show", self.show_app),
            pystray.MenuItem("Start Timer", self.start_timer),
            pystray.MenuItem("Stop Timer", self.stop_timer),
            pystray.MenuItem("Exit", self.exit_app)
        ))

        self.tray_icon.run_detached()
        self.tray_icon_created = True

    def show_app(self):
        self.root.deiconify()

    def exit_app(self):
        self.tray_icon.stop()
        self.root.quit()

    def start_timer(self):
        self.toggle_timer()

    def stop_timer(self):
        self.toggle_timer()

    def update_timer_in_tray(self):
        if self.is_timer_running:
            elapsed_time = datetime.now() - self.start_time + self.elapsed_time
            hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed_time_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
            self.start_stop_button.config(text=elapsed_time_str, style="Danger.TButton")
            self.tray_icon.title = f"Timer: {elapsed_time_str}"
        else:
            self.start_stop_button.config(text="Start", style="TButton")
            self.tray_icon.title = "Timer: Stopped"
        self.root.after(1000, self.update_timer_in_tray)


if __name__ == "__main__":
    root = tk.Tk()
    app = TimeEntryApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (root.withdraw(), app.create_system_tray()))
    root.mainloop()
