import hmac
import json
import os
import random
import re
import secrets
import socket
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "restaurant_data.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
IMG_DIR = os.path.join(BASE_DIR, "images")
PAGES = {"/staff": "staff.html", "/order": "order.html"}
TABLES = 15
STATUSES = ("New", "Preparing", "Served", "Cancelled")

DEFAULT_MENU = [
    {"category": "Main courses", "name": "Special Beef Pho", "price": 18.5, "image": "pho.png", "emoji": "🍜"},
    {"category": "Main courses", "name": "Grilled Pork Chop Rice", "price": 19.5, "image": "pork_rice.png", "emoji": "🍚"},
    {"category": "Main courses", "name": "Hanoi Bun Cha", "price": 18.0, "image": "buncha.png", "emoji": "🍖"},
    {"category": "Main courses", "name": "Seafood Fried Noodles", "price": 21.5, "image": "noodles.png", "emoji": "🍝"},
    {"category": "Drinks", "name": "Coca Cola", "price": 4.5, "image": "coca.png", "emoji": "🥤"},
    {"category": "Drinks", "name": "Ice Tea", "price": 4.0, "image": "icetea.png", "emoji": "🧋"},
    {"category": "Drinks", "name": "Fresh Orange Juice", "price": 7.0, "image": "orange_juice.png", "emoji": "🍊"},
    {"category": "Drinks", "name": "Heineken Beer", "price": 9.0, "image": "beer.png", "emoji": "🍺"},
    {"category": "Starters", "name": "French Fries", "price": 8.0, "image": "fries.png", "emoji": "🍟"},
    {"category": "Starters", "name": "Spring Rolls", "price": 10.5, "image": "spring_rolls.png", "emoji": "🥟"},
    {"category": "Starters", "name": "Crab Soup", "price": 12.5, "image": "crab_soup.png", "emoji": "🍲"},
]
MENU_FILE = os.path.join(BASE_DIR, "menu.json")   
MENU = []              
PRICE_CENTS = {}       
MENU_VERSION = int(time.time())
IMAGE_RE = re.compile(r"^[\w\-. ]{1,60}\.(png|jpe?g|gif|webp)$", re.I)

LOCK = threading.RLock()
SESSIONS = {}         
LOGIN_FAILS = {}       
ORDER_TIMES = {}       
SESSION_SECONDS = 12 * 3600


class ApiError(Exception):
    def __init__(self, msg, code=400):
        super().__init__(msg)
        self.msg, self.code = msg, code


#config and data
def load_config():
    cfg = {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        pass
    changed = False
    pin = str(cfg.get("pin", ""))
    if not (pin.isdigit() and len(pin) >= 4):
        cfg["pin"] = f"{secrets.randbelow(10 ** 6):06d}"
        changed = True
        print(f"\n  A new staff PIN was created: {cfg['pin']}")
        print(f"  Change it any time by editing {CONFIG_FILE}\n")
    if not isinstance(cfg.get("port"), int):
        cfg["port"] = 8000
        changed = True
    if changed:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    return cfg


def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d, dict):
            raise ValueError
    except FileNotFoundError:
        d = {}
    except (OSError, ValueError):
        os.replace(DATA_FILE, DATA_FILE + ".broken")   #keep the unreadable file instead of overwriting it
        print("  restaurant_data.json could not be read; it was kept as restaurant_data.json.broken")
        d = {}
    d.setdefault("orders", [])
    d.setdefault("expenses", [])
    return normalize(d)


def normalize(d):
    """Accept data written by the old desktop app (payment_method, no status or source, no quantities)."""
    orders, expenses = [], []
    for o in d["orders"] if isinstance(d["orders"], list) else []:
        if not isinstance(o, dict) or not isinstance(o.get("id"), int):
            continue
        pay = o.get("payment", o.get("payment_method"))
        o.pop("payment_method", None)
        o["payment"] = pay if pay in ("Cash", "Card") else None
        o["status"] = o.get("status") if o.get("status") in STATUSES else "Served"
        o["source"] = "customer" if o.get("source") == "customer" else "staff"
        o["table"] = str(o.get("table") or "?")
        o["date"] = str(o.get("date") or today())
        o["time"] = str(o.get("time") or "00:00:00")
        o["note"] = str(o.get("note") or "")
        items = []
        for i in o.get("items") if isinstance(o.get("items"), list) else []:
            if isinstance(i, dict):
                items.append({"name": str(i.get("name", "?")), "price": float(i.get("price") or 0),
                              "qty": i.get("qty") if isinstance(i.get("qty"), int) and i["qty"] > 0 else 1})
        o["items"] = items
        try:
            o["amount"] = float(o.get("amount") or 0)
        except (TypeError, ValueError):
            o["amount"] = 0.0
        orders.append(o)
    for e in d["expenses"] if isinstance(d["expenses"], list) else []:
        if not isinstance(e, dict) or not isinstance(e.get("id"), int):
            continue
        try:
            e["amount"] = float(e.get("amount") or 0)
        except (TypeError, ValueError):
            e["amount"] = 0.0
        e["date"] = str(e.get("date") or today())
        e["time"] = str(e.get("time") or "00:00:00")
        e["description"] = str(e.get("description") or "General expense")
        expenses.append(e)
    d["orders"], d["expenses"] = orders, expenses
    return d


def save_data():
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(DATA, f, ensure_ascii=False, indent=1)
    os.replace(tmp, DATA_FILE)         #never leaves a half-written file


def today():
    return datetime.now().strftime("%Y-%m-%d")


def now_time():
    return datetime.now().strftime("%H:%M:%S")


def next_id(rows):
    return max((r["id"] for r in rows), default=0) + 1


def add_sample_data():
    if DATA["orders"]:
        return
    rnd = random.Random()
    for i in range(6, 0, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        for k in range(2 + rnd.randrange(3)):
            raw = [{"name": rnd.choice(MENU)["name"], "qty": 1 + rnd.randrange(2)} for _ in range(1 + rnd.randrange(3))]
            items, amount = build_items(raw)
            DATA["orders"].append({
                "id": next_id(DATA["orders"]), "table": f"Table {1 + rnd.randrange(TABLES)}", "date": day,
                "time": f"12:{10 + k * 7:02d}:00", "amount": amount, "payment": rnd.choice(["Cash", "Cash", "Card"]),
                "status": "Served", "source": "staff", "items": items, "note": ""})
        DATA["expenses"].append({"id": next_id(DATA["expenses"]), "date": day, "time": "09:00:00",
                                 "amount": 80 + rnd.randrange(120), "description": "Ingredients (sample)"})
    save_data()


#validation helpers
def build_items(raw):
    """Turn [{name, qty}] from a client into priced items. Prices always come from MENU."""
    if not isinstance(raw, list) or not raw or len(raw) > 30:
        raise ApiError("The order has no items.")
    merged = {}
    for r in raw:
        name = r.get("name") if isinstance(r, dict) else None
        qty = r.get("qty") if isinstance(r, dict) else None
        if name not in PRICE_CENTS:
            raise ApiError("One of the items is no longer available. Please reload the menu.")
        if not isinstance(qty, int) or isinstance(qty, bool) or not 1 <= qty <= 20:
            raise ApiError("Quantity must be a whole number from 1 to 20.")
        merged[name] = merged.get(name, 0) + qty
    if sum(merged.values()) > 50:
        raise ApiError("Too many items in one order.")
    items = [{"name": n, "price": PRICE_CENTS[n] / 100, "qty": q} for n, q in merged.items()]
    cents = sum(PRICE_CENTS[n] * q for n, q in merged.items())
    return items, cents / 100


def parse_table(v):
    if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= TABLES:
        raise ApiError(f"Table must be a number from 1 to {TABLES}.")
    return f"Table {v}"


def parse_payment(v):
    if v not in ("Cash", "Card"):
        raise ApiError("Payment must be Cash or Card.")
    return v


def refresh_prices():
    PRICE_CENTS.clear()
    PRICE_CENTS.update({m["name"]: round(m["price"] * 100) for m in MENU if m["available"]})


def save_menu():
    global MENU_VERSION
    tmp = MENU_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(MENU, f, ensure_ascii=False, indent=1)
    os.replace(tmp, MENU_FILE)
    refresh_prices()
    MENU_VERSION += 1        #lets open pages notice that the menu changed


def clean_menu_item(b, ignore_id=None):
    name = str(b.get("name") or "").strip()
    cat = str(b.get("category") or "").strip()
    if not 1 <= len(name) <= 60:
        raise ApiError("Enter a dish name (up to 60 characters).")
    if not 1 <= len(cat) <= 30:
        raise ApiError("Enter a category (up to 30 characters).")
    price = b.get("price")
    if not isinstance(price, (int, float)) or isinstance(price, bool) or not 0 < price <= 1000:
        raise ApiError("Enter a price between 0.01 and 1000.")
    image = str(b.get("image") or "").strip()
    if image and not IMAGE_RE.match(image):
        raise ApiError("Picture file name must end in .png, .jpg, .jpeg, .gif or .webp and must not contain folders.")
    for m in MENU:
        if m["id"] != ignore_id and m["name"].lower() == name.lower():
            raise ApiError("A dish with this name already exists.")
    return {"category": cat, "name": name, "price": round(price * 100) / 100, "image": image,
            "emoji": str(b.get("emoji") or "").strip()[:8] or "🍽️", "available": b.get("available") is not False}


def find_menu_item(mid):
    for m in MENU:
        if m["id"] == mid:
            return m
    raise ApiError("Dish not found.", 404)


def load_menu():
    try:
        with open(MENU_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            raise ValueError
    except FileNotFoundError:
        raw = None
    except (OSError, ValueError):
        os.replace(MENU_FILE, MENU_FILE + ".broken")
        print("  menu.json could not be read; it was kept as menu.json.broken and the default menu is used")
        raw = None
    MENU.clear()
    used = set()
    for r in (DEFAULT_MENU if raw is None else raw):
        if not isinstance(r, dict):
            continue
        try:
            item = clean_menu_item(r)
        except ApiError:
            continue
        rid = r.get("id")
        item["id"] = rid if isinstance(rid, int) and rid not in used else next_id(MENU)
        used.add(item["id"])
        MENU.append(item)
    refresh_prices()
    if raw is None:
        save_menu()


def find_order(oid):
    for o in DATA["orders"]:
        if o["id"] == oid:
            return o
    raise ApiError("Order not found.", 404)


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))    #no packet is sent
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


#HTTP handler
class Handler(BaseHTTPRequestHandler):
    server_version = "ComNha"

    def log_message(self, *args):
        pass

    #output
    def _send(self, code, body, ctype, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or []):
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, obj, code=200, extra=None):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", extra)

    def send_file(self, path, ctype):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except OSError:
            raise ApiError("Not found.", 404)
        self._send(200, body, ctype)

    #input
    def ip(self):
        return self.client_address[0]

    def read_json(self):
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            raise ApiError("Content-Type must be application/json.", 415)
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise ApiError("Bad request.")
        if n > 20000:
            raise ApiError("Request too large.", 413)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            raise ApiError("Bad JSON.")
        if not isinstance(body, dict):
            raise ApiError("Bad JSON.")
        return body

    def session_token(self):
        c = SimpleCookie(self.headers.get("Cookie") or "")
        return c["session"].value if "session" in c else None

    def is_staff(self):
        tok = self.session_token()
        with LOCK:
            exp = SESSIONS.get(tok)
            if exp and exp > time.time():
                return True
            SESSIONS.pop(tok, None)
        return False

    def require_staff(self):
        if not self.is_staff():
            raise ApiError("PIN required.", 401)

    #routing
    def do_GET(self):
        self.route(self.get)

    def do_POST(self):
        self.route(self.post)

    def route(self, fn):
        try:
            fn(urlparse(self.path))
        except ApiError as e:
            self.send_json({"error": e.msg}, e.code)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:                   #keep the server alive whatever happens
            import traceback
            print("  error while handling", self.path)
            traceback.print_exc()
            try:
                self.send_json({"error": "Server error."}, 500)
            except OSError:
                pass

    def get(self, u):
        p = u.path
        if p == "/":
            return self._send(302, b"", "text/plain", [("Location", "/staff")])
        if p in PAGES:
            return self.send_file(os.path.join(BASE_DIR, PAGES[p]), "text/html; charset=utf-8")
        if p.startswith("/images/"):
            name = os.path.basename(unquote(p))
            ext = os.path.splitext(name)[1].lower()
            types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
            if ext not in types:
                raise ApiError("Not found.", 404)
            return self.send_file(os.path.join(IMG_DIR, name), types[ext])
        if p == "/api/menu":
            with LOCK:
                return self.send_json({"menu": [m for m in MENU if m["available"]], "tables": TABLES, "version": MENU_VERSION})
        if p == "/api/menu-all":                         #staff: includes hidden dishes
            self.require_staff()
            with LOCK:
                return self.send_json({"menu": MENU, "version": MENU_VERSION})
        if p == "/api/me":
            return self.send_json({"staff": self.is_staff()})
        if p == "/api/order-status":                     #public: lets a customer follow their own order
            try:
                oid = int(parse_qs(u.query).get("id", [""])[0])
            except ValueError:
                raise ApiError("Bad order number.")
            with LOCK:
                o = find_order(oid)
                return self.send_json({"status": o["status"], "paid": o["payment"] is not None})
        if p == "/api/data":
            self.require_staff()
            with LOCK:
                return self.send_json({"orders": DATA["orders"], "expenses": DATA["expenses"], "menuVersion": MENU_VERSION})
        if p == "/api/info":
            self.require_staff()
            return self.send_json({"ip": lan_ip(), "port": PORT, "tables": TABLES})
        raise ApiError("Not found.", 404)

    def post(self, u):
        p = u.path
        body = self.read_json()
        if p == "/api/login":
            return self.login(body)
        if p == "/api/logout":
            with LOCK:
                SESSIONS.pop(self.session_token(), None)
            return self.send_json({"ok": True}, extra=[("Set-Cookie", "session=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict")])
        if p == "/api/customer-order":
            return self.customer_order(body)
        self.require_staff()
        with LOCK:
            if p == "/api/orders":
                items, amount = build_items(body.get("items"))
                o = {"id": next_id(DATA["orders"]), "table": parse_table(body.get("table")), "date": today(),
                     "time": now_time(), "amount": amount, "payment": parse_payment(body.get("payment")),
                     "status": "Served", "source": "staff", "items": items, "note": ""}
                DATA["orders"].append(o)
                save_data()
                return self.send_json({"order": o})
            if p == "/api/orders/status":
                o = find_order(body.get("id"))
                if body.get("status") not in STATUSES:
                    raise ApiError("Unknown status.")
                if o["payment"] is not None:
                    raise ApiError("This order is already paid.")
                o["status"] = body["status"]
                save_data()
                return self.send_json({"order": o})
            if p == "/api/orders/pay":
                o = find_order(body.get("id"))
                if o["payment"] is not None:
                    raise ApiError("This order is already paid.")
                if o["status"] == "Cancelled":
                    raise ApiError("This order was cancelled.")
                o["payment"] = parse_payment(body.get("payment"))
                o["paid_date"], o["paid_time"] = today(), now_time()
                if o["status"] in ("New", "Preparing"):
                    o["status"] = "Served"
                save_data()
                return self.send_json({"order": o})
            if p == "/api/menu/save":
                mid = body.get("id")
                if mid is None:
                    if len(MENU) >= 200:
                        raise ApiError("The menu is full (200 dishes).")
                    item = clean_menu_item(body)
                    item["id"] = next_id(MENU)
                    MENU.append(item)
                else:
                    item = find_menu_item(mid)
                    item.update(clean_menu_item(body, ignore_id=item["id"]))
                save_menu()
                return self.send_json({"item": item})
            if p == "/api/menu/delete":
                MENU.remove(find_menu_item(body.get("id")))
                save_menu()
                return self.send_json({"ok": True})
            if p == "/api/expenses":
                amount = body.get("amount")
                if not isinstance(amount, (int, float)) or isinstance(amount, bool) or not 0 < amount <= 1_000_000:
                    raise ApiError("Enter an amount greater than 0.")
                desc = str(body.get("description") or "").strip()[:100] or "General expense"
                e = {"id": next_id(DATA["expenses"]), "date": today(), "time": now_time(),
                     "amount": round(float(amount), 2), "description": desc}
                DATA["expenses"].append(e)
                save_data()
                return self.send_json({"expense": e})
        raise ApiError("Not found.", 404)

    #actions
    def login(self, body):
        ip, now = self.ip(), time.time()
        with LOCK:
            f = LOGIN_FAILS.setdefault(ip, {"n": 0, "until": 0})
            if f["until"] > now:
                raise ApiError(f"Too many wrong PINs. Try again in {int(f['until'] - now) + 1} seconds.", 429)
            if hmac.compare_digest(str(body.get("pin", "")).encode(), CONFIG["pin"].encode()):
                f["n"] = 0
                tok = secrets.token_urlsafe(32)
                SESSIONS[tok] = now + SESSION_SECONDS
                cookie = f"session={tok}; Path=/; Max-Age={SESSION_SECONDS}; HttpOnly; SameSite=Strict"
                return self.send_json({"ok": True}, extra=[("Set-Cookie", cookie)])
            f["n"] += 1
            if f["n"] >= 5:
                f["n"], f["until"] = 0, now + 60
            raise ApiError("Wrong PIN.", 401)

    def customer_order(self, body):
        ip, now = self.ip(), time.time()
        with LOCK:
            recent = [t for t in ORDER_TIMES.get(ip, []) if now - t < 600]
            if len(recent) >= 6:
                raise ApiError("Too many orders from this phone. Please ask a staff member.", 429)
            waiting = sum(1 for o in DATA["orders"] if o["source"] == "customer" and o["payment"] is None and o["status"] != "Cancelled")
            if waiting >= 100:
                raise ApiError("The kitchen is very busy. Please ask a staff member.", 429)
            items, amount = build_items(body.get("items"))
            o = {"id": next_id(DATA["orders"]), "table": parse_table(body.get("table")), "date": today(),
                 "time": now_time(), "amount": amount, "payment": None, "status": "New", "source": "customer",
                 "items": items, "note": str(body.get("note") or "").strip()[:100]}
            DATA["orders"].append(o)
            save_data()
            recent.append(now)
            ORDER_TIMES[ip] = recent
        self.send_json({"id": o["id"], "amount": amount, "table": o["table"]})


#start
CONFIG = load_config()
DATA = load_data()
load_menu()
PORT = CONFIG["port"]


def main():
    global PORT
    if "--sample" in sys.argv:
        add_sample_data()
    server = None
    for port in range(CONFIG["port"], CONFIG["port"] + 20):
        try:
            server = ThreadingHTTPServer(("0.0.0.0", port), Handler)   # reachable from other devices on the Wi-Fi
            PORT = port
            break
        except OSError:
            continue
    if server is None:
        sys.exit("No free port found.")
    server.daemon_threads = True
    ip = lan_ip()
    print("Cơm Nhà server is running.")
    print(f"  Staff page (this computer):   http://localhost:{PORT}/staff")
    print(f"  Staff page (other devices):   http://{ip}:{PORT}/staff")
    print(f"  Customer page, e.g. table 5:  http://{ip}:{PORT}/order?table=5")
    print("  Print the QR codes from the 'QR codes' tab of the staff page.")
    print("  If phones cannot connect, allow Python through the firewall and check they use the shop Wi-Fi.")
    print("  Press Ctrl+C to stop.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(f"http://localhost:{PORT}/staff")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
