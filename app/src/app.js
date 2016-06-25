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
var Food = require('./controllers/food.js')
var Fridge = require('./controllers/fridge.js')
var InteractiveCooking = require('./controllers/interactiveCooking.js')
var Inventory = require('./controllers/inventory.js')
var Recipes = require('./controllers/recipes.js')
var Shopping = require('./controllers/shopping.js')
var commonUtils = require("./utils/common.js");
var serviceConfig = require("../service_config.js")
import './styles/app.scss'

let appState = {
  inventory: null,
  inventorySort: "arrivalevent_time",
  currentItemReadId: null,
  selectCount: 0,
  recipeSearch : {
      search: "",
      ingredients: [],
      splits: []
  },
  baseUrl: serviceConfig["baseUrl"],
  headers: {"Authorization": ""}
}

const controller = {
  'Food': Food.run,
  'Fridge': Fridge.run,
  'InteractiveCooking': InteractiveCooking.run,
  'Inventory': Inventory.run,
  'Recipes': Recipes.run,
  'Shopping': Shopping.run
}

controller['Inventory'](appState);

window.addEventListener('push', function(e) {
    controller[e.detail.state.title](appState)
})
