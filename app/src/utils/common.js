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
function addListenerOnce(button, event, callback) {
    button.removeEventListener(event, callback)
    button.addEventListener(event, callback)
}

function getUrl(obj) {
    if(obj.food_image_url){
        return obj.food_image_url
    }
    else{
        return "http://blog.1800gotjunk.com/wp-content/themes/1800gotjunk/img/default-placeholder.png"
    }
}

function handleSegmentedControl() {
    let links = document.querySelectorAll('.non-seg-control')
    for (let i = 0; i < links.length; i++) {
	links[i].addEventListener('touchend', function (e) {
	    // remove active class from all links
	    let links = document.querySelectorAll('.non-seg-control')
	    for (let i = 0; i < links.length; i++) {
		links[i].classList.remove('active')
	    }
	    
	    // add active class to clicked link
	    e.currentTarget.classList.add('active')
	    
	    // remove active class from all content divs
	    let content = document.querySelectorAll('.control-content')
	    for (let j = 0; j < content.length; j++) {
		if (content[j].classList.contains(e.currentTarget.dataset.targetclass)) {
		    content[j].classList.remove('active')
		    
		    // add active class to matching content div 
		    if (content[j].id === e.currentTarget.dataset.targetid) {
			content[j].classList.add('active')
		    }
		}
	    }
	})
    }
}

function registerCallbacks(callbacks) {
    for(let i = 0; i < callbacks.length; i++){
	let obj = callbacks[i]
	console.log(callbacks[i])
	if(obj.elementId){
	    let el = document.getElementById(obj.elementId)
	    if(el){ addListenerOnce(el, obj.event, obj.callback) }
	}
	else if(obj.className){
	    let els = document.querySelectorAll('.'+obj.className)
	    for (let j = 0; j < els.length; j++) {
		addListenerOnce(els[j], obj.event, obj.callback)
	    }
	}
    }
}

function leftPad(num, d) {
    var ret = String(num)
    while (ret.length < d) {
	ret = '0' + ret
    }
    return ret
}

module.exports = {
    addListenerOnce: addListenerOnce,
    getUrl: getUrl,
    handleSegmentedControl: handleSegmentedControl,
    registerCallbacks: registerCallbacks,
    leftPad: leftPad
}
