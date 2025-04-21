# standard imports
import os
#import locale
from datetime import date, datetime

# external imports
from flask import Flask, request, render_template, g, redirect
from cryptography.fernet import Fernet

# local imports
from transaction import Transaction
from collections import defaultdict

KEY = b'ZfTpJ-ExWHiDFA_BNxi1kLKv97u_DLlE6fGLwqD1OXQ='
f = Fernet(KEY)
USERS = {}
USER_SECRETS = {}
USER = "JOJO"
u_list = []
#locale.setlocale(locale.LC_ALL, "en_US")

app = Flask(__name__)

entities = set()
descriptions = set()

@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

@app.route("/add_transaction", methods=["GET"])
def add_transaction():
    ents = [e.upper() for e in entities]
    ents.sort()

    return render_template("transaction.html", ents=ents, m=date.today().month, d=date.today().day, y=date.today().year)

@app.route("/add_transaction", methods=["POST"])
def process_transaction():
    u_entities  = request.form.getlist("vendor[]")
    dates       = request.form.getlist("date[]")
    total_prices= request.form.getlist("total_price[]")
    categories  = request.form.getlist("category[]")
    for i in range(len(dates)):
        add_expense(dates[i], u_entities[i], total_prices[i], categories[i])
    save_all_info()
    return render_template("receipt.html",
                           transactions=u_list,
                           success=True)

@app.route("/receipts", methods=["GET"])
def view_receipts():
    return render_template("receipt.html", 
                           transactions=u_list,
                           success=False)

@app.route("/analytics", methods=["GET"])
def analytics():
    if not u_list:
        return render_template("analytics.html", no_data=True)

    # ----- totals -----
    total_spending = sum(t.net for t in u_list)

    # ----- by category -----
    category_spending = defaultdict(float)
    for t in u_list:
        category_spending[t.category] += t.net

    # ----- per‑month sums & counts -----
    monthly_spending = defaultdict(float)
    monthly_counts   = defaultdict(int)
    for t in u_list:
        key = t.date.strftime("%Y-%m")
        monthly_spending[key] += t.net
        monthly_counts[key]   += 1                       # NEW

    sorted_months   = sorted(monthly_spending.keys())
    monthly_vals    = [monthly_spending[m] for m in sorted_months]
    monthly_txn_cts = [monthly_counts[m]   for m in sorted_months]  # NEW

    # ----- top vendors -----
    vendor_spending = defaultdict(float)
    for t in u_list:
        vendor_spending[t.vendor] += t.net
    top_vendors = sorted(vendor_spending.items(), key=lambda x: x[1], reverse=True)[:5]

    return render_template("analytics.html",
                           no_data=False,
                           total_spending=total_spending,
                           category_spending=dict(category_spending),
                           sorted_months=sorted_months,
                           monthly_spending_list=monthly_vals,
                           monthly_counts_list=monthly_txn_cts,      # NEW
                           top_vendors=top_vendors)

"""
File IO Functions

"""
def extract_all_info():
    with open(os.path.join("data/", "logins.txt"), "r", encoding="utf-8") as access_logins:
        lines = access_logins.readlines()
        for line in lines:
            line = f.decrypt(line.strip().encode()).decode()
            u = line[:line.index(",")]
            p = line[line.index(",") + 1 : line.rindex(",")]
            s = line[line.rindex(",") + 1:]
            USERS[u] = p
            USER_SECRETS[u] = s
        access_logins.close()

    with open(os.path.join("data/", "entities.txt"), "r", encoding="utf-8") as access_entities:
        lines = access_entities.readlines()
        for line in lines:
            entities.add(f.decrypt(line.strip().encode()).decode())

    with open(os.path.join("data/", USER_SECRETS[USER]), "r", encoding="utf-8") as u_file:
        u_info = u_file.readlines()
        if len(u_info) >= 1:
            u_stats = f.decrypt(u_info[0].strip().encode()).decode()
            parse_file(u_info[1:])
            u_entries = int(u_stats[:u_stats.index(",")])
            u_amount = float(u_stats[u_stats.index(",") + 1:])
        else:
            u_entries = 0
            u_amount = 0
        #print("WELCOME", USER, "YOU HAVE", u_entries, "TRANSACTIONS ENTERED AND A BALANCE OF", locale.currency(u_amount))
        u_file.close()

def adjust_vendor(string):
    string = string.upper()
    updated = ""
    for e in string:
        if e == "&":
            updated += "AND"
        elif e == "," or e == "'" or e == ".":
            pass
        else:
            updated += e

    return updated


def save_all_info():
    with open(os.path.join("data/", "logins.txt"), "w", encoding="utf-8") as save_logins:
        for u, p in USERS.items():
            login_str = u + "," + p + "," + USER_SECRETS[u]
            save_logins.write(encrypt_to_file(login_str))
        save_logins.close()

    with open(os.path.join("data/", USER_SECRETS[USER]), "w", encoding="utf-8") as u_file:
        total = 0
        for t in u_list:
            total += t.net
        u_file.write(encrypt_to_file(f"{len(u_list)},{total}"))
        for item in u_list:
            u_file.write(encrypt_to_file(item.csv()))
        u_file.close()

    with open(os.path.join("data/", "entities.txt"), "w", encoding="utf-8") as save_entities:
        for e in entities:
            save_entities.write(encrypt_to_file(e))

def parse_file(user_list):
    for line in user_list:
        fields = f.decrypt(line.strip().encode()).decode().split(",")
        net,vendor,yyyy,mm,dd = fields[:5]
        cat = fields[5] if len(fields)==6 else "Uncategorized"
        u_list.append(Transaction(float(net),vendor,
                                  date(int(yyyy),int(mm),int(dd)),cat))
def encrypt_to_file(text):
    return f.encrypt((text.encode())).decode() + "\n"

def add_expense(date, vendor, money, category):
    vendor = adjust_vendor(vendor.strip())
    entities.add(vendor)
    u_list.append(
        Transaction(float(money),
                    vendor,
                    datetime.strptime(date,"%m/%d/%y").date(),
                    category.strip() or "Uncategorized")
    )

if __name__ == "__main__":
    extract_all_info()
    app.run(host='0.0.0.0', port=8080, debug=False)

