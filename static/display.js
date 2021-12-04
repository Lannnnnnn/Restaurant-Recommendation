/* On search, scroll down to results */
function scrolldown() {
    var first_result = document.getElementById("result_element");
    first_result.scrollIntoView();
}

/* When results are produced, fade them in */
function fade_in(element) {
    var opacity = 0.01;
    var timer = setInterval(function () {
        if (opacity >= 1){
            clearInterval(timer);
        }
        element.style.opacity = opacity;
        element.style.filter = opacity*100;
        opacity += opacity * 0.1;
    }, 25);
}