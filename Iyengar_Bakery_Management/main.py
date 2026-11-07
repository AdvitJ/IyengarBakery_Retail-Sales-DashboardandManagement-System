"""
Iyengar Bakery — Retail Sales Dashboard & Management System
A beginner-friendly desktop application using Tkinter, Pandas, Matplotlib and CSV.

Run:
    pip install -r requirements.txt
    python main.py
"""

import csv
import os
import shutil
import tempfile
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

APP_TITLE = "Iyengar Bakery — Retail Sales Dashboard & Management System"
BASE_DIR = Path(__file__).resolve().parent
PRODUCTS_FILE = BASE_DIR / "products.csv"
SALES_FILE = BASE_DIR / "sales.csv"

PRODUCT_COLUMNS = [
    "product_id", "product_name", "category", "price", "stock",
    "low_stock_threshold", "active"
]
SALE_COLUMNS = [
    "sale_id", "sale_date", "product_id", "product_name", "category",
    "quantity", "unit_price", "total_amount"
]
MONEY = "₹{:,.2f}"
COLORS = {
    "cream": "#F7F2E8", "paper": "#FFFCF6", "brown": "#624631",
    "brown_dark": "#3E2B20", "green": "#6F8061", "green_dark": "#526447",
    "muted": "#817568", "line": "#DCCFBC", "warning": "#A94F35",
    "white": "#FFFFFF",
}

SAMPLE_PRODUCTS = [
    ["IB001", "Veg Puff", "Puffs & Snacks", 25, 42, 8, True],
    ["IB002", "Paneer Puff", "Puffs & Snacks", 35, 18, 5, True],
    ["IB003", "Aloo Bun", "Buns & Rolls", 20, 30, 8, True],
    ["IB004", "Masala Bun", "Buns & Rolls", 25, 24, 6, True],
    ["IB005", "Khara Bun", "Buns & Rolls", 25, 16, 5, True],
    ["IB006", "Dil Pasand", "Sweet Bakery", 30, 22, 6, True],
    ["IB007", "Coconut Bun", "Sweet Bakery", 30, 14, 5, True],
    ["IB008", "Honey Cake", "Cakes", 40, 12, 4, True],
    ["IB009", "Plum Cake Slice", "Cakes", 45, 10, 4, True],
    ["IB010", "Rusk (Pack)", "Biscuits & Rusk", 50, 26, 7, True],
    ["IB011", "Butter Biscuits", "Biscuits & Rusk", 40, 20, 6, True],
    ["IB012", "Khara Biscuit", "Biscuits & Rusk", 35, 17, 5, True],
    ["IB013", "Veg Sandwich", "Quick Bites", 55, 15, 5, True],
    ["IB014", "Samosa", "Puffs & Snacks", 20, 35, 8, True],
    ["IB015", "Cream Roll", "Sweet Bakery", 25, 19, 5, True],
]

def seed_sales():
    """Create a small realistic demo sales history for the first launch."""
    today = date.today()
    rows = []
    transactions = [
        (0, "IB001", 5), (0, "IB003", 4), (0, "IB006", 3),
        (1, "IB014", 6), (1, "IB010", 2), (1, "IB002", 2),
        (2, "IB001", 4), (2, "IB013", 2), (2, "IB008", 1),
        (3, "IB004", 3), (3, "IB011", 2), (3, "IB015", 4),
        (4, "IB001", 7), (4, "IB014", 5), (4, "IB005", 2),
        (5, "IB006", 4), (5, "IB009", 2), (5, "IB012", 3),
        (6, "IB003", 5), (6, "IB013", 3), (6, "IB010", 2),
        (7, "IB002", 3), (7, "IB007", 2), (7, "IB014", 4),
        (8, "IB001", 6), (8, "IB008", 2), (8, "IB011", 3),
        (9, "IB004", 4), (9, "IB006", 3), (9, "IB015", 2),
    ]
    lookup = {p[0]: p for p in SAMPLE_PRODUCTS}
    for n, (days_ago, pid, qty) in enumerate(transactions, 1):
        product = lookup[pid]
        price = float(product[3])
        rows.append([
            f"SALE{n:04d}", (today - pd.Timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            pid, product[1], product[2], qty, price, round(qty * price, 2)
        ])
    return rows

def ensure_csv_files():
    """Create starter CSV files with realistic Iyengar Bakery demo data."""
    if not PRODUCTS_FILE.exists():
        pd.DataFrame(SAMPLE_PRODUCTS, columns=PRODUCT_COLUMNS).to_csv(
            PRODUCTS_FILE, index=False, encoding="utf-8-sig")
    if not SALES_FILE.exists():
        pd.DataFrame(seed_sales(), columns=SALE_COLUMNS).to_csv(
            SALES_FILE, index=False, encoding="utf-8-sig")

def read_csv_safely(path, required_columns):
    try:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        missing = [c for c in required_columns if c not in frame.columns]
        if missing:
            raise ValueError("Missing required column(s): " + ", ".join(missing))
        return frame[required_columns].copy()
    except pd.errors.EmptyDataError:
        raise ValueError(f"{path.name} is empty or has no header row.")
    except (OSError, UnicodeError, pd.errors.ParserError) as exc:
        raise ValueError(f"Could not read {path.name}: {exc}")

def clean_products(frame):
    result = frame.copy()
    for col in PRODUCT_COLUMNS:
        if col not in result.columns:
            raise ValueError(f"Products data is missing column: {col}")
    result = result[PRODUCT_COLUMNS].fillna("")
    if result.empty:
        return pd.DataFrame(columns=PRODUCT_COLUMNS)
    for col in ["product_id", "product_name", "category"]:
        result[col] = result[col].astype(str).str.strip()
    if (result.product_id == "").any() or result.product_id.duplicated().any():
        raise ValueError("Product IDs must be present and unique.")
    if (result.product_name == "").any() or (result.category == "").any():
        raise ValueError("Every product needs a name and category.")
    for col in ["price", "stock", "low_stock_threshold"]:
        result[col] = pd.to_numeric(result[col], errors="raise")
    if (result.price < 0).any():
        raise ValueError("Product prices cannot be negative.")
    for col in ["stock", "low_stock_threshold"]:
        if (result[col] < 0).any() or ((result[col] % 1) != 0).any():
            raise ValueError(f"{col} must contain non-negative whole numbers.")
    result["stock"] = result.stock.astype(int)
    result["low_stock_threshold"] = result.low_stock_threshold.astype(int)
    result["active"] = result.active.astype(str).str.strip().str.lower().map(
        lambda x: "False" if x in ("false", "0", "no", "inactive") else "True")
    return result

def clean_sales(frame):
    result = frame.copy()
    for col in SALE_COLUMNS:
        if col not in result.columns:
            raise ValueError(f"Sales data is missing column: {col}")
    result = result[SALE_COLUMNS].fillna("")
    if result.empty:
        return pd.DataFrame(columns=SALE_COLUMNS)
    result["sale_id"] = result.sale_id.astype(str).str.strip()
    if (result.sale_id == "").any() or result.sale_id.duplicated().any():
        raise ValueError("Sale IDs must be present and unique.")
    dates = pd.to_datetime(result.sale_date, errors="coerce")
    if dates.isna().any():
        raise ValueError("Sales contain invalid dates. Use YYYY-MM-DD.")
    result["sale_date"] = dates.dt.strftime("%Y-%m-%d")
    for col in ["product_id", "product_name", "category"]:
        result[col] = result[col].astype(str).str.strip()
    if (result.product_name == "").any():
        raise ValueError("Every sale needs a product name.")
    for col in ["quantity", "unit_price", "total_amount"]:
        result[col] = pd.to_numeric(result[col], errors="raise")
    if (result.quantity <= 0).any() or ((result.quantity % 1) != 0).any():
        raise ValueError("Sale quantities must be positive whole numbers.")
    if (result.unit_price < 0).any():
        raise ValueError("Sale prices cannot be negative.")
    result["quantity"] = result.quantity.astype(int)
    result["total_amount"] = (result.quantity * result.unit_price).round(2)
    return result

def atomic_save(frame, path):
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", newline="", encoding="utf-8-sig",
            dir=path.parent, delete=False, suffix=".tmp"
        ) as temp_file:
            temp_name = temp_file.name
            frame.to_csv(temp_file, index=False)
        os.replace(temp_name, path)
    except Exception:
        if temp_name and os.path.exists(temp_name):
            try:
                os.remove(temp_name)
            except OSError:
                pass
        raise

class IyengarBakeryApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1450x900")
        self.root.minsize(1120, 720)
        self.root.configure(bg=COLORS["cream"])
        ensure_csv_files()
        self.products = clean_products(read_csv_safely(PRODUCTS_FILE, PRODUCT_COLUMNS))
        self.sales = clean_sales(read_csv_safely(SALES_FILE, SALE_COLUMNS))
        self.selected_product_id = None
        self.selected_sale_id = None
        self._build_style()
        self._build_header()
        self._build_tabs()
        self.refresh_all()

    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", font=("Segoe UI", 10))
        style.configure("TFrame", background=COLORS["cream"])
        style.configure("Card.TFrame", background=COLORS["paper"], relief="flat")
        style.configure("TLabel", background=COLORS["cream"], foreground=COLORS["brown_dark"])
        style.configure("Heading.TLabel", font=("Segoe UI", 17, "bold"), foreground=COLORS["brown_dark"])
        style.configure("Subheading.TLabel", font=("Segoe UI", 11, "bold"), foreground=COLORS["brown"])
        style.configure("TButton", padding=(11, 7), background=COLORS["green"], foreground="white")
        style.map("TButton", background=[("active", COLORS["green_dark"])])
        style.configure("Accent.TButton", padding=(12, 8), background=COLORS["brown"], foreground="white")
        style.map("Accent.TButton", background=[("active", COLORS["brown_dark"])])
        style.configure("Treeview", background=COLORS["paper"], fieldbackground=COLORS["paper"],
                        foreground=COLORS["brown_dark"], rowheight=27)
        style.configure("Treeview.Heading", background="#E9DFCE", foreground=COLORS["brown_dark"],
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#D8E0CE")],
                  foreground=[("selected", COLORS["brown_dark"])])
        style.configure("TNotebook", background=COLORS["cream"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 10), background="#E9DFCE")
        style.map("TNotebook.Tab", background=[("selected", COLORS["paper"])])

    def _build_header(self):
        header = tk.Frame(self.root, bg=COLORS["brown_dark"], padx=22, pady=15)
        header.pack(fill="x")
        left = tk.Frame(header, bg=COLORS["brown_dark"])
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text="IYENGAR BAKERY", bg=COLORS["brown_dark"], fg="#FFF8EB",
                 font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(left, text="Retail Sales Dashboard & Management System",
                 bg=COLORS["brown_dark"], fg="#E8D9C5", font=("Segoe UI", 10)).pack(anchor="w")
        tk.Label(header, text="BAKERY MANAGEMENT  •  CSV + PYTHON",
                 bg=COLORS["brown_dark"], fg="#D9C7AE",
                 font=("Segoe UI", 9, "bold")).pack(side="right", anchor="e")

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=(12, 6))
        self.dashboard_tab = ttk.Frame(self.notebook, padding=12)
        self.products_tab = ttk.Frame(self.notebook, padding=12)
        self.sales_tab = ttk.Frame(self.notebook, padding=12)
        self.records_tab = ttk.Frame(self.notebook, padding=12)
        for tab, label in [(self.dashboard_tab, "Dashboard"), (self.products_tab, "Products"),
                           (self.sales_tab, "New Sale"), (self.records_tab, "Sales Records")]:
            self.notebook.add(tab, text=label)
        self._build_dashboard_tab()
        self._build_products_tab()
        self._build_sales_tab()
        self._build_records_tab()
        footer = tk.Frame(self.root, bg=COLORS["cream"], padx=20, pady=7)
        footer.pack(fill="x")
        tk.Label(footer, text="Iyengar Bakery Management System",
                 bg=COLORS["cream"], fg=COLORS["brown"],
                 font=("Segoe UI", 9, "bold")).pack(side="right")

    def _label(self, parent, text, row, column, **kwargs):
        ttk.Label(parent, text=text).grid(row=row, column=column, sticky="w", padx=5, pady=5, **kwargs)

    def _entry(self, parent, variable, row, column, width=24, **kwargs):
        entry = ttk.Entry(parent, textvariable=variable, width=width, **kwargs)
        entry.grid(row=row, column=column, sticky="ew", padx=5, pady=5)
        return entry

    def _make_tree(self, parent, columns, headings, widths=None, height=12):
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)
        tree = ttk.Treeview(container, columns=columns, show="headings", height=height)
        yscroll = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        for i, col in enumerate(columns):
            tree.heading(col, text=headings[i])
            tree.column(col, width=widths[i] if widths else 120, anchor="w")
        tree.tag_configure("low", foreground=COLORS["warning"])
        return tree

    def _next_id(self, prefix, existing, width=4):
        nums = []
        for value in existing:
            value = str(value)
            if value.startswith(prefix) and value[len(prefix):].isdigit():
                nums.append(int(value[len(prefix):]))
        return f"{prefix}{max(nums, default=0) + 1:0{width}d}"

    def _commit(self, products=None, sales=None):
        new_products = clean_products(products if products is not None else self.products)
        new_sales = clean_sales(sales if sales is not None else self.sales)
        atomic_save(new_products[PRODUCT_COLUMNS], PRODUCTS_FILE)
        atomic_save(new_sales[SALE_COLUMNS], SALES_FILE)
        self.products, self.sales = new_products, new_sales
        self.refresh_all()

    def refresh_all(self):
        self.refresh_products_table()
        self.refresh_product_dropdowns()
        self.refresh_sales_table()
        self.refresh_dashboard()

    # ---------------- Products ----------------
    def _build_products_tab(self):
        ttk.Label(self.products_tab, text="Product Catalogue", style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        form = ttk.LabelFrame(self.products_tab, text="Product details", padding=10)
        form.pack(fill="x", pady=(0, 10))
        self.p_id, self.p_name, self.p_category = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.p_price, self.p_stock = tk.StringVar(), tk.StringVar()
        self.p_threshold, self.p_active = tk.StringVar(value="5"), tk.BooleanVar(value=True)
        fields = [("Product ID", self.p_id), ("Product Name", self.p_name),
                  ("Category", self.p_category), ("Selling Price (₹)", self.p_price),
                  ("Current Stock", self.p_stock), ("Low-stock Threshold", self.p_threshold)]
        for i, (label, var) in enumerate(fields):
            r, c = divmod(i, 3)
            self._label(form, label, r * 2, c)
            self._entry(form, var, r * 2 + 1, c, width=27)
        ttk.Checkbutton(form, text="Active product", variable=self.p_active).grid(row=4, column=0, sticky="w", padx=5)
        buttons = ttk.Frame(form)
        buttons.grid(row=4, column=1, columnspan=2, sticky="e")
        for label, command in [("Add Product", self.add_product), ("Update Selected", self.update_product),
                               ("Delete / Deactivate", self.delete_product), ("Clear Form", self.clear_product_form)]:
            ttk.Button(buttons, text=label, command=command).pack(side="left", padx=3)
        tools = ttk.Frame(self.products_tab)
        tools.pack(fill="x", pady=(0, 8))
        self.product_search = tk.StringVar()
        self.product_category_filter = tk.StringVar(value="All categories")
        ttk.Label(tools, text="Search").pack(side="left", padx=(0, 5))
        search = ttk.Entry(tools, textvariable=self.product_search, width=28)
        search.pack(side="left", padx=(0, 12))
        search.bind("<KeyRelease>", lambda _e: self.refresh_products_table())
        ttk.Label(tools, text="Category").pack(side="left", padx=(0, 5))
        self.product_category_combo = ttk.Combobox(tools, textvariable=self.product_category_filter,
                                                    state="readonly", width=23)
        self.product_category_combo.pack(side="left")
        self.product_category_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_products_table())
        ttk.Button(tools, text="Import Products CSV", command=self.import_products).pack(side="right", padx=3)
        ttk.Button(tools, text="Export Products CSV", command=self.export_products).pack(side="right", padx=3)
        cols = ("product_id", "product_name", "category", "price", "stock", "threshold", "active", "status")
        heads = ("Product ID", "Product Name", "Category", "Price", "Stock", "Low-stock At", "Active", "Stock Status")
        self.products_tree = self._make_tree(self.products_tab, cols, heads,
                                             (95, 210, 165, 95, 75, 95, 75, 115), 12)
        self.products_tree.bind("<<TreeviewSelect>>", self.on_product_select)

    def clear_product_form(self):
        self.selected_product_id = None
        for var in (self.p_id, self.p_name, self.p_category, self.p_price, self.p_stock):
            var.set("")
        self.p_threshold.set("5")
        self.p_active.set(True)
        self.p_id.set(self._next_id("IB", self.products.product_id.tolist(), 3))
        self.products_tree.selection_remove(self.products_tree.selection())

    def _validate_product_form(self):
        pid, name, category = self.p_id.get().strip(), self.p_name.get().strip(), self.p_category.get().strip()
        if not pid or not name or not category:
            raise ValueError("Product ID, product name and category are required.")
        try:
            price = float(self.p_price.get())
            stock = int(self.p_stock.get())
            threshold = int(self.p_threshold.get())
        except ValueError:
            raise ValueError("Price must be numeric; stock and threshold must be whole numbers.")
        if price < 0 or stock < 0 or threshold < 0:
            raise ValueError("Price, stock and threshold cannot be negative.")
        return [pid, name, category, price, stock, threshold, bool(self.p_active.get())]

    def add_product(self):
        try:
            values = self._validate_product_form()
            if values[0] in self.products.product_id.astype(str).tolist():
                raise ValueError("That Product ID already exists.")
            new = pd.concat([self.products, pd.DataFrame([values], columns=PRODUCT_COLUMNS)], ignore_index=True)
            self._commit(products=new)
            messagebox.showinfo("Product added", f"{values[1]} was added.")
            self.clear_product_form()
        except Exception as exc:
            messagebox.showerror("Could not add product", str(exc))

    def update_product(self):
        if not self.selected_product_id:
            messagebox.showwarning("Select a product", "Choose a product from the table first.")
            return
        try:
            values = self._validate_product_form()
            if values[0] != self.selected_product_id and values[0] in self.products.product_id.astype(str).tolist():
                raise ValueError("That Product ID already exists.")
            new = self.products.copy()
            idx = new.index[new.product_id == self.selected_product_id][0]
            new.loc[idx] = values
            self._commit(products=new)
            messagebox.showinfo("Updated", "Product details updated.")
            self.clear_product_form()
        except Exception as exc:
            messagebox.showerror("Could not update product", str(exc))

    def delete_product(self):
        if not self.selected_product_id:
            messagebox.showwarning("Select a product", "Choose a product from the table first.")
            return
        if not messagebox.askyesno("Confirm", "Deactivate this product? Existing sales records will be kept."):
            return
        new = self.products.copy()
        new.loc[new.product_id == self.selected_product_id, "active"] = "False"
        self._commit(products=new)
        self.clear_product_form()

    def on_product_select(self, _event=None):
        selected = self.products_tree.selection()
        if not selected:
            return
        vals = self.products_tree.item(selected[0], "values")
        self.selected_product_id = vals[0]
        row = self.products[self.products.product_id == vals[0]].iloc[0]
        self.p_id.set(row.product_id); self.p_name.set(row.product_name)
        self.p_category.set(row.category); self.p_price.set(str(row.price))
        self.p_stock.set(str(row.stock)); self.p_threshold.set(str(row.low_stock_threshold))
        self.p_active.set(row.active == "True")

    def refresh_products_table(self):
        if not hasattr(self, "products_tree"):
            return
        self.products_tree.delete(*self.products_tree.get_children())
        if not self.products.empty:
            data = self.products.copy()
            term = self.product_search.get().strip().lower()
            if term:
                data = data[data.apply(lambda r: term in " ".join(map(str, r.values)).lower(), axis=1)]
            category = self.product_category_filter.get()
            if category and category != "All categories":
                data = data[data.category == category]
            for _, r in data.iterrows():
                status = "Low stock" if int(r.stock) <= int(r.low_stock_threshold) else "In stock"
                self.products_tree.insert("", "end", values=(
                    r.product_id, r.product_name, r.category, MONEY.format(float(r.price)),
                    r.stock, r.low_stock_threshold, r.active, status),
                    tags=("low",) if status == "Low stock" else ())

    def refresh_product_dropdowns(self):
        if not hasattr(self, "product_category_combo"):
            return
        categories = sorted(self.products.category.dropna().astype(str).unique().tolist()) if not self.products.empty else []
        self.product_category_combo["values"] = ["All categories"] + categories
        if self.product_category_filter.get() not in ["All categories"] + categories:
            self.product_category_filter.set("All categories")
        active = self.products[self.products.active == "True"] if not self.products.empty else self.products
        self.sale_product_combo["values"] = [
            f"{r.product_id} — {r.product_name} (₹{float(r.price):.2f})" for _, r in active.iterrows()
        ]
        if self.sale_product_var.get() not in self.sale_product_combo["values"]:
            self.sale_product_var.set("")

    def import_products(self):
        path = filedialog.askopenfilename(title="Import products CSV", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            imported = clean_products(read_csv_safely(Path(path), PRODUCT_COLUMNS))
            if imported.product_id.duplicated().any():
                raise ValueError("Imported Product IDs must be unique.")
            self._commit(products=imported)
            messagebox.showinfo("Import complete", f"Imported {len(imported)} products.")
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))

    def export_products(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
                                            initialfile="iyengar_bakery_products.csv")
        if path:
            try:
                self.products[PRODUCT_COLUMNS].to_csv(path, index=False, encoding="utf-8-sig")
                messagebox.showinfo("Export complete", "Products exported successfully.")
            except Exception as exc:
                messagebox.showerror("Export failed", str(exc))

    # ---------------- Sales entry ----------------
    def _build_sales_tab(self):
        ttk.Label(self.sales_tab, text="Record a New Sale", style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        form = ttk.LabelFrame(self.sales_tab, text="Sale details", padding=16)
        form.pack(fill="x", anchor="n")
        self.sale_product_var = tk.StringVar()
        self.sale_quantity_var = tk.StringVar(value="1")
        self.sale_date_var = tk.StringVar(value=date.today().isoformat())
        self.sale_product_combo = ttk.Combobox(form, textvariable=self.sale_product_var, state="readonly", width=52)
        self._label(form, "Product", 0, 0)
        self.sale_product_combo.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self._label(form, "Quantity", 0, 1)
        self._entry(form, self.sale_quantity_var, 1, 1, width=15)
        self._label(form, "Sale date (YYYY-MM-DD)", 0, 2)
        self._entry(form, self.sale_date_var, 1, 2, width=18)
        ttk.Button(form, text="Record Sale", style="Accent.TButton", command=self.record_sale).grid(
            row=2, column=0, sticky="w", padx=5, pady=14)
        self.sale_total_label = ttk.Label(form, text="Select a product to see its price.", style="Subheading.TLabel")
        self.sale_total_label.grid(row=2, column=1, columnspan=2, sticky="w", padx=5)
        self.sale_product_combo.bind("<<ComboboxSelected>>", self.update_sale_preview)
        self.sale_quantity_var.trace_add("write", lambda *_: self.update_sale_preview())
        ttk.Label(self.sales_tab, text="Stock is reduced automatically when a sale is recorded. "
                  "A sale cannot be saved if the requested quantity exceeds available stock.",
                  wraplength=900).pack(anchor="w", pady=14)

    def update_sale_preview(self, _event=None):
        if not hasattr(self, "sale_total_label"):
            return
        product = self._selected_sale_product()
        try:
            qty = int(self.sale_quantity_var.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            self.sale_total_label.config(text="Enter a positive whole-number quantity.")
            return
        if product is None:
            self.sale_total_label.config(text="Select a product to see its price.")
        else:
            self.sale_total_label.config(text=f"Unit price: {MONEY.format(float(product.price))}     "
                                             f"Total: {MONEY.format(float(product.price) * qty)}     "
                                             f"Available: {int(product.stock)}")

    def _selected_sale_product(self):
        value = self.sale_product_var.get()
        if not value:
            return None
        pid = value.split(" — ", 1)[0]
        matches = self.products[self.products.product_id == pid]
        return None if matches.empty else matches.iloc[0]

    def record_sale(self):
        try:
            product = self._selected_sale_product()
            if product is None:
                raise ValueError("Select a product.")
            qty = int(self.sale_quantity_var.get())
            if qty <= 0:
                raise ValueError("Quantity must be a positive whole number.")
            sale_date = datetime.strptime(self.sale_date_var.get().strip(), "%Y-%m-%d").date()
            if qty > int(product.stock):
                raise ValueError(f"Only {int(product.stock)} item(s) are currently in stock.")
            price = float(product.price)
            sale = [self._next_id("SALE", self.sales.sale_id.tolist()), sale_date.isoformat(),
                    product.product_id, product.product_name, product.category, qty, price, round(qty * price, 2)]
            new_sales = pd.concat([self.sales, pd.DataFrame([sale], columns=SALE_COLUMNS)], ignore_index=True)
            new_products = self.products.copy()
            new_products.loc[new_products.product_id == product.product_id, "stock"] = int(product.stock) - qty
            self._commit(products=new_products, sales=new_sales)
            messagebox.showinfo("Sale recorded", f"Sale saved.\nTotal: {MONEY.format(qty * price)}")
            self.sale_quantity_var.set("1")
            self.sale_product_var.set("")
            self.sale_date_var.set(date.today().isoformat())
            self.update_sale_preview()
        except Exception as exc:
            messagebox.showerror("Could not record sale", str(exc))

    # ---------------- Sales records ----------------
    def _build_records_tab(self):
        ttk.Label(self.records_tab, text="Sales History", style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        tools = ttk.Frame(self.records_tab)
        tools.pack(fill="x", pady=(0, 8))
        self.record_search_var = tk.StringVar()
        ttk.Label(tools, text="Search").pack(side="left", padx=(0, 5))
        search = ttk.Entry(tools, textvariable=self.record_search_var, width=28)
        search.pack(side="left", padx=(0, 10))
        search.bind("<KeyRelease>", lambda _e: self.refresh_sales_table())
        ttk.Button(tools, text="Export Sales CSV", command=self.export_sales).pack(side="right", padx=3)
        ttk.Button(tools, text="Delete Selected Sale", command=self.delete_sale).pack(side="right", padx=3)
        cols = ("sale_id", "sale_date", "product_id", "product_name", "category", "quantity", "unit_price", "total_amount")
        heads = ("Sale ID", "Date", "Product ID", "Product", "Category", "Qty", "Unit Price", "Total")
        self.sales_tree = self._make_tree(self.records_tab, cols, heads,
                                          (105, 105, 95, 180, 145, 55, 100, 110), 15)
        self.sales_tree.bind("<<TreeviewSelect>>", self.on_sale_select)

    def refresh_sales_table(self):
        if not hasattr(self, "sales_tree"):
            return
        self.sales_tree.delete(*self.sales_tree.get_children())
        if self.sales.empty:
            return
        data = self.sales.sort_values(["sale_date", "sale_id"], ascending=[False, False])
        term = self.record_search_var.get().strip().lower()
        if term:
            data = data[data.apply(lambda r: term in " ".join(map(str, r.values)).lower(), axis=1)]
        for _, r in data.iterrows():
            self.sales_tree.insert("", "end", values=(
                r.sale_id, r.sale_date, r.product_id, r.product_name, r.category,
                r.quantity, MONEY.format(float(r.unit_price)), MONEY.format(float(r.total_amount))))

    def on_sale_select(self, _event=None):
        selected = self.sales_tree.selection()
        self.selected_sale_id = self.sales_tree.item(selected[0], "values")[0] if selected else None

    def delete_sale(self):
        if not self.selected_sale_id:
            messagebox.showwarning("Select a sale", "Choose a sale record first.")
            return
        if not messagebox.askyesno("Confirm deletion", "Delete this sale and restore its quantity to stock?"):
            return
        matches = self.sales[self.sales.sale_id == self.selected_sale_id]
        if matches.empty:
            return
        sale = matches.iloc[0]
        new_sales = self.sales[self.sales.sale_id != self.selected_sale_id].copy()
        new_products = self.products.copy()
        mask = new_products.product_id == sale.product_id
        if mask.any():
            new_products.loc[mask, "stock"] = new_products.loc[mask, "stock"].astype(int) + int(sale.quantity)
        self._commit(products=new_products, sales=new_sales)
        self.selected_sale_id = None
        messagebox.showinfo("Sale deleted", "Sale removed and stock restored.")

    def export_sales(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
                                            initialfile="iyengar_bakery_sales.csv")
        if path:
            try:
                self.sales[SALE_COLUMNS].to_csv(path, index=False, encoding="utf-8-sig")
                messagebox.showinfo("Export complete", "Sales exported successfully.")
            except Exception as exc:
                messagebox.showerror("Export failed", str(exc))

    # ---------------- Dashboard ----------------
    def _build_dashboard_tab(self):
        ttk.Label(self.dashboard_tab, text="Business Overview", style="Heading.TLabel").pack(anchor="w", pady=(0, 10))
        cards = ttk.Frame(self.dashboard_tab)
        cards.pack(fill="x", pady=(0, 10))
        self.metric_labels = {}
        for key, title in [("revenue", "Total Revenue"), ("orders", "Total Sales"),
                           ("products", "Active Products"), ("low", "Low-stock Items")]:
            card = tk.Frame(cards, bg=COLORS["paper"], padx=18, pady=13,
                            highlightbackground=COLORS["line"], highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=5)
            tk.Label(card, text=title, bg=COLORS["paper"], fg=COLORS["muted"],
                     font=("Segoe UI", 10)).pack(anchor="w")
            value = tk.Label(card, text="—", bg=COLORS["paper"], fg=COLORS["brown_dark"],
                             font=("Segoe UI", 19, "bold"))
            value.pack(anchor="w", pady=(5, 0))
            self.metric_labels[key] = value
        chart_area = ttk.Frame(self.dashboard_tab)
        chart_area.pack(fill="both", expand=True)
        self.figure = Figure(figsize=(10, 4.6), dpi=100, facecolor=COLORS["cream"])
        self.ax_sales = self.figure.add_subplot(121)
        self.ax_products = self.figure.add_subplot(122)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_area)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        ttk.Button(self.dashboard_tab, text="Refresh Dashboard", command=self.refresh_dashboard).pack(anchor="e", pady=5)

    def refresh_dashboard(self):
        if not hasattr(self, "metric_labels"):
            return
        revenue = float(self.sales.total_amount.sum()) if not self.sales.empty else 0
        orders = len(self.sales)
        active = int((self.products.active == "True").sum()) if not self.products.empty else 0
        low = int(((self.products.stock <= self.products.low_stock_threshold) &
                   (self.products.active == "True")).sum()) if not self.products.empty else 0
        self.metric_labels["revenue"].config(text=MONEY.format(revenue))
        self.metric_labels["orders"].config(text=str(orders))
        self.metric_labels["products"].config(text=str(active))
        self.metric_labels["low"].config(text=str(low))
        self.ax_sales.clear(); self.ax_products.clear()
        self.ax_sales.set_title("Revenue by Date", color=COLORS["brown_dark"])
        if not self.sales.empty:
            daily = self.sales.groupby("sale_date").total_amount.sum().sort_index().tail(10)
            self.ax_sales.bar(daily.index, daily.values, color=COLORS["green"])
            self.ax_sales.tick_params(axis="x", rotation=40, labelsize=8)
            self.ax_sales.set_ylabel("Revenue (₹)")
        else:
            self.ax_sales.text(.5, .5, "No sales recorded", ha="center", va="center", transform=self.ax_sales.transAxes)
        self.ax_products.set_title("Top Selling Products", color=COLORS["brown_dark"])
        if not self.sales.empty:
            top = self.sales.groupby("product_name").quantity.sum().sort_values(ascending=False).head(6).sort_values()
            self.ax_products.barh(top.index, top.values, color=COLORS["brown"])
            self.ax_products.set_xlabel("Units sold")
            self.ax_products.tick_params(axis="y", labelsize=8)
        else:
            self.ax_products.text(.5, .5, "No sales recorded", ha="center", va="center", transform=self.ax_products.transAxes)
        self.figure.tight_layout()
        self.canvas.draw_idle()

def main():
    root = tk.Tk()
    try:
        IyengarBakeryApp(root)
    except Exception as exc:
        messagebox.showerror("Startup error", f"The application could not start:\n{exc}")
        root.destroy()
        raise
    root.mainloop()

if __name__ == "__main__":
    main()
