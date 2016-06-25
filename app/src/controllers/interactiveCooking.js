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
import InteractiveCookingComponent from '../components/interactiveCooking'
import interactiveCookingUtils from '../utils/interactiveCooking'

module.exports = {
    run: function(appState) {
	console.log("controller: interactiveCooking")
	interactiveCookingUtils.initialize(appState)
	interactiveCookingUtils.registerStaticCallbacks()
	let url = appState.baseUrl + '/split?' + JSON.stringify({previousSplits: appState.recipeSearch.splits})
	xhr(
	{url: url, headers: appState.headers, json: true}, 
	(err, req, body) => {
	    console.log("getSplit body =", body)
	    appState.recipeSearch.splits.push([body, null])
	    let split = appState.recipeSearch.splits[appState.recipeSearch.splits.length-1][0]
	    ReactDOM.render(<InteractiveCookingComponent split={split} />,
			document.getElementById('interactiveCooking'))
	    interactiveCookingUtils.registerDynamicCallbacks()
	})
    }
}
