import re
a = 'Hei Online Linjeforeningen for Informatikk,\r\n\r\nDet har kommet inn en ny ordre via TidypayGO - her er detaljene:\r\n\r\n\r\nOrdrenummer:    15644\r\nFakturanummer:  16270\r\nDato og tid:    2024-03-26 14:36:40\r\n\r\n\r\nKunde:  Ådne Børresen ( adne_2000@hotmail.com  / 4791103600 )\r\n\r\n\r\n        2 stk Kjærlighet på pinne á kr 4.00 = kr 8.00\r\n\r\nSum ordre ink MVA kr 8.00\r\nHerav MVA kr 0.00\r\n\r\nDenne e-posten er sendt fra Tidypay (tidypay.no).\r\n'

order_number = re.search(r'Ordrenummer:\s+(\d+)', a).group(1)
print(order_number)

# Extracting invoice number (unused in Transaction, included for completeness)
invoice_number = re.search(r'Fakturanummer:\s+(\d+)', a).group(1)
print(invoice_number)

# Extracting date and time
# datetime = re.search(r'Dato og tid:\s+([\d:\s-]+)', a).group(1)
datetime = re.search(r'Dato og tid:\s+([-\d:\s]+)', a).group(1)
print(datetime.strip())

# Extracting customer name and email
name_email_match = re.search(r'Kunde:\s+(.*?)\s+\(\s*(.*?)\s*/', a)
name, email_addr = name_email_match.group(1), name_email_match.group(2)
print(name)
print(email_addr)

# Extracting amount (Sum ordre ink MVA)
amount = int(float(re.search(r'Sum ordre ink MVA kr\s+(\d+.\d+)', a).group(1)))

print(amount)
# Assuming the product description is consistent for parsing
product_description = re.search(r'(\d+ stk [^\=]+=\s+kr\s+\d+.\d+)', a).group(1)
print(product_description)