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
    } else {
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
 * @param {*} segmentElement
 * @param {*} answerKey
 */
function insertAnswerFormOrHint(segmentElement, answerKey) {

    // prevent insertion if current element is already marked as active
    if (segmentElement.getAttribute('data-active') === "true") {
        return
    }

    if (answerKey.endsWith(user_role)) {
        return insertAnswerForm(segmentElement, answerKey);
    } else {
        return insertHintField(segmentElement, answerKey, user_role);
    }
}


function insertHintField(segment_element, answerKey, user_role) {

    const clonedHintTemplate =  document.getElementById("segment_answer_hint").content.cloneNode(true);
    const hintContainer = clonedHintTemplate.getElementById("__segment_answer_hint_container_id");
    hintContainer.id = "segment_answer_hint_container";

    const hintDiv = hintContainer.getElementsByClassName("segment_answer_hint")[0];

    hintDiv.innerHTML = getHintMessage(segment_element.id, answerKey, user_role);

    // define action of OK button (-> make the hint removable)
    hintContainer.getElementsByClassName("_ok_button")[0].addEventListener('click', function() {
        segment_element.setAttribute('data-active', false);
        hintContainer.remove();
    });

    insertAfter(clonedHintTemplate, segment_element);
    segment_element.setAttribute('data-active', "true");

}

function getHintMessage(segmentId, answerKey, userRole){
    if (!userIsAuthenticated) {
        // this should not occur because segments without answers should not be clickable for non-logged-in users.
        // We have this as 'second line of defense' (if something goes wrong)
        return "You cannot answer without logging in."
    }

    const username = readJsonWithDefault("data-user_name", null);
    const requiredRole = answerKey.slice(-1);
    if (["a", "b"].includes(userRole)) {
        const part1 = `You cannot answer to your own segment (${segmentId}). `;
        const part2 = `You ("${username}") have role <b>${userRole}</b> in this debate. `;
        const part3 = `However, role <b>${requiredRole}</b> is required to answer to segment ${segmentId}.`;
        return part1 + part2 + part3

    } else {

        // this should not occur because segments without answers should not be clickable for users with no role.
        // We have this as 'second line of defense' (if something goes wrong)
        const part1 = `You (username: "${username}") cannot answer to any segment `;
        const part2 = `of this debate because your have neither role a nor role b. See documentation for more information.`;
        return part1 + part2
    }
}


function insertAnswerForm(segmentElement, answerKey, returnMode=null) {

    // in case there already is an opened answer form -> close it
    removeSegmentAnswerFormContainer();

    const clonedFormTemplate =  document.getElementById("segment_answer_form_template").content.cloneNode(true);
    // change ids from the template for the real elements
    const form_container = clonedFormTemplate.getElementById("__segment_answer_form_container_id");
    form_container.id = "segment_answer_form_container";
    form_container.setAttribute("data-related_segment", segmentElement.id);

    // add warning
    if (userIsAuthenticated) {
        form_container.getElementsByClassName("not_logged_in_warning")[0].classList.add("hidden");
    }

    const form = clonedFormTemplate.getElementById("__segment_answer_form_id");
    form.id = "segment_answer_form";

    form.getElementsByClassName("custom-textarea")[0].name = "body"
    form.getElementsByClassName("_reference_segment")[0].value = segmentElement.id;

    const cancelButton = form.getElementsByClassName("_cancel_button")[0];
    cancelButton.id = `cancel_btn_${answerKey}`
    cancelButton.addEventListener('click', function() {
        cancelSegmentAnswerForm(segmentElement.id);
    });

    if (returnMode === null) {
        insertAfter(clonedFormTemplate, segmentElement);
    } else {
        // this is used to edit existing answers
        // (append the form to the answerDiv element)
        return clonedFormTemplate;
    }

    segmentElement.setAttribute('data-active', "true");
}

function cancelSegmentAnswerForm(segment_id) {
    const segment_element = document.getElementById(segment_id);
    segment_element.setAttribute('data-active', false);
    removeSegmentAnswerFormContainer();
}

function removeSegmentAnswerFormContainer(){
    const segment_answer_form_container = document.getElementById("segment_answer_form_container");
    if (segment_answer_form_container != null) {

        const relatedSegmentId = segment_answer_form_container.getAttribute("data-related_segment");
        if (relatedSegmentId != null) {
            document.getElementById(relatedSegmentId).setAttribute('data-active', "false");
        }

        segment_answer_form_container.remove();
    }
}


var answerObjects = null;
var answerMap = {};
var segmentObjects = null;
const userIsAuthenticated = readJsonWithDefault("data-user_is_authenticated", false);
const user_role = readJsonWithDefault("data-user_role", null);
const segIdDisplay = document.getElementById('seg_id_display');
const utdPageType = readJsonWithDefault("data-utd_page_type", null);
const apiData = JSON.parse(readJsonWithDefault("data-api_data", "null"));
const csrfToken = readJsonWithDefault("data-csrf_token", null);
const modalDialog = document.getElementById("modal-dialog");
var activeTextArea = null;

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
        const answerKey = getAnswerKey(segment_span.id);
        if (answerKey in answerMap) {

            // for this segment there is already an answer
            // -> add square symbol
            segment_span.classList.add("sqn");

            const answerDiv = answerMap[answerKey];

            // -> add function to toggle the visibility of the answer
            segment_span.addEventListener('click', function() {
                toggleDisplayNoneBlock(answerDiv);
            });

            // special treatment for db_contributions
            if (answerDiv.classList.contains("db_ctb")){
                segment_span.classList.add("dba");  // distinguish the segment

                const separatorDiv = getSeparatorDiv(segment_span, answerDiv);
                answerDiv.appendChild(separatorDiv);

            }
        } else {
            // This segment does not yet have an answer
            if (!userIsAuthenticated){
                // non-logged-in user: no click-action
                return
            }
            if (!["a", "b"].includes(user_role)){
                // logged-in user with no role: no click-action
                return
            }

            segment_span.addEventListener('click', function() {

                insertAnswerFormOrHint(segment_span, answerKey);
            });
        }
    });

    unfoldAllUncommittedContributions();
    connectCommitAllCtbsButton();
    initializeModalWarningElement();
}

function connectCommitAllCtbsButton() {

    const btn = document.getElementById('commit_all_ctbs_button');
    if (btn === null){
        return
    }

    btn.addEventListener('click', async function () {
        try {
            const response = await fetch(apiData.commit_all_url, generateRequestObjectForCtb(
                apiData.debate_key
            ));
            location.reload();
        } catch(err) {
            console.error(err);
        }
    });

}

function unfoldAllUncommittedContributions() {

    dbCtbDivList = Array.from(document.getElementsByClassName("db_ctb"));
    dbCtbDivList.forEach(ansDiv => {
        // convert "answer_a3b4a12b" to "a3b4a12"
        const key = ansDiv.id.replace("answer_", "").slice(0, -1);
        let parts = key.match(/[ab]\d+/g);
        let cumKey = "";
        // let cumKeys = [];
        parts.forEach(part => {
            cumKey += part;
            // create strings like "a3", "a3b4", "a3b4a12"
            // cumKeys.push(cumKey);

            // ensure element is visible
            document.getElementById(getAnswerKey(cumKey)).style.display = "block";
        });

        // console.log("cumKeys", cumKeys);

    });
}

/**
 * create a div-element as separator below an uncommitted contribution
 * (above the edit field which might be inserted)
 */
function getSeparatorDiv(segment_span, answerDiv){


    const clonedSeparatorTemplateFragment =  document.getElementById("_UCCtbSeparatorTemplate").content.cloneNode(true);
    // note: .getElementsByClassName is not available for Fragments, but querySelector is
    const separatorDiv = clonedSeparatorTemplateFragment.querySelector(".answer_form_separator");
    const answerKey = answerDiv.id;

    // convert "answer_a3b" to "a3b"
    const answerKeyShort = answerKey.replace("answer_", "");
    const textDiv = separatorDiv.getElementsByClassName("_text")[0];
    let info = `Your contribution ${answerKeyShort} is not yet published. `
    info += "You can update it here:"
    textDiv.innerHTML = info;
    //const buttonContainerDiv = separatorDiv.getElementsByClassName("container")[0];
    const editButton = separatorDiv.getElementsByClassName("_edit_button")[0];

    // add unique ids to identify the buttons in unittests
    editButton.id = `edit_btn_${answerKey}`

    editButton.addEventListener('click', function() {
        function okFunc() {
            console.log("edit", segment_span.id)

            // append update form (specify optional second argument)
            const formElement = insertAnswerForm(segment_span, answerKey, true);
            answerDiv.appendChild(formElement);

            // read original md source from data-attribute and insert it to textarea
            const originalMdSrc = answerDiv.getAttribute("data-plain_md_src");
            if (originalMdSrc != null) {

                initActiveTextArea(answerDiv.getElementsByClassName("custom-textarea")[0]);
                activeTextArea.innerHTML = JSON.parse(originalMdSrc);
            }
        }
        activateModalWarningIfNecessary(okFunc);
    });

    // add unique ids to identify the buttons in unittests
    const commitButton = separatorDiv.getElementsByClassName("_commit_button")[0];
    const deleteButton = separatorDiv.getElementsByClassName("_delete_button")[0];
    commitButton.id = `commit_btn_${answerKey}`;
    deleteButton.id = `delete_btn_${answerKey}`;

    commitButton.addEventListener('click', async function() {
        try {
            const response = await fetch(apiData.commit_url, generateRequestObjectForCtb(
                apiData.debate_key, answerKeyShort
            ));
            location.reload();
        } catch(err) {
            console.error(err);
        }
    });

    deleteButton.addEventListener('click', async function() {
        try {
            const response = await fetch(apiData.delete_url, generateRequestObjectForCtb(
                apiData.debate_key, answerKeyShort
            ));
            location.reload();
        } catch(err) {
            console.error(err);
        }
    });

    return separatorDiv
}

function generateRequestObjectForCtb(debateKey, answerKeyShort=null) {

    const body_obj = {
        debate_key: debateKey,
        csrfmiddlewaretoken: csrfToken,
    }

    if (answerKeyShort !== null) {
        body_obj.contribution_key = answerKeyShort
    }

    const requestObj = {
        method: "POST",
        body: JSON.stringify(body_obj),
        headers: {
          "Content-type": "application/json; charset=UTF-8",
          'X-CSRFToken': csrfToken
        }
    }

    return requestObj
}

function initializeModalWarningElement(){
    // Get the modal
    const modalDialogCloseWidget = modalDialog.getElementsByClassName("close-modal")[0];

    // When the user clicks on <span> (x), close the modal
    modalDialogCloseWidget.onclick = closeModalWarning;
    document.getElementById("modal-dialog-cancel-button").onclick = function() {
        closeModalWarning();
    }
}

/**
 *
 * @param {*} oKFunc  function which is executed on OK
 */
function activateModalWarningIfNecessary(okFunc) {
    if (activeTextArea !== null) {
        if (activeTextArea.getAttribute("data-has_changed") === "true") {
            // modal warning dialog is necessary
            activateModalWarning(okFunc);
            return
        }
    }

    // modal warning dialog was not necessary
    okFunc();
}

function initActiveTextArea(taElement) {
    activeTextArea = taElement;
    taElement.setAttribute("data-has_changed", "false");

    taElement.addEventListener('keydown', function(){
        taElement.setAttribute("data-has_changed", "true");
    }, { once: true });
}

function activateModalWarning(okFunc) {
    modalDialog.classList.remove("hidden");

    document.getElementById("modal-dialog-ok-button").addEventListener("click", function() {
        okFunc();
        closeModalWarning();
    }, { once: true });
}

function closeModalWarning() {
    modalDialog.classList.add("hidden");
}



function onLoadForSimplePage(){
    if (utdPageType === "utd_trigger_js_error_page"){
        const x = notExistingVariable*0;
    }
    console.log("simple page loaded")
}

console.log("core.js loaded");
