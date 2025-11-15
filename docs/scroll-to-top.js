document.addEventListener("DOMContentLoaded", function() {
    // 1. Create the button element
    const button = document.createElement("button");
    button.setAttribute("id", "scrollToTopBtn");
    button.setAttribute("title", "Scroll to Top"); // Sets the hover text
    button.innerHTML = "<i class='fa-solid fa-arrow-up'></i>"; // Font Awesome up-arrow icon

    // 2. Append the button to the body
    document.body.appendChild(button);

    // 3. Define when to show the button (when scrolled more than 100px)
    window.onscroll = function() {
        if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
            button.style.display = "block";
        } else {
            button.style.display = "none";
        }
    };

    // 4. Define the click action (scroll to 0)
    button.onclick = function() {
        document.body.scrollTop = 0; // For Safari
        document.documentElement.scrollTop = 0; // For others
    };
});

