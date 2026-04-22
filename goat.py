import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from animal_params import ANIMAL_PARAMS

API_URL = "http://localhost:8000/simulate"

st.set_page_config(page_title="Livestock Population Simulation", layout="wide")
ANIMAL_EMOJIS = {
    "Goat": "🐐",
    "Cow": "🐮", 
    "Buffalo": "🐃"
}

animal_type = st.sidebar.selectbox(
    "Select Animal",
    ["Goat", "Cow", "Buffalo"]
)
animal_emoji = ANIMAL_EMOJIS[animal_type]

params = ANIMAL_PARAMS[animal_type.lower()]
animal_label = animal_type
p_female_kid_default = params["p_female_kid"]
p_get_pregnant_default = params["p_get_pregnant"]
p_kids_default = params["p_kids"]
p_sell_male_default = params["p_sell_male"]
p_sell_female_default = params["p_sell_female"]
animal_label = animal_type.capitalize()

st.title(f"{animal_emoji} {animal_label} Population Simulation Dashboard")

# ---------------- Sidebar Inputs ----------------
st.sidebar.header(f"Initial {animal_label} Population")

st.sidebar.subheader("Female Age Distribution")

init_female_total = st.sidebar.number_input(f"Total Female {animal_label}s", min_value=0, value=10)

female_age_counts = []
for i, (min_age, max_age) in enumerate(params['female_age_ranges']):
    label = f"Age {min_age}–{max_age} months" if max_age < 1000 else f"Age {min_age}+ months"
    count = st.sidebar.number_input(label, min_value=0, value=init_female_total // len(params['female_age_ranges']))
    female_age_counts.append(count)

if sum(female_age_counts) != init_female_total:
    st.error("Sum of female age groups must equal total females")
    st.stop()



init_male = st.sidebar.number_input(
    f"Initial Male {animal_type.capitalize()}s", min_value=0, value=5
)
init_male_age = st.sidebar.number_input(
    f"Initial Male Age (months)", min_value=0, value=1
)

st.sidebar.header("Simulation Parameters")
# iterations = st.sidebar.number_input("Iterations", min_value=1, value=1)
sim_duration_months = st.sidebar.number_input(
    "Simulation Duration (months)", min_value=1, value=12
)

start_date = st.sidebar.date_input("Simulation Start Date", value=datetime.today())

st.sidebar.subheader("Age Parameters")
t_max_male = st.sidebar.number_input(
    "Max Male Age",
    value=params["t_max_male"],
    disabled=True
)

t_max_female = st.sidebar.number_input(
    "Max Female Age", 
    value=params["t_max_female"], 
    disabled=True
)

t_prod_start = st.sidebar.number_input(
    "Production Start Age", 
    value=params["t_prod_start"], 
    disabled=True
)
t_prod_end = st.sidebar.number_input(
    "Production End Age", 
    value=params["t_prod_end"], disabled=True
)

t_preg_duration = st.sidebar.number_input(
    "Pregnancy Duration",
    value=params["t_preg_duration"],
    disabled=True
)



t_preg_gap = st.sidebar.number_input("Pregnancy Gap", value=params["t_preg_gap"])

st.sidebar.subheader("Sell Parameters")
t_sell_min_male = st.sidebar.number_input("Sell Male Age", value=params["t_sell_min_male"])
t_sell_min_female = st.sidebar.number_input("Sell Female Age", value=params["t_sell_min_female"])

st.sidebar.subheader("Probabilities")
p_prod_start = st.sidebar.slider("P survive to prod start", 0.0, 1.0, value=params["p_prod_start"])
p_prod_end = st.sidebar.slider("P survive to prod end", 0.0, 1.0, value=params["p_prod_end"])
p_female_kid = st.sidebar.slider("P Female Kid", 0.0, 1.0, value= p_female_kid_default)
p_get_pregnant = st.sidebar.slider("P Get Pregnant", 0.0, 1.0, value=p_get_pregnant_default)


# Kids distribution input
st.sidebar.subheader("Kids Birth Distribution")
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    p_kid_1 = st.number_input("1 Kid", min_value=0.0, max_value=1.0, value=p_kids_default[0])
with col2:
    p_kid_2 = st.number_input("2 Kids", min_value=0.0, max_value=1.0, value=p_kids_default[1])
with col3:
    p_kid_3 = st.number_input("3+ Kids", min_value=0.0, max_value=1.0,  value=p_kids_default[2] if len(p_kids_default) > 2 else 0.0)

p_sell_male = st.sidebar.slider("P Sell Male", 0.0, 1.0, value=p_sell_male_default)
p_sell_female = st.sidebar.slider("P Sell Female", 0.0, 1.0, value=p_sell_female_default)
# 🔥 NEW SECTION: Death Probabilities (after p_sell_female slider)
st.sidebar.subheader("⚰️ Death Probabilities")

params = ANIMAL_PARAMS[animal_type.lower()]
death_probs = params["death_probs"]

# Initialize session state
if f"{animal_type.lower()}_death_probs" not in st.session_state:
    st.session_state[f"{animal_type.lower()}_death_probs"] = [
        [float(min_age), float(max_age), float(prob)] for min_age, max_age, prob in death_probs
    ]

custom_death_probs = []
for i, (min_age, max_age, default_prob) in enumerate(death_probs):
    age_range = f"{min_age}-{max_age-1}" if max_age < 1000 else f"{min_age}+"
    
    prob = st.sidebar.slider(
        f"Age {age_range} months",
        min_value=0.0, max_value=0.20, value=st.session_state[f"{animal_type.lower()}_death_probs"][i][2],
        step=0.001, format="%.3f",
        key=f"death_prob_{animal_type.lower()}_{i}"
    )
    
    # Update session state
    st.session_state[f"{animal_type.lower()}_death_probs"][i][2] = prob
    custom_death_probs.append([float(min_age), float(max_age), prob])

expand_ownership = st.sidebar.checkbox("Expand Ownership", value=False)

# ---------------- Run Simulation ----------------
if st.button("▶ Predict Population Growth"):
  
    if init_male_age > t_max_male:
        st.error(
            f"❌ Male {animal_label} age ({init_male_age}) "
            f"cannot exceed max age ({t_max_male})"
        )
        st.stop()

    payload = {
        "animal_type": animal_type.lower(),

        "init_female_total": init_female_total,
        "init_female_by_age": female_age_counts,  

        "init_male_goats": init_male,
        "init_male_age": init_male_age,

        "t_preg_gap": t_preg_gap,
        "t_sell_min_male": t_sell_min_male,
        "t_sell_min_female": t_sell_min_female,

        "p_prod_start": p_prod_start,
        "p_prod_end": p_prod_end,
        "p_female_kid": p_female_kid,
        "p_get_pregnant": p_get_pregnant,
        "p_kids": [p_kid_1, p_kid_2, p_kid_3],
        "p_sell_male": p_sell_male,
        "p_sell_female": p_sell_female,
        "death_probs": st.session_state[f"{animal_type.lower()}_death_probs"],
        "expand_ownership": expand_ownership,
        "sim_duration_months": sim_duration_months,
    }

    try:
        with st.spinner("Running simulation..."):
            response = requests.post(API_URL, json=payload , timeout=150)
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
    except requests.exceptions.Timeout:
        st.error("❌ Server timeout. Simulation is taking too long.")
        st.stop()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to FastAPI server. Is it running?")
        st.stop()

    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        
        st.success("✅ Simulation completed successfully!")
        
        # Calculate additional statistics
        
        initial_total = init_male + init_female_total

        final_total = df["num_male"].iloc[-1] + df["num_female"].iloc[-1]
        
        # Calculate births (approximation based on population change and deaths)
        # Births = (Final population + Deaths) - Initial population
        total_sold_male = df["sold_male"].iloc[-1]
        total_sold_female = df["sold_female"].iloc[-1]
        total_sold = total_sold_male + total_sold_female
        total_deaths_male = df["dead_male"].iloc[-1]
        total_deaths_female = df["dead_female"].iloc[-1]
        total_deaths = total_deaths_male + total_deaths_female

        
        total_births = (final_total + total_deaths + total_sold) - initial_total

        
        # Estimate male/female births based on probability
        estimated_male_births = int(total_births * (1 - p_female_kid))
        estimated_female_births = int(total_births * p_female_kid)
        
        # ------------------ Display Statistics in Columns ------------------
        st.subheader("📊 Simulation Summary")

        # ---------- Population Snapshot ----------

        colA, colB, colC , colD , colE , colF = st.columns(6)

        with colA:
            st.metric(f"Initial Male {animal_label}", init_male)
            st.metric(f"Initial Female {animal_label}", init_female_total)
            st.metric("Initial Total", initial_total)

        with colB:
            st.metric(f"Final Male {animal_label}", df["num_male"].iloc[-1])
            st.metric(f"Final Female {animal_label}", df["num_female"].iloc[-1])
            st.metric("Final Total", final_total)

        with colC:
            st.metric("Estimated New Male Births", estimated_male_births)
            st.metric("Estimated New Female Births", estimated_female_births)
            st.metric("Estimated New Total Births", estimated_male_births + estimated_female_births)
            

        with colD:
            st.metric("Males Sold", total_sold_male)
            st.metric("Females Sold", total_sold_female)
            st.metric("Total Sold", total_sold)

        with colE:
            st.metric("Male Deaths (Natural)", total_deaths_male)
            st.metric("Female Deaths (Natural)", total_deaths_female)
            st.metric("Total Natural Deaths", total_deaths_male + total_deaths_female)
            
        with colF:
            st.metric(
                "Net Population Change",
                final_total - initial_total,
                delta=final_total - initial_total,
                delta_color="normal" if (final_total - initial_total) >= 0 else "inverse",
            )

        # ------------------ Detailed Population Breakdown ------------------
        st.subheader(f"{animal_emoji} Detailed Population Analysis")

        
        # ------------------ Add new tab for deaths and births ------------------
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Population Trends", "💰 Selling Analysis", "⚰️ Deaths & Births", "📋 Final Results"])

        # Existing tab1: Population Trends
        with tab1:
            fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            ax1.plot(df["months"], df["num_male"], label="Male Population", color='blue', linewidth=2)
            ax1.plot(df["months"], df["num_female"], label="Female Population", color='magenta', linewidth=2)
            ax1.plot(df["months"], df["num_male"] + df["num_female"], label="Total Population", color='green', linewidth=2, linestyle='--')
            ax1.set_title(f"{animal_label} Population Over Time")
            ax1.set_xlabel("Months")
            ax1.set_ylabel(f"Number of {animal_label}")

            ax1.legend()
            ax1.grid(True, alpha=0.3)

            ax2.plot(df["months"], df["sold_male"], label="Cumulative Male Sold", color='darkblue', linewidth=2)
            ax2.plot(df["months"], df["sold_female"], label="Cumulative Female Sold", color='darkmagenta', linewidth=2)
            ax2.set_title("Cumulative Selling Over Time")
            ax2.set_xlabel("Months")
            ax2.set_ylabel("Cumulative Selling")
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig1)

# ------------------ New Tab: Deaths & Births ------------------
        with tab3:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Deaths graph
            ax1.plot(df["months"], df["dead_male"], label="Male Deaths", color='red', linewidth=2)
            ax1.plot(df["months"], df["dead_female"], label="Female Deaths", color='orange', linewidth=2)
            ax1.set_title(f"{animal_label} Deaths Over Time")
            ax1.set_xlabel("Months")
            ax1.set_ylabel("Deaths")
            ax1.legend()
            ax1.grid(True, alpha=0.3)
    
    # Kids born graph
    # Assuming your API returns 'born_male' and 'born_female' cumulative or monthly
            male_births = np.diff(df["born_male"].tolist(), prepend=0) if "born_male" in df.columns else None
            female_births = np.diff(df["born_female"].tolist(), prepend=0) if "born_female" in df.columns else None
    
            if male_births is not None and female_births is not None:
                ax2.plot(df["months"], male_births, label="Male Kids Born", color='blue', linewidth=2)
                ax2.plot(df["months"], female_births, label="Female Kids Born", color='magenta', linewidth=2)
                ax2.set_title("Kids Born Over Time")
                ax2.set_xlabel("Months")
                ax2.set_ylabel("Number of Kids Born")
                ax2.legend()
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(0.5, 0.5, "Birth data not available from API", ha='center', va='center')
    
            plt.tight_layout()
        st.pyplot(fig)

        with tab2:
            col1, col2 = st.columns(2)
    
            with col1:
        # Selling distribution pie chart
                fig2, ax = plt.subplots(figsize=(6, 6))
                sold_labels = ['Male Sold', 'Female Sold']
                sold_sizes = [total_sold_male, total_sold_female]
                colors = ['lightblue', 'lightpink']
                ax.pie(sold_sizes, labels=sold_labels, autopct='%1.1f%%', colors=colors, startangle=90)
                ax.set_title("Selling Distribution by Gender")
                st.pyplot(fig2)
    
            with col2:
                # Monthly selling rate bar chart
                fig3, ax = plt.subplots(figsize=(6, 6))
                months = df["months"].tolist()
                male_sold_rate = np.diff(df["sold_male"].tolist(), prepend=0)
                female_sold_rate = np.diff(df["sold_female"].tolist(), prepend=0)

                 # Define x positions and bar width
                x = np.arange(len(months))
                width = 0.35

                ax.bar(x - width/2, male_sold_rate, width, label='Male Sold/Month', color='blue', alpha=0.7)
                ax.bar(x + width/2, female_sold_rate, width, label='Female Sold/Month', color='magenta', alpha=0.7)

                ax.set_xlabel("Months")
                ax.set_ylabel("Selling per Month")
                ax.set_title("Monthly Selling Rates")
                ax.legend()
                ax.grid(True, alpha=0.3)

        # Show only every 12th month label for readability
                ax.set_xticks(x[::12])
                ax.set_xticklabels(months[::12])

                st.pyplot(fig3)

        
        with tab4:
            st.subheader("🎯 Final Simulation Results")
            
            # Create a results dataframe
            results_data = {
                "Metric": ["Total Population", 
                           "Male Population", 
                           "Female Population", 
                           "Total Sold",
                           "Male Sold", 
                           "Female Sold", 
                           "Estimated Births",
                          "Net Population Change"],
                "Value": [final_total, 
                          df["num_male"].iloc[-1], 
                          df["num_female"].iloc[-1],
                          total_deaths, 
                          total_deaths_male, 
                          total_deaths_female,
                          total_births, 
                          final_total - initial_total,
                        ]
            }
            
            results_df = pd.DataFrame(results_data)
            st.dataframe(results_df, use_container_width=True)
           
        # ------------------ Download Results ------------------
        st.subheader("💾 Export Results")
        
        # Convert to downloadable format
        csv = df.to_csv(index=False)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="📥 Download Simulation Data (CSV)",
                data=csv,
                file_name="goat_simulation_results.csv",
                mime="text/csv",
            )
        with col2:
            # Create summary report
            summary_text = f"""{animal_label} Simulation Results
========================
Initial Population: {initial_total}
Final Population: {final_total}
Net Change: {final_total - initial_total}
Total Sold: {total_deaths}
Estimated Births: {total_births}
Simulation Duration: {sim_duration_months} months
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            st.download_button(
                label="📄 Download Summary Report (TXT)",
                data=summary_text,
                file_name="simulation_summary.txt",
                mime="text/plain",
            )
        
        # ------------------ Raw Data View (Optional) ------------------
        with st.expander("📊 View Raw Data"):
            st.dataframe(df)
            
    else:
        st.error(f"❌ Simulation failed with error: {response.text}")

# ------------------ Instructions Section ------------------
st.sidebar.markdown("---")
with st.sidebar.expander("📖 How to Use"):
    st.markdown("""
    1. **Set Initial Population**: Enter starting number of goats
    2. **Adjust Parameters**: Modify age, probability, and selling parameters
    3. **Run Simulation**: Click the 'Run Simulation' button
    4. **Analyze Results**: View different tabs for detailed analysis
    
    **Key Metrics Shown**:
    - Population growth/decline
    - Selling statistics by gender
    - Estimated births
    - Family dynamics
    - Final prediction results
    """)

# ------------------ About Section ------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Goat Population Model")
st.sidebar.markdown("""
This simulation models:
- Birth & pregnancy dynamics
- Age-based mortality
- Selling probabilities
- Family/ownership expansion
""")