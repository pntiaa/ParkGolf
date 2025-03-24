import random
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

@st.cache_resource
def load_members_from_excel():
    # Load the Excel file
    file_path = r'./다솜회_순위집계.xlsx'
    df = pd.read_excel(file_path, sheet_name="회원명부")
    members = {}
    for _, row in df.iloc[1:].iterrows():  # Skip the first row which is the title
        name = row["회원이름"]
        gender = row["성별"]
        members[name] = {"available": True, "gender": gender}
    return members

# Load members from the Excel file
members = load_members_from_excel()

def allocate_groups_random(members_list):
    """Randomly allocate members to groups of approximately equal size"""
    random.shuffle(members_list)  # Shuffle the list randomly
    
    groups = [members_list[i:i+max_group_size] for i in range(0, len(members_list), max_group_size)]
    
    # If last group has fewer than 4 members and there's an extra group, balance them
    if len(groups) > 1 and len(groups[-1]) < max_group_size:
        extra_members = groups.pop()
        for i, member in enumerate(extra_members):
            groups[i % len(groups)].append(member)
    
    return groups

# Initialize score structure for a player
def init_player_scores():
    return {
        "round_1": {f"hole_{i}": None for i in range(1, 10)},
        "round_2": {f"hole_{i}": None for i in range(1, 10)},
        "round_3": {f"hole_{i}": None for i in range(1, 10)},
        "round_4": {f"hole_{i}": None for i in range(1, 10)}
    }

# Streamlit UI Setup
st.title("Golf Group and Score Management")

# Initialize session state
if "members" not in st.session_state:
    st.session_state.members = members

if "groups" not in st.session_state:
    st.session_state.groups = []

if "scores" not in st.session_state:
    st.session_state.scores = {}
    for member in st.session_state.members:
        st.session_state.scores[member] = init_player_scores()

# Main tabs for app sections
tab1, tab2, tab3, tab4 = st.tabs(["Group Allocation", "Score Collection","Leader Board","Track Record"])

with tab1:
    # Tab for managing member details
    st.sidebar.title("Member List")

    with st.sidebar.expander("회원상세", expanded=True):
        for member, data in st.session_state.members.items():
            col1, col2 = st.columns([3, 2])
            with col1:
                st.markdown(f"#### {member}")
            with col2:
                st.session_state.members[member]["available"] = st.checkbox(
                    "참가", value=data["available"], key=f"avail_{member}")
            # st.divider()

    # Sidebar for managing members
    st.sidebar.title("Member Management")

    # Tab for adding/removing members
    with st.sidebar.expander("Add/Remove Members", expanded=True):
        # Add a new member
        new_member = st.text_input("Add a new member")
        new_member_gender = st.selectbox("Gender", ["Male", "Female"])
        
        if st.button("Add Member") and new_member:
            if new_member not in st.session_state.members:
                st.session_state.members[new_member] = {"available": True, "gender": new_member_gender}
                st.session_state.scores[new_member] = init_player_scores()
        
        # Remove members
        to_remove = st.multiselect("Select members to remove", list(st.session_state.members.keys()))
        if st.button("Remove Selected Members") and to_remove:
            for member in to_remove:
                if member in st.session_state.members:
                    del st.session_state.members[member]
                    if member in st.session_state.scores:
                        del st.session_state.scores[member]
    #---------------------------------------------------------------
    # Display member availability status
    st.write("## 월레회 참가자")

    # Create a dataframe for better visualization
    member_df = pd.DataFrame([
        {"Name": name, "Gender": data["gender"], "Available": data["available"]}
        for name, data in st.session_state.members.items()
    ])

    # Filter for available and unavailable members
    available_members = member_df[member_df["Available"]]
    unavailable_members = member_df[~member_df["Available"]]

    # Display available members as a list
    st.write(f"**Available Members ({len(available_members)}):**")
    if not available_members.empty:
        st.write(", ".join(available_members["Name"].tolist()))

    # Display unavailable members
    if not unavailable_members.empty:
        st.write(f"**Unavailable Members ({len(unavailable_members)}):**")
        st.write(", ".join(unavailable_members["Name"].tolist()))

    # Group allocation options
    st.write("## Group Allocation")
    col1, col2 = st.columns(2)

    with col1:
        # Removed balanced allocation option, keeping only Random
        allocation_method = "Random"
        st.write("**Allocation Method:** Random")

    with col2:
        max_group_size = st.slider("Maximum Players per Group", 
                                min_value=2, max_value=6, value=4)

    if st.button("Allocate Groups"):
        # Get available members
        available_member_names = [name for name, data in st.session_state.members.items() 
                                if data["available"]]
        
        # Only use random allocation since balanced option was removed
        st.session_state.groups = allocate_groups_random(available_member_names)

    # Display and allow manual adjustment of groups==============================
    if st.session_state.groups:
        st.write("## Current Groups")
        
        # Track all assigned members to prevent duplicates
        all_assigned = set()
        new_groups = []

        num_cols= len(st.session_state.groups)
        cols = st.columns(num_cols)
        
        for i, (col, group) in enumerate(zip(cols, st.session_state.groups)):
            with col:
                st.write(f"### Group {i+1}")
                
                # Get member details for this group
                group_data = []
                for member in group:
                    if member in st.session_state.members:
                        member_data = st.session_state.members[member]
                        group_data.append({
                            "Name": member,
                            "Gender": member_data["gender"]
                        })

                # Display group stats
                if group_data:
                    group_df = pd.DataFrame(group_data)
                    st.dataframe(group_df["Name"], use_container_width=True)
                    
                    # Calculate group statistics (only gender now since scores were removed)
                    gender_counts = group_df["Gender"].value_counts().to_dict()
                    st.write(f"**Gender Distribution:** " + ", ".join([f"{g}: {c}" for g, c in gender_counts.items()]))
                
                # Allow manual adjustments
                available_for_selection = [m for m in st.session_state.members if 
                                        st.session_state.members[m]["available"] and 
                                        (m in group or m not in all_assigned)]
                
                selected_members = st.multiselect(
                    f"Adjust Group {i+1}",
                    available_for_selection,
                    default=group,
                    key=f"group_{i}"
                )
                
                # Add selected members to tracking set and new groups
                for member in selected_members:
                    all_assigned.add(member)
                
                new_groups.append(selected_members)
        
        if st.button("Update Groups"):
            st.session_state.groups = new_groups
            st.rerun()
        
        # Export option
        st.write("## Export Groups")
        if st.button("Copy to Clipboard"):
            # Create a text representation of the groups
            groups_text = "Golf Groups:\n\n"
            for i, group in enumerate(st.session_state.groups, 1):
                groups_text += f"Group {i}:\n"
                for member in group:
                    member_data = st.session_state.members.get(member, {})
                    gender = member_data.get("gender", "N/A")
                    groups_text += f"- {member} ({gender})\n"
                groups_text += "\n"
            
            # Use JavaScript to copy to clipboard
            st.code(groups_text)
            st.success("Groups copied to clipboard! You can now paste this information elsewhere.")

# Score Collection Tab
with tab2:
    st.header("Score Collection")
    
    if not st.session_state.groups:
        st.warning("Please allocate groups first in the Group Allocation tab.")
    else:
        # Select which round to enter scores for
        round_selection = st.selectbox(
            "Select Round", 
            ["Round 1", "Round 2", "Round 3", "Round 4"],
            key="round_select"
        )
        
        round_key = round_selection.lower().replace(" ", "_")
        
        # Create tabs for each group
        group_tabs = st.tabs([f"Group {i+1}" for i in range(len(st.session_state.groups))])
        
        # Function to calculate stats
        def calculate_stats(player_scores, round_key):
            if not any(player_scores[round_key].values()):
                return None, None
                
            valid_scores = [score for score in player_scores[round_key].values() if score is not None]
            if not valid_scores:
                return None, None
                
            total = sum(valid_scores)
            holes_played = len(valid_scores)
            return total, round(total / holes_played, 1) if holes_played > 0 else None
            
        # Display and collect scores for each group
        for i, (tab, group) in enumerate(zip(group_tabs, st.session_state.groups)):
            with tab:
                st.subheader(f"Group {i+1} - {round_selection}")
                
                # Create a table-like interface for score entry
                col_labels = st.columns([2] + [1] * 9 + [1.5, 1.5])
                with col_labels[0]:
                    st.write("**Player**")
                for j in range(1, 10):
                    with col_labels[j]:
                        st.write(f"**H{j}**")
                with col_labels[10]:
                    st.write("**Total**")
                with col_labels[11]:
                    st.write("**Avg**")
                
                # Input fields for each player's scores
                for player in group:
                    if player in st.session_state.scores:
                        cols = st.columns([2] + [1] * 9 + [1.5, 1.5])
                        
                        with cols[0]:
                            st.write(player)
                        
                        # Holes input
                        for hole in range(1, 10):
                            hole_key = f"hole_{hole}"
                            with cols[hole]:
                                current_value = st.session_state.scores[player][round_key][hole_key]
                                # Fix: Use a default value of 1 (instead of 0) when no score is entered yet
                                display_value = 3 if current_value is None else int(current_value)
                                new_value = st.number_input(
                                    f"{player} - Hole {hole}",
                                    min_value=1, 
                                    max_value=20,
                                    value=display_value,
                                    label_visibility="collapsed",
                                    key=f"{player}_{round_key}_{hole_key}"
                                )
                                # Store score if it's different from the default (1)
                                if new_value != 1 or (current_value is not None and current_value != 1):
                                    st.session_state.scores[player][round_key][hole_key] = new_value
                                else:
                                    # Reset to None if it's still the default value
                                    st.session_state.scores[player][round_key][hole_key] = None
                        
                        # Calculate and display total and average
                        total, avg = calculate_stats(st.session_state.scores[player], round_key)
                        
                        with cols[10]:
                            st.write(f"**{total}**" if total is not None else "-")
                        
                        with cols[11]:
                            st.write(f"**{avg}**" if avg is not None else "-")
                
                # Save button for this group
                if st.button(f"Save Scores for Group {i+1}", key=f"save_group_{i}"):
                    st.success(f"Scores saved for Group {i+1}, {round_selection}")
    with tab3:
        # Summary statistics section
        st.header("Score Summary")
        
        if st.button("Generate Summary"):
            # Create summary dataframe
            summary_data = []
            
            # Get all players with scores
            all_players = [player for group in st.session_state.groups for player in group]
            
            for player in all_players:
                if player in st.session_state.scores:
                    player_data = {"Player": player}
                    
                    # Add round data
                    for r in range(1, 5):
                        round_key = f"round_{r}"
                        total, avg = calculate_stats(st.session_state.scores[player], round_key)
                        player_data[f"Round {r} Total"] = total if total is not None else "-"
                        # player_data[f"Round {r} Avg"] = avg if avg is not None else "-"
                    
                    # Calculate overall statistics
                    all_scores = []
                    for r in range(1, 5):
                        round_key = f"round_{r}"
                        scores = [score for score in st.session_state.scores[player][round_key].values() 
                                if score is not None]
                        all_scores.extend(scores)
                    
                    if all_scores:
                        player_data["Overall Total"] = sum(all_scores)
                        # player_data["Overall Avg"] = round(sum(all_scores) / len(all_scores), 1)
                        player_data["Best Score"] = min(all_scores) if all_scores else "-"
                        player_data["Worst Score"] = max(all_scores) if all_scores else "-"
                    else:
                        player_data["Overall Total"] = "-"
                        # player_data["Overall Avg"] = "-"
                        player_data["Best Score"] = "-"
                        player_data["Worst Score"] = "-"
                    
                    summary_data.append(player_data)
            
            # Display summary
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
                
                # Add download button for CSV
                if not summary_df.empty:
                    csv = summary_df.to_csv(index=False)
                    st.download_button(
                        label="Download Summary as CSV",
                        data=csv,
                        file_name="golf_scores_summary.csv",
                        mime="text/csv",
                    )
            else:
                st.warning("No scores have been entered yet.")
        
        # Visualize scores
        st.header("Score Visualization")
        
        # Only show if there's data to visualize
        any_scores = False
        for player in st.session_state.scores:
            for round_key in st.session_state.scores[player]:
                if any(score is not None for score in st.session_state.scores[player][round_key].values()):
                    any_scores = True
                    break
            if any_scores:
                break
        
        if any_scores:
            viz_type = st.selectbox(
                "Select Visualization", 
                ["Player Performance by Round", "Group Performance Comparison"]
            )
            
            if viz_type == "Player Performance by Round":
                # Allow selection of a player
                all_players = [player for group in st.session_state.groups for player in group]
                selected_player = st.selectbox("Select Player", all_players)
                
                if selected_player in st.session_state.scores:
                    # Create data for chart
                    chart_data = []
                    
                    for r in range(1, 5):
                        round_key = f"round_{r}"
                        for h in range(1, 10):
                            hole_key = f"hole_{h}"
                            score = st.session_state.scores[selected_player][round_key][hole_key]
                            if score is not None:
                                chart_data.append({
                                    "Round": f"Round {r}",
                                    "Hole": h,
                                    "Score": score
                                })
                    
                    if chart_data:
                        chart_df = pd.DataFrame(chart_data)
                        st.bar_chart(chart_df.pivot(index="Hole", columns="Round", values="Score"))
                    else:
                        st.info(f"No scores recorded for {selected_player} yet.")
            
            elif viz_type == "Group Performance Comparison":
                # Calculate and show group averages
                group_data = []
                
                for i, group in enumerate(st.session_state.groups):
                    group_scores = []
                    for player in group:
                        if player in st.session_state.scores:
                            for r in range(1, 5):
                                round_key = f"round_{r}"
                                scores = [score for score in st.session_state.scores[player][round_key].values() 
                                        if score is not None]
                                group_scores.extend(scores)
                    
                    if group_scores:
                        group_data.append({
                            "Group": f"Group {i+1}",
                            "Avg Score": sum(group_scores) / len(group_scores)
                        })
                
                if group_data:
                    group_df = pd.DataFrame(group_data)
                    st.bar_chart(data=group_df, x="Group", y="Avg Score")
                else:
                    st.info("Not enough score data to compare groups.")
        else:
            st.info("Enter some scores to enable visualizations.")
    with tab4:
        # Track Record Tab
        st.header("Track Record")

        uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
        
        if uploaded_file:
            # Load the existing Excel file
            existing_df = pd.read_excel(uploaded_file, sheet_name="Sheet1")
            st.write("Existing Data:")
            st.dataframe(existing_df)

            # Append summary_df data to existing dataframe
            if "summary_df" in locals():
                updated_df = pd.concat([existing_df, summary_df], ignore_index=True)
            st.write("Updated Data:")
            st.dataframe(updated_df)

            # Save the updated dataframe to a new Excel file
            updated_file = "updated_golf_scores.xlsx"
            updated_df.to_excel(updated_file, index=False)

            # Insert download button for the updated Excel file
            with open(updated_file, "rb") as file:
                st.download_button(
                    label="Download Updated Excel File",
                    data=file,
                    file_name=updated_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.warning("No summary data available to append.")

