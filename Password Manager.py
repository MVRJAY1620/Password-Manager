import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import re
from cryptography.fernet import Fernet
import pyperclip
import time
import threading

key = Fernet.generate_key()
fernet_key = Fernet(key)
# Creates a database to store passwords
connection = sqlite3.connect('passwords.db')
c = connection.cursor()
c.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
''')

connection.commit()
# This functon is used to check the strength of the password based on the length of the password
def check_passwordstrength(password):
    password_length = len(password)
    digit_in_password = re.search(r'\d', password)
    uppercase_in_password = re.search(r'[A-Z]', password)
    lowercase_in_password = re.search(r'[a-z]', password)
    special_character_in_password = re.search(r'[!@#$%^&*()?<>]', password)

    password_score = sum([password_length, bool(digit_in_password), bool(uppercase_in_password), bool(lowercase_in_password), bool(special_character_in_password)])

    if password_score <= 4:
        return "Weak, use some better characters", "red"
    elif password_score == 5 or password_score == 6:
        return "Medium, could be better", "orange"
    else:
        return "Strong, Great", "green"
# This function is used to prompt the user to get valid credentials
def add_password():
    website = website_entry.get()
    username = username_entry.get()
    password = password_entry.get()

    if not website or not username or not password:
        messagebox.showerror("Error", "All fields are required")
        return

    encrypted_password = fernet_key.encrypt(password.encode())
    c.execute('INSERT INTO passwords (website, username, password) VALUES (?, ?, ?)',(website, username, encrypted_password))
    connection.commit()

    messagebox.showinfo("Success", "Password saved suuccessfully")

    website_entry.delete(0, tk.END)
    username_entry.delete(0, tk.END)
    password_entry.delete(0, tk.END)

    update_table()
# This function is used to delete the credential
def delete_password():
    selected_password = tree.focus()
    if not selected_password:
        messagebox.showerror("Error", "Select a password to delete")
        return
    values = tree.item(selected_password, 'values')
    c.execute('DELETE FROM passwords WHERE id = ?', (values[0],))
    connection.commit()

    update_table()
# This function is used to copy the password from the selected credential to the clipboard for 10sec
def copy_password():
    selected_password = tree.focus()
    if not selected_password:
        messagebox.showerror("Error", "Select a entry to copy a password")
        return
    values = tree.item(selected_password, 'values')
    c.execute('SELECT password FROM passwords WHERE id = ?', (values[0],))
    encrypt_password = c.fetchone()[0]
    decrypt_password = fernet_key.decrypt(encrypt_password).decode()
    pyperclip.copy(decrypt_password)
    messagebox.showinfo("Copied", "Password copied to clipboard, cleared in 10sec")

    def clear_clipboard():
        time.sleep(10)
        pyperclip.copy("")

    threading.Thread(target=clear_clipboard, daemon=True).start()
# this function updates the credentials
def update_table():
    for row in tree.get_children():
        tree.delete(row)
    c.execute('SELECT * FROM passwords')
    for row in c.fetchall():
        tree.insert("", tk.END, values=(row[0], row[1], row[2]))
# This function shows the strength of the password while the user enters the password
def on_password_entry(event):
    strength, color = check_passwordstrength(password_entry.get())
    label_strength.config(text=f"Strength: {strength}", fg=color)
# UI
root = tk.Tk()
root.title("Password Manager")
root.geometry("700x500")

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Website:").grid(row=0, column=0, padx=5, pady=5)
website_entry = tk.Entry(frame)
website_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame, text="Username:").grid(row=1, column=0, padx=5, pady=5)
username_entry = tk.Entry(frame)
username_entry.grid(row=1, column=1, padx=5, pady=5)

tk.Label(frame, text="Password:").grid(row=2, column=0, padx=5, pady=5)
password_entry = tk.Entry(frame, show="*")
password_entry.grid(row=2, column=1, padx=5, pady=5)
password_entry.bind("<KeyRelease>", on_password_entry)

label_strength = tk.Label(frame, text="Strength: ", fg="black")
label_strength.grid(row=2, column=2, padx=10)
# adds buttons for add the credentials, deleting and copying.
tk.Button(frame, text="Add", command=add_password).grid(row=3, column=0, pady=10)
tk.Button(frame, text="Delete", command=delete_password).grid(row=3, column=1, pady=10)
tk.Button(frame, text="Copy", command=copy_password).grid(row=3, column=2, pady=10)

columnss = ("ID", "Website", "Username")
tree = ttk.Treeview(root, columns=columnss, show='headings')
for col in columnss:
    tree.heading(col, text=col)
tree.pack(fill=tk.BOTH, expand=True)

update_table()


root.mainloop()
