import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from g4f.client import Client
import uuid

# Setting page configuration for a modern look
st.set_page_config(page_title="Job Exposure Dashboard", layout="wide")

# Adding custom CSS for Tailwind-like styling
st.markdown("""
    <style>
    .main { background-color: #f9fafb; padding: 20px; }
    .stApp { background-color: #f9fafb; }
    .title { font-size: 2.5rem; font-weight: bold; color: #1f2937; text-align: center; margin-bottom: 20px; }
    .subtitle { font-size: 1.5rem; color: #4b5563; text-align: center; margin-bottom: 30px; }
    .sidebar .sidebar-content { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stButton>button { background-color: #3b82f6; color: white; border-radius: 8px; padding: 10px 20px; }
    .stButton>button:hover { background-color: #2563eb; }
    .chat-container { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-top: 20px; }
    .chat-message { background-color: #e5e7eb; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# Initializing session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Loading and cleaning data
@st.cache_data
def load_and_clean_data():
    # Reading CSV file
    df = pd.read_csv('data-x3jzk.csv')
    
    # Cleaning headers and values
    df.columns = [col.strip().replace('"', '') for col in df.columns]
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip().str.replace('^"|"$', '', regex=True)
    
    # Converting numerical columns
    df['Average score'] = pd.to_numeric(df['Average score'], errors='coerce')
    df['Standard deviation'] = pd.to_numeric(df['Standard deviation'], errors='coerce')
    
    # Dropping rows with invalid numerical values
    df = df.dropna(subset=['Average score', 'Standard deviation'])
    
    return df

# Initializing Grok client
grok_client = Client()

# Loading data
df = load_and_clean_data()

# Creating main title and subtitle
st.markdown('<div class="title">Job Exposure Analysis Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Explore job titles by automation exposure and variability</div>', unsafe_allow_html=True)

# Sidebar for filters
with st.sidebar:
    st.header("Filters")
    major_groups = ['All'] + sorted(df['Major groups'].unique())
    selected_group = st.selectbox("Select Major Group", major_groups)
    exposure_levels = ['All'] + sorted(df['mean_exposure_level'].unique())
    selected_exposure = st.selectbox("Select Exposure Level", exposure_levels)

# Filtering data based on selections
filtered_df = df.copy()
if selected_group != 'All':
    filtered_df = filtered_df[filtered_df['Major groups'] == selected_group]
if selected_exposure != 'All':
    filtered_df = filtered_df[filtered_df['mean_exposure_level'] == selected_exposure]

# Layout with two columns
col1, col2 = st.columns([2, 1])

# Bar Chart: Top 10 Job Titles by Average Score
with col1:
    st.subheader("Top 10 Job Titles by Average Score")
    top_10_df = filtered_df.nlargest(10, 'Average score')
    fig_bar = px.bar(
        top_10_df,
        x='Average score',
        y='Job title',
        color='Major groups',
        text='Average score',
        height=400,
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='auto')
    fig_bar.update_layout(
        xaxis_title="Average Score",
        yaxis_title="Job Title",
        template="plotly_white",
        font=dict(size=12),
        margin=dict(l=150)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Pie Chart: Distribution of Exposure Levels
with col2:
    st.subheader("Exposure Level Distribution")
    exposure_counts = filtered_df['mean_exposure_level'].value_counts().reset_index()
    exposure_counts.columns = ['mean_exposure_level', 'count']
    fig_pie = px.pie(
        exposure_counts,
        names='mean_exposure_level',
        values='count',
        height=400,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_pie.update_traces(textinfo='percent+label', pull=[0.1 if i == 0 else 0 for i in range(len(exposure_counts))])
    fig_pie.update_layout(template="plotly_white", font=dict(size=12))
    st.plotly_chart(fig_pie, use_container_width=True)

# Scatter Plot: Average Score vs Standard Deviation
st.subheader("Average Score vs Standard Deviation by Exposure Level")
fig_scatter = px.scatter(
    filtered_df,
    x='Average score',
    y='Standard deviation',
    color='mean_exposure_level',
    hover_data=['Job title', 'Major groups'],
    size='Average score',
    height=500,
    color_discrete_sequence=px.colors.qualitative.Bold
)
fig_scatter.update_layout(
    xaxis_title="Average Score",
    yaxis_title="Standard Deviation",
    template="plotly_white",
    font=dict(size=12)
)
st.plotly_chart(fig_scatter, use_container_width=True)

# Interesting Fact
st.subheader("Interesting Fact")
st.markdown("""
Surprisingly, **Clerical Support Workers** like Data Entry Clerks and Typists dominate the highest exposure levels (gradient 4), with average scores above 0.6. This suggests that routine, low-variability tasks are most at risk of automation, even compared to some professional roles like Financial Analysts.
""")

# Chat Interface with Grok
st.subheader("Ask Grok About the Data")
user_query = st.text_input("Enter your question about the job exposure data:")
if user_query:
    # Preparing context for Grok
    context = f"""
    The dataset contains job titles with their major groups, average scores (0 to 1, higher means more automation exposure), mean exposure levels (e.g., 'Highest exposure, low task variability (gradient 4)'), and standard deviations. Here are some sample rows:
    {df.head(5).to_string()}
    User question: {user_query}
    """
    
    try:
        response = grok_client.chat.completions.create(
            model="grok",
            messages=[{"role": "user", "content": context}]
        )
        answer = response.choices[0].message.content
        st.session_state.chat_history.append({"id": str(uuid.uuid4()), "query": user_query, "answer": answer})
    except Exception as e:
        answer = f"Error contacting Grok: {str(e)}"
        st.session_state.chat_history.append({"id": str(uuid.uuid4()), "query": user_query, "answer": answer})

# Displaying chat history
if st.session_state.chat_history:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for chat in st.session_state.chat_history[::-1]:
        st.markdown(f'<div class="chat-message"><strong>You:</strong> {chat["query"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-message"><strong>Grok:</strong> {chat["answer"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
