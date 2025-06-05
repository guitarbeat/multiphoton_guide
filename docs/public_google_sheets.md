# Using a Public Google Sheet with Streamlit

This guide walks through connecting your Streamlit application to a public Google Sheet using `st.connection` and the `streamlit-gsheets-connection` package. It summarizes the steps from [Streamlit's tutorial](https://docs.streamlit.io/develop/tutorials/databases/public-gsheet).

## Prerequisites

- **Streamlit** version `1.28` or newer
- **Python package** `st-gsheets-connection` installed

Install the package with:

```bash
pip install st-gsheets-connection
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

Use `st.connection` to create a connection and call `.read()` to retrieve the data or
`conn.update()` to write data back:

```python
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Create a connection object
conn = st.connection("gsheets", type=GSheetsConnection)

# Read a worksheet by name
df = conn.read(worksheet="Sheet1")

# Display the results
for row in df.itertuples():
    st.write(f"{row.name} has a :{row.pet}:")

## 4. Write data back to the Sheet

```python
new_df = pd.DataFrame({"name": ["Lucia"], "pet": ["dog"]})
conn.update(worksheet="Sheet1", data=new_df)
```

## Optional: customize caching and range

`st.connection` caches `.read()` by default. You can adjust parameters such as the worksheet, columns, number of rows, and cache duration:

```python
df = conn.read(
    worksheet="Sheet1",
    ttl="10m",    # cache results for at most 10 minutes
    usecols=[0, 1],
    nrows=3,
)
```

Set `ttl=0` to disable caching entirely if needed.

## 5. Deploying on Streamlit Community Cloud

When deploying to Streamlit Community Cloud:

1. Include `st-gsheets-connection` in your `requirements.txt`.
2. Add the same `[connections.gsheets]` section in your app's Secrets configuration on Cloud.

Your app can then read from the public Google Sheet in the same way as locally.

---

Following these steps lets you pull data from a public Google Sheet without storing credentials in your code. `st.connection` handles secrets, caching, and retries for you.
