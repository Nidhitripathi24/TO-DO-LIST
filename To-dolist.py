import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import sqlite3
from datetime import datetime, timedelta
import threading
import time

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            deadline DATE NOT NULL,
            priority TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0,
            category TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Add a new task
def add_task():
    task = task_entry.get()
    deadline = deadline_entry.get()
    priority = priority_var.get()
    category = category_var.get()

    if task and deadline and priority:
        try:
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
            conn = sqlite3.connect('tasks.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO tasks (task, deadline, priority, category) VALUES (?, ?, ?, ?)', 
                         (task, deadline, priority, category))
            conn.commit()
            conn.close()
            refresh_tasks()
            task_entry.delete(0, tk.END)
            show_notification("Task Added", f"Task '{task}' has been added.")
        except ValueError:
            messagebox.showerror("Invalid date", "Please enter the date in YYYY-MM-DD format.")
    else:
        messagebox.showwarning("Incomplete data", "Please fill in all fields.")

# Edit an existing task
def edit_task():
    selected_task = task_listbox.curselection()
    if not selected_task:
        messagebox.showwarning("No selection", "Please select a task to edit.")
        return
    task_id = task_listbox.get(selected_task[0]).split(" | ")[0]

    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, task, deadline, priority, completed, category FROM tasks WHERE id = ?', (task_id,))
    current_task = cursor.fetchone()
    conn.close()
    
    if not current_task:
        return

    edit_window = tk.Toplevel(root)
    edit_window.title("Edit Task")
    edit_window.geometry("400x300")
    
    ttk.Label(edit_window, text="Task:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=10)
    task_var = tk.StringVar(value=current_task[1])
    ttk.Entry(edit_window, textvariable=task_var, width=30).grid(row=0, column=1, pady=5, padx=10)

    ttk.Label(edit_window, text="Deadline (YYYY-MM-DD):").grid(row=1, column=0, sticky=tk.W, pady=5, padx=10)
    deadline_var = tk.StringVar(value=current_task[2])
    ttk.Entry(edit_window, textvariable=deadline_var, width=30).grid(row=1, column=1, pady=5, padx=10)

    ttk.Label(edit_window, text="Priority:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=10)
    edit_priority_var = tk.StringVar(value=current_task[3])
    ttk.Combobox(edit_window, textvariable=edit_priority_var, values=["High", "Medium", "Low"], 
                state="readonly", width=28).grid(row=2, column=1, pady=5, padx=10)

    ttk.Label(edit_window, text="Category:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=10)
    edit_category_var = tk.StringVar(value=current_task[5])
    ttk.Combobox(edit_window, textvariable=edit_category_var, values=["Work", "Personal", "Health", "Education", "Errands"], 
                width=28).grid(row=3, column=1, pady=5, padx=10)

    completed_var = tk.BooleanVar(value=bool(current_task[4]))
    ttk.Checkbutton(edit_window, text="Completed", variable=completed_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=10, padx=10)

    def save_changes():
        new_task = task_var.get()
        new_deadline = deadline_var.get()
        new_priority = edit_priority_var.get()
        new_category = edit_category_var.get()
        new_completed = completed_var.get()

        if new_task and new_deadline and new_priority:
            try:
                datetime.strptime(new_deadline, '%Y-%m-%d')
                conn = sqlite3.connect('tasks.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tasks
                    SET task = ?, deadline = ?, priority = ?, completed = ?, category = ?
                    WHERE id = ?
                ''', (new_task, new_deadline, new_priority, new_completed, new_category, task_id))
                conn.commit()
                conn.close()
                refresh_tasks()
                edit_window.destroy()
                show_notification("Task Updated", f"Task '{new_task}' has been updated.")
            except ValueError:
                messagebox.showerror("Invalid date", "Please enter the date in YYYY-MM-DD format.")
        else:
            messagebox.showwarning("Incomplete data", "Please fill in all fields.")

    ttk.Button(edit_window, text="Save Changes", command=save_changes).grid(row=5, column=0, pady=15, padx=10)
    ttk.Button(edit_window, text="Cancel", command=edit_window.destroy).grid(row=5, column=1, pady=15, padx=10)

# Delete a task
def delete_task():
    selected_task = task_listbox.curselection()
    if not selected_task:
        messagebox.showwarning("No selection", "Please select a task to delete.")
        return
    
    task_id = task_listbox.get(selected_task[0]).split(" | ")[0]
    
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT task FROM tasks WHERE id = ?', (task_id,))
    task_name = cursor.fetchone()[0]
    
    confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete task '{task_name}'?")
    if confirm:
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()
        refresh_tasks()
        show_notification("Task Deleted", f"Task '{task_name}' has been deleted.")
    else:
        conn.close()

# Mark a task as complete
def complete_task():
    selected_task = task_listbox.curselection()
    if selected_task:
        task_id = task_listbox.get(selected_task[0]).split(" | ")[0]
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT task, completed FROM tasks WHERE id = ?', (task_id,))
        task_info = cursor.fetchone()
        
        if task_info[1] == 0:  # If not completed
            cursor.execute('UPDATE tasks SET completed = 1 WHERE id = ?', (task_id,))
            status_msg = "completed"
        else:
            cursor.execute('UPDATE tasks SET completed = 0 WHERE id = ?', (task_id,))
            status_msg = "pending"
            
        conn.commit()
        conn.close()
        refresh_tasks()
        show_notification("Status Changed", f"Task '{task_info[0]}' marked as {status_msg}.")
    else:
        messagebox.showwarning("No selection", "Please select a task to complete.")

# Refresh the task list
def refresh_tasks():
    task_listbox.delete(0, tk.END)
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    # Get filter settings
    show_completed = show_completed_var.get()
    priority_filter = priority_filter_var.get()
    sort_by = sort_by_var.get()
    
    # Build the query
    query = 'SELECT id, task, deadline, priority, completed, category FROM tasks WHERE 1=1'
    params = []
    
    if not show_completed:
        query += " AND completed = 0"
    
    if priority_filter != "All":
        query += " AND priority = ?"
        params.append(priority_filter)
    
    # Add sorting
    if sort_by == "Deadline":
        query += " ORDER BY deadline ASC"
    elif sort_by == "Priority":
        query += " ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 END"
    elif sort_by == "Category":
        query += " ORDER BY category ASC"
    
    cursor.execute(query, params)
    tasks = cursor.fetchall()
    conn.close()
    
    # Update stats
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task[4])
    pending_tasks = total_tasks - completed_tasks
    
    stats_label.config(text=f"Tasks: {pending_tasks} Pending | {completed_tasks} Completed")
    
    # Priority colors
    priority_colors = {
        "High": "#ff4d4d",
        "Medium": "#ffa64d",
        "Low": "#66cc66"
    }
    
    for task in tasks:
        task_id, task_text, deadline, priority, completed, category = task
        days_left = (datetime.strptime(deadline, '%Y-%m-%d') - datetime.now()).days
        
        status = "✓" if completed else "⌛"
        priority_indicator = f"[{priority}]"
        
        deadline_text = f"{deadline} ({days_left} days left)" if days_left >= 0 else f"{deadline} (OVERDUE)"
        
        task_display = f"{task_id} | {status} {priority_indicator} {task_text} | {deadline_text} | #{category}"
        
        task_listbox.insert(tk.END, task_display)
        
        # Format based on status and priority
        if completed:
            task_listbox.itemconfig(tk.END, {'bg': '#e6ffe6', 'fg': '#888888'})
        else:
            task_listbox.itemconfig(tk.END, {'fg': priority_colors.get(priority, 'black')})
            if days_left < 0:
                task_listbox.itemconfig(tk.END, {'bg': '#ffebeb'})

# Show notification
def show_notification(title, message):
    notification = tk.Toplevel(root)
    notification.title("")
    notification.geometry("300x80+{}+{}".format(
        root.winfo_rootx() + root.winfo_width() - 320,
        root.winfo_rooty() + 20
    ))
    notification.overrideredirect(True)
    
    tk.Label(notification, text=title, font=("Helvetica", 12, "bold")).pack(pady=(10, 0))
    tk.Label(notification, text=message).pack(pady=5)
    
    notification.after(3000, notification.destroy)

# Search tasks
def search_tasks():
    search_term = search_entry.get().lower()
    if not search_term:
        refresh_tasks()
        return
    
    task_listbox.delete(0, tk.END)
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, task, deadline, priority, completed, category FROM tasks
        WHERE lower(task) LIKE ? OR lower(category) LIKE ?
    ''', (f'%{search_term}%', f'%{search_term}%'))
    
    tasks = cursor.fetchall()
    conn.close()
    
    for task in tasks:
        task_id, task_text, deadline, priority, completed, category = task
        days_left = (datetime.strptime(deadline, '%Y-%m-%d') - datetime.now()).days
        
        status = "✓" if completed else "⌛"
        priority_indicator = f"[{priority}]"
        deadline_text = f"{deadline} ({days_left} days left)" if days_left >= 0 else f"{deadline} (OVERDUE)"
        
        task_display = f"{task_id} | {status} {priority_indicator} {task_text} | {deadline_text} | #{category}"
        task_listbox.insert(tk.END, task_display)
        
        if completed:
            task_listbox.itemconfig(tk.END, {'bg': '#e6ffe6', 'fg': '#888888'})
        elif days_left < 0:
            task_listbox.itemconfig(tk.END, {'bg': '#ffebeb'})

# Context menu for task options
def show_context_menu(event):
    try:
        task_index = task_listbox.nearest(event.y)
        task_listbox.selection_clear(0, tk.END)
        task_listbox.selection_set(task_index)
        task_listbox.activate(task_index)

        selected_task = task_listbox.get(task_index).split(" | ")[0]
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('SELECT completed FROM tasks WHERE id = ?', (selected_task,))
        is_completed = cursor.fetchone()[0]
        conn.close()

        context_menu = tk.Menu(root, tearoff=0)
        context_menu.add_command(label="Edit Task", command=edit_task)
        
        if is_completed:
            context_menu.add_command(label="Mark as Pending", command=complete_task)
        else:
            context_menu.add_command(label="Mark as Completed", command=complete_task)
        
        context_menu.add_separator()
        context_menu.add_command(label="Delete Task", command=delete_task)
        
        context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        context_menu.grab_release()

# Check for upcoming deadlines
def check_deadlines():
    while True:
        current_time = datetime.now()
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, task, deadline FROM tasks WHERE completed = 0')
        tasks = cursor.fetchall()
        conn.close()

        for task in tasks:
            task_id, task_name, deadline = task
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
            days_left = (deadline_date - current_time).days
            
            # Notify for tasks due within 24 hours
            if days_left == 0 and current_time.hour == 9:  # Only notify once a day at 9 AM
                notification_title = "Tasks Due Today"
                notification_text = f"Task '{task_name}' is due today!"
                # Add to notification queue
                notification_queue.append((notification_title, notification_text))
        
        time.sleep(3600)  # Check every hour

# Process notification queue
def process_notifications():
    if notification_queue:
        title, message = notification_queue.pop(0)
        show_notification(title, message)
    
    root.after(5000, process_notifications)

# Initialize the main window
root = tk.Tk()
root.title("Simple Task Manager")
root.geometry("900x600")

# Create a notification queue
notification_queue = []

# Main container with two frames
main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True)

# Header frame
header_frame = ttk.Frame(main_frame)
header_frame.pack(fill=tk.X, pady=(0, 10))

# App title
ttk.Label(header_frame, text="Task Manager", font=("Helvetica", 16, "bold")).pack(side=tk.LEFT)

# Stats label
stats_label = ttk.Label(header_frame, text="Loading stats...")
stats_label.pack(side=tk.RIGHT)

# Search frame
search_frame = ttk.Frame(main_frame)
search_frame.pack(fill=tk.X, pady=5)

search_entry = ttk.Entry(search_frame, width=30)
search_entry.pack(side=tk.LEFT, padx=5)
search_entry.bind("<Return>", lambda event: search_tasks())

ttk.Button(search_frame, text="Search", command=search_tasks).pack(side=tk.LEFT, padx=5)
ttk.Button(search_frame, text="Clear", 
           command=lambda: [search_entry.delete(0, tk.END), refresh_tasks()]).pack(side=tk.LEFT)

# Filter frame
filter_frame = ttk.Frame(main_frame)
filter_frame.pack(fill=tk.X, pady=5)

# Show completed filter
show_completed_var = tk.BooleanVar(value=True)
ttk.Checkbutton(filter_frame, text="Show Completed", 
                variable=show_completed_var, command=refresh_tasks).pack(side=tk.LEFT, padx=5)

# Priority filter
ttk.Label(filter_frame, text="Priority:").pack(side=tk.LEFT, padx=(20, 5))
priority_filter_var = tk.StringVar(value="All")
ttk.OptionMenu(filter_frame, priority_filter_var, "All", "All", "High", "Medium", "Low", 
               command=lambda _: refresh_tasks()).pack(side=tk.LEFT)

# Sort filter
ttk.Label(filter_frame, text="Sort by:").pack(side=tk.LEFT, padx=(20, 5))
sort_by_var = tk.StringVar(value="Deadline")
ttk.OptionMenu(filter_frame, sort_by_var, "Deadline", "Deadline", "Priority", "Category", 
               command=lambda _: refresh_tasks()).pack(side=tk.LEFT)

# Content area - split into left panel for task list and right panel for entry
content_frame = ttk.Frame(main_frame)
content_frame.pack(fill=tk.BOTH, expand=True, pady=10)

# Task list panel
list_frame = ttk.Frame(content_frame, relief=tk.GROOVE, borderwidth=1)
list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

ttk.Label(list_frame, text="Tasks", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, padx=10, pady=5)

task_listbox = tk.Listbox(list_frame, height=20, font=("Helvetica", 10), 
                         selectbackground="#4CAF50", selectforeground="white")
task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
task_listbox.bind("<Button-3>", show_context_menu)  # Right-click for context menu
task_listbox.bind("<Double-Button-1>", lambda event: edit_task())  # Double-click to edit

scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=task_listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=5)
task_listbox.config(yscrollcommand=scrollbar.set)

# Task entry panel
entry_frame = ttk.Frame(content_frame, relief=tk.GROOVE, borderwidth=1)
entry_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

ttk.Label(entry_frame, text="Add New Task", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, padx=15, pady=5)

form_frame = ttk.Frame(entry_frame)
form_frame.pack(fill=tk.X, padx=15, pady=5)

ttk.Label(form_frame, text="Task:").grid(row=0, column=0, sticky=tk.W, pady=5)
task_entry = ttk.Entry(form_frame, width=40)
task_entry.grid(row=0, column=1, sticky=tk.W, pady=5)

ttk.Label(form_frame, text="Deadline:").grid(row=1, column=0, sticky=tk.W, pady=5)
deadline_entry = ttk.Entry(form_frame, width=40)
deadline_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
# Set default date to tomorrow
tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
deadline_entry.insert(0, tomorrow)

ttk.Label(form_frame, text="Priority:").grid(row=2, column=0, sticky=tk.W, pady=5)
priority_var = tk.StringVar(value="Medium")
ttk.OptionMenu(form_frame, priority_var, "Medium", "High", "Medium", "Low").grid(row=2, column=1, sticky=tk.W, pady=5)

ttk.Label(form_frame, text="Category:").grid(row=3, column=0, sticky=tk.W, pady=5)
category_var = tk.StringVar(value="Work")
ttk.OptionMenu(form_frame, category_var, "Work", "Work", "Personal", "Health", "Education", "Errands").grid(row=3, column=1, sticky=tk.W, pady=5)

# Buttons
buttons_frame = ttk.Frame(entry_frame)
buttons_frame.pack(fill=tk.X, padx=15, pady=15)

ttk.Button(buttons_frame, text="Add Task", command=add_task).pack(side=tk.LEFT, padx=5)
ttk.Button(buttons_frame, text="Complete Task", command=complete_task).pack(side=tk.LEFT, padx=5)
ttk.Button(buttons_frame, text="Delete Task", command=delete_task).pack(side=tk.RIGHT, padx=5)

# Initialize the database and refresh the task list
init_db()


# Start the deadline checker in a separate thread
deadline_thread = threading.Thread(target=check_deadlines, daemon=True)
deadline_thread.start()

# Start processing notifications
process_notifications()


refresh_tasks()
# Run the application
root.mainloop()