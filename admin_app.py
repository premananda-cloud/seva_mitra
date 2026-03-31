"""
admin_app.py
============
KOISK Admin — desktop app for non-developer admins.
Requires only the Python standard library + requests.

    pip install requests
    python admin_app.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
TOKEN    = None
ROLE     = None
MY_ID    = None


# ─── Helpers ──────────────────────────────────────────────────────────────────

def api(method, path, **kwargs):
    headers = {}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    try:
        r = requests.request(method, BASE_URL + path, headers=headers, timeout=10, **kwargs)
        return r
    except requests.ConnectionError:
        messagebox.showerror("Connection Error", "Cannot reach the API.\nMake sure the server is running.")
        return None


def fmt_date(s):
    if not s:
        return "—"
    try:
        return datetime.fromisoformat(s.replace("Z", "")).strftime("%d %b %Y  %H:%M")
    except Exception:
        return s


def lbl(parent, text, **kw):
    return tk.Label(parent, text=text, bg="#f4f4f4", **kw)


# ─── Login ────────────────────────────────────────────────────────────────────

class LoginWindow:
    def __init__(self, root):
        self.root = root
        root.title("KOISK Admin — Login")
        root.resizable(False, False)
        root.configure(bg="#f4f4f4")

        f = tk.Frame(root, bg="#f4f4f4", padx=40, pady=30)
        f.pack()

        tk.Label(f, text="KOISK Admin Panel", font=("Helvetica", 16, "bold"),
                 bg="#f4f4f4").grid(row=0, column=0, columnspan=2, pady=(0, 20))

        lbl(f, "Username:").grid(row=1, column=0, sticky="e", pady=6)
        self.u = tk.Entry(f, width=26)
        self.u.grid(row=1, column=1, pady=6, padx=(8, 0))

        lbl(f, "Password:").grid(row=2, column=0, sticky="e", pady=6)
        self.p = tk.Entry(f, width=26, show="*")
        self.p.grid(row=2, column=1, pady=6, padx=(8, 0))
        self.p.bind("<Return>", lambda e: self.do_login())

        self.err = tk.Label(f, text="", fg="red", bg="#f4f4f4", font=("Helvetica", 10))
        self.err.grid(row=3, column=0, columnspan=2)

        self.btn = tk.Button(f, text="Sign In", width=20,
                             bg="#2563eb", fg="white", font=("Helvetica", 11, "bold"),
                             relief="flat", cursor="hand2", command=self.do_login)
        self.btn.grid(row=4, column=0, columnspan=2, pady=(16, 0))
        self.u.focus()

    def do_login(self):
        global TOKEN, ROLE, MY_ID
        user = self.u.get().strip()
        pw   = self.p.get()
        if not user or not pw:
            self.err.config(text="Enter username and password.")
            return
        self.btn.config(state="disabled", text="Signing in…")
        self.err.config(text="")

        def run():
            global TOKEN, ROLE, MY_ID
            r = api("POST", "/admin/login", data={"username": user, "password": pw})
            if r is None:
                self.btn.config(state="normal", text="Sign In")
                return
            if r.status_code == 200:
                d = r.json()
                TOKEN = d["access_token"]
                ROLE  = d.get("role", "")
                MY_ID = d.get("admin_id")
                self.root.after(0, self.open_main)
            else:
                msg = r.json().get("detail", "Login failed.")
                self.root.after(0, lambda: self.err.config(text=msg))
                self.root.after(0, lambda: self.btn.config(state="normal", text="Sign In"))

        threading.Thread(target=run, daemon=True).start()

    def open_main(self):
        self.root.destroy()
        r = tk.Tk()
        MainWindow(r)
        r.mainloop()


# ─── Main window ──────────────────────────────────────────────────────────────

class MainWindow:
    def __init__(self, root):
        self.root = root
        root.title("KOISK Admin Panel")
        root.geometry("980x640")
        root.configure(bg="#f4f4f4")

        bar = tk.Frame(root, bg="#1e3a5f", height=46)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="  KOISK Admin Panel", font=("Helvetica", 13, "bold"),
                 bg="#1e3a5f", fg="white").pack(side="left", padx=8)
        tk.Label(bar, text=f"Logged in as: {ROLE}", font=("Helvetica", 10),
                 bg="#1e3a5f", fg="#93c5fd").pack(side="right", padx=16)

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.build_health_tab()
        self.build_requests_tab()
        self.build_payments_tab()
        self.build_users_tab()
        self.build_config_tab()

        self.load_health()

    # ── Health ────────────────────────────────────────────────────────────────

    def build_health_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="  Health  ")
        self.health_text = tk.Text(f, height=14, font=("Courier", 11),
                                   bg="#1e1e1e", fg="#d4d4d4", relief="flat",
                                   padx=12, pady=12, state="disabled")
        self.health_text.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Button(f, text="↺  Refresh", command=self.load_health,
                  bg="#2563eb", fg="white", relief="flat", cursor="hand2",
                  padx=14, pady=4).pack(pady=(0, 10))

    def load_health(self):
        def run():
            r = api("GET", "/health")
            if r and r.ok:
                d = r.json()
                lines = [
                    f"  Status      : {d.get('status','—').upper()}",
                    f"  Timestamp   : {fmt_date(d.get('timestamp'))}",
                    f"  Mock Payment: {d.get('mock_payment','—')}",
                    f"  Departments : {', '.join(d.get('departments', []))}",
                ]
            else:
                lines = ["  Could not reach /health"]
            self.root.after(0, lambda: self._set_text(self.health_text, "\n".join(lines)))
        threading.Thread(target=run, daemon=True).start()

    # ── Requests ──────────────────────────────────────────────────────────────

    def build_requests_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="  Service Requests  ")

        fb = tk.Frame(f, bg="#f4f4f4")
        fb.pack(fill="x", padx=10, pady=8)
        lbl(fb, "Dept:").pack(side="left")
        self.req_dept = ttk.Combobox(fb, values=["","electricity","water","gas","municipal"],
                                     width=12, state="readonly")
        self.req_dept.set("")
        self.req_dept.pack(side="left", padx=(4, 12))
        lbl(fb, "Status:").pack(side="left")
        self.req_status = ttk.Combobox(
            fb, values=["","PENDING","IN_PROGRESS","DELIVERED","FAILED","CANCELLED"],
            width=14, state="readonly")
        self.req_status.set("")
        self.req_status.pack(side="left", padx=(4, 12))
        tk.Button(fb, text="Load", command=self.load_requests,
                  bg="#2563eb", fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=2).pack(side="left")
        self.req_count = lbl(fb, "")
        self.req_count.pack(side="right", padx=8)

        cols = ("ID", "Department", "Status", "Created")
        self.req_tree = ttk.Treeview(f, columns=cols, show="headings", height=16)
        for col, w in zip(cols, (280, 110, 120, 160)):
            self.req_tree.heading(col, text=col)
            self.req_tree.column(col, width=w, anchor="w")
        self.req_tree.pack(fill="both", expand=True, padx=10)

        tk.Button(f, text="Update Status on Selected", command=self.update_request_status,
                  bg="#059669", fg="white", relief="flat", cursor="hand2",
                  padx=14, pady=4).pack(pady=8)

    def load_requests(self):
        url = "/admin/requests?limit=100"
        d, s = self.req_dept.get(), self.req_status.get()
        if d: url += f"&department={d}"
        if s: url += f"&status={s}"

        def run():
            r = api("GET", url)
            if r and r.ok:
                data = r.json()
                rows = data.get("requests", [])
                def fill():
                    self.req_tree.delete(*self.req_tree.get_children())
                    for row in rows:
                        self.req_tree.insert("", "end", values=(
                            row.get("service_request_id") or row.get("id","—"),
                            row.get("department","—"),
                            row.get("status","—"),
                            fmt_date(row.get("created_at")),
                        ))
                    self.req_count.config(text=f"{len(rows)} of {data.get('total',0)} shown")
                self.root.after(0, fill)
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Failed to load requests."))
        threading.Thread(target=run, daemon=True).start()

    def update_request_status(self):
        sel = self.req_tree.selection()
        if not sel:
            messagebox.showinfo("Select a row", "Click a request row first.")
            return
        req_id = self.req_tree.item(sel[0])["values"][0]
        new_s  = simpledialog.askstring(
            "Update Status",
            f"Request: {req_id}\n\nNew status:\nPENDING / IN_PROGRESS / DELIVERED / FAILED / CANCELLED",
            parent=self.root,
        )
        if not new_s:
            return

        def run():
            r = api("PATCH", f"/admin/requests/{req_id}/status",
                    json={"status": new_s.strip().upper()})
            if r and r.ok:
                self.root.after(0, lambda: messagebox.showinfo("Done", "Status updated."))
                self.root.after(0, self.load_requests)
            else:
                detail = r.json().get("detail","Failed") if r else "No response"
                self.root.after(0, lambda: messagebox.showerror("Error", detail))
        threading.Thread(target=run, daemon=True).start()

    # ── Payments ──────────────────────────────────────────────────────────────

    def build_payments_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="  Payments  ")

        fb = tk.Frame(f, bg="#f4f4f4")
        fb.pack(fill="x", padx=10, pady=8)
        lbl(fb, "Dept:").pack(side="left")
        self.pay_dept = ttk.Combobox(fb, values=["","electricity","water","gas","municipal"],
                                     width=12, state="readonly")
        self.pay_dept.set("")
        self.pay_dept.pack(side="left", padx=(4, 12))
        lbl(fb, "Status:").pack(side="left")
        self.pay_status = ttk.Combobox(fb, values=["","captured","pending","failed","refunded"],
                                       width=12, state="readonly")
        self.pay_status.set("")
        self.pay_status.pack(side="left", padx=(4, 12))
        tk.Button(fb, text="Load", command=self.load_payments,
                  bg="#2563eb", fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=2).pack(side="left")
        self.pay_count = lbl(fb, "")
        self.pay_count.pack(side="right", padx=8)

        cols = ("ID","Dept","Amount (₹)","Gateway","Method","Status","Paid At")
        self.pay_tree = ttk.Treeview(f, columns=cols, show="headings", height=16)
        for col, w in zip(cols, (60,100,90,90,90,90,160)):
            self.pay_tree.heading(col, text=col)
            self.pay_tree.column(col, width=w, anchor="w")
        self.pay_tree.pack(fill="both", expand=True, padx=10, pady=(0,10))

    def load_payments(self):
        url = "/admin/payments?limit=100"
        d, s = self.pay_dept.get(), self.pay_status.get()
        if d: url += f"&department={d}"
        if s: url += f"&status={s}"

        def run():
            r = api("GET", url)
            if r and r.ok:
                rows = r.json().get("payments", [])
                def fill():
                    self.pay_tree.delete(*self.pay_tree.get_children())
                    for p in rows:
                        self.pay_tree.insert("", "end", values=(
                            p.get("id","—"), p.get("dept","—"),
                            f"{float(p.get('amount',0)):.2f}",
                            p.get("gateway","—"), p.get("method","—"),
                            p.get("status","—"),
                            fmt_date(p.get("paidAt") or p.get("createdAt")),
                        ))
                    self.pay_count.config(text=f"{len(rows)} shown")
                self.root.after(0, fill)
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Failed to load payments."))
        threading.Thread(target=run, daemon=True).start()

    # ── Admin Users ───────────────────────────────────────────────────────────

    def build_users_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="  Admin Users  ")

        bb = tk.Frame(f, bg="#f4f4f4")
        bb.pack(fill="x", padx=10, pady=8)

        tk.Button(bb, text="↺  Refresh", command=self.load_users,
                  bg="#2563eb", fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=2).pack(side="left", padx=(0,8))

        if ROLE == "super_admin":
            tk.Button(bb, text="+ Register New Admin", command=self.open_register,
                      bg="#059669", fg="white", relief="flat", cursor="hand2",
                      padx=12, pady=2).pack(side="left", padx=(0,8))

        tk.Button(bb, text="Change My Password", command=self.open_change_own_password,
                  bg="#d97706", fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=2).pack(side="left", padx=(0,8))

        if ROLE == "super_admin":
            tk.Button(bb, text="Change Selected Password", command=self.open_change_selected_password,
                      bg="#d97706", fg="white", relief="flat", cursor="hand2",
                      padx=12, pady=2).pack(side="left", padx=(0,8))
            tk.Button(bb, text="Deactivate", command=lambda: self.toggle_active(False),
                      bg="#6b7280", fg="white", relief="flat", cursor="hand2",
                      padx=12, pady=2).pack(side="left", padx=(0,4))
            tk.Button(bb, text="Activate", command=lambda: self.toggle_active(True),
                      bg="#059669", fg="white", relief="flat", cursor="hand2",
                      padx=12, pady=2).pack(side="left", padx=(0,4))
            tk.Button(bb, text="Delete", command=self.delete_user,
                      bg="#dc2626", fg="white", relief="flat", cursor="hand2",
                      padx=12, pady=2).pack(side="left")

        self.users_count = lbl(bb, "")
        self.users_count.pack(side="right", padx=8)

        cols = ("ID","Username","Full Name","Email","Role","Department","Active","Last Login")
        self.users_tree = ttk.Treeview(f, columns=cols, show="headings", height=18)
        for col, w in zip(cols, (40,110,160,200,120,110,60,160)):
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=w, anchor="w")

        sb = ttk.Scrollbar(f, orient="vertical", command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=sb.set)
        self.users_tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=(0,10))
        sb.pack(side="left", fill="y", pady=(0,10))

        self.load_users()

    def load_users(self):
        def run():
            r = api("GET", "/admin/users")
            if r and r.ok:
                rows = r.json().get("admins", [])
                def fill():
                    self.users_tree.delete(*self.users_tree.get_children())
                    for a in rows:
                        self.users_tree.insert("", "end", iid=str(a["id"]), values=(
                            a["id"], a["username"], a["full_name"], a["email"],
                            a["role"], a.get("department") or "all",
                            "Yes" if a["is_active"] else "No",
                            fmt_date(a.get("last_login")),
                        ))
                    self.users_count.config(text=f"{len(rows)} admin(s)")
                self.root.after(0, fill)
            elif r:
                self.root.after(0, lambda: messagebox.showerror("Error", r.json().get("detail","Failed")))
        threading.Thread(target=run, daemon=True).start()

    def _selected_user_id(self):
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showinfo("Select a row", "Click an admin row first.")
            return None
        return int(sel[0])

    def open_register(self):
        RegisterDialog(self.root, on_success=self.load_users)

    def open_change_own_password(self):
        ChangePasswordDialog(self.root, target_id=MY_ID, my_id=MY_ID, my_role=ROLE)

    def open_change_selected_password(self):
        uid = self._selected_user_id()
        if uid is not None:
            ChangePasswordDialog(self.root, target_id=uid, my_id=MY_ID, my_role=ROLE)

    def toggle_active(self, activate: bool):
        uid = self._selected_user_id()
        if uid is None:
            return
        action = "activate" if activate else "deactivate"
        if not messagebox.askyesno("Confirm", f"Are you sure you want to {action} this admin?"):
            return

        def run():
            r = api("PATCH", f"/admin/users/{uid}/{action}")
            if r and r.ok:
                msg = r.json().get("message","Done")
                self.root.after(0, lambda: messagebox.showinfo("Done", msg))
                self.root.after(0, self.load_users)
            else:
                detail = r.json().get("detail","Failed") if r else "No response"
                self.root.after(0, lambda: messagebox.showerror("Error", detail))
        threading.Thread(target=run, daemon=True).start()

    def delete_user(self):
        uid = self._selected_user_id()
        if uid is None:
            return
        if not messagebox.askyesno("Confirm Delete",
                                    "Permanently delete this admin?\nThis cannot be undone."):
            return

        def run():
            r = api("DELETE", f"/admin/users/{uid}")
            if r and r.ok:
                self.root.after(0, lambda: messagebox.showinfo("Deleted","Admin deleted."))
                self.root.after(0, self.load_users)
            else:
                detail = r.json().get("detail","Failed") if r else "No response"
                self.root.after(0, lambda: messagebox.showerror("Error", detail))
        threading.Thread(target=run, daemon=True).start()

    # ── Config ────────────────────────────────────────────────────────────────

    def build_config_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="  Config  ")

        def field_row(parent, label, row, show=None):
            lbl(parent, f"{label}:", width=20, anchor="e").grid(row=row, column=0, pady=5, padx=(0,8))
            e = tk.Entry(parent, width=36, show=show or "")
            e.grid(row=row, column=1, pady=5, sticky="w")
            return e

        mg = tk.LabelFrame(f, text="  Merchant / Gateway Setup  ",
                           font=("Helvetica",10,"bold"), bg="#f4f4f4", padx=14, pady=10)
        mg.pack(fill="x", padx=14, pady=(14,8))

        lbl(mg, "Gateway:", width=20, anchor="e").grid(row=0, column=0, pady=5, padx=(0,8))
        self.cfg_gateway = ttk.Combobox(mg, values=["razorpay","portone","mock"],
                                        width=33, state="readonly")
        self.cfg_gateway.set("razorpay")
        self.cfg_gateway.grid(row=0, column=1, pady=5, sticky="w")

        self.cfg_mid    = field_row(mg, "Merchant ID",    1)
        self.cfg_chkey  = field_row(mg, "Channel Key",    2)
        self.cfg_apikey = field_row(mg, "API Key/Secret", 3, show="*")
        self.cfg_notes  = field_row(mg, "Notes",          4)

        tk.Button(mg, text="Save Merchant Config", command=self.save_merchant,
                  bg="#2563eb", fg="white", relief="flat", cursor="hand2",
                  padx=14, pady=4).grid(row=5, column=1, pady=(10,0), sticky="w")

        kg = tk.LabelFrame(f, text="  Kiosk Razorpay Keys  (super_admin only)  ",
                           font=("Helvetica",10,"bold"), bg="#f4f4f4", padx=14, pady=10)
        kg.pack(fill="x", padx=14, pady=8)

        lbl(kg, "Department:", width=20, anchor="e").grid(row=0, column=0, pady=5, padx=(0,8))
        self.ksk_dept = ttk.Combobox(kg, values=["global","electricity","water","municipal"],
                                     width=33, state="readonly")
        self.ksk_dept.set("global")
        self.ksk_dept.grid(row=0, column=1, pady=5, sticky="w")

        lbl(kg, "Mode:", width=20, anchor="e").grid(row=1, column=0, pady=5, padx=(0,8))
        self.ksk_mode = ttk.Combobox(kg, values=["test","live"], width=33, state="readonly")
        self.ksk_mode.set("test")
        self.ksk_mode.grid(row=1, column=1, pady=5, sticky="w")

        lbl(kg, "Key ID:", width=20, anchor="e").grid(row=2, column=0, pady=5, padx=(0,8))
        self.ksk_keyid = tk.Entry(kg, width=36)
        self.ksk_keyid.grid(row=2, column=1, pady=5, sticky="w")

        lbl(kg, "Key Secret:", width=20, anchor="e").grid(row=3, column=0, pady=5, padx=(0,8))
        self.ksk_secret = tk.Entry(kg, width=36, show="*")
        self.ksk_secret.grid(row=3, column=1, pady=5, sticky="w")

        self.ksk_active = tk.BooleanVar(value=True)
        tk.Checkbutton(kg, text="Active", variable=self.ksk_active,
                       bg="#f4f4f4", cursor="hand2").grid(row=4, column=1, sticky="w")
        tk.Button(kg, text="Save Kiosk Keys", command=self.save_kiosk,
                  bg="#2563eb", fg="white", relief="flat", cursor="hand2",
                  padx=14, pady=4).grid(row=5, column=1, pady=(10,0), sticky="w")

    def save_merchant(self):
        payload = {
            "gateway":     self.cfg_gateway.get(),
            "merchant_id": self.cfg_mid.get().strip(),
            "channel_key": self.cfg_chkey.get().strip() or None,
            "api_key":     self.cfg_apikey.get() or None,
            "notes":       self.cfg_notes.get().strip() or None,
        }
        if not payload["merchant_id"]:
            messagebox.showwarning("Required", "Merchant ID is required.")
            return

        def run():
            r = api("POST", "/admin/merchant/setup", json=payload)
            ok = r and r.ok
            msg = "Merchant config saved." if ok else (r.json().get("detail","Failed") if r else "No response")
            self.root.after(0, lambda: (messagebox.showinfo if ok else messagebox.showerror)("Result", msg))
        threading.Thread(target=run, daemon=True).start()

    def save_kiosk(self):
        payload = {
            "department":          self.ksk_dept.get(),
            "razorpay_mode":       self.ksk_mode.get(),
            "razorpay_key_id":     self.ksk_keyid.get().strip() or None,
            "razorpay_key_secret": self.ksk_secret.get() or None,
            "is_active":           self.ksk_active.get(),
        }

        def run():
            r = api("POST", "/admin/kiosk-config", json=payload)
            ok = r and r.ok
            msg = "Kiosk config saved." if ok else (r.json().get("detail","Failed") if r else "No response")
            self.root.after(0, lambda: (messagebox.showinfo if ok else messagebox.showerror)("Result", msg))
        threading.Thread(target=run, daemon=True).start()

    # ── Util ──────────────────────────────────────────────────────────────────

    def _set_text(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.config(state="disabled")


# ─── Register Dialog ──────────────────────────────────────────────────────────

class RegisterDialog(tk.Toplevel):
    def __init__(self, parent, on_success=None):
        super().__init__(parent)
        self.title("Register New Admin")
        self.resizable(False, False)
        self.configure(bg="#f4f4f4")
        self.on_success = on_success
        self.grab_set()

        f = tk.Frame(self, bg="#f4f4f4", padx=28, pady=20)
        f.pack()

        tk.Label(f, text="Register New Admin", font=("Helvetica",13,"bold"),
                 bg="#f4f4f4").grid(row=0, column=0, columnspan=2, pady=(0,16))

        def row(label, r, show=None):
            lbl(f, f"{label}:", width=16, anchor="e").grid(row=r, column=0, pady=5, padx=(0,8))
            e = tk.Entry(f, width=28, show=show or "")
            e.grid(row=r, column=1, pady=5, sticky="w")
            return e

        self.username  = row("Username",    1)
        self.full_name = row("Full Name",   2)
        self.email     = row("Email",       3)
        self.password  = row("Password",    4, show="*")
        self.confirm   = row("Confirm Pwd", 5, show="*")

        lbl(f, "Role:", width=16, anchor="e").grid(row=6, column=0, pady=5, padx=(0,8))
        self.role = ttk.Combobox(f, values=["department_admin","super_admin"], width=26, state="readonly")
        self.role.set("department_admin")
        self.role.grid(row=6, column=1, pady=5, sticky="w")
        self.role.bind("<<ComboboxSelected>>", self._on_role_change)

        lbl(f, "Department:", width=16, anchor="e").grid(row=7, column=0, pady=5, padx=(0,8))
        self.dept = ttk.Combobox(f, values=["electricity","water","gas","municipal"],
                                 width=26, state="readonly")
        self.dept.set("electricity")
        self.dept.grid(row=7, column=1, pady=5, sticky="w")

        self.err = tk.Label(f, text="", fg="red", bg="#f4f4f4", wraplength=280)
        self.err.grid(row=8, column=0, columnspan=2, pady=(4,0))

        self.btn = tk.Button(f, text="Register", bg="#2563eb", fg="white",
                             relief="flat", cursor="hand2", padx=18, pady=5,
                             command=self.submit)
        self.btn.grid(row=9, column=0, columnspan=2, pady=(12,0))

    def _on_role_change(self, _=None):
        if self.role.get() == "super_admin":
            self.dept.set("")
            self.dept.config(state="disabled")
        else:
            self.dept.config(state="readonly")
            self.dept.set("electricity")

    def submit(self):
        pw = self.password.get()
        if pw != self.confirm.get():
            self.err.config(text="Passwords do not match.")
            return
        if len(pw) < 8:
            self.err.config(text="Password must be at least 8 characters.")
            return
        role = self.role.get()
        dept = self.dept.get() if role == "department_admin" else None
        if role == "department_admin" and not dept:
            self.err.config(text="Select a department.")
            return
        payload = {
            "username":   self.username.get().strip(),
            "full_name":  self.full_name.get().strip(),
            "email":      self.email.get().strip(),
            "password":   pw,
            "role":       role,
            "department": dept,
        }
        if not all([payload["username"], payload["full_name"], payload["email"]]):
            self.err.config(text="All fields are required.")
            return

        self.btn.config(state="disabled", text="Registering…")
        self.err.config(text="")

        def run():
            r = api("POST", "/admin/register", json=payload)
            if r and r.status_code == 201:
                self.after(0, self.destroy)
                if self.on_success:
                    self.after(0, self.on_success)
                self.after(0, lambda: messagebox.showinfo("Done", f"Admin '{payload['username']}' created."))
            else:
                detail = r.json().get("detail","Failed") if r else "No response"
                self.after(0, lambda: self.err.config(text=detail))
                self.after(0, lambda: self.btn.config(state="normal", text="Register"))
        threading.Thread(target=run, daemon=True).start()


# ─── Change Password Dialog ───────────────────────────────────────────────────

class ChangePasswordDialog(tk.Toplevel):
    def __init__(self, parent, target_id, my_id, my_role):
        super().__init__(parent)
        self.title("Change Password")
        self.resizable(False, False)
        self.configure(bg="#f4f4f4")
        self.target_id = target_id
        self.is_own    = (target_id == my_id)
        self.grab_set()

        f = tk.Frame(self, bg="#f4f4f4", padx=28, pady=20)
        f.pack()

        tk.Label(f, text="Change Password", font=("Helvetica",13,"bold"),
                 bg="#f4f4f4").grid(row=0, column=0, columnspan=2, pady=(0,14))

        self.cur_entry = None
        if self.is_own:
            lbl(f, "Current Password:", width=18, anchor="e").grid(row=1, column=0, pady=5, padx=(0,8))
            self.cur_entry = tk.Entry(f, width=28, show="*")
            self.cur_entry.grid(row=1, column=1, pady=5, sticky="w")

        lbl(f, "New Password:", width=18, anchor="e").grid(row=2, column=0, pady=5, padx=(0,8))
        self.new_entry = tk.Entry(f, width=28, show="*")
        self.new_entry.grid(row=2, column=1, pady=5, sticky="w")

        lbl(f, "Confirm New:", width=18, anchor="e").grid(row=3, column=0, pady=5, padx=(0,8))
        self.conf_entry = tk.Entry(f, width=28, show="*")
        self.conf_entry.grid(row=3, column=1, pady=5, sticky="w")

        self.err = tk.Label(f, text="", fg="red", bg="#f4f4f4", wraplength=280)
        self.err.grid(row=4, column=0, columnspan=2, pady=(4,0))

        self.btn = tk.Button(f, text="Update Password", bg="#2563eb", fg="white",
                             relief="flat", cursor="hand2", padx=18, pady=5,
                             command=self.submit)
        self.btn.grid(row=5, column=0, columnspan=2, pady=(12,0))

    def submit(self):
        new  = self.new_entry.get()
        conf = self.conf_entry.get()
        if new != conf:
            self.err.config(text="Passwords do not match.")
            return
        if len(new) < 8:
            self.err.config(text="Password must be at least 8 characters.")
            return
        payload = {"new_password": new}
        if self.is_own and self.cur_entry:
            payload["current_password"] = self.cur_entry.get()

        self.btn.config(state="disabled", text="Updating…")
        self.err.config(text="")

        def run():
            r = api("PATCH", f"/admin/users/{self.target_id}/password", json=payload)
            if r and r.ok:
                self.after(0, self.destroy)
                self.after(0, lambda: messagebox.showinfo("Done","Password updated successfully."))
            else:
                detail = r.json().get("detail","Failed") if r else "No response"
                self.after(0, lambda: self.err.config(text=detail))
                self.after(0, lambda: self.btn.config(state="normal", text="Update Password"))
        threading.Thread(target=run, daemon=True).start()


# ─── Entry ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()
