import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from PIL import Image
import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Initialize the Streamlit app
st.set_page_config(page_title="Planner App", page_icon="🌍", layout="wide")

# Load the API Key
load_dotenv()
genai.configure(api_key=os.getenv("key"))

# Google Calendar API Setup
SERVICE_ACCOUNT_FILE = 'gen-lang-client-0445774123-4a187b86b57d.json'  # Replace with your actual file
SCOPES = ['https://www.googleapis.com/auth/calendar']

creds = None
try:
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    st.write("Google Calendar service initialized.")
except FileNotFoundError:
    st.error("Service account file not found. Please upload it.")
    creds = None
except Exception as e:
    st.error(f"An error occurred during Google Calendar setup: {e}")
    st.error(f"Full Exception: {e}")
    creds = None

# Function to load Google Gemini Vision Model and get response
def get_response_image(image, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([image[0], prompt])
    return response.text

# Function to load Google Gemini Pro Model and get response
def get_response(prompt, input):
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    response = model.generate_content([prompt, input])
    return response.text

# Prep Image Data
def prep_image(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [{"mime_type": uploaded_file.type, "data": bytes_data}]
        return image_parts
    else:
        raise FileNotFoundError("No File is uploaded!")

# Function to add event to Google Calendar
def add_event_to_calendar(summary, description, start_time, end_time):
    if creds:
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
        }
        try:
            st.write(f"Attempting to add event: {event}")  # Debugging line
            event = service.events().insert(calendarId='primary', body=event).execute() # changed calendarID to primary
            st.success(f"Event created: {event.get('htmlLink')}")
        except Exception as e:
            st.error(f"Failed to add event to calendar: {e}")
            st.error(f"Full Exception: {e}")  # More detailed error
    else:
        st.error("Google Calendar credentials not set up.")

# Add Background Image
page_bg_img = '''
<style>
.stApp {
    background-image: url("https://64.media.tumblr.com/f6d849f74aa1c67193d8d0a08f0b89e6/tumblr_pt41e8eELy1uvsi7jo1_1280.gifv");
    background-size: cover;
}
</style>
'''
st.markdown(page_bg_img, unsafe_allow_html=True)

st.image('logo.png', width=400)
st.title("Planner: Discover and Plan Your Adventures! 🌟")

# Sidebar Navigation
st.sidebar.header("Navigation")
section_choice = st.sidebar.radio("Choose Section:", ("Location Finder", "Trip Planner", "Weather Forecasting", "Restaurant & Hotel Planner"))

st.markdown("---")

if section_choice == "Location Finder":
    st.subheader("📍 Location Finder")
    upload_file = st.file_uploader("Upload an image of a location", type=["jpg", "jpeg", "png"])
    if upload_file is not None:
        image = Image.open(upload_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

    input_prompt_loc = """
    You are an expert Tourist Guide. Provide:
    - Summary of the place
    - Location details
    - State & Capital
    - Coordinates
    - Popular nearby places
    """
    if st.button("🔍 Get Location"):
        image_data = prep_image(upload_file)
        response = get_response_image(image_data, input_prompt_loc)
        st.subheader("🏞 Tour Bot:")
        st.write(response)

elif section_choice == "Trip Planner":
    st.subheader("🗺 Trip Planner")
    input_prompt_planner = """
    You are an expert Tour Planner. Provide recommendations for the given location and days.
    - Suggest hidden gems, hotels, must-visit places
    - Best time to visit
    """
    input_plan = st.text_area("Enter location and number of days:")
    if st.button("📅 Plan My Trip"):
        response = get_response(input_prompt_planner, input_plan)
        st.subheader("🧳 Planner Bot:")
        st.write(response)

        # Add Google Calendar integration
        if creds:
            if st.checkbox("Add to Google Calendar"):
                trip_details = response
                start_date = st.date_input("Start Date", datetime.date.today())
                num_days = int(input_plan.split("days")[0].split()[-1])
                end_date = start_date + datetime.timedelta(days=num_days)

                start_time = datetime.datetime.combine(start_date, datetime.time(9, 0))
                end_time = datetime.datetime.combine(end_date, datetime.time(17, 0))

                add_event_to_calendar("Trip to " + input_plan.split("days")[0].split()[0], trip_details, start_time, end_time)

elif section_choice == "Weather Forecasting":
    st.subheader("🌤 Weather Forecasting")
    input_prompt_weather = """
    You are an expert weather forecaster. Provide a 7-day forecast for the given location, including:
    - Precipitation
    - Humidity
    - Wind conditions
    - Air Quality
    - Cloud Cover
    """
    input_plan = st.text_area("Enter location for weather forecast:")
    if st.button("🌦 Get Forecast"):
        response = get_response(input_prompt_weather, input_plan)
        st.subheader("🌍 Weather Bot:")
        st.write(response)

elif section_choice == "Restaurant & Hotel Planner":
    st.subheader("🍽 Restaurant & Hotel Planner")
    input_prompt_hotel = """
    You are an expert in Restaurant & Hotel Planning. Provide:
    - Top 5 restaurants (address & avg cost per cuisine)
    - Top 5 hotels (address & avg cost per night)
    - Balanced options (not too expensive or cheap)
    """
    input_plan = st.text_area("Enter location to find Hotels & Restaurants:")
    if st.button("🏨 Find Places"):
        response = get_response(input_prompt_hotel, input_plan)
        st.subheader("🍴 Accommodation Bot:")
        st.write(response)

st.markdown("---")