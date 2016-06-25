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

module.exports = ({grocery_list}) => {
  if (grocery_list.length) {
    return (
	<ul className="table-view">
	  {newItem()}
	  {grocery_list.map((item) => {
	  //console.log("GroceryList item: ", item);
          return (
	    <li key={item.food_name} className="table-view-cell grocery-bundle">
	      <div className="pure-g">
		<div className="pure-u-18-24">{item.food_name}</div>
		<div className="pure-u-2-24 text-align-center">
		  <a className="grocery-list-link" data-id={item.food_name+"-"} data-food_name={item.food_name} data-quantity={item.quantity}>
		    <i className="icon material-icons">remove</i>
		  </a>
	        </div>
		<div className="pure-u-2-24 text-align-center">
		  {item.quantity}
		</div>
		<div className="pure-u-2-24 text-align-center">
		  <a className="grocery-list-link" data-id={item.food_name+"+"} data-food_name={item.food_name} data-quantity={item.quantity}>
		    <i className="icon material-icons">add</i>
		  </a>
		</div>
	      </div>
	    </li>
          )
          })}
	</ul>
    )
  }
  else{
      return (<ul className="table-view">{newItem()}</ul>)
  }
}

function newItem() {
    return (
      <li className="table-view-cell grocery-bundle">
	<div className="pure-g">
	  <div className="pure-u-18-24">
	    <form id="groceryNewBundle">
	    <input type="text" className="grocery-new-bundle" placeholder="Add item"></input>
	    </form>
	  </div>
	</div>
      </li>
    )
}
