# Sustainable-recipe-recommender
A recipe recommendation engine suggesting similar recipes that are more sustainable. This is the repository for the website. If you are interested in fetching and preprocessing of the data have a look at [this repo](https://github.com/sbuergers/sustainable-recipe-recommender). 

# Ready to cook more sustainably?
Identifying ways to make one's diet more sustainable can be challenging. Often information is not readily available and implementing drastic changes such as fully switching to a vegetarian or vegan diet can seem daunting.

Sustainable recipe recommender is a tool to help people adopt more sustainable cooking habits by
1. estimating the environmental impact of recipes based on [scientific data](https://science.sciencemag.org/content/360/6392/987), and
2. recommending sustainable recipes similar to the ones you already like.

# Estimating greenhouse gas emissions of recipes
The idea for sustainable recipe recommender is heavily inspired by an excellent article on [ourworldindata.org](https://ourworldindata.org/environmental-impacts-of-food), by Hannah Ritchie and Max Roser. The article summarizes and reviews the implications of the findings from a 2018 paper published in Science that assesses the life-cycle environmental impact of approximately 90% of the world's food production (Poore & Nemecek, 2018). Both the [paper](https://science.sciencemag.org/content/360/6392/987) and [data](https://science.sciencemag.org/content/360/6392/987/tab-figures-data) are freely available online. 

To assess a recipe's sustainability score, ingredient labels were manually mapped to 42 fundamental food categories as identified by Poore and Nemecek (2018). 

# Dive deeper
If you are curious about exploring the environmental impact of recipes and different food categories further, want to know more about how ingredient labels and quantities were parsed from text data, or are interested in how the recipe recommendation system works, have a look at [the blog](https://sustainable-recipe-recommender.herokuapp.com/blog). 

# Give feedback
I am happy to receive feedback on how to improve sustainable recipe recommender, both in terms of user experience and anything related to data sources and processing. Just drop me an [email](mailto:sbuergers@gmail.com) at sbuergers at gmail dot com or message me on github.

# References
1. Hannah Ritchie (2020) - "Environmental impacts of food production". Published online at OurWorldInData.org. Retrieved from: 'https://ourworldindata.org/environmental-impacts-of-food' [Online Resource]
2. Poore, J., and T. Nemecek. “Reducing Food’s Environmental Impacts through Producers and Consumers.” Science 360, no. 6392 (June 1, 2018): 987–92. https://doi.org/10.1126/science.aaq0216.
3. www.epicurious.com
