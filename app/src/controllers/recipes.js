/*
The MIT License (MIT)

Copyright (c) 2016 Jake Lussier (Stanford University)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/
import React from 'react'
import ReactDOM from 'react-dom'
import xhr from 'xhr'
import RecipesComponent from '../components/recipes'
import RecipeIngredientsComponent from '../components/recipeIngredients'
import RecipeFiltersComponent from '../components/recipeFilters'
let commonUtils = require("../utils/common.js")
let recipeUtils = require("../utils/recipes.js")

module.exports = {
    run: function(appState) {
	recipeUtils.initialize(appState)
	recipeUtils.registerStaticCallbacks()
	recipeUtils.setRecipeIngredients(appState)
	renderFilterModalInventory(appState.recipeSearch.ingredients)
	let [includeIngredients, excludeIngredients] = recipeUtils.getRecipeIngredients()
	renderFilters(includeIngredients, excludeIngredients, appState.recipeSearch.search)
	let keywords = appState.recipeSearch.search.split(/[ ,]+/)
	let sortby = ["relevance", "popular", "rating"], per_page = 20, page=1
	let data = {
	    include_ingredients: includeIngredients,
	    exclude_ingredients: excludeIngredients,
	    keywords: keywords,
	    sortby: sortby, per_page: per_page, page: page
	}
	let url = appState.baseUrl + '/recipes?' + JSON.stringify(data)
	console.log("url =", url)
	xhr({
	    url: url,
	    headers: appState.headers,
	    json: true
	}, (err, req, body) => {
	    if (err) {
		console.log('No recipes received.')
		renderRecipes([])
	    } else {
		console.log(body.length,'item(s) received.')
		renderRecipes(body)
	    }
	    recipeUtils.registerDynamicCallbacks()
	})
    }
}

function renderFilterModalInventory (ingredients) {
    ReactDOM.render(<RecipeIngredientsComponent items={ingredients} />,
		    document.getElementById('filterModalInventory'))
}

function renderFilters (includeIngredients, excludeIngredients, search) {
    ReactDOM.render(<RecipeFiltersComponent includeIngredientNames={Object.keys(includeIngredients)} excludeIngredientNames={Object.keys(excludeIngredients)} search={search} />,
		    document.getElementById('filters'))
}

function renderRecipes (recipes) {
    ReactDOM.render(<RecipesComponent recipes={recipes}/>, document.getElementById('recipes'))
}
