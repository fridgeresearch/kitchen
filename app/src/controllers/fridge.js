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
import FridgeComponent from '../components/fridge'

module.exports = {
    run: function(appState) {
	xhr({
	    url: appState.baseUrl + '/photos',
	    headers: appState.headers,
	    json: true
	}, 
	 (err, req, body) => {
	     if (err) {
		 console.log('No fridge photos received.')
		 ReactDOM.render(<FridgeComponent photos={null} />, document.getElementById('fridge'))
	     }
	     else {
		 console.log('Fridge photos received.')
		 ReactDOM.render(<FridgeComponent photos={body} />, document.getElementById('fridge'))
	     }
	 })
    }
}
