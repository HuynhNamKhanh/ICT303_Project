import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, timedelta

DATA_FILE = "restaurant_data.json"

def load_data():
    """Load restaurant data from JSON file."""

    if not os.path.exists(DATA_FILE):
        return {
            "orders": [],
            "expenses": []
        }

    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)

            if "orders" not in data:
                data["orders"] = []

            if "expenses" not in data:
                data["expenses"] = []

            return data

    except (json.JSONDecodeError, FileNotFoundError):
        return {
            "orders": [],
            "expenses": []
        }


def save_data():
    """Save all data to JSON file."""

    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

data = load_data()

def get_today():
    """Return today's date."""

    return datetime.now().strftime("%Y-%m-%d")


def get_current_time():
    """Return current time."""

    return datetime.now().strftime("%H:%M:%S")


def get_next_order_id():
    """Generate the next order ID."""

    if not data["orders"]:
        return 1

    return max(order["id"] for order in data["orders"]) + 1


def calculate_daily_totals(date):
    """Calculate cash, card, sales, expenses and profit."""

    cash = 0
    card = 0
    expenses = 0

    # Calculate sales
    for order in data["orders"]:

        if order["date"] == date:

            if order["payment_method"] == "Cash":
                cash += order["amount"]

            elif order["payment_method"] == "Card":
                card += order["amount"]

    # Calculate expenses
    for expense in data["expenses"]:

        if expense["date"] == date:
            expenses += expense["amount"]

    total_sales = cash + card
    profit = total_sales - expenses

    return cash, card, total_sales, expenses, profit

root = tk.Tk()

root.title("Restaurant Management System")
root.geometry("1000x650")
root.minsize(900, 600)

root.configure(bg="#f2f2f2")

title_label = tk.Label(
    root,
    text="RESTAURANT MANAGEMENT SYSTEM",
    font=("Arial", 22, "bold"),
    bg="#f2f2f2"
)

title_label.pack(pady=20)

top_frame = tk.Frame(
    root,
    bg="#f2f2f2"
)

top_frame.pack(pady=5)


date_label = tk.Label(
    top_frame,
    text="Date:",
    font=("Arial", 12),
    bg="#f2f2f2"
)

date_label.grid(row=0, column=0, padx=5)


today_label = tk.Label(
    top_frame,
    text=get_today(),
    font=("Arial", 12, "bold"),
    bg="#f2f2f2"
)

today_label.grid(row=0, column=1, padx=5)

order_frame = tk.LabelFrame(
    root,
    text="New Order / Customer Payment",
    font=("Arial", 13, "bold"),
    padx=15,
    pady=15
)

order_frame.pack(
    fill="x",
    padx=30,
    pady=10
)


# Amount

amount_label = tk.Label(
    order_frame,
    text="Order Amount ($):",
    font=("Arial", 11)
)

amount_label.grid(
    row=0,
    column=0,
    padx=10,
    pady=10
)


amount_entry = tk.Entry(
    order_frame,
    width=20,
    font=("Arial", 11)
)

amount_entry.grid(
    row=0,
    column=1,
    padx=10,
    pady=10
)


# Payment method

payment_label = tk.Label(
    order_frame,
    text="Payment Method:",
    font=("Arial", 11)
)

payment_label.grid(
    row=0,
    column=2,
    padx=10,
    pady=10
)


payment_var = tk.StringVar()

payment_combo = ttk.Combobox(
    order_frame,
    textvariable=payment_var,
    values=["Cash", "Card"],
    state="readonly",
    width=15
)

payment_combo.grid(
    row=0,
    column=3,
    padx=10,
    pady=10
)

payment_combo.set("Cash")

def add_order():

    amount_text = amount_entry.get().strip()
    payment_method = payment_var.get()

    # Check amount
    try:
        amount = float(amount_text)

        if amount <= 0:
            raise ValueError

    except ValueError:
        messagebox.showerror(
            "Invalid Amount",
            "Please enter a valid amount greater than 0."
        )
        return

    # Check payment method
    if payment_method not in ["Cash", "Card"]:
        messagebox.showerror(
            "Payment Method",
            "Please select Cash or Card."
        )
        return

    # Create order
    order = {
        "id": get_next_order_id(),
        "date": get_today(),
        "time": get_current_time(),
        "amount": amount,
        "payment_method": payment_method
    }

    data["orders"].append(order)

    save_data()

    messagebox.showinfo(
        "Success",
        f"Order #{order['id']} added successfully."
    )

    amount_entry.delete(0, tk.END)

    update_dashboard()
    refresh_orders()


add_order_button = tk.Button(
    order_frame,
    text="ADD ORDER",
    font=("Arial", 11, "bold"),
    width=15,
    command=add_order
)

add_order_button.grid(
    row=0,
    column=4,
    padx=20
)

expense_frame = tk.LabelFrame(
    root,
    text="Daily Expense",
    font=("Arial", 13, "bold"),
    padx=15,
    pady=15
)

expense_frame.pack(
    fill="x",
    padx=30,
    pady=10
)


expense_label = tk.Label(
    expense_frame,
    text="Expense Amount ($):",
    font=("Arial", 11)
)

expense_label.grid(
    row=0,
    column=0,
    padx=10,
    pady=10
)


expense_entry = tk.Entry(
    expense_frame,
    width=20,
    font=("Arial", 11)
)

expense_entry.grid(
    row=0,
    column=1,
    padx=10,
    pady=10
)


description_label = tk.Label(
    expense_frame,
    text="Description:",
    font=("Arial", 11)
)

description_label.grid(
    row=0,
    column=2,
    padx=10,
    pady=10
)


description_entry = tk.Entry(
    expense_frame,
    width=25,
    font=("Arial", 11)
)

description_entry.grid(
    row=0,
    column=3,
    padx=10,
    pady=10
)

def add_expense():

    amount_text = expense_entry.get().strip()
    description = description_entry.get().strip()

    try:
        amount = float(amount_text)

        if amount <= 0:
            raise ValueError

    except ValueError:
        messagebox.showerror(
            "Invalid Amount",
            "Please enter a valid expense amount."
        )
        return

    if description == "":
        description = "General Expense"

    expense = {
        "id": len(data["expenses"]) + 1,
        "date": get_today(),
        "time": get_current_time(),
        "amount": amount,
        "description": description
    }

    data["expenses"].append(expense)

    save_data()

    messagebox.showinfo(
        "Success",
        "Expense added successfully."
    )

    expense_entry.delete(0, tk.END)
    description_entry.delete(0, tk.END)

    update_dashboard()


add_expense_button = tk.Button(
    expense_frame,
    text="ADD EXPENSE",
    font=("Arial", 11, "bold"),
    width=15,
    command=add_expense
)

add_expense_button.grid(
    row=0,
    column=4,
    padx=20
)

dashboard_frame = tk.LabelFrame(
    root,
    text="Today's Summary",
    font=("Arial", 13, "bold"),
    padx=15,
    pady=15
)

dashboard_frame.pack(
    fill="x",
    padx=30,
    pady=10
)


cash_value = tk.Label(
    dashboard_frame,
    text="$0.00",
    font=("Arial", 14, "bold")
)

cash_value.grid(
    row=0,
    column=1,
    padx=25
)


cash_label = tk.Label(
    dashboard_frame,
    text="Cash Sales",
    font=("Arial", 11)
)

cash_label.grid(
    row=1,
    column=1
)


card_value = tk.Label(
    dashboard_frame,
    text="$0.00",
    font=("Arial", 14, "bold")
)

card_value.grid(
    row=0,
    column=2,
    padx=25
)


card_label = tk.Label(
    dashboard_frame,
    text="Card Sales",
    font=("Arial", 11)
)

card_label.grid(
    row=1,
    column=2
)


sales_value = tk.Label(
    dashboard_frame,
    text="$0.00",
    font=("Arial", 14, "bold")
)

sales_value.grid(
    row=0,
    column=3,
    padx=25
)


sales_label = tk.Label(
    dashboard_frame,
    text="Total Sales",
    font=("Arial", 11)
)

sales_label.grid(
    row=1,
    column=3
)


expenses_value = tk.Label(
    dashboard_frame,
    text="$0.00",
    font=("Arial", 14, "bold")
)

expenses_value.grid(
    row=0,
    column=4,
    padx=25
)


expenses_label = tk.Label(
    dashboard_frame,
    text="Expenses",
    font=("Arial", 11)
)

expenses_label.grid(
    row=1,
    column=4
)


profit_value = tk.Label(
    dashboard_frame,
    text="$0.00",
    font=("Arial", 14, "bold")
)

profit_value.grid(
    row=0,
    column=5,
    padx=25
)


profit_label = tk.Label(
    dashboard_frame,
    text="Net Profit",
    font=("Arial", 11)
)

profit_label.grid(
    row=1,
    column=5
)


# =========================================================
# UPDATE DASHBOARD
# =========================================================

def update_dashboard():

    today = get_today()

    cash, card, sales, expenses, profit = calculate_daily_totals(today)

    cash_value.config(
        text=f"${cash:,.2f}"
    )

    card_value.config(
        text=f"${card:,.2f}"
    )

    sales_value.config(
        text=f"${sales:,.2f}"
    )

    expenses_value.config(
        text=f"${expenses:,.2f}"
    )

    profit_value.config(
        text=f"${profit:,.2f}"
    )

button_frame = tk.Frame(
    root,
    bg="#f2f2f2"
)

button_frame.pack(
    pady=15
)

def view_orders():

    window = tk.Toplevel(root)

    window.title("Orders")
    window.geometry("800x450")

    title = tk.Label(
        window,
        text="ALL CUSTOMER ORDERS",
        font=("Arial", 16, "bold")
    )

    title.pack(pady=10)

    columns = (
        "id",
        "date",
        "time",
        "amount",
        "payment"
    )

    tree = ttk.Treeview(
        window,
        columns=columns,
        show="headings"
    )

    tree.heading("id", text="Order ID")
    tree.heading("date", text="Date")
    tree.heading("time", text="Time")
    tree.heading("amount", text="Amount")
    tree.heading("payment", text="Payment")

    tree.column("id", width=80)
    tree.column("date", width=120)
    tree.column("time", width=100)
    tree.column("amount", width=120)
    tree.column("payment", width=120)

    tree.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    for order in data["orders"]:

        tree.insert(
            "",
            tk.END,
            values=(
                order["id"],
                order["date"],
                order["time"],
                f"${order['amount']:.2f}",
                order["payment_method"]
            )
        )

def daily_report():

    window = tk.Toplevel(root)

    window.title("Daily Report")
    window.geometry("600x500")

    title = tk.Label(
        window,
        text="DAILY FINANCIAL REPORT",
        font=("Arial", 18, "bold")
    )

    title.pack(pady=20)

    date = get_today()

    cash, card, sales, expenses, profit = calculate_daily_totals(date)

    report_text = (
        f"Date: {date}\n\n"
        f"Cash Sales:       ${cash:,.2f}\n\n"
        f"Card Sales:       ${card:,.2f}\n\n"
        f"Total Sales:      ${sales:,.2f}\n\n"
        f"Total Expenses:   ${expenses:,.2f}\n\n"
        f"Net Profit:       ${profit:,.2f}"
    )

    report_label = tk.Label(
        window,
        text=report_text,
        font=("Arial", 13),
        justify="left"
    )

    report_label.pack(
        pady=20
    )

def weekly_report():

    window = tk.Toplevel(root)

    window.title("Weekly Report")
    window.geometry("800x600")

    title = tk.Label(
        window,
        text="WEEKLY FINANCIAL REPORT",
        font=("Arial", 18, "bold")
    )

    title.pack(pady=15)

    input_frame = tk.Frame(window)

    input_frame.pack(pady=10)

    start_label = tk.Label(
        input_frame,
        text="Week starting date (YYYY-MM-DD):"
    )

    start_label.grid(
        row=0,
        column=0,
        padx=5
    )

    start_entry = tk.Entry(
        input_frame,
        width=15
    )

    start_entry.grid(
        row=0,
        column=1,
        padx=5
    )

    start_entry.insert(
        0,
        get_today()
    )

    result_text = tk.Text(
        window,
        width=80,
        height=25,
        font=("Courier New", 10)
    )

    result_text.pack(
        padx=20,
        pady=10
    )

    def generate_report():

        start_date_text = start_entry.get().strip()

        try:
            start_date = datetime.strptime(
                start_date_text,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            messagebox.showerror(
                "Invalid Date",
                "Please enter the date in YYYY-MM-DD format."
            )

            return

        end_date = start_date + timedelta(days=6)

        weekly_orders = []
        weekly_expenses = []

        for order in data["orders"]:

            order_date = datetime.strptime(
                order["date"],
                "%Y-%m-%d"
            ).date()

            if start_date <= order_date <= end_date:
                weekly_orders.append(order)

        for expense in data["expenses"]:

            expense_date = datetime.strptime(
                expense["date"],
                "%Y-%m-%d"
            ).date()

            if start_date <= expense_date <= end_date:
                weekly_expenses.append(expense)

        cash = 0
        card = 0

        for order in weekly_orders:

            if order["payment_method"] == "Cash":
                cash += order["amount"]

            elif order["payment_method"] == "Card":
                card += order["amount"]

        total_sales = cash + card

        total_expenses = sum(
            expense["amount"]
            for expense in weekly_expenses
        )

        profit = total_sales - total_expenses

        result_text.delete(
            "1.0",
            tk.END
        )

        result_text.insert(
            tk.END,
            "====================================================\n"
        )

        result_text.insert(
            tk.END,
            "                 WEEKLY REPORT\n"
        )

        result_text.insert(
            tk.END,
            "====================================================\n\n"
        )

        result_text.insert(
            tk.END,
            f"Week: {start_date} to {end_date}\n\n"
        )

        result_text.insert(
            tk.END,
            f"Cash Sales:       ${cash:,.2f}\n"
        )

        result_text.insert(
            tk.END,
            f"Card Sales:       ${card:,.2f}\n"
        )

        result_text.insert(
            tk.END,
            f"Total Sales:      ${total_sales:,.2f}\n"
        )

        result_text.insert(
            tk.END,
            f"Total Expenses:   ${total_expenses:,.2f}\n"
        )

        result_text.insert(
            tk.END,
            f"Net Profit:       ${profit:,.2f}\n\n"
        )

        result_text.insert(
            tk.END,
            "----------------------------------------------------\n"
        )

        result_text.insert(
            tk.END,
            "DAILY BREAKDOWN\n"
        )

        result_text.insert(
            tk.END,
            "----------------------------------------------------\n\n"
        )

        for i in range(7):

            current_date = start_date + timedelta(days=i)

            date_string = current_date.strftime(
                "%Y-%m-%d"
            )

            day_cash = 0
            day_card = 0
            day_expenses = 0

            for order in weekly_orders:

                if order["date"] == date_string:

                    if order["payment_method"] == "Cash":
                        day_cash += order["amount"]

                    elif order["payment_method"] == "Card":
                        day_card += order["amount"]

            for expense in weekly_expenses:

                if expense["date"] == date_string:
                    day_expenses += expense["amount"]

            day_sales = day_cash + day_card
            day_profit = day_sales - day_expenses

            result_text.insert(
                tk.END,
                f"{date_string}\n"
                f"  Cash:     ${day_cash:,.2f}\n"
                f"  Card:     ${day_card:,.2f}\n"
                f"  Sales:    ${day_sales:,.2f}\n"
                f"  Expenses: ${day_expenses:,.2f}\n"
                f"  Profit:   ${day_profit:,.2f}\n\n"
            )

    generate_button = tk.Button(
        input_frame,
        text="GENERATE REPORT",
        command=generate_report,
        font=("Arial", 10, "bold")
    )

    generate_button.grid(
        row=0,
        column=2,
        padx=10
    )

def view_expenses():

    window = tk.Toplevel(root)

    window.title("Expenses")
    window.geometry("700x450")

    title = tk.Label(
        window,
        text="EXPENSE RECORDS",
        font=("Arial", 16, "bold")
    )

    title.pack(pady=10)

    columns = (
        "id",
        "date",
        "time",
        "amount",
        "description"
    )

    tree = ttk.Treeview(
        window,
        columns=columns,
        show="headings"
    )

    tree.heading("id", text="ID")
    tree.heading("date", text="Date")
    tree.heading("time", text="Time")
    tree.heading("amount", text="Amount")
    tree.heading("description", text="Description")

    tree.column("id", width=50)
    tree.column("date", width=110)
    tree.column("time", width=90)
    tree.column("amount", width=100)
    tree.column("description", width=250)

    tree.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    for expense in data["expenses"]:

        tree.insert(
            "",
            tk.END,
            values=(
                expense["id"],
                expense["date"],
                expense["time"],
                f"${expense['amount']:.2f}",
                expense["description"]
            )
        )

view_orders_button = tk.Button(
    button_frame,
    text="VIEW ORDERS",
    width=16,
    font=("Arial", 10, "bold"),
    command=view_orders
)

view_orders_button.grid(
    row=0,
    column=0,
    padx=5
)


daily_report_button = tk.Button(
    button_frame,
    text="DAILY REPORT",
    width=16,
    font=("Arial", 10, "bold"),
    command=daily_report
)

daily_report_button.grid(
    row=0,
    column=1,
    padx=5
)


weekly_report_button = tk.Button(
    button_frame,
    text="WEEKLY REPORT",
    width=16,
    font=("Arial", 10, "bold"),
    command=weekly_report
)

weekly_report_button.grid(
    row=0,
    column=2,
    padx=5
)


expenses_button = tk.Button(
    button_frame,
    text="VIEW EXPENSES",
    width=16,
    font=("Arial", 10, "bold"),
    command=view_expenses
)

expenses_button.grid(
    row=0,
    column=3,
    padx=5
)

update_dashboard()

root.mainloop()