import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from connectdb import engine, get_session
from sqlalchemy import text

# ── Data Layer (unchanged) ────────────────────────────────────────────────────

class DatabaseConnection:
    def __init__(self):
        self.engine = engine
        self.connection = engine

    def connect(self):
        try:
            with self.engine.connect() as conn:
                print("Connection successful!")
        except Exception as ex:
            print(f"Error: {ex}")

    def close(self):
        pass

class DataQuery:
    def __init__(self, db_connection):
        self.engine = db_connection.engine

    def fetch_all(self, table_name):
        try:
            session = get_session()
            result = session.execute(text(f"SELECT * FROM {table_name}"))
            data = result.fetchall()
            session.close()
            return data
        except Exception as e:
            print(f"Error fetching {table_name}: {e}")
            return []

    def insert_identifier(self, identifier_name, description, identifier_type):
        try:
            session = get_session()
            desc_esc = description.replace("'", "''") if description else ""
            session.execute(text(
                f"INSERT INTO Identifiers (identifier_name, description, identifier_type) "
                f"VALUES ('{identifier_name}', '{desc_esc}', '{identifier_type}')"
            ))
            session.commit()
            session.close()
        except Exception as e:
            print(f"Error inserting identifier: {e}")

    def delete_dependencies(self, table_name, identifier_column, identifier_value):
        try:
            session = get_session()
            if table_name == "Identifiers":
                session.execute(text(f"DELETE FROM Ownership WHERE identifier_name = '{identifier_value}'"))
                session.execute(text(f"DELETE FROM Relationships WHERE from_identifier_name = '{identifier_value}' OR to_identifier_name = '{identifier_value}'"))
                session.execute(text(f"DELETE FROM IdentifierCharacteristics WHERE identifier_name = '{identifier_value}'"))
            if table_name == "Countries":
                session.execute(text(f"DELETE FROM ConsumerUnits WHERE country_name = '{identifier_value}'"))
            session.commit()
            session.close()
        except Exception as e:
            print(f"Error deleting dependencies: {e}")

    def delete_entry(self, table_name, identifier_column, identifier_value):
        self.delete_dependencies(table_name, identifier_column, identifier_value)
        try:
            session = get_session()
            session.execute(text(f"DELETE FROM {table_name} WHERE {identifier_column} = '{identifier_value}'"))
            session.commit()
            session.close()
        except Exception as e:
            print(f"Error deleting entry: {e}")

# ── Palette ───────────────────────────────────────────────────────────────────

BG          = '#0d0e12'
SIDEBAR     = '#111318'
SURFACE     = '#15171f'
CARD        = '#1c1f2a'
BORDER      = '#22262f'
BORDER_LT   = '#2e3340'

ACCENT      = '#4d9ff8'
ACCENT_DK   = '#2563d4'
ACCENT_GLOW = '#1a3a6e'

TEXT        = '#edf1fa'
TEXT_MED    = '#8c96ae'
TEXT_MUTED  = '#4e5670'

SUCCESS     = '#2dd4a0'
SUCCESS_DK  = '#1aab7e'
DANGER      = '#f47171'
DANGER_DK   = '#c94545'

TREE_A      = '#0d0e12'
TREE_B      = '#111318'
TREE_SEL    = '#13234a'
HEAD_BG     = '#0a0b0f'

# ── Fonts ─────────────────────────────────────────────────────────────────────

SB   = 'Segoe UI Semibold'
SL   = 'Segoe UI Light'
SR   = 'Segoe UI'

# ── Tables ────────────────────────────────────────────────────────────────────

NAV_ITEMS = [
    ('Identifiers',     'Identifiers'),
    ('Countries',       'Countries'),
    ('ConsumerUnits',   'Consumer Units'),
    ('Ownership',       'Ownership'),
    ('Relationships',   'Relationships'),
    ('Characteristics', 'Characteristics'),
]

TABLE_COLS = {
    'Identifiers':     (['Identifier Name', 'Description', 'Type'],            'identifier_name'),
    'Countries':       (['Name', 'ISO Code', 'Short Code'],                    'name'),
    'ConsumerUnits':   (['# Consumers', 'Country Name'],                       'country_name'),
    'Ownership':       (['Identifier Name', 'Originator First', 'User ID'],    'identifier_name'),
    'Relationships':   (['From Identifier', 'To Identifier', 'Relationship'],  'from_identifier_name'),
    'Characteristics': (['Master Name', 'Name', 'Specifics'],                  'master_name'),
}

# ── Application ───────────────────────────────────────────────────────────────

class Application:
    def __init__(self, root, db_connection):
        self.root          = root
        self.dq            = DataQuery(db_connection)
        self.current_table = 'Identifiers'
        self.nav_rows      = {}
        self.trees         = {}
        self.table_frames  = {}

        self._apply_style()
        self._build_ui()
        self._select_table('Identifiers')

    # ── ttk theming ───────────────────────────────────────────────────────────

    def _apply_style(self):
        s = ttk.Style()
        s.theme_use('clam')

        s.configure('T.Treeview',
            background=TREE_A,
            foreground=TEXT,
            fieldbackground=TREE_A,
            borderwidth=0,
            font=(SL, 10),
            rowheight=32,
        )
        s.configure('T.Treeview.Heading',
            background=HEAD_BG,
            foreground=ACCENT,
            font=(SB, 9),
            borderwidth=0,
            relief='flat',
            padding=(12, 8),
        )
        s.map('T.Treeview',
            background=[('selected', TREE_SEL)],
            foreground=[('selected', TEXT)],
        )
        s.map('T.Treeview.Heading',
            background=[('active', HEAD_BG)],
        )
        s.configure('S.Vertical.TScrollbar',
            background=CARD,
            troughcolor=SURFACE,
            borderwidth=0,
            arrowcolor=BORDER_LT,
            width=5,
        )

    # ── UI build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.configure(bg=BG)

        # ── Topbar ────────────────────────────────────────────────────────────
        topbar = tk.Frame(self.root, bg=SIDEBAR, height=68)
        topbar.pack(fill='x')
        topbar.pack_propagate(False)

        # Logo
        try:
            _img = Image.open('pg_logo.png').convert('RGBA')
            _img = _img.resize((46, 46), Image.LANCZOS)
            self._logo = ImageTk.PhotoImage(_img)
            tk.Label(topbar, image=self._logo, bg=SIDEBAR, bd=0
                     ).pack(side='left', padx=(18, 12), pady=11)
        except Exception:
            c = tk.Canvas(topbar, width=46, height=46, bg=SIDEBAR, highlightthickness=0)
            c.pack(side='left', padx=(18, 12), pady=11)
            c.create_oval(2, 2, 44, 44, fill=ACCENT_DK, outline='')
            c.create_text(23, 24, text='P&G', fill='#fff', font=(SB, 10))

        # Title
        tk.Label(topbar, text='Database Manager', bg=SIDEBAR,
                 fg=TEXT, font=(SB, 14)).pack(side='left', pady=22)

        # Live indicator dot + text
        dot_frame = tk.Frame(topbar, bg=SIDEBAR)
        dot_frame.pack(side='right', padx=26, pady=26)
        dot = tk.Canvas(dot_frame, width=8, height=8, bg=SIDEBAR, highlightthickness=0)
        dot.pack(side='left', padx=(0, 5))
        dot.create_oval(1, 1, 7, 7, fill=SUCCESS, outline='')
        tk.Label(dot_frame, text='Live', bg=SIDEBAR, fg=TEXT_MED,
                 font=(SR, 9)).pack(side='left')

        # Topbar bottom border
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill='x')

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill='both', expand=True)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = tk.Frame(body, bg=SIDEBAR, width=228)
        sidebar.pack(fill='y', side='left')
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=SIDEBAR, height=10).pack()

        for table_name, label in NAV_ITEMS:
            row = tk.Frame(sidebar, bg=SIDEBAR, cursor='hand2')
            row.pack(fill='x')

            bar = tk.Frame(row, bg=SIDEBAR, width=3)
            bar.pack(side='left', fill='y')

            lbl = tk.Label(row, text=label, bg=SIDEBAR, fg=TEXT_MUTED,
                           font=(SR, 10), anchor='w', padx=18, pady=12)
            lbl.pack(side='left', fill='x', expand=True)

            for w in (row, lbl):
                w.bind('<Button-1>', lambda _, t=table_name: self._select_table(t))
                w.bind('<Enter>',    lambda _, r=row, l=lbl, t=table_name: self._hover_on(r, l, t))
                w.bind('<Leave>',    lambda _, r=row, l=lbl, t=table_name: self._hover_off(r, l, t))

            self.nav_rows[table_name] = (row, bar, lbl)

        # Sidebar border
        tk.Frame(body, bg=BORDER, width=1).pack(fill='y', side='left')

        # ── Main content ──────────────────────────────────────────────────────
        content = tk.Frame(body, bg=BG)
        content.pack(fill='both', expand=True)

        # -- Status bar (pack bottom-up so table expands correctly) ------------
        tk.Frame(content, bg=BORDER, height=1).pack(fill='x', side='bottom')
        sbar = tk.Frame(content, bg=SIDEBAR, height=28)
        sbar.pack(fill='x', side='bottom')
        sbar.pack_propagate(False)
        self.status_var = tk.StringVar(value='Ready')
        tk.Label(sbar, textvariable=self.status_var, bg=SIDEBAR, fg=TEXT_MUTED,
                 font=(SL, 9), anchor='w').pack(side='left', padx=20, fill='y')

        # -- Input / action row ------------------------------------------------
        tk.Frame(content, bg=BORDER, height=1).pack(fill='x', side='bottom')

        ctrl = tk.Frame(content, bg=BG, height=88)
        ctrl.pack(fill='x', side='bottom')
        ctrl.pack_propagate(False)

        # Input fields (Identifiers only)
        self.input_frame = tk.Frame(ctrl, bg=BG)
        self.input_frame.pack(side='left', fill='y', padx=(24, 0))

        self.entries = {}
        for i, (key, label) in enumerate([
            ('identifier_name', 'IDENTIFIER NAME'),
            ('description',     'DESCRIPTION'),
            ('identifier_type', 'TYPE'),
        ]):
            col = tk.Frame(self.input_frame, bg=BG)
            col.grid(row=0, column=i, padx=(0, 12), pady=20)
            tk.Label(col, text=label, bg=BG, fg=TEXT,
                     font=(SR, 7, 'bold')).pack(anchor='w', pady=(0, 4))
            e = tk.Entry(col, bg=CARD, fg=TEXT, insertbackground=ACCENT,
                         relief='flat', font=(SL, 11), width=20,
                         highlightthickness=1,
                         highlightbackground=BORDER_LT,
                         highlightcolor=ACCENT)
            e.pack(ipady=8)
            self.entries[key] = e

        # Buttons
        btn_row = tk.Frame(ctrl, bg=BG)
        btn_row.pack(side='right', padx=24, fill='y', anchor='center')
        self._btn(btn_row, '+ Add Entry',     SUCCESS, SUCCESS_DK, self._add_identifier ).pack(side='left', padx=(0, 10))
        self._btn(btn_row, 'Delete Selected', DANGER,  DANGER_DK,  self._delete_selected).pack(side='left')

        # -- Content header ----------------------------------------------------
        ch = tk.Frame(content, bg=BG, height=62)
        ch.pack(fill='x', padx=26, pady=(22, 0))
        ch.pack_propagate(False)

        self.title_lbl = tk.Label(ch, text='', bg=BG, fg=TEXT,
                                  font=(SB, 15), anchor='w')
        self.title_lbl.pack(side='left', fill='y')

        self.count_lbl = tk.Label(ch, text='', bg=BG, fg=TEXT_MUTED,
                                  font=(SL, 9), anchor='e')
        self.count_lbl.pack(side='right', fill='y')

        # Accent underline beneath title
        accent_line = tk.Frame(content, bg=ACCENT, height=2)
        accent_line.pack(fill='x', padx=26)
        # Full-width separator in a dimmer color to close off the gap
        tk.Frame(content, bg=BORDER, height=1).pack(fill='x', padx=26)

        # -- Table area --------------------------------------------------------
        table_area = tk.Frame(content, bg=BG)
        table_area.pack(fill='both', expand=True, padx=26, pady=(8, 0))

        for tname, (cols, _) in TABLE_COLS.items():
            frame = tk.Frame(table_area, bg=SURFACE)

            tree = ttk.Treeview(frame, columns=cols, show='headings',
                                style='T.Treeview', selectmode='browse')
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=160, minwidth=80, stretch=True)
            tree.tag_configure('a', background=TREE_A)
            tree.tag_configure('b', background=TREE_B)

            vsb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview,
                                style='S.Vertical.TScrollbar')
            tree.configure(yscrollcommand=vsb.set)
            vsb.pack(side='right', fill='y')
            tree.pack(fill='both', expand=True)

            self.trees[tname]        = tree
            self.table_frames[tname] = frame

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _btn(self, parent, text, color, dark, cmd):
        b = tk.Label(parent, text=text, bg=color, fg='#fff',
                     font=(SB, 9), padx=18, pady=9, cursor='hand2')
        b.bind('<Button-1>', lambda _: cmd())
        b.bind('<Enter>',    lambda _: b.config(bg=dark))
        b.bind('<Leave>',    lambda _: b.config(bg=color))
        return b

    def _hover_on(self, row, lbl, table_name):
        if table_name == self.current_table:
            return
        row.config(bg=SURFACE)
        lbl.config(bg=SURFACE, fg=TEXT_MED)

    def _hover_off(self, row, lbl, table_name):
        if table_name == self.current_table:
            return
        row.config(bg=SIDEBAR)
        lbl.config(bg=SIDEBAR, fg=TEXT_MUTED)

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _select_table(self, table_name):
        for name, (row, bar, lbl) in self.nav_rows.items():
            if name == table_name:
                row.config(bg=SURFACE)
                bar.config(bg=ACCENT)
                lbl.config(bg=SURFACE, fg=TEXT, font=(SB, 10))
            else:
                row.config(bg=SIDEBAR)
                bar.config(bg=SIDEBAR)
                lbl.config(bg=SIDEBAR, fg=TEXT_MUTED, font=(SR, 10))

        for name, frame in self.table_frames.items():
            frame.pack_forget()
        self.table_frames[table_name].pack(fill='both', expand=True)

        if table_name == 'Identifiers':
            self.input_frame.pack(side='left', fill='y', padx=(24, 0))
        else:
            self.input_frame.pack_forget()

        self.current_table = table_name
        self.title_lbl.config(text=table_name)
        self._load_table(table_name)

    def _load_table(self, table_name):
        tree = self.trees[table_name]
        tree.delete(*tree.get_children())

        data = self.dq.fetch_all(table_name)
        for i, row in enumerate(data):
            tree.insert('', 'end', values=[str(v) for v in row],
                        tags=('a' if i % 2 == 0 else 'b',))

        n = len(data)
        self.count_lbl.config(text=f'{n} record{"s" if n != 1 else ""}')
        self.status_var.set(f'Loaded {n} record{"s" if n != 1 else ""} from {table_name}')

    def _add_identifier(self):
        name  = self.entries['identifier_name'].get().strip()
        desc  = self.entries['description'].get().strip()
        itype = self.entries['identifier_type'].get().strip()

        if not (name and desc and itype):
            self.status_var.set('All three fields are required.')
            return

        self.dq.insert_identifier(name, desc, itype)

        tree = self.trees['Identifiers']
        n    = len(tree.get_children())
        tree.insert('', 'end', values=(name, desc, itype),
                    tags=('a' if n % 2 == 0 else 'b',))

        for e in self.entries.values():
            e.delete(0, tk.END)

        self.count_lbl.config(text=f'{n + 1} records')
        self.status_var.set(f'Added identifier: {name}')

    def _delete_selected(self):
        tree     = self.trees[self.current_table]
        selected = tree.selection()
        if not selected:
            self.status_var.set('No row selected.')
            return

        id_value       = tree.item(selected, 'values')[0]
        _, id_col      = TABLE_COLS[self.current_table]

        self.dq.delete_entry(self.current_table, id_col, id_value)
        tree.delete(selected)

        n = len(tree.get_children())
        self.count_lbl.config(text=f'{n} record{"s" if n != 1 else ""}')
        self.status_var.set(f'Deleted: {id_value}')

# ── Entry point ───────────────────────────────────────────────────────────────

def run_app():
    db_connection = DatabaseConnection()
    db_connection.connect()

    root = tk.Tk()
    root.title('P&G Database Manager')
    root.geometry('1200x740')
    root.minsize(920, 580)

    Application(root, db_connection)
    root.mainloop()
    db_connection.close()

if __name__ == '__main__':
    run_app()
