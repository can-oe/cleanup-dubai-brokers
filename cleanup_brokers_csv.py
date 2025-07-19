import pandas as pd
import re
from datetime import datetime

INPUT_CSV = "brokers.csv"
DATE_COLUMN = "LICENSE_START_DATE"
PHONE_COLUMN = "PHONE"

def clean_phone(num):
    return re.sub(r'\D', '', str(num))  # remove non-digit characters

def main():
    # select start date
    start_date = input("Enter the start date (YYYY-MM-DD): ")
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        print("Invalid date!")
        return

    # read CSV
    df = pd.read_csv(INPUT_CSV)

    # filter by start date
    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors='coerce')
    df = df[df[DATE_COLUMN] >= start_dt].copy()

    # 1. remove non-digit characters from phone numbers
    df[PHONE_COLUMN] = df[PHONE_COLUMN].apply(clean_phone)

    # 2. remove empty phone numbers
    df = df[df[PHONE_COLUMN].str.strip() != '']

    # 3. only keep numbers starting with 9710, 9715, 5, or 05
    pattern = r'^(9710|9715|5|05)'
    df = df[df[PHONE_COLUMN].str.match(pattern)]

    # 4. add '971' prefix if missing
    df[PHONE_COLUMN] = df[PHONE_COLUMN].apply(lambda num: num if num.startswith('971') else '971' + num)

    # 5. '97105' → '9715'
    df[PHONE_COLUMN] = df[PHONE_COLUMN].apply(lambda num: num.replace('97105', '9715', 1) if num.startswith('97105') else num)

    # 6. only keep phone numbers with 12 digits
    df = df[df[PHONE_COLUMN].str.len() == 12]

    # 7. sort by start date
    df = df.sort_values(DATE_COLUMN, ascending=False)

    # 8. remove unnecessary columns
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

    print("Which message should be used?")
    print("1. Cine")
    print("2. Vero")
    choice = input("Please select 1 or 2: ").strip()
    if choice == '1':
        message = message_cine
        OUTPUT_EXCEL = "brokers-cleaned_cine.xlsx"
    else:
        message = message_vero
        OUTPUT_EXCEL = "brokers-cleaned_vero.xlsx"

    whatsapp_urls = (
        "https://web.whatsapp.com/send?phone="
        + df[PHONE_COLUMN]
        + "&text=" + message
    )

    # add WhatsApp column
    df["WHATSAPP"] = whatsapp_urls

    # format excel output
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='BROKERS')
        workbook = writer.book
        worksheet = writer.sheets['BROKERS']

        # write header in bold
        header_format = workbook.add_format({'bold': True})
        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num, value.upper(), header_format)

        # adjust column widths
        for i, column in enumerate(df.columns):
            if column == "WHATSAPP":
                worksheet.set_column(i, i, 20)  # wide for WhatsApp
            else:
                max_len = max([len(str(s)) for s in df[column].values] + [len(column)]) + 2
                worksheet.set_column(i, i, max_len)

        # set WhatsApp links as clickable URLs
        whatsapp_col = df.columns.get_loc("WHATSAPP")
        for row_num, url in enumerate(df["WHATSAPP"], start=1):
            worksheet.write_url(row_num, whatsapp_col, url, string="Send WhatsApp")

    print(f"Cleaned file saved as: {OUTPUT_EXCEL}")

if __name__ == "__main__":
    main()
