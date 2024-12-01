import pandas as pd
import matplotlib.pyplot as plt
from shiny import App, render, ui

# Load datasets
covid_vacc = pd.read_csv('C:/Users/Shreya Work/OneDrive/Documents/GitHub/python2_final_project/data/covid_vaccine_statewise.csv')
covid_test = pd.read_csv('C:/Users/Shreya Work/OneDrive/Documents/GitHub/python2_final_project/data/StatewiseTestingDetails.csv')
population = pd.read_csv('C:/Users/Shreya Work/OneDrive/Documents/GitHub/python2_final_project/data/state_population.csv')

# Convert dates to datetime
covid_vacc['Date'] = pd.to_datetime(covid_vacc['Updated On'], format='%d/%m/%Y')
covid_test['Date'] = pd.to_datetime(covid_test['Date'])

# Filter data for January to June 2021
covid_vacc = covid_vacc[(covid_vacc['Date'] > '2020-12-31') & (covid_vacc['Date'] <= '2021-06-30')]
covid_test = covid_test[(covid_test['Date'] > '2020-12-31') & (covid_test['Date'] <= '2021-06-30')]

# Aggregate data to monthly level
covid_vacc['Month'] = covid_vacc['Date'].dt.to_period('M')
covid_test['Month'] = covid_test['Date'].dt.to_period('M')

# Use last day of month value for cumulative metrics
covid_vacc_monthly = covid_vacc.sort_values('Date').groupby(['State', 'Month'])['Total Individuals Vaccinated'].last().reset_index()
covid_test_monthly = covid_test.sort_values('Date').groupby(['State', 'Month'])['TotalSamples'].last().reset_index()

# Merge datasets
covid_merged = pd.merge(covid_vacc_monthly, covid_test_monthly, on=['State', 'Month'], how='inner')
covid_merged = pd.merge(covid_merged, population, on='State', how='left')

# Calculate testing and vaccination rates
covid_merged['testing_rate'] = covid_merged['TotalSamples'] / covid_merged['Projected Total Population'] * 100000
covid_merged['vaccination_rate'] = covid_merged['Total Individuals Vaccinated'] / covid_merged['Projected Total Population'] * 100

# Shiny app UI
app_ui = ui.page_fluid(
    ui.h2("COVID-19 Testing and Vaccination Analysis (Jan-Jun 2021)"),
    ui.row(
        ui.column(4,
            ui.input_switch("compare_states", "Compare Two States", value=False),
            ui.input_select("state1", "Select First State", 
                          choices=sorted(covid_merged['State'].unique().tolist())),
            ui.panel_conditional(
                "input.compare_states",
                ui.input_select("state2", "Select Second State", 
                              choices=sorted(covid_merged['State'].unique().tolist()))
            )
        ),
        ui.column(8,
            ui.output_plot("scatter_plot")
        )
    )
)

def server(input, output, session):
    @output
    @render.plot
    def scatter_plot():
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot first state
        state1_data = covid_merged[covid_merged['State'] == input.state1()]
        ax.scatter(state1_data['testing_rate'], state1_data['vaccination_rate'], 
                  label=input.state1(), color='teal', alpha=0.6)
        
        # Plot second state if comparison is enabled
        if input.compare_states():
            state2_data = covid_merged[covid_merged['State'] == input.state2()]
            ax.scatter(state2_data['testing_rate'], state2_data['vaccination_rate'], 
                      label=input.state2(), color='darkorange', alpha=0.6)
        
        ax.set_xlabel('Testing Rate per 100,000 population')
        ax.set_ylabel('Vaccination Rate (%)')
        if input.compare_states():
            ax.set_title(f'Testing Rate vs Vaccination Rate Comparison:\n{input.state1()} vs {input.state2()}')
        else:
            ax.set_title(f'Testing Rate vs Vaccination Rate for {input.state1()}')
        
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        return fig

app = App(app_ui, server)

if __name__ == "__main__":
    app.run()