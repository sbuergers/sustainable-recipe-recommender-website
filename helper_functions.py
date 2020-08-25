import pandas as pd
import numpy as np
from hist_emissions import make_histogram


recipes = pd.read_csv(r'./data/recipes_sql.csv', index_col=0)


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


def similarity_to_percentage(results, ref):
    '''
    DESCRIPTION:
        Converts raw similarity scores to percentages
    INPUT:
        results (DataFrame): Subset of recipes DataFrame containing
            similar recipes to reference recipe to be diplayed

        ref (DataFrame): Single row subset of the
            recipes DataFrame containing the recipe of interest
    OUTPUT:
        List of length(results) with similarity percentages for
        each row in results
    '''
    return [round(sim*100) for sim in results['similarity']]


def rating_to_percentage(results, ref):
    '''
    DESCRIPTION:
        Converts raw ratings to percentage ratings (e.g. 4
        stars would be converted to 80%)
    INPUT:
        results (DataFrame): Subset of recipes DataFrame containing
            similar recipes to reference recipe to be diplayed

        ref (DataFrame): Single row subset of the
            recipes DataFrame containing the recipe of interest
    OUTPUT:
        rating_percentage (list): List of length(results) with the
            corresponding percentage ratings
    '''
    # Replace nans with 0
    # TODO REMOVE this, and deal with nans in the .csv itself?
    if np.isnan(ref['rating']):
        ref['rating'] = 0
    results['rating'] = results['rating'].fillna(0)

    # Compute percentages
    rating_percentage = [round(ref['rating']*20)] + \
                        [round(ra*20) for ra in results['rating']]
    return rating_percentage


def emissions_to_percentage(results, ref):
    '''
    DESCRIPTION:
        Converts raw emissions scores to quantiles
    INPUT:
        results (DataFrame): Subset of recipes DataFrame containing
            similar recipes to reference recipe to be diplayed

        ref (DataFrame): Single row subset of the
            recipes DataFrame containing the recipe of interest
    OUTPUT:
        emission_quantile (list): List of length(results) with the
            corresponding emission quantiles over all recipes
    '''
    N = recipes.shape[0]
    emission_quantile = [round(sum(recipes['ghg'] < ref['ghg'])*100 / N)] + \
                        [round(sum(recipes['ghg'] < em)*100 / N)
                         for em in results['ghg']]
    return [100 - eq for eq in emission_quantile]


def add_figures_to_df(results):
    '''
    DESCRIPTION:
        takes a results DataFrame with the recipes to be displayed
        and appends columns for plotting information in the form
        of bokeh output of script and div objects
    INPUT:
        results (DataFrame): Dataframe of recipes to be diplayed
    OUTPUT:
        results (DataFrame): Input DataFrame with additional columns
            (see description for details)
    '''
    plots = []
    divs = []
    for recipesID, _ in results.iterrows():
        p, div = make_histogram(recipesID, recipes)
        divs.append(div)
        plots.append(p)
    results['plot_hist'] = plots
    results['div_hist'] = divs
    return results


# eof
