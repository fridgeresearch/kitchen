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

module.exports = ({recipes}) => {
  let inds = []
  for (let i=1; i<=5; i++){ inds.push(i) }
  if (recipes.length) {
    return (
      <ul className="table-view">
        {recipes.map((recipe) => {
          return (
            <li key={recipe.id} className="table-view-cell recipe">
	      <div className="pure-g">
		<a href={recipe.url} className="inventory-link">
		  <div className="pure-u-6-24">
		    <img className="thumbnail" src={recipe["image-url"]} />
		  </div>
		  <div className="pure-u-18-24 recipe-info">
		     <div className="recipe-title">{recipe.title.replace(/recipe$/i,"")}</div>
		     <div className="quant-container">
		     {inds.map((i) => {
			 return(
			   <img key={recipe.id+"-star-"+i} className="star" src={getStarIcon(recipe["rating"], i)}>
			   </img>	     
			 )
		     })}
	             <span className="made-it">{recipe["made-it"]+" made it"}</span>
	             </div>
	             {/*<div className="description two-line-text">{recipe["meta-description"]}</div>*/}
	             <div className="description two-line-text">{recipe["categories"].join(", ")}</div>
		     <span className="missing">
		       {recipe.missing_ingredients.length ? " missing " : ""}
	             </span>
		     <span className="missing-ingredients">
		       {recipe.missing_ingredients.length ? recipe.missing_ingredients.join(', ') : ""}
	             </span>
	          </div>
	        </a>
	      </div>
            </li>
          )
        })}
      </ul>
    )
  }
  return (
    <ul className="table-view">
      <li className="table-view-cell recipe">No recipes found in fridge.</li>
    </ul>
  )
}

function getStarIcon(rating, i) {
    let r = Math.round(rating*2)/2
    if (i <= r) {
	return "icons/stars/full-star.svg"
    }
    else if (i <= r + 0.5) {
	return "icons/stars/half-star.svg"
    }
    else {
	return "icons/stars/empty-star.svg"
    }
}
