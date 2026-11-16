# HICAI ULTIMATE V13.0
# Single-file Kivy Student Management App
# Android / Pydroid 3 compatible; uses only Python standard library + Kivy.
# Keep this file in the SAME folder as your existing V9/V10 JSON data files.

import os, json, csv, zipfile, uuid
from datetime import datetime, date
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar

VERSION = "13.0"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FILES = {
    "subjects": "v9_subjects.json",
    "tasks": "v9_tasks.json",
    "attendance": "v9_attendance.json",
    "timetable": "v9_timetable.json",
    "sessions": "v9_sessions.json",
    "grades": "v10_grades.json",
}
COLORS = {
    "bg": "#0B1020", "surface": "#171F33", "surface2": "#202B45",
    "purple": "#7658F5", "blue": "#3189F5", "cyan": "#18BDE0",
    "green": "#16C995", "orange": "#F3A641", "red": "#ED6175",
    "white": "#F5F7FF", "muted": "#A4AEC5", "line": "#303B59"
}
Window.clearcolor = get_color_from_hex(COLORS["bg"])

def uid():
    return str(uuid.uuid4())

def valid_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except Exception:
        return False

class Database:
    def __init__(self):
        self.data = {}
        self.load()

    def path(self, key):
        return os.path.join(ROOT_DIR, FILES[key])

    def load(self):
        for key, filename in FILES.items():
            try:
                path = self.path(key)
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        value = json.load(f)
                    self.data[key] = value if isinstance(value, list) else []
                else:
                    self.data[key] = []
            except Exception as exc:
                print("Could not load", filename, exc)
                self.data[key] = []
        self.normalise()
        self.save_all()

    def normalise(self):
        for item in self.data["subjects"]:
            if isinstance(item, str):
                continue
            if isinstance(item, dict):
                item.setdefault("id", uid())
                item.setdefault("name", "Subject")
        for task in self.data["tasks"]:
            if isinstance(task, dict):
                task.setdefault("id", uid())
                task.setdefault("name", "Untitled task")
                task.setdefault("subject", "")
                task.setdefault("priority", "Medium")
                task.setdefault("due_date", "")
                task.setdefault("completed", bool(task.get("done", False)))
                task["done"] = task["completed"]
        for record in self.data["attendance"]:
            if isinstance(record, dict):
                record.setdefault("id", uid())
                record.setdefault("date", "")
                record.setdefault("status", "Present")
        for key in ("timetable", "grades", "sessions"):
            for item in self.data[key]:
                if isinstance(item, dict):
                    item.setdefault("id", uid())

    def save(self, key):
        path = self.path(key)
        temp = path + ".tmp"
        try:
            with open(temp, "w", encoding="utf-8") as f:
                json.dump(self.data[key], f, indent=2, ensure_ascii=False)
            os.replace(temp, path)
        except Exception as exc:
            print("Save error:", key, exc)
            try:
                if os.path.exists(temp):
                    os.remove(temp)
            except Exception:
                pass

    def save_all(self):
        for key in FILES:
            self.save(key)

class Panel(BoxLayout):
    def __init__(self, color=None, **kwargs):
        super().__init__(**kwargs)
        fill = get_color_from_hex(color or COLORS["surface"])
        with self.canvas.before:
            Color(*fill)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size,
                                         radius=[dp(15)])
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class HICAI(App):
    def build(self):
        self.title = "HICAI Ultimate V13.0"
        self.db = Database()
        self.page = "Dashboard"
        self.timer_left = 0
        self.timer_total = 0
        self.timer_event = None
        self.timer_running = False
        self.timer_label = None
        self.root_box = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        self.header = Panel(orientation="vertical", size_hint_y=None, height=dp(65),
                            padding=[dp(12), dp(5)], spacing=dp(1))
        self.header.add_widget(self.label("✦ HICAI ULTIMATE  V13.0", 19, "white", True))
        self.header.add_widget(self.label("STUDENT MANAGEMENT • STUDY • PRODUCTIVITY", 9, "cyan"))
        self.root_box.add_widget(self.header)
        self.page_title = self.label("Dashboard", 19, "white", True, height=dp(30))
        self.root_box.add_widget(self.page_title)
        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.content = GridLayout(cols=1, spacing=dp(9), padding=[dp(2), dp(5)],
                                  size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))
        self.scroll.add_widget(self.content)
        self.root_box.add_widget(self.scroll)
        self.nav = GridLayout(cols=5, spacing=dp(4), size_hint_y=None, height=dp(54))
        for title, target in [("Home","Dashboard"),("Study","Study"),
                              ("Progress","Progress"),("Tools","Tools"),("More","More")]:
            self.nav.add_widget(self.button(title, lambda p=target: self.show(p),
                                            "purple" if target == "Dashboard" else "blue", 48))
        self.root_box.add_widget(self.nav)
        self.show("Dashboard")
        Clock.schedule_once(self.check_due_tasks, 2)
        return self.root_box

    def color(self, name):
        return get_color_from_hex(COLORS.get(name, name))

    def label(self, text, size=13, color="white", bold=False, height=None,
              align="left"):
        # Do not pass height=None: Kivy expects a numeric height value.
        # Labels without a fixed height should keep their normal size hint.
        if height is None:
            w = Label(text=str(text), font_size=sp(size), color=self.color(color),
                      bold=bold, halign=align, valign="middle", size_hint_y=1)
        else:
            w = Label(text=str(text), font_size=sp(size), color=self.color(color),
                      bold=bold, halign=align, valign="middle",
                      size_hint_y=None, height=height)
        w.bind(size=lambda obj, val: setattr(obj, "text_size", val))
        return w

    def button(self, text, callback, color="blue", height=43):
        b = Button(text=text, font_size=sp(12), bold=True,
                   color=self.color("white"), background_normal="",
                   background_down="", background_color=self.color(color),
                   size_hint_y=None, height=dp(height))
        b.bind(on_release=lambda *_: callback())
        return b

    def section(self, text):
        self.content.add_widget(self.label(text.upper(), 12, "cyan", True, dp(28)))

    def info_card(self, title, value, hint, accent):
        p = Panel(orientation="vertical", padding=dp(10), spacing=dp(2),
                  size_hint_y=None, height=dp(100))
        p.add_widget(self.label(title.upper(), 10, "muted", True, dp(20)))
        p.add_widget(self.label(value, 24, accent, True, dp(34)))
        p.add_widget(self.label(hint, 9, "muted", False, dp(18)))
        return p

    def stat_grid(self, entries):
        grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for entry in entries:
            grid.add_widget(self.info_card(*entry))
        self.content.add_widget(grid)

    def card_text(self, title, detail="", color="white"):
        p = Panel(orientation="vertical", padding=dp(10), spacing=dp(3),
                  size_hint_y=None, height=dp(67))
        p.add_widget(self.label(title, 13, color, True, dp(22)))
        if detail:
            p.add_widget(self.label(detail, 10, "muted", False, dp(20)))
        self.content.add_widget(p)

    def show(self, page):
        self.page = page
        self.page_title.text = page
        self.content.clear_widgets()
        self.scroll.scroll_y = 1
        try:
            {"Dashboard": self.dashboard, "Study": self.study_page,
             "Progress": self.progress_page, "Tools": self.tools_page,
             "More": self.more_page}[page]()
        except Exception as exc:
            self.content.add_widget(self.label("Could not open this page:", 15, "red", True, dp(35)))
            self.content.add_widget(self.label(str(exc), 11, "white", False, dp(90)))
            print("Page error:", page, exc)

    def dashboard(self):
        tasks = [x for x in self.db.data["tasks"] if isinstance(x, dict)]
        done = sum(bool(x.get("completed", x.get("done", False))) for x in tasks)
        pending = len(tasks) - done
        att = [x for x in self.db.data["attendance"] if isinstance(x, dict)]
        present = sum(x.get("status") == "Present" for x in att)
        att_pct = f"{present / len(att) * 100:.0f}%" if att else "—"
        grade_values = []
        for g in self.db.data["grades"]:
            try:
                maximum, marks = float(g.get("maximum", 0)), float(g.get("marks", 0))
                if maximum > 0:
                    grade_values.append(marks / maximum * 100)
            except Exception:
                pass
        grade_avg = f"{sum(grade_values)/len(grade_values):.1f}%" if grade_values else "—"
        today = date.today().isoformat()
        due = sum(x.get("due_date") == today and not x.get("completed") for x in tasks)
        self.content.add_widget(self.label("Welcome back 👋", 20, "white", True, dp(35)))
        self.content.add_widget(self.label(datetime.now().strftime("%A, %d %B %Y"), 10, "muted", False, dp(22)))
        self.section("Academic overview")
        self.stat_grid([
            ("Subjects", str(len(self.db.data["subjects"])), "Registered subjects", "cyan"),
            ("Total tasks", str(len(tasks)), "All study tasks", "blue"),
            ("Completed", str(done), "Successfully finished", "green"),
            ("Pending", str(pending), "Tasks remaining", "orange"),
            ("Due today", str(due), "Tasks scheduled today", "red"),
            ("Attendance", att_pct, "Recorded attendance", "green"),
            ("Grade average", grade_avg, "Recorded marks", "purple"),
            ("Study sessions", str(len(self.db.data["sessions"])), "Focus sessions", "cyan"),
        ])
        self.section("Task progress")
        pct = done / len(tasks) * 100 if tasks else 0
        self.content.add_widget(self.label(f"{done} of {len(tasks)} tasks completed  •  {pct:.0f}%", 11, "muted", False, dp(22)))
        bar = ProgressBar(max=100, value=pct, size_hint_y=None, height=dp(13))
        self.content.add_widget(bar)
        self.section("Quick actions")
        for text, action in [("+ Add task", self.add_task),("+ Add subject", self.add_subject),
                             ("Mark attendance", self.add_attendance),("Open focus timer", lambda: self.show("Tools"))]:
            self.content.add_widget(self.button(text, action, "purple"))
        self.section("Upcoming tasks")
        upcoming = [x for x in tasks if not x.get("completed")]
        upcoming.sort(key=lambda x: x.get("due_date") or "9999-12-31")
        if not upcoming:
            self.content.add_widget(self.label("No pending tasks. Add your first task above.", 11, "muted", False, dp(38)))
        for t in upcoming[:5]:
            self.card_text(t.get("name","Task"), "Due: " + (t.get("due_date") or "Not set") + " • " + t.get("priority","Medium"))

    def study_page(self):
        self.section("Study management")
        self.content.add_widget(self.button("Subjects", lambda: self.list_subjects()))
        self.content.add_widget(self.button("Tasks", lambda: self.list_tasks()))
        self.content.add_widget(self.button("Weekly timetable", lambda: self.list_timetable()))
        self.content.add_widget(self.button("Focus timer", lambda: self.focus_page()))
        self.content.add_widget(self.button("+ Add subject", self.add_subject, "purple"))
        self.content.add_widget(self.button("+ Add task", self.add_task, "purple"))
        self.content.add_widget(self.button("+ Add timetable entry", self.add_timetable, "purple"))

    def progress_page(self):
        self.section("Academic progress")
        self.content.add_widget(self.button("Attendance records", self.list_attendance))
        self.content.add_widget(self.button("Grades and marks", self.list_grades))
        self.content.add_widget(self.button("Analytics", self.analytics))
        self.content.add_widget(self.button("+ Mark attendance", self.add_attendance, "purple"))
        self.content.add_widget(self.button("+ Add grade", self.add_grade, "purple"))

    def tools_page(self):
        self.section("Productivity tools")
        self.content.add_widget(self.button("Focus timer", self.focus_page, "purple"))
        self.content.add_widget(self.button("Search tasks", self.search_tasks))
        self.content.add_widget(self.button("Export CSV report", self.export_csv, "green"))
        self.content.add_widget(self.button("Create ZIP backup", self.backup, "blue"))

    def more_page(self):
        self.section("More options")
        self.content.add_widget(self.button("Reports / CSV export", self.export_csv))
        self.content.add_widget(self.button("Backup data", self.backup))
        self.content.add_widget(self.button("Restore backup", self.restore_popup, "orange"))
        self.content.add_widget(self.button("Refresh dashboard", lambda: self.show("Dashboard")))
        self.content.add_widget(self.label("HICAI Ultimate V13.0 • Your data stays in local JSON files.", 10, "muted", False, dp(45)))

    # ---------- Subjects ----------
    def list_subjects(self):
        self.content.clear_widgets()
        self.page_title.text = "Subjects"
        self.content.add_widget(self.button("+ Add subject", self.add_subject, "purple"))
        if not self.db.data["subjects"]:
            self.content.add_widget(self.label("No subjects yet.", 12, "muted", False, dp(40)))
        for subject in list(self.db.data["subjects"]):
            name = subject.get("name","Subject") if isinstance(subject,dict) else str(subject)
            row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
            row.add_widget(self.label(name, 13, "white", True))
            row.add_widget(self.button("Delete", lambda s=subject: self.delete_subject(s), "red", 40))
            self.content.add_widget(row)

    def add_subject(self):
        self.form("Add subject", [("Subject name","text","")], self.save_subject)

    def save_subject(self, v):
        name = v[0].strip()
        if not name: raise ValueError("Enter a subject name.")
        names = [x.get("name","") if isinstance(x,dict) else str(x) for x in self.db.data["subjects"]]
        if name.lower() in [x.lower() for x in names]: raise ValueError("Subject already exists.")
        self.db.data["subjects"].append({"id":uid(),"name":name})
        self.db.save("subjects")
        self.list_subjects()

    def delete_subject(self, subject):
        name = subject.get("name","") if isinstance(subject,dict) else str(subject)
        linked = any(isinstance(t,dict) and t.get("subject","") == name for t in self.db.data["tasks"])
        if linked:
            self.message("This subject is used by a task. Update or remove that task first.")
            return
        self.ask("Delete subject?", lambda: self._delete_subject(subject))

    def _delete_subject(self, subject):
        if subject in self.db.data["subjects"]:
            self.db.data["subjects"].remove(subject)
        self.db.save("subjects")
        self.list_subjects()

    # ---------- Tasks ----------
    def list_tasks(self):
        self.content.clear_widgets()
        self.page_title.text = "Tasks"
        self.content.add_widget(self.button("+ Add task", self.add_task, "purple"))
        tasks = [x for x in self.db.data["tasks"] if isinstance(x,dict)]
        if not tasks:
            self.content.add_widget(self.label("No tasks yet. Create your first task.", 12, "muted", False, dp(40)))
        for task in tasks:
            done = task.get("completed", task.get("done",False))
            p = Panel(orientation="vertical", padding=dp(9), spacing=dp(4),
                      size_hint_y=None, height=dp(126))
            p.add_widget(self.label(("✓ " if done else "○ ") + task.get("name","Task"), 13, "green" if done else "white", True, dp(23)))
            p.add_widget(self.label("Subject: " + (task.get("subject") or "General") + " • " + task.get("priority","Medium") + " • Due: " + (task.get("due_date") or "Not set"), 9, "muted", False, dp(20)))
            row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(4))
            row.add_widget(self.button("Undo" if done else "Done", lambda t=task:self.toggle_task(t), "green", 35))
            row.add_widget(self.button("Edit", lambda t=task:self.edit_task(t), "blue", 35))
            row.add_widget(self.button("Delete", lambda t=task:self.delete_task(t), "red", 35))
            p.add_widget(row)
            self.content.add_widget(p)

    def add_task(self):
        self.form("New task", [("Task title","text",""),("Subject","text",""),("Priority","choice",["Low","Medium","High"]),("Due date (YYYY-MM-DD, optional)","text","")], self.save_task)

    def save_task(self,v):
        name, subject, priority, due = v
        if not name.strip(): raise ValueError("Enter a task title.")
        if due.strip() and not valid_date(due.strip()): raise ValueError("Date must be YYYY-MM-DD.")
        self.db.data["tasks"].append({"id":uid(),"name":name.strip(),"subject":subject.strip(),
            "priority":priority,"due_date":due.strip(),"completed":False,"done":False})
        self.db.save("tasks")
        self.list_tasks()

    def edit_task(self, task):
        self.form("Edit task", [("Task title","text",task.get("name","")),
            ("Subject","text",task.get("subject","")),("Priority","choice",["Low","Medium","High"]),
            ("Due date (YYYY-MM-DD)","text",task.get("due_date",""))],
            lambda v:self.update_task(task,v), selected=task.get("priority","Medium"))

    def update_task(self,task,v):
        name,subject,priority,due=v
        if not name.strip(): raise ValueError("Task title cannot be empty.")
        if due.strip() and not valid_date(due.strip()): raise ValueError("Date must be YYYY-MM-DD.")
        task.update({"name":name.strip(),"subject":subject.strip(),"priority":priority,"due_date":due.strip()})
        self.db.save("tasks")
        self.list_tasks()

    def toggle_task(self,task):
        task["completed"] = not task.get("completed",task.get("done",False))
        task["done"] = task["completed"]
        self.db.save("tasks")
        self.list_tasks()

    def delete_task(self,task):
        self.ask("Permanently delete this task?",lambda:self._delete_task(task))

    def _delete_task(self,task):
        if task in self.db.data["tasks"]: self.db.data["tasks"].remove(task)
        self.db.save("tasks")
        self.list_tasks()

    # ---------- Attendance ----------
    def list_attendance(self):
        self.content.clear_widgets()
        self.page_title.text = "Attendance"
        records = [x for x in self.db.data["attendance"] if isinstance(x,dict)]
        present = sum(x.get("status")=="Present" for x in records)
        pct = present/len(records)*100 if records else None
        self.content.add_widget(self.info_card("Attendance", f"{pct:.1f}%" if pct is not None else "—",
                                               f"{present} present / {len(records)} records" if records else "No records yet","green"))
        self.content.add_widget(self.button("+ Mark attendance",self.add_attendance,"purple"))
        for r in reversed(records):
            row=BoxLayout(size_hint_y=None,height=dp(43),spacing=dp(4))
            row.add_widget(self.label(r.get("date","")+" • "+r.get("status",""),12))
            row.add_widget(self.button("Delete",lambda x=r:self.delete_record("attendance",x,self.list_attendance),"red",36))
            self.content.add_widget(row)

    def add_attendance(self):
        self.form("Mark attendance",[("Date YYYY-MM-DD","text",date.today().isoformat()),
            ("Status","choice",["Present","Absent","Leave"])],self.save_attendance)

    def save_attendance(self,v):
        day,status=v
        if not valid_date(day): raise ValueError("Enter a valid YYYY-MM-DD date.")
        self.db.data["attendance"].append({"id":uid(),"date":day,"status":status})
        self.db.save("attendance")
        self.list_attendance()

    # ---------- Timetable ----------
    def list_timetable(self):
        self.content.clear_widgets()
        self.page_title.text="Timetable"
        self.content.add_widget(self.button("+ Add timetable entry",self.add_timetable,"purple"))
        entries=[x for x in self.db.data["timetable"] if isinstance(x,dict)]
        order=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        entries.sort(key=lambda x:(order.index(x.get("day")) if x.get("day") in order else 7,x.get("time","")))
        if not entries: self.content.add_widget(self.label("No timetable entries yet.",12,"muted",False,dp(40)))
        for e in entries:
            row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(4))
            row.add_widget(self.label(e.get("day","")+" • "+e.get("time","")+" • "+e.get("subject",""),11))
            row.add_widget(self.button("Delete",lambda x=e:self.delete_record("timetable",x,self.list_timetable),"red",36))
            self.content.add_widget(row)

    def add_timetable(self):
        self.form("Timetable entry",[("Day","choice",["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]),
            ("Time","text","09:00 AM"),("Subject / activity","text","")],self.save_timetable)

    def save_timetable(self,v):
        day,time,subject=v
        if not subject.strip(): raise ValueError("Enter a subject or activity.")
        self.db.data["timetable"].append({"id":uid(),"day":day,"time":time.strip(),"subject":subject.strip()})
        self.db.save("timetable")
        self.list_timetable()

    # ---------- Grades ----------
    def list_grades(self):
        self.content.clear_widgets()
        self.page_title.text="Grades"
        self.content.add_widget(self.button("+ Add grade",self.add_grade,"purple"))
        grades=[x for x in self.db.data["grades"] if isinstance(x,dict)]
        vals=[]
        for g in grades:
            try:
                m=float(g.get("marks",0)); mx=float(g.get("maximum",0))
                if mx>0: vals.append(m/mx*100)
            except Exception: pass
        avg=sum(vals)/len(vals) if vals else None
        self.content.add_widget(self.info_card("Grade average",f"{avg:.1f}%" if avg is not None else "—","Across recorded assessments","purple"))
        for g in grades:
            row=BoxLayout(size_hint_y=None,height=dp(45),spacing=dp(4))
            row.add_widget(self.label(f'{g.get("subject","")} • {g.get("marks","")} / {g.get("maximum","")}',11))
            row.add_widget(self.button("Delete",lambda x=g:self.delete_record("grades",x,self.list_grades),"red",36))
            self.content.add_widget(row)

    def add_grade(self):
        self.form("Add grade",[("Subject / test","text",""),("Marks obtained","text",""),("Maximum marks","text","100")],self.save_grade)

    def save_grade(self,v):
        subject,marks,maximum=v
        if not subject.strip(): raise ValueError("Enter subject or test name.")
        try:
            marks=float(marks); maximum=float(maximum)
            if maximum<=0 or marks<0 or marks>maximum: raise ValueError()
        except Exception: raise ValueError("Marks must be valid and cannot exceed maximum.")
        self.db.data["grades"].append({"id":uid(),"subject":subject.strip(),"marks":marks,"maximum":maximum,"date":date.today().isoformat()})
        self.db.save("grades")
        self.list_grades()

    def delete_record(self,key,item,refresh):
        self.ask("Delete this record?",lambda:self._delete_record(key,item,refresh))

    def _delete_record(self,key,item,refresh):
        if item in self.db.data[key]: self.db.data[key].remove(item)
        self.db.save(key)
        refresh()

    # ---------- Analytics ----------
    def analytics(self):
        self.content.clear_widgets()
        self.page_title.text="Analytics"
        tasks=[x for x in self.db.data["tasks"] if isinstance(x,dict)]
        done=sum(bool(x.get("completed",x.get("done",False))) for x in tasks)
        pct=done/len(tasks)*100 if tasks else 0
        mins=0
        for s in self.db.data["sessions"]:
            try: mins+=int(s.get("minutes",0))
            except Exception: pass
        self.content.add_widget(self.info_card("Task completion",f"{pct:.1f}%",f"{done} completed of {len(tasks)}","green"))
        self.content.add_widget(self.info_card("Study time",f"{mins//60}h {mins%60}m","Recorded focus time","cyan"))
        records=self.db.data["attendance"]
        present=sum(isinstance(x,dict) and x.get("status")=="Present" for x in records)
        self.content.add_widget(self.info_card("Attendance",f"{present/len(records)*100:.1f}%" if records else "—","Based on saved records","purple"))
        self.content.add_widget(self.button("Back to Progress",lambda:self.show("Progress")))

    # ---------- Focus timer ----------
    def focus_page(self):
        self.content.clear_widgets()
        self.page_title.text="Focus Timer"
        self.content.add_widget(self.label("FOCUS • ONE TASK AT A TIME",11,"cyan",True,dp(28)))
        self.timer_label=self.label(self.timer_text(),42,"green",True,dp(90), "center")
        self.content.add_widget(self.timer_label)
        self.duration=Spinner(text="25 minutes",values=["15 minutes","25 minutes","30 minutes","45 minutes","60 minutes"],
            size_hint_y=None,height=dp(44),background_normal="",background_color=self.color("surface2"),color=self.color("white"))
        self.content.add_widget(self.duration)
        self.content.add_widget(self.button("Start / Resume",self.start_timer,"green"))
        self.content.add_widget(self.button("Pause",self.pause_timer,"orange"))
        self.content.add_widget(self.button("Reset",self.reset_timer,"red"))
        self.content.add_widget(self.label(f"Saved focus sessions: {len(self.db.data['sessions'])}",11,"muted",False,dp(35)))

    def timer_text(self):
        return f"{self.timer_left//60:02d}:{self.timer_left%60:02d}"

    def start_timer(self):
        if self.timer_running: return
        if self.timer_left<=0:
            try: minutes=int(self.duration.text.split()[0])
            except Exception: minutes=25
            self.timer_total=minutes*60
            self.timer_left=self.timer_total
        self.timer_running=True
        self.timer_event=Clock.schedule_interval(self.tick,1)
        self.update_timer()

    def tick(self,dt):
        if not self.timer_running: return False
        self.timer_left=max(0,self.timer_left-1)
        self.update_timer()
        if self.timer_left==0:
            self.pause_timer()
            minutes=max(1,self.timer_total//60)
            self.db.data["sessions"].append({"id":uid(),"date":date.today().isoformat(),"minutes":minutes,
                                             "completed_at":datetime.now().isoformat()})
            self.db.save("sessions")
            self.message(f"Focus session complete. {minutes} minutes saved.")
            self.focus_page()
            return False
        return True

    def update_timer(self):
        if self.timer_label: self.timer_label.text=self.timer_text()

    def pause_timer(self):
        self.timer_running=False
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event=None
        self.update_timer()

    def reset_timer(self):
        self.pause_timer()
        self.timer_left=0
        self.timer_total=0
        self.update_timer()

    # ---------- Search ----------
    def search_tasks(self):
        self.content.clear_widgets()
        self.page_title.text="Search tasks"
        field=TextInput(hint_text="Type a task title...",multiline=False,size_hint_y=None,height=dp(45),
                        background_normal="",background_color=self.color("surface2"),foreground_color=self.color("white"))
        self.content.add_widget(field)
        results=GridLayout(cols=1,spacing=dp(5),size_hint_y=None)
        results.bind(minimum_height=results.setter("height"))
        self.content.add_widget(results)
        def run_search():
            results.clear_widgets()
            q=field.text.strip().lower()
            matches=[t for t in self.db.data["tasks"] if isinstance(t,dict) and q and q in t.get("name","").lower()]
            if not matches: results.add_widget(self.label("No matching tasks.",11,"muted",False,dp(35)))
            for t in matches: results.add_widget(self.label(t.get("name","")+" • "+(t.get("due_date") or "No due date"),11,"white",False,dp(35)))
        self.content.add_widget(self.button("Search",run_search,"purple"))
        field.bind(on_text_validate=lambda *_:run_search())

    # ---------- CSV and ZIP ----------
    def export_csv(self):
        path=os.path.join(ROOT_DIR,"HICAI_Tasks_Report.csv")
        try:
            with open(path,"w",newline="",encoding="utf-8") as f:
                w=csv.writer(f)
                w.writerow(["Task","Subject","Priority","Due date","Completed"])
                for t in self.db.data["tasks"]:
                    if isinstance(t,dict):
                        w.writerow([t.get("name",""),t.get("subject",""),t.get("priority",""),t.get("due_date",""),t.get("completed",False)])
            self.message("CSV report saved in the app folder:\nHICAI_Tasks_Report.csv")
        except Exception as exc: self.message("CSV export failed: "+str(exc))

    def backup(self):
        self.db.save_all()
        path=os.path.join(ROOT_DIR,"HICAI_Backup_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".zip")
        try:
            with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as z:
                for filename in FILES.values():
                    full=os.path.join(ROOT_DIR,filename)
                    if os.path.exists(full): z.write(full,filename)
            self.message("Backup created:\n"+os.path.basename(path))
        except Exception as exc: self.message("Backup failed: "+str(exc))

    def restore_popup(self):
        box=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(8))
        field=TextInput(hint_text="Full path to backup ZIP",multiline=False,size_hint_y=None,height=dp(45))
        box.add_widget(self.label("Enter the full path of a HICAI ZIP backup.",10,"muted",False,dp(30)))
        box.add_widget(field)
        pop=Popup(title="Restore backup",content=box,size_hint=(.92,.4))
        box.add_widget(self.button("Restore",lambda:self.restore_zip(field.text,pop),"green"))
        box.add_widget(self.button("Cancel",pop.dismiss,"red"))
        pop.open()

    def restore_zip(self,path,popup):
        path=path.strip()
        if not os.path.isfile(path): self.message("Backup ZIP not found."); return
        try:
            replacement={}
            with zipfile.ZipFile(path,"r") as z:
                names=z.namelist()
                for key,filename in FILES.items():
                    if filename in names:
                        value=json.loads(z.read(filename).decode("utf-8"))
                        if not isinstance(value,list): raise ValueError("Invalid file: "+filename)
                        replacement[key]=value
            if not replacement: raise ValueError("No HICAI data files found.")
            # Validate all archive entries before changing current data.
            old={k:self.db.data[k] for k in replacement}
            try:
                self.db.data.update(replacement)
                self.db.normalise()
                self.db.save_all()
            except Exception:
                self.db.data.update(old)
                raise
            popup.dismiss()
            self.show("Dashboard")
            self.message("Backup restored.")
        except Exception as exc: self.message("Restore failed: "+str(exc))

    # ---------- Forms / dialogs ----------
    def form(self,title,fields,callback,selected=None):
        box=BoxLayout(orientation="vertical",padding=dp(11),spacing=dp(5))
        widgets=[]
        for i,(caption,kind,default) in enumerate(fields):
            box.add_widget(self.label(caption,10,"muted",False,dp(19)))
            if kind=="choice":
                value=selected if i==2 and selected in default else default[0]
                w=Spinner(text=value,values=default,size_hint_y=None,height=dp(41),
                          background_normal="",background_color=self.color("surface2"),color=self.color("white"))
            else:
                w=TextInput(text=str(default),hint_text=caption,multiline=False,size_hint_y=None,height=dp(41),
                            background_normal="",background_color=self.color("surface2"),
                            foreground_color=self.color("white"),cursor_color=self.color("cyan"))
            widgets.append(w)
            box.add_widget(w)
        pop=Popup(title=title,content=box,size_hint=(.93,.82))
        def submit():
            try:
                callback([w.text for w in widgets])
                pop.dismiss()
            except Exception as exc:
                self.message(str(exc))
        box.add_widget(self.button("SAVE",submit,"green"))
        box.add_widget(self.button("CANCEL",pop.dismiss,"red"))
        pop.open()

    def ask(self,text,callback):
        box=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(8))
        box.add_widget(self.label(text,12,"white",False,dp(55)))
        pop=Popup(title="Please confirm",content=box,size_hint=(.86,.35))
        box.add_widget(self.button("Confirm",lambda:(callback(),pop.dismiss()),"red"))
        box.add_widget(self.button("Cancel",pop.dismiss,"blue"))
        pop.open()

    def message(self,text):
        box=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(8))
        box.add_widget(self.label(text,12,"white",False,dp(65)))
        pop=Popup(title="HICAI",content=box,size_hint=(.88,.38))
        box.add_widget(self.button("OK",pop.dismiss,"blue"))
        pop.open()

    def check_due_tasks(self,dt):
        today=date.today().isoformat()
        due=[t for t in self.db.data["tasks"] if isinstance(t,dict) and t.get("due_date")==today and not t.get("completed")]
        if due: self.message(f"You have {len(due)} unfinished task(s) due today.")

    def on_pause(self):
        self.pause_timer()
        self.db.save_all()
        return True

    def on_stop(self):
        self.pause_timer()
        self.db.save_all()

if __name__ == "__main__":
    HICAI().run()
