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
var commonUtils = require("../utils/common.js");

module.exports = ({items}) => {
  if (items.length) {
    return (
      <div className="pure-g">
        {items.map((item) => {
          var divStyle = {backgroundImage: 'url(' + commonUtils.getUrl(item) + ')'};
          return (
            <div key={item.itemread_id} className="pure-u-8-24 item-container-8-24">
              <a href="./food.html" className="inventory-link" data-id={item.itemread_id} data-transition="slide-in">
                <div className="item-thumbnail-8-24" style={divStyle}></div>
                <div className="item-name-8-24 two-line-text">{item.food_name}</div>
		{getIcon(item)}
              </a>
              <div className="select" data-id={item.itemread_id} data-food_name={item.food_name}></div>
            </div>
          )
        })}
      </div>
    )
  }
  return (
    <ul className="table-view">
      <li className="table-view-cell">No items found in fridge.</li>
    </ul>
  )
}

function getIcon(obj) {
    console.log(obj.food_name, obj.remaining_time)
    if(obj["remaining_time"] != null && obj["remaining_time"] < 7){
	let percent = Math.round(Math.min(100,100*obj["fraction_life"])/5) * 5
	return (
	    <div>
		<div className="item-fraction-life-8-24">
		    <img src={"icons/progress/progress-"+commonUtils.leftPad(percent,3)+".png"}/>
		</div>
		<div className="item-remaining-time-8-24">{Math.round(obj["remaining_time"])}d</div>
		</div>
	)	    
    }
}
