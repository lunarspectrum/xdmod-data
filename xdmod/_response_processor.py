import csv
from datetime import datetime
import html
import numpy as np
import pandas as pd
import re


def _process_get_data_response(dw, params, response):
    csv_data = csv.reader(response.splitlines())
    if params['timeseries']:
        return __parse_timeseries_csv_data(dw, params, csv_data)
    else:
        return __parse_aggregate_csv_data(params, csv_data)


def __parse_timeseries_csv_data(dw, params, csv_data):
    time_values = []
    data = []
    for line_num, line in enumerate(csv_data):
        if line_num == 7:
            dimension_values = __parse_timeseries_dimension_values(line[1:])
        elif line_num > 7 and len(line) > 1:
            time_values.append(__parse_timeseries_date_string(line[0]))
            data.append(np.asarray(line[1:]))
    return pd.DataFrame(
        data=data,
        index=pd.Series(data=time_values, name='Time'),
        columns=pd.Series(
            dimension_values,
            name=dw._get_dimension_label(
                params['realm'], params['dimension']
            )
        )
    )


def __parse_aggregate_csv_data(params, csv_data):
    dimension_values = []
    data = []
    for line_num, line in enumerate(csv_data):
        if line_num > 7 and len(line) > 1:
            dimension_values.append(html.unescape(line[0]))
            data.append(line[1])
    return pd.Series(
        data=data,
        name=params['metric'],
        index=pd.Series(data=dimension_values, name=params['dimension']),
    )


def __parse_timeseries_dimension_values(labels):
    label_re = re.compile(r'\[([^\]]+)\].*')
    dimension_values = []
    for label in labels:
        match = label_re.match(label)
        if match:
            dimension_values.append(html.unescape(match.group(1)))
        else:
            dimension_values.append(html.unescape(label))
    return dimension_values


def __parse_timeseries_date_string(date_string):
    # Match YYYY-MM-DD
    if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', date_string):
        format_ = '%Y-%m-%d'
    # Match YYYY-MM
    elif re.match(r'^[0-9]{4}-[0-9]{2}$', date_string):
        format_ = '%Y-%m'
    # Match YYYY
    elif re.match(r'^[0-9]{4}$', date_string):
        format_ = '%Y'
    # Match YYYY Q#
    elif re.match(r'^[0-9]{4} Q[0-9]$', date_string):
        (date_string, format_) = __parse_quarter_date_string(date_string)
    else:
        raise Exception(
            'Unsupported date specification ' + date_string + '.'
        )
    return datetime.strptime(date_string, format_)


def __parse_quarter_date_string(date_string):
    year, quarter = date_string.split(' ')
    if quarter == 'Q1':
        month = '01'
    elif quarter == 'Q2':
        month = '04'
    elif quarter == 'Q3':
        month = '07'
    elif quarter == 'Q4':
        month = '10'
    else:
        raise Exception(
            'Unsupported date quarter specification '
            + date_string + '.'
        )
    date_string = year + '-' + month + '-01'
    format_ = '%Y-%m-%d'
    return (date_string, format_)
