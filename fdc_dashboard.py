import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="FDC Sensor Monitoring")

@st.cache_data
def load_data():
    df = pd.read_csv('cleaned_tool_sensor_data.csv')
    df['DateTime'] = pd.to_datetime(df['TimeStamp'], format='%d/%m/%Y %H:%M', errors='coerce')
    return df

df = load_data()

# Define metadata columns (from your CSV header)
metadata_cols = [
    'TimeStamp', 'ToolName', 'TOOL_ID', 'Run', 'RunStartTime', 'DATA_QUALITY',
    'EQPType', 'HasComments', 'LOT_ID', 'LogicalRecipeID', 'LotPurposeType',
    'LotType', 'MachineRecipeID', 'PhysicalRecipeID', 'PortID', 'ProcessOpNum',
    'ProductGrpID', 'ProductID', 'RECIPE_ID', 'ReticleID', 'RouteID', 'Technology', 'WAFER_ID',
    'DateTime', 'is_anomaly'
]

# Identify sensor columns = all columns not in metadata
sensor_cols = [col for col in df.columns if col not in metadata_cols]

# Sidebar filters
st.sidebar.header("🔍 Filters")
tools = df['ToolName'].unique()
selected_tool = st.sidebar.multiselect(
    "Tool", 
    tools, 
    default=tools[:2] if len(tools) >= 2 else tools
)

runs = df['Run'].astype(str).unique()
selected_runs = st.sidebar.multiselect(
    "Run ID", 
    runs, 
    default=runs[:5] if len(runs) >= 5 else runs
)

# Apply filters
if selected_tool and selected_runs:
    mask = df['ToolName'].isin(selected_tool) & df['Run'].astype(str).isin(selected_runs)
    df_filtered = df[mask]
else:
    df_filtered = df.copy()

# Main title
st.title("🔧 Semiconductor Tool Sensor Monitoring (FDC)")

# Summary metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Runs", len(df_filtered))
col2.metric("Anomalous Runs", int(df_filtered['is_anomaly'].sum()))
col3.metric("Tools Monitored", df_filtered['ToolName'].nunique())

# Sensor time series
st.subheader("📈 Sensor Trends Over Time")
if sensor_cols:
    selected_sensor = st.selectbox("Select Sensor", sensor_cols, index=0)

    fig = px.line(
        df_filtered,
        x='DateTime',
        y=selected_sensor,
        color='Run',
        title=f"{selected_sensor} Over Time",
        markers=True
    )
    # Add normal range based on FULL dataset (not filtered)
    mean_val = df[selected_sensor].mean()
    std_val = df[selected_sensor].std()
    if pd.notna(mean_val) and pd.notna(std_val) and std_val > 0:
        fig.add_hrect(
            y0=mean_val - 3 * std_val,
            y1=mean_val + 3 * std_val,
            fillcolor="green",
            opacity=0.1,
            line_width=0,
            annotation_text="Normal Range (±3σ)"
        )
    st.plotly_chart(fig, use_container_width=True)

    # Anomaly table
    st.subheader("⚠️ Anomaly Alerts")
    anomaly_df = df_filtered[df_filtered['is_anomaly']][['Run', 'ToolName', 'DateTime', selected_sensor]]
    if not anomaly_df.empty:
        st.dataframe(anomaly_df.sort_values('DateTime', ascending=False), use_container_width=True)
    else:
        st.info("No anomalies detected in selected data.")
else:
    st.warning("No sensor columns found.")

# Correlation heatmap (optional)
if st.checkbox("Show Sensor Correlation"):
    if len(sensor_cols) >= 2:
        # Use top 8 sensors by variance
        top_sensors = df[sensor_cols].var().sort_values(ascending=False).head(8).index
        corr = df[top_sensors].corr()
        fig_corr = px.imshow(corr, text_auto='.2f', title="Sensor Correlation (Top 8 by Variance)")
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.warning("Not enough sensor data for correlation.")