import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import json
import os
import csv
import math 
import time 
import webbrowser 
import sys
from datetime import datetime

# DATABASE ENGINE (DESENSITIZED)

csv_filename = "floral_prices.csv"
catalog = {}
flower_names = []

def generate_template_csv():
    """ Creates a fresh template if the file is missing """
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Using generic headers for public sharing
        writer.writerow(["Flower_Name", "Variety", "COMPA_Price", "COMPB_Price", "Bunch_Size"])
        writer.writerow(["Rose", "Vendela", "1.00", "1.10", "25"])
        writer.writerow(["Hydrangea", "White", "2.00", "2.50", "5"])

def load_database():
    global catalog, flower_names
    catalog.clear()
    
    if not os.path.exists(csv_filename):
        generate_template_csv()
        
    try:
        with open(csv_filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                flower = row['Flower_Name'].strip()
                variety = row['Variety'].strip()
                
                # Match these keys exactly to the headers in generate_template_csv
                a_price = float(row['COMPA_Price']) if row['COMPA_Price'] else 0.0
                b_price = float(row['COMPB_Price']) if row['COMPB_Price'] else 0.0
                bunch_sz = int(row['Bunch_Size']) if row['Bunch_Size'] else 1
                
                if flower not in catalog:
                    catalog[flower] = {
                        "varieties": [], 
                        "vendors": {"Vendor_A": {}, "Vendor_B": {}}, 
                        "bunch_size": bunch_sz
                    }
                
                if variety:
                    catalog[flower]["varieties"].append(variety)
                    if a_price > 0: catalog[flower]["vendors"]["Vendor_A"][variety] = a_price
                    if b_price > 0: catalog[flower]["vendors"]["Vendor_B"][variety] = b_price
                else:
                    if a_price > 0: catalog[flower]["vendors"]["Vendor_A"][""] = a_price
                    if b_price > 0: catalog[flower]["vendors"]["Vendor_B"][""] = b_price
                    
        flower_names = sorted(list(catalog.keys()))
        return len(catalog)
    except Exception as e:
        print(f"Error loading database: {e}")
        return 0

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def setup_app():
    load_database() 
    
    root = tk.Tk()
    root.title("Shop Florals - Master POS")
    root.geometry("1250x850") 
    root.config(padx=20, pady=20)
    
    try:
        app_icon = tk.PhotoImage(file=resource_path('logo.png'))
        root.iconphoto(True, app_icon)
    except Exception:
        pass
    
    global cart, display_order
    cart = {} 
    display_order = [] 

    # ==========================================
    # GLOBAL VARIABLES
    # ==========================================
    selected_flower = tk.StringVar()
    entered_variety = tk.StringVar()
    entered_quantity = tk.StringVar()
    vendor_override = tk.StringVar(value="Auto (Cheapest)") 
    
    floral_subtotal = tk.DoubleVar(value=0.0) 
    optimal_floral_subtotal = tk.DoubleVar(value=0.0) 
    
    client_name_input = tk.StringVar(value="")
    event_date_input = tk.StringVar(value="")

    client_revenue_input = tk.StringVar(value="0.00") 
    delivery_fee_input = tk.StringVar(value="0.00")
    tax_rate_input = tk.StringVar(value="6.625")
    hardgoods_input = tk.StringVar(value="0.00") 
    rentals_input = tk.StringVar(value="0.00")
    deposit_input = tk.StringVar(value="0.00")

    # UI LAYOUT: COLUMN 1 (The Cart)
    left_frame = tk.Frame(root)
    left_frame.pack(side="left", fill="y", padx=(0, 20))

    tk.Label(left_frame, text="Build Order", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 15), columnspan=2)

    tk.Label(left_frame, text="Flower Name:").grid(row=1, column=0, sticky="w", pady=5)
    flower_combo = ttk.Combobox(left_frame, textvariable=selected_flower, width=28)
    flower_combo.grid(row=1, column=1, pady=5)

    tk.Label(left_frame, text="Variety:").grid(row=2, column=0, sticky="w", pady=5)
    variety_combo = ttk.Combobox(left_frame, textvariable=entered_variety, width=28, state='disabled')
    variety_combo.grid(row=2, column=1, pady=5)

    tk.Label(left_frame, text="Stems Needed:").grid(row=3, column=0, sticky="w", pady=5)
    quantity_entry = tk.Entry(left_frame, textvariable=entered_quantity, width=31)
    quantity_entry.grid(row=3, column=1, pady=5)

    tk.Label(left_frame, text="Vendor Pref:").grid(row=4, column=0, sticky="w", pady=5)
    vendor_combo = ttk.Combobox(left_frame, textvariable=vendor_override, values=["Auto (Cheapest)", "Force Vendor A", "Force Vendor B"], width=28, state='readonly')
    vendor_combo.grid(row=4, column=1, pady=5)

    tk.Label(left_frame, text="Current Wholesale Order (Click to Delete):").grid(row=5, column=0, sticky="sw", pady=(20, 0), columnspan=2)
    order_list = tk.Listbox(left_frame, width=65, height=28, font=("Courier", 9))
    order_list.grid(row=6, column=0, columnspan=2, pady=5)

    # UI LAYOUT: COLUMN 2 (Settings & Database)
    middle_frame = tk.Frame(root, bg="#f4f4f4", bd=2, relief="groove", padx=15, pady=15)
    middle_frame.pack(side="left", fill="y", padx=(0, 20))

    tk.Label(middle_frame, text="Quote Management", font=("Arial", 14, "bold"), bg="#f4f4f4").pack(anchor="w", pady=(0, 10))
    
    meta_frame = tk.Frame(middle_frame, bg="#f4f4f4")
    meta_frame.pack(fill="x", pady=(0, 5))
    tk.Label(meta_frame, text="Client:", bg="#f4f4f4").grid(row=0, column=0, sticky="w", pady=5)
    tk.Entry(meta_frame, textvariable=client_name_input, width=22).grid(row=0, column=1, sticky="e", pady=5)
    tk.Label(meta_frame, text="Date:", bg="#f4f4f4").grid(row=1, column=0, sticky="w", pady=5)
    tk.Entry(meta_frame, textvariable=event_date_input, width=22).grid(row=1, column=1, sticky="e", pady=5)

    button_frame = tk.Frame(meta_frame, bg="#f4f4f4")
    button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
    btn_save = tk.Button(button_frame, text="💾 Save", bg="lightblue", width=10)
    btn_save.pack(side="left", padx=5)
    btn_load = tk.Button(button_frame, text="📂 Load", bg="lightgray", width=10)
    btn_load.pack(side="left", padx=5)

    lbl_status = tk.Label(meta_frame, text="", bg="#f4f4f4", fg="green", font=("Arial", 9, "italic"))
    lbl_status.grid(row=3, column=0, columnspan=2, sticky="w", pady=(5, 5))

    tk.Frame(middle_frame, height=2, bg="#cccccc").pack(fill="x", pady=10) 

    tk.Label(middle_frame, text="Database (CSV)", font=("Arial", 12, "bold"), bg="#f4f4f4").pack(anchor="w", pady=(0, 5))
    db_frame = tk.Frame(middle_frame, bg="#f4f4f4")
    db_frame.pack(fill="x", pady=(0, 5))
    
    btn_open_csv = tk.Button(db_frame, text="⚙️ Open in Excel", width=14, command=lambda: os.startfile(csv_filename))
    btn_open_csv.pack(side="left", padx=2)
    
    def trigger_reload():
        count = load_database()
        flower_combo.config(values=flower_names)
        lbl_status.config(text=f"✓ Reloaded {count} flowers from CSV", fg="blue")
        
    btn_reload_csv = tk.Button(db_frame, text="🔄 Reload App", width=14, command=trigger_reload)
    btn_reload_csv.pack(side="right", padx=2)
    
    tk.Frame(middle_frame, height=2, bg="#cccccc").pack(fill="x", pady=10) 

    tk.Label(middle_frame, text="Financials", font=("Arial", 14, "bold"), bg="#f4f4f4").pack(anchor="w", pady=(0, 10))

    settings_frame = tk.Frame(middle_frame, bg="#f4f4f4")
    settings_frame.pack(fill="x")

    tk.Label(settings_frame, text="Client Total ($):", bg="#f4f4f4").grid(row=0, column=0, sticky="w", pady=5)
    entry_client = tk.Entry(settings_frame, textvariable=client_revenue_input, width=15)
    entry_client.grid(row=0, column=1, sticky="e", pady=5)
    
    tk.Label(settings_frame, text="Delivery ($):", bg="#f4f4f4").grid(row=1, column=0, sticky="w", pady=5)
    entry_delivery = tk.Entry(settings_frame, textvariable=delivery_fee_input, width=15)
    entry_delivery.grid(row=1, column=1, sticky="e", pady=5)
    
    tk.Label(settings_frame, text="Tax Rate (%):", bg="#f4f4f4").grid(row=2, column=0, sticky="w", pady=5)
    entry_tax = tk.Entry(settings_frame, textvariable=tax_rate_input, width=15)
    entry_tax.grid(row=2, column=1, sticky="e", pady=5)
    
    tk.Label(settings_frame, text="Hardgoods ($):", bg="#f4f4f4").grid(row=3, column=0, sticky="w", pady=5)
    entry_hg = tk.Entry(settings_frame, textvariable=hardgoods_input, width=15)
    entry_hg.grid(row=3, column=1, sticky="e", pady=5)
    
    tk.Label(settings_frame, text="Rentals ($):", bg="#f4f4f4").grid(row=4, column=0, sticky="w", pady=5)
    entry_rentals = tk.Entry(settings_frame, textvariable=rentals_input, width=15)
    entry_rentals.grid(row=4, column=1, sticky="e", pady=5)
    
    tk.Label(settings_frame, text="Deposit ($):", bg="#f4f4f4").grid(row=5, column=0, sticky="w", pady=5)
    entry_deposit = tk.Entry(settings_frame, textvariable=deposit_input, width=15)
    entry_deposit.grid(row=5, column=1, sticky="e", pady=5)

    tk.Frame(settings_frame, height=1, bg="#ccc").grid(row=6, column=0, columnspan=2, pady=(15, 5), sticky="we")
    
    tk.Label(settings_frame, text="Optimal COG:", bg="#f4f4f4", font=("Arial", 10, "bold"), fg="#555").grid(row=7, column=0, sticky="w", pady=5)
    lbl_optimal_insight = tk.Label(settings_frame, text="$0.00", bg="#f4f4f4", fg="green", font=("Arial", 10, "bold"))
    lbl_optimal_insight.grid(row=7, column=1, sticky="e", pady=5)

    fin_entries = [entry_client, entry_delivery, entry_tax, entry_hg, entry_rentals, entry_deposit]
    def handle_fin_nav(event, current_idx, direction):
        next_idx = (current_idx + direction) % len(fin_entries)
        fin_entries[next_idx].focus_set()
        fin_entries[next_idx].select_range(0, tk.END) 
        return "break"
    for i, entry in enumerate(fin_entries):
        entry.bind('<Up>', lambda e, idx=i: handle_fin_nav(e, idx, -1))
        entry.bind('<Down>', lambda e, idx=i: handle_fin_nav(e, idx, 1))

    # UI LAYOUT: COLUMN 3 (The Receipt)

    right_frame = tk.Frame(root, bg="white", bd=1, relief="solid", padx=25, pady=25)
    right_frame.pack(side="left", fill="both", expand=True)

    tk.Label(right_frame, text="--- CLIENT INVOICE ---", bg="white", font=("Courier", 12, "bold"), fg="#555").pack(anchor="w", pady=(0,5))
    lbl_client_rev = tk.Label(right_frame, text="FLORAL REVENUE:\t$0.00", bg="white", font=("Courier", 12))
    lbl_client_rev.pack(anchor="w", pady=2)
    lbl_delivery = tk.Label(right_frame, text="DELIVERY:\t$0.00", bg="white", font=("Courier", 12))
    lbl_delivery.pack(anchor="w", pady=2)
    lbl_tax = tk.Label(right_frame, text="TAX:\t\t$0.00", bg="white", font=("Courier", 12))
    lbl_tax.pack(anchor="w", pady=2)
    lbl_grand_total = tk.Label(right_frame, text="GRAND TOTAL:\t$0.00", bg="white", font=("Courier", 14, "bold"))
    lbl_grand_total.pack(anchor="w", pady=(10,2))
    lbl_balance = tk.Label(right_frame, text="BALANCE DUE:\t$0.00", bg="white", font=("Courier", 13, "bold"), fg="blue")
    lbl_balance.pack(anchor="w", pady=2)

    tk.Frame(right_frame, height=2, bg="#ccc").pack(fill="x", pady=20) 

    tk.Label(right_frame, text="--- SHOP PROFITABILITY ---", bg="white", font=("Courier", 12, "bold"), fg="#555").pack(anchor="w", pady=(0,5))
    
    lbl_hg_rental = tk.Label(right_frame, text="HARDGOODS/RENTAL:-$0.00", bg="white", font=("Courier", 11), fg="red")
    lbl_hg_rental.pack(anchor="w", pady=2)
    lbl_net_floral = tk.Label(right_frame, text="NET FLORAL:\t$0.00", bg="white", font=("Courier", 11))
    lbl_net_floral.pack(anchor="w", pady=2)
    
    lbl_target_cog = tk.Label(right_frame, text="TARGET COG(25%):$0.00", bg="white", font=("Courier", 11))
    lbl_target_cog.pack(anchor="w", pady=2)
    lbl_actual_cost = tk.Label(right_frame, text="ACTUAL WHOLESALE:\t$0.00", bg="white", font=("Courier", 13, "bold"))
    lbl_actual_cost.pack(anchor="w", pady=(10,2))
    
    lbl_budget_status = tk.Label(right_frame, text="", bg="white", font=("Courier", 11, "bold"))
    lbl_budget_status.pack(anchor="w", pady=(5, 10))

    tk.Frame(right_frame, height=1, bg="#eee").pack(fill="x", pady=5) 

    lbl_actual_cog_pct = tk.Label(right_frame, text="ACTUAL COG %:\t0.00%", bg="white", font=("Courier", 12, "bold"), fg="purple")
    lbl_actual_cog_pct.pack(anchor="w", pady=2)
    lbl_gross_profit = tk.Label(right_frame, text="GROSS PROFIT:\t$0.00", bg="white", font=("Courier", 14, "bold"), fg="green")
    lbl_gross_profit.pack(anchor="w", pady=(10, 2))

    tk.Frame(right_frame, height=2, bg="#ccc").pack(fill="x", pady=20) 
    
    print_frame = tk.Frame(right_frame, bg="white")
    print_frame.pack(fill="x", pady=5)
    btn_print_client = tk.Button(print_frame, text="📄 Print Client Quote", bg="#e6f2ff", font=("Arial", 11, "bold"), height=2)
    btn_print_client.pack(side="left", expand=True, fill="x", padx=5)
    btn_print_shop = tk.Button(print_frame, text="🖨️ Print Shop Ticket", bg="#fff2e6", font=("Arial", 11, "bold"), height=2)
    btn_print_shop.pack(side="left", expand=True, fill="x", padx=5)

    # BEHAVIOR & LOGIC 
    def filter_flower_dropdown():
        typed = selected_flower.get().lower()
        if not typed: flower_combo.config(values=flower_names)
        else:
            filtered = [item for item in flower_names if item.lower().startswith(typed)]
            flower_combo.config(values=filtered)

    def filter_variety_dropdown():
        flower = selected_flower.get()
        typed = entered_variety.get().lower()
        varieties = catalog.get(flower, {}).get("varieties", [])
        if not typed: variety_combo.config(values=varieties)
        else:
            filtered = [item for item in varieties if item.lower().startswith(typed)]
            variety_combo.config(values=filtered)

    flower_combo.config(postcommand=filter_flower_dropdown)
    variety_combo.config(postcommand=filter_variety_dropdown)

    def update_variety_state(*args):
        raw_flower = selected_flower.get().strip().lower()
        matched_flower = None
        for name in flower_names:
            if name.lower() == raw_flower:
                matched_flower = name
                break
                
        if matched_flower:
            varieties = catalog[matched_flower].get("varieties", [])
            if not varieties: 
                variety_combo.set("")
                variety_combo.config(state='disabled')
            else:
                variety_combo.config(state='normal')
                if len(varieties) == 1:
                    variety_combo.set(varieties[0]) 
        else:
            variety_combo.set("")
            variety_combo.config(state='disabled')

    selected_flower.trace_add("write", update_variety_state)

    def jump_to_variety():
        if str(variety_combo['state']) == 'normal':
            variety_combo.focus()
            variety_combo.event_generate('<Down>')
        else:
            quantity_entry.focus()

    def jump_to_quantity():
        quantity_entry.focus()

    def jump_to_flower():
        flower_combo.focus()

    last_flower_select_time = [0]
    def on_flower_select(event=None):
        now = time.time()
        if now - last_flower_select_time[0] < 0.2: return "break"
        last_flower_select_time[0] = now
        root.after(10, jump_to_variety)
        return "break"

    last_variety_select_time = [0]
    def on_variety_select(event=None):
        now = time.time()
        if now - last_variety_select_time[0] < 0.2: return "break"
        last_variety_select_time[0] = now
        root.after(10, jump_to_quantity)
        return "break"

    def auto_fill_flower(event=None):
        typed = selected_flower.get().strip()
        for name in flower_names:
            if name.lower() == typed.lower():
                selected_flower.set(name)
                on_flower_select()
                return "break"
        for name in flower_names:
            if name.lower().startswith(typed.lower()):
                selected_flower.set(name)
                flower_combo.icursor(tk.END)
                root.after(10, lambda: flower_combo.event_generate('<Down>')) 
                return "break"

    def auto_fill_variety(event=None):
        flower = selected_flower.get()
        typed = entered_variety.get().strip()
        varieties = catalog.get(flower, {}).get("varieties", [])
        if not typed:
            root.after(10, lambda: variety_combo.event_generate('<Down>'))
            return "break"
        for v in varieties:
            if v.lower() == typed.lower():
                entered_variety.set(v)
                on_variety_select()
                return "break"
        for v in varieties:
            if v.lower().startswith(typed.lower()):
                entered_variety.set(v)
                variety_combo.icursor(tk.END)
                root.after(10, lambda: variety_combo.event_generate('<Down>'))
                return "break"

    def handle_quantity_enter(event=None):
        flower = selected_flower.get()
        variety = entered_variety.get()
        qty_str = entered_quantity.get()
        override = vendor_override.get()
        
        if not qty_str.isdigit() or int(qty_str) <= 0: return

        qty = int(qty_str)
        bunch_size = catalog[flower].get("bunch_size", 1) 
        available_vendors = catalog[flower].get("vendors", {})
        
        valid_options = {}
        for vendor_name, varieties_dict in available_vendors.items():
            if variety in varieties_dict or not variety: 
                valid_options[vendor_name] = varieties_dict.get(variety, 0.0)

        if not valid_options and variety: return

        if override == "Auto (Cheapest)" and valid_options:
            chosen_vendor = min(valid_options, key=valid_options.get)
            price_per_unit = valid_options[chosen_vendor]
        elif override == "Force Vendor A" and "Vendor_A" in valid_options:
            chosen_vendor = "Vendor_A"
            price_per_unit = valid_options["Vendor_A"]
        elif override == "Force Vendor B" and "Vendor_B" in valid_options:
            chosen_vendor = "Vendor_B"
            price_per_unit = valid_options["Vendor_B"]
        else:
            price_per_unit = 0.0
            chosen_vendor = "Default"
            
        item_key = f"{flower}|{variety}|{chosen_vendor}" 
        if item_key in cart: cart[item_key]["qty"] += qty
        else: cart[item_key] = {"flower": flower, "variety": variety, "qty": qty, "price": price_per_unit, "bunch_size": bunch_size, "vendor": chosen_vendor}

        update_receipt()

        selected_flower.set("")
        entered_variety.set("")
        entered_quantity.set("")
        vendor_override.set("Auto (Cheapest)") 
        root.after(10, jump_to_flower) 

    def filter_combobox(event, combo_widget, full_list):
        if event.keysym in ('Return', 'Tab', 'Down', 'Up', 'Right', 'Left'): return
        typed = combo_widget.get()
        cursor_pos = combo_widget.index(tk.INSERT) 
        if not typed: 
            combo_widget['values'] = full_list
            return
        filtered = [item for item in full_list if item.lower().startswith(typed.lower())]
        combo_widget['values'] = filtered
        if filtered:
            combo_widget.set(typed)
            combo_widget.icursor(cursor_pos)

    def delete_item(event):
        selection_index = order_list.curselection()
        if selection_index:
            key_to_delete = display_order[selection_index[0]]
            del cart[key_to_delete]
            update_receipt()
            order_list.selection_clear(0, tk.END) 

    def update_receipt():
        order_list.delete(0, tk.END) 
        display_order.clear() 
        wholesale_subtotal = 0.0
        optimal_subtotal = 0.0 

        for item_key, item_data in cart.items():
            flower = item_data["flower"]
            variety = item_data["variety"]
            qty_needed = item_data["qty"]
            bunch_sz = item_data["bunch_size"]
            price_per_stem = item_data["price"]
            chosen_vendor = item_data["vendor"]
            
            bunches_to_buy = math.ceil(qty_needed / bunch_sz)
            total_stems_bought = bunches_to_buy * bunch_sz
            wholesale_cost = total_stems_bought * price_per_stem
            wholesale_subtotal += wholesale_cost
            
            # Optimal math
            v_data = catalog.get(flower, {}).get("vendors", {})
            valid_prices = [p for p in [v_data.get("Vendor_A", {}).get(variety), v_data.get("Vendor_B", {}).get(variety)] if p is not None and p > 0]
            
            min_price = min(valid_prices) if valid_prices else price_per_stem
            optimal_subtotal += (total_stems_bought * min_price)

            display_name = f"{item_data['flower']} "
            if item_data['variety']: display_name = f"{item_data['variety']} [{chosen_vendor}]"
            else: display_name = f"{item_data['flower']} [{chosen_vendor}]"
            
            display_text = f"{display_name:<20} Need {qty_needed:<3} -> {bunches_to_buy} Bunch(es) .... ${wholesale_cost:.2f}"
            
            order_list.insert(tk.END, display_text)
            display_order.append(item_key) 

        floral_subtotal.set(wholesale_subtotal)
        optimal_floral_subtotal.set(optimal_subtotal)

    def recalculate_totals(*args):
        try:
            actual_floral_cost = floral_subtotal.get()

            client_rev = float(client_revenue_input.get()) if client_revenue_input.get() else 0.0
            delivery = float(delivery_fee_input.get()) if delivery_fee_input.get() else 0.0
            tax_percent = float(tax_rate_input.get()) if tax_rate_input.get() else 0.0
            dep = float(deposit_input.get()) if deposit_input.get() else 0.0
            hg = float(hardgoods_input.get()) if hardgoods_input.get() else 0.0
            rentals = float(rentals_input.get()) if rentals_input.get() else 0.0

            sub_with_delivery = client_rev + delivery
            tax_amount = sub_with_delivery * (tax_percent / 100)
            grand_total = sub_with_delivery + tax_amount
            balance = grand_total - dep

            lbl_client_rev.config(text=f"FLORAL REVENUE:\t${client_rev:,.2f}")
            lbl_delivery.config(text=f"DELIVERY:\t${delivery:,.2f}")
            lbl_tax.config(text=f"TAX ({tax_percent}%):\t${tax_amount:,.2f}")
            lbl_grand_total.config(text=f"GRAND TOTAL:\t${grand_total:,.2f}")
            lbl_balance.config(text=f"BALANCE DUE:\t${balance:,.2f}")

            deductions = hg + rentals
            net_floral = client_rev - deductions
            target_cog = net_floral * 0.25
            difference = target_cog - actual_floral_cost

            gross_profit = net_floral - actual_floral_cost
            actual_cog_pct = (actual_floral_cost / net_floral * 100) if net_floral > 0 else 0.0

            lbl_hg_rental.config(text=f"HARDGOODS/RENTAL:-${deductions:,.2f}")
            lbl_net_floral.config(text=f"NET FLORAL:\t${net_floral:,.2f}")
            lbl_target_cog.config(text=f"TARGET COG(25%):${target_cog:,.2f}")
            lbl_actual_cost.config(text=f"ACTUAL WHOLESALE:\t${actual_floral_cost:,.2f}")
            
            opt_cost = optimal_floral_subtotal.get()
            savings = actual_floral_cost - opt_cost
            
            if savings > 0.01:
                lbl_optimal_insight.config(text=f"${opt_cost:,.2f} (Save ${savings:,.2f})", fg="#d97706")
            else:
                lbl_optimal_insight.config(text=f"${opt_cost:,.2f} (Optimized)", fg="green")

            lbl_actual_cog_pct.config(text=f"ACTUAL COG %:\t{actual_cog_pct:.1f}%")
            lbl_gross_profit.config(text=f"GROSS PROFIT:\t${gross_profit:,.2f}")

            if difference >= 0:
                lbl_budget_status.config(text=f"✓ UNDER BUDGET by ${difference:,.2f}", fg="green")
                lbl_actual_cog_pct.config(fg="green")
            else:
                lbl_budget_status.config(text=f"⚠ OVER BUDGET by ${abs(difference):,.2f}", fg="red")
                lbl_actual_cog_pct.config(fg="red")

        except ValueError:
            pass 

    # --- HTML / PDF EXPORT ENGINE ---
    def generate_pdf(doc_type="client"):
        client = client_name_input.get() or "Client Name"
        date = event_date_input.get() or "TBD"
        now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        logo_path = os.path.abspath("logo.png")
        logo_html = f'<img src="file:///{logo_path}" alt="Shop Logo" style="max-height: 80px;">' if os.path.exists("logo.png") else "<h2>Shop Florals</h2>"
        
        html_content = f"""
        <html>
        <head>
            <title>Shop Florals - {client}</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; padding: 40px; max-width: 850px; margin: auto; }}
                .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #2c3e50; padding-bottom: 20px; margin-bottom: 30px; }}
                .shop-info {{ text-align: right; color: #666; font-size: 0.9em; line-height: 1.4; }}
                .client-box {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #e9ecef; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 0.95em; }}
                th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
                th {{ background-color: #2c3e50; color: white; font-weight: 500; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .totals-container {{ display: flex; justify-content: flex-end; }}
                .totals {{ width: 350px; background: #fff; border: 1px solid #ddd; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
                .totals p {{ margin: 8px 0; display: flex; justify-content: space-between; font-size: 0.95em; }}
                .grand-total {{ font-size: 1.2em; font-weight: bold; color: #2c3e50; border-top: 2px solid #ccc; padding-top: 10px; margin-top: 10px; }}
                .balance {{ font-size: 1.1em; font-weight: bold; color: #27ae60; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div>{logo_html}</div>
                <div class="shop-info">
                    <strong>Shop Florals</strong><br>
                    Main Street, Suite A<br>
                    City, State Zip<br>
                    (555) 000-0000<br>
                    info@example.com
                </div>
            </div>
            <div class="client-box">
                <div><strong>Quote For:</strong> {client}</div>
                <div style="text-align: right;"><strong>Date:</strong> {date}</div>
            </div>
            <h3>Recipe Requirements</h3>
            <table>
                <tr><th>Flower</th><th>Variety</th><th>Stems</th></tr>
        """
        for item_key, item_data in cart.items():
            html_content += f"<tr><td>{item_data['flower']}</td><td>{item_data['variety']}</td><td>{item_data['qty']}</td></tr>"
        
        html_content += """</table></body></html>"""
        
        filename = f"{client.replace(' ', '_')}_Quote.html"
        filepath = os.path.abspath(filename)
        with open(filepath, "w", encoding='utf-8') as file:
            file.write(html_content)
        webbrowser.open(f"file://{filepath}")

    btn_print_client.config(command=lambda: generate_pdf("client"))
    btn_print_shop.config(command=lambda: generate_pdf("shop"))

    def save_quote():
        quote_data = {"metadata": {"client_name": client_name_input.get(), "event_date": event_date_input.get()}, "settings": {"client_revenue": client_revenue_input.get(), "delivery": delivery_fee_input.get(), "tax_rate": tax_rate_input.get(), "deposit": deposit_input.get(), "hardgoods": hardgoods_input.get(), "rentals": rentals_input.get()}, "cart": cart}
        default_filename = f"{client_name_input.get()}_Quote.json" if client_name_input.get() else "New_Quote.json"
        filepath = filedialog.asksaveasfilename(defaultextension=".json", initialfile=default_filename, filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if filepath: 
            with open(filepath, 'w') as file: json.dump(quote_data, file, indent=4)
            lbl_status.config(text=f"✓ Saved '{os.path.basename(filepath)}'\n  at {datetime.now().strftime('%I:%M %p')}", fg="green")

    def load_quote():
        global cart 
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if filepath:
            try:
                with open(filepath, 'r') as file: quote_data = json.load(file)
                client_name_input.set(quote_data["metadata"].get("client_name", ""))
                event_date_input.set(quote_data["metadata"].get("event_date", ""))
                client_revenue_input.set(quote_data["settings"].get("client_revenue", "0.00"))
                delivery_fee_input.set(quote_data["settings"].get("delivery", "0.00"))
                tax_rate_input.set(quote_data["settings"].get("tax_rate", "6.625"))
                deposit_input.set(quote_data["settings"].get("deposit", "0.00"))
                hardgoods_input.set(quote_data["settings"].get("hardgoods", "0.00"))
                rentals_input.set(quote_data["settings"].get("rentals", "0.00"))
                cart = quote_data.get("cart", {})
                update_receipt()
                lbl_status.config(text=f"✓ Loaded '{os.path.basename(filepath)}'", fg="blue")
            except Exception as e:
                lbl_status.config(text=f"⚠ Error loading file!", fg="red")

    btn_save.config(command=save_quote)
    btn_load.config(command=load_quote)

    floral_subtotal.trace_add("write", recalculate_totals)
    client_revenue_input.trace_add("write", recalculate_totals)
    tax_rate_input.trace_add("write", recalculate_totals)
    delivery_fee_input.trace_add("write", recalculate_totals)
    deposit_input.trace_add("write", recalculate_totals)
    hardgoods_input.trace_add("write", recalculate_totals)
    rentals_input.trace_add("write", recalculate_totals)

    flower_combo.bind("<<ComboboxSelected>>", on_flower_select)
    variety_combo.bind("<<ComboboxSelected>>", on_variety_select)
    flower_combo.bind("<Return>", auto_fill_flower)
    variety_combo.bind("<Return>", auto_fill_variety)
    quantity_entry.bind("<Return>", handle_quantity_enter)
    order_list.bind("<<ListboxSelect>>", delete_item)
    flower_combo.bind('<KeyRelease>', lambda e: filter_combobox(e, flower_combo, flower_names))
    variety_combo.bind('<KeyRelease>', lambda e: filter_combobox(e, variety_combo, catalog.get(selected_flower.get(), {}).get("varieties", [])))

    recalculate_totals()
    flower_combo.focus()
    root.mainloop()

if __name__ == "__main__":
    setup_app()