import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
from statsmodels.formula.api import ols
from shiny import App, render, ui

# Load datasets
covid_vacc = pd.read_csv('C:/Users/Shreya Work/OneDrive/Documents/GitHub/python2_final_project/data/covid_vaccine_statewise.csv')
covid_test = pd.read_csv('C:/Users/Shreya Work/OneDrive/Documents/GitHub/python2_final_project/data/StatewiseTestingDetails.csv')
population = pd.read_csv('C:/Users/Shreya Work/OneDrive/Documents/GitHub/python2_final_project/data/state_population.csv')

# Convert dates to datetime
covid_vacc['Date'] = pd.to_datetime(covid_vacc['Updated On'], format='%d/%m/%Y')
covid_test['Date'] = pd.to_datetime(covid_test['Date'])

# Filter data for 2021 onwards
covid_vacc = covid_vacc[covid_vacc['Date'] > '2020-12-31']
covid_test = covid_test[covid_test['Date'] > '2020-12-31']

# Aggregate data to monthly level
covid_vacc['Month'] = covid_vacc['Date'].dt.to_period('M')
covid_test['Month'] = covid_test['Date'].dt.to_period('M')

covid_vacc_monthly = covid_vacc.groupby(['State', 'Month'])['Total Individuals Vaccinated'].max().reset_index()
covid_test_monthly = covid_test.groupby(['State', 'Month'])['TotalSamples'].max().reset_index()

# Merge datasets
covid_merged = pd.merge(covid_vacc_monthly, covid_test_monthly, on=['State', 'Month'], how='inner')
covid_merged = pd.merge(covid_merged, population, on='State', how='left')

# Calculate testing and vaccination rates
covid_merged['testing_rate'] = covid_merged['TotalSamples'] / covid_merged['Projected Total Population'] * 100000
covid_merged['vaccination_rate'] = covid_merged['Total Individuals Vaccinated'] / covid_merged['Projected Total Population'] * 100

# Save the merged dataset
covid_merged.to_csv('covid_final.csv', index=False)

print(covid_merged.head())
print(f"Number of unique states: {covid_merged['State'].nunique()}")

# Plotting
plt.figure(figsize=(12, 6))
plt.boxplot([covid_merged[covid_merged['State'] == state]['testing_rate'] for state in covid_merged['State'].unique()],
            labels=covid_merged['State'].unique())
plt.title('Distribution of Testing Rates by State')
plt.xlabel('State')
plt.ylabel('Testing Rate per 100,000 population')
plt.xticks(rotation=90)
plt.grid(axis='y')
plt.tight_layout()
plt.savefig('testing_distribution.png')
plt.close()

plt.figure(figsize=(12, 6))
for state in covid_merged['State'].unique():
    state_data = covid_merged[covid_merged['State'] == state]
    plt.plot(state_data['Month'].astype(str), state_data['vaccination_rate'], label=state)

plt.title('Vaccination Progress by State Over Time')
plt.xlabel('Month')
plt.ylabel('Vaccination Rate (%)')
plt.legend(title='State', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('vaccination_progress.png')
plt.close()

# Analysis
correlation = covid_merged[['testing_rate', 'vaccination_rate']].corr().iloc[0, 1]
print(f"Correlation between testing rate and vaccination rate: {correlation:.2f}")

model = ols('vaccination_rate ~ testing_rate', data=covid_merged).fit()
print(model.summary())

# Shiny app
app_ui = ui.page_fluid(
    ui.input_select("state", "Select State", choices=covid_merged['State'].unique().tolist()),
    ui.output_plot("scatter_plot")
)

def server(input, output, session):
    @output
    @render.plot
    def scatter_plot():
        state_data = covid_merged[covid_merged['State'] == input.state()]
        
        fig, ax = plt.subplots()
        ax.scatter(state_data['testing_rate'], state_data['vaccination_rate'])
        ax.set_xlabel('Testing Rate per 100,000 population')
        ax.set_ylabel('Vaccination Rate (%)')
        ax.set_title(f'Testing Rate vs Vaccination Rate for {input.state()}')
        
        return fig

app = App(app_ui, server)

if __name__ == "__main__":
    app.run()
