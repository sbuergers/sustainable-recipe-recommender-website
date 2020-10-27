import altair as alt
import numpy as np


def bar_compare_emissions(reference_recipe, search_results, relative=True,
                          base_url='https://sustainable-recipe-recommender.herokuapp.com/search/',
                          sort_by='Similarity', scale='lin'):
    '''
    DESCRIPTION:
        Creates a bar chart of GHG emissions for the reference
        recipe and suggested similar recipes relative to the
        reference recipe.

    INPUT:
        reference_recipe (DataFrame): Recipe dataframe row for the
            reference recipe (to which everything else is compared)

        search_results (DataFrame): Recipe dataframe with rows being
            the suggested similar recipes to the reference recipe.

        relative (Boolean): If true, emission scores are relative to
            the reference recipe, otherwise absolute emissions are
            shown (default=True).

        base_url (String): Base url of the recipe search website

        sort_by (String): Url GET query by which to sort recipes
            (default=Similarity).

        scale (String): Can be 'lin' for linear scale, or 'log' for
            log-scale (default='lin')

    OUTPUT:
        Altair json object
    '''

    # determine scale
    if scale == 'log':
        voi = 'emissions_log10'
        xlabel = 'log10(kg CO2 eq)'
    else:
        voi = 'emissions'
        xlabel = 'kg CO2 eq'

    if relative:
        # compute emissions relative to reference
        source = search_results.copy()
        source['emission change'] = np.ceil(100*(
                                       search_results[voi].values -
                                       reference_recipe[voi]))/100
        source['emission_change'] = source['emission change']

        # create bar chart
        bars = alt.Chart(
            source
        ).transform_calculate(
            link=base_url + alt.datum.url + '?sort_by=' + sort_by
        ).mark_bar().encode(
            y=alt.Y("title:N", axis=alt.Axis(orient='right',
                                             title=' ',
                                             labels=True),
                    sort=list(range(source.shape[0]))
                    ),
            x=alt.X("emission_change:Q",
                    axis=alt.Axis(title=xlabel)
                    ),
            tooltip=['title', 'emission change'],
            href='link:N',
            color=alt.condition(
                alt.datum.emission_change > 0,
                alt.value("palevioletred"),  # The positive color
                alt.value("palegreen")  # The negative color
            )
        ).properties(
            width=250,
            height=500,
            title='Similar recipes'
        ).configure_axis(
            labelFontSize=16,
            titleFontSize=16,
            labelFontWeight='normal',
            titleFontWeight='normal',
            labelColor='gray',
            titleColor='gray',
        ).configure_title(
            fontSize=22,
            fontWeight='normal',
            anchor='start'
        ).interactive()

    else:
        # TODO option for plotting absolute emission scores
        pass

    # Return .json of chart
    return bars.to_json()

# eof
