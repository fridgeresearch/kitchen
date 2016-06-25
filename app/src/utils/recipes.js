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
import RecipeIngredientsComponent from '../components/recipeIngredients'
import React from 'react'
import ReactDOM from 'react-dom'
let commonUtils = require("./common.js")
let interactiveCookingUtils = require("./interactiveCooking.js")
let appState = null;
import xhr from 'xhr'

function sortAlphabetical(a, b) {
    return a.food_name.toLowerCase() < b.food_name.toLowerCase() ? -1 : 1;
}

let staticCallbacks = [
    {
	elementId: "recipeSearch",
	event: "submit",
	callback: function(e) {
	    console.log('recipeSearchSubmit')
	    e.preventDefault()
	    appState.recipeSearch.search = document.querySelector('input[type=search]').value
	    // create a touch event
	    let evt = document.createEvent('TouchEvent');
	    evt.initUIEvent('touchend', true, true);
	    // trigger touch event on elements to navigate
	    document.getElementById('recipes-page').dispatchEvent(evt);
	}
    },
    {
	elementId: "filterModalSearch",
	event: "touchend",
	callback: function(e) {
	    console.log('filterModalSearchTouchend')
	    let toggles = document.querySelectorAll('.toggle')
	    for (let i = 0; i < toggles.length; i++) {
		appState.recipeSearch.ingredients[i].include = toggles[i].classList.contains('active');
	    }
	    // create a touch event
	    let evt = document.createEvent('TouchEvent');
	    evt.initUIEvent('touchend', true, true);
	    // trigger touch event on elements to navigate
	    document.getElementById('recipes-page').dispatchEvent(evt);
	}
    },
    {
	elementId: "filterModalCancel",
	event: "touchend",
	callback: function(e) {
	    console.log('filterModalCancelTouchend')
	    for (let i = 0; i < appState.recipeSearch.ingredients.length; i++) {
		if(appState.recipeSearch.ingredients[i].include == "pending"){
		    appState.recipeSearch.ingredients[i].include = false;
		}
	    }
	    // create a touch event
	    let evt = document.createEvent('TouchEvent');
	    evt.initUIEvent('touchend', true, true);
	    
	    // trigger touch event on elements to navigate
	    document.getElementById('recipes-page').dispatchEvent(evt);
	}
    },
    {
	elementId: "filter",
	event: "touchend",
	callback: function(e) {
	    console.log('filterTouchend')
	    document.querySelector("header").classList.add('hidden')
	}
    },
    {
	elementId: "filterModalCancel",
	event: "touchend",
	callback: function(e) {
	    console.log('filterModalCancelTouchend')
	    document.querySelector("header").classList.remove('hidden')
	}
    },
    {
	elementId: "filterModalSearch",
	event: "touchend",
	callback: function(e) {
	    console.log('filterModalSearchTouchend')
	    document.querySelector("header").classList.remove('hidden')
	}
    }
    /*{
	elementId: "chefs",
	event: "touchend",
	callback: function(e) {
	    console.log('chefsTouchend')
	    document.querySelector("header").classList.add('hidden')
	}
    },
    {
	elementId: "chefsModalCancel",
	event: "touchend",
	callback: function(e) {
	    console.log('chefsModalCancelTouchend')
	    document.querySelector("header").classList.remove('hidden')
	}
    }*/
]

function ingredientIndex(ingredient, ingredientList) {
    for (let i = 0; i < ingredientList.length; i++){
	if(ingredientList[i].food_name.toLowerCase() == ingredient.food_name.toLowerCase()){
	    return i
	}
    }
    return -1
}

let dynamicCallbacks = [
    {
	elementId: "newIngredient",
	event: "submit",
	callback: function(e) {
	    console.log('newIngredientSubmit')
	    e.preventDefault()
	    let val = document.querySelector('input[type=text]').value
	    document.querySelector('input[type=text]').value = ""
	    let ingredient = {food_name: val, ingredient_tags: [val], active: "pending"}
	    let idx = ingredientIndex(ingredient, appState.recipeSearch.ingredients)
	    if (idx < 0){
		appState.recipeSearch.ingredients.push(ingredient)		
	    }
	    else if (!appState.recipeSearch.ingredients[idx].include) {
		appState.recipeSearch.ingredients[idx].include = "pending"
	    }
	    appState.recipeSearch.ingredients.sort(sortAlphabetical)
	    ReactDOM.render(<RecipeIngredientsComponent items={appState.recipeSearch.ingredients} />,
			    document.getElementById('filterModalInventory'))
	}
    }
]

function setRecipeIngredients (state) {
    console.log('setRecipeIngredients')
    if(!state.recipeSearch.ingredients.length){
	for (let i=0; i < state.inventory.length; i++) {
	    let item = state.inventory[i]
	    let idx = ingredientIndex(item, state.recipeSearch.ingredients)
	    if (idx < 0) {
		let foodtag_names = []
		for (let j = 0; j < item.foodtags.length; j++){
		    foodtag_names.push(item.foodtags[j]["FoodTag.name"])
		}
		state.recipeSearch.ingredients.push({food_name: item.food_name,
						     ingredient_tags: foodtag_names,
						     include: item.active, exclude: false})
	    }
	    else if (item.include){
		state.recipeSearch.ingredients[idx].include = item.include
	    }
	}
	state.recipeSearch.ingredients.sort(sortAlphabetical)
    }
}

function getRecipeIngredients () {
    console.log('getRecipeIngredients')
    let includeIngredients = {}, excludeIngredients = {}
    for(let i = 0; i < appState.recipeSearch.ingredients.length; i++){
	let item = appState.recipeSearch.ingredients[i]
	if(item.include) {
	    includeIngredients[item.food_name] = item.ingredient_tags
	}
	else if(item.exclude) {
	    excludeIngredients[item.food_name] = item.ingredient_tags
	}
    }
    for(let i = 0; i < appState.recipeSearch.splits.length; i++){
	let [name, yesNo] = appState.recipeSearch.splits[i]
	if(yesNo==1){
	    includeIngredients[name] = [name]
	}
	else if(yesNo==0){
	    excludeIngredients[name] = [name]
	}
    }
    return [includeIngredients, excludeIngredients]
}

module.exports = {
    initialize: function(state){ appState = state; },
    registerStaticCallbacks: function() { commonUtils.registerCallbacks(staticCallbacks) },
    registerDynamicCallbacks: function() { commonUtils.registerCallbacks(dynamicCallbacks) },
    setRecipeIngredients: setRecipeIngredients,
    getRecipeIngredients: getRecipeIngredients
}
