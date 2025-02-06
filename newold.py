import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from collections import Counter

# Set Page Config
st.set_page_config(page_title="Flipkart Web Scraper", layout="wide")

# Sidebar Login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.sidebar.title("🔐 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username == "adminSaheli" and password == "25@das20":
            st.session_state["logged_in"] = True
            st.sidebar.success("✅ Logged in successfully!")
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid credentials. Try again.")

# Show App Functionality Only If Logged In
if st.session_state["logged_in"]:
    # Sidebar Navigation
    st.sidebar.title("📌 Navigation")
    tab = st.sidebar.radio("Go to", ["🏠 Home", "📊 Key Metrics", "💰 Price Analysis", "🔽 Discount Analysis", "⭐ Ratings Analysis", "🔠 Text Analysis"])


    # Function to Scrape Data
    def scrape_data(url, n):
        products = []
        for i in range(1, n + 1):
            page_url = f"{url}&page={i}"
            response = requests.get(page_url)

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "lxml")
            mine = soup.find("div", class_="DOjaWF gdgoEp")
            product_containers = mine.find_all('div', class_=['tUxRFH', 'slAVV4', '_1sdMkc LFEi7Z']) if mine else []

            for container in product_containers:
                name = container.find(["div", "a"], class_=['WKTcLC BwBZTg','WKTcLC','wjcEIp','ZHvV68','KzDlHZ'])
                price = container.find("div", class_=['J5MN75','Nx9bqj','Nx9bqj _4b5DiR','Nx9bqj OQ4U3k'])
                ratings = container.find("div", class_=re.compile(r"XQDdHH"))
                mrp = container.find("div", class_=['yRaY8j','yRaY8j ZYYwLA'])
                discount=container.find("div",class_='UkUFwK')
                reviews = container.find("span", class_=['Wphh3N','&nbsp'])

                product = {
                    "Product Name": name.text.strip() if name else "N/A",
                    "Price(₹)": price.text.strip().replace("₹", "").replace(",", "") if price else None,
                    "Ratings": ratings.text.strip() if ratings else None,
                    "MRP(₹)": mrp.text.strip().replace("₹", "").replace(",", "") if mrp else None,
                    "Discount(%)":discount.text.strip().replace("%","").replace("off","") if discount else None,
                    "No. of Reviews": re.search(r"(\d[\d,]*)\s*Reviews", reviews.text.strip()).group(1).replace(",", "") if reviews and re.search(r"(\d[\d,]*)\s*Reviews", reviews.text.strip()) else "0",

                }

                products.append(product)

        if products:
            df = pd.DataFrame(products)
            df["Price(₹)"] = pd.to_numeric(df["Price(₹)"], errors="coerce")
            df["Ratings"] = pd.to_numeric(df["Ratings"], errors="coerce")
            df["MRP(₹)"] = pd.to_numeric(df["MRP(₹)"], errors="coerce", downcast='integer')
            df["Discount(%)"]=pd.to_numeric(df["Discount(%)"],errors="coerce")
            df["No. of Reviews"] = pd.to_numeric(df["No. of Reviews"], errors="coerce", downcast='integer')
            df.dropna(subset=["Price(₹)"], inplace=True)
            return df
        return None

    # Home Page
    if tab == "🏠 Home":
        st.title("🛒 Flipkart Web Scraper")
        st.markdown("### **Enter a Flipkart product URL to scrape product data, including prices, ratings, and reviews.**")

        url = st.text_input("🔗 Enter Flipkart Product URL:")
        n = st.number_input("📄 Number of pages to scrape:", min_value=1, max_value=20, value=5, step=1)

        if st.button("🚀 Scrape Data"):
            if url:
                st.write("⏳ Fetching data...")
                df = scrape_data(url, n)
                if df is not None:
                    st.success("✅ Data scraped successfully!")
                    st.write("### **All Scraped Data:**")
                    st.dataframe(df)  # Shows the entire dataset

                    st.session_state["df"] = df  # Save dataframe for later use
                else:
                    st.error("❌ No valid product data found.")
            else:
                st.error("❌ Please enter a valid URL.")

    # Key Metrics Page
    elif tab == "📊 Key Metrics":
        st.markdown("<h2 style='background-color:blue; color:white; padding:10px;'>📊 Key Business Metrics</h2>", unsafe_allow_html=True)

        if "df" in st.session_state:
            df = st.session_state["df"]

            st.metric("Total products", len(df))
            st.metric("Average price", f"₹ {df['Price(₹)'].mean():,.2f}")
            st.metric("Average ratings", f"{df['Ratings'].mean():.2f}")
            st.metric("Most expensive product", df.loc[df["Price(₹)"].idxmax(), "Product Name"])
            st.metric("Cheapest product", df.loc[df["Price(₹)"].idxmin(), "Product Name"])

    # Price Analysis Page
    elif tab == "💰 Price Analysis":
        st.markdown("<h2 style='background-color:blue; color:white; padding:10px;'>💰 Price Analysis</h2>", unsafe_allow_html=True)

        if "df" in st.session_state:
            df = st.session_state["df"]

            # Ensure "Price" is numeric and handle errors gracefully
            df["Price(₹)"] = pd.to_numeric(df["Price(₹)"], errors="coerce")  # Convert to numeric, coerce errors to NaN
            df.dropna(subset=["Price(₹)"], inplace=True)  # Remove rows where "Price" is NaN

            # Price Distribution Histogram
            st.write("### 📊 Price Distribution")
            fig, ax = plt.subplots()
            sns.histplot(df["Price(₹)"], bins=20, kde=True, color="blue", ax=ax)
            st.pyplot(fig)

            # Display the 5 most expensive products
            st.write("### 📈 Top 5 Most Expensive Products")
            top_5_expensive = df.nlargest(5, 'Price(₹)')[["Product Name", "Price(₹)"]]
            st.dataframe(top_5_expensive)

            # Identifying and displaying outliers based on IQR
            st.write("### 🚨 Outliers Based on Price")
            
            # Calculate IQR for outlier detection
            Q1 = df["Price(₹)"].quantile(0.25)
            Q3 = df["Price(₹)"].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            # Filter out the outliers
            outliers = df[(df["Price(₹)"] < lower_bound) | (df["Price(₹)"] > upper_bound)]
            st.dataframe(outliers)

    # Discount Analysis Page
    elif tab == "🔽 Discount Analysis":
        st.markdown("<h2 style='background-color:blue; color:white; padding:10px;'>🔽 Discount Analysis</h2>", unsafe_allow_html=True)

        if "df" in st.session_state:
            df = st.session_state["df"]

            # Ensure "Discount(%)" is numeric and handle errors gracefully
            df["Discount(%)"] = pd.to_numeric(df["Discount(%)"], errors="coerce")  # Convert to numeric
            df.dropna(subset=["Discount(%)"], inplace=True)  # Remove rows where "Discount" is NaN

            # Discount Distribution Histogram
            st.write("### 📊 Discount Distribution")
            fig, ax = plt.subplots()
            sns.histplot(df["Discount(%)"], bins=20, kde=True, color="purple", ax=ax)
            st.pyplot(fig)

            # Display the 5 most discounted products
            st.write("### 🔝 Top 5 Highest Discounted Products")
            top_5_discounts = df.nlargest(5, 'Discount(%)')[["Product Name", "Discount(%)", "Price(₹)", "MRP(₹)"]]
            st.dataframe(top_5_discounts)

            # Price vs. Discount Relationship
            st.write("### 💰 Price vs. Discount Relationship")
            fig, ax = plt.subplots()
            sns.scatterplot(x=df["MRP(₹)"], y=df["Discount(%)"], color="red", alpha=0.6, ax=ax)
            ax.set_xlabel("MRP (₹)")
            ax.set_ylabel("Discount (%)")
            st.pyplot(fig)
        

    # Ratings Analysis Page
    elif tab == "⭐ Ratings Analysis":
        st.markdown("<h2 style='background-color:blue; color:white; padding:10px;'>⭐ Ratings Analysis</h2>", unsafe_allow_html=True)

        if "df" in st.session_state:
            df = st.session_state["df"]

            # Ensure "Ratings" is numeric and handle errors gracefully
            df["Ratings"] = pd.to_numeric(df["Ratings"], errors="coerce")  # Convert to numeric, coerce errors to NaN
            df.dropna(subset=["Ratings"], inplace=True)  # Remove rows where "Ratings" is NaN

            # Ratings Distribution Histogram
            st.write("### 📊 Ratings Distribution")
            fig, ax = plt.subplots()
            sns.histplot(df["Ratings"], bins=10, kde=True, color="green", ax=ax)
            st.pyplot(fig)

            # Display the 5 highest rated products
            st.write("### ⭐ Top 5 Highest Rated Products")
            top_5_rated = df.nlargest(5, 'Ratings')[["Product Name", "Ratings"]]
            st.dataframe(top_5_rated)

    # Text Analysis Page
    elif tab == "🔠 Text Analysis":
        st.markdown("<h2 style='background-color:blue; color:white; padding:10px;'>🔠 Text Analysis</h2>", unsafe_allow_html=True)

        if "df" in st.session_state:
            df = st.session_state["df"]

            text = " ".join(df["Product Name"].dropna().astype(str))
            words = re.findall(r"\b\w+\b", text.lower())
            word_freq = Counter(words).most_common(10)

            word_df = pd.DataFrame(word_freq, columns=["Word", "Frequency"])

            st.write("### 📊 Most Common Words in Product Names")
            fig, ax = plt.subplots()
            sns.barplot(x="Word", y="Frequency", data=word_df, ax=ax, hue="Word", palette="viridis", legend=False)

            st.pyplot(fig)