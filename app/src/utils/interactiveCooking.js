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
let commonUtils = require("./common.js")
let appState = null;
import xhr from 'xhr'

function getSplit(state) {
    let url = state.baseUrl + '/split?' + JSON.stringify({previousSplits: state.recipeSearch.splits})
    console.log("getSplit url =", url)
    xhr(
	{url: url, headers: state.headers, json: true}, 
	(err, req, body) => {
	    console.log("getSplit body =", body)
	    state.recipeSearch.splits.push([parseInt(body, 10), null])
	    //renderInteractiveCooking(body)
	}
    )
}

let staticCallbacks = [
    {
	elementId: "pageExit",
	event: "touchend",
	callback: function(e) {
	    console.log('pageExitTouchend')
	    appState.recipeSearch.splits = []
	}
    }
]

let dynamicCallbacks = [
    {
	elementId: "interactiveNo",
	event: "touchend",
	callback: function(e) {
	    console.log('interactiveNoTouchend')
	    appState.recipeSearch.splits[appState.recipeSearch.splits.length-1][1] = 0
	}
    },
    {
	elementId: "interactiveYes",
	event: "touchend",
	callback: function(e) {
	    console.log('interactiveYesTouchend')
	    appState.recipeSearch.splits[appState.recipeSearch.splits.length-1][1] = 1
	}
    }
]

module.exports = {
    initialize: function(state) { appState = state; },
    registerStaticCallbacks: function() { commonUtils.registerCallbacks(staticCallbacks) },
    registerDynamicCallbacks: function() { commonUtils.registerCallbacks(dynamicCallbacks) },
    getSplit: function(state) { getSplit(state) }
}
