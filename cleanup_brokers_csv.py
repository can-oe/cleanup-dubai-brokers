import pandas as pd
import re
from datetime import datetime

INPUT_CSV = "brokers.csv"
DATE_COLUMN = "LICENSE_START_DATE"
PHONE_COLUMN = "PHONE"

def clean_phone(num):
    return re.sub(r'\D', '', str(num))  # Sonderzeichen entfernen

def main():
    # Zeitraum eingeben
    start_date = input("Bitte Startdatum angeben (YYYY-MM-DD): ")
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        print("Ungültiges Datum!")
        return

    # CSV einlesen
    df = pd.read_csv(INPUT_CSV)

    # Nach Datum filtern
    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors='coerce')
    df = df[df[DATE_COLUMN] >= start_dt].copy()

    # 1. Sonderzeichen entfernen
    df[PHONE_COLUMN] = df[PHONE_COLUMN].apply(clean_phone)

    # 2. Leere Nummern entfernen
    df = df[df[PHONE_COLUMN].str.strip() != '']

    # 3. Nur Nummern, die mit 9710, 9715, 5 oder 05 beginnen
    pattern = r'^(9710|9715|5|05)'
    df = df[df[PHONE_COLUMN].str.match(pattern)]

    # 4. Füge '971' am Anfang hinzu, wenn nicht vorhanden
    df[PHONE_COLUMN] = df[PHONE_COLUMN].apply(lambda num: num if num.startswith('971') else '971' + num)

    # 5. '97105' → '9715'
    df[PHONE_COLUMN] = df[PHONE_COLUMN].apply(lambda num: num.replace('97105', '9715', 1) if num.startswith('97105') else num)

    # 6. Nur 12-stellige Nummern behalten
    df = df[df[PHONE_COLUMN].str.len() == 12]

    # 7. Sortieren
    df = df.sort_values(DATE_COLUMN, ascending=False)

    # 8. Unnötige Spalten löschen
    df = df.drop(columns=[col for col in ['GENDER_EN', 'LICENSE_END_DATE', 'WEBPAGE', 'FAX', 'REAL_ESTATE_NUMBER'] if col in df.columns])

    # 9. WhatsApp-Messages
    message_cine = (
        "Hi%2C+this+is+Cinare+from+Danube+Properties+%F0%9F%98%8A%0A%0A"
        "I+hope+you%E2%80%99re+doing+well.%0A%0A"
        "Just+wanted+to+quickly+reach+out+and+see+if+you%E2%80%99re+currently+working+with+Danube+%E2%80%94+or+open+to+new+opportunities%3F%0A%0A"
        "Even+if+you+already+have+a+Danube+contact%2C+working+with+me+could+offer+extra+value+%E2%80%94+especially+since+I+speak+German+%F0%9F%87%A9%F0%9F%87%AA+and+Turkish+%F0%9F%87%B9%F0%9F%87%B7%2C+which+can+be+a+big+advantage+with+European+clients.%0A%0A"
        "You+can+also+check+out+all+the+latest+projects+on+my+personal+website%3A+https%3A%2F%2Fwww.cinarezamanli.com%0A%0A"
        "So+when+can+we+schedule+a+quick+call%3F+%F0%9F%98%8A"
    )
    message_vero = (
        "Hey%2C+this+is+Veronika+from+DAR+Global+%E2%80%93+a+luxury+real+estate+developer.%0A%0A"
        "Hope+you%E2%80%99re+doing+well%21%0AJust+wanted+to+check+if+you%E2%80%99re+already+working+with+us+%E2%80%93+or+open+to+new+opportunities%3F%0A%0A"
        "You+might+know+us+from+our+villas+in+JGE+%F0%9F%8F%A1+or+the+Trump+Tower+on+SZR+%F0%9F%8F%99%EF%B8%8F%0A%0A"
        "I+speak+German+%F0%9F%87%A9%F0%9F%87%AA+Russian+%F0%9F%87%B7%F0%9F%87%BA+and+can+support+you+with+international+clients+%F0%9F%98%83%0A%0A"
        "So+when+can+we+schedule+a+quick+briefing+to+close+some+deals%3F%F0%9F%98%8A"
    )

    print("Welche Message soll verwendet werden?")
    print("1. Cine")
    print("2. Vero")
    wahl = input("Bitte 1 oder 2 eingeben: ").strip()
    if wahl == '1':
        message = message_cine
        OUTPUT_EXCEL = "brokers-bereinigt_cine.xlsx"
    else:
        message = message_vero
        OUTPUT_EXCEL = "brokers-bereinigt_vero.xlsx"

    whatsapp_urls = (
        "https://web.whatsapp.com/send?phone="
        + df[PHONE_COLUMN]
        + "&text=" + message
    )

    # WhatsApp-Spalte einfügen
    df["WHATSAPP"] = whatsapp_urls

    # --- Excel mit Formatierung ---
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Brokers')
        workbook = writer.book
        worksheet = writer.sheets['Brokers']

        # Überschriften fett und in CAPS
        header_format = workbook.add_format({'bold': True})
        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num, value.upper(), header_format)

        # Spaltenbreite automatisch anpassen
        for i, column in enumerate(df.columns):
            if column == "WHATSAPP":
                worksheet.set_column(i, i, 20)  # Breite für WhatsApp-Spalte
            else:
                max_len = max([len(str(s)) for s in df[column].values] + [len(column)]) + 2
                worksheet.set_column(i, i, max_len)

        # WhatsApp-Link als Hyperlink setzen
        whatsapp_col = df.columns.get_loc("WHATSAPP")
        for row_num, url in enumerate(df["WHATSAPP"], start=1):
            worksheet.write_url(row_num, whatsapp_col, url, string="WhatsApp senden")

    print(f"Bereinigte Datei gespeichert als: {OUTPUT_EXCEL}")

if __name__ == "__main__":
    main()
