import streamlit as st
import pandas as pd
import re
from datetime import datetime
from io import BytesIO
from urllib.parse import unquote

def clean_phone(num):
    return re.sub(r'\D', '', str(num)) if pd.notnull(num) else ''

def process_dataframe(df, start_date, message, mobile_mode=False):
    DATE_COLUMN = "LICENSE_START_DATE"
    PHONE_COLUMN = "PHONE"

    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors='coerce')
    df = df[df[DATE_COLUMN] >= start_date].copy()
    df[PHONE_COLUMN] = df[PHONE_COLUMN].apply(clean_phone)
    df = df[df[PHONE_COLUMN].str.strip() != '']
    pattern = r'^(9710|9715|5|05)'
    df = df[df[PHONE_COLUMN].str.match(pattern)]
    df[PHONE_COLUMN] = df[PHONE_COLUMN].apply(lambda num: num if num.startswith('971') else '971' + num)
    df[PHONE_COLUMN] = df[PHONE_COLUMN].apply(lambda num: num.replace('97105', '9715', 1) if num.startswith('97105') else num)
    df = df[df[PHONE_COLUMN].str.len() == 12]
    df = df.sort_values(DATE_COLUMN, ascending=False)
    df = df.drop(columns=[col for col in ['GENDER_EN', 'LICENSE_END_DATE', 'WEBPAGE', 'FAX', 'REAL_ESTATE_NUMBER'] if col in df.columns])

    # WhatsApp Link: mobile (whatsapp://send) or desktop (web.whatsapp.com)
    if mobile_mode:
        # decode message so emojis show up on the phone
        message_plain = unquote(message)
        whatsapp_urls = (
            "https://wa.me/" + df[PHONE_COLUMN] + "?text=" + message_plain
        )
    else:
        whatsapp_urls = (
            "https://web.whatsapp.com/send?phone=" + df[PHONE_COLUMN] + "&text=" + message
        )
    df["WHATSAPP"] = whatsapp_urls

    # For mobile: only show minimal columns
    if mobile_mode:
        possible_broker_cols = [col for col in df.columns if "BROKER" in col.upper() or "NAME" in col.upper()]
        broker_col = possible_broker_cols[0] if possible_broker_cols else None
        selected_cols = [col for col in [broker_col, DATE_COLUMN, PHONE_COLUMN, "WHATSAPP"] if col in df.columns]
        df = df[selected_cols]
    else:
        # Move WhatsApp to end
        columns = [col for col in df.columns if col != "WHATSAPP"] + ["WHATSAPP"]
        df = df[columns]
    return df

st.set_page_config(
    page_title="Dubai Brokers Cleanup",
    page_icon="🏙️",
    layout="centered"
)

st.title("Dubai Brokers CSV Cleanup")

st.markdown(
    """
    **You can download the latest brokers.csv here:**
    [Dubai Land Department – Real Estate Data](https://dubailand.gov.ae/en/open-data/real-estate-data/)

    :point_right: After opening the page, please click on the **'Broker'** tab to download the correct file.
    """
)

uploaded_file = st.file_uploader("Upload your brokers.csv", type=["csv"])

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

message_choice = st.selectbox("Which message should be used?", ["Cine", "Vero"])
if message_choice == "Cine":
    message = message_cine
    default_filename = "brokers-cleaned_cine.xlsx"
else:
    message = message_vero
    default_filename = "brokers-cleaned_vero.xlsx"

mobile_mode = st.checkbox("Mobile-friendly version", value=False)

start_date = st.date_input("Choose the start date", value=datetime.today())
start_date = pd.to_datetime(start_date)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df_result = process_dataframe(df, start_date, message, mobile_mode)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, index=False, sheet_name='BROKERS')
        workbook = writer.book
        worksheet = writer.sheets['BROKERS']
        header_format = workbook.add_format({'bold': True})
        for col_num, value in enumerate(df_result.columns):
            worksheet.write(0, col_num, value.upper(), header_format)
        for i, column in enumerate(df_result.columns):
            if column == "WHATSAPP":
                worksheet.set_column(i, i, 20)
            else:
                values = df_result[column].dropna().astype(str)
                max_len = max([len(column)] + [len(v) for v in values]) + 2
                worksheet.set_column(i, i, max_len)
        whatsapp_col = df_result.columns.get_loc("WHATSAPP")
        for row_num, url in enumerate(df_result["WHATSAPP"], start=1):
            worksheet.write_url(row_num, whatsapp_col, url, string="Send WhatsApp")
    output.seek(0)
    st.success("Done! Download your Excel file below:")
    st.download_button(
        label="Download cleaned Excel",
        data=output,
        file_name=default_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
