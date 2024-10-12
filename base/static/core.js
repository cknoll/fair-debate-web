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

console.log("core.js loaded");
