import pandas as pd
import matplotlib.pyplot as plt
from shiny import App, render, ui

# Load datasets
covid_vacc = pd.read_csv('C:/Users/Shreya Work/OneDrive/Documents/GitHub/python2_final_project/data/covid_vaccine_statewise.csv')
covid_test = pd.read_csv('C:/Users/Shreya Work/OneDrive/Documents/GitHub/python2_final_project/data/StatewiseTestingDetails.csv')
population = pd.read_csv('C:/Users/Shreya Work/OneDrive/Documents/GitHub/python2_final_project/data/state_population.csv')
hospital = pd.read_csv('C:/Users/Shreya Work/OneDrive/Documents/GitHub/python2_final_project/data/Hospital_India.csv')

# Data preprocessing (as in your original code)
covid_vacc['Date'] = pd.to_datetime(covid_vacc['Updated On'], format='%d/%m/%Y')
covid_test['Date'] = pd.to_datetime(covid_test['Date'])

covid_vacc = covid_vacc.rename(columns={'Total Doses Administered': 'total_doses'})
covid_vacc = covid_vacc[~covid_vacc['total_doses'].isna()]
covid_vacc = covid_vacc.sort_values(['State', 'Date'])

covid_vacc['lagged_value'] = covid_vacc.groupby('State')['total_doses'].shift(1)
covid_vacc['lagged_value'] = covid_vacc['lagged_value'].fillna(0)
covid_vacc['total_doses_day'] = covid_vacc['total_doses'] - covid_vacc['lagged_value']
covid_vacc = covid_vacc[covid_vacc['total_doses_day']>=0]

covid_test = covid_test.sort_values(['State', 'Date'])
covid_test['lagged_value'] = covid_test.groupby('State')['TotalSamples'].shift(1)
covid_test['lagged_value'] = covid_test['lagged_value'].fillna(0)
covid_test['total_samples_day'] = covid_test['TotalSamples'] - covid_test['lagged_value']
covid_test = covid_test[covid_test['total_samples_day']>=0]

covid_vacc = covid_vacc[(covid_vacc['Date'] > '2020-12-31')]
covid_test = covid_test[(covid_test['Date'] > '2020-12-31')]

covid_vacc['Month'] = covid_vacc['Date'].dt.strftime('%m').astype(int)
covid_test['Month'] = covid_test['Date'].dt.strftime('%m').astype(int)

covid_vacc_monthly = covid_vacc.sort_values('Date').groupby(['State', 'Month'])['total_doses_day'].sum().reset_index()
covid_test_monthly = covid_test.sort_values('Date').groupby(['State', 'Month'])['total_samples_day'].sum().reset_index()

covid_merged = pd.merge(covid_vacc_monthly, covid_test_monthly, on=['State', 'Month'], how='inner')
covid_merged = pd.merge(covid_merged, population, on='State', how='left')

covid_merged['testing_rate'] = 100*(covid_merged['total_samples_day'] / covid_merged['Projected Total Population'])
covid_merged['vaccination_rate'] = 100*(covid_merged['total_doses_day'] / covid_merged['Projected Total Population'])

# Process hospital data
hospital = hospital.rename(columns={'State/UT/India': 'State', 'No. of beds available in public facilities': 'num_beds'})
hospital['State'] = hospital['State'].replace({'Andaman & Nicobar Islands': 'Andaman and Nicobar Islands', 'Jammu & Kashmir': 'Jammu and Kashmir'})
hospital['num_beds'] = pd.to_numeric(hospital['num_beds'], errors='coerce')

# Merge hospital data
covid_merged = pd.merge(covid_merged, hospital[['State', 'num_beds']], on='State', how='left')

# Calculate hospital beds per capita
covid_merged['beds_per_capita'] = covid_merged['num_beds'] / covid_merged['Projected Total Population'] * 100000

# Shiny app UI
app_ui = ui.page_fluid(
    ui.h2("COVID-19 Testing, Vaccination, and Healthcare Infrastructure Analysis (Jan-Aug 2021)"),
    ui.row(
        ui.column(4,
            ui.input_select("state1", "Select First State", 
                          choices=sorted(covid_merged['State'].unique().tolist())),
            ui.input_select("graph_type", "Select Graph Type", 
                          choices=["Testing vs Vaccination", "Testing vs Hospital Beds", "Vaccination vs Hospital Beds"]),
            ui.input_switch("compare_states", "Compare Two States", value=False),
            ui.panel_conditional(
                "input.compare_states",
                ui.input_select("state2", "Select Second State", 
                              choices=sorted(covid_merged['State'].unique().tolist()))
            )
        ),
        ui.column(8,
            ui.output_plot("comparison_plot")
        )
    )
)

def server(input, output, session):
    @output
    @render.plot
    def comparison_plot():
        fig, ax = plt.subplots(figsize=(10, 6))
        
        def plot_state_data(state, color):
            state_data = covid_merged[covid_merged['State'] == state]
            if input.graph_type() == "Testing vs Vaccination":
                ax.scatter(state_data['testing_rate'], state_data['vaccination_rate'], 
                           label=state, color=color, alpha=0.6)
                ax.set_xlabel('Testing Rate (%)')
                ax.set_ylabel('Vaccination Rate (%)')
            elif input.graph_type() == "Testing vs Hospital Beds":
                ax.scatter(state_data['beds_per_capita'], state_data['testing_rate'], 
                           label=state, color=color, alpha=0.6)
                ax.set_xlabel('Hospital Beds per 100,000 Population')
                ax.set_ylabel('Testing Rate (%)')
            else:  # Vaccination vs Hospital Beds
                ax.scatter(state_data['beds_per_capita'], state_data['vaccination_rate'], 
                           label=state, color=color, alpha=0.6)
                ax.set_xlabel('Hospital Beds per 100,000 Population')
                ax.set_ylabel('Vaccination Rate (%)')
        
        plot_state_data(input.state1(), 'teal')
        if input.compare_states():
            plot_state_data(input.state2(), 'darkorange')
        
        if input.compare_states():
            ax.set_title(f'{input.graph_type()} Comparison:\n{input.state1()} vs {input.state2()}')
        else:
            ax.set_title(f'{input.graph_type()} for {input.state1()}')
        
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        return fig

app = App(app_ui, server)