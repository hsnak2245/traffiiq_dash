import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os
import warnings

# Suppress the specific pandas warnings
warnings.filterwarnings('ignore', category=pd.core.common.SettingWithCopyWarning)

class QatarAccidentsAnimation:
    def __init__(self, csv_path):
        # Read CSV with proper options to handle mixed types
        self.df = pd.read_csv(csv_path, low_memory=False)
        self.years = sorted(self.df['ACCIDENT_YEAR'].unique())
        
    def create_severity_animation(self, category='NATIONALITY_GROUP_OF_ACCIDENT_'):
        """Create an animated stacked bar chart for accident severity."""
        frames = []
        for year in self.years:
            # Create a copy of the filtered data
            year_data = self.df[self.df['ACCIDENT_YEAR'] == year].copy()
            severity_counts = year_data.groupby([category, 'ACCIDENT_SEVERITY']).size().unstack().fillna(0)
            
            frame_data = []
            for severity in severity_counts.columns:
                frame_data.append(
                    go.Bar(
                        name=severity,
                        x=severity_counts.index,
                        y=severity_counts[severity],
                        text=severity_counts[severity].round(0).astype(int),
                        textposition='auto',
                    )
                )
            
            frames.append(go.Frame(
                data=frame_data,
                name=str(year),
                traces=[i for i in range(len(severity_counts.columns))]
            ))

        # Create the base figure with initial data
        initial_year = self.years[0]
        initial_data = self.df[self.df['ACCIDENT_YEAR'] == initial_year].copy()
        initial_counts = initial_data.groupby([category, 'ACCIDENT_SEVERITY']).size().unstack().fillna(0)

        fig = go.Figure(
            data=[
                go.Bar(
                    name=severity,
                    x=initial_counts.index,
                    y=initial_counts[severity],
                    text=initial_counts[severity].round(0).astype(int),
                    textposition='auto'
                ) for severity in initial_counts.columns
            ],
            frames=frames
        )

        # Add animation controls
        fig.update_layout(
            updatemenus=[{
                'buttons': [
                    {
                        'args': [None, {'frame': {'duration': 1000, 'redraw': True},
                                      'fromcurrent': True}],
                        'label': 'Play',
                        'method': 'animate'
                    },
                    {
                        'args': [[None], {'frame': {'duration': 0, 'redraw': True},
                                        'mode': 'immediate',
                                        'transition': {'duration': 0}}],
                        'label': 'Pause',
                        'method': 'animate'
                    }
                ],
                'type': 'buttons'
            }],
            sliders=[{
                'currentvalue': {'prefix': 'Year: '},
                'steps': [
                    {'args': [[str(year)], {'frame': {'duration': 0, 'redraw': True},
                                          'mode': 'immediate',
                                          'transition': {'duration': 0}}],
                     'label': str(year),
                     'method': 'animate'} for year in self.years
                ]
            }],
            title=f'Accident Severity by {category} (Animated)',
            barmode='stack',
            colorway=['rgb(245,245,220)', 'rgb(176,48,96)', 'rgb(139,0,0)']
        )
        
        return fig

    def create_age_animation(self):
        """Create an animated scatter plot for age distribution."""
        frames = []
        for year in self.years:
            # Create a copy of the filtered data
            year_data = self.df[self.df['ACCIDENT_YEAR'] == year].copy()
            
            # Calculate ages properly using loc
            year_data.loc[:, 'AGE'] = year_data['BIRTH_YEAR_OF_ACCIDENT_PERPETR'].apply(
                lambda x: year - x if pd.notnull(x) else None
            )
            
            # Filter age range
            valid_age_mask = (year_data['AGE'] >= 0) & (year_data['AGE'] <= 90)
            year_data = year_data[valid_age_mask]
            
            # Calculate statistics
            age_counts = year_data.groupby('AGE').size().reset_index(name='ACCIDENT_COUNT')
            mean_age = year_data['AGE'].mean()

            frames.append(go.Frame(
                data=[go.Scatter(
                    x=age_counts['AGE'],
                    y=age_counts['ACCIDENT_COUNT'],
                    mode='markers',
                    marker=dict(
                        size=age_counts['ACCIDENT_COUNT'],
                        sizeref=2.*max(age_counts['ACCIDENT_COUNT'])/(40.**2),
                        sizemin=4
                    ),
                    name=f'Year {year}'
                )],
                name=str(year),
                layout=go.Layout(
                    annotations=[{
                        'x': 0.95,
                        'y': 1.05,
                        'xref': 'paper',
                        'yref': 'paper',
                        'text': f'Mean Age: {mean_age:.1f}',
                        'showarrow': False,
                        'font': {'size': 12},
                        'align': 'right'
                    }]
                )
            ))

        # Create base figure with initial data
        initial_year = self.years[0]
        initial_data = self.df[self.df['ACCIDENT_YEAR'] == initial_year].copy()
        initial_data.loc[:, 'AGE'] = initial_data['BIRTH_YEAR_OF_ACCIDENT_PERPETR'].apply(
            lambda x: initial_year - x if pd.notnull(x) else None
        )
        
        valid_age_mask = (initial_data['AGE'] >= 0) & (initial_data['AGE'] <= 90)
        initial_data = initial_data[valid_age_mask]
        
        initial_counts = initial_data.groupby('AGE').size().reset_index(name='ACCIDENT_COUNT')
        initial_mean = initial_data['AGE'].mean()

        fig = go.Figure(
            data=[go.Scatter(
                x=initial_counts['AGE'],
                y=initial_counts['ACCIDENT_COUNT'],
                mode='markers',
                marker=dict(
                    size=initial_counts['ACCIDENT_COUNT'],
                    sizeref=2.*max(initial_counts['ACCIDENT_COUNT'])/(40.**2),
                    sizemin=4
                ),
                name=f'Year {initial_year}'
            )],
            frames=frames
        )

        # Add animation controls
        fig.update_layout(
            updatemenus=[{
                'buttons': [
                    {
                        'args': [None, {'frame': {'duration': 1000, 'redraw': True},
                                      'fromcurrent': True}],
                        'label': 'Play',
                        'method': 'animate'
                    },
                    {
                        'args': [[None], {'frame': {'duration': 0, 'redraw': True},
                                        'mode': 'immediate',
                                        'transition': {'duration': 0}}],
                        'label': 'Pause',
                        'method': 'animate'
                    }
                ],
                'type': 'buttons'
            }],
            sliders=[{
                'currentvalue': {'prefix': 'Year: '},
                'steps': [
                    {'args': [[str(year)], {'frame': {'duration': 0, 'redraw': True},
                                          'mode': 'immediate',
                                          'transition': {'duration': 0}}],
                     'label': str(year),
                     'method': 'animate'} for year in self.years
                ]
            }],
            title='Age Distribution of Accident Perpetrators (Animated)',
            xaxis_title='Age',
            yaxis_title='Number of Accidents',
            showlegend=False
        )

        return fig

    def save_animations(self, output_dir='animations'):
        """Save both animations as HTML files."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Create and save severity animation
        severity_fig = self.create_severity_animation()
        severity_fig.write_html(os.path.join(output_dir, 'severity_animation.html'))
        
        # Create and save age animation
        age_fig = self.create_age_animation()
        age_fig.write_html(os.path.join(output_dir, 'age_animation.html'))
        
        print(f"Animations saved in {output_dir} directory")

# Example usage:
if __name__ == "__main__":
    # Initialize with CSV path
    animator = QatarAccidentsAnimation('facc.csv')
    animator.save_animations()