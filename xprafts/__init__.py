from xprafts import *

def parse_tot_data(tot_file, events_file):
    raw_data = pd.read_csv(rainfall_source, header=2, index_col=0, parse_dates=True, dayfirst=True)
#    raw_data['Cumulative'] = raw_data[rainfall_field].cumsum()
    raw_data = raw_data.resample('5T').sum()
    raw_data.loc[:,rainfall_field] = raw_data.loc[:,rainfall_field].fillna(0)
    
    return raw_data