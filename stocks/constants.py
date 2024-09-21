import pandas as pd
import datetime
import random
from pathlib import Path

def get_dt():

    infile = Path(__file__).parent / "stocks.csv"
    df = pd.read_csv(infile, parse_dates=['date'])

    max_date = df['date'].max()
    future_steps = 10
    lookback = 7
    weight = 5

    df_long = pd.melt(df,id_vars=['date'], value_vars=df.columns[1:], var_name='company', value_name='price').sort_values('date')

    for c in df_long['company'].unique():
        for n in range(1,future_steps+1):
            df_long.loc[len(df_long)] = [max_date + datetime.timedelta(days=n), c, predict(df_long[df_long['company'] == c][-lookback:]['price'],weight)]

    return df_long, max_date, future_steps 
    
        
def predict(l : list[float] | pd.Series, weight: float = 1.0)->float:
    if type(l) == pd.Series: l=l.to_list()
    diff = [l[i] - l[i-1] for i in range(1,len(l))]
    avg = sum(diff)/len(diff) * random.uniform(-weight, weight)

    return l[-1] + avg


def gain_loss(future: list[float], total_owned: int, fee:float, pct_flag:bool=False):
    current_total = total_owned*future[0]
    current_total_fee_deducted = current_total - fee if not pct_flag else current_total*(1-fee/100)

    max_value = max(future)
    max_index = future.index(max_value)

    min_value = min(future)
    min_index = future.index(min_value)

    max_total = total_owned*max_value - fee if not pct_flag else total_owned*max_value*(1-fee/100)
    min_total = total_owned*min_value - fee if not pct_flag else total_owned*min_value*(1-fee/100)

    if max_index == 0:
        msg='Downward trend to be expected, sell now to prevent significant loss.<br>'
        msg+='After sale: <b>${0:.2f}</b> (fee deducted).<br>'.format(current_total_fee_deducted)
        msg+='Potential amount saved: <b>${}</b> (fee deducted).'.format(current_total_fee_deducted-min_total)


    elif min_index == 0:
        msg= f'Upward trend to be expected, reaching peak in {max_index} days.<br>'
        msg+='If sold during the peak: <b>${0:.2f}</b> (fee deducted).<br>'.format(max_total)
        msg+='Forecasted gain: <b>${0:.2f}</b> (fee deducted).'.format(max_total-current_total_fee_deducted)

    else:
        

        msg='Fluctuations expected, '
        msg+=f'hitting floor in {min_index} days and reaching peak in {max_index} days.<br>' if min_index<max_index else f'hitting peak in {max_index} days and reaching floor in {min_index} days.'
        msg+='Potential gain in {0} days: <b>${1:.2f}</b> (fee deducted).<br>'.format(max_index, max_total-current_total_fee_deducted)
        msg+='Potential loss if forecast is wrong:<b>${0:.2f}</b> (fee deducted).'.format(current_total_fee_deducted-min_total)


    return current_total, msg

def process_table_view(df):
    curr = df.iloc[0, 1]
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')

    def highlight_custom(val):
        if val == curr: return None
        color = '#079300' if val > curr else '#851404'
        return f'background-color: {color}'


    return (
            df.style.set_table_attributes(
                    'class="dataframe shiny-table table w-auto"'
                )
                .hide(axis="index")
                .format(
                    {
                        "price": "{0:0.2f}",
                    }
                )
                .set_table_styles(
                    [dict(selector="th", props=[("text-align", "left")])]
                )
                .applymap(highlight_custom, subset=['price'])
            )