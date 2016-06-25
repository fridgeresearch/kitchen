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
import ActionDetailsComponent from '../components/actionDetails'
import InventoryComponent from '../components/inventory'
let appState = null
let commonUtils = require("../utils/common.js")
let inventoryUtils = require("../utils/inventory.js")

module.exports = {
    run: function(state) {
	appState = state
	inventoryUtils.initialize(appState)
	inventoryUtils.registerStaticCallbacks()
	commonUtils.handleSegmentedControl()	
	if (appState.inventory) {
	    render()
	} else {
	    console.log('Fetching inventory...')
	    xhr({
		url: appState.baseUrl + '/inventory',
		headers: appState.headers,
		json: true
	    }, (err, req, body) => {
		if (err) {
		    console.log('No items received.')
		    ReactDOM.render(<InventoryComponent items={[]} />, document.getElementById('inventory'))
		} else {
		    console.log(body.length,'item(s) received.')
		    appState.inventory = body
		    render()
		}
	    })
	}
    },
    sortInventory: function(sorttype) {
    	sortAndRenderInventory(sorttype)
    }
}

function render () {
    console.log("render")
    renderInventory()
    inventoryUtils.registerDynamicCallbacks()
    renderActions()
}
function renderInventory () {
    console.log("renderInventory")
    inventoryUtils.sortAndRenderInventory()
 //    let sortReverseArrivalTime = function(a, b){
	// return a.arrivalevent_time > b.arrivalevent_time ? -1 : 1;
 //    }
 //    let inventory = appState.inventory.sort(sortReverseArrivalTime)
 //    //console.log(appState.inventory)
 //    ReactDOM.render(<InventoryComponent items={inventory} />, document.getElementById('inventory'))
}

// function sortAndRenderInventory (sorttype) {
// 	console.log("Sort by = ", sorttype)
// 	let sortInventory = null
// 	if (sorttype == "remaining_time") {
//     	sortInventory = function(a, b){
// 			return a.remaining_time > b.remaining_time ? -1 : 1;
//     	}
// 	} else if (sorttype == "most_frequently_used") {
//     	sortInventory = function(a, b){
// 			return a.itemread_id > b.itemread_id ? -1 : 1;
//     	}
// 	} else { // sort on arrivalevent_time by default (sorttype == "arrivalevent_time")
//     	sortInventory = function(a, b){
// 			return a.arrivalevent_time > b.arrivalevent_time ? -1 : 1;
//     	}
// 	}
// 	console.lo
//     let inventory = appState.inventory.sort(sortInventory)
//     //console.log(appState.inventory)
//     ReactDOM.render(<InventoryComponent items={inventory} />, document.getElementById('inventory'))	
// }

function renderActions () {
    console.log("renderActions")
    let ingredients = inventoryUtils.getAging(appState.inventory)
    if(ingredients.length){
	ReactDOM.render(<ActionDetailsComponent items={ingredients} />,
			document.getElementById('recipeActionDetails'))
	document.getElementById('recipeAction').classList.remove('hidden')
	/*ReactDOM.render(<ActionDetailsComponent items={ingredients} />,
			document.getElementById('shoppingActionDetails'))
	document.getElementById('shoppingAction').classList.remove('hidden')*/
    }
}
