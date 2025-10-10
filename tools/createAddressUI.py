#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import codecs
import sys
import pymssql
import tomllib
import tkinter as tk
from typing import Any
from pathlib import Path
from tkinter import ttk, messagebox, simpledialog


SCRIPT_DIR: Path = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH: Path = SCRIPT_DIR / "../server/config.toml"
USER_CONFIG_DIR: Path = Path.home() / ".wiffzack_additions"
USER_CONFIG_PATH: Path = USER_CONFIG_DIR / "config.toml"

config: dict[str, Any] = {}
try:
    with open(DEFAULT_CONFIG_PATH, "rb") as f:
        config = tomllib.load(f)
except FileNotFoundError:
    print(
        f"Default configuration file not found at {DEFAULT_CONFIG_PATH}. Exiting.")
    exit(1)  # Good to exit if default is missing too
except tomllib.TOMLDecodeError as e:
    print(
        f"Error decoding default configuration file {DEFAULT_CONFIG_PATH}: {e}. Exiting.")
    exit(1)

try:
    with open(USER_CONFIG_PATH, "rb") as f:
        config_user: dict[str, Any] = tomllib.load(f)
        # This is fine if client.toml replaces whole sections like [client]
        config |= config_user
except FileNotFoundError:
    print(
        f"Client config not found. Please create a '{USER_CONFIG_PATH}' file.")
    exit(1)
except tomllib.TOMLDecodeError as e:
    print(
        f"Error decoding user configuration file {USER_CONFIG_PATH}: {e}. Exiting.")
    exit(1)



class AddressManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Address Manager")
        self.root.geometry("900x600")

        # Set database connection parameters
        self.HOST = config["database"]["server"]
        self.USER = config["database"]["username"]
        self.PASSWORD = config["database"]["password"]
        self.DATABASE = config["database"]["database"]
        
        # Database connection
        self.db_conn = None
        
        # Create GUI elements
        self.create_widgets()
        
        # Connect to database
        self.connect_to_db()
        
        # Populate the address list on startup
        self.refresh_address_list()
    
    def create_widgets(self):
        # Main frame with two parts
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left frame for address list
        left_frame = ttk.LabelFrame(main_frame, text="Address List")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Search frame
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=2)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.search_entry.bind("<Return>", lambda e: self.search_address())
        
        ttk.Button(search_frame, text="Search", command=self.search_address).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text="Clear", command=self.clear_search).pack(side=tk.LEFT, padx=2)
        
        # Address list with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("ID", "Company", "First Name", "Last Name", "Street", "ZIP", "City")
        self.address_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        
        # Set column headings and widths
        self.address_tree.heading("ID", text="ID")
        self.address_tree.heading("Company", text="Company")
        self.address_tree.heading("First Name", text="First Name")
        self.address_tree.heading("Last Name", text="Last Name")
        self.address_tree.heading("Street", text="Street")
        self.address_tree.heading("ZIP", text="ZIP")
        self.address_tree.heading("City", text="City")
        
        self.address_tree.column("ID", width=50, anchor=tk.W)
        self.address_tree.column("Company", width=150, anchor=tk.W)
        self.address_tree.column("First Name", width=120, anchor=tk.W)
        self.address_tree.column("Last Name", width=120, anchor=tk.W)
        self.address_tree.column("Street", width=150, anchor=tk.W)
        self.address_tree.column("ZIP", width=70, anchor=tk.W)
        self.address_tree.column("City", width=120, anchor=tk.W)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.address_tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.address_tree.xview)
        self.address_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Place the treeview and scrollbars
        self.address_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click to edit
        self.address_tree.bind("<Double-1>", lambda e: self.edit_address())
        
        # Right frame for form
        self.right_frame = ttk.LabelFrame(main_frame, text="Address Details")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5, ipadx=5, ipady=5, expand=False)
        
        # Form fields
        form_frame = ttk.Frame(self.right_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Address ID (hidden)
        self.address_id = tk.StringVar()
        
        # Company
        ttk.Label(form_frame, text="Company:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.company_var = tk.StringVar()
        self.company_entry = ttk.Entry(form_frame, textvariable=self.company_var, width=30)
        self.company_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2)
        
        # First Name
        ttk.Label(form_frame, text="First Name:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.fname_var = tk.StringVar()
        self.fname_entry = ttk.Entry(form_frame, textvariable=self.fname_var, width=30)
        self.fname_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2)
        
        # Last Name
        ttk.Label(form_frame, text="Last Name:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.lname_var = tk.StringVar()
        self.lname_entry = ttk.Entry(form_frame, textvariable=self.lname_var, width=30)
        self.lname_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=2)
        
        # Street
        ttk.Label(form_frame, text="Street:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.street_var = tk.StringVar()
        self.street_entry = ttk.Entry(form_frame, textvariable=self.street_var, width=30)
        self.street_entry.grid(row=3, column=1, sticky=tk.W+tk.E, pady=2)
        
        # ZIP
        ttk.Label(form_frame, text="ZIP:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.zip_var = tk.StringVar()
        self.zip_entry = ttk.Entry(form_frame, textvariable=self.zip_var, width=30)
        self.zip_entry.grid(row=4, column=1, sticky=tk.W+tk.E, pady=2)
        
        # City
        ttk.Label(form_frame, text="City:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.city_var = tk.StringVar()
        self.city_entry = ttk.Entry(form_frame, textvariable=self.city_var, width=30)
        self.city_entry.grid(row=5, column=1, sticky=tk.W+tk.E, pady=2)
        
        # Form buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="New", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save", command=self.save_address).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Main buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Create New Address", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Selected", command=self.edit_address).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
    
    def connect_to_db(self):
        try:
            self.db_conn = pymssql.connect(host=self.HOST, user=self.USER, password=self.PASSWORD, database=self.DATABASE, tds_version=r"7.0")
            self.status_var.set("Connected to database")
        except Exception as e:
            messagebox.showerror("Database Connection Error", f"Failed to connect to database: {str(e)}")
            self.status_var.set("Database connection failed")
    
    def run_query(self, query):
        if self.db_conn is None:
            self.connect_to_db()
            if self.db_conn is None:
                return []
        
        try:
            cur = self.db_conn.cursor()
            cur.execute(query)
            
            try:
                return cur.fetchall()
            except pymssql.OperationalError:
                return []
        except Exception as e:
            messagebox.showerror("Query Error", f"Error executing query: {str(e)}")
            return []
    
    def commit(self):
        if self.db_conn:
            try:
                self.db_conn.commit()
                self.status_var.set("Changes committed to database")
                return True
            except Exception as e:
                messagebox.showerror("Commit Error", f"Error committing changes: {str(e)}")
                return False
        else:
            messagebox.showerror("Database Error", "No database connection")
            return False
    
    def rollback(self):
        if self.db_conn:
            try:
                self.db_conn.rollback()
                self.status_var.set("Changes rolled back")
            except Exception as e:
                messagebox.showerror("Rollback Error", f"Error rolling back changes: {str(e)}")
    
    def get_addresses(self, search_string=None):
        if search_string is None or search_string.strip() == "":
            query = """SELECT adresse_id, adresse_firma, adresse_vorname, adresse_nachname, 
                    adresse_strasse, adresse_plz, adresse_ort FROM adressen_basis 
                    ORDER BY adresse_firma, adresse_nachname"""
        else:
            # Sanitize the search string to prevent SQL injection
            search_string = search_string.replace("'", "''")
            
            query = """SELECT adresse_id, adresse_firma, adresse_vorname, adresse_nachname, 
                    adresse_strasse, adresse_plz, adresse_ort FROM adressen_basis 
                    WHERE 1=1
                    AND (adresse_firma LIKE '%%%s%%' 
                    OR adresse_vorname LIKE '%%%s%%'
                    OR adresse_nachname LIKE '%%%s%%') 
                    ORDER BY adresse_firma, adresse_nachname""" % (search_string, search_string, search_string)
        
        return self.run_query(query)
    
    def get_address(self, address_id):
        # Sanitize input to prevent SQL injection
        try:
            address_id = int(address_id)
        except ValueError:
            return None
        
        query = """SELECT adresse_id, adresse_firma, adresse_vorname, adresse_nachname, 
                adresse_strasse, adresse_plz, adresse_ort FROM adressen_basis 
                WHERE adresse_id = %s
                ORDER BY adresse_firma, adresse_nachname""" % (address_id,)
        
        result = self.run_query(query)
        if not result:
            return None
        return result[0]
    
    def insert_or_update_address(self, company, fname, lname, street, zip_code, city, addr_id=None):
        # Sanitize inputs to prevent SQL injection
        company = company.replace("'", "''")
        fname = fname.replace("'", "''")
        lname = lname.replace("'", "''")
        street = street.replace("'", "''")
        zip_code = zip_code.replace("'", "''")
        city = city.replace("'", "''")
        
        if addr_id is None:
            query = """INSERT INTO adressen_basis
                    (adresse_firma, adresse_vorname, adresse_nachname, 
                    adresse_strasse, adresse_plz, adresse_ort, 
                    adresse_ist_stammgast, adresse_ist_lieferant, adresse_ist_gast,
                    adresse_dt_erstellung)
                    VALUES 
                    ('%s', '%s', '%s', 
                    '%s', '%s', '%s', 
                    0, 0, 1,
                    GETDATE())""" % (company, fname, lname, street, zip_code, city)
        else:
            # Validate addr_id
            try:
                addr_id = int(addr_id)
            except ValueError:
                messagebox.showerror("Invalid ID", "Address ID must be an integer")
                return False
            
            query = """UPDATE adressen_basis
                    SET adresse_firma = '%s', adresse_vorname = '%s', adresse_nachname = '%s', 
                    adresse_strasse = '%s', adresse_plz = '%s', adresse_ort = '%s' 
                    WHERE adresse_id = %s""" % (company, fname, lname, street, zip_code, city, addr_id)
        
        self.run_query(query)
        return self.commit()
    
    def refresh_address_list(self):
        # Clear existing data
        for i in self.address_tree.get_children():
            self.address_tree.delete(i)
        
        # Get addresses from database
        addresses = self.get_addresses()
        
        # Insert data into treeview
        for addr in addresses:
            self.address_tree.insert("", "end", values=addr)
        
        self.status_var.set(f"Loaded {len(addresses)} addresses")
    
    def search_address(self):
        search_text = self.search_entry.get()
        
        # Clear existing data
        for i in self.address_tree.get_children():
            self.address_tree.delete(i)
        
        # Get filtered addresses
        addresses = self.get_addresses(search_text)
        
        # Insert data into treeview
        for addr in addresses:
            self.address_tree.insert("", "end", values=addr)
        
        self.status_var.set(f"Found {len(addresses)} matches for '{search_text}'")
    
    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.refresh_address_list()
    
    def clear_form(self):
        # Clear all form fields
        self.address_id.set("")
        self.company_var.set("")
        self.fname_var.set("")
        self.lname_var.set("")
        self.street_var.set("")
        self.zip_var.set("")
        self.city_var.set("")
        
        # Focus on first field
        self.company_entry.focus_set()
        
        # Update form title
        self.right_frame.config(text="New Address")
    
    def edit_address(self):
        # Get selected item
        selection = self.address_tree.selection()
        if not selection:
            messagebox.showinfo("Selection Required", "Please select an address to edit")
            return
        
        # Get item values
        item = self.address_tree.item(selection[0])
        addr_id = item["values"][0]
        
        # Get address details from database
        address = self.get_address(addr_id)
        if not address:
            messagebox.showerror("Error", f"Address with ID {addr_id} not found")
            return
        
        # Fill form with data
        self.address_id.set(address[0])
        self.company_var.set(address[1] or "")
        self.fname_var.set(address[2] or "")
        self.lname_var.set(address[3] or "")
        self.street_var.set(address[4] or "")
        self.zip_var.set(address[5] or "")
        self.city_var.set(address[6] or "")
        
        # Update form title
        self.right_frame.config(text=f"Edit Address (ID: {addr_id})")
    
    def save_address(self):
        # Get values from form
        company = self.company_var.get()
        fname = self.fname_var.get()
        lname = self.lname_var.get()
        street = self.street_var.get()
        zip_code = self.zip_var.get()
        city = self.city_var.get()
        addr_id = self.address_id.get() or None
        
        # Validate required fields
        if not (company or fname or lname):
            messagebox.showwarning("Validation Error", "Please enter at least Company, First Name, or Last Name")
            return
        
        # Confirm with user
        message = f"""Please confirm the address details:
        
Company: {company}
First Name: {fname}
Last Name: {lname}
Street: {street}
ZIP: {zip_code}
City: {city}
"""
        if not messagebox.askyesno("Confirm", message):
            return
        
        # Save to database
        if self.insert_or_update_address(company, fname, lname, street, zip_code, city, addr_id):
            # Refresh the address list
            self.refresh_address_list()
            # Clear the form for next entry
            self.clear_form()
            
            if addr_id:
                messagebox.showinfo("Success", "Address updated successfully")
            else:
                messagebox.showinfo("Success", "New address created successfully")
        else:
            messagebox.showerror("Error", "Failed to save address")

def main():
    root = tk.Tk()
    app = AddressManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()