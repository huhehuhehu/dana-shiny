from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_plotly
import shinyswatch
import datetime
import seaborn as sns
from constants import get_dt, gain_loss, process_table_view
import matplotlib.pyplot as plt
import random

_SEL_ALL = 'SELECT ALL'
_PREV_SEL = False
_DARK_COLOR = '#000000'
_LIGHT_FONT = '#ffffff'
_HIGHLIGHT_COLOR = '#999999'
_PCT = random.uniform(25,85)

ui.page_opts(title="Stock Price Forecast",
            fillable=True,
            theme=shinyswatch.theme.darkly()
            )

#SET DARK MODE PLOTS
custom_style = {
                'axes.labelcolor': _LIGHT_FONT,
                'xtick.color': _LIGHT_FONT,
                'ytick.color': _LIGHT_FONT,
                'text.color': _LIGHT_FONT,
                'axes.facecolor': _DARK_COLOR,
                'axes.edgecolor': _DARK_COLOR,
                'grid.color': _LIGHT_FONT,
                'figure.facecolor': _DARK_COLOR
               }
sns.set_style("darkgrid", rc=custom_style)
colors = [
    '#FF6347',  # Tomato
    '#4682B4',  # Steel Blue
    '#32CD32',  # Lime Green
    '#FFD700',  # Gold
    '#FF69B4',  # Hot Pink
    '#8A2BE2',  # Blue Violet
    '#FF4500',  # Orange Red
    '#00CED1',  # Dark Turquoise
    '#FF8C00',  # Dark Orange
]
sns.set_palette(colors)

# ui.tags.head(ui.tags.link(rel="shortcut icon", href="favicon.ico"))

footer = ui.card_footer('Highlighted area in the chart contains forecasted values.')

ui.nav_spacer()

df, _MAX_DATE, _future_steps = get_dt()

#CONTROL "SELECT ALL" SELECTION
@reactive.effect
@reactive.event(input.cb)
def select_all():
    global _PREV_SEL
    selected = list(input.cb())

    if _PREV_SEL and not all([c in selected for c in df['company'].unique()]):
        try:
            selected.remove(_SEL_ALL)
            ui.update_checkbox_group("cb", selected=selected)
        except ValueError:
            pass
        finally:
            _PREV_SEL = False
            return

    if not _PREV_SEL and _SEL_ALL in selected or ((len(selected) >= len(df['company'].unique())) and all([True if c in selected else False for c in df['company'].unique()])):
        ui.update_checkbox_group("cb", selected=[_SEL_ALL] + df['company'].to_list())
        _PREV_SEL = True

##########################################################################################################################

#FIRST PAGE
with ui.nav_panel("Prediction"):

    with ui.layout_columns(col_widths=(2, 10, 12)):

        #SIDEBAR
        with ui.card(full_screen=True):
            ui.input_checkbox_group(
                "cb",
                "Company", 
                [_SEL_ALL] + df['company'].to_list(),
                selected=random.sample(list(df['company'].unique()), random.randint(0,len(df['company'].unique())))
            )
            ui.input_slider(
                "minmax",
                "Date range",
                min(df['date']),
                max(df['date']),
                [min(df['date']),max(df['date'])],
                time_format="%F",
                width="97%;"
            )

            footer


        #PLOTS
        with ui.card(full_screen=True):
            ui.tags.h1('Trend (past 500 days)')

            @render.plot
            def plot_1():  
                ax = sns.lineplot(data=df[(df['date'] <= input.minmax()[1]) & (df['date'] >= input.minmax()[0]) & df['company'].isin(input.cb())], hue='company', x = 'date', y='price')
                ax.set_title("STOCKS")
                ax.set_xlabel("")
                ax.set_ylabel("$")
                ax.legend(title='')
                ax.axvspan(_MAX_DATE, _MAX_DATE + datetime.timedelta(days=_future_steps), facecolor=_HIGHLIGHT_COLOR, alpha=0.8)

                return ax


#############################################################################################################################
#SECOND PAGE
with ui.nav_panel("What to do?"):

    with ui.layout_columns(col_widths=(2, 8, 2)):

        #SIDEBAR
        with ui.card(full_screen=True):
            ui.input_select('com', 'Company', choices=list(df['company'].unique()))

            ui.input_slider(
                "minmax2",
                "Date range",
                min(df['date']),
                max(df['date']),
                [min(df['date']),max(df['date'])],
                time_format="%F",
                width="97%;"
            )

            ui.input_numeric('owned', 'Owned/to buy', 10)

            ui.input_numeric("fee", "Broker fee", 0)
            ui.input_select('fee_type', 'Fee type', ['fixed','percentage'])

            footer

        #STUFF
        with ui.card(full_screen=True):

            

            @render.ui
            def dynamic_header():
                return ui.tags.h1(input.com())

            @render.plot
            def plot_2():  
                ax = sns.lineplot(data=df[(df['date'] <= input.minmax2()[1]) & (df['date'] >= input.minmax2()[0]) & (df['company'] == input.com())], x = 'date', y='price')
                # ax.set_title("STOCKS")
                ax.set_xlabel("")
                ax.set_ylabel("$")
                ax.grid()
                ax.axvspan(_MAX_DATE, _MAX_DATE + datetime.timedelta(days=_future_steps), facecolor=_HIGHLIGHT_COLOR, alpha=.8)
                # ax.legend(loc='right')

                return ax

        #RECOMMENDATION
        with ui.card(full_screen=True):

            with ui.card(full_screen=True):
                @render.table
                def next_step2():
                    return process_table_view(df[df['company'] == input.com()][-_future_steps-1:][['date','price']])

            with ui.card(full_screen=True, min_height='25%'):
                @render.ui
                def next_step():

                    curr_total, msg = gain_loss(
                                            df[df['company'] == input.com()][-_future_steps-1:]['price'].to_list(),
                                            input.owned() or 0,
                                            input.fee() or 0,
                                            pct_flag=True if input.fee_type() == 'percentage' else False)
                    return ui.tags.p('Current total: ',
                                    ui.tags.b('${0:.2f}\n'.format(curr_total)),
                                    ui.tags.br(),
                                    ui.tags.b('Forecast Accuracy: {0:.2f}%'.format(_PCT)),
                                    ui.tags.br(),
                                    ui.tags.br(),
                                    ui.HTML(msg),
                                    )
            

                