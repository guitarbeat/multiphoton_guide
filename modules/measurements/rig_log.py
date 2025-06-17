"""
Rig log module for the Multiphoton Microscopy Guide application.
Implements a comprehensive system change tracking feature.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from modules.core.constants import RIG_LOG_CATEGORIES, RIG_LOG_COLUMNS, RIG_LOG_FILE
from modules.core.data_utils import ensure_columns, save_dataframe
from modules.core.shared_utils import load_measurement_dataframe
from modules.ui.components import (
    create_header,
    create_metric_row,
    create_plot,
    create_tab_section,
)


def render_rig_log_tab():
    """Render the rig log tab content."""

    create_header(
        "Microscope Log",
        f"Track maintenance, calibration, and modifications to ensure reproducibility",
    )

    # Load existing data using the template function
    rig_log_df = load_measurement_dataframe("rig_log")

    # Ensure all required columns exist
    rig_log_df = ensure_columns(rig_log_df, RIG_LOG_COLUMNS)

    # Create tabs for better organization
    tab1, tab2 = st.tabs(["📋 View & Filter Log", "📊 Log Analysis"])

    with tab1:
        # Create two columns for layout
        info_col, stats_col = st.columns([1, 2])

        with info_col:
            render_rig_log_introduction()

        with stats_col:
            # Quick stats about the log
            if not rig_log_df.empty:
                pass  # Removed Log Overview and metrics

        st.markdown("---")
        render_rig_log_table(rig_log_df)
        st.markdown("---")

        # Entry form
        if "show_entry_form" not in st.session_state:
            st.session_state.show_entry_form = False

        if st.session_state.show_entry_form:
            render_rig_log_entry_form(rig_log_df)

            # Button to hide form
            if st.button("↑ Hide Form", key="hide_form"):
                st.session_state.show_entry_form = False
        else:
            # Show button to expand form
            if st.button(
                "📝 Add New Log Entry", key="show_form", use_container_width=True
            ):
                st.session_state.show_entry_form = True

    with tab2:
        render_rig_log_visualization(rig_log_df)


def render_rig_log_introduction():
    """Render the introduction section for the rig log."""

    create_tab_section(
        "📖 Why Keep a Microscope Log?",
        lambda: st.markdown(
            """
        A comprehensive microscope log enhances reproducibility and simplifies troubleshooting. As noted in the Nature Protocols article:

        > **CRITICAL:** Keep a shared, dated log of all microscope system changes (alignment, calibrations, software updates, etc.) that is accessible to all users. A good 'rig log' pays dividends in years to come.

        **Benefits:**

        * **Troubleshooting** - Trace issues to recent microscope changes
        * **Reproducibility** - Recreate exact conditions for critical experiments
        * **Knowledge Transfer** - Preserve institutional memory as team members change
        * **Maintenance Schedule** - Track when components were last serviced

        This log automatically records measurements and optimizations performed through the application and allows manual entry of additional microscope changes.
    """
        ),
        expanded=False,
    )


def render_rig_log_table(rig_log_df):
    """Render the rig log table with filtering options."""

    st.subheader("Microscope Change History")

    # Create filter controls in a more compact layout
    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 0.5])

    with col1:
        # Date range filter
        date_options = ["All Time", "Today", "Past Week", "Past Month", "Past Year"]
        date_filter = st.selectbox("📅 Date Range:", date_options, index=0)

    with col2:
        # Category filter
        unique_categories = rig_log_df["Category"].dropna().unique().tolist()
        categories = ["All Categories"] + sorted(unique_categories)
        category_filter = st.selectbox("🏷️ Category:", categories, index=0)

    with col3:
        # Researcher filter
        # Filter out NaN values to avoid type error when sorting
        unique_researchers = rig_log_df["Researcher"].dropna().unique().tolist()
        researchers = ["All Researchers"] + sorted(unique_researchers)
        researcher_filter = st.selectbox("👤 Researcher:", researchers, index=0)

    with col4:
        # Help popover
        with st.popover("ℹ️ Help", use_container_width=True):
            st.markdown(
                """
            **How to use this log:**
            
            * **Filter:** Use dropdowns to filter entries
            * **Sort:** Click column headers to sort
            * **Search:** Use browser search (Ctrl+F/⌘+F)
            
            **Categories explained:**
            * **Measurement:** Power, resolution assessments
            * **Optimization:** GDD, alignment tuning
            * **Maintenance:** Cleaning, repairs
            * **Calibration:** System calibration
            * **Software:** Updates, configurations
            * **Hardware:** Modifications, upgrades
            """
            )

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
            "Date", help="Date and time of the change", width="medium"
        ),
        "Researcher": st.column_config.TextColumn(
            "Researcher", help="Person who made the change", width="small"
        ),
        "Activity": st.column_config.TextColumn(
            "Activity", help="Brief description of the activity", width="medium"
        ),
        "Description": st.column_config.TextColumn(
            "Description", help="Detailed description of the change", width="large"
        ),
        "Category": st.column_config.SelectboxColumn(
            "Category", help="Type of change", width="small", options=RIG_LOG_CATEGORIES
        ),
    }

    # Display the filtered data
    if filtered_df.empty:
        st.info("📭 No log entries match the selected filters.")
    else:
        # Sort by date (newest first)
        filtered_df = filtered_df.sort_values("Date", ascending=False).reset_index(drop=True)

        # Use st.data_editor for inline editing and deleting
        edited_df = st.data_editor(
            filtered_df,
            num_rows="dynamic",  # Allow add/delete
            use_container_width=True,
            key="rig_log_editor"
        )

        # Save changes if the DataFrame was edited
        if st.button("💾 Save Changes to Log"):
            # Only save if there are actual changes
            if not edited_df.equals(filtered_df):
                save_dataframe(edited_df, RIG_LOG_FILE)
                st.success("Log updated!")
                st.rerun()
            else:
                st.info("No changes to save.")


def render_rig_log_entry_form(rig_log_df):
    """Render the form for adding new rig log entries."""

    st.subheader("📝 Add New Log Entry")

    # Create cleaner form layout
    form_col1, form_col2 = st.columns([2, 1])

    with st.form(key="rig_log_entry_form"):
        with form_col1:
            # Activity and description
            activity = st.text_input(
                "Activity:",
                placeholder="e.g., Laser alignment, Objective cleaning",
                help="Brief title for the activity performed",
            )

            description = st.text_area(
                "Description:",
                placeholder="What was changed and why? Include any measurements or settings.",
                help="Detailed description of what was done and why",
                height=100,
            )

        with form_col2:
            # Category and date options
            category = st.selectbox("Category:", RIG_LOG_CATEGORIES, index=2)

            # Add researcher field (default to session state)
            researcher = st.text_input(
                "Researcher:",
                value=st.session_state.researcher,
                help="Person making the change",
            )

        # Submit button
        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button(
                "Add Entry", use_container_width=True, type="primary"
            )
        with col2:
            st.markdown("")  # Empty space for layout balance

    if submitted:
        if not activity or not description:
            st.warning("⚠️ Please provide both an activity and description.")
        else:
            # Create new entry
            new_entry = pd.DataFrame(
                {
                    "Date": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                    "Researcher": [researcher],
                    "Activity": [activity],
                    "Description": [description],
                    "Category": [category],
                }
            )

            # Append to existing log
            updated_log = pd.concat([rig_log_df, new_entry], ignore_index=True)

            # Save updated log
            save_dataframe(updated_log, RIG_LOG_FILE)

            st.success("✅ Log entry added successfully!")

            # Hide the form after successful submission
            st.session_state.show_entry_form = False
            # Force a rerun to refresh the page with the new entry
            st.rerun()


def render_rig_log_visualization(rig_log_df):
    """Render visualizations for the rig log data."""

    if rig_log_df.empty:
        st.info("📊 Add log entries to see analysis and trends")
        return

    viz_col1, viz_col2 = st.columns(2)

    with viz_col1:
        st.subheader("Activity by Category")

        # Create activity by category plot
        def plot_activity_by_category(fig, ax):
            # Count entries by category
            category_counts = rig_log_df["Category"].value_counts()

            # Create horizontal bar chart with better colors
            colors = ["#4BA3C4", "#6BBFDB", "#89CBE5", "#A8D7EE", "#C6E3F6", "#E5F0FD"]
            y_pos = np.arange(len(category_counts.index))
            bars = ax.barh(
                y_pos,
                category_counts.values,
                color=(
                    colors[: len(category_counts)]
                    if len(category_counts) <= len(colors)
                    else colors
                ),
                alpha=0.8,
            )

            # Add labels
            ax.set_yticks(y_pos)
            ax.set_yticklabels(category_counts.index)
            ax.set_xlabel("Number of Entries")

            # Add count labels on bars with better positioning
            for i, v in enumerate(category_counts.values):
                ax.text(
                    max(v - 0.9, 0.1) if v > 5 else v + 0.1,
                    i,
                    str(v),
                    va="center",
                    ha="right" if v > 5 else "left",
                    color="white" if v > 5 else "black",
                    fontweight="bold",
                )

            # Add grid but make it less prominent
            ax.grid(True, linestyle="--", alpha=0.3, axis="x")

            # Remove top and right spines
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        # Display the plot
        category_plot = create_plot(plot_activity_by_category)
        st.pyplot(category_plot)

    # Create activity timeline plot if enough data
    if len(rig_log_df) >= 5:
        with viz_col2:
            st.subheader("Activity Timeline")

            def plot_activity_timeline(fig, ax):
                # Convert dates to datetime
                rig_log_df["Date_DT"] = pd.to_datetime(
                    rig_log_df["Date"], errors="coerce"
                )

                # Group by date and count
                timeline_df = (
                    rig_log_df.groupby(rig_log_df["Date_DT"].dt.date)
                    .size()
                    .reset_index(name="count")
                )
                timeline_df = timeline_df.sort_values("Date_DT")

                # Plot timeline with improved styling
                ax.plot(
                    timeline_df["Date_DT"],
                    timeline_df["count"],
                    marker="o",
                    linestyle="-",
                    color="#BF5701",
                    linewidth=2,
                    markersize=6,
                )

                # Fill area under the curve
                ax.fill_between(
                    timeline_df["Date_DT"],
                    timeline_df["count"],
                    alpha=0.2,
                    color="#BF5701",
                )

                # Add labels
                ax.set_xlabel("Date")
                ax.set_ylabel("Number of Activities")

                # Format x-axis dates
                fig.autofmt_xdate()

                # Add grid but make it less prominent
                ax.grid(True, linestyle="--", alpha=0.3)

                # Remove top and right spines
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)

            # Display the plot
            timeline_plot = create_plot(plot_activity_timeline)
            st.pyplot(timeline_plot)

    # Add explanation in a cleaner format
    st.subheader("📊 Insights")
    cols = st.columns(2)

    with cols[0]:
        st.markdown(
            """
        **Activities by Category Chart**
        
        This visualization shows the distribution of maintenance activities:
        
        * **Balanced categories** indicate comprehensive system care
        * **High maintenance counts** might signal aging equipment
        * **Low calibration counts** could suggest missed opportunities for optimization
        
        Aim for regular, preventative maintenance across all categories.
        """
        )

    with cols[1]:
        st.markdown(
            """
        **Activity Timeline Chart**
        
        The timeline reveals maintenance patterns over time:
        
        * **Regular spacing** indicates good maintenance practices
        * **Clusters** often represent troubleshooting periods
        * **Gaps** may indicate periods when logging was overlooked
        
        Record all changes consistently, even minor ones, to build a complete history.
        """
        )
