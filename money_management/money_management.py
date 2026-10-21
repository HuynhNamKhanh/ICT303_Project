import json
import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "restaurant_data.json")
IMG_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMG_DIR, exist_ok=True)

MENU = {
    "Main Courses": {
        "Special Beef Pho": {"price": 30, "image": "pho.png"},
        "Grilled Pork Chop Rice": {"price": 30, "image": "pork_rice.png"},
        "Hanoi Bun Cha": {"price": 30, "image": "buncha.png"},
        "Seafood Fried Noodles": {"price": 30, "image": "noodles.png"},
    },
    "Beverages": {
        "Coca Cola": {"price": 30, "image": "coca.png"},
        "Ice Tea": {"price": 30, "image": "icetea.png"},
        "Fresh Orange Juice": {"price": 30, "image": "orange_juice.png"},
        "Heineken Beer": {"price": 30, "image": "beer.png"},
    },
    "Appetizers / Snacks": {
        "French Fries": {"price": 30, "image": "fries.png"},
        "Spring Rolls": {"price": 30, "image": "spring_rolls.png"},
        "Crab Soup": {"price": 30, "image": "crab_soup.png"},
    },
}


# ------------------------------------------------------------------ data
def load_data():
    empty = {"orders": [], "expenses": []}
    if not os.path.exists(DATA_FILE):
        return empty
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
    except (json.JSONDecodeError, OSError):
        return empty
    d.setdefault("orders", [])
    d.setdefault("expenses", [])
    return d


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


data = load_data()


def money(n):
    return f"${n:,.0f}"


def get_today():
    return datetime.now().strftime("%Y-%m-%d")


def get_current_time():
    return datetime.now().strftime("%H:%M:%S")


def get_next_order_id():
    return max((o["id"] for o in data["orders"]), default=0) + 1


def calculate_daily_totals(date):
    cash = card = expenses = 0
    for o in data["orders"]:
        if o["date"] == date:
            if o["payment_method"] == "Cash":
                cash += o["amount"]
            elif o["payment_method"] == "Card":
                card += o["amount"]
    for e in data["expenses"]:
        if e["date"] == date:
            expenses += e["amount"]
    total = cash + card
    return cash, card, total, expenses, total - expenses


# ------------------------------------------------------------------ main window + styles
root = tk.Tk()
root.title("Restaurant Management System - POS with Images")
root.geometry("1050x720")
root.minsize(950, 650)
root.configure(bg="#f2f2f2")

style = ttk.Style(root)
style.theme_use("clam")  # lets buttons show our colours on macOS


def button_style(name, color, hover):
    style.configure(name, background=color, foreground="white",
                    font=("Arial", 10, "bold"), padding=7, borderwidth=0)
    style.map(name, background=[("active", hover), ("pressed", hover)])


button_style("Green.TButton", "#27ae60", "#1e8449")
button_style("Blue.TButton", "#2980b9", "#1f618d")
button_style("Purple.TButton", "#8e44ad", "#6c3483")
button_style("Orange.TButton", "#e67e22", "#ca6f1e")
button_style("Red.TButton", "#c0392b", "#922b21")
button_style("Grey.TButton", "#7f8c8d", "#626d6e")

tk.Label(root, text="RESTAURANT MANAGEMENT SYSTEM (POS)",
         font=("Arial", 20, "bold"), bg="#f2f2f2").pack(pady=10)

top_frame = tk.Frame(root, bg="#f2f2f2")
top_frame.pack(pady=2)
tk.Label(top_frame, text="Working Date:", font=("Arial", 11), bg="#f2f2f2").grid(row=0, column=0, padx=5)
tk.Label(top_frame, text=get_today(), font=("Arial", 11, "bold"), bg="#f2f2f2").grid(row=0, column=1, padx=5)

# ------------------------------------------------------------------ 1. order frame
order_frame = tk.LabelFrame(root, text="New Order & Menu Selection",
                            font=("Arial", 12, "bold"), padx=15, pady=10)
order_frame.pack(fill="x", padx=30, pady=5)

tk.Label(order_frame, text="Table:", font=("Arial", 11)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
table_var = tk.StringVar(value="Table 1")
table_combo = ttk.Combobox(order_frame, textvariable=table_var,
                           values=[f"Table {i}" for i in range(1, 16)], state="readonly", width=10)
table_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")

tk.Label(order_frame, text="Payment:", font=("Arial", 11)).grid(row=0, column=2, padx=5, pady=5, sticky="w")
payment_var = tk.StringVar(value="Cash")
ttk.Combobox(order_frame, textvariable=payment_var, values=["Cash", "Card"],
             state="readonly", width=10).grid(row=0, column=3, padx=5, pady=5, sticky="w")

current_order_items = []


def update_summary():
    total = sum(i["price"] for i in current_order_items)
    order_summary_label.config(
        text=f"{table_var.get()} | Items: {len(current_order_items)} | Total: {money(total)}")


table_combo.bind("<<ComboboxSelected>>", lambda e: update_summary())


def show_preview(label, filename):
    """Show a dish picture in `label`. Works with or without Pillow."""
    path = os.path.join(IMG_DIR, filename)
    if not os.path.exists(path):
        label.config(image="", text="Image not found\n(put it in the\n'images' folder)")
        label.image = None
        return
    try:
        if HAS_PIL:
            resample = getattr(Image, "Resampling", Image).LANCZOS
            photo = ImageTk.PhotoImage(Image.open(path).resize((150, 150), resample))
        else:  # no Pillow: PNG/GIF only, shrink with subsample
            photo = tk.PhotoImage(file=path)
            factor = max(1, max(photo.width(), photo.height()) // 150)
            if factor > 1:
                photo = photo.subsample(factor, factor)
        label.config(image=photo, text="")
        label.image = photo  # keep a reference so Python does not delete the picture
    except Exception:
        label.config(image="", text="Cannot load image")
        label.image = None


def open_menu_window():
    menu_win = tk.Toplevel(root)
    menu_win.title("Restaurant Menu with Images")
    menu_win.geometry("780x580")
    menu_win.transient(root)

    tk.Label(menu_win, text="RESTAURANT MENU CATALOG", font=("Arial", 14, "bold")).pack(pady=10)

    draft = list(current_order_items)  # working copy until "Confirm"

    bottom = tk.Frame(menu_win, padx=10, pady=10)
    bottom.pack(side="bottom", fill="x", padx=15)
    status_var = tk.StringVar()
    tk.Label(bottom, textvariable=status_var, font=("Arial", 11, "bold"), fg="#27ae60").pack(side="left")

    def refresh_status():
        status_var.set(f"Selected: {len(draft)} items | Total: {money(sum(i['price'] for i in draft))}")

    refresh_status()

    notebook = ttk.Notebook(menu_win)
    notebook.pack(fill="both", expand=True, padx=15, pady=5)

    for category, items in MENU.items():
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=category)

        add_row = ttk.Frame(tab)
        add_row.pack(side="bottom", pady=6)

        left = tk.Frame(tab)
        left.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        right = tk.LabelFrame(tab, text="Image Preview", font=("Arial", 10, "bold"), width=200, padx=10)
        right.pack(side="right", fill="y", padx=5, pady=5)
        right.pack_propagate(False)
        img_label = tk.Label(right, text="Select a dish\nto see its picture", bg="#e0e0e0", font=("Arial", 10))
        img_label.pack(fill="both", expand=True, padx=5, pady=5)

        tree = ttk.Treeview(left, columns=("item", "price"), show="headings", height=10)
        tree.heading("item", text="Item Name")
        tree.heading("price", text="Price")
        tree.column("item", width=220)
        tree.column("price", width=120, anchor="e")
        tree.pack(fill="both", expand=True, padx=5, pady=5)
        for name, info in items.items():
            tree.insert("", tk.END, values=(name, money(info["price"])))

        def on_select(event, t=tree, lbl=img_label, cat=category):
            sel = t.selection()
            if sel:
                name = t.item(sel[0], "values")[0]
                show_preview(lbl, MENU[cat][name]["image"])

        tree.bind("<<TreeviewSelect>>", on_select)

        def add_item(t=tree, cat=category):
            sel = t.selection()
            if not sel:
                messagebox.showwarning("Warning", "Please select an item from the list!", parent=menu_win)
                return
            name = t.item(sel[0], "values")[0]
            draft.append({"name": name, "price": MENU[cat][name]["price"]})
            refresh_status()

        ttk.Button(add_row, text="+ Add Item to Order", style="Green.TButton", command=add_item).pack()

    def remove_last():
        if draft:
            draft.pop()
            refresh_status()

    def confirm():
        global current_order_items
        current_order_items = draft
        update_summary()
        menu_win.destroy()

    ttk.Button(bottom, text="Confirm Selection", style="Blue.TButton", command=confirm).pack(side="right")
    ttk.Button(bottom, text="Remove last item", style="Grey.TButton", command=remove_last).pack(side="right", padx=8)


order_summary_frame = tk.Frame(order_frame, bg="#ffffff", padx=10, pady=8)
order_summary_frame.grid(row=1, column=0, columnspan=6, sticky="we", pady=5)
order_summary_label = tk.Label(order_summary_frame, text="", font=("Arial", 11, "bold"),
                               bg="#ffffff", fg="#e74c3c")
order_summary_label.pack(side="left")

ttk.Button(order_frame, text="OPEN MENU & IMAGES", style="Purple.TButton",
           command=open_menu_window).grid(row=0, column=4, padx=10, pady=5)


def save_current_order():
    global current_order_items
    if not current_order_items:
        messagebox.showwarning("Empty", "No items selected for this order yet!")
        return
    total = sum(i["price"] for i in current_order_items)
    order = {
        "id": get_next_order_id(),
        "table": table_var.get(),
        "date": get_today(),
        "time": get_current_time(),
        "amount": total,
        "payment_method": payment_var.get(),
        "items": list(current_order_items),
    }
    data["orders"].append(order)
    save_data()
    messagebox.showinfo("Success", f"Order saved for {order['table']}: {money(total)}")
    current_order_items = []
    update_summary()
    update_dashboard()


ttk.Button(order_frame, text="SAVE & CHECKOUT", style="Orange.TButton",
           command=save_current_order).grid(row=0, column=5, padx=10, pady=5)

# ------------------------------------------------------------------ 2. expenses
expense_frame = tk.LabelFrame(root, text="Daily Expense Management",
                              font=("Arial", 12, "bold"), padx=15, pady=10)
expense_frame.pack(fill="x", padx=30, pady=5)

tk.Label(expense_frame, text="Expense Amount:", font=("Arial", 11)).grid(row=0, column=0, padx=5, pady=5)
expense_entry = tk.Entry(expense_frame, width=15, font=("Arial", 11))
expense_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Label(expense_frame, text="Description:", font=("Arial", 11)).grid(row=0, column=2, padx=5, pady=5)
description_entry = tk.Entry(expense_frame, width=22, font=("Arial", 11))
description_entry.grid(row=0, column=3, padx=5, pady=5)


def add_expense():
    try:
        amount = float(expense_entry.get().strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid expense amount greater than 0.")
        return
    data["expenses"].append({
        "id": max((e["id"] for e in data["expenses"]), default=0) + 1,
        "date": get_today(),
        "time": get_current_time(),
        "amount": amount,
        "description": description_entry.get().strip() or "General Expense",
    })
    save_data()
    messagebox.showinfo("Success", "Expense recorded successfully.")
    expense_entry.delete(0, tk.END)
    description_entry.delete(0, tk.END)
    update_dashboard()


ttk.Button(expense_frame, text="ADD EXPENSE", style="Red.TButton",
           command=add_expense).grid(row=0, column=4, padx=15, pady=5)

# ------------------------------------------------------------------ 3. dashboard
dashboard_frame = tk.LabelFrame(root, text="Today's Revenue Summary",
                                font=("Arial", 12, "bold"), padx=15, pady=10)
dashboard_frame.pack(fill="x", padx=30, pady=5)

dash_labels = {}
for col, (key, caption, color) in enumerate([
        ("cash", "Cash Sales", "black"), ("card", "Card Sales", "black"),
        ("sales", "Total Revenue", "black"), ("expenses", "Total Expenses", "#c0392b"),
        ("profit", "Net Profit", "#27ae60")], start=1):
    lbl = tk.Label(dashboard_frame, text="$ 0", font=("Arial", 12, "bold"), fg=color)
    lbl.grid(row=0, column=col, padx=15)
    tk.Label(dashboard_frame, text=caption, font=("Arial", 10)).grid(row=1, column=col)
    dash_labels[key] = lbl


def update_dashboard():
    cash, card, sales, expenses, profit = calculate_daily_totals(get_today())
    for key, value in zip(("cash", "card", "sales", "expenses", "profit"),
                          (cash, card, sales, expenses, profit)):
        dash_labels[key].config(text=money(value))


# ------------------------------------------------------------------ reports
def view_orders():
    win = tk.Toplevel(root)
    win.title("Order History")
    win.geometry("900x450")
    tk.Label(win, text="CUSTOMER ORDERS LIST", font=("Arial", 14, "bold")).pack(pady=10)
    cols = ("id", "table", "date", "time", "amount", "payment", "items")
    heads = ("ID", "Table", "Date", "Time", "Total", "Payment", "Order Details")
    widths = (40, 70, 90, 70, 100, 80, 380)
    tree = ttk.Treeview(win, columns=cols, show="headings")
    for c, h, w in zip(cols, heads, widths):
        tree.heading(c, text=h)
        tree.column(c, width=w)
    tree.pack(fill="both", expand=True, padx=15, pady=10)
    for o in reversed(data["orders"]):
        items = ", ".join(f"{i['name']} ({i['price']:,.0f})" for i in o.get("items", []))
        tree.insert("", tk.END, values=(o["id"], o.get("table", "?"), o["date"], o["time"],
                                        money(o["amount"]), o["payment_method"], items))


def daily_report():
    win = tk.Toplevel(root)
    win.title("Daily Report")
    win.geometry("450x330")
    tk.Label(win, text="DAILY FINANCIAL REPORT", font=("Arial", 14, "bold")).pack(pady=15)
    date = get_today()
    cash, card, sales, expenses, profit = calculate_daily_totals(date)
    text = (f"Date: {date}\n\n"
            f"Cash Sales:       {money(cash)}\n"
            f"Card Sales:       {money(card)}\n"
            f"Total Revenue:    {money(sales)}\n"
            f"Total Expenses:   {money(expenses)}\n"
            f"Net Profit:       {money(profit)}")
    tk.Label(win, text=text, font=("Courier New", 12), justify="left").pack(pady=10)


def weekly_report():
    win = tk.Toplevel(root)
    win.title("Weekly Report")
    win.geometry("780x520")
    tk.Label(win, text="WEEKLY / MULTI-DAY SUMMARY", font=("Arial", 14, "bold")).pack(pady=10)
    row = tk.Frame(win)
    row.pack(pady=5)
    tk.Label(row, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5)
    start_entry = tk.Entry(row, width=15)
    start_entry.grid(row=0, column=1, padx=5)
    start_entry.insert(0, get_today())
    result = tk.Text(win, width=80, height=18, font=("Courier New", 10))
    result.pack(padx=20, pady=10)

    def generate():
        try:
            start = datetime.strptime(start_entry.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Error", "Invalid date format (YYYY-MM-DD).", parent=win)
            return
        result.delete("1.0", tk.END)
        result.insert(tk.END, f"--- SUMMARY FROM {start} TO {start + timedelta(days=6)} ---\n\n")
        for i in range(7):
            d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            _, _, sales, expenses, profit = calculate_daily_totals(d)
            result.insert(tk.END, f"{d} | Revenue: {sales:>12,.0f} | Expenses: {expenses:>12,.0f} | Profit: {profit:>12,.0f}\n")

    ttk.Button(row, text="Generate Summary", style="Blue.TButton", command=generate).grid(row=0, column=2, padx=5)
    generate()


def view_chart():
    win = tk.Toplevel(root)
    win.title("Sales Chart")
    win.geometry("720x420")
    win.configure(bg="#ffffff")
    tk.Label(win, text="LAST 7 DAYS CHART (REVENUE & PROFIT)", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=10)
    canvas = tk.Canvas(win, width=680, height=300, bg="#f9f9f9", highlightthickness=0)
    canvas.pack(pady=5)

    end = datetime.now().date()
    dates, sales_list, profits = [], [], []
    for i in range(7):
        day = end - timedelta(days=6 - i)
        dates.append(day.strftime("%d/%m"))
        _, _, sales, _, profit = calculate_daily_totals(day.strftime("%Y-%m-%d"))
        sales_list.append(sales)
        profits.append(profit)
    max_val = max(sales_list + profits) or 1
    if max_val <= 0:
        max_val = 1

    W, H, ml, mb = 680, 300, 70, 35
    chart_w, chart_h = W - ml - 30, H - mb - 30
    base = H - mb
    canvas.create_line(ml, base, W - 15, base, width=2)
    canvas.create_line(ml, 15, ml, base, width=2)
    for i in range(5):
        val = max_val * i / 4
        y = base - (val / max_val) * chart_h
        canvas.create_line(ml - 5, y, ml, y)
        canvas.create_text(ml - 8, y, text=f"{val:,.0f}", anchor="e", font=("Arial", 8))

    group = chart_w / 7
    bar = group * 0.35
    for i in range(7):
        gx = ml + i * group + group / 2
        sh = (sales_list[i] / max_val) * chart_h
        ph = (max(0, profits[i]) / max_val) * chart_h
        canvas.create_rectangle(gx - bar - 2, base - sh, gx - 2, base, fill="#3498db", outline="")
        canvas.create_rectangle(gx + 2, base - ph, gx + bar + 2, base, fill="#2ecc71", outline="")
        canvas.create_text(gx, base + 12, text=dates[i], font=("Arial", 9))

    canvas.create_rectangle(ml + 30, 8, ml + 45, 18, fill="#3498db", outline="")
    canvas.create_text(ml + 50, 13, text="Revenue", anchor="w", font=("Arial", 9))
    canvas.create_rectangle(ml + 130, 8, ml + 145, 18, fill="#2ecc71", outline="")
    canvas.create_text(ml + 150, 13, text="Profit", anchor="w", font=("Arial", 9))


# ------------------------------------------------------------------ bottom buttons
button_frame = tk.Frame(root, bg="#f2f2f2")
button_frame.pack(pady=10)
for col, (text, cmd, st) in enumerate([
        ("VIEW ORDERS", view_orders, "Blue.TButton"),
        ("DAILY REPORT", daily_report, "Blue.TButton"),
        ("WEEKLY REPORT", weekly_report, "Blue.TButton"),
        ("SALES CHART", view_chart, "Orange.TButton")]):
    ttk.Button(button_frame, text=text, style=st, width=16, command=cmd).grid(row=0, column=col, padx=4)

update_summary()
update_dashboard()
root.mainloop()