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

module.exports = ({split}) => {
    console.log("split =", split)
    return (
      <div>
	<div className="pure-g">
	  <div className="pure-u-24-24 text-align-center">
	    Do you have {split}?
	  </div>
	</div>
	<div className="pure-g">
	  <div className="pure-u-12-24 text-align-center">
	    <a id="interactiveNo" className="link-button" href="./interactiveCooking.html">
	      No
	    </a>
	  </div>
	  <div className="pure-u-12-24 text-align-center">
	    <a id="interactiveYes" className="link-button" href="./interactiveCooking.html">
	      Yes
	    </a>
	  </div>
	</div>
      </div>
    )
}
