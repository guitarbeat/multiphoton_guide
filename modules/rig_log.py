"""
Rig log module for the Multiphoton Microscopy Guide application.
Implements a comprehensive system change tracking feature.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from pathlib import Path

from modules.data_utils import load_dataframe, save_dataframe, ensure_columns
from modules.ui_components import create_header, create_info_box, create_warning_box, create_success_box, create_metric_row, create_data_editor, create_plot, create_tab_section, create_form_section

# Constants
RIG_LOG_FILE = "rig_log.csv"

def render_rig_log_tab():
    """Render the rig log tab content."""
    
    create_header("Microscope System Change Log", 
                 f"Study: {st.session_state.study_name} | Researcher: {st.session_state.researcher}")
    
    # Load existing data
    rig_log_df = load_dataframe(RIG_LOG_FILE, pd.DataFrame({
        "Date": [],
        "Researcher": [],
        "Activity": [],
        "Description": [],
        "Category": []
    }))
    
    # Ensure all required columns exist
    required_columns = ["Date", "Researcher", "Activity", "Description", "Category"]
    rig_log_df = ensure_columns(rig_log_df, required_columns)
    
    # Create two columns for layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        render_rig_log_introduction()
        render_rig_log_table(rig_log_df)
    
    with col2:
        render_rig_log_entry_form(rig_log_df)
        render_rig_log_visualization(rig_log_df)

def render_rig_log_introduction():
    """Render the introduction section for the rig log."""
    
    create_tab_section("📖 Introduction & Importance", lambda: st.markdown("""
        A comprehensive system change log is critical for maintaining consistent microscope performance and ensuring reproducible results. As noted in the Nature Protocols article:

        > **CRITICAL:** Keep a shared, dated log of all changes to the microscope system (for example, alignment, calibrations, measurements, software updates and so on) that is easily accessible by all users. A good 'rig log' pays dividends in years to come.

        **Benefits of maintaining a detailed rig log:**

        1. **Troubleshooting:** When issues arise, the log provides context about recent changes
        2. **Reproducibility:** Helps recreate exact conditions for follow-up experiments
        3. **Maintenance:** Tracks when components were last serviced or calibrated
        4. **Knowledge Transfer:** Preserves institutional knowledge when team members change
        5. **Performance Monitoring:** Reveals gradual system degradation over time

        This log automatically records all measurements and optimizations performed through the application, and allows manual entry of additional system changes.
    """), expanded=True)

def render_rig_log_table(rig_log_df):
    """Render the rig log table with filtering options."""
    
    st.subheader("System Change History")
    
    # Help popover
    with st.popover("ℹ️ How to use this log", use_container_width=True):
        st.markdown("""
        **Features:**
        1. **Filtering:** Use the dropdowns to filter by date range, category, or researcher
        2. **Sorting:** Click column headers to sort the table
        3. **Searching:** Use the search box to find specific entries
        4. **Adding Entries:** Use the form on the right to add new entries
        
        **Categories:**
        - **Measurement:** Power, resolution, or other quantitative assessments
        - **Optimization:** GDD, alignment, or other performance tuning
        - **Maintenance:** Cleaning, component replacement, or repairs
        - **Calibration:** System calibration procedures
        - **Software:** Software updates or configuration changes
        - **Hardware:** Hardware modifications or upgrades
        """)
    
    # Create filter controls
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        # Date range filter
        date_options = ["All Time", "Today", "Past Week", "Past Month", "Past Year"]
        date_filter = st.selectbox("Date Range:", date_options, index=0)
    
    with filter_col2:
        # Category filter
        categories = ["All Categories"] + sorted(rig_log_df["Category"].unique().tolist())
        category_filter = st.selectbox("Category:", categories, index=0)
    
    with filter_col3:
        # Researcher filter
        researchers = ["All Researchers"] + sorted(rig_log_df["Researcher"].unique().tolist())
        researcher_filter = st.selectbox("Researcher:", researchers, index=0)
    
    # Apply filters
    filtered_df = rig_log_df.copy()
    
    # Date filter
    if date_filter != "All Time":
        current_date = datetime.now()
        if date_filter == "Today":
            start_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == "Past Week":
            start_date = current_date - timedelta(days=7)
        elif date_filter == "Past Month":
            start_date = current_date - timedelta(days=30)
        elif date_filter == "Past Year":
            start_date = current_date - timedelta(days=365)
        
        # Convert string dates to datetime for comparison
        filtered_df["Date_DT"] = pd.to_datetime(filtered_df["Date"], errors="coerce")
        filtered_df = filtered_df[filtered_df["Date_DT"] >= start_date]
        filtered_df = filtered_df.drop(columns=["Date_DT"])
    
    # Category filter
    if category_filter != "All Categories":
        filtered_df = filtered_df[filtered_df["Category"] == category_filter]
    
    # Researcher filter
    if researcher_filter != "All Researchers":
        filtered_df = filtered_df[filtered_df["Researcher"] == researcher_filter]
    
    # Configure columns for the data editor
    column_config = {
        "Date": st.column_config.TextColumn(
            "Date",
            help="Date and time of the change",
            width="medium"
        ),
        "Researcher": st.column_config.TextColumn(
            "Researcher",
            help="Person who made the change",
            width="small"
        ),
        "Activity": st.column_config.TextColumn(
            "Activity",
            help="Brief description of the activity",
            width="medium"
        ),
        "Description": st.column_config.TextColumn(
            "Description",
            help="Detailed description of the change",
            width="large"
        ),
        "Category": st.column_config.TextColumn(
            "Category",
            help="Type of change",
            width="small"
        )
    }
    
    # Display the filtered data
    if filtered_df.empty:
        st.info("No log entries match the selected filters.")
    else:
        # Sort by date (newest first)
        filtered_df = filtered_df.sort_values("Date", ascending=False)
        
        # Display the table
        st.dataframe(
            filtered_df,
            column_config=column_config,
            hide_index=True,
            use_container_width=True
        )
        
        st.caption(f"Showing {len(filtered_df)} of {len(rig_log_df)} total entries")

def render_rig_log_entry_form(rig_log_df):
    """Render the form for adding new rig log entries."""
    
    st.subheader("Add New Log Entry")
    
    with st.form(key="rig_log_entry_form"):
        # Activity
        activity = st.text_input("Activity:", 
                               placeholder="e.g., Laser alignment, Objective cleaning",
                               help="Brief title for the activity performed")
        
        # Description
        description = st.text_area("Description:", 
                                 placeholder="Provide detailed information about the change...",
                                 help="Detailed description of what was done and why")
        
        # Category
        category_options = ["Measurement", "Optimization", "Maintenance", "Calibration", "Software", "Hardware"]
        category = st.selectbox("Category:", category_options, index=2)
        
        # Submit button
        submitted = st.form_submit_button("Add Log Entry")
    
    if submitted:
        if not activity or not description:
            st.warning("Please provide both an activity and description.")
        else:
            # Create new entry
            new_entry = pd.DataFrame({
                "Date": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                "Researcher": [st.session_state.researcher],
                "Activity": [activity],
                "Description": [description],
                "Category": [category]
            })
            
            # Append to existing log
            updated_log = pd.concat([rig_log_df, new_entry], ignore_index=True)
            
            # Save updated log
            save_dataframe(updated_log, RIG_LOG_FILE)
            
            st.success("Log entry added successfully!")

def render_rig_log_visualization(rig_log_df):
    """Render visualizations for the rig log data."""
    
    st.subheader("Log Analysis")
    
    if rig_log_df.empty:
        st.info("Add log entries to see analysis")
        return
    
    # Create activity by category plot
    def plot_activity_by_category(fig, ax):
        # Count entries by category
        category_counts = rig_log_df["Category"].value_counts()
        
        # Create horizontal bar chart
        y_pos = np.arange(len(category_counts.index))
        ax.barh(y_pos, category_counts.values, color='#4BA3C4', alpha=0.7)
        
        # Add labels
        ax.set_yticks(y_pos)
        ax.set_yticklabels(category_counts.index)
        ax.set_xlabel('Number of Entries')
        ax.set_title('Activities by Category')
        
        # Add count labels on bars
        for i, v in enumerate(category_counts.values):
            ax.text(v + 0.1, i, str(v), va='center')
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7, axis='x')
    
    # Display the plot
    category_plot = create_plot(plot_activity_by_category)
    st.pyplot(category_plot)
    
    # Create activity timeline plot if enough data
    if len(rig_log_df) >= 5:
        def plot_activity_timeline(fig, ax):
            # Convert dates to datetime
            rig_log_df["Date_DT"] = pd.to_datetime(rig_log_df["Date"], errors="coerce")
            
            # Group by date and count
            timeline_df = rig_log_df.groupby(rig_log_df["Date_DT"].dt.date).size().reset_index(name="count")
            timeline_df = timeline_df.sort_values("Date_DT")
            
            # Plot timeline
            ax.plot(timeline_df["Date_DT"], timeline_df["count"], 'o-', color='#BF5701', linewidth=2, markersize=6)
            
            # Add labels
            ax.set_xlabel('Date')
            ax.set_ylabel('Number of Activities')
            ax.set_title('Activity Timeline')
            
            # Format x-axis dates
            fig.autofmt_xdate()
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.7)
        
        # Display the plot
        timeline_plot = create_plot(plot_activity_timeline)
        st.pyplot(timeline_plot)
    
    # Add explanation
    with st.expander("📊 Understanding These Plots"):
        st.markdown("""
        These visualizations help you understand system maintenance patterns:
        
        **Activities by Category:**
        - Shows the distribution of different types of system changes
        - Helps identify if certain categories are over or under-represented
        - Maintenance-heavy logs might indicate aging equipment
        
        **Activity Timeline:**
        - Shows the frequency of system changes over time
        - Clusters may indicate intensive troubleshooting periods
        - Regular, evenly-spaced activities suggest good maintenance practices
        
        **Best practices:**
        - Aim for regular, preventative maintenance rather than reactive fixes
        - Document all changes, even minor ones
        - Include enough detail that future users understand what was done and why
        """)
