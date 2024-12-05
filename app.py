import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pyfonts import load_font
import time

#load and cache fonts
@st.cache_data(persist=True, show_spinner=False)
def load_fonts():
    font_b = load_font(
                    font_url='https://github.com/andrew-paglinawan/QuicksandFamily/blob/master/fonts/statics/Quicksand-Bold.ttf?raw=true'
                    )
    font_r = load_font(
                    font_url='https://github.com/andrew-paglinawan/QuicksandFamily/blob/master/fonts/statics/Quicksand-Regular.ttf?raw=true'
                    )
    font_m = load_font(
                    font_url='https://github.com/andrew-paglinawan/QuicksandFamily/blob/master/fonts/statics/Quicksand-Medium.ttf?raw=true'
                    )
    return(font_b, font_r, font_m)

@st.cache_data(persist=True, show_spinner=False)
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    return df

#---------------------------------------------------------------
#Main app--------------------------------------------------------
st.set_page_config(
    page_title="Strava unwrapped",
    page_icon="weight_lifter",
    #layout="wide",
     )

#session states
if "init" not in st.session_state:
    st.session_state["init"] = True
    st.session_state["is_csv"] = None
    st.session_state["upload_success"] = None
    #st.session_state["rerun"] = True
    st.session_state["FormSubmitter:user_inputs-Create visualisation"] = False

st.title('My year in sports')
st.markdown("\n")

#upload data
st.sidebar.subheader("Data upload")
with st.sidebar:
    uploaded_file = st.file_uploader("Upload your Strava csv file", 
                                    accept_multiple_files=False)
    
    if uploaded_file is None:
        st.session_state["is_csv"] = None
        st.session_state["upload_success"] = None
    
    if uploaded_file is not None:
        try:
            df = load_data(uploaded_file)
            st.session_state["is_csv"] = True    
        except UnicodeDecodeError:
            st.warning("Whoops, incorrect file format. Make sure to upload a `.csv` file to use this app")
            st.session_state["is_csv"] = False
            st.session_state["upload_success"]=False   

    #run check if correct file
    data_flag = False

    if st.session_state["is_csv"]==True:
        columns = df.columns
        expected_columns = ['Activity ID', 'Activity Date', 'Activity Name', 
                                'Activity Type', 'Distance.1', 'Moving Time']
        missing_columns = []
        for column in expected_columns:
            if column not in columns:
                data_flag=True
                missing_columns.append(column)
        if data_flag==True:
            st.warning("""
                    Whoops, your dataset doesn't look quite right ...\n
                    It's missing the following columns: {}\n
                    Check that the dataset matches the expected format                 
                    """.format(str(missing_columns)))
        if data_flag==False:
            st.session_state["upload_success"] = True
            with st.spinner('Uploading data ...'):

                #reduce to relevant columns
                df = df[expected_columns].rename(columns={"Distance.1":"Distance"})

                #convert date column into datetime
                df["Activity Date"] = pd.to_datetime(df["Activity Date"])

                #load fonts---------------------------
                font_b, font_r, font_m = load_fonts()

                #display success message
                st.success("Data upload successful")


#user inputs  
#submitted = None
st.write()
if st.session_state["upload_success"]==True:
    with st.form(key='user_inputs'):
        col1, col2 = st.columns(2)
        with col1:
            year_filter = st.selectbox(
                "Year",
                df["Activity Date"].dt.year.unique()
               #("Email", "Home phone", "Mobile phone"),
                )
        with col2:
            distance_unit = st.selectbox(
                "Distance unit",
                ("N/A","Kilometers","Miles"),
                help="Select 'N/A' if you don't want to visualise distance"
                )
        submitted = st.form_submit_button('Create visualisation')


#Chart functions---------------------------
#calculate dynamic axis ticks based on max time per month
def get_axis_ticks(max_sec):
        n_ticks=4
        if round(max_sec/n_ticks/60/60)>0:
            steps = 60*60*(round(max_sec/n_ticks/60/60))
        elif round(max_sec/n_ticks/60)>0:
            steps = 60*(round(max_sec/6/60))
        else:
            steps = n_ticks
        return steps

#convert seconds into nice format on chart
def convert_time(sec):
        hour = sec // 3600
        sec %= 3600
        min = sec // 60
        sec %= 60
        return "%02d:%02d" % (hour, min) 

#final chart
#def create_visualisation(circles_df, time_values, distance_values):


#create visualisation
if st.session_state["FormSubmitter:user_inputs-Create visualisation"]==True:
    #prepare data for analysis----------------------------
    df_filtered = df[df["Activity Date"].dt.year == year_filter]

    #get max top 3 activity types by count
    top_three = df_filtered["Activity Type"].value_counts().head(3).index.to_list()

    #derive clean column for activity types to use later
    df_filtered["Activity Type clean"] = [activity if activity in top_three else "Other"
                                            for activity in df_filtered['Activity Type']]
    df_filtered["Activity rank"] = df_filtered["Activity Type"].map(
        dict(zip(top_three, np.arange(0,len(top_three),1)))
        ).fillna(len(top_three)+1)

    #pre-aggregate data---------------------------
    #for daily circles
    circles_df = df_filtered.groupby([df_filtered["Activity Date"].dt.month,
                                df_filtered["Activity Date"].dt.day]).agg({'Activity Type clean': ','.join})
    circles_df.index.names = ["Month", "Day"]
    circles_df = circles_df.reset_index()
    circles_df["Activity Type clean"] = [i.split(",") for i in circles_df["Activity Type clean"]]

    #for small multiples
    months = np.arange(1,13,1)
    time_values = []
    distance_values = []
    for month in months:
        time_values.append(df_filtered[(df_filtered["Activity Date"].dt.month == month)]["Moving Time"].sum())
        if distance_unit=="Kilometers":
            distance_values.append(df_filtered[(df_filtered["Activity Date"].dt.month == month)]["Distance"].sum()/1000)
        elif distance_unit=="Miles":
            distance_values.append(df_filtered[(df_filtered["Activity Date"].dt.month == month)]["Distance"].sum()/1600)

    #configs for visual-------------------------------------
    #create colour dict for activities
    act_color = ["#6DB4C8", "#FD7B5C", "#FBCA58", "#7E8384"]
    act_colormap = dict(zip(top_three + ["Other"], act_color))

    #colors
    colors = {"bg": "#FDFBF7", "text":"#2E3234", "bars":"#FBF9F5"}

    #basesize of circles
    markersize = 80

    #axis labels
    month_labels = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']



st.write(st.session_state)