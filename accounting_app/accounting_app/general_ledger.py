from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

def make_gl_entries(gl_entry):
    for gl in gl_entry:
        gl.update({"doctype": "GL Entry"});
        doc = frappe.get_doc(gl);
        print(doc.account)
        doc.insert();
        doc.submit();

def make_reverse_gl_entry(voucher_type, voucher_number):
    gl_entries = frappe.get_all('GL Entry', filters={"voucher_type": voucher_type, "voucher_number": voucher_number}, fields=["*"])
    print(gl_entries)

    if gl_entries:
        set_as_cancel(gl_entries[0].voucher_type, gl_entries[0].voucher_number)

        for entry in gl_entries:
            debit = entry.get("debit_amount",0)
            credit = entry.get("credit_amount",0)
            entry["name"] = None
            entry["debit_amount"] = credit
            entry["credit_amount"] = debit
            entry["remarks"] = "On cancellation of " + entry.get("voucher_number")
            entry["is_cancelled"] = 1

            if entry["debit_amount"] or entry["credit_amount"]:
                make_entry(entry)

def set_as_cancel(voucher_type, voucher_number):
    frappe.db.sql(""" UPDATE `tabGL Entry` SET is_cancelled=1
        WHERE voucher_type=%s and voucher_number=%s and is_cancelled=0""", (voucher_type, voucher_number))

def make_entry(entry):
    print(entry)
    gl_entry = frappe.new_doc("GL Entry")
    gl_entry.update(entry)
    gl_entry.insert()
    gl_entry.submit()