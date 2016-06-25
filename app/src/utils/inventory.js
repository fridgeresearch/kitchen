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
import InventoryComponent from '../components/inventory'
let commonUtils = require("./common.js")
let appState = null;

let staticCallbacks = [
    {
	elementId: "inventorySearch",
	event: "keyup",
	callback: function (e) {
	    console.log('inventorySearchKeyup')
	    e.preventDefault()
	    if (appState.inventory) {
		let searchResults = appState.inventory.filter(function(item) {
		    return item.food_name.search(new RegExp(document.querySelector('input[type=search]').value, 'i')) > -1
		}, this)
		ReactDOM.render(<InventoryComponent items={searchResults} />, document.getElementById('inventory'))
		commonUtils.registerCallbacks(dynamicCallbacks)
	    }
	}
    },
    {
	elementId: "recipeAction",
	event: "touchend",
	callback: function(e) {
	    console.log('recipeActionTouchend')
	    appState.recipeSearch.ingredients = []
	    let ingredients = getAging(appState.inventory)
	    for (let i = 0; i < appState.inventory.length; i++){
		appState.inventory[i]["active"] = false;
		for (let j = 0; j < ingredients.length; j++) {
		    if (ingredients[j].itemread_id == appState.inventory[i].itemread_id){
			appState.inventory[i]["active"] = true;
		    }
		}
	    }    
	    let evt = document.createEvent('TouchEvent');
	    
	    // reinitialize state variables.
	    //appState.inventory = null
	    appState.currentItemReadId = null
	    
	    // create a touch event
	    evt.initUIEvent('touchend', true, true);
	    
	    // trigger touch event to close out footer
	    document.getElementById('cancelBtn').dispatchEvent(evt);
	    
	    // trigger touch event on elements to navigate
	    document.getElementById('recipes-page').dispatchEvent(evt);
	}
    },
    {
	elementId: "clearRecipeAction",
	event: "touchend",
	callback: function(e) {
	    console.log('clearRecipeActionTouchend')
	    e.stopImmediatePropagation(); // so that parent clickable div callback not triggered
	    document.getElementById('recipeAction').classList.add('hidden')
	}
    },
    {
	elementId: "shoppingAction",
	event: "touchend",
	callback: function(e) { // TODO(jake): implement
	    console.log('shoppingActionTouchend')
	}
    },
    {
	elementId: "clearShoppingAction",
	event: "touchend",
	callback: function(e) {
	    console.log('clearShoppingActionTouchend')
	    e.stopImmediatePropagation(); // so that parent clickable div callback not triggered
	    document.getElementById('shoppingAction').classList.add('hidden')
	}
    },
    {
	elementId: "selectBtn",
	event: "touchend",
	callback: function(e) {
	    console.log('selectBtnTouchend')
	    let select = document.querySelectorAll('.select')	    
	    // show selectable div
	    for (let i = 0; i < select.length; i++) {
		select[i].classList.add('on')
	    }    
	    // make search invisible when selecting items
	    document.querySelector('input[type=search]').classList.add('invisible')
	}
    },
    {
	elementId: "sortBtn",
	event: "touchend",
	callback: function(e) {
		e.preventDefault()
	    console.log('sortBtnTouchend')
	    console.log('Current sort = ' + appState.inventorySort)
	    if (appState.inventorySort == "arrivalevent_time") {
	    	appState.inventorySort = "remaining_time"
	    } else if (appState.inventorySort == "remaining_time") {
	    	appState.inventorySort = "most_frequently_used"
	    } else {
	    	appState.inventorySort = "arrivalevent_time"
	    }
	    console.log('New sort = ' + appState.inventorySort)	    
	    sortAndRenderInventory(appState.inventorySort)
	}
    },
    {
	elementId: "cancelBtn",
	event: "touchend",
	callback: function(e) {
	    console.log('cancelBtnTouchend')
	    let select = document.querySelectorAll('.select')
	    // hide selectable div
	    for (let i = 0; i < select.length; i++) {
		select[i].classList.remove('on')
		select[i].classList.remove('selected')
	    }    
	    // make search visible when not selecting items
	    document.querySelector('input[type=search]').classList.remove('invisible')
	    // make appState.selectCount === 0
	    setSelectCount(0)    
	    // remove active class from links
	    document.getElementById('selectAll').classList.remove('active')
	    deactivateModals()
	}
    },
    {
	elementId: "selectAll",
	event: "touchend",
	callback: function(e) {
	    console.log('selectAllBtnTouchend')
	    let select = document.querySelectorAll('.select')
            if (e.currentTarget.classList.contains('active')) {
		e.currentTarget.classList.remove('active')
		deactivateModals()
		setSelectCount(0)
		for (let i = 0; i < select.length; i++) {
		    select[i].classList.remove('selected')
		}
	    } else {
		e.currentTarget.classList.add('active')
		activateModals()
		setSelectCount(appState.inventory ? appState.inventory.length : 0)
		for (let i = 0; i < select.length; i++) {
		    select[i].classList.add('selected')
		}
	    }
	}
    },
    {
	elementId: "inventoryToRecipes",
	event: "touchend",
	callback: function (e) {
	    console.log('inventoryToRecipesTouchend')
	    appState.recipeSearch.ingredients = []
	    let irs = getSelectedItemReadIds()
	    for (let i = 0; i < appState.inventory.length; i++){
		appState.inventory[i]["active"] = false;
		for (let j = 0; j < irs.length; j++) {
		    if (irs[j] == appState.inventory[i].itemread_id){
			appState.inventory[i]["active"] = true;
		    }
		}
	    }
	    let evt = document.createEvent('TouchEvent');
	    
	    // reinitialize state variables.
	    //appState.inventory = null
	    appState.currentItemReadId = null
	    
	    // create a touch event
	    evt.initUIEvent('touchend', true, true);
	    
	    // trigger touch event to close out footer
	    document.getElementById('cancelBtn').dispatchEvent(evt);
	    
	    // trigger touch event on elements to navigate
	    document.getElementById('recipes-page').dispatchEvent(evt);
	}
    },
    {
	elementId: "addToListConfirm",
	event: "touchend",
	callback: function (e) {
	    console.log('addToListConfirmTouchend')
	    let food_names = getSelectedFoodNames()
	    let evt = document.createEvent('TouchEvent');
	    
	    // add items to grocery list.
	    let quants = []
	    for(let i = 0; i < food_names.length; i++){
		quants[i] = 1
	    }
	    updateGroceryBundles(food_names, quants, "POST")
	    
	    // reinitialize state variables.
	    //appState.inventory = null
	    appState.currentItemReadId = null
	    
	    // create a touch event
	    evt.initUIEvent('touchend', true, true);
	    
	    // trigger touch event to close out footer
	    document.getElementById('cancelBtn').dispatchEvent(evt);
	    
	    // trigger touch event on elements to navigate
	    document.getElementById('shopping-page').dispatchEvent(evt);
	}
    },
    {
	elementId: "deleteConfirm",
	event: "touchend",
	callback: function (e) {
	    console.log('deleteConfirmTouchend')
	    let selected_itemread_ids = getSelectedItemReadIds()
	    let evt = document.createEvent('TouchEvent');
	    
	    // delete items from inventory.
	    deleteFromInventory(selected_itemread_ids)
	    
	    // reinitialize state variables.
	    appState.inventory = null
	    appState.currentItemReadId = null
	    
	    // create a touch event
	    evt.initUIEvent('touchend', true, true);
	    
	    // trigger touch event to close out footer
	    document.getElementById('cancelBtn').dispatchEvent(evt);
	    
	    // trigger touch event on elements to navigate
	    document.getElementById('inventory-page').dispatchEvent(evt);
	}
    }
]

let dynamicCallbacks = [
    {
	className: "inventory-link",
	event: "touchend",
	callback: function (e) {
	    console.log("inventoryLinkTouchend")
	    appState.currentItemReadId = parseInt(e.currentTarget.dataset.id, 10)
	}
    },
    {
	className: "select",
	event: "tap",
	callback: function(e) {
	    console.log("selectTap")
	    if (e.currentTarget.classList.contains('selected')) {
		e.currentTarget.classList.remove('selected')
		setSelectCount(appState.selectCount-1)
	    } else {
		e.currentTarget.classList.add('selected')
		setSelectCount(appState.selectCount+1)
	    }	
	    if (appState.selectCount === appState.inventory.length) {
		document.getElementById('selectAll').classList.add('active')
		activateModals()
	    } else if (appState.selectCount === 0) {
		document.getElementById('selectAll').classList.remove('active')
		deactivateModals()
	    } else {
		document.getElementById('selectAll').classList.remove('active')
		activateModals()
	    }
	}
    }
]

function setSelectCount (cnt) {
    appState.selectCount = cnt
    let info_str = cnt + " Items Selected"
    document.getElementById('deleteConfirmInfo').innerHTML = info_str
    document.getElementById('addToListConfirmInfo').innerHTML = info_str
}

function activateModals () {
    document.getElementById('inventoryToRecipes').classList.add('active')
    document.getElementById('addToList').classList.add('active')
    document.getElementById('delete').classList.add('active')
    document.getElementById('deleteModal').classList.add('modal')
    document.getElementById('deleteModal').classList.remove('hidden')
    document.getElementById('addToListModal').classList.add('modal')
    document.getElementById('addToListModal').classList.remove('hidden')
}

function deactivateModals () {
    document.getElementById('inventoryToRecipes').classList.remove('active')
    document.getElementById('addToList').classList.remove('active')
    document.getElementById('delete').classList.remove('active')
    document.getElementById('deleteModal').classList.add('hidden')
    document.getElementById('deleteModal').classList.remove('modal')
    document.getElementById('addToListModal').classList.add('hidden')
    document.getElementById('addToListModal').classList.remove('modal')
}

function getAging (inventory) {
    console.log("getAging")
    let sortRemainingTime = function(a, b) {
	return a.remaining_time < b.remaining_time ? -1 : 1;
    }
    let inv = inventory.sort(sortRemainingTime)
    let items = []
    for(let i=0; i < Math.min(inv.length, 5); i++){
	if(inv[i].remaining_time < 7){
	    items.push(inv[i])
	}
    }
    return items
}


function updateGroceryBundles(food_names, quants, method){
    console.log('updating grocery bundles...', food_names, quants)
    let data = { food_name: food_names, quantity: quants }
    let url = appState.baseUrl + '/groceryBundles?' + JSON.stringify(data)
    console.log("url =", url)
    xhr({
      url: url,
      method: method,
      headers: appState.headers,
      json: true
    }, (err, req, body) => {
      if (err) {
	console.log(url)
        console.log('Could not insert items....')
      } else {
        console.log('item(s) inserted.')
      }
    })
}
function deleteFromInventory (itemread_ids) {
    console.log('deleting items...', itemread_ids)
    let data = {"ids" : itemread_ids}
    let url = appState.baseUrl + '/inventory?' + JSON.stringify(data)
    console.log("url =", url)
    xhr({
      url: url,
      method: 'DELETE',
      headers: appState.headers,
      json: true
    }, (err, req, body) => {
      if (err) {
        console.log('Could not delete items....')
      } else {
        console.log('item(s) deleted.')
      }
    })
}

function getSelectedItemReadIds () {
  let select = document.querySelectorAll('.selected'), ret = []
  for (let i = 0; i < select.length; i++) {
    ret[i] = parseInt(select[i].dataset.id, 10)
  }
  return ret
}

function getSelectedFoodNames () {
  let select = document.querySelectorAll('.selected'),
      ret = []
  for (let i = 0; i < select.length; i++) {
    ret[i] = select[i].dataset.food_name
  }
  return ret
}

function sortAndRenderInventory (sorttype) {
	console.log("Sort by = ", sorttype)
	let sortInventory = null
	let btnText = "Arrival"
	if (sorttype == "remaining_time") {
		btnText = "Expire"
    	sortInventory = function(a, b){
			return a.remaining_time < b.remaining_time ? -1 : 1;
    	}
	} else if (sorttype == "most_frequently_used") {
		btnText = "Usage"
    	sortInventory = function(a, b){
			return a.itemread_id > b.itemread_id ? -1 : 1;
    	}
	} else { // sort on arrivalevent_time by default (sorttype == "arrivalevent_time")
		btnText = "Arrival"
    	sortInventory = function(a, b){
			return a.arrivalevent_time > b.arrivalevent_time ? -1 : 1;
    	}
	}
	let el = document.getElementById('sortBtn').firstChild.data = btnText
	console.log(el)
	//.nodeValue = btnText
    let inventory = appState.inventory.sort(sortInventory)
    ReactDOM.render(<InventoryComponent items={inventory} />, document.getElementById('inventory'))	
}

module.exports = {
    initialize: function(state){ appState = state; },
    registerStaticCallbacks: function() { commonUtils.registerCallbacks(staticCallbacks) },
    registerDynamicCallbacks: function() { commonUtils.registerCallbacks(dynamicCallbacks) },
    sortAndRenderInventory,
    getAging: getAging,
    updateGroceryBundles: updateGroceryBundles
}
