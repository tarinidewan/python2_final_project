import pandas as pd
import matplotlib.pyplot as plt
from shiny import App, render, ui

# Load dataset
covid_merged = pd.read_csv('covid_final.csv')

# Calculate hospital beds per capita
covid_merged['beds_per_capita'] = (covid_merged['num_beds']/covid_merged['Projected Total Population']) * 100000

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