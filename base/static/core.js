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
 * If the current user has the wrong role insert a hint-element instead
 * @param {*} segment_element
 * @param {*} answer_key
 */
function insertAnswerFormOrHint(segment_element, answer_key) {
    // prevent insertion if current element is already marked as active
    if (segment_element.getAttribute('data-active') === "true") {
        return
    }

    const user_role = JSON.parse(document.getElementById("data-user_role").text)
    console.log("AnswerFormOrHint", segment_element, answer_key, user_role);

    if (answer_key.endsWith(user_role)) {
        return insertAnswerForm(segment_element);
    } else {
        return insertHintField(segment_element, answer_key, user_role);
    }
}


function insertHintField(segment_element, answer_key, user_role) {

    const clonedHintTemplate =  document.getElementById("segment_answer_hint").content.cloneNode(true);
    const hintContainer = clonedHintTemplate.getElementById("__segment_answer_hint_container_id");
    hintContainer.id = "segment_answer_hint_container";

    const hintDiv = hintContainer.getElementsByClassName("segment_answer_hint")[0];

    hintDiv.textContent = getHintMessage(segment_element.id, answer_key, user_role);

    // define action of OK button (-> make the hint removable)
    hintContainer.getElementsByClassName("_ok_button")[0].addEventListener('click', function() {
        segment_element.setAttribute('data-active', false);
        hintContainer.remove();
    });

    insertAfter(clonedHintTemplate, segment_element);
    segment_element.setAttribute('data-active', "true");

}

function getHintMessage(segmentId, answer_key, userRole){

    // this should not occur because segments without answers should not be clickable for
    // non-logged-in users (and users which have no role in this debate)
    if (!user_is_authenticated) {
        return "You cannot answer without logging in."
    }

    const username = readJsonWithDefault("data-user_name", null);
    const requiredRole = answer_key.slice(-1);
    if (["a", "b"].includes(userRole)) {
        return `You cannot answer to segment ${segmentId}. You (username: "${username}") have role ${userRole} but role ${requiredRole} is required.`

    } else {
        return `You (username: "${username}") cannot answer to any segment of this debate because your have neither role a nor role b. See documentation for more information.`

    }

}


function insertAnswerForm(segment_element) {

    const clonedFormTemplate =  document.getElementById("segment_answer_form_template").content.cloneNode(true);
    // change ids from the template for the real elements
    const form_container = clonedFormTemplate.getElementById("__segment_answer_form_container_id");
    form_container.id = "segment_answer_form_container";

    // add warning
    // todo: unify
    const userIsAuthenticated = user_is_authenticated;
    if (userIsAuthenticated) {
        form_container.getElementsByClassName("not_logged_in_warning")[0].classList.add("hidden");
    }

    const form = clonedFormTemplate.getElementById("__segment_answer_form_id");
    form.id = "segment_answer_form";

    form.getElementsByClassName("custom-textarea")[0].name = "body"
    form.getElementsByClassName("_reference_segment")[0].value = segment_element.id;
    form.getElementsByClassName("_cancel_button")[0].addEventListener('click', function() {
        cancelSegmentAnswerForm(segment_element.id);
    });

    insertAfter(clonedFormTemplate, segment_element);
    segment_element.setAttribute('data-active', "true");
}


function cancelSegmentAnswerForm(segment_id) {
    const segment_element = document.getElementById(segment_id);
    segment_element.setAttribute('data-active', false);
    document.getElementById("segment_answer_form_container").remove();
}


var answerObjects = null;
var answerMap = {};
var segmentObjects = null;
const user_is_authenticated = readJsonWithDefault("data-user_is_authenticated", false);
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

            // for this segment there is already an answer
            // -> add square symbol
            segment_span.classList.add("sqn");

            // -> add function to toggle the visibility of the answer
            segment_span.addEventListener('click', function() {
                toggleDisplayNoneBlock(answerMap[answer_key]);
            });
        } else {
            // This segment does not yet have an answer
            segment_span.addEventListener('click', function() {
                // test if user should be able anyway
                insertAnswerFormOrHint(segment_span, answer_key);
            });
        }
    });


}

console.log("core.js loaded");
