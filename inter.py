from sqlalchemy import create_engine, text
import pandas as pd
import streamlit as st
import base64

# Ensure you have 'psycopg2' installed:
# pip install psycopg2-binary

# Database connection function using SQLAlchemy
def get_connection():
    engine = create_engine('postgresql://myadmin:passme@localhost/project')
    return engine

# Fetch flights from the database
def fetch_flight():
    query = """
    SELECT FlightID, Airline || ' from ' || Origin || ' to ' || Destination || 
    ' departs at ' || TO_CHAR(DepartureTime, 'YYYY-MM-DD HH24:MI') || 
    ' arrives at ' || TO_CHAR(ArrivalTime, 'YYYY-MM-DD HH24:MI') ||
    ', Price: $' || Price AS FlightDetails 
    FROM Flight;
    """
    df = pd.read_sql(query, get_connection())
    return df

# Fetch hotels from the database
def fetch_hotel():
    query = "SELECT HotelID, Name || ', ' || Location || ', $' || PricePerNight || ' per night' || ',' || personperroom || ' person per room' AS HotelDetails FROM Hotel;"
    df = pd.read_sql(query, get_connection())
    return df

# Fetch rental cars from the database
def fetch_rental_car():
    query = "SELECT RentalID, Company || ' - ' || Model || ', ' || Location || ', $' || PricePerDay || ' per day' || ',' || passangercapacity || ' person capacity' AS RentalDetails FROM RentalCar;"
    df = pd.read_sql(query, get_connection())
    return df

# Fetch restaurants from the database
def fetch_restaurant():
    query = "SELECT RestaurantID, Name || ', ' || Location || ', ' || Cuisine || ', ' || PriceRange || ', Rating: ' || Rating AS RestaurantDetails FROM Restaurant;"
    df = pd.read_sql(query, get_connection())
    return df

# Function to insert booking into the database
def insert_booking(customer_details, flight_id, hotel_id, rental_id, restaurant_id):
    with get_connection().connect() as conn:
        trans = conn.begin()
        try:
            customer_query = text("""
            INSERT INTO Customers (Name, Email, PhoneNumber, Cardnumber)
            VALUES (:name, :email, :phone, :cardnumber)
            RETURNING CustomerID;
            """)
            result = conn.execute(customer_query, customer_details)
            customer_id = result.fetchone()[0]

            booking_query = text("""
            INSERT INTO Bookings (CustomerID, FlightID, HotelID, RentalID, RestaurantID, BookingDate)
            VALUES (:customer_id, :flight_id, :hotel_id, :rental_id, :restaurant_id, CURRENT_DATE)
            RETURNING BookingID;
            """)
            booking_params = {
                'customer_id': customer_id,
                'flight_id': flight_id,
                'hotel_id': hotel_id,
                'rental_id': rental_id,
                'restaurant_id': restaurant_id
            }
            booking_result = conn.execute(booking_query, booking_params)
            booking_id = booking_result.fetchone()[0]

            trans.commit()
            return f"Booking successful! Booking ID: {booking_id}"
        except Exception as e:
            trans.rollback()
            return f"An error occurred while making the booking: {e}"

# Add custom CSS for background images
background_image = {
    "Flight": "images/flight.jpg",
    "Hotel": "images/hotel.jpg",
    "Rental Car": "images/rentalcar.jpeg",
    "Restaurant": "images/rest.jpg",
    "Bookings": "images/booking.jpeg"  # Updated to use booking.jpg
}

def set_background(image_file):
    with open(image_file, "rb") as image:
        b64 = base64.b64encode(image.read()).decode()
        st.markdown(
            f"""
            <style>
            .main {{
                background-image: url("data:image/jpg;base64,{b64}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

# Sidebar for navigation
selected_option = st.sidebar.selectbox(
    "Choose a category",
    ["Flight", "Hotel", "Rental Car", "Restaurant", "Bookings"],
    index=0
)

st.title("Paradise Tours")

# Set the background image based on the selected option
set_background(background_image[selected_option])

# Display content based on selected category
if selected_option == "Flight":
    st.subheader("Available Flights")
    st.dataframe(fetch_flight())

elif selected_option == "Hotel":
    st.subheader("Available Hotels")
    st.dataframe(fetch_hotel())

elif selected_option == "Rental Car":
    st.subheader("Available Rental Cars")
    st.dataframe(fetch_rental_car())

elif selected_option == "Restaurant":
    st.subheader("Available Restaurants")
    st.dataframe(fetch_restaurant())

elif selected_option == "Bookings":
    st.subheader("Make a Booking")
    name = st.text_input("Name", key="name")
    email = st.text_input("Email", key="email")
    phone = st.text_input("Phone", key="phone")
    cardnumber = st.text_input("Cardnumber", key="cardnumber")
    flight_id = st.text_input("Flight ID", key="flight_id")
    hotel_id = st.text_input("Hotel ID", key="hotel_id")
    rental_id = st.text_input("Rental Car ID", key="rental_id")
    restaurant_id = st.text_input("Restaurant ID", key="restaurant_id")
    if st.button('Book Now', key='book_button'):
        try:
            flight_id = int(flight_id) if flight_id.isdigit() else None
            hotel_id = int(hotel_id) if hotel_id.isdigit() else None
            rental_id = int(rental_id) if rental_id.isdigit() else None
            restaurant_id = int(restaurant_id) if restaurant_id.isdigit() else None
            result = insert_booking({'name': name, 'email': email, 'phone': phone, 'cardnumber': cardnumber}, flight_id, hotel_id, rental_id, restaurant_id)
            st.success(result)
        except ValueError:
            st.error("Please enter valid numeric IDs.")
        except Exception as e:
            st.error(f"An error occurred while making the booking: {e}")
