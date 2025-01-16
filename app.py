import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pyfonts import load_font

#---------------------------------------------------------------
#Configs and functions -----------------------------------------
st.set_page_config(
    page_title="Year in Sports",
    page_icon="weight_lifter",
    #layout="wide",
     )

#session states
if "init" not in st.session_state:
    st.session_state["init"] = True
    st.session_state["is_csv"] = None
    st.session_state["upload_success"] = None
    st.session_state["rerun_data_processing"] = True
    st.session_state["FormSubmitter:user_inputs-Create visualisation"]=None
#st.write(st.session_state)

def set_rerun_true():
    st.session_state["rerun_data_processing"] = True

def form_submit_callback():
    st.session_state["rerun_data_processing"] = False
    #st.session_state["run_visualisation"] = True

#cache data and fonts
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

@st.cache_data(show_spinner=False, ttl=60*30)
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    return df


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

  
#process data for chart
def process_data(df):

    #prepare data for analysis----------------------------
    df_filtered = df[df["Activity Date"].dt.year == year_filter]

    #get max top 3 activity types by count
    top_three = df_filtered["Activity Type"].value_counts().head(3).index.to_list()

    #derive clean column for activity types to use later
    df_filtered["Activity Type clean"] = [activity if activity in top_three else "Other"
                                            for activity in df_filtered['Activity Type']]
    df_filtered["Activity rank"] = df_filtered["Activity Type"].map(
        dict(zip(top_three, np.arange(0,len(top_three),1)))
        ).fillna(len(top_three))

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
        elif distance_unit=="Metres":
            distance_values.append(df_filtered[(df_filtered["Activity Date"].dt.month == month)]["Distance"].sum())

    #top three df
    top_three_df = df_filtered[["Activity rank","Activity Type clean"]].value_counts().to_frame().reset_index().sort_values(by="Activity rank")

    return df_filtered,top_three,top_three_df,circles_df,time_values,distance_values,months

#create visual
def create_visualisation(df_filtered,top_three,top_three_df,circles_df,time_values,distance_values,months):

    #configs-------------------------------------
    #colors
    act_color = ["#6DB4C8", "#FD7B5C", "#FBCA58", "#7E8384"]
    act_colormap = dict(zip(top_three + ["Other"], act_color))
    colors = {"bg": "#FBF9F5", "text":"#2E3234", "bars":"#C6C9CA"}

    #base size of circles
    markersize = 80

    #axis labels
    month_labels = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']

    #setup fig-------------------------------
    fig = plt.figure(figsize=(10,12))
    fig.set_facecolor(colors["bg"])
    gs = GridSpec(5, 4, figure=fig)
    ax1 = fig.add_subplot(gs[0:4, 0:3])
    ax3 = fig.add_subplot(gs[3:4:, 3:])
    if len(distance_values)!=0:
        ax2 = fig.add_subplot(gs[2:3:, 3:])
    plt.subplots_adjust(hspace=1, wspace=0.3)
    for ax in fig.axes:
        ax.set_facecolor(colors["bg"])

    #plot data -----------
    #circles
    for row in range(len(circles_df)):
        for i,label in enumerate(circles_df.loc[row]["Activity Type clean"]):
            if i==0:
                ax1.scatter(x=circles_df.loc[row]["Month"],
                    y=circles_df.loc[row]["Day"],
                    s=15,
                    linewidth=0,
                    color=act_colormap[label],
                    clip_on=False)
            else:
                ax1.scatter(x=circles_df.loc[row]["Month"],
                    y=circles_df.loc[row]["Day"],
                    s=(i**1.7)*markersize,
                    color="None",
                    edgecolor=act_colormap[label],
                    linewidth=1.3,
                    clip_on=False)
                
    #bar charts
    if len(distance_values)!=0:
        ax2.bar(months, distance_values, color=colors["bars"], zorder=3)
    ax3.bar(months, time_values, color=colors["bars"], zorder=3)
                
    #format axis------------------
    #circles
    ax1.set_xticks(np.arange(1,13,1))
    ax1.set_yticks(np.arange(1,32,1))
    ax1.tick_params(axis="both", length=0, labeltop=True, labelbottom=False,)
    ax1.set_yticklabels(labels=ax1.get_yticks(), fontproperties=font_r, fontsize=10, color=colors["text"])
    ax1.set_xticklabels(labels=month_labels, fontproperties=font_r, fontsize=10,color=colors["text"])
    ax1.set_xlim(xmin=0.3,xmax=12.5)
    ax1.set_ylim(ymin=0,ymax=31)
    ax1.invert_yaxis()
    for pos in ["top", "bottom", "left", "right"]:
        ax1.spines[pos].set_visible(False)

    #distance
    if len(distance_values)!=0:
        ax2.locator_params(axis='y', nbins=4)
        ax2.set_yticks(ax2.get_yticks())
        distance_unit_display = distance_unit.replace("Kilometers","km").replace("Miles","m").replace("Metres","m")
        ax2.set_yticklabels([""]+["{}{}".format(i.astype(int),distance_unit_display) for i in ax2.get_yticks()][1:],fontproperties=font_r, fontsize=9,color=colors["text"])
        ax2.text(0,ax2.get_yticks()[-1]+ax2.get_yticks()[1], "Distance", fontsize=12, ha="left", va="center", fontproperties=font_m, color=colors["text"], alpha=0.9)
        ax2.set_xticks(np.arange(1,13,1))
        ax2.set_xticklabels(labels=month_labels, fontproperties=font_r, fontsize=10,color=colors["text"])
        ax2.tick_params(axis="both", length=0,labelleft=False, labelright=True,)
        ax2.grid(visible="True", axis='y', zorder=1, color=colors["text"], alpha=0.3, linewidth=0.5)
        for pos in ["top", "left", "right"]:
            ax2.spines[pos].set_visible(False)

    #total time
    tick_steps = get_axis_ticks(max(time_values))
    ax3.set_yticks(np.arange(0, max(time_values)+tick_steps, tick_steps))
    ax3.set_yticklabels([""]+[convert_time(i) for i in ax3.get_yticks()][1:],fontproperties=font_r, fontsize=9,color=colors["text"])
    ax3.text(0,max(time_values)+tick_steps, "Moving time", fontsize=12, ha="left", va="center", fontproperties=font_m, color=colors["text"], alpha=0.9)
    ax3.set_xticks(np.arange(1,13,1))
    ax3.set_xticklabels(labels=month_labels, fontproperties=font_r, fontsize=10,color=colors["text"])
    ax3.tick_params(axis="both", length=0,labelleft=False, labelright=True,)
    ax3.grid(visible="True", axis='y', zorder=1, color=colors["text"], alpha=0.3, linewidth=0.5)
    for pos in ["top", "left", "right"]:
        ax3.spines[pos].set_visible(False)

    #legend--------------------------------
    lg = fig.add_subplot(gs[0:2:, 3:])
    labels = top_three_df["Activity Type clean"].to_list()
    lg.barh(top_three_df["Activity rank"], top_three_df["count"], height=0.2, color=top_three_df["Activity Type clean"].map(act_colormap))
    lg.set_ylim(ymin=-1.2,ymax=6)
    lg.invert_yaxis()
    lg.text(0, lg.get_ylim()[1], "Activities", fontsize=12, ha="left", va="bottom", fontproperties=font_m, color=colors["text"], alpha=0.9)
    for i in range(len(top_three_df)):
        lg.text(0.1, i-0.35, labels[i]+", "+str( top_three_df["count"][i]), fontsize=10.5, ha="left", va="center", fontproperties=font_r, color=colors["text"], alpha=0.9)
    lg.axis("off")

    #header and footer------------------------
    plt.figtext(0.5,0.99,'My year in sports'.upper(), 
                ha="center",
                fontsize = 45, 
                color=colors["text"], 
                fontproperties=font_b)
    plt.figtext(0.5,1.06,'{}'.format(year_filter), ha="center",fontsize = 25, color=colors["text"], alpha=0.95, fontproperties=font_r)
    plt.figtext(0.5,0.19,'Data: Strava | Design: Lisa Hornung',ha="center", fontsize = 7, color=colors["text"], alpha=0.7,fontproperties=font_r)

    return fig

#Main app--------------------------------------------------------
st.title('My year in sports')
st.markdown("#### Create a poster of all your Strava activities")
st.write("")

#upload data
st.sidebar.subheader("Data upload")

with st.sidebar:
    st.write("")
    with st.expander("What data do I need?", expanded=False):
        st.markdown("""
        You’ll need to download your activity data from Strava. Follow [this guide](https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export) 
        to get a data dump.
        """)
        st.markdown("""
        The folder should contain `activities.csv` which we will use.
        """)
    st.write("") 
    uploaded_file = st.file_uploader("Upload your Strava csv file", 
                                    accept_multiple_files=False,
                                    on_change=set_rerun_true())
    
    if uploaded_file is None:
        st.session_state["is_csv"] = None
        st.session_state["upload_success"] = None
        st.session_state["FormSubmitter:user_inputs-Create visualisation"] = None
    
    if (st.session_state["rerun_data_processing"]== True) & (uploaded_file is not None):
        try:
            df = load_data(uploaded_file)
            st.session_state["is_csv"] = True    
        except UnicodeDecodeError:
            st.warning("Whoops, incorrect file format. Make sure to upload a `.csv` file to use this app")
            st.session_state["is_csv"] = False
            st.session_state["upload_success"]=False   

    #run check if correct file
    data_flag = False

    if (st.session_state["is_csv"]==True) & (st.session_state["rerun_data_processing"]== True):
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

st.sidebar.divider() 
st.sidebar.subheader("About this app")
st.sidebar.write("Made by Lisa Hornung with `streamlit`, `matplotlib` and `pyfonts`.")
st.sidebar.markdown("""
            Visit my [website](https://inside-numbers.com/) 
            or get in touch on [Github](https://github.com/Lisa-Ho), 
            [Mastodon](https://fosstodon.org/@LisaHornung), 
            [Bluesky](https://bsky.app/profile/lisahornung.bsky.social).
            """)

#user inputs  
if st.session_state["upload_success"]==True:
    with st.form(key='user_inputs'):
        col1, col2 = st.columns(2)
        with col1:
            year_filter = st.selectbox(
                "Year",
                df["Activity Date"].dt.year.unique()
                )
        with col2:
            distance_unit = st.selectbox(
                "Distance unit",
                ("N/A","Kilometers","Metres","Miles"),
                help="Select 'N/A' if you don't want to visualise distance"
                )
        submitted = st.form_submit_button('Create visualisation',
                                          on_click=form_submit_callback())

st.markdown("\n")

#run visualisation
if st.session_state["FormSubmitter:user_inputs-Create visualisation"] is not None:
    df_filtered,top_three,top_three_df, circles_df,time_values,distance_values,months = process_data(df)
    fig = create_visualisation(df_filtered,top_three,top_three_df,circles_df,time_values,distance_values,months)
    st.write(fig)


#download image
if st.session_state["FormSubmitter:user_inputs-Create visualisation"] is not None:
    st.divider()
    st.write("")   
    plt.savefig("my-year-in-sports.png", bbox_inches="tight", pad_inches=0.8)
    with open("my-year-in-sports.png", "rb") as file:
        btn = st.download_button(
                    label="Download image",
                    data=file,
                    file_name="my-year-in-sports-{}.png".format(year_filter),
                    mime="image/png"
                )

    plt.savefig("my-year-in-sports.svg",bbox_inches="tight", pad_inches=0.8)
    with open("my-year-in-sports.svg", "rb") as file:
        btn = st.download_button(
                    label="Download svg",
                    data=file,
                    file_name="my-year-in-sports-{}.svg".format(year_filter),
                    mime="svg"
                )

if st.session_state["upload_success"] != True:
    st.image("https://github.com/Lisa-Ho/year-in-sports/blob/main/year_in_sports_example_output.png?raw=true",
             width=400)