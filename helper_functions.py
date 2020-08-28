import pandas as pd
import numpy as np
from hist_emissions import make_histogram


def sort_search_results(results, sort_by):
    '''
    DESCRIPTION:
        Sorts results dataframe by column specified in sort_by
    INPUT:
        results (DataFrame): Subset of recipes DataFrame containing
            similar recipes to reference recipe to be diplayed

        sort_by (string): What metric to sort rows by. Can be one of
            ['similarity', 'sustainability', 'rating'],
            default = 'similarity'
    OUTPUT:
        Updated results dataframe sorted as requested.
    '''
    # When sort_by is empty, simply return input dataframe
    # This can happen when they URL is tempered with manually
    if not sort_by:
        return results

    # Otherwise try to sort
    sort_by = sort_by.lower()
    if sort_by == 'similarity':
        return results
    if sort_by == 'sustainability':
        return results.sort_values(by='ghg', ascending=True)
    if sort_by == 'rating':
        return results.sort_values(by='rating', ascending=False)
    return results


# eof
