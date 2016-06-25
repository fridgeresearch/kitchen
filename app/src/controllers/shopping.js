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
import GroceryListComponent from "../components/groceryList"
let commonUtils = require("../utils/common.js");
let shoppingUtils = require("../utils/shopping.js");
let appState = null

module.exports = {
    run: function(state) {
	appState = state
	xhr({
	    url: appState.baseUrl + '/groceryList',
	    headers: appState.headers,
	    json: true
	}, (err, req, body) => {
	    if (!body.statusCode) {
		ReactDOM.render(<GroceryListComponent grocery_list={body} />, document.getElementById('grocerylist'));
	    }
	    else if(body.statusCode == 404) {
		console.log('No grocery list received.');
	    }
	    else{
		console.log('Unknown statusCode: No grocery list received.', body.statusCode);
	    }
	    shoppingUtils.registerDynamicCallbacks()
	})
	commonUtils.handleSegmentedControl()
    }
}
