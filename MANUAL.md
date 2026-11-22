# Harvesta Uganda Manual

## 1. Start the app

1. Open a terminal in the Harvesta project folder.
2. Activate the environment:
   - Windows PowerShell: `.\venv\Scripts\Activate.ps1`
3. Install dependencies: `pip install -r requirements.txt`
4. Create the Uganda demo data: `python seed_uganda.py`
5. Start the API: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
6. Open a second terminal.
7. Start the website: `python -m streamlit run streamlit_app/Home.py --server.port 8501`
8. Open `http://localhost:8501`.

## 2. Create an account

1. Open the menu from the left side of the home screen.
2. Select **Create account**.
3. Enter full name, +256 phone number, Gmail address and password.
4. Enter the district or address.
5. Enter GPS latitude and longitude if known.
6. Select Buyer, Farmer, Driver or Shop Manager.
7. Select **Create account**.

## 3. Sign in

Use a registered Gmail address or +256 phone number as the login identifier, plus your password.

## 4. Browse and order

1. Open **Marketplace**.
2. Use category or search filters.
3. Set quantity and select **Add to Cart**.
4. Enter delivery address and notes.
5. Select **Place Order**.
6. Open **Orders and Deliveries** to view the order.

## 5. Farmer tools

1. Sign in as a farmer.
2. Open **My Farm**.
3. Register a farm with location and GPS coordinates.
4. Open **List a new product**.
5. Enter quantity, unit and UGX price.
6. Publish the product.

## 6. Weather

1. Open **Farm Weather**.
2. Select a district or enter GPS coordinates.
3. Select **Get forecast**.
4. Review temperature, humidity, rainfall and seven-day rain probability.

## 7. Veterinary care

1. Sign in.
2. Open **Veterinary**.
3. Filter by district.
4. Select an animal and describe the symptoms.
5. Select a preferred date and request the visit.

## 8. Dark mode

Open the left menu and switch **Dark mode** on or off.

## Demo accounts

- Buyer: `buyer@harvesta.ug` / `buyer123`
- Farmer: `farmer@harvesta.ug` / `farmer123`
- Driver: `driver@harvesta.ug` / `driver123`
- Shop manager: `shop@harvesta.ug` / `shop123`
