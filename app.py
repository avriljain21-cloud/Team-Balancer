import streamlit as st
import pandas as pd
import random
from io import BytesIO

st.set_page_config(page_title="AI Tennis Team Balancer", layout="wide")
st.title(" Tennis Team Balancer")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.title()

    # Convert numeric columns
    for col in ["Utr", "Wins", "Losses", "Game_Diff"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # -------- Strength Calculation --------
    df["Strength"] = 0

    if "Utr" in df.columns:
        df["Strength"] += df["Utr"] * 10

    if "Wins" in df.columns and "Losses" in df.columns:
        df["Win_Rate"] = df["Wins"] / (df["Wins"] + df["Losses"] + 1)
        df["Strength"] += df["Win_Rate"] * 50

    if "Game_Diff" in df.columns:
        df["Strength"] += df["Game_Diff"] * 5

    if "Playstyle" in df.columns:
        df["Strength"] = df.apply(
            lambda r: r["Strength"] * 1.02 if str(r["Playstyle"]).upper()=="N"
            else r["Strength"] * 1.01,
            axis=1
        )

    df["Strength"] = df["Strength"].round(2)

    st.subheader("Players")
    show_cols = [c for c in ["Name","Strength","Playstyle"] if c in df.columns]
    st.dataframe(df[show_cols])

    num_players = len(df)

    num_teams = st.number_input(
        "Number of Teams",
        min_value=1,
        max_value=num_players,
        value=min(2, num_players)
    )

    # Shuffle seed
    if "shuffle_seed" not in st.session_state:
        st.session_state.shuffle_seed = 0

    generate = st.button("Generate Balanced Teams")
    shuffle = st.button("🔀 Shuffle Teams")

    # -------- AI Team Balancer --------
    if generate or shuffle:

        if shuffle:
            st.session_state.shuffle_seed += 1

        random.seed(st.session_state.shuffle_seed)

        players = df.to_dict("records")

        best_teams = None
        best_strengths = None
        best_score = float("inf")

        for _ in range(2000):

            random.shuffle(players)

            teams = [[] for _ in range(num_teams)]
            strengths = [0] * num_teams

            for p in players:
                idx = strengths.index(min(strengths))
                teams[idx].append(p)
                strengths[idx] += p["Strength"]

            score = max(strengths) - min(strengths)

            if score < best_score:
                best_score = score
                best_teams = teams
                best_strengths = strengths

        st.subheader("Balanced Teams")

        all_teams = []

        for i, team in enumerate(best_teams):

            team_df = pd.DataFrame(team)
            team_df = team_df.sort_values("Strength", ascending=False)

            st.markdown(f"### Team {i+1} — Total Strength: {best_strengths[i]:.2f}")

            cols = [c for c in ["Name","Strength","Playstyle"] if c in team_df.columns]
            st.dataframe(team_df[cols])

            team_df["Team"] = f"Team {i+1}"
            all_teams.append(team_df)

        diff = max(best_strengths) - min(best_strengths)

        st.success(f"Strength Difference Between Teams: {diff:.2f}")

        # Excel download
        final_df = pd.concat(all_teams)

        buffer = BytesIO()
        final_df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            "Download Teams Excel",
            data=buffer,
            file_name="balanced_teams.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
st.caption("Results Found By AI")


