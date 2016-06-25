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

module.exports = ({includeIngredientNames, excludeIngredientNames, search}) => {
  if(search.length || includeIngredientNames.length || excludeIngredientNames.length){
      return (
	<ul className="table-view">
	  <li className="table-view-cell filters">
	    {search.length ? "results for" : "recipes"}
	    <span className="recipeSearch">
	      {search.length ? ' "'+search+'"' : ""}
	    </span>
	    {includeIngredientNames.length ? " including ingredients" : ""}
	    <span className="includeIngredients">
	      {includeIngredientNames.length ? " "+includeIngredientNames.join(', ') : ""}
	    </span>
	    {includeIngredientNames.length && excludeIngredientNames.length ? " but not" : ""}
	    {!includeIngredientNames.length && excludeIngredientNames.length ? " excluding ingredients" : ""}
	    <span className="excludeIngredients">
	      {excludeIngredientNames.length ? " "+excludeIngredientNames.join(', ') : ""}
	    </span>
	  </li>
	</ul>
      )
  }
  return (<div></div>)  
}
