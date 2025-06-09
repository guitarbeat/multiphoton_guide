# Using a Public Google Sheet with Streamlit

This guide walks through connecting your Streamlit application to a public Google Sheet using [`gspread`](https://pypi.org/project/gspread/).

## Prerequisites

- **Streamlit** version `1.28` or newer
- **Python package** `gspread` installed

Install the package with:

```bash
pip install gspread gspread-dataframe
```

## 1. Create a Google Sheet and enable link sharing

1. Create a spreadsheet in Google Sheets (or open an existing one).
2. Share it using **Anyone with the link** set to **Viewer**.
3. Copy the share URL.

## 2. Store the Sheet URL in Streamlit secrets

Create (or update) `.streamlit/secrets.toml` in your project and add the link:

```toml
# .streamlit/secrets.toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/XXXXXX/edit#gid=0"
```

## 3. Read data from the Sheet in your app

Use `gspread` to authenticate and read data:


```python
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe

creds = st.secrets["connections"]["gsheets"]
client = gspread.service_account_from_dict(creds)
sheet = client.open_by_url(creds["spreadsheet"])
worksheet = sheet.worksheet("Sheet1")
df = get_as_dataframe(worksheet)

# Display the results
for row in df.itertuples():
    st.write(f"{row.name} has a :{row.pet}:")
## 4. Write data back to the Sheet

```python
new_df = pd.DataFrame({"name": ["Lucia"], "pet": ["dog"]})
set_with_dataframe(worksheet, new_df, include_index=False, resize=True)

```

## Optional: customize caching and range

`gspread` does not cache requests by default. Use Streamlit caching utilities if needed.

## 5. Deploying on Streamlit C

When deploying to Streamlit Community Cloud:

1. Include `gspread` in your `requirements.txt`.
2. Add the same `[connections.gsheets]` section in your app's Secrets configuration on Cloud.

Your app can then read from the public Google Sheet in the same way as locally.

---

Following these steps lets you pull data from a public Google Sheet without storing credentials in your code. Combine `gspread` with Streamlit's caching utilities for optimal performance.
