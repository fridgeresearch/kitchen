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

module.exports = ({items}) => {
  if (items.length) {
    return (
    <ul className="table-view">
    {newIngredient()}
    {items.map((item) => {
	return (
		<li key={item.food_name} className="table-view-cell recipe-ingredient-item">
		  <div className="text">
		    {item.food_name}
		    <span className="ingredients">{item.ingredient_tags.length ? " ("+item.ingredient_tags.join(', ')+")" : ""}</span>
		  </div>
		  <div className={"toggle "+(item.include ? "active" : "")}>
		    <div className="toggle-handle"></div>
		  </div>
		</li>
	)
    })}
    </ul>
  )
  }
}

function newIngredient() {
    return (
	<li key="newIngredient" className="table-view-cell recipe-ingredient-item">
	    <form id="newIngredient">
	      <input type="text" placeholder="Add ingredient"></input>
	    </form>
	</li>
    )
}
