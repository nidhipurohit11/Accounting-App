# -*- coding: utf-8 -*-
# Copyright (c) 2021, Nidhi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, getdate, flt
from accounting_app.accounting_app.general_ledger import make_gl_entries, make_reverse_gl_entry

class SalesInvoice(Document):
    def validate(self):
        self.check_date()
        self.check_total_amount()
        self.check_item_quantity_and_amount()
        self.add_total_amount()

    def check_date(self):
        #Posting date should not be a Past Date
        date = getdate()
        if getdate(self.posting_date) < date :
            frappe.throw("Posting date should be greater than or equal to today's date")
            
    def check_total_amount(self):
        #Total amount should be greater than zero
        if self.total_amount <= 0 :
            frappe.throw("Total Amount should be greater than zero")

    def check_item_quantity_and_amount(self) :
        #Item quantity in item table should be greater than zero
        for i in self.items:
            if i.quantity <= 0 :
                frappe.throw("Item Quantity should be greater than zero")
            #Item's amount in item table should be sum of each item's rate * qty
            i.rate = frappe.db.get_value("Item", i.item, "standard_selling_rate")
            i.amount = flt(i.quantity * i.rate)
            #i.qty = flt(i.quantity, i.precision("quantity"))
            #i.amount = i.rate * i.qty

    def add_total_amount(self):
        #Total qty and total amount should be sum of all items qty and amount from item table
        self.total_amount, self.total_qty = 0, 0
        for i in self.items:
            self.total_qty += i.quantity
            self.total_amount += i.amount

    def on_submit(self):
        self.make_gl_entry()
        self.check_debit_credit()
        
    def on_cancel(self):
        self.ignore_linked_doctypes = ('GL Entry')
        make_reverse_gl_entry(voucher_type = self.doctype, voucher_number = self.name)

    def make_gl_entry(self):
        gl_entry = [];
        gl_entry.append({
            "posting_date": self.get("posting_date"),
            "account": self.get("debit_to"),
            "party": self.get("party"),
            "voucher_number": self.get("name"),
            "voucher_type": "Sales Invoice",
            "debit_amount": self.get("total_amount"),
            "credit_amount": 0.00,
            "due_date": self.get("payment_due_date")
        })
        gl_entry.append({
            "posting_date": self.get("posting_date"),
            "account": self.get("income_account"),
            "party": self.get("party"),
            "voucher_number": self.get("name"),
            "voucher_type": "Sales Invoice",
            "debit_amount": 0.00,
            "credit_amount": self.get("total_amount"),
            "due_date": self.get("payment_due_date")
        })

        if gl_entry:
            make_gl_entries(gl_entry)

    def check_debit_credit(self):
        gl_entries = frappe.get_all('GL Entry', filters={"voucher_type": "Sales Invoice", "voucher_number": self.name}, fields=["*"])

        if gl_entries[0].get("debit_amount") == gl_entries[1].get("credit_amount") :
            frappe.msgprint("Credited and debited amount are same")