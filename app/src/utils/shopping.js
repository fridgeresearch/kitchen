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
let inventoryUtils = require("./inventory.js")
let commonUtils = require("./common.js")

let dynamicCallbacks = [
    {
	className: "grocery-list-link",
	event: "touchend",
	callback: function (e) {
	    console.log("groceryListLinkTouchend")
	    let name = e.currentTarget.dataset.food_name
	    let quant = parseInt(e.currentTarget.dataset.quantity, 10)
	    let id = e.currentTarget.dataset.id
	    if(id.charAt(id.length-1) == "+"){
		inventoryUtils.updateGroceryBundles([name], [quant+1], "POST")
	    }
	    else{
		inventoryUtils.updateGroceryBundles([name], [quant-1], "POST")
	    }
	    let evt = document.createEvent('TouchEvent');
	    evt.initUIEvent('touchend', true, true);
	    document.getElementById('shopping-page').dispatchEvent(evt)
	}
    },
    {
	elementId: "groceryNewBundle",
	event: "submit",
	callback: function(e) {
	    console.log('groceryNewSubmit')
	    e.preventDefault()
	    let evt = document.createEvent('TouchEvent');
	    evt.initUIEvent('touchend', true, true);
	    let name = document.querySelector('input[type=text]').value
	    inventoryUtils.updateGroceryBundles([name], [1], "POST")
	    document.getElementById('shopping-page').dispatchEvent(evt)
	}
    }
]

module.exports = {
    registerDynamicCallbacks: function() { commonUtils.registerCallbacks(dynamicCallbacks) }
}
