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
require('babel-register')
var HtmlWebpackPlugin = require('html-webpack-plugin')
var getConfig = require('hjs-webpack')
var serviceConfig = require("./service_config.js")
var config = {
  in: 'src/app.js',
  out: 'public',
  clearBeforeBuild: false,
  html: false,
}
config.output = {}
config.output.publicPath = serviceConfig["publicPath"]
if(serviceConfig["hostname"]) {
    config.hostname = serviceConfig["hostname"]
    config.port = serviceConfig["port"]
}
config = getConfig(config)
//config.isDev = true

config.plugins.push(
  new HtmlWebpackPlugin({
    template: './src/templates/index.html', // Load a custom template
    inject: 'body' // Inject all scripts into the body 
  })
)

config.plugins.push(
  new HtmlWebpackPlugin({
    filename: 'recipes.html',
    template: './src/templates/recipes.html', // Load a custom template
    inject: 'body' // Inject all scripts into the body 
  })
)

config.plugins.push(
  new HtmlWebpackPlugin({
    filename: 'shopping.html',
    template: './src/templates/shopping.html', // Load a custom template
    inject: 'body' // Inject all scripts into the body 
  })
)

config.plugins.push(
  new HtmlWebpackPlugin({
    filename: 'fridge.html',
    template: './src/templates/fridge.html', // Load a custom template
    inject: 'body' // Inject all scripts into the body 
  })
)

config.plugins.push(
  new HtmlWebpackPlugin({
    filename: 'food.html',
    template: './src/templates/food.html', // Load a custom template
    inject: 'body' // Inject all scripts into the body 
  })
)

config.plugins.push(
  new HtmlWebpackPlugin({
    filename: 'interactiveCooking.html',
    template: './src/templates/interactiveCooking.html', // Load a custom template
    inject: 'body' // Inject all scripts into the body 
  })
)

module.exports = config
