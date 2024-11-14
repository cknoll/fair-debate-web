var activeItemMenu = null;


// ddm{s}: drop down menu {symbol}
// using the spread operator `...` to convert a HTMLCollection to an array
const itemMenus = [...document.getElementsByClassName('ddms')];


function closeActiveMenu(){
    if (activeItemMenu == null) {
        return;
    }
    if (activeItemMenu.classList.contains('show')) {
        activeItemMenu.classList.remove('show');
        activeItemMenu = null;
    }

}

// add eventlisteners for all menus
itemMenus.forEach((ddms, idx) => {

    // get id of menu from the id of the symbol (ims -> im)
    var im_id = ddms.id.replace("ddms_", "ddm_");
    var itemMenu = document.getElementById(im_id);

    console.log(ddms.id);

    ddms.addEventListener('click', function() {
        console.log("click", ddms.id);

        if (activeItemMenu == itemMenu) {
            closeActiveMenu();
            return;
        }

        closeActiveMenu();
        if (activeItemMenu != itemMenu) {
            itemMenu.classList.add('show');
            activeItemMenu = itemMenu;
            itemMenu.associatedSymbol = ddms;
        }
    });

});



// add event listener to hide the menu if user clicks outside of the menu

window.addEventListener('click', function(event) {

    if (activeItemMenu == null) {
        return;
    }

    if ((activeItemMenu.contains(event.target) || activeItemMenu.associatedSymbol.contains(event.target))) {
        // console.log("inside");
    } else {
        // console.log("outside");
        closeActiveMenu();
    }
});


function getAnswerKey(key){
    var parts = key.match(/[ab]\d+/g);
    var first_letter_of_last_element = parts.pop()[0]
    var appendix = null;
    if (first_letter_of_last_element == "a") {
        appendix = "b";
    } else {
        appendix = "a";
    }
    return `answer_${key}${appendix}`
}

function toggleDisplayNoneBlock(element) {
    if (element.style.display === "none" || element.style.display === "") {
        element.style.display = "block";
    } else {
        element.style.display = "none";
    }
}

function readJsonWithDefault(dataId, defaultValue) {
    const dataElement = document.getElementById(dataId);
    let result = defaultValue; // Default value

    if (dataElement) {
        try {
            result = JSON.parse(dataElement.text);
        } catch (error) {
            // Handle JSON parsing error if needed
            // console.error("Parsing error:", error);
            result = defaultValue; // Set it once again
        }
    }
    return result
}

/**
 * insert an new element (which can also be a DocumentFragment) after a given element
 * Motivation: A cloned template results in a DocumentFragment which cannot be
 * inserted by refElement.insertAdjacentHTML('afterend', newElement)
 *
 * @param {*} newNode
 * @param {*} referenceNode
 */
function insertAfter(newNode, referenceNode) {
    // Check if the referenceNode has a next sibling
    if (referenceNode.nextSibling) {
        // Insert newNode before the next sibling of referenceNode
        referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling);
    } else {
        // If there is no next sibling, append it to the end
        referenceNode.parentNode.appendChild(newNode);
    }
}

/**
 * Insert answer-form after after the segment element (when clicked on it)
 * @param {*} segment_element
 * @param {*} answer_key
 */
function insertAnswerForm(segment_element, answer_key) {

    // prevent insertion if current element is already marked as active
    if (segment_element.getAttribute('data-active') === "true") {
        return
    }

    console.log(segment_element, answer_key);
    const clonedTemplate =  document.getElementById("segment_answer_form_template").content.cloneNode(true);
    // change ids from the template for the real elements
    const form_container = clonedTemplate.getElementById("__segment_answer_form_container_id");
    form_container.id = "segment_answer_form_container";

    // add warning
    const userIsAuthenticated = readJsonWithDefault("data-user_is_authenticated", false);
    if (userIsAuthenticated) {
        form_container.getElementsByClassName("not_logged_in_warning")[0].classList.add("hidden");
    }

    const form = clonedTemplate.getElementById("__segment_answer_form_id");
    form.id = "segment_answer_form";

    form.getElementsByClassName("custom-textarea")[0].name = "body"
    form.getElementsByClassName("_reference_segment")[0].value = segment_element.id;
    form.getElementsByClassName("_cancel_button")[0].addEventListener('click', function() {
        cancelSegmentAnswerForm(segment_element.id);
    });

    insertAfter(clonedTemplate, segment_element);
    segment_element.setAttribute('data-active', "true");
}

function cancelSegmentAnswerForm(segment_id) {
    console.log(segment_id);
    const segment_element = document.getElementById(segment_id);
    segment_element.setAttribute('data-active', false);
    document.getElementById("segment_answer_form_container").remove();
}


var answerObjects = null;
var answerMap = {};
var segmentObjects = null;
const segIdDisplay = document.getElementById('seg_id_display');

function onLoadForShowDebatePage(){
    answerObjects = Array.from(document.getElementsByClassName("answer"));
    answerObjects.forEach(ansDiv => {
        answerMap[ansDiv.id] = ansDiv;
    });

    segmentObjects = Array.from(document.getElementsByClassName("segment"));

    // Add mouseover and mouseout event listeners to each span
    segmentObjects.forEach(segment_span => {
        segment_span.addEventListener('mouseover', function() {
            // Display the id of the hovered span
            segIdDisplay.textContent = this.id;
        });

        segment_span.addEventListener('mouseout', function() {
            // Clear the display when not hovering
            segIdDisplay.textContent = '';
        });
    });

    // add square symbols and click-event-handler to those segments which have an answer
    segmentObjects.forEach(segment_span => {
        const answer_key = getAnswerKey(segment_span.id);
        if (answer_key in answerMap) {
            segment_span.classList.add("sqn");

            segment_span.addEventListener('click', function() {
                toggleDisplayNoneBlock(answerMap[answer_key]);
            });
        } else {
            // This segment does not yet have an answer
            segment_span.addEventListener('click', function() {
                insertAnswerForm(segment_span, answer_key);
            });
        }
    });


}


// window.onload = function() {
//     document.getElementById('js_warning').remove();

//     var panZoom = svgPanZoom('#main-svg-object', {
//       zoomEnabled: false,
//       controlIconsEnabled: false
//     });
//     var initialZoom = 0.99;

//     panZoom.zoomBy(initialZoom);
//     panZoom.fit();

//     function FuncZoomIn(ev){
//       // ev.preventDefault();
//       panZoom.zoomIn();
//     }

//     function FuncZoomOut(ev){
//         // ev.preventDefault();
//         panZoom.zoomOut();
//       }

//       function FuncZoomReset(ev){
//         // ev.preventDefault();
//         panZoom.resetZoom();
//         panZoom.fit();
//         panZoom.zoomBy(initialZoom);
//         panZoom.center();
//     }

//     document.getElementById('zoom-in1').addEventListener('click', FuncZoomIn);
//     document.getElementById('zoom-in2').addEventListener('click', FuncZoomIn);
//     document.getElementById('zoom-out1').addEventListener('click', FuncZoomOut);
//     document.getElementById('zoom-out2').addEventListener('click', FuncZoomOut);
//     document.getElementById('reset1').addEventListener('click', FuncZoomReset);
//     document.getElementById('reset2').addEventListener('click', FuncZoomReset);
//   };



console.log("core.js loaded");
