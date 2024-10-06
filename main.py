import tkinter as tk
from tkinter import messagebox, Listbox, StringVar, Entry, Button
import pyodbc

class PerfumeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Perfume Collection Manager")
        self.conn_str = "f"DRIVER={config['connection_string']['DRIVER']};"
    f"SERVER={config['connection_string']['SERVER']};"
    f"DATABASE={config['connection_string']['DATABASE']};"
    f"UID={config['connection_string']['UID']};"
    f"PWD={config['connection_string']['PWD']};"
        # Database connection
        self.conn = pyodbc.connect(self.conn_str)
        self.cursor = self.conn.cursor()

        # Create a search bar
        self.search_var = StringVar()
        self.search_bar = Entry(root, textvariable=self.search_var)
        self.search_bar.pack(pady=10)
        self.search_bar.bind('<KeyRelease>', self.update_search_results)

        # Create a listbox for search results
        self.results_listbox = Listbox(root)
        self.results_listbox.pack(pady=10, fill=tk.BOTH, expand=True)
        self.results_listbox.bind('<Double-1>', self.show_details)

        # Create buttons
        self.add_button = Button(root, text="Add to My Collection", state=tk.DISABLED, command=self.add_to_collection)
        self.add_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.my_collection_button = Button(root, text="My Collection", command=self.show_my_collection)
        self.my_collection_button.pack(side=tk.BOTTOM, padx=10, pady=10, fill=tk.X)

        # Details frame
        self.details_frame = tk.Frame(root)
        self.details_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        self.details_label = tk.Label(self.details_frame, text="")
        self.details_label.pack()

        self.back_button = Button(self.details_frame, text="Back", command=self.hide_details)
        self.back_button.pack(pady=10)

    def update_search_results(self, event):
        query = self.search_var.get()
        self.results_listbox.delete(0, tk.END)
        if query:
            self.cursor.execute("""
            SELECT perfume_name, perfume_brand
            FROM dbo.perfumes
            WHERE perfume_name LIKE ? OR perfume_brand LIKE ?
            """, ('%' + query + '%', '%' + query + '%'))
            results = self.cursor.fetchall()
            for result in results:
                self.results_listbox.insert(tk.END, f"{result[0]} ({result[1]})")

    def show_details(self, event):
        selected = self.results_listbox.get(tk.ACTIVE)
        if selected:
            name, brand = selected.split(' (')
            brand = brand.rstrip(')')
            self.cursor.execute("""
            SELECT perfume_name, perfume_brand, perfume_link, main_accords, top_notes, heart_notes, base_notes
            FROM dbo.perfumes
            WHERE perfume_name = ? AND perfume_brand = ?
            """, name, brand)
            details = self.cursor.fetchone()
            if details:
                details_str = (f"Name: {details[0]}\nBrand: {details[1]}\nLink: {details[2]}\n"
                               f"Accords: {details[3]}\nTop Notes: {details[4]}\nHeart Notes: {details[5]}\n"
                               f"Base Notes: {details[6]}")
                self.details_label.config(text=details_str)
                self.results_listbox.pack_forget()
                self.add_button.pack_forget()
                self.my_collection_button.pack_forget()
                self.details_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

                self.add_button.config(state=tk.NORMAL)

    def hide_details(self):
        self.details_frame.pack_forget()
        self.results_listbox.pack(pady=10, fill=tk.BOTH, expand=True)
        self.add_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.my_collection_button.pack(side=tk.BOTTOM, padx=10, pady=10, fill=tk.X)

    def add_to_collection(self):
        selected = self.results_listbox.get(tk.ACTIVE)
        if selected:
            name, brand = selected.split(' (')
            brand = brand.rstrip(')')
            self.cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM dbo.my_collection WHERE myperfume_name = ? AND myperfume_brand = ?)
            INSERT INTO dbo.my_collection (myperfume_name, myperfume_brand)
            VALUES (?, ?)
            """, name, brand, name, brand)
            self.conn.commit()
            messagebox.showinfo("Success", f"Added {selected} to My Collection!")

    def show_my_collection(self):
        MyCollectionWindow(self.root, self.conn)

class MyCollectionWindow:
    def __init__(self, master, conn):
        self.top = tk.Toplevel(master)
        self.top.title("My Collection")
        self.conn = conn
        self.cursor = self.conn.cursor()

        # Listbox to display collection
        self.collection_listbox = Listbox(self.top)
        self.collection_listbox.pack(pady=10, fill=tk.BOTH, expand=True)
        self.populate_collection_listbox()

        # Buttons
        self.add_button = Button(self.top, text="Add", command=self.add_perfume)
        self.add_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.delete_button = Button(self.top, text="Delete", command=self.delete_perfume)
        self.delete_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.edit_button = Button(self.top, text="Edit", command=self.edit_perfume)
        self.edit_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.back_button = Button(self.top, text="Back to Main", command=self.top.destroy)
        self.back_button.pack(side=tk.LEFT, padx=10, pady=10)

        # Details frame
        self.details_frame = tk.Frame(self.top)
        self.details_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        self.details_label = tk.Label(self.details_frame, text="")
        self.details_label.pack()

        self.back_button_details = Button(self.details_frame, text="Back", command=self.hide_details)
        self.back_button_details.pack(pady=10)

        self.collection_listbox.bind('<Double-1>', self.show_details)

    def populate_collection_listbox(self):
        self.collection_listbox.delete(0, tk.END)
        self.cursor.execute("SELECT myperfume_name, myperfume_brand FROM dbo.my_collection")
        results = self.cursor.fetchall()
        for result in results:
            self.collection_listbox.insert(tk.END, f"{result[0]} ({result[1]})")

    def add_perfume(self):
        AddPerfumeWindow(self.top, self.conn)

    def delete_perfume(self):
        selected = self.collection_listbox.get(tk.ACTIVE)
        if selected:
            name, brand = selected.split(' (')
            brand = brand.rstrip(')')
            self.cursor.execute("""
            DELETE FROM dbo.my_collection
            WHERE myperfume_name = ? AND myperfume_brand = ?
            """, name, brand)
            self.conn.commit()
            self.populate_collection_listbox()
            messagebox.showinfo("Success", f"Deleted {selected} from My Collection!")

    def edit_perfume(self):
        selected = self.collection_listbox.get(tk.ACTIVE)
        if selected:
            name, brand = selected.split(' (')
            brand = brand.rstrip(')')
            self.cursor.execute("""
            SELECT * FROM dbo.perfumes WHERE perfume_name = ? AND perfume_brand = ?
            """, name, brand)
            details = self.cursor.fetchone()
            if details:
                EditPerfumeWindow(self.top, self.conn, name, brand)

    def show_details(self, event):
        selected = self.collection_listbox.get(tk.ACTIVE)
        if selected:
            name, brand = selected.split(' (')
            brand = brand.rstrip(')')
            self.cursor.execute("""
            SELECT perfume_name, perfume_brand, perfume_link, main_accords, top_notes, heart_notes, base_notes
            FROM dbo.perfumes
            WHERE perfume_name = ? AND perfume_brand = ?
            """, name, brand)
            details = self.cursor.fetchone()
            if details:
                details_str = (f"Name: {details[0]}\nBrand: {details[1]}\nLink: {details[2]}\n"
                               f"Accords: {details[3]}\nTop Notes: {details[4]}\nHeart Notes: {details[5]}\n"
                               f"Base Notes: {details[6]}")
                self.details_label.config(text=details_str)
                self.collection_listbox.pack_forget()
                self.add_button.pack_forget()
                self.delete_button.pack_forget()
                self.edit_button.pack_forget()
                self.back_button.pack_forget()
                self.details_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def hide_details(self):
        self.details_frame.pack_forget()
        self.collection_listbox.pack(pady=10, fill=tk.BOTH, expand=True)
        self.add_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.delete_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.edit_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.back_button.pack(side=tk.LEFT, padx=10, pady=10)

class AddPerfumeWindow:
    def __init__(self, master, conn):
        self.top = tk.Toplevel(master)
        self.top.title("Add Perfume to My Collection")
        self.conn = conn
        self.cursor = self.conn.cursor()

        # Create search bar for adding perfume
        self.add_search_var = StringVar()
        self.add_search_bar = Entry(self.top, textvariable=self.add_search_var)
        self.add_search_bar.pack(pady=10)
        self.add_search_bar.bind('<KeyRelease>', self.update_add_search_results)

        # Listbox for search results
        self.add_results_listbox = Listbox(self.top)
        self.add_results_listbox.pack(pady=10, fill=tk.BOTH, expand=True)
        self.add_results_listbox.bind('<Double-1>', self.select_perfume_for_addition)

        # Create Add and Cancel buttons
        self.save_button = Button(self.top, text="Save", command=self.save_perfume)
        self.save_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.cancel_button = Button(self.top, text="Cancel", command=self.top.destroy)
        self.cancel_button.pack(side=tk.LEFT, padx=10, pady=10)

    def update_add_search_results(self, event):
        query = self.add_search_var.get()
        self.add_results_listbox.delete(0, tk.END)
        if query:
            self.cursor.execute("""
            SELECT perfume_name, perfume_brand
            FROM dbo.perfumes
            WHERE perfume_name LIKE ? OR perfume_brand LIKE ?
            """, ('%' + query + '%', '%' + query + '%'))
            results = self.cursor.fetchall()
            for result in results:
                self.add_results_listbox.insert(tk.END, f"{result[0]} ({result[1]})")

    def select_perfume_for_addition(self, event):
        selected = self.add_results_listbox.get(tk.ACTIVE)
        if selected:
            self.selected_perfume = selected

    def save_perfume(self):
        if hasattr(self, 'selected_perfume'):
            name, brand = self.selected_perfume.split(' (')
            brand = brand.rstrip(')')
            self.cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM dbo.my_collection WHERE myperfume_name = ? AND myperfume_brand = ?)
            INSERT INTO dbo.my_collection (myperfume_name, myperfume_brand)
            VALUES (?, ?)
            """, name, brand, name, brand)
            self.conn.commit()
            messagebox.showinfo("Success", f"Added {self.selected_perfume} to My Collection!")
            self.top.destroy()
        else:
            messagebox.showwarning("No Selection", "Please select a perfume to add.")

class EditPerfumeWindow:
    def __init__(self, master, conn, name, brand):
        self.top = tk.Toplevel(master)
        self.top.title("Edit Perfume Details")
        self.conn = conn
        self.cursor = self.conn.cursor()

        # Retrieve and display current details
        self.cursor.execute("""
        SELECT perfume_name, perfume_brand, perfume_link, main_accords, top_notes, heart_notes, base_notes
        FROM dbo.perfumes
        WHERE perfume_name = ? AND perfume_brand = ?
        """, name, brand)
        details = self.cursor.fetchone()

        if details:
            self.details_vars = {col: StringVar(value=details[i]) for i, col in enumerate(
                ["Name", "Brand", "Link", "Accords", "Top Notes", "Heart Notes", "Base Notes"])}
            for i, (key, value) in enumerate(self.details_vars.items()):
                tk.Label(self.top, text=key).grid(row=i, column=0, padx=10, pady=5)
                tk.Entry(self.top, textvariable=value).grid(row=i, column=1, padx=10, pady=5)

            # Save and Cancel buttons
            self.save_button = Button(self.top, text="Save", command=self.save_changes)
            self.save_button.grid(row=len(self.details_vars), column=0, padx=10, pady=10)
            self.cancel_button = Button(self.top, text="Cancel", command=self.top.destroy)
            self.cancel_button.grid(row=len(self.details_vars), column=1, padx=10, pady=10)

    def save_changes(self):
        new_details = [var.get() for var in self.details_vars.values()]
        self.cursor.execute("""
        UPDATE dbo.perfumes
        SET perfume_name = ?, perfume_brand = ?, perfume_link = ?, main_accords = ?, top_notes = ?, heart_notes = ?, base_notes = ?
        WHERE perfume_name = ? AND perfume_brand = ?
        """, *new_details, self.details_vars['Name'].get(), self.details_vars['Brand'].get())
        self.conn.commit()
        messagebox.showinfo("Success", "Details updated successfully!")
        self.top.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PerfumeApp(root)
    root.mainloop()
