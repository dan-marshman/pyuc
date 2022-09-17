import os

import pandas as pd


def load_master_sets(data, settings):
    sets = dict()

    sets['intervals'] = Set('intervals', data['traces']['demand'].index.to_list())
    sets['units'] = Set('units', data['units'].index.to_list())
    sets['scenarios'] = Set('scenarios', list(range(settings['NUM_SCENARIOS'])))

    all_reserve_indices = \
        pd.read_csv(os.path.join(default_files_path, 'all_reserve_indices.csv'))
    reserve_indices = \
        [r for r in all_reserve_indices['ReserveType'] if r in data['as_reqt'].columns]

    sets['reserves'] = Set('reserves', reserve_indices)

    return sets
