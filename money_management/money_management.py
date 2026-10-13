from datetime import datetime, timedelta
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

DATA_FILE = "restaurant_data.json"

MENU = {
    "Main Courses": {
        "Special Beef Pho": {
            "price": 65000,
            "image": "images/pho.png",
        },
        "Grilled Pork Chop Rice": {
            "price": 55000,
            "image": "images/pork_rice.png",
        },
        "Hanoi Bun Cha": {"price": 50000, "image": "images/buncha.png"},
        "Seafood Fried Noodles": {
            "price": 60000,
            "image": "images/noodles.png",
        },
    },
    "Beverages": {
        "Coca Cola": {"price": 15000, "image": "images/coca.png"},
        "Ice Tea": {"price": 5000, "image": "images/icetea.png"},
        "Fresh Orange Juice": {
            "price": 30000,
            "image": "images/orange_juice.png",
        },
        "Heineken Beer": {"price": 25000, "image": "images/beer.png"},
    },
    "Appetizers / Snacks": {
        "French Fries": {"price": 30000, "image": "images/fries.png"},
        "Spring Rolls": {"price": 40000, "image": "images/spring_rolls.png"},
        "Crab Soup": {"price": 35000, "image": "images/crab_soup.png"},
    },
}


def load_data():
  """Load restaurant data from JSON file."""
  if not os.path.exists(DATA_FILE):
    return {"orders": [], "expenses": []}

  try:
    with open(DATA_FILE, "r", encoding="utf-8") as file:
      data = json.load(file)
      if "orders" not in data:
        data["orders"] = []
      if "expenses" not in data:
        data["expenses"] = []
      return data
  except (json.JSONDecodeError, FileNotFoundError):
    return {"orders": [], "expenses": []}


def save_data():
  """Save all data to JSON file."""
  with open(DATA_FILE, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=4, ensure_ascii=False)


data = load_data()


def get_today():
  return datetime.now().strftime("%Y-%m-%d")


def get_current_time():
  return datetime.now().strftime("%H:%M:%S")


def get_next_order_id():
  if not data["orders"]:
    return 1
  return max(order["id"] for order in data["orders"]) + 1


def calculate_daily_totals(date):
  cash = 0
  card = 0
  expenses = 0

  for order in data["orders"]:
    if order["date"] == date:
      if order["payment_method"] == "Cash":
        cash += order["amount"]
      elif order["payment_method"] == "Card":
        card += order["amount"]

  for expense in data["expenses"]:
    if expense["date"] == date:
      expenses += expense["amount"]

  total_sales = cash + card
  profit = total_sales - expenses
  return cash, card, total_sales, expenses, profit


# MAIN INTERFACE
root = tk.Tk()
root.title("Restaurant Management System - POS with Images")
root.geometry("1050x720")
root.minsize(950, 650)
root.configure(bg="#f2f2f2")

title_label = tk.Label(
    root,
    text="RESTAURANT MANAGEMENT SYSTEM (POS)",
    font=("Arial", 20, "bold"),
    bg="#f2f2f2",
)
title_label.pack(pady=10)

top_frame = tk.Frame(root, bg="#f2f2f2")
top_frame.pack(pady=2)

date_label = tk.Label(
    top_frame, text="Working Date:", font=("Arial", 11), bg="#f2f2f2"
)
date_label.grid(row=0, column=0, padx=5)

today_label = tk.Label(
    top_frame, text=get_today(), font=("Arial", 11, "bold"), bg="#f2f2f2"
)
today_label.grid(row=0, column=1, padx=5)

# 1. Order & Menu Frame
order_frame = tk.LabelFrame(
    root,
    text="New Order & Menu Selection",
    font=("Arial", 12, "bold"),
    padx=15,
    pady=10,
)
order_frame.pack(fill="x", padx=30, pady=5)

# Table Selection
tk.Label(order_frame, text="Table:", font=("Arial", 11)).grid(
    row=0, column=0, padx=5, pady=5, sticky="w"
)
table_var = tk.StringVar(value="Table 1")
table_combo = ttk.Combobox(
    order_frame,
    textvariable=table_var,
    values=[f"Table {i}" for i in range(1, 16)],
    state="readonly",
    width=10,
)
table_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")

# Payment Method
tk.Label(order_frame, text="Payment:", font=("Arial", 11)).grid(
    row=0, column=2, padx=5, pady=5, sticky="w"
)
payment_var = tk.StringVar(value="Cash")
payment_combo = ttk.Combobox(
    order_frame,
    textvariable=payment_var,
    values=["Cash", "Card"],
    state="readonly",
    width=10,
)
payment_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")

current_order_items = []

# Danh sách giữ tham chiếu ảnh để tránh bị Garbage Collection của Python xóa mất
img_references = []


# Menu Window Selection with Images Preview
def open_menu_window():
  global img_references
  img_references = []  # Clear references cũ

  menu_win = tk.Toplevel(root)
  menu_win.title("Restaurant Menu with Images")
  menu_win.geometry("750x550")

  tk.Label(
      menu_win, text="RESTAURANT MENU CATALOG", font=("Arial", 14, "bold")
  ).pack(pady=10)

  notebook = ttk.Notebook(menu_win)
  notebook.pack(fill="both", expand=True, padx=15, pady=5)

  selected_items_temp = list(current_order_items)

  bottom_frame = tk.Frame(menu_win, padx=10, pady=10)
  bottom_frame.pack(fill="x", padx=15)

  selected_lbl = tk.Label(
      bottom_frame,
      text=f"Selected: {len(selected_items_temp)} items",
      font=("Arial", 11, "bold"),
      fg="#27ae60",
  )
  selected_lbl.pack(side=tk.LEFT)

  for category, items in MENU.items():
    tab = ttk.Frame(notebook)
    notebook.add(tab, text=category)

    # Frame chứa danh sách món (bên trái) và khung xem trước ảnh (bên phải)
    left_sub_frame = tk.Frame(tab)
    left_sub_frame.pack(
        side=tk.LEFT, fill="both", expand=True, padx=5, pady=5
    )

    right_sub_frame = tk.LabelFrame(
        tab, text="Image Preview", font=("Arial", 10, "bold"), width=200, padx=10
    )
    right_sub_frame.pack(
        side=tk.RIGHT, fill="y", expand=False, padx=5, pady=5
    )
    right_sub_frame.pack_propagate(False)

    img_label = tk.Label(
        right_sub_frame,
        text="No image\nselected",
        bg="#e0e0e0",
        font=("Arial", 10),
    )
    img_label.pack(fill="both", expand=True, padx=5, pady=5)

    tree = ttk.Treeview(
        left_sub_frame, columns=("item", "price"), show="headings", height=10
    )
    tree.heading("item", text="Item Name")
    tree.heading("price", text="Price ($)")
    tree.column("item", width=220)
    tree.column("price", width=120, anchor="e")
    tree.pack(fill="both", expand=True, padx=5, pady=5)

    for item_name, info in items.items():
      tree.insert(
          "",
          tk.END,
          values=(item_name, f"{info['price']:,.0f} $"),
          tag=(info["image"], info["price"]),
      )

    # Sự kiện khi click chọn món trên bảng -> Hiển thị hình ảnh tương ứng
    def on_item_select(event, t=tree, lbl=img_label, cat=category):
      selected_item = t.selection()
      if not selected_item:
        return
      item_values = t.item(selected_item[0], "values")
      item_name = item_values[0]
      img_path = MENU[cat][item_name]["image"]

      if os.path.exists(img_path):
        try:
          # Mở ảnh và resize về kích thước 150x150 pixel
          pil_img = Image.open(img_path)
          pil_img = pil_img.resize((150, 150), Image.Resampling.LANCZOS)
          tk_img = ImageTk.PhotoImage(pil_img)

          lbl.config(image=tk_img, text="")
          # Giữ tham chiếu để ảnh không bị biến mất do bộ gom rác Python
          img_references.append(tk_img)
        except Exception as e:
          lbl.config(image="", text="Load image error")
      else:
        lbl.config(image="", text="Image not found\n(Check folder 'images')")

    tree.bind("<<TreeviewSelect>>", on_item_select)

    def add_item_to_order(t=tree, cat=category):
      selected_item = t.selection()
      if not selected_item:
        messagebox.showwarning("Warning", "Please select an item from the list!")
        return
      item_values = t.item(selected_item[0], "values")
      item_name = item_values[0]
      item_price = MENU[cat][item_name]["price"]

      selected_items_temp.append({"name": item_name, "price": item_price})
      selected_lbl.config(
          text=f"Selected: {len(selected_items_temp)} items in order"
      )

    add_btn = tk.Button(
        tab,
        text="➕ Add Item to Order",
        bg="#2ecc71",
        fg="white",
        font=("Arial", 10, "bold"),
        command=add_item_to_order,
    )
    add_btn.pack(pady=5)

  def confirm_selection():
    global current_order_items
    current_order_items = selected_items_temp
    total_amount = sum(item["price"] for item in current_order_items)
    order_summary_label.config(
        text=(
            f"Table: {table_var.get()} | Items: {len(current_order_items)} |"
            f" Total: {total_amount:,.0f} $"
        )
    )
    menu_win.destroy()

  confirm_btn = tk.Button(
      bottom_frame,
      text="Confirm Selection",
      bg="#3498db",
      fg="white",
      font=("Arial", 11, "bold"),
      command=confirm_selection,
  )
  confirm_btn.pack(side=tk.RIGHT)


# Summary & Action Buttons
order_summary_frame = tk.Frame(order_frame, bg="#ffffff", padx=10, pady=8)
order_summary_frame.grid(row=1, column=0, columnspan=6, sticky="we", pady=5)

order_summary_label = tk.Label(
    order_summary_frame,
    text="Table: Table 1 | Items: 0 | Total: 0 $",
    font=("Arial", 11, "bold"),
    bg="#ffffff",
    fg="#e74c3c",
)
order_summary_label.pack(side=tk.LEFT)

open_menu_btn = tk.Button(
    order_frame,
    text="📖 OPEN MENU & IMAGES",
    font=("Arial", 10, "bold"),
    bg="#9b59b6",
    fg="white",
    command=open_menu_window,
)
open_menu_btn.grid(row=0, column=4, padx=10, pady=5)


def save_current_order():
  global current_order_items
  if not current_order_items:
    messagebox.showwarning("Empty", "No items selected for this order yet!")
    return

  total_amount = sum(item["price"] for item in current_order_items)

  order = {
      "id": get_next_order_id(),
      "table": table_var.get(),
      "date": get_today(),
      "time": get_current_time(),
      "amount": total_amount,
      "payment_method": payment_var.get(),
      "items": list(current_order_items),
  }

  data["orders"].append(order)
  save_data()
  messagebox.showinfo(
      "Success",
      f"Order saved for {order['table']} with total amount"
      f" {total_amount:,.0f} $!",
  )

  current_order_items = []
  order_summary_label.config(text="Table: Table 1 | Items: 0 | Total: 0 $")
  update_dashboard()


checkout_btn = tk.Button(
    order_frame,
    text="💾 SAVE & CHECKOUT",
    font=("Arial", 10, "bold"),
    bg="#e67e22",
    fg="white",
    command=save_current_order,
)
checkout_btn.grid(row=0, column=5, padx=10, pady=5)


# 2. Expense Frame
expense_frame = tk.LabelFrame(
    root, text="Daily Expense Management", font=("Arial", 12, "bold"), padx=15, pady=10
)
expense_frame.pack(fill="x", padx=30, pady=5)

tk.Label(expense_frame, text="Expense Amount ($):", font=("Arial", 11)).grid(
    row=0, column=0, padx=5, pady=5
)
expense_entry = tk.Entry(expense_frame, width=15, font=("Arial", 11))
expense_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(expense_frame, text="Description:", font=("Arial", 11)).grid(
    row=0, column=2, padx=5, pady=5
)
description_entry = tk.Entry(expense_frame, width=22, font=("Arial", 11))
description_entry.grid(row=0, column=3, padx=5, pady=5)


def add_expense():
  amount_text = expense_entry.get().strip()
  description = description_entry.get().strip()

  try:
    amount = float(amount_text)
    if amount <= 0:
      raise ValueError
  except ValueError:
    messagebox.showerror(
        "Error", "Please enter a valid expense amount greater than 0."
    )
    return

  if not description:
    description = "General Expense"

  expense = {
      "id": len(data["expenses"]) + 1,
      "date": get_today(),
      "time": get_current_time(),
      "amount": amount,
      "description": description,
  }

  data["expenses"].append(expense)
  save_data()
  messagebox.showinfo("Success", "Expense recorded successfully.")
  expense_entry.delete(0, tk.END)
  description_entry.delete(0, tk.END)
  update_dashboard()


add_expense_btn = tk.Button(
    expense_frame,
    text="ADD EXPENSE",
    font=("Arial", 10, "bold"),
    bg="#c0392b",
    fg="white",
    command=add_expense,
)
add_expense_btn.grid(row=0, column=4, padx=15, pady=5)


# 3. Dashboard Frame
dashboard_frame = tk.LabelFrame(
    root, text="Today's Revenue Summary", font=("Arial", 12, "bold"), padx=15, pady=10
)
dashboard_frame.pack(fill="x", padx=30, pady=5)

cash_value = tk.Label(dashboard_frame, text="0 $", font=("Arial", 12, "bold"))
cash_value.grid(row=0, column=1, padx=15)
tk.Label(dashboard_frame, text="Cash Sales", font=("Arial", 10)).grid(
    row=1, column=1
)

card_value = tk.Label(dashboard_frame, text="0 $", font=("Arial", 12, "bold"))
card_value.grid(row=0, column=2, padx=15)
tk.Label(dashboard_frame, text="Card Sales", font=("Arial", 10)).grid(
    row=1, column=2
)

sales_value = tk.Label(dashboard_frame, text="0 $", font=("Arial", 12, "bold"))
sales_value.grid(row=0, column=3, padx=15)
tk.Label(dashboard_frame, text="Total Revenue", font=("Arial", 10)).grid(
    row=1, column=3
)

expenses_value = tk.Label(
    dashboard_frame, text="0 $", font=("Arial", 12, "bold"), fg="#c0392b"
)
expenses_value.grid(row=0, column=4, padx=15)
tk.Label(dashboard_frame, text="Total Expenses", font=("Arial", 10)).grid(
    row=1, column=4
)

profit_value = tk.Label(
    dashboard_frame, text="0 $", font=("Arial", 12, "bold"), fg="#27ae60"
)
profit_value.grid(row=0, column=5, padx=15)
tk.Label(dashboard_frame, text="Net Profit", font=("Arial", 10)).grid(
    row=1, column=5
)


def update_dashboard():
  today = get_today()
  cash, card, sales, expenses, profit = calculate_daily_totals(today)
  cash_value.config(text=f"{cash:,.0f} $")
  card_value.config(text=f"{card:,.0f} $")
  sales_value.config(text=f"{sales:,.0f} $")
  expenses_value.config(text=f"{expenses:,.0f} $")
  profit_value.config(text=f"{profit:,.0f} $")


# NAVIGATION BUTTONS
button_frame = tk.Frame(root, bg="#f2f2f2")
button_frame.pack(pady=10)


def view_orders():
  window = tk.Toplevel(root)
  window.title("Order History")
  window.geometry("850x450")
  tk.Label(
      window, text="CUSTOMER ORDERS LIST", font=("Arial", 14, "bold")
  ).pack(pady=10)

  columns = ("id", "table", "date", "time", "amount", "payment", "items")
  tree = ttk.Treeview(window, columns=columns, show="headings")
  tree.heading("id", text="ID")
  tree.heading("table", text="Table")
  tree.heading("date", text="Date")
  tree.heading("time", text="Time")
  tree.heading("amount", text="Total")
  tree.heading("payment", text="Payment")
  tree.heading("items", text="Order Details")

  tree.column("id", width=40)
  tree.column("table", width=70)
  tree.column("date", width=90)
  tree.column("time", width=70)
  tree.column("amount", width=100)
  tree.column("payment", width=80)
  tree.column("items", width=350)

  tree.pack(fill="both", expand=True, padx=15, pady=10)

  for order in data["orders"]:
    items_str = ", ".join(
        [
            f"{item['name']} ({item['price']:,.0f})"
            for item in order.get("items", [])
        ]
    )
    tree.insert(
        "",
        tk.END,
        values=(
            order["id"],
            order.get("table", "Table ?"),
            order["date"],
            order["time"],
            f"{order['amount']:,.0f} $",
            order["payment_method"],
            items_str,
        ),
    )


def daily_report():
  window = tk.Toplevel(root)
  window.title("Daily Report")
  window.geometry("450x350")
  tk.Label(
      window, text="DAILY FINANCIAL REPORT", font=("Arial", 14, "bold")
  ).pack(pady=15)

  date = get_today()
  cash, card, sales, expenses, profit = calculate_daily_totals(date)
  report_text = (
      f"Date: {date}\n\n"
      f"💵 Cash Sales:        {cash:,.0f} $\n"
      f"💳 Card Sales:        {card:,.0f} $\n"
      f"💰 Total Revenue:     {sales:,.0f} $\n"
      f"💸 Total Expenses:    {expenses:,.0f} $\n"
      f"📈 Net Profit:        {profit:,.0f} $"
  )
  tk.Label(window, text=report_text, font=("Arial", 12), justify="left").pack(
      pady=10
  )


def weekly_report():
  window = tk.Toplevel(root)
  window.title("Weekly Report")
  window.geometry("750x520")
  tk.Label(
      window, text="WEEKLY / MULTI-DAY SUMMARY", font=("Arial", 14, "bold")
  ).pack(pady=10)

  input_frame = tk.Frame(window)
  input_frame.pack(pady=5)

  tk.Label(input_frame, text="Start Date (YYYY-MM-DD):").grid(
      row=0, column=0, padx=5
  )
  start_entry = tk.Entry(input_frame, width=15)
  start_entry.grid(row=0, column=1, padx=5)
  start_entry.insert(0, get_today())

  result_text = tk.Text(window, width=75, height=18, font=("Courier New", 10))
  result_text.pack(padx=20, pady=10)

  def generate_report():
    try:
      start_date = datetime.strptime(
          start_entry.get().strip(), "%Y-%m-%d"
      ).date()
    except ValueError:
      messagebox.showerror("Error", "Invalid date format (YYYY-MM-DD).")
      return

    end_date = start_date + timedelta(days=6)
    result_text.delete("1.0", tk.END)
    result_text.insert(
        tk.END,
        f"--- SUMMARY FROM {start_date} TO {end_date} ---\n\n",
    )

    for i in range(7):
      current_date = start_date + timedelta(days=i)
      date_str = current_date.strftime("%Y-%m-%d")
      _, _, sales, expenses, profit = calculate_daily_totals(date_str)
      result_text.insert(
          tk.END,
          f"Date: {date_str} | Revenue: {sales:,.0f} | Expenses:"
          f" {expenses:,.0f} | Profit: {profit:,.0f} $\n",
      )

  tk.Button(
      input_frame,
      text="Generate Summary",
      bg="#2980b9",
      fg="white",
      command=generate_report,
  ).grid(row=0, column=2, padx=5)
  generate_report()


def view_chart():
  window = tk.Toplevel(root)
  window.title("Sales Chart")
  window.geometry("720x420")
  window.configure(bg="#ffffff")

  tk.Label(
      window,
      text="LAST 7 DAYS CHART (REVENUE & PROFIT)",
      font=("Arial", 12, "bold"),
      bg="#ffffff",
  ).pack(pady=10)

  canvas = tk.Canvas(window, width=680, height=300, bg="#f9f9f9")
  canvas.pack(pady=5)

  dates = []
  sales_list = []
  profits_list = []

  end_date = datetime.now().date()
  start_date = end_date - timedelta(days=6)

  for i in range(7):
    current_date = start_date + timedelta(days=i)
    date_str = current_date.strftime("%Y-%m-%d")
    dates.append(current_date.strftime("%d/%m"))
    _, _, sales, _, profit = calculate_daily_totals(date_str)
    sales_list.append(sales)
    profits_list.append(profit)

  max_val = max(sales_list + profits_list) if (sales_list + profits_list) else 1
  if max_val == 0:
    max_val = 1

  canvas_width = 680
  canvas_height = 300
  margin_left = 60
  margin_bottom = 35
  chart_width = canvas_width - margin_left - 30
  chart_height = canvas_height - margin_bottom - 30

  canvas.create_line(
      margin_left,
      canvas_height - margin_bottom,
      canvas_width - 15,
      canvas_height - margin_bottom,
      fill="black",
      width=2,
  )
  canvas.create_line(
      margin_left,
      15,
      margin_left,
      canvas_height - margin_bottom,
      fill="black",
      width=2,
  )

  for i in range(5):
    val = max_val * (i / 4)
    y_pos = (canvas_height - margin_bottom) - (val / max_val) * chart_height
    canvas.create_line(
        margin_left - 5, y_pos, margin_left, y_pos, fill="black"
    )
    canvas.create_text(
        margin_left - 10,
        y_pos,
        text=f"{val:,.0f}",
        anchor="e",
        font=("Arial", 8),
    )

  num_bars = len(dates)
  group_width = chart_width / num_bars

  for i in range(num_bars):
    group_x = margin_left + i * group_width + group_width / 2
    bar_width = group_width * 0.35

    sales_h = (sales_list[i] / max_val) * chart_height
    canvas.create_rectangle(
        group_x - bar_width - 2,
        (canvas_height - margin_bottom) - sales_h,
        group_x - 2,
        canvas_height - margin_bottom,
        fill="#3498db",
    )

    profit_h = (max(0, profits_list[i]) / max_val) * chart_height
    canvas.create_rectangle(
        group_x + 2,
        (canvas_height - margin_bottom) - profit_h,
        group_x + bar_width + 2,
        canvas_height - margin_bottom,
        fill="#2ecc71",
    )

    canvas.create_text(
        group_x,
        canvas_height - margin_bottom + 12,
        text=dates[i],
        font=("Arial", 9),
    )

  canvas.create_rectangle(
      margin_left + 30, 8, margin_left + 45, 18, fill="#3498db"
  )
  canvas.create_text(
      margin_left + 50, 13, text="Revenue", anchor="w", font=("Arial", 9)
  )
  canvas.create_rectangle(
      margin_left + 130, 8, margin_left + 145, 18, fill="#2ecc71"
  )
  canvas.create_text(
      margin_left + 150, 13, text="Profit", anchor="w", font=("Arial", 9)
  )


tk.Button(
    button_frame,
    text="📋 VIEW ORDERS",
    width=16,
    font=("Arial", 10, "bold"),
    command=view_orders,
).grid(row=0, column=0, padx=4)
tk.Button(
    button_frame,
    text="📊 DAILY REPORT",
    width=16,
    font=("Arial", 10, "bold"),
    command=daily_report,
).grid(row=0, column=1, padx=4)
tk.Button(
    button_frame,
    text="📅 WEEKLY REPORT",
    width=16,
    font=("Arial", 10, "bold"),
    command=weekly_report,
).grid(row=0, column=2, padx=4)
tk.Button(
    button_frame,
    text="📈 SALES CHART",
    width=16,
    font=("Arial", 10, "bold"),
    bg="#e67e22",
    fg="white",
    command=view_chart,
).grid(row=0, column=3, padx=4)

update_dashboard()
root.mainloop()